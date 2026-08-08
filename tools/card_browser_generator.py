"""
SPDT-004 知识卡片浏览器报告生成器

生成静态 HTML 文件（无需服务器，双击即可打开），支持：
  - 全库统计概览
  - 按批次 / 类型 / 领域过滤
  - front/back 全文搜索（前端 JS）
  - materials 覆盖率高亮
  - 同义标签提示

用法：
    python card_browser_generator.py [--core <core_dir>] [--out <output.html>]
"""

import json
import sys
import os
from pathlib import Path
from datetime import date

TODAY = date.today().isoformat()
CORE_ROOT = Path(__file__).parent.parent / "core"
REPORTS_DIR = Path(__file__).parent.parent / "reports"
OUT_PATH = REPORTS_DIR / "card_browser.html"


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>知识卡片库 · SPDT-004 · {today}</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
        background: #f5f5f7; color: #1d1d1f; line-height: 1.6; }}
.wrap {{ max-width: 1200px; margin: 0 auto; padding: 24px 16px; }}

/* 头部 */
header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
          color: white; padding: 32px 24px; border-radius: 16px;
          margin-bottom: 24px; }}
header h1 {{ font-size: 24px; font-weight: 600; margin-bottom: 8px; }}
header .subtitle {{ color: #a0a0b0; font-size: 14px; }}
.stats-bar {{ display: flex; gap: 24px; margin-top: 20px; flex-wrap: wrap; }}
.stat {{ background: rgba(255,255,255,0.1); border-radius: 10px;
         padding: 12px 20px; text-align: center; flex: 1; min-width: 100px; }}
.stat .num {{ font-size: 28px; font-weight: 700; }}
.stat .label {{ font-size: 12px; color: #a0a0b0; margin-top: 4px; }}

/* 过滤器 */
.filters {{ background: white; border-radius: 12px; padding: 16px 20px;
             margin-bottom: 20px; display: flex; gap: 12px; flex-wrap: wrap;
             align-items: center; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
.filters label {{ font-size: 13px; color: #666; font-weight: 500; }}
.filters select {{ padding: 6px 12px; border: 1px solid #e0e0e0; border-radius: 8px;
                  font-size: 13px; background: white; min-width: 140px; }}
.filters input#search {{ flex: 1; padding: 8px 14px; border: 1px solid #e0e0e0;
                        border-radius: 8px; font-size: 13px; min-width: 200px; }}
.filters .reset-btn {{ padding: 6px 16px; background: #f0f0f0; border: none;
                       border-radius: 8px; cursor: pointer; font-size: 13px;
                       color: #555; }}
.filters .reset-btn:hover {{ background: #e0e0e0; }}

/* 卡片 */
.card-list {{ display: flex; flex-direction: column; gap: 12px; }}
.card {{ background: white; border-radius: 12px; padding: 16px 20px;
         box-shadow: 0 1px 3px rgba(0,0,0,0.06);
         border-left: 4px solid transparent; transition: box-shadow 0.2s; }}
.card:hover {{ box-shadow: 0 4px 12px rgba(0,0,0,0.12); }}
.card.node {{ border-left-color: #3b82f6; }}
.card.strategy_cause {{ border-left-color: #f59e0b; }}
.card.strategy_impact {{ border-left-color: #10b981; }}
.card.strategy_turning {{ border-left-color: #ef4444; }}
.card.chain {{ border-left-color: #8b5cf6; }}
.card-header {{ display: flex; gap: 8px; align-items: flex-start; margin-bottom: 8px; }}
.card-id {{ font-size: 11px; color: #999; font-family: monospace; white-space: nowrap; }}
.card-type {{ font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 4px;
              color: white; }}
.type-node {{ background: #3b82f6; }}
.type-strategy_cause {{ background: #f59e0b; }}
.type-strategy_impact {{ background: #10b981; }}
.type-strategy_turning {{ background: #ef4444; }}
.type-chain {{ background: #8b5cf6; }}
.cardinality-badge {{ font-size: 10px; padding: 2px 6px; border-radius: 4px; margin-left: auto; }}
.cardinality-核心卡 {{ background: #dcfce7; color: #166534; }}
.cardinality-标准卡 {{ background: #fef9c3; color: #854d0e; }}
.cardinality-辅助卡 {{ background: #f3f4f6; color: #6b7280; }}
.card-front {{ font-size: 14px; font-weight: 600; color: #1d1d1f; margin-bottom: 6px; }}
.card-back {{ font-size: 13px; color: #444; background: #f9fafb; padding: 10px 12px;
              border-radius: 8px; margin-bottom: 8px; line-height: 1.7; }}
.card-meta {{ display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }}
.tag {{ font-size: 11px; padding: 2px 8px; background: #eef2ff; color: #4338ca;
        border-radius: 4px; }}
.concept {{ font-size: 11px; padding: 2px 8px; background: #fef3c7; color: #92400e;
            border-radius: 4px; }}
.batch {{ font-size: 11px; color: #9ca3af; margin-left: auto; }}
.card-footer {{ margin-top: 8px; border-top: 1px solid #f0f0f0; padding-top: 8px; }}
.materials-info {{ font-size: 11px; color: #9ca3af; display: flex; gap: 12px; }}
.mat-ok {{ color: #10b981; }}
.mat-empty {{ color: #fca5a5; }}

/* 无结果 */
.no-result {{ text-align: center; padding: 60px; color: #9ca3af; font-size: 15px; }}

/* 警告 */
.alert {{ background: #fef3c7; border: 1px solid #fcd34d; border-radius: 8px;
          padding: 12px 16px; margin-bottom: 16px; font-size: 13px; color: #92400e; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>📚 知识卡片库</h1>
    <div class="subtitle">SPDT-004 EduContent · {today} · 共 {total} 张卡片</div>
    <div class="stats-bar">
      {stats_html}
    </div>
  </header>

  {alert_html}

  <div class="filters">
    <label>批次:</label>
    <select id="filter-batch">
      <option value="">全部</option>
      {batch_options}
    </select>
    <label>类型:</label>
    <select id="filter-type">
      <option value="">全部</option>
      <option value="node">节点 (node)</option>
      <option value="strategy_cause">原因 (strategy_cause)</option>
      <option value="strategy_impact">影响 (strategy_impact)</option>
      <option value="strategy_turning">转折 (strategy_turning)</option>
      <option value="chain">链 (chain)</option>
    </select>
    <label>价值:</label>
    <select id="filter-cardinality">
      <option value="">全部</option>
      <option value="核心卡">核心卡</option>
      <option value="标准卡">标准卡</option>
      <option value="辅助卡">辅助卡</option>
    </select>
    <input id="search" type="text" placeholder="搜索 front / back / tags / concepts…">
    <button class="reset-btn" onclick="resetFilters()">重置</button>
  </div>

  <div id="card-list" class="card-list"></div>
</div>

<script>
const CARDS = {cards_json};
const BATCHES = {batches_json};

// 渲染
function render() {{
  const batch = document.getElementById('filter-batch').value;
  const ctype = document.getElementById('filter-type').value;
  const cardinality = document.getElementById('filter-cardinality').value;
  const kw = document.getElementById('search').value.trim().toLowerCase();

  const filtered = CARDS.filter(c => {{
    if (batch && c._batch !== batch) return false;
    if (ctype && c.type !== ctype) return false;
    if (cardinality && c._cardinality !== cardinality) return false;
    if (kw) {{
      const hay = (c.front + ' ' + c.back + ' ' + c.tags.join(' ') + ' ' + c.concepts.join(' ')).toLowerCase();
      if (!hay.includes(kw)) return false;
    }}
    return true;
  }});

  const list = document.getElementById('card-list');
  if (!filtered.length) {{
    list.innerHTML = '<div class="no-result">没有找到匹配的卡片</div>';
    return;
  }}

  list.innerHTML = filtered.map(c => `
    <div class="card ${{c.type}}">
      <div class="card-header">
        <span class="card-id">${{c.card_id}}</span>
        <span class="card-type type-${{c.type}}">${{typeLabel(c.type)}}</span>
        <span class="cardinality-badge cardinality-${{c._cardinality}}">${{c._cardinality}}</span>
      </div>
      ${{c.front ? '<div class="card-front">'+escHtml(c.front)+'</div>' : ''}}
      <div class="card-back">${{escHtml(c.back)}}</div>
      <div class="card-meta">
        ${{c.tags.slice(0,5).map(t => '<span class="tag">'+escHtml(t)+'</span>').join('')}}
        ${{c.concepts.slice(0,3).map(t => '<span class="concept">'+escHtml(t)+'</span>').join('')}}
        <span class="batch">${{c._batch}}</span>
      </div>
      <div class="card-footer">
        <div class="materials-info">
          <span class="${{c.materials.quote ? 'mat-ok' : 'mat-empty'}}">引用 ${{c.materials.quote ? '✓' : '✗'}}</span>
          <span class="${{c.materials.scene ? 'mat-ok' : 'mat-empty'}}">场景 ${{c.materials.scene ? '✓' : '✗'}}</span>
          <span class="${{c.materials.data ? 'mat-ok' : 'mat-empty'}}">数据 ${{c.materials.data ? '✓' : '✗'}}</span>
        </div>
      </div>
    </div>
  `).join('');
}}

function escHtml(s) {{
  if (!s) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}}

function typeLabel(t) {{
  const map = {{ node:'节点', strategy_cause:'原因', strategy_impact:'影响', strategy_turning:'转折', chain:'链' }};
  return map[t] || t;
}}

function resetFilters() {{
  document.getElementById('filter-batch').value = '';
  document.getElementById('filter-type').value = '';
  document.getElementById('filter-cardinality').value = '';
  document.getElementById('search').value = '';
  render();
}}

['filter-batch','filter-type','filter-cardinality','search'].forEach(id => {{
  document.getElementById(id).addEventListener('input', render);
  document.getElementById(id).addEventListener('change', render);
}});

render();
</script>
</body>
</html>
"""


def generate_html(cards: list, stats: dict) -> str:
    # 批次选项
    batches = sorted(set(c.get("_batch", "") for c in cards))
    batch_options = "\n".join(
        f'      <option value="{b}">{b}</option>' for b in batches
    )

    # 统计卡片
    type_labels = {
        "node": "节点",
        "strategy_cause": "原因",
        "strategy_impact": "影响",
        "strategy_turning": "转折",
        "chain": "链",
    }
    type_stats = stats.get("by_type", {})
    stats_html = "\n".join(
        f'      <div class="stat">'
        f'<div class="num">{type_stats.get(t, 0)}</div>'
        f'<div class="label">{type_labels.get(t, t)}</div></div>'
        for t in ("node", "strategy_cause", "strategy_impact", "strategy_turning", "chain")
    )
    card_stats = stats.get("cardinality_stats", {})
    stats_html += (
        f'\n      <div class="stat">'
        f'<div class="num">{card_stats.get("核心卡", 0)}</div>'
        f'<div class="label">核心卡</div></div>'
    )

    # materials 警告
    all_assist = stats.get("cardinality_stats", {}).get("辅助卡", 0)
    alert_html = ""
    if all_assist == len(cards):
        alert_html = (
            '<div class="alert">⚠️ 当前所有卡片均为"辅助卡"（materials 层为空）。'
            '建议按 SOP 1 补充 materials 层，以提升卡片价值等级。</div>'
        )

    # 序列化卡片数据（前端 JS）
    # 只传必要字段，避免 HTML 超大
    cards_for_js = []
    for c in cards:
        m = c.get("materials", {})
        if isinstance(m, dict):
            mat = m
        else:
            mat = {"quote": "", "scene": "", "data": ""}

        cards_for_js.append({
            "card_id": c.get("card_id", ""),
            "type": c.get("type", ""),
            "front": c.get("front", ""),
            "back": c.get("back", ""),
            "tags": c.get("tags", []),
            "concepts": c.get("concepts", []),
            "_batch": c.get("_batch", ""),
            "_cardinality": c.get("_cardinality", "辅助卡"),
            "materials": mat,
        })

    cards_json = json.dumps(cards_for_js, ensure_ascii=False)
    batches_json = json.dumps(batches)

    return HTML_TEMPLATE.format(
        today=TODAY,
        total=len(cards),
        stats_html=stats_html,
        batch_options=batch_options,
        cards_json=cards_json,
        batches_json=batches_json,
        alert_html=alert_html,
    )


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--core", default=str(CORE_ROOT))
    parser.add_argument("--out", default=str(OUT_PATH))
    args = parser.parse_args()

    # 扫描
    sys.path.insert(0, str(Path(__file__).parent))
    from import_card import scan_core, build_registry, META_DIR
    META_DIR.mkdir(exist_ok=True)

    cards, _ = scan_core()
    print(f"扫描 {args.core}：{len(cards)} 张卡片")

    # 生成报告
    registry = build_registry(cards)
    registry_path = Path(args.core) / "_meta" / "registry.json"
    registry_path.parent.mkdir(exist_ok=True)
    with open(registry_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)

    html = generate_html(cards, registry)

    out_path = Path(args.out)
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)

    print(f"报告已生成：{out_path}")
    print(f"Registry 已更新：{registry_path}")


if __name__ == "__main__":
    main()
