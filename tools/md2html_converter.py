# -*- coding: utf-8 -*-
"""
md2html_converter.py — 三件套 Markdown → 学习中心 HTML DATA 转换器

将各学科"三件套/*.md"文件解析为 HTML DATA 格式（body/cards/quiz）。

用法:
  python md2html_converter.py --all
  python md2html_converter.py --subject 历史
  python md2html_converter.py --subject 古诗文 英语
"""
import sys, io, re, json, argparse
from pathlib import Path
from datetime import datetime

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ============================================================
# 配置
# ============================================================
# 输出根
OUTPUT_ROOT = Path(r"D:\Z_学习平台\data\curated")

# 学科配置：源目录（"三件套"文件夹） + html_key + body_type + 状态默认值
SUBJECTS = {
    "历史":   {"src": Path(r"D:\B_历史\三件套"),   "html_key": "history",  "body_type": "叙事体",   "default_status": "已过审·三件套精写"},
    "地理":   {"src": Path(r"D:\C_地理\三件套"),   "html_key": "geography","body_type": "案例图解体","default_status": "已过审·三件套精写"},
    "政治":   {"src": Path(r"D:\D_政治\三件套"),   "html_key": "politics", "body_type": "原理解析体","default_status": "已过审·三件套精写"},
    "古诗文": {"src": Path(r"D:\E_古诗文\三件套"), "html_key": "guwen",    "body_type": "语料精讲体","default_status": "已过审·三件套精写"},
    "英语":   {"src": Path(r"D:\F_英语\三件套"),   "html_key": "english",  "body_type": "语法精讲体","default_status": "已过审·三件套精写"},
}

# ============================================================
# 文本处理工具
# ============================================================

def md_inline(s: str) -> str:
    """简单的 Markdown inline → HTML 转换（保留原意 + 转义 < >）"""
    # 转义 HTML 特殊字符（但先做 markdown 替换）
    # 1. **粗体** → <strong>...</strong>
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    # 2. *斜体* → <em>...</em>（避免与列表 * 冲突，仅匹配 "文字*" 模式）
    s = re.sub(r"(?<![*\w])\*([^*\n]+?)\*(?![*\w])", r"<em>\1</em>", s)
    # 3. `code` → <code>...</code>
    s = re.sub(r"`([^`\n]+?)`", r"<code>\1</code>", s)
    # 4. 转义 < >
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # 但要恢复我们刚生成的 <strong> <em> <code>
    s = s.replace("&lt;strong&gt;", "<strong>").replace("&lt;/strong&gt;", "</strong>")
    s = s.replace("&lt;em&gt;", "<em>").replace("&lt;/em&gt;", "</em>")
    s = s.replace("&lt;code&gt;", "<code>").replace("&lt;/code&gt;", "</code>")
    return s


def md_block(s: str) -> str:
    """Markdown block → HTML block（处理换行、引用、标题）"""
    lines = s.split("\n")
    out = []
    in_blockquote = False
    for line in lines:
        stripped = line.rstrip()
        if stripped.startswith("### "):
            if in_blockquote:
                out.append("</blockquote>")
                in_blockquote = False
            out.append(f"<h3>{md_inline(stripped[4:])}</h3>")
        elif stripped.startswith("#### "):
            if in_blockquote:
                out.append("</blockquote>")
                in_blockquote = False
            out.append(f"<h4>{md_inline(stripped[5:])}</h4>")
        elif stripped.startswith("> "):
            if not in_blockquote:
                out.append("<blockquote>")
                in_blockquote = True
            out.append(md_inline(stripped[2:]))
        elif stripped == "":
            if in_blockquote:
                out.append("</blockquote>")
                in_blockquote = False
        else:
            if in_blockquote:
                out.append("</blockquote>")
                in_blockquote = False
            out.append(md_inline(stripped))
    if in_blockquote:
        out.append("</blockquote>")
    return "\n".join(out)


# ============================================================
# 第一件 · 解析 body
# ============================================================

def extract_h1_concept(text: str) -> str:
    """从 H1 标题提取概念名：
    `# 三件套 · 科举制（主题线 2：制度与国家治理）` → 科举制
    `# 三件套 · 实词簇"过"（古诗文试产样板 1/3）` → 实词簇"过"
    """
    m = re.search(r"^#\s*三件套\s*[·．.]\s*(.+?)(?:\s*[（\(].*)?$", text, re.M)
    if m:
        return m.group(1).strip()
    # 回退：找第一个 # 标题
    m = re.search(r"^#\s+(.+?)(?:\s*[（\(].*)?$", text, re.M)
    if m:
        return m.group(1).strip().lstrip("·").strip()
    return ""


