# -*- coding: utf-8 -*-
"""
wifi_watchdog.py — wifi 通道生存时间监控

每 N 秒测一次 /health，记录 server onBackground 时机。
用于测试 USB 拔掉后 wifi 通道能撑多久。
"""
import io, json, sys, time, argparse, urllib.request, urllib.error
from datetime import datetime

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

PHONE_IP = "192.168.1.102"
RUJING_PORT = 18999
HEALTH_URL = f"http://{PHONE_IP}:{RUJING_PORT}/health"
SUBJECTS_URL = f"http://{PHONE_IP}:{RUJING_PORT}/subjects"
ARTICLES_DUMP_URL = f"http://{PHONE_IP}:{RUJING_PORT}/articles_dump"

def http_get(url, timeout=5):
    start = time.time()
    try:
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode('utf-8', errors='replace')
            elapsed_ms = int((time.time() - start) * 1000)
            return r.getcode(), body, elapsed_ms
    except urllib.error.URLError as e:
        elapsed_ms = int((time.time() - start) * 1000)
        return -1, f"URLError: {e}", elapsed_ms
    except Exception as e:
        elapsed_ms = int((time.time() - start) * 1000)
        return -1, f"{type(e).__name__}: {e}", elapsed_ms

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--interval', type=int, default=30)
    parser.add_argument('--max-min', type=int, default=10)
    parser.add_argument('--once', action='store_true')
    parser.add_argument('--full', action='store_true')
    args = parser.parse_args()

    print(f"=== wifi watchdog v1.0 ===")
    print(f"phone: {PHONE_IP}:{RUJING_PORT}")
    print(f"interval: {args.interval}s, max: {args.max_min}min")
    print(f"start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    end_time = time.time() + args.max_min * 60
    iteration = 0
    last_status = None
    on_background_at = None
    health_history = []

    while time.time() < end_time:
        iteration += 1
        ts = datetime.now().strftime('%H:%M:%S')
        if args.full:
            print(f"--- iter {iteration} @ {ts} ---")
            code, body, ms = http_get(HEALTH_URL)
            health_ok = code == 200
            print(f"  /health: code={code} time={ms}ms {'OK' if health_ok else 'FAIL'}")
            if not health_ok:
                print(f"    body: {body[:100]}")
            code2, body2, ms2 = http_get(SUBJECTS_URL)
            subj_ok = code2 == 200
            print(f"  /subjects: code={code2} time={ms2}ms {'OK' if subj_ok else 'FAIL'}")
            code3, body3, ms3 = http_get(ARTICLES_DUMP_URL, timeout=10)
            dump_ok = code3 == 200
            dump_total = 0
            dump_polluted = 0
            if dump_ok:
                try:
                    j = json.loads(body3)
                    dump_total = j.get('total', 0)
                    dump_polluted = j.get('polluted', 0)
                except:
                    pass
            print(f"  /articles_dump: code={code3} time={ms3}ms total={dump_total} polluted={dump_polluted}")
            status = 'OK' if (health_ok and subj_ok and dump_ok) else 'FAIL'
        else:
            code, body, ms = http_get(HEALTH_URL)
            health_ok = code == 200
            status = 'OK' if health_ok else 'FAIL'
            if args.full or iteration <= 3 or status != last_status:
                if health_ok:
                    try:
                        j = json.loads(body)
                        last_result = j.get('last_result', '?')
                        print(f"  [{iteration:3d}] {ts} {status} health={ms}ms last_result={last_result[:60]}")
                    except:
                        print(f"  [{iteration:3d}] {ts} {status} health={ms}ms")
                else:
                    print(f"  [{iteration:3d}] {ts} {status} {body[:80]}")
        if last_status == 'OK' and status == 'FAIL' and on_background_at is None:
            on_background_at = ts
            print(f"\n  *** server onBackground detected at {ts} ***\n")
        if last_status == 'FAIL' and status == 'OK' and on_background_at is not None:
            on_background_at = None
            print(f"\n  *** server back to foreground ***\n")
        last_status = status
        health_history.append((ts, status))
        if args.once:
            break
        if iteration == 1:
            time.sleep(2)
        else:
            time.sleep(args.interval)

    print()
    print("=== 总结 ===")
    ok_count = sum(1 for _, s in health_history if s == 'OK')
    fail_count = sum(1 for _, s in health_history if s == 'FAIL')
    print(f"  测 {len(health_history)} 次")
    print(f"  OK: {ok_count} ({ok_count * 100 / max(1, len(health_history)):.0f}%)")
    print(f"  FAIL: {fail_count}")
    if on_background_at:
        print(f"  onBackground 起始: {on_background_at}")
    print(f"  end: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == '__main__':
    main()
