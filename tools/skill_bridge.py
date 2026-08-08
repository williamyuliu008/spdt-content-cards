"""
SPDT-004 写作管线串联脚本

一键执行：export_view（聚合卡片包）→ skill_selector（推荐 Skill）

用法：
    # 最简：按概念聚合并推荐 Skill
    python tools/skill_bridge.py --concepts "安史之乱,颜真卿"

    # 完整流程：聚合 → 推荐 → 生成写作计划
    python tools/skill_bridge.py --concepts "安史之乱" --context '{"chapter_position":"opening"}' --top 3

    # 链式 Skill 推荐（给定前一个 Skill）
    python tools/skill_bridge.py --concepts "藩镇割据" --previous-skill "hist-macro-micro"

输出：
    1. 写作聚合包（JSON，写入 views/writing_pool/）
    2. Skill 推荐结果（含 Layer1/2/3 评分和理由）
    3. materials 覆盖率统计（提示叙事能力）
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from datetime import date

TODAY = date.today().isoformat()
TOOLS_DIR = Path(__file__).parent
CORE_ROOT = TOOLS_DIR.parent / "core"
VIEWS_DIR = TOOLS_DIR.parent / "views" / "writing_pool"
SKILL_SELECTOR = TOOLS_DIR / "skill_selector.py"
EXPORT_SCRIPT = TOOLS_DIR / "export_view.py"


def run_python(script: Path, args: list[str]) -> str:
    """运行 Python 脚本并返回 stdout。"""
    result = subprocess.run(
        [sys.executable, str(script)] + args,
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode != 0:
        print(f"[ERROR] {' '.join(args)}")
        print(result.stderr)
        sys.exit(result.returncode)
    return result.stdout


def main():
    import argparse
    parser = argparse.ArgumentParser(description="写作管线：聚合卡片 → 推荐 Skill")
    parser.add_argument("--concepts", help="逗号分隔的概念列表")
    parser.add_argument("--tags", help="逗号分隔的标签列表")
    parser.add_argument("--previous-skill", dest="previous_skill", help="前一个 Skill ID（Layer3 语境修正）")
    parser.add_argument("--chapter-position", dest="chapter_position",
                        choices=["opening", "middle", "closing"],
                        help="章节位置（Layer3 语境修正）")
    parser.add_argument("--top", type=int, default=3, help="返回 Top N 推荐（默认3）")
    parser.add_argument("--core", default=str(CORE_ROOT))
    args = parser.parse_args()

    if not args.concepts and not args.tags:
        print("错误：必须指定 --concepts 或 --tags")
        sys.exit(1)

    # 1. 导出写作聚合包
    concepts = [x.strip() for x in args.concepts.split(",")] if args.concepts else None
    tags = [x.strip() for x in args.tags.split(",")] if args.tags else None

    safe_name = (concepts[0] if concepts else tags[0]).replace("/", "_")[:20]
    out_file = VIEWS_DIR / f"pool_{safe_name}_{TODAY}.json"
    out_file.parent.mkdir(exist_ok=True, parents=True)

    export_args = [
        "--scenario", "writing",
        "--core", args.core,
        "--out", str(out_file),
    ]
    if concepts:
        export_args += ["--concepts", ",".join(concepts)]
    if tags:
        export_args += ["--tags", ",".join(tags)]

    print("=" * 50)
    print(f"[Step 1] 导出写作聚合包")
    print("=" * 50)
    out = run_python(EXPORT_SCRIPT, export_args)
    print(out)

    # 读取导出的 JSON，获取统计信息
    with open(out_file, "r", encoding="utf-8") as f:
        pool = json.load(f)

    total = pool.get("total_cards", 0)
    mat_stats = pool.get("materials_stats", {})
    coverage = mat_stats.get("coverage_pct", {})

    # 2. 推断驱动类型
    concept_count = len(concepts) if concepts else 0
    tag_str = ",".join(tags) if tags else ""
    if "决策" in tag_str or "抉择" in tag_str or "安史" in tag_str:
        driven_type = "事件驱动型 → 建议 chain_A 或 hist-decisive-moment"
    elif "制度" in tag_str or "结构" in tag_str:
        driven_type = "结构驱动型 → 建议 chain_B 或 hist-institution-kills"
    elif "人物" in tag_str or "颜" in tag_str:
        driven_type = "人物驱动型 → 建议 chain_C 或 hist-decisive-moment"
    else:
        driven_type = "待定（Layer2 评分决定）"

    # 3. Skill 推荐
    print()
    print("=" * 50)
    print(f"[Step 2] Skill 推荐")
    print("=" * 50)

    ctx = {}
    if args.previous_skill:
        ctx["previous_skill"] = args.previous_skill
    if args.chapter_position:
        ctx["chapter_position"] = args.chapter_position

    selector_args = [str(out_file), "--top", str(args.top)]
    if ctx:
        selector_args += ["--context", json.dumps(ctx)]

    sel_out = run_python(SKILL_SELECTOR, selector_args)
    print(sel_out)

    # 4. materials 覆盖率提示
    print("=" * 50)
    print(f"[Step 3] materials 覆盖率评估")
    print("=" * 50)
    has_any_pct = coverage.get("has_any", 0)
    core_pct = coverage.get("core", 0)
    if has_any_pct < 10:
        narrative_warning = "⚠️ materials 层严重不足（<10%），叙事类 Skill 输出质量将受限，建议先补充 quotes 和 scenes。"
    elif has_any_pct < 30:
        narrative_warning = "⚠️ materials 层覆盖率偏低（<30%），叙事类 Skill 输出效果有限。"
    else:
        narrative_warning = "✅ materials 层覆盖率良好，叙事类 Skill 可正常执行。"

    print(f"  核心卡（quotes + scenes）：{core_pct}%")
    print(f"  有任意 materials：{has_any_pct}%")
    print(f"  {narrative_warning}")
    print(f"  推断驱动类型：{driven_type}")

    print()
    print("=" * 50)
    print(f"写作聚合包已保存：{out_file}")
    print("=" * 50)


if __name__ == "__main__":
    main()
