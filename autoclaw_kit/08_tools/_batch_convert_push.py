"""
_batch_convert_push.py — 批量转换 + 推送所有 172 套（历史 62 + 地理 49 + 政治 61）v2.0
================================================================================
详见:
  SPDT-004/PRODUCT_LINE.md v2.0
  SPDT-004/tools/accuracy_auditor.py

变更 (vs v1.0):
  - 修 SUBJECTS 漏历史 bug（之前只跑 地理+政治 111 套）
  - 集成 accuracy_auditor 验收
  - 失败重试 3 次（之前无重试）
  - 失败标记到 _failed_<timestamp>/ 目录
  - 转换前先看是否已有 rujing_*.json（避免重复转换）
  - 详细进度日志到 push_log_<timestamp>.txt

用法:
  python _batch_convert_push.py            # 跑全部
  python _batch_convert_push.py --dry-run  # 只转换不推送
  python _batch_convert_push.py --skip-convert  # 只推送已有 rujing_*.json
  python _batch_convert_push.py --accuracy # 跑 accuracy_auditor
"""
import argparse
import io
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ============================================================
# 配置
# ============================================================

PHONE_IP = "192.168.1.102"
PORT = 18999
UPLOAD = f"http://{PHONE_IP}:{PORT}/upload"

OUT_DIR = Path(r"D:/4_data/rujing_out")
CONVERTER = Path(r"D:/4_data/knowledge_cards/autoclaw_kit/08_tools/ru_cardpkg_convert.py")
ACCURACY_AUDITOR = Path(r"D:/2_products/education/SPDT-004_EduContent/tools/accuracy_auditor.py")

SUBJECTS = ["历史", "地理", "政治"]  # 历史 62 + 地理 49 + 政治 61 = 172

PUSH_TIMEOUT = 30
RETRY_MAX = 3
RETRY_DELAY = 5  # 秒

# ============================================================
# 工具函数
# ============================================================

def log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}][{level}] {msg}")


def convert_one(subj, set_name, dry_run=False):
    """转换一套卡片为 rujing CardPackage"""
    src = Path(f"D:/4_data/knowledge_cards/{subj}/cards/{set_name}")
    out_json = OUT_DIR / f"rujing_{set_name}.json"
    if out_json.exists() and out_json.stat().st_size > 1000:
        return True, "already-exists", out_json
    if dry_run:
        return True, "dry-run", out_json
    try:
        r = subprocess.run(
            ["python", "-X", "utf8", str(CONVERTER), "--card-dir", str(src), "--output", str(out_json)],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=PUSH_TIMEOUT,
        )
        if r.returncode == 0 and out_json.exists():
            return True, "ok", out_json
        return False, f"convert-fail: {r.stderr[:200]}", out_json
    except Exception as e:
        return False, f"convert-error: {e}", out_json


