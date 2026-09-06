# -*- coding: utf-8 -*-
"""
_wifi_batch_push.py — wifi 通道批量推送（v1.0.6 优化版）

相对 _cleaned_batch_push.py 的改进：
  1. wake 频率：20 套 1 次 → 5 套 1 次（防 server 后台冻结）
  2. retry 次数：1 次 → 2 次
  3. 走真实 CardPackage（rujing_*.json 含 node_cards/strategy_cards）
  4. 跑完自动调 /articles_refresh 兜底
  5. 详细 timing 报告

用法:
  python -X utf8 _wifi_batch_push.py [--subjects 历史 地理 政治] [--wake-every 5] [--retry 2]
"""
import io, json, os, re, sys, time, argparse, subprocess, urllib.request, urllib.error, shutil
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
HDC_BIN = r"C:\Users\willi\AppData\Local\OpenHarmony\Sdk\26.0.0\toolchains\hdc.exe"
DEVICE_ID = "7GL0226313016118"
SUBJECTS = ["历史", "地理", "政治"]
UPLOAD_URL = f"http://{PHONE_IP}:{RUJING_PORT}/upload"
ARTICLES_REFRESH_URL = f"http://{PHONE_IP}:{RUJING_PORT}/articles_refresh"
TIMEOUT = 15
WARN_TIMEOUT = 30

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
    """推 1 个 CardPackage 到 server。失败时立即 wake_server 再重试。返回 (success, response, elapsed_ms)"""
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
                # 失败时主动 wake_server（防 server 后台冻结）
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
    parser.add_argument('--wake-every', type=int, default=5, help='每 N 套 wake 一次（默认 5）')
    parser.add_argument('--retry', type=int, default=2, help='失败重试次数（默认 2）')
    parser.add_argument('--timeout', type=int, default=TIMEOUT, help='单套超时秒数（默认 15）')
    parser.add_argument('--skip-refresh', action='store_true', help='跳过最后 /articles_refresh')
    parser.add_argument('--limit', type=int, default=0, help='最多推送 N 套（0=全部）')
    args = parser.parse_args()

    print(f"=== wifi 通道批量推送 v1.0.6 ===")
    print(f"phone: {PHONE_IP}:{RUJING_PORT}")
    print(f"kb_root: {KB_ROOT}")
    print(f"out_dir: {OUT_DIR}")
    print(f"subjects: {args.subjects}")
    print(f"wake_every: {args.wake_every}, retry: {args.retry}, timeout: {args.timeout}s")
    print()

    chains = discover_chains(args.subjects)
    if args.limit > 0:
        chains = chains[:args.limit]
    print(f"发现 {len(chains)} 套")
    print()

    # 清空旧产物
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 健康检查
    try:
        req = urllib.request.Request(f"http://{PHONE_IP}:{RUJING_PORT}/health", method='GET')
        with urllib.request.urlopen(req, timeout=5) as r:
            print(f"[health] {r.read().decode('utf-8', errors='replace')}")
    except Exception as e:
        print(f"[health] FAIL: {e}")
        print("  → 继续，可能 server 还没起")

    # 首次 wake
    wake_server(verbose=False)
    time.sleep(1)

    stats = {
        'total': len(chains),
        'ok': 0,
        'fail': 0,
        'convert_fail': 0,
        'total_cards': 0,
        'total_chains': 0,
        'times': [],
        'errors': []
    }
    start_all = time.time()

    for i, (subj, chain_dir) in enumerate(chains, 1):
        name = chain_dir.name
        out_path = OUT_DIR / f"rujing_{name}.json"

        # 转换
        t_convert = time.time()
        try:
            out_path = convert_one(subj, chain_dir, OUT_DIR)
        except Exception as e:
            stats['convert_fail'] += 1
            stats['fail'] += 1
            stats['errors'].append(('convert', name, str(e)[:100]))
            print(f"  [{i:3d}/{len(chains)}] X convert {name}: {str(e)[:100]}")
            continue

        # 每 N 套 wake 一次
        if (i - 1) % args.wake_every == 0:
            wake_server(verbose=False)
            time.sleep(0.2)

        # 推送
        ok, resp, elapsed = push_one(out_path, retry=args.retry, timeout=args.timeout)
        stats['times'].append(elapsed)
        if ok:
            try:
                j = json.loads(resp)
                if j.get('status') == 'imported':
                    stats['ok'] += 1
                    stats['total_cards'] += j.get('cards', 0)
                    stats['total_chains'] += j.get('chains', 0)
                    print(f"  [{i:3d}/{len(chains)}] OK  {name}  {j.get('cards')}/{j.get('chains')}  {elapsed}ms")
                else:
                    stats['fail'] += 1
                    stats['errors'].append(('resp', name, resp[:100]))
                    print(f"  [{i:3d}/{len(chains)}] X  resp {name}: {resp[:100]}")
            except Exception as e:
                stats['fail'] += 1
                stats['errors'].append(('parse', name, str(e)[:100]))
                print(f"  [{i:3d}/{len(chains)}] X  parse {name}: {e}")
        else:
            stats['fail'] += 1
            stats['errors'].append(('push', name, resp[:100]))
            print(f"  [{i:3d}/{len(chains)}] X  push {name}: {resp[:100]}")

        # 进度报告
        if i % 25 == 0:
            elapsed_all = time.time() - start_all
            print(f"  --- [progress] {i}/{len(chains)} elapsed={elapsed_all:.0f}s ok={stats['ok']} fail={stats['fail']} ---")

    total_elapsed = time.time() - start_all
    print()
    print("=" * 60)
    print(f"总: {stats['total']} / OK: {stats['ok']} / FAIL: {stats['fail']} (convert: {stats['convert_fail']})")
    print(f"总卡: {stats['total_cards']} / 总链: {stats['total_chains']}")
    print(f"总耗时: {total_elapsed:.0f}s ({total_elapsed/60:.1f}min)")
    if stats['times']:
        avg = sum(stats['times']) / len(stats['times'])
        mn = min(stats['times'])
        mx = max(stats['times'])
        sorted_t = sorted(stats['times'])
        p95 = sorted_t[int(len(sorted_t) * 0.95)]
        print(f"推送 timing: min={mn}ms / avg={avg:.0f}ms / p95={p95}ms / max={mx}ms")
    if stats['errors']:
        print(f"\n前 5 错误:")
        for kind, name, msg in stats['errors'][:5]:
            print(f"  [{kind}] {name}: {msg}")

    # 跑完 /articles_refresh 兜底
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