def extract_filename_concept(filepath: Path) -> str:
    """从文件名提取概念名：
    `2026-0815_三件套-科举制.md` → 科举制
    """
    name = filepath.stem  # 不含扩展名
    m = re.search(r"三件套[--](.+)$", name)
    if m:
        return m.group(1).strip()
    return name


def extract_status(text: str, default: str) -> str:
    """从开头引用块提取状态
    `> 状态：试产样板` → 试产样板
    `> 状态：修订版（待审核入库）` → 修订版（待审核入库）
    `> 状态：**试产样板**（史实审核未完成...）` → 试产样板
    """
    # 找第一个引用块
    m = re.search(r"^>\s*状态[：:]\s*(.+)$", text, re.M)
    if m:
        s = m.group(1).strip()
        # 去掉 **xxx** 标记
        s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
        # 去掉第一个括号之前的内容（如 `试产样板（存疑清单见文末）` → 试产样板）
        s = re.sub(r"^([^（(]+?)[（(].*$", r"\1", s).strip()
        if s:
            return f"{default}（{s}）"
    return default


def extract_production_date(text: str) -> str:
    """提取生产日期"""
    m = re.search(r"生产日期[：:]\s*(\d{4}-\d{2}-\d{2})", text)
    if m:
        return m.group(1)
    return ""


