# -*- coding: utf-8 -*-
"""
_wifi_incremental_push.py — wifi 通道增量推送（v1.0.7 优化版）

相对 _wifi_batch_push.py 的改进：
  1. SHA-256 hash 标识 chain 内容，只推变更
  2. state.json 持久化（记录每套 chain 的 hash + last_pushed_at）
  3. 首次跑 = 全量（生成 state）；后续跑 = 增量
  4. 支持强制全量 (--full)
  5. 输出详细的"新增/修改/未变/总数"报告

用法:
  # 首次：全量推
  python -X utf8 _wifi_incremental_push.py
  # 后续：只推变更
  python -X utf8 _wifi_incremental_push.py
  # 强制全量
  python -X utf8 _wifi_incremental_push.py --full
  # 看 diff（不实际推）
  python -X utf8 _wifi_incremental_push.py --dry-run
"""
import io, json, os, re, sys, time, argparse, subprocess, urllib.request, urllib.error, shutil, hashlib
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# === 配置 ===
PHONE_IP = "192.168.1.102"
RUJING_PORT = 18999
KB_ROOT = Path(r"D:\4_data\knowledge_cards")
CONVERT_TOOL = KB_ROOT / "_tools" / "ru_cardpkg_convert.py"
OUT_DIR = Path(r"D:\4_data\rujing_out\_wifi_push")
STATE_FILE = OUT_DIR / "state.json"
HDC_BIN = r"C:\Users\willi\AppData\Local\OpenHarmony\Sdk\26.0.0\toolchains\hdc.exe"
DEVICE_ID = "7GL0226313016118"
SUBJECTS = ["历史", "地理", "政治"]
UPLOAD_URL = f"http://{PHONE_IP}:{RUJING_PORT}/upload"
ARTICLES_REFRESH_URL = f"http://{PHONE_IP}:{RUJING_PORT}/articles_refresh"
TIMEOUT = 15
WARN_TIMEOUT = 30

STATE_VERSION = 1


def wake_server(verbose: bool = False):
    """拉 rujing APP 到前台防 server 冻"""
    if sys.platform != "win32":
        return
    try:
        r = subprocess.run(
            [HDC_BIN, "-t", DEVICE_ID, "shell", "aa", "start", "-b", "com.harmonystudio.rujing", "-a", "EntryAbility"],
            capture_output=True, timeout=5
        )
        if verbose:
            print(f"    [wake] {r.stdout.decode('utf-8', errors='replace').strip() or 'OK'}")
    except Exception as e:
        if verbose:
            print(f"    [wake] fail: {e}")


def chain_hash(chain_dir: Path) -> str:
    """计算一个 chain 的 SHA-256 hash（基于 chain.json + main.json + K*.json 合并）"""
    h = hashlib.sha256()
    # 排序：先 chain.json 再 main.json 再 K*.json
    files = []
    for name in ('chain.json', 'main.json'):
        p = chain_dir / name
        if p.exists():
            files.append(p)
    for p in sorted(chain_dir.glob('K*.json')):
        files.append(p)
    for p in files:
        h.update(p.name.encode('utf-8'))
        h.update(b'\0')
        try:
            h.update(p.read_bytes())
        except Exception as e:
            h.update(f"ERROR:{e}".encode('utf-8'))
        h.update(b'\0')
    return h.hexdigest()


def load_state() -> dict:
    """读 state.json，没有就返回空"""
    if not STATE_FILE.exists():
        return {"version": STATE_VERSION, "last_run": None, "chains": {}}
    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            state = json.load(f)
        if state.get('version') != STATE_VERSION:
            print(f"  [state] 版本不匹配 (got {state.get('version')}, expect {STATE_VERSION})，重置")
            return {"version": STATE_VERSION, "last_run": None, "chains": {}}
        return state
    except Exception as e:
        print(f"  [state] 读取失败: {e}，重置")
        return {"version": STATE_VERSION, "last_run": None, "chains": {}}


