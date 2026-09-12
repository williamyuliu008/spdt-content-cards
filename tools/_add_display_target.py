"""
_add_display_target.py — 给雪薇端产出的知识卡补全 display_target 字段

============================================================
背景 (commit 543c7d5 v1.0 协作基线)
============================================================
display_target 字段必填, 用于决定卡片在哪个窗口展示:
  - ["学习中心"]                      → 雪薇端产出, 仅学习中心窗口
  - ["RUJING"]                        → 宇兄端产出, 仅 RUJING 窗口
  - ["学习中心", "RUJING"]            → 共同仓通用, 双窗口
  - []                                → 共同规范/工具, 不展示 (autoclaw_kit 等)

v1.0/v1.1 时代产出 (历史内容) 由系统默认按 ['学习中心', 'RUJING'] 双展示,
**不需要** 主动打标, 本脚本也 **不会** 修改历史已带 display_target 的内容。

============================================================
本脚本范围
============================================================
扫描: knowledge-cards-prod/projects/ 下的所有知识卡文件
模式: main.json | K*.json | M_*.json
      (cards/ 下的主卡/知识卡, methods/ 下的方法论卡)
      跳过 curated/ 聚合 JSON (它的内容是 cards/ 的子集, 已被覆盖)
跳过:
  - 共同规范/工具 (autoclaw_kit 21 文件, 防御性跳过, 默认不在 projects/ 内)
  - 已有 display_target 字段的文件
  - 备份文件 (*.bak)

补全值: ["学习中心"]  (本机 = 雪薇端)

============================================================
使用
============================================================
  # 1) 预览 (不写盘)
  python tools/_add_display_target.py --dry-run

  # 2) 真实跑
  python tools/_add_display_target.py

  # 3) 回滚 (如有需要)
  git checkout -- knowledge-cards-prod/projects/
  git clean -fd knowledge-cards-prod/projects/   # 警告: 也会清掉新增文件
"""

import argparse
import json
import re
import sys
from pathlib import Path

# --- 常量 ----------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECTS_ROOT = REPO_ROOT / "knowledge-cards-prod" / "projects"

# 雪薇端产出 → 单窗口 "学习中心"
SNOWEI_DEFAULT = ["学习中心"]
# 共同规范/工具 → 空列表 (不展示) — 仅用于防御性跳过
COMMON_DEFAULT = []

# 卡片文件名模式
CARD_FILE_PATTERNS = [
    re.compile(r"^main\.json$"),
    re.compile(r"^K\d+\.json$"),
    re.compile(r"^M_.+\.json$"),
]

# 需要跳过的目录 (autoclaw_kit 21 文件, 防御性: 即便不在 projects/ 也跳过)
SKIP_PATH_PARTS = {
    "autoclaw_kit",
    "autoclaw-k",
    "_autoclaw_kit_extracted",
}

# 备份文件后缀
BACKUP_SUFFIXES = (".bak", ".bak1", ".bak2", ".orig", ".tmp", ".swp")


# --- 工具函数 ------------------------------------------------------------
def detect_indent(text: str) -> str:
    """从原始文本推断缩进 (2 空格 / 4 空格 / Tab), 默认 2 空格。"""
    for line in text.splitlines():
        stripped = line.lstrip(" \t")
        if stripped and stripped != stripped.lstrip():
            # 行首有空白, 取这部分作为缩进示例
            indent = line[: len(line) - len(stripped)]
            if "\t" in indent:
                return "\t"
            return indent
    return "  "  # 默认 2 空格


def is_card_file(path: Path) -> bool:
    """判断 path 是否为待处理的卡片文件。"""
    name = path.name
    if name.endswith(BACKUP_SUFFIXES):
        return False
    return any(p.match(name) for p in CARD_FILE_PATTERNS)


def is_skipped_path(path: Path) -> bool:
    """防御性: 路径任何一段在 SKIP_PATH_PARTS 即跳过。"""
    return any(part in SKIP_PATH_PARTS for part in path.parts)