def parse_body(text: str, first_section_name: str = "正文") -> list:
    """解析"## 第一件"section → body[]
    
    策略：提取 H2 后到下一个 H2/--- 之间的所有非空段落，按空行分块。
    第一个 block 是 lead:true。
    处理：
    - ### 小标题 → <h3>
    - **粗体** → <strong>
    - > 引用 → <blockquote>
    """
    # 找第一件 section
    m = re.search(r"^##\s*第一件[^\n]*\n(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    if not m:
        return []
    section = m.group(1).strip()
    # 去掉 --- 分隔线
    section = re.sub(r"^---\s*$", "", section, flags=re.M)
    # 去掉最后可能的 ---
    section = re.sub(r"---\s*$", "", section).strip()
    
    # 按空行分块（每个 block 是一个段落或一个标题）
    blocks = re.split(r"\n\s*\n", section)
    blocks = [b.strip() for b in blocks if b.strip()]
    
    body = []
    for i, block in enumerate(blocks):
        is_lead = (i == 0)
        # 处理 block 内的换行：在 paragraph 内 <br>
        html = md_block(block)
        # 保留换行
        html = html.replace("\n", "<br>")
        body.append({"lead": is_lead, "text": html})
    return body


# ============================================================
# 第二件 · 解析 cards
# ============================================================

def parse_table_row(line: str) -> list:
    """解析 markdown 表格行 → cell 列表"""
    # 去掉首尾 |
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    cells = [c.strip() for c in s.split("|")]
    return cells


def is_separator_row(line: str) -> bool:
    """是否是表格分隔行 `|---|---|`"""
    s = line.strip()
    cells = parse_table_row(s) if "|" in s else []
    return all(re.match(r"^:?-+:?$", c) for c in cells if c)


def parse_cards(text: str) -> tuple:
    """解析"## 第二件"section → (cards[], headers[])
    
    解析 markdown 表格，第一行表头，后续行数据。
    去掉第一列 #，用行号代替。
    返回 (cards, headers)
    """
    m = re.search(r"^##\s*第二件[^\n]*\n(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    if not m:
        return [], []
    section = m.group(1).strip()
    
    # 找表格行
    lines = section.split("\n")
    table_lines = [l for l in lines if l.strip().startswith("|")]
    if len(table_lines) < 2:
        return [], []
    
    # 解析表头
    headers = parse_table_row(table_lines[0])
    # 跳过分隔行
    data_lines = [l for l in table_lines[1:] if not is_separator_row(l)]
    
    cards = []
    for idx, line in enumerate(data_lines, 1):
        cells = parse_table_row(line)
        # 处理每个 cell 的 markdown
        cells = [md_inline(c) for c in cells]
        # 第一列如果是 # 号（可能是 N 或名称），保留
        # 但用 idx 作为编号（更稳定）
        if cells:
            cells[0] = str(idx)
        cards.append(cells)
    
    return cards, headers


# ============================================================
# 第三件 · 解析 quiz
# ============================================================

def parse_quiz(text: str) -> list:
    """解析"## 第三件"section → quiz[]
    
    每道题以 `### 题 N · xxx` 开始，包含 `> ` 行（题面 + 答案）。
    """
    m = re.search(r"^##\s*第三件[^\n]*\n(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    if not m:
        return []
    section = m.group(1).strip()
    
    # 按 ### 题 N 切分
    parts = re.split(r"^###\s*题\s*\d+\s*[·．.]?\s*", section, flags=re.M)
    quiz = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # 第一行是类型（如 "语法填空（考点 3，头号易混）"）
        # 后面是 > 开头的引用块
        lines = part.split("\n")
        # 类型行：第一行（非空、非 > 开头）
        type_line = ""
        content_start = 0
        for i, l in enumerate(lines):
            s = l.strip()
            if s and not s.startswith(">"):
                type_line = s
                content_start = i + 1
                break
        
        # 收集 > 开头的行
        content_lines = []
        for l in lines[content_start:]:
            s = l.strip()
            if s.startswith("> "):
                content_lines.append(s[2:])
            elif s.startswith(">"):
                content_lines.append(s[1:].lstrip())
            elif s == "":
                content_lines.append("")
            else:
                # 非 > 行（可能是落选的）
                continue
        content = "\n".join(content_lines).strip()
        
        # 分离题面和答案
        # 三件套的答案标记有多种形式：
        #   `**答案：B**` （单选/判断/填空，答案简短）
        #   `**参考答案**：...` （翻译/简答，答案+解析）
        #   `**参考断句**：...` + `**评分标准**：...` （断句题，多段答案）
        # 策略：找第一个以"答案/参考"开头的加粗标签，把它及之后的内容作为 ans
        ans_match = re.search(
            r"\*\*(?:答案|参考答案|答案与解析|参考断句|参考译文|翻译|得分要点|答案要点|解析)\s*[:：][^*]*\*\*",
            content
        )
        if ans_match:
            # 答案标记之前是题面（去掉末尾可能残留的换行）
            body = content[:ans_match.start()].rstrip()
            # 答案标记及之后的所有内容（包括后续的 **评分标准**、**拆解** 等）
            ans = content[ans_match.start():].strip()
        else:
            body = content
            ans = ""
        
        # 答案中转义 **
        ans = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", ans)
        # body 中也转义
        body = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", body)
        # 转 < >
        body = body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        body = re.sub(r"&lt;strong&gt;", "<strong>", body).replace("&lt;/strong&gt;", "</strong>")
        ans = ans.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        ans = re.sub(r"&lt;strong&gt;", "<strong>", ans).replace("&lt;/strong&gt;", "</strong>")
        # 换行保留
        body = body.replace("\n", "<br>")
        ans = ans.replace("\n", "<br>")
        
        quiz.append({
            "type": type_line,
            "body": body,
            "ans": ans
        })
    return quiz


# ============================================================
# 主解析函数
# ============================================================

def parse_md(filepath: Path, subject_cfg: dict) -> dict | None:
    """解析单个 .md 文件 → DATA 条目"""
    try:
        text = filepath.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  [SKIP] {filepath.name}: {e}")
        return None
    
    # 概念名：H1 优先，文件名回退
    concept_name = extract_h1_concept(text)
    if not concept_name:
        concept_name = extract_filename_concept(filepath)
    if not concept_name:
        print(f"  [WARN] {filepath.name}: 无法提取概念名")
        return None
    
    # 状态
    production_date = extract_production_date(text)
    status = extract_status(text, subject_cfg["default_status"])
    if production_date:
        status = f"{status}（{production_date}）"
    
    # 解析三件
    body = parse_body(text)
    cards, headers = parse_cards(text)
    quiz = parse_quiz(text)
    
    return {
        "concept_name": concept_name,
        "data": {
            "status": status,
            "tags": {
                "type": subject_cfg["body_type"],
                "headers": headers,
                "source": "三件套精写"
            },
            "body": body,
            "cards": cards,
            "quiz": quiz
        }
    }


# ============================================================
# 输出 JS
# ============================================================

def js_escape(s: str) -> str:
    """转义 JS 字符串中的特殊字符"""
    s = s.replace("\\", "\\\\")
    s = s.replace("'", "\\'")
    s = s.replace("\n", "\\n")
    s = s.replace("\r", "")
    return s


def format_body(body_list: list) -> str:
    parts = []
    for p in body_list:
        lead = "true" if p["lead"] else "false"
        parts.append(f"  {{ lead:{lead},text:'{js_escape(p['text'])}' }}")
    return ",\n".join(parts)


def format_cards(cards_list: list) -> str:
    parts = []
    for c in cards_list:
        cells = [f"'{js_escape(cell)}'" for cell in c]
        parts.append(f"  [{','.join(cells)}]")
    return ",\n".join(parts)


def format_quiz(quiz_list: list) -> str:
    parts = []
    for q in quiz_list:
        parts.append(f"  {{ type:'{js_escape(q['type'])}', body:'{js_escape(q['body'])}', ans:'{js_escape(q['ans'])}' }}")
    return ",\n".join(parts)


def generate_js(subject_zh: str, html_key: str, concepts: list) -> str:
    """生成完整 JS 代码段"""
    lines = []
    lines.append(f"/* ---------- {subject_zh} 三件套精写（md2html_converter.py） ---------- */")
    lines.append(f"/* 加载顺序：在 generated 之后加载，覆盖同名 key */")
    for c in concepts:
        cn = c["concept_name"]
        d = c["data"]
        headers = d["tags"].get("headers", [])
        body_type = d["tags"].get("type", "")
        source = d["tags"].get("source", "")
        headers_js = json.dumps(headers, ensure_ascii=False)
        lines.append(f"DATA.{html_key}['{js_escape(cn)}'] = {{")
        lines.append(f"  status:'{js_escape(d['status'])}',")
        lines.append(f"  tags:{{ type:'{js_escape(body_type)}', headers:{headers_js}, source:'{js_escape(source)}' }},")
        lines.append(f"  body:[")
        lines.append(format_body(d["body"]))
        lines.append(f"  ],")
        lines.append(f"  cards:[")
        lines.append(format_cards(d["cards"]))
        lines.append(f"  ],")
        lines.append(f"  quiz:[")
        lines.append(format_quiz(d["quiz"]))
        lines.append(f"  ]")
        lines.append(f"}};")
    return "\n".join(lines)


# ============================================================
# 入口
# ============================================================

def process_subject(subject_zh: str) -> int:
    """处理一个学科的所有三件套"""
    cfg = SUBJECTS[subject_zh]
    src_dir = cfg["src"]
    if not src_dir.exists():
        print(f"[{subject_zh}] 源目录不存在: {src_dir}")
        return 0
    
    md_files = sorted(src_dir.glob("*.md"))
    print(f"[{subject_zh}] 发现 {len(md_files)} 个三件套 .md")
    
    concepts = []
    for f in md_files:
        result = parse_md(f, cfg)
        if result:
            concepts.append(result)
            print(f"  [OK] {result['concept_name']}  (body={len(result['data']['body'])}, cards={len(result['data']['cards'])}, quiz={len(result['data']['quiz'])})")
    
    if not concepts:
        print(f"[{subject_zh}] 无有效三件套")
        return 0
    
    # 输出
    output_path = OUTPUT_ROOT / f"{cfg['html_key']}_curated.js"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    js_code = generate_js(subject_zh, cfg["html_key"], concepts)
    output_path.write_text(js_code, encoding="utf-8")
    print(f"[{subject_zh}] 输出: {output_path}  ({len(js_code)} 字节, {len(concepts)} 条)")
    return len(concepts)


def main():
    parser = argparse.ArgumentParser(description="三件套 Markdown → 学习中心 HTML DATA 转换器")
    parser.add_argument("--all", action="store_true", help="处理全部学科")
    parser.add_argument("--subject", nargs="+", choices=list(SUBJECTS.keys()), help="指定学科")
    args = parser.parse_args()
    
    if args.all:
        subjects = list(SUBJECTS.keys())
    elif args.subject:
        subjects = args.subject
    else:
        parser.print_help()
        return
    
    total = 0
    for s in subjects:
        total += process_subject(s)
    
    print(f"\n[完成] 共处理 {total} 条三件套")


if __name__ == "__main__":
    main()
