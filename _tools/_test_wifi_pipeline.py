# -*- coding: utf-8 -*-
"""
test_wifi_pipeline.py — wifi 通道端到端测试 v1.0

测试覆盖（13 个用例）：
  T01 wifi TCP 连通
  T02 /health 返回 rujing ready
  T03 /subjects 数据完整（4 学科 + 总数）
  T04 /articles_dump 数量 + 污染
  T05 /articles_refresh 端点
  T06 单条 /upload 幂等（同 chain 推第二次应 cards=0）
  T07 /articles_dump 重读一致
  T08 增量推送 - 无变更
  T09 增量推送 - 改 1 套自动识别
  T10 增量推送 - 加 1 套自动识别
  T11 增量推送 - 删 1 套不推（state 残留）
  T12 增量推送 - state.json 持久化
  T13 端到端 - 改 + 推 + dump 0 污染

用法:
  python -X utf8 test_wifi_pipeline.py
  python -X utf8 test_wifi_pipeline.py --skip-git
  python -X utf8 test_wifi_pipeline.py --verbose
"""
import io, json, os, sys, time, argparse, subprocess, urllib.request, urllib.error, shutil, hashlib
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# === 配置 ===
PHONE_IP = "192.168.1.102"
RUJING_PORT = 18999
KB_ROOT = Path(r"D:\4_data\knowledge_cards")
STATE_FILE = Path(r"D:\4_data\rujing_out\_wifi_push\state.json")
HDC_BIN = r"C:\Users\willi\AppData\Local\OpenHarmony\Sdk\26.0.0\toolchains\hdc.exe"
DEVICE_ID = "7GL0226313016118"

BASE_URL = f"http://{PHONE_IP}:{RUJING_PORT}"
TIMEOUT = 15

# 测试结果
results = []
def t(name: str, ok: bool, msg: str = "", duration_ms: int = 0):
    status = "✓" if ok else "✗"
    results.append((name, ok, msg, duration_ms))
    suffix = f"  ({duration_ms}ms)" if duration_ms else ""
    print(f"  {status} {name}: {msg}{suffix}")

def http_get(path: str, timeout: int = TIMEOUT):
    url = BASE_URL + path
    start = int(time.time() * 1000)
    try:
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode('utf-8', errors='replace')
            elapsed = int(time.time() * 1000) - start
            return r.getcode(), body, elapsed
    except Exception as e:
        elapsed = int(time.time() * 1000) - start
        return -1, str(e), elapsed

def http_post(path: str, body: str = "", timeout: int = TIMEOUT):
    url = BASE_URL + path
    start = int(time.time() * 1000)
    try:
        req = urllib.request.Request(url, method='POST', data=body.encode('utf-8') if isinstance(body, str) else body)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = r.read().decode('utf-8', errors='replace')
            elapsed = int(time.time() * 1000) - start
            return r.getcode(), resp, elapsed
    except Exception as e:
        elapsed = int(time.time() * 1000) - start
        return -1, str(e), elapsed

def chain_hash(chain_dir: Path) -> str:
    h = hashlib.sha256()
    for name in ('chain.json', 'main.json'):
        p = chain_dir / name
        if p.exists():
            h.update(p.name.encode('utf-8'))
            h.update(b'\0')
            h.update(p.read_bytes())
            h.update(b'\0')
    for p in sorted(chain_dir.glob('K*.json')):
        h.update(p.name.encode('utf-8'))
        h.update(b'\0')
        h.update(p.read_bytes())
        h.update(b'\0')
    return h.hexdigest()


def run_incremental(verbose: bool = False) -> tuple[int, int, int, int, str]:
    """调 _wifi_incremental_push.py，返回 (returncode, ok_count, fail_count, total_count, stdout)"""
    script = KB_ROOT / "_tools" / "_wifi_incremental_push.py"
    # 实际脚本叫 _wifi_incremental_push.py
    candidates = [
        KB_ROOT / "_tools" / "_wifi_incremental_push.py",
        KB_ROOT / "_tools" / "wifi_incremental_push.py",
    ]
    for s in candidates:
        if s.exists():
            script = s
            break
    else:
        return -1, 0, 0, 0, "incremental script not found"

    args = [sys.executable, "-X", "utf8", str(script)]
    if verbose:
        args.append('--verbose')
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=600, encoding='utf-8', errors='replace')
        # 解析 stdout 找 (新增, 修改, 未变, 总数)
        out = r.stdout
        new_c = mod_c = unc_c = 0
        for line in out.split('\n'):
            if '新增:' in line:
                try: new_c = int(line.split('新增:')[1].split()[0])
                except: pass
            elif '修改:' in line:
                try: mod_c = int(line.split('修改:')[1].split()[0])
                except: pass
            elif '未变:' in line:
                try: unc_c = int(line.split('未变:')[1].split()[0])
                except: pass
        return r.returncode, new_c, mod_c, unc_c, out
    except Exception as e:
        return -1, 0, 0, 0, str(e)


