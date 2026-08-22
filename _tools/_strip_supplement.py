# -*- coding: utf-8 -*-
"""
_strip_supplement.py — 清洗 autoclaw 端 back_detail 末尾的重复污染

污染形态（autoclaw 端 LLM repetition loop）：
  "补充说明：本考点在近三年上海等级考中属高频内容，复习时务必结合{案例|史实}与辨析要点。"
  "补充说明：本考点在近三年上海等级考中属高频内容，复习时务必结合史实与辨析要点，做到以史实立论、以方法释史。"

仅清洗上述 2 个 regex，不影响其他 "补充说明：..." 模式（政治学科真实补充说明要保留）。

用法：
  python -X utf8 _strip_supplement.py [--dry-run] [--dir <git_kb_root>]

默认扫描 D:/4_data/knowledge_cards/{历史,地理,政治}/cards 下所有 */*.json
"""
import io, json, re, sys, argparse
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# 核心污染 marker：autoclaw 端 LLM 重复模板
# 模式 A/B/C: 模式 A (案例与辨析) / 模式 B (史实与辨析) / 模式 C (长版) 全部含 "本考点在近三年上海等级考中属高频内容"
RE_POLLUTION = re.compile(
    r'[\r\n]*补充说明[：:].*?本考点在近三年上海等级考中属高频内容.*?[。]\s*',
    re.DOTALL
)
# 模式 C' 尾巴：旧 regex 漏的短版尾巴
RE_TAIL = re.compile(
    r'[\r\n]*这一历史考点在专题框架中占有重要位置。\s*'
)
# 模式 D/E/F (v1.0.3): 政治学科真实补充说明 - 现按用户实际体验升级为污染
# 涵盖 "本考点常以..." / "复习时要把..." / "答题框架..." / "注意区分主体..." 等所有 "补充说明：..." 开头段
# 策略: 检测 "补充说明：..." 任意内容后接换行或 2+ 段堆叠则清; 单独一段若不含具体考点也清
RE_POLITICAL_SUPPLEMENT = re.compile(
    r'[\r\n]*补充说明[：:][^。\n]{0,150}[。][\s]*',
    re.DOTALL
)

def clean_text(text: str) -> tuple[str, int]:
    """返回 (cleaned_text, n_stripped)"""
    if not text:
        return text, 0
    n = 0
    # 模式 A/B/C (上海高考套话)
    new_text, c1 = RE_POLLUTION.subn('', text)
    n += c1
    # 模式 C' 尾巴
    new_text, c2 = RE_TAIL.subn('', new_text)
    n += c2
    # 模式 D/E/F (政治学科"补充说明：..."所有变体) - v1.0.3 升级为污染
    new_text, c3 = RE_POLITICAL_SUPPLEMENT.subn('', new_text)
    n += c3
    return new_text, n

def process_file(path: Path, dry_run: bool = True) -> dict:
    """处理单个 JSON 文件，返回 {cleaned, n, fields}"""
    try:
        raw = path.read_text(encoding='utf-8')
    except Exception as e:
        return {'error': str(e)}

    try:
        data = json.loads(raw)
    except Exception as e:
        return {'error': f'JSON parse: {e}'}

    n_total = 0
    fields = ['back_detail']
    # main 卡 + sub 卡都处理
    for field in fields:
        if field in data and isinstance(data[field], str):
            cleaned, n = clean_text(data[field])
            n_total += n
            data[field] = cleaned

    if n_total > 0 and not dry_run:
        # 写回原文件（无 BOM）
        new_raw = json.dumps(data, ensure_ascii=False, indent=2)
        path.write_text(new_raw, encoding='utf-8')

    return {'cleaned': n_total > 0, 'n': n_total, 'fields': fields}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='只扫描不写（默认 execute）')
    parser.add_argument('--dir', type=Path, default=Path(r'D:\4_data\knowledge_cards'),
                        help='git 知识库根目录')
    args = parser.parse_args()

    # 扫描 3 个学科 cards 目录
    subjects = ['历史', '地理', '政治']
    all_json = []
    for subj in subjects:
        subj_dir = args.dir / subj / 'cards'
        if subj_dir.exists():
            for p in subj_dir.rglob('*.json'):
                if p.name in ('chain.json', 'main.json') or re.match(r'^K\d+\.json$', p.name):
                    all_json.append(p)

    print(f'扫描 {len(all_json)} 个 JSON 文件 ({", ".join(subjects)})')
    print(f'模式: {"DRY-RUN" if args.dry_run else "EXECUTE"}')
    print()

    stats = {'total': len(all_json), 'files_cleaned': 0, 'strip_total': 0}
    by_subject = {s: {'files': 0, 'strip': 0} for s in subjects}

    for p in all_json:
        result = process_file(p, dry_run=args.dry_run)
        if 'error' in result:
            print(f'  ❌ {p.relative_to(args.dir)}: {result["error"]}')
            continue
        if result.get('cleaned'):
            stats['files_cleaned'] += 1
            stats['strip_total'] += result['n']
            # 找学科
            subj = p.parts[-4] if len(p.parts) >= 4 else '?'
            if subj in by_subject:
                by_subject[subj]['files'] += 1
                by_subject[subj]['strip'] += result['n']
            if not args.dry_run:
                print(f'  ✓ {p.relative_to(args.dir)}: {result["n"]} 处清洗')

    print()
    print('=' * 50)
    print(f'总文件: {stats["total"]} | 清洗文件: {stats["files_cleaned"]} | 总清洗处: {stats["strip_total"]}')
    print('--- 按学科 ---')
    for s, v in by_subject.items():
        print(f'  {s}: {v["files"]} 文件 / {v["strip"]} 处')
    print()
    if args.dry_run:
        print('⚠️  DRY-RUN 模式，未写文件。加 --execute 实际写回。')
    else:
        print('✅ 已写回原文件。')

    return 0

if __name__ == '__main__':
    sys.exit(main())
