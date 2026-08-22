# -*- coding: utf-8 -*-
"""
_cleaned_batch_push.py — v6.0 批量转 + 推清洗版到 rujing server

步骤:
  1. 扫描 git 知识库 173 套 main.json/K0X.json (清洗版)
  2. 每套用 ru_cardpkg_convert.py 转 v6.0 CardPackage 到 D:\4_data\rujing_out\_cleaned\
  3. 用 urllib POST /upload 推 server (按 chain_id 覆盖)
  4. 失败重试 3 次 + 报告

用法:
  python -X utf8 _cleaned_batch_push.py [--dry-run] [--subjects 历史 地理 政治] [--skip-convert]
"""
import io, json, os, re, sys, time, argparse, subprocess, urllib.request, shutil, platform
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# === 配置 ===
PHONE_IP = "192.168.1.102"
RUJING_PORT = 18999
KB_ROOT = Path(r"D:\4_data\knowledge_cards")
CONVERT_TOOL = KB_ROOT / "_tools" / "ru_cardpkg_convert.py"
OUT_DIR = Path(r"D:\4_data\rujing_out\_cleaned")
UPLOAD_URL = f"http://{PHONE_IP}:{RUJING_PORT}/upload"
TIMEOUT = 10
RETRY = 1
PUSH_BATCH = 20  # 每推 N 套拉一次前台

SUBJECTS = ["历史", "地理", "政治"]
HDC_BIN = r"C:\Users\willi\AppData\Local\OpenHarmony\Sdk\26.0.0\toolchains\hdc.exe"
DEVICE_ID = "7GL0226313016118"

def wake_server():
    """拉 rujing APP 到前台防止 server 冻"""
    if platform.system() != "Windows":
        return
    try:
        subprocess.run([HDC_BIN, "-t", DEVICE_ID, "shell", "aa", "start", "-b", "com.harmonystudio.rujing", "-a", "EntryAbility"],
                       capture_output=True, timeout=5)
    except Exception:
        pass

def discover_chains(subjects: list) -> list:
    """扫描 173 套 (按 chain.json)"""
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
    """调用 ru_cardpkg_convert.py 转 1 套"""
    out_path = out_dir / f"{subj}_{chain_dir.name}.json"
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

def push_one(json_path: Path) -> tuple[bool, str]:
    """用 urllib 推 1 个 CardPackage"""
    with open(json_path, 'rb') as f:
        body = f.read()
    for attempt in range(RETRY):
        try:
            req = urllib.request.Request(
                UPLOAD_URL, data=body, method='POST',
                headers={'Content-Type': 'application/json; charset=utf-8'}
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                resp = r.read().decode('utf-8', errors='replace')
                return True, resp.strip()
        except Exception as e:
            if attempt < RETRY - 1:
                time.sleep(2)
                continue
            return False, str(e)
    return False, "max retries"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='只转换不推送')
    parser.add_argument('--subjects', nargs='+', default=SUBJECTS, help='学科')
    parser.add_argument('--skip-convert', action='store_true', help='跳过转换（用已有 CardPackage）')
    args = parser.parse_args()

    print(f"=== 批量转+推清洗版 ===")
    print(f"phone: {PHONE_IP}:{RUJING_PORT}")
    print(f"kb_root: {KB_ROOT}")
    print(f"out_dir: {OUT_DIR}")
    print(f"subjects: {args.subjects}")
    print(f"mode: {'DRY-RUN' if args.dry_run else 'EXECUTE'}")
    print()

    chains = discover_chains(args.subjects)
    print(f"发现 {len(chains)} 套")
    print()

    stats = {
        'total': len(chains),
        'converted': 0,
        'pushed_ok': 0,
        'pushed_fail': 0,
        'convert_fail': 0,
        'errors': []
    }

    if not args.skip_convert:
        # 清空 out_dir 旧产物
        if OUT_DIR.exists():
            shutil.rmtree(OUT_DIR)
        OUT_DIR.mkdir(parents=True, exist_ok=True)

    for i, (subj, chain_dir) in enumerate(chains, 1):
        out_path = OUT_DIR / f"{subj}_{chain_dir.name}.json"
        if not args.skip_convert:
            try:
                out_path = convert_one(subj, chain_dir, OUT_DIR)
                stats['converted'] += 1
            except Exception as e:
                stats['convert_fail'] += 1
                stats['errors'].append(('convert', str(chain_dir), str(e)))
                print(f"  [{i:3d}/{len(chains)}] ✗ CONVERT {chain_dir.name}: {e}")
                continue

        if args.dry_run:
            print(f"  [{i:3d}/{len(chains)}] DRY {chain_dir.name}")
            continue

        # 每 N 套拉一次前台防冻
        if i % PUSH_BATCH == 1:
            wake_server()
            time.sleep(0.5)

        # 推
        ok, resp = push_one(out_path)
        if ok:
            stats['pushed_ok'] += 1
            # 抽 result 看卡数
            try:
                j = json.loads(resp)
                n_cards = j.get('cards', 0)
            except:
                n_cards = '?'
            print(f"  [{i:3d}/{len(chains)}] ✓ {chain_dir.name} → {n_cards} cards")
        else:
            stats['pushed_fail'] += 1
            stats['errors'].append(('push', str(chain_dir), resp[:200]))
            print(f"  [{i:3d}/{len(chains)}] ✗ PUSH {chain_dir.name}: {resp[:100]}")

    print()
    print("=" * 50)
    print(f"总: {stats['total']}")
    if not args.skip_convert:
        print(f"转换: {stats['converted']} ✓ | {stats['convert_fail']} ✗")
    if not args.dry_run:
        print(f"推送: {stats['pushed_ok']} ✓ | {stats['pushed_fail']} ✗")
    if stats['errors']:
        print()
        print(f"前 5 错误:")
        for kind, path, msg in stats['errors'][:5]:
            print(f"  [{kind}] {path}: {msg}")
    return 0 if stats['pushed_fail'] == 0 and stats['convert_fail'] == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