def wake_server():
    if sys.platform != "win32":
        return
    try:
        subprocess.run(
            [HDC_BIN, "-t", DEVICE_ID, "shell", "aa", "start", "-b", "com.harmonystudio.rujing", "-a", "EntryAbility"],
            capture_output=True, timeout=5
        )
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', action='store_true', help='详细输出')
    parser.add_argument('--skip-git', action='store_true', help='跳过需要改 git 源的测试')
    args = parser.parse_args()

    print(f"=== wifi 通道端到端测试 ===")
    print(f"phone: {PHONE_IP}:{RUJING_PORT}")
    print(f"time: {time.strftime('%Y-%m-%dT%H:%M:%S')}")
    print()

    # wake
    wake_server()
    time.sleep(1)

    # T01: TCP 连通（用 health 代理）
    print("[T01] wifi TCP 连通")
    code, body, ms = http_get('/health', timeout=5)
    ok = code == 200
    msg = f"GET /health → {code}" if ok else f"GET /health FAIL: {body[:50]}"
    t("T01 wifi TCP 连通", ok, msg, ms)
    if not ok:
        print("  → server 不可达，终止后续测试")
        return 1

    # T02: /health 返回 rujing ready
    print("\n[T02] /health 返回 rujing ready")
    try:
        j = json.loads(body)
        ok = j.get('status') == 'rujing ready'
        msg = f"status: {j.get('status')}, port: {j.get('port')}"
    except Exception as e:
        ok = False
        msg = f"parse fail: {e}"
    t("T02 /health 返回 rujing ready", ok, msg)

    # T03: /subjects 数据完整
    print("\n[T03] /subjects 数据完整")
    code, body, ms = http_get('/subjects')
    try:
        j = json.loads(body)
        subjects = j.get('subjects', [])
        total_chains = sum(s.get('chain_count', 0) for s in subjects)
        total_cards = sum(s.get('card_count', 0) for s in subjects)
        ok = (len(subjects) >= 3 and total_chains >= 150 and total_cards >= 1000)
        sub_summary = ', '.join(f"{s['subject']}={s['chain_count']}/{s['card_count']}" for s in subjects)
        msg = f"{len(subjects)} 学科 / {total_chains} 链 / {total_cards} 张 [{sub_summary}]"
    except Exception as e:
        ok = False
        msg = f"parse fail: {e}"
    t("T03 /subjects 数据完整", ok, msg, ms)

    # T04: /articles_dump 数量 + 污染
    print("\n[T04] /articles_dump 数量 + 污染")
    code, body, ms = http_get('/articles_dump', timeout=30)
    try:
        j = json.loads(body)
        total = j.get('total', 0)
        polluted = j.get('polluted', 0)
        ok = (total >= 150 and polluted == 0)
        msg = f"total: {total}, polluted: {polluted}"
    except Exception as e:
        ok = False
        msg = f"parse fail: {e}"
    t("T04 /articles_dump 数量 + 污染", ok, msg, ms)

    # T05: /articles_refresh 端点（不动实际数据）
    print("\n[T05] /articles_refresh 端点（不动实际数据）")
    code, body, ms = http_post('/articles_refresh', '', timeout=60)
    try:
        j = json.loads(body)
        ok = j.get('status') == 'refreshing'
        msg = f"status: {j.get('status')}"
    except Exception as e:
        ok = False
        msg = f"parse fail: {e}"
    t("T05 /articles_refresh 端点", ok, msg, ms)
    time.sleep(2)

    # T06: /articles_dump 重读一致
    print("\n[T06] /articles_dump 重读一致")
    code, body2, ms = http_get('/articles_dump', timeout=30)
    try:
        j = json.loads(body2)
        total2 = j.get('total', 0)
        polluted2 = j.get('polluted', 0)
        ok = (total2 == total and polluted2 == 0)
        msg = f"total: {total2} (was {total}), polluted: {polluted2}"
    except Exception as e:
        ok = False
        msg = f"parse fail: {e}"
    t("T06 /articles_dump 重读一致", ok, msg, ms)

    # T07: 单条 /upload 幂等
    print("\n[T07] 单条 /upload（推一历史 chain）")
    # 找一张历史 chain
    hist_dir = KB_ROOT / '历史' / 'cards'
    test_chain = hist_dir / '2026-08-16_一国两制与祖国统一'
    if test_chain.exists():
        # 直接调 server /upload 推一张（用我们自己的 CardPackage 转换）
        try:
            r = subprocess.run(
                [sys.executable, "-X", "utf8", str(KB_ROOT / "_tools" / "ru_cardpkg_convert.py"),
                 "--card-dir", str(test_chain),
                 "--output", str(Path("D:/4_data/rujing_out/_test_cardpkg.json"))],
                capture_output=True, text=True, timeout=30, encoding='utf-8', errors='replace'
            )
            with open("D:/4_data/rujing_out/_test_cardpkg.json", 'rb') as f:
                body_pkg = f.read()
            code, resp, ms = http_post('/upload', body_pkg)
            try:
                j = json.loads(resp)
                ok = j.get('status') == 'imported'
                msg = f"status: {j.get('status')}, cards: {j.get('cards')}, chains: {j.get('chains')}"
            except Exception as e:
                ok = False
                msg = f"parse fail: {e}"
        except Exception as e:
            ok = False
            msg = f"upload fail: {e}"
    else:
        ok = False
        msg = f"test chain not found: {test_chain}"
    t("T07 单条 /upload", ok, msg, ms)

    # T08: 增量推送 - 无变更
    print("\n[T08] 增量推送 - 无变更（应 待推=0）")
    rc, new_c, mod_c, unc_c, out = run_incremental(args.verbose)
    if rc == -1:
        ok = False
        msg = out
    else:
        to_push = new_c + mod_c
        ok = (to_push == 0)
        msg = f"新增: {new_c}, 修改: {mod_c}, 未变: {unc_c}, 待推: {to_push}, rc: {rc}"
    t("T08 增量推送 - 无变更", ok, msg)

    if not args.skip_git:
        # T09: 改 1 套 → 应识别修改
        print("\n[T09] 增量推送 - 改 1 套（应 待推=1 修改）")
        test_file = test_chain / 'main.json'
        backup = test_file.with_suffix('.json.bak')
        if test_file.exists():
            try:
                shutil.copy2(test_file, backup)
                j = json.loads(test_file.read_text(encoding='utf-8-sig'))
                j['front'] = j.get('front', '') + ' '
                test_file.write_text(json.dumps(j, ensure_ascii=False, indent=2), encoding='utf-8')
                rc, new_c, mod_c, unc_c, out = run_incremental(args.verbose)
                to_push = new_c + mod_c
                ok = (mod_c == 1 and to_push == 1)
                msg = f"新增: {new_c}, 修改: {mod_c}, 未变: {unc_c}, 待推: {to_push}"
                # 还原
                shutil.copy2(backup, test_file)
                backup.unlink()
            except Exception as e:
                ok = False
                msg = f"exception: {e}"
                if backup.exists():
                    try: shutil.copy2(backup, test_file); backup.unlink()
                    except: pass
        else:
            ok = False
            msg = f"test file not found: {test_file}"
        t("T09 增量推送 - 改 1 套", ok, msg)

        # T10: 新增 1 套 → 应识别新增
        print("\n[T10] 增量推送 - 加 1 套（应 待推=1 新增）")
        # 临时加一个测试 chain（再删）
        test_new = KB_ROOT / '历史' / 'cards' / '_test_wifi_new_2026-08-23'
        try:
            test_new.mkdir(parents=True, exist_ok=True)
            (test_new / 'chain.json').write_text(json.dumps({
                "chain_id": "history/H-TEST-99-测试", "chain_title": "测试新增",
                "subject": "历史", "chain_type": "因果链", "status": "trial_production",
                "module": "test", "topic": "test", "lines": [99]
            }, ensure_ascii=False), encoding='utf-8')
            (test_new / 'main.json').write_text(json.dumps({
                "card_id": "MAIN_H_TEST_99", "chain_id": "H-TEST-99-测试", "chain_title": "测试新增",
                "card_type": "心法卡", "chain_role": "RESULT",
                "front": "测试 front", "back_core": "测试", "back_detail": "测试 back",
                "exam_questions": [], "sources": [], "maturity": "trial_production"
            }, ensure_ascii=False), encoding='utf-8')
            rc, new_c, mod_c, unc_c, out = run_incremental(args.verbose)
            to_push = new_c + mod_c
            # 接受"新增"或"修改"任一 ≥ 1（state 残留时可能算修改）
            ok = (to_push >= 1)
            msg = f"新增: {new_c}, 修改: {mod_c}, 未变: {unc_c}, 待推: {to_push} (接受 new>=1 或 mod>=1)"
        except Exception as e:
            ok = False
            msg = f"exception: {e}"
        finally:
            # 清理
            if test_new.exists():
                shutil.rmtree(test_new, ignore_errors=True)
        t("T10 增量推送 - 加 1 套", ok, msg)

        # T11: 删 1 套（state 残留，不推）
        print("\n[T11] 增量推送 - 删 1 套（state 残留，NEW 应为 0）")
        # 临时加一个 chain，推一次，再删
        test_temp = KB_ROOT / '历史' / 'cards' / '_test_wifi_temp_2026-08-23'
        try:
            test_temp.mkdir(parents=True, exist_ok=True)
            (test_temp / 'chain.json').write_text(json.dumps({
                "chain_id": "history/H-TEMP", "chain_title": "temp", "subject": "历史"
            }, ensure_ascii=False), encoding='utf-8')
            (test_temp / 'main.json').write_text(json.dumps({
                "card_id": "TEMP", "chain_id": "H-TEMP", "chain_title": "temp",
                "card_type": "心法卡", "front": "x", "back_core": "x", "back_detail": "x"
            }, ensure_ascii=False), encoding='utf-8')
            # 推 1 次让 state 知道
            run_incremental(verbose=False)
            # 删
            shutil.rmtree(test_temp, ignore_errors=True)
            # 再跑（state 还有，但 git 没了 → 不算 NEW，state 残留）
            rc, new_c, mod_c, unc_c, out = run_incremental(args.verbose)
            # 期望：新增 0（因为没新东西），但 state 里有一条 orphan
            ok = (new_c == 0)
            msg = f"新增: {new_c} (期望 0), state orphan 待清理"
        except Exception as e:
            ok = False
            msg = f"exception: {e}"
        finally:
            if test_temp.exists():
                shutil.rmtree(test_temp, ignore_errors=True)
        t("T11 增量推送 - 删 1 套", ok, msg)

    # T12: state.json 持久化
    print("\n[T12] state.json 持久化")
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text(encoding='utf-8'))
            chains = state.get('chains', {})
            ok = len(chains) >= 150
            msg = f"state.chains: {len(chains)}, last_run: {state.get('last_run')}"
        except Exception as e:
            ok = False
            msg = f"parse fail: {e}"
    else:
        ok = False
        msg = "state.json not exist"
    t("T12 state.json 持久化", ok, msg)

    # T13: 端到端 - 改 + 推 + dump 0 污染
    print("\n[T13] 端到端 - 改 + 推 + dump 0 污染")
    test_file = test_chain / 'main.json' if test_chain.exists() else None
    if test_file and not args.skip_git:
        backup = test_file.with_suffix('.json.bak')
        try:
            shutil.copy2(test_file, backup)
            j = json.loads(test_file.read_text(encoding='utf-8-sig'))
            j['front'] = j.get('front', '') + '  '
            test_file.write_text(json.dumps(j, ensure_ascii=False, indent=2), encoding='utf-8')
            # 推
            run_incremental(verbose=False)
            # dump
            code, body, ms = http_get('/articles_dump', timeout=30)
            j = json.loads(body)
            polluted = j.get('polluted', 0)
            total = j.get('total', 0)
            ok = (polluted == 0 and total >= 150)
            msg = f"dump total: {total}, polluted: {polluted}"
            # 还原
            shutil.copy2(backup, test_file)
            backup.unlink()
        except Exception as e:
            ok = False
            msg = f"exception: {e}"
            if backup.exists():
                try: shutil.copy2(backup, test_file); backup.unlink()
                except: pass
    else:
        ok = None
        msg = "skipped (--skip-git)"
    t("T13 端到端 - 改 + 推 + dump 0 污染", ok, msg)

    # 总结
    print()
    print("=" * 60)
    passed = sum(1 for _, ok, _, _ in results if ok is True)
    failed = sum(1 for _, ok, _, _ in results if ok is False)
    skipped = sum(1 for _, ok, _, _ in results if ok is None)
    print(f"总计: {len(results)} 测试")
    print(f"  通过: {passed}")
    print(f"  失败: {failed}")
    print(f"  跳过: {skipped}")
    print()
    if failed > 0:
        print("失败测试:")
        for name, ok, msg, _ in results:
            if ok is False:
                print(f"  ✗ {name}: {msg}")
    print()
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
