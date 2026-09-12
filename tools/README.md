# tools/

雪薇端开发 / 维护脚本目录。所有脚本假定从仓库根目录调用。

---

## 索引

| 脚本 | 用途 | 备注 |
|---|---|---|
| `_add_display_target.py` | 给雪薇端产出的知识卡批量补全 `display_target: ["学习中心"]` 字段 | v1.0 协作基线 (commit 543c7d5) 要求 display_target 必填 |
| `json2html_converter.py` | 知识卡 JSON → 学习中心 HTML | — |
| `md2html_converter.py` | Markdown → 学习中心 HTML | — |
| `md_math_converter.py` | 含数学公式的 Markdown → HTML | — |
| `make_global_climate_v2.py` | 生成《全球气候变化》专题 v2 | — |
| `upgrade_v1_cards.py` | 知识卡 v0.x → v1.x 升级脚本 | — |
| `json2html_converter.legacy.py` | 旧版 JSON→HTML 转换器 | 保留以便回滚 |

---

## `_add_display_target.py`

### 背景

v1.0 协作基线拍板 `display_target` 字段为**必填** (commit `543c7d5`)。该字段决定卡片在哪个窗口展示:

| 值 | 含义 |
|---|---|
| `["学习中心"]` | 雪薇端产出, 仅学习中心窗口 |
| `["RUJING"]` | 宇兄端产出, 仅 RUJING 窗口 |
| `["学习中心", "RUJING"]` | 共同仓通用, 双窗口 |
| `[]` | 共同规范/工具, 不展示 (如 `autoclaw_kit`) |

**v1.0/v1.1 时代产出** (历史内容) 由系统默认按 `['学习中心', 'RUJING']` 双展示, 不需要主动打标。本脚本只处理**新内容**——给"明确属于某一窗口"的卡片补全字段。

### 范围

- **扫描根目录**: `knowledge-cards-prod/projects/`
- **匹配文件**: `main.json` / `K*.json` / `M_*.json`
  - `main.json` + `K*.json` → `cards/` 下的主卡 / 知识卡
  - `M_*.json` → `methods/` 下的方法论卡 (政治 5 + 数学 30)
- **跳过**:
  - `curated/*.json` (聚合文件, 内容是 `cards/` 子集, 已被覆盖)
  - 路径含 `autoclaw_kit` / `autoclaw-k` / `_autoclaw_kit_extracted` (防御性, 默认不在 projects/ 内)
  - 已有 `display_target` 字段的文件
  - `*.bak` / `*.orig` / `*.tmp` / `*.swp` 备份文件

### 补全值

本机为雪薇端, 补全值固定为 `["学习中心"]`。

### 使用

```bash
# 1) 预览 (不写盘)
python tools/_add_display_target.py --dry-run

# 2) 真实跑
python tools/_add_display_target.py

# 3) 回滚 (如有需要)
git checkout -- knowledge-cards-prod/projects/
```

### 风险与回滚

- 本脚本会批量修改数百至上千个 JSON 文件, **必须** 先 `--dry-run` 确认。
- 所有修改已纳入 git, 任意时刻可 `git checkout -- knowledge-cards-prod/projects/` 回滚。
- 脚本只在**文件无 `display_target` 字段时**才追加, 不会覆盖已有值, 二次运行是安全的 (第二次会全部 skipped)。

### 关键逻辑

```python
data = json.loads(json_path.read_text(encoding='utf-8'))
if 'display_target' not in data:
    data['display_target'] = ['学习中心']
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=原缩进), encoding='utf-8')
```

- 保留原文件缩进风格 (2 空格 / 4 空格 / Tab)
- 保留原文件末尾换行
- `display_target` 追加到 JSON 对象末尾 (Python 3.7+ 保证 dict 插入顺序)

---

## 调用约定

- 脚本入口统一为 `if __name__ == "__main__":`, 可直接 `python tools/<script>.py` 跑
- 路径统一基于 `Path(__file__).resolve().parent.parent` 解析仓库根
- 编码统一 `utf-8`
- 临时 / 调试脚本以 `_` 前缀标记 (如 `_add_display_target.py`)