def process_file(json_path: Path, default: list, dry_run: bool) -> str:
    """
    处理单个文件。
    返回: 'modified' | 'skipped' | 'failed'
    """
    # 必须用二进制读取, 否则 Windows 的 universal newlines 会把 CRLF → LF,
    # 导致 line ending 检测失败, 进而把原 CRLF 文件误写成 LF
    try:
        raw_bytes = json_path.read_bytes()
    except Exception as exc:
        print(f"  [ERROR] 读取失败: {json_path.relative_to(REPO_ROOT)} — {exc}")
        return "failed"

    try:
        original_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        print(f"  [ERROR] 解码失败: {json_path.relative_to(REPO_ROOT)} — {exc}")
        return "failed"

    try:
        data = json.loads(original_text)
    except json.JSONDecodeError as exc:
        print(f"  [ERROR] JSON 解析失败: {json_path.relative_to(REPO_ROOT)} — {exc}")
        return "failed"

    # 已有 display_target → 跳过
    if "display_target" in data:
        return "skipped"

    # 写入新字段
    data["display_target"] = list(default)  # 拷贝, 避免共享引用

    # 保留原文件缩进风格 + line ending + 末尾换行
    indent = detect_indent(original_text)
    # 用 raw_bytes 检测原文件 line ending (text 已被 universal newlines 规范化)
    has_crlf = b"\r\n" in raw_bytes
    newline = "\r\n" if has_crlf else "\n"
    # 用 raw_bytes 判断末尾换行 (因为 text 已经被规范化)
    has_trailing_newline = raw_bytes.endswith(b"\r\n") or raw_bytes.endswith(b"\n")

    # json.dumps 只输出 \n, 根据原 line ending 替换
    new_text = json.dumps(
        data,
        ensure_ascii=False,
        indent=indent if indent == "\t" else (indent or "  "),
    )
    if has_crlf:
        # 先归一再统一替换, 避免双重 replace 出错
        new_text = new_text.replace("\r\n", "\n").replace("\n", "\r\n")
    if has_trailing_newline:
        new_text += newline

    if dry_run:
        # 预览: 只显示将插入的字段
        print(
            f"  [DRY]   {json_path.relative_to(REPO_ROOT)}"
            f"  →  display_target = {default}"
        )
        return "modified"

    try:
        # 用二进制模式 + 显式 UTF-8 编码, 确保与原文件一致
        json_path.write_bytes(new_text.encode("utf-8"))
        return "modified"
    except Exception as exc:
        print(f"  [ERROR] 写入失败: {json_path.relative_to(REPO_ROOT)} — {exc}")
        return "failed"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="给雪薇端产出的知识卡补全 display_target 字段",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只预览, 不实际修改文件",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=PROJECTS_ROOT,
        help="扫描根目录 (默认: knowledge-cards-prod/projects/)",
    )
    parser.add_argument(
        "--default",
        type=str,
        default=json.dumps(SNOWEI_DEFAULT, ensure_ascii=False),
        help="默认 display_target 值 (默认: ['学习中心'])",
    )
    args = parser.parse_args()

    default_value = json.loads(args.default)
    if not isinstance(default_value, list):
        print(f"[ERROR] --default 必须是 JSON 数组, 收到: {args.default}", file=sys.stderr)
        return 2

    if not args.root.exists():
        print(f"[ERROR] 根目录不存在: {args.root}", file=sys.stderr)
        return 2

    print(f"扫描根目录: {args.root}")
    print(f"默认 display_target: {default_value}")
    print(f"模式: {', '.join(p.pattern for p in CARD_FILE_PATTERNS)}")
    if args.dry_run:
        print("模式: DRY-RUN (不写盘)")
    print("-" * 70)

    counts = {"modified": 0, "skipped": 0, "failed": 0, "path_skipped": 0}

    # 收集所有候选文件
    candidates = [
        p for p in args.root.rglob("*.json")
        if is_card_file(p) and not is_skipped_path(p)
    ]
    print(f"候选文件数: {len(candidates)}")
    print("-" * 70)

    for json_path in sorted(candidates):
        result = process_file(json_path, default_value, args.dry_run)
        counts[result] += 1

    print("-" * 70)
    print("汇总:")
    print(f"  modified   = {counts['modified']}")
    print(f"  skipped    = {counts['skipped']}  (已有 display_target)")
    print(f"  failed     = {counts['failed']}")
    if args.dry_run:
        print("\n[DRY-RUN 完成, 未修改任何文件]")
    else:
        print(f"\n完成。修改文件数: {counts['modified']}")

    return 0 if counts["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