def push_one(json_path, retry=0):
    """推送一个 rujing CardPackage 到手机"""
    try:
        with open(json_path, "rb") as f:
            body = f.read()
        req = urllib.request.Request(
            UPLOAD, data=body, method="POST",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        r = urllib.request.urlopen(req, timeout=PUSH_TIMEOUT)
        if r.getcode() == 200:
            return True, "ok"
        return False, f"http-{r.getcode()}"
    except urllib.error.URLError as e:
        if retry < RETRY_MAX:
            time.sleep(RETRY_DELAY)
            return push_one(json_path, retry + 1)
        return False, f"url-error: {e.reason}"
    except Exception as e:
        if retry < RETRY_MAX:
            time.sleep(RETRY_DELAY)
            return push_one(json_path, retry + 1)
        return False, f"error: {e}"


def accuracy_audit(json_path):
    """用 accuracy_auditor 跑准确性"""
    try:
        r = subprocess.run(
            ["python", "-X", "utf8", str(ACCURACY_AUDITOR), "--product", "P-002", "--input", str(json_path)],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
        )
        if r.returncode == 0:
            # 提取总分
            for line in r.stdout.split("\n"):
                if "总分:" in line:
                    return True, line.strip()
            return True, "ok"
        return False, f"audit-fail: {r.stderr[:200]}"
    except Exception as e:
        return False, f"audit-error: {e}"


# ============================================================
# 主流程
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="批量转换 + 推送 172 套卡片")
    parser.add_argument("--dry-run", action="store_true", help="只转换不推送")
    parser.add_argument("--skip-convert", action="store_true", help="只推送已有 rujing_*.json")
    parser.add_argument("--accuracy", action="store_true", help="推送前跑 accuracy_auditor")
    parser.add_argument("--subjects", nargs="+", default=SUBJECTS, help="指定学科（默认全部 3 个）")
    args = parser.parse_args()

    # 准备失败目录
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fail_dir = OUT_DIR / f"_failed_{ts}"
    fail_dir.mkdir(parents=True, exist_ok=True)
    log_file = OUT_DIR / f"push_log_{ts}.txt"
    log_lines = []

    def emit(msg):
        log(msg)
        log_lines.append(msg)

    emit(f"=== 批量推送启动 {ts} ===")
    emit(f"学科: {args.subjects}")
    emit(f"模式: {'dry-run' if args.dry_run else 'skip-convert' if args.skip_convert else 'full'}")
    emit(f"accuracy: {'开启' if args.accuracy else '关闭'}")
    emit(f"失败目录: {fail_dir}")
    emit("")

    total = 0
    ok_convert = 0
    ok_push = 0
    ok_accuracy = 0
    fail_list = []

    for subj in args.subjects:
        cards_dir = Path(f"D:/4_data/knowledge_cards/{subj}/cards")
        if not cards_dir.exists():
            emit(f"[WARN] 学科目录不存在: {cards_dir}", "WARN")
            continue
        sets = sorted([d.name for d in cards_dir.iterdir() if d.is_dir()])
        emit(f"[{subj}] 共 {len(sets)} 套")

        for s in sets:
            total += 1

            # 1. 转换
            if args.skip_convert:
                out_json = OUT_DIR / f"rujing_{s}.json"
                if not out_json.exists():
                    fail_list.append((f"{subj}/{s}", "skip-convert-no-file"))
                    continue
                ok_convert += 1
                status_convert = "skip-convert"
            else:
                ok, status_convert, out_json = convert_one(subj, s, dry_run=args.dry_run)
                if ok:
                    ok_convert += 1
                else:
                    fail_list.append((f"{subj}/{s}", status_convert))
                    if total % 10 == 0:
                        emit(f"[{total}] 进度: convert={ok_convert} push={ok_push} fail={len(fail_list)}")
                    continue

            # 2. accuracy_auditor（可选）
            if args.accuracy and out_json.exists():
                ok_acc, msg_acc = accuracy_audit(out_json)
                if ok_acc:
                    ok_accuracy += 1
                else:
                    emit(f"[WARN] accuracy 失败: {subj}/{s}: {msg_acc}", "WARN")

            # 3. 推送
            if args.dry_run or args.skip_convert and not out_json.exists():
                continue
            if not out_json.exists():
                fail_list.append((f"{subj}/{s}", "no-output-file"))
                continue
            ok_push_status, push_msg = push_one(out_json)
            if ok_push_status:
                ok_push += 1
            else:
                fail_list.append((f"{subj}/{s}", f"push: {push_msg}"))
                # 失败文件复制到 fail_dir
                if out_json.exists():
                    try:
                        import shutil
                        shutil.copy(out_json, fail_dir / out_json.name)
                    except Exception:
                        pass

            if total % 10 == 0:
                emit(f"[{total}] 进度: convert={ok_convert} push={ok_push} fail={len(fail_list)}")

    emit("")
    emit("=== 批量推送完成 ===")
    emit(f"总套数: {total}")
    emit(f"转换成功: {ok_convert}")
    if args.accuracy:
        emit(f"accuracy 通过: {ok_accuracy}")
    emit(f"推送成功: {ok_push}")
    emit(f"失败: {len(fail_list)}")
    if fail_list:
        emit("失败列表（前 20）:")
        for f in fail_list[:20]:
            emit(f"  {f[0]}: {f[1]}")
        if len(fail_list) > 20:
            emit(f"  ... 还有 {len(fail_list) - 20} 个")

    # 写日志
    with open(log_file, "w", encoding="utf-8") as f:
        f.write("\n".join(log_lines))
    emit(f"日志: {log_file}")

    return 0 if not fail_list else 1


if __name__ == "__main__":
    sys.exit(main())
