# -*- coding: utf-8 -*-
"""
run_cron_incremental.py — cron 调度的增量推送 wrapper

设计要点：
  1. 调 _wifi_incremental_push.py 跑增量推送
  2. 失败时 hdc force-stop + start 拉前台（兜底 server 冻结）
  3. 最多重试 3 次
  4. 失败时输出 ERROR 日志 + 退出码 1
  5. 成功时输出 OK 日志 + 退出码 0

用法:
  python -X utf8 run_cron_incremental.py [--max-retry 3] [--wake-on-fail]

适用:
  - mavis cron 每 6h 调度
  - Windows Task Scheduler
  - 任何定时调度器
"""
import io, json, os, sys, time, argparse, subprocess
from datetime import datetime

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

KB_ROOT = __import__('pathlib').Path(r"D:\4_data\knowledge_cards")
INCREMENTAL_SCRIPT = KB_ROOT / "_tools" / "_wifi_incremental_push.py"
LOG_DIR = __import__('pathlib').Path(r"D:\4_data\rujing_out\_cron_logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

HDC_BIN = r"C:\Users\willi\AppData\Local\OpenHarmony\Sdk\26.0.0\toolchains\hdc.exe"
DEVICE_ID = "7GL0226313016118"


def log(msg: str):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    sys.stdout.flush()


def wake_rujing():
    """force-stop + start rujing（兜底 server 后台冻结）"""
    try:
        log("  [wake] force-stop ...")
        r = subprocess.run(
            [HDC_BIN, "-t", DEVICE_ID, "shell", "aa", "force-stop", "com.harmonystudio.rujing"],
            capture_output=True, timeout=10
        )
        time.sleep(2)
        log("  [wake] start ...")
        r = subprocess.run(
            [HDC_BIN, "-t", DEVICE_ID, "shell", "aa", "start", "-b", "com.harmonystudio.rujing", "-a", "EntryAbility"],
            capture_output=True, timeout=10
        )
        time.sleep(5)
        return True
    except Exception as e:
        log(f"  [wake] fail: {e}")
        return False


def run_incremental():
    """跑 _wifi_incremental_push.py，返回 (returncode, stdout, stderr)"""
    log(f"  [run] {INCREMENTAL_SCRIPT.name}")
    try:
        r = subprocess.run(
            [sys.executable, "-X", "utf8", str(INCREMENTAL_SCRIPT)],
            capture_output=True, text=True, timeout=300, encoding='utf-8', errors='replace'
        )
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired as e:
        return -1, "", f"timeout: {e}"
    except Exception as e:
        return -1, "", f"exception: {e}"


def check_health() -> bool:
    """快速检测 server 是否在响应"""
    try:
        import urllib.request
        req = urllib.request.Request("http://192.168.1.102:18999/health", method='GET')
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.getcode() == 200
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-retry', type=int, default=3, help='最大重试次数')
    parser.add_argument('--wake-on-fail', action='store_true', default=True, help='失败时是否 wake rujing')
    parser.add_argument('--log-prefix', default='cron', help='日志文件名前缀')
    args = parser.parse_args()

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_path = LOG_DIR / f"{args.log_prefix}_{ts}.log"
    log_file = open(log_path, 'w', encoding='utf-8')

    def log_both(msg):
        log(msg)
        log_file.write(msg + '\n')
        log_file.flush()

    log_both("=" * 60)
    log_both(f"cron run start, log={log_path}")
    log_both(f"max_retry={args.max_retry}, wake_on_fail={args.wake_on_fail}")

    final_rc = 1
    new_count = 0
    mod_count = 0
    fail_reason = ""

    for attempt in range(1, args.max_retry + 1):
        log_both(f"\n--- attempt {attempt}/{args.max_retry} ---")

        # 先看 health（避免不必要的重试）
        if not check_health():
            log_both("  [health] FAIL")
            if args.wake_on_fail and attempt < args.max_retry:
                log_both("  [wake] server frozen, force-stop + start")
                if wake_rujing():
                    log_both("  [wake] OK, retry health")
                    if check_health():
                        log_both("  [health] recovered OK")
                    else:
                        log_both("  [health] still FAIL after wake")
                        continue
                else:
                    continue
            else:
                log_both("  [skip] health fail, no wake")
                fail_reason = "health FAIL (server frozen, wake failed or disabled)"
                continue

        # 跑增量推送
        rc, stdout, stderr = run_incremental()
        log_both(f"  [rc] {rc}")
        if stdout:
            # 提取关键信息
            for line in stdout.split('\n'):
                if any(k in line for k in ['待推', '新增', '修改', '未变', 'OK', 'FAIL', 'ARTICLES', '完成']):
                    log_both(f"  > {line.strip()}")
            # 解析新增/修改/未变数字
            for line in stdout.split('\n'):
                if '新增:' in line:
                    try: new_count = int(line.split('新增:')[1].split()[0])
                    except: pass
                if '修改:' in line:
                    try: mod_count = int(line.split('修改:')[1].split()[0])
                    except: pass
        if stderr:
            for line in stderr.split('\n')[:5]:
                if line.strip():
                    log_both(f"  ! {line.strip()}")

        if rc == 0:
            final_rc = 0
            log_both(f"  [OK] attempt {attempt} success")
            break
        else:
            log_both(f"  [FAIL] rc={rc}")
            fail_reason = f"incremental rc={rc}"
            if args.wake_on_fail and attempt < args.max_retry:
                log_both("  [wake] retry with wake")
                wake_rujing()
                continue
            else:
                continue

    log_both("")
    log_both("=" * 60)
    log_both(f"cron run end, final_rc={final_rc}")
    log_both(f"new={new_count} mod={mod_count} fail_reason={fail_reason or 'none'}")
    log_file.close()
    return final_rc


if __name__ == '__main__':
    sys.exit(main())