def save_state(state: dict):
    """写 state.json"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix('.json.tmp')
    try:
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)
        # 原子重命名
        os.replace(tmp, STATE_FILE)
    except Exception as e:
        print(f"  [state] 写入失败: {e}")
        if tmp.exists():
            try:
                tmp.unlink()
            except:
                pass


def discover_chains(subjects: list) -> list:
    """扫描学科下的所有 chain 目录"""
    chains = []
    for subj in subjects:
        cards_dir = KB_ROOT / subj / "cards"
        if not cards_dir.exists():
            continue
        for chain_dir in cards_dir.iterdir():
            if not chain_dir.is_dir():
                continue
            chain_json = chain_dir / "chain.json"
            main_json = chain_dir / "main.json"
            if chain_json.exists() and main_json.exists():
                chains.append((subj, chain_dir))
    return chains


def convert_one(subj: str, chain_dir: Path, out_dir: Path) -> Path:
    """调用 ru_cardpkg_convert.py 转 1 套为 CardPackage"""
    out_path = out_dir / f"rujing_{chain_dir.name}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable, "-X", "utf8",
        str(CONVERT_TOOL),
        "--card-dir", str(chain_dir),
        "--output", str(out_path)
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode != 0 or not out_path.exists():
        raise RuntimeError(f"转换失败: {chain_dir}\n{r.stderr[-500:]}")
    return out_path


def push_one(json_path: Path, retry: int = 2, timeout: int = TIMEOUT) -> tuple[bool, str, int]:
    """推 1 个 CardPackage 到 server。失败时立即 wake_server 再重试。"""
    with open(json_path, 'rb') as f:
        body = f.read()
    for attempt in range(retry + 1):
        start_ms = int(time.time() * 1000)
        try:
            req = urllib.request.Request(
                UPLOAD_URL, data=body, method='POST',
                headers={'Content-Type': 'application/json; charset=utf-8'}
            )
            with urllib.request.urlopen(req, timeout=timeout) as r:
                resp = r.read().decode('utf-8', errors='replace')
                elapsed = int(time.time() * 1000) - start_ms
                return True, resp.strip(), elapsed
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ConnectionError) as e:
            elapsed = int(time.time() * 1000) - start_ms
            err = str(e)
            if attempt < retry:
                wake_server(verbose=False)
                time.sleep(1)
                continue
            return False, err, elapsed
        except Exception as e:
            elapsed = int(time.time() * 1000) - start_ms
            return False, f"unexpected: {e}", elapsed
    return False, "max retries", 0


def call_articles_refresh() -> str:
    """调 /articles_refresh 用 DB 重写 filesDir"""
    try:
        req = urllib.request.Request(ARTICLES_REFRESH_URL, method='POST', data=b'')
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read().decode('utf-8', errors='replace')
    except Exception as e:
        return f"refresh fail: {e}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--subjects', nargs='+', default=SUBJECTS, help='学科列表')
    parser.add_argument('--wake-every', type=int, default=5, help='每 N 套 wake 一次')
    parser.add_argument('--retry', type=int, default=2, help='失败重试次数')
    parser.add_argument('--full', action='store_true', help='强制全量推（忽略 state）')
    parser.add_argument('--dry-run', action='store_true', help='只显示 diff，不实际推')
    parser.add_argument('--skip-refresh', action='store_true', help='跳过最后 /articles_refresh')
    parser.add_argument('--limit', type=int, default=0, help='最多推送 N 套（0=全部）')
    args = parser.parse_args()

    print(f"=== wifi 增量推送 v1.0.7 ===")
    print(f"phone: {PHONE_IP}:{RUJING_PORT}")
    print(f"kb_root: {KB_ROOT}")
    print(f"out_dir: {OUT_DIR}")
    print(f"subjects: {args.subjects}")
    print(f"mode: {'FORCE FULL' if args.full else ('DRY-RUN' if args.dry_run else 'INCREMENTAL')}")
    print()

    # 扫描 chain
    chains = discover_chains(args.subjects)
    if args.limit > 0:
        chains = chains[:args.limit]
    print(f"发现 {len(chains)} 套")

    # 算 hash
    chain_info = []  # [(subj, chain_dir, hash, status)]
    print(f"计算 hash ...")
    for subj, chain_dir in chains:
        try:
            h = chain_hash(chain_dir)
            chain_info.append((subj, chain_dir, h))
        except Exception as e:
            print(f"  [hash] {chain_dir.name}: {e}")

    # 读 state
    state = load_state()
    state_chains = state.get('chains', {})
    if args.full:
        print(f"[state] 强制全量（忽略已有 {len(state_chains)} 条记录）")
    else:
        print(f"[state] 已有 {len(state_chains)} 条记录")

    # diff
    new_chains = []      # chain_id 不在 state
    modified_chains = []  # chain_id 在 state 但 hash 不同
    unchanged = 0
    for subj, chain_dir, h in chain_info:
        cid = chain_dir.name
        if cid not in state_chains:
            new_chains.append((subj, chain_dir, h))
        elif state_chains[cid].get('hash') != h:
            modified_chains.append((subj, chain_dir, h))
        else:
            unchanged += 1

    to_push = new_chains + modified_chains
    print()
    print(f"[diff] 总 {len(chain_info)} 套")
    print(f"       新增: {len(new_chains)}")
    print(f"       修改: {len(modified_chains)}")
    print(f"       未变: {unchanged}")
    print(f"       待推: {len(to_push)}")
    print()

    if len(to_push) == 0:
        print("=== 无变更，无需推送 ===")
        # 仍然写 state（更新 last_run）
        state['last_run'] = time.strftime('%Y-%m-%dT%H:%M:%S')
        save_state(state)
        return 0

    if args.dry_run:
        print("=== DRY-RUN: 列出待推 ===")
        for subj, chain_dir, h in to_push:
            tag = "NEW" if chain_dir.name not in state_chains else "MOD"
            print(f"  [{tag}] {subj} {chain_dir.name}  hash={h[:12]}...")
        return 0  # 修复：dry-run 不算失败

    # 健康检查
    try:
        req = urllib.request.Request(f"http://{PHONE_IP}:{RUJING_PORT}/health", method='GET')
        with urllib.request.urlopen(req, timeout=5) as r:
            print(f"[health] {r.read().decode('utf-8', errors='replace')}")
    except Exception as e:
        print(f"[health] FAIL: {e}")

    # 首次 wake
    wake_server(verbose=False)
    time.sleep(1)

    # 清空旧 out_dir
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 推送
    stats = {
        'ok': 0,
        'fail': 0,
        'convert_fail': 0,
        'total_cards': 0,
        'total_chains': 0,
        'times': [],
        'errors': []
    }
    start_all = time.time()

    for i, (subj, chain_dir, h) in enumerate(to_push, 1):
        name = chain_dir.name
        out_path = OUT_DIR / f"rujing_{name}.json"
        # 转换
        try:
            out_path = convert_one(subj, chain_dir, OUT_DIR)
        except Exception as e:
            stats['convert_fail'] += 1
            stats['fail'] += 1
            stats['errors'].append(('convert', name, str(e)[:100]))
            print(f"  [{i:3d}/{len(to_push)}] X convert {name}: {str(e)[:100]}")
            continue

        # 每 N 套 wake
        if (i - 1) % args.wake_every == 0:
            wake_server(verbose=False)
            time.sleep(0.2)

        # 推
        ok, resp, elapsed = push_one(out_path, retry=args.retry, timeout=TIMEOUT)
        stats['times'].append(elapsed)
        if ok:
            try:
                j = json.loads(resp)
                if j.get('status') == 'imported':
                    stats['ok'] += 1
                    stats['total_cards'] += j.get('cards', 0)
                    stats['total_chains'] += j.get('chains', 0)
                    # 更新 state
                    state['chains'][name] = {
                        'hash': h,
                        'last_pushed_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
                        'cards': j.get('cards', 0),
                        'subject': subj
                    }
                    print(f"  [{i:3d}/{len(to_push)}] OK  {name}  {j.get('cards')}/{j.get('chains')}  {elapsed}ms")
                else:
                    stats['fail'] += 1
                    stats['errors'].append(('resp', name, resp[:100]))
                    print(f"  [{i:3d}/{len(to_push)}] X  resp {name}: {resp[:100]}")
            except Exception as e:
                stats['fail'] += 1
                stats['errors'].append(('parse', name, str(e)[:100]))
                print(f"  [{i:3d}/{len(to_push)}] X  parse {name}: {e}")
        else:
            stats['fail'] += 1
            stats['errors'].append(('push', name, resp[:100]))
            print(f"  [{i:3d}/{len(to_push)}] X  push {name}: {resp[:100]}")

    total_elapsed = time.time() - start_all
    print()
    print("=" * 60)
    print(f"推送: {stats['ok']} OK / {stats['fail']} FAIL (convert: {stats['convert_fail']})")
    print(f"总卡: {stats['total_cards']} / 总链: {stats['total_chains']}")
    print(f"耗时: {total_elapsed:.0f}s")
    if stats['times']:
        avg = sum(stats['times']) / len(stats['times'])
        mn = min(stats['times'])
        mx = max(stats['times'])
        sorted_t = sorted(stats['times'])
        p95 = sorted_t[int(len(sorted_t) * 0.95)] if len(sorted_t) > 0 else 0
        print(f"timing: min={mn}ms / avg={avg:.0f}ms / p95={p95}ms / max={mx}ms")
    if stats['errors']:
        print(f"\n前 5 错误:")
        for kind, name, msg in stats['errors'][:5]:
            print(f"  [{kind}] {name}: {msg}")

    # 写 state
    state['last_run'] = time.strftime('%Y-%m-%dT%H:%M:%S')
    save_state(state)
    print(f"\n[state] 已更新 {STATE_FILE}")

    # /articles_refresh 兜底
    if not args.skip_refresh and stats['ok'] > 0:
        print()
        print("[refresh] /articles_refresh 兜底...")
        wake_server(verbose=False)
        time.sleep(1)
        r = call_articles_refresh()
        print(f"  {r}")

    print()
    print(f"=== 完成: 退出码 {0 if stats['fail'] == 0 else 1} ===")
    return 0 if stats['fail'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
