# -*- coding: utf-8 -*-
"""
_push_to_rujing.py — 推 rujing CardPackage 到手机 server (v2)
- 用 argparse 接 json 路径
- 用 urllib (POST /upload)
- 修 hardcode bug (v1 永远是 rujing_01.json)
"""
import argparse, sys, json, io
from pathlib import Path
import urllib.request, urllib.error

PHONE_IP = "192.168.1.102"
RUJING_PORT = 18999
UPLOAD_URL = f"http://{PHONE_IP}:{RUJING_PORT}/upload"

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

def push_one(json_path: Path) -> tuple[bool, str]:
    if not json_path.exists():
        return False, f"file not found: {json_path}"
    with open(json_path, "rb") as f:
        body = f.read()
    print(f"[push] {json_path.name} ({len(body)} bytes)")
    try:
        req = urllib.request.Request(UPLOAD_URL, data=body, method="POST",
                                      headers={"Content-Type": "application/json; charset=utf-8"})
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = r.read().decode("utf-8", errors="replace").strip()
            print(f"  -> {r.getcode()} {resp}")
            return True, resp
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:200]}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"

def main():
    parser = argparse.ArgumentParser(description="推 rujing CardPackage 到手机 server")
    parser.add_argument("files", nargs="+", help="要推的 rujing_*.json 文件路径")
    args = parser.parse_args()

    print(f"=== 推送到 {UPLOAD_URL} ===")
    print(f"模式: {len(args.files)} 个文件")
    print()
    ok, fail = 0, 0
    for f in args.files:
        success, msg = push_one(Path(f))
        if success:
            ok += 1
        else:
            fail += 1
            print(f"  FAIL: {msg}")
    print()
    print(f"=== 汇总: {ok} ✓ | {fail} ✗ ===")
    return 0 if fail == 0 else 1

if __name__ == "__main__":
    sys.exit(main())