# 知识卡片 v1.0 规范

> 本规范是 autoclaw 端产出卡片必须遵守的硬性要求。
> 配合 `07_validate.py` 自动校验：20 项硬指标 + 10 项自检。
> 校验失败的卡片**不会被 rujing 接收**。

---

## §0 目录结构

每套卡片 = 1 目录，命名 `YYYY-MM-DD_概念名`：

```
地理/cards/
└── 2026-08-16_热力环流与风/    ← 1 套 = 1 目录
    ├── chain.json                ← 链元数据（必需，1 个）
    ├── main.json                 ← 主卡（必需，1 个）
    ├── K01.json                  ← 子卡 1（必需）
    ├── K02.json                  ← 子卡 2
    ├── ...                       
    └── K08.json                  ← 子卡 N（6 ≤ N ≤ 10）
```

**规则**：
- 每套 = 1 主卡 + 6-10 子卡（子卡 6-10 张）
- 目录名 `YYYY-MM-DD_概念名` 中的 `概念名` 必须与 `chain.json` 的 `chain_id` 末尾概念名一致
- 文件名禁止含中文标点 `：；，。！？（）《》【】、`

---

## §1 chain.json 字段（链元数据）

### §1.1 必填字段

```json
{
  "chain_id":      "geography/G-P1-2-热力环流与风",
  "chain_title":   "热力环流与风",
  "subject":       "GEOGRAPHY",
  "chain_type":    "因果链",
  "domain":        "自然地理·大气与气候",
  "lines":         ["大气受热", "热力环流"],
  "module":        "模块一·自然地理基础",
  "topic":         "专题1 大气与气候",
  "is_main_line":  true,
  "total_cards":   9,
  "generated_at":  "2026-08-16",
  "generated_by":  "autoclaw-v1.0",
  "status":        "trial_production",
  "open_questions_count": 3,
  "exam_questions_count": 5
}
```

### §1.2 字段约束

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `chain_id` | string | 格式 `<domain>/<subj>-M<mod>-<idx>-<name>` | 详见 04_chain_id_naming.md |
| `chain_title` | string | 中文，2-30 字 | 用于 APP 显示 |
| `subject` | string | 必填下列之一 | `HISTORY` / `GEOGRAPHY` / `POLITICS` / `GUWEN` / `CALLIGRAPHY` / `ENGLISH` |
| `chain_type` | string | 必填下列之一 | `因果链` / `时序链` / `对比链` / `要素链` / `理论运用链` |
| `domain` | string | 学科域，如 `自然地理·大气与气候` | 自由文本 |
| `lines` | string[] | 2-4 个主线条标签 | 用于 APP 跨链检索 |
| `module` | string | 学科内大单元 | 自由文本 |
| `topic` | string | 模块内小节 | 自由文本 |
| `is_main_line` | boolean | 主线条 / 辅助线 | true/false |
| `total_cards` | int | = 实际 K 卡数 + 1（主卡）| 自动校对 |
| `generated_at` | string | `YYYY-MM-DD` | = 目录名日期部分 |
| `generated_by` | string | 必填 | 标识作者/系统 |
| `status` | string | `trial_production`（试产）/ `done`（定稿）| trial_production 会被校验标 WARN |
| `open_questions_count` | int | = main.json 的 `open_questions` 数组长度 | 自动校对 |
| `exam_questions_count` | int | = main.json 的 `exam_questions` 数组长度 | 自动校对 |

### §1.3 chain_id 格式详解

```
geography/G-P1-2-热力环流与风
└──┘ └────────┬──────┘ └──┬──┘
domain      短链 ID      name
```

- `geography` = 学科目录名（小写英文）
- `G` = 学科首字母大写（与 subject 映射）
- `M1` = 模块 1
- `2` = 概念号（模块内编号）
- `热力环流与风` = 概念名

详见 `04_chain_id_naming.md`。

---

## §2 main.json 字段（主卡 = 链长文 + 自测题 source）

### §2.1 主卡结构

```json
{
  "card_id":         "G-M1-2-MAIN-001",
  "card_type":       "STRATEGY",
  "chain_role":      "BACKGROUND",
  "maturity":        "RAW",
  "front":           "热力环流的形成机制是什么？",
  "back_core":       "地面冷热不均→空气垂直运动→同一水平面气压差→空气水平运动（风）。核心是热力差异驱动气压梯度力。",
  "back_detail":     "（800-1200 字长文，会升为 chain.article）",
  "concepts":        ["热力环流", "气压梯度力", "水平气压梯度", ...],
  "tags":            ["#domain/自然地理", "#content/热力环流", "#考频/★★★", "#朝代/现代"],
  "sources":         [
    {"type": "academic", "source": "《大气科学》", "detail": "第3章", "url": ""}
  ],
  "exam_questions":  [
    {"qid": "Q1", "type": "单选", "question": "...", "options": ["A", "B", "C", "D"], "answer": "B", "explanation": "..."}
  ],
  "open_questions":  ["城市热岛对局地环流的影响？", "海陆风季风差异？"],
  "confidence":      "high"
}
```

### §2.2 字段约束

| 字段 | 类型 | 约束 | 校验 |
|------|------|------|------|
| `card_id` | string | `<SUBJ>-M<mod>-<idx>-MAIN-001` | 正则 |
| `card_type` | string | `STRATEGY` / `BIG_PICTURE` / `METHODOLOGY` / `CASE_STUDY` / `PARADOX` | enum |
| `chain_role` | string | `BACKGROUND` / `TRIGGER` / `PROCESS` / `RESULT` / `COUNTER` / `PATTERN` | enum |
| `maturity` | string | 必填 `RAW` | 强校验 |
| `front` | string | 30-100 字（去空白），以 `？` 结尾 | 长度 + 标点 |
| `back_core` | string | 150-250 字（去空白） | 长度 |
| `back_detail` | string | **800-1200 字**（去空白） | 长度（**重要：长文 source**）+ **末尾禁重复模板**（见 §2.3）|
| `concepts` | string[] | **5-8 个**概念，正文须出现 | 数量 + 弱检查 |
| `tags` | string[] | 必含 `#domain/` `#content/` `#考频/` `#朝代/` 四类 | 必含 |
| `sources` | Source[] | **3-8 条**，至少 1 条 `type=academic` | 数量 + 类型 |
| `exam_questions` | ExamQ[] | **5-6 道**，必含 5 类题型 | 数量 + 题型 |
| `open_questions` | string[] | **5-10 条**，每条 ≤ 50 字 | 数量 + 长度 |
| `confidence` | string | `high` / `medium` / `low` | enum + 自校 |

### §2.3 back_detail 末尾禁重复模板（**硬规则 · 重要**）

**禁止在 `back_detail` 末尾（或任何位置）出现以下重复模板**（autoclaw 端 LLM 已知问题）：

| 模式 | 形态 |
|---|---|
| 模式 A | `补充说明：本考点在近三年上海等级考中属高频内容，复习时务必结合{案例\|史实}与辨析要点。` |
| 模式 B | `补充说明：本考点在近三年上海等级考中属高频内容，复习时务必结合史实与辨析要点，做到以史实立论、以方法释史。` |
| 模式 C 短 | `补充说明：本考点在近三年上海等级考中属高频内容，复习时务必结合史实与辨析要点。这一历史考点在专题框架中占有重要位置。` |

**核验**：
- 任意 `back_detail` 字段值如匹配上述任一模式 → **ERR**（PC 端 `_validate_cards.py` 自动检测）
- 强制清洗工具：`python _tools/_strip_supplement.py` （已写，991 文件 / 2662 处实测）

**autoclaw 端 prompt 必须显式禁止 LLM 输出"补充说明：本考点在近三年..."等重复模板**。可在 prompt 加：
> "back_detail 末尾禁止添加'补充说明：'开头的总结句。如果内容需要总结，应在前文'⚠️ 易错点'段后直接收尾，不要再额外加段落。"

### §2.4 题型必含

`exam_questions` 数组必须包含 5 类题型（缺一即 ERR）：

| type | 数量 | 说明 |
|------|------|------|
| `单选` | 至少 1 道 | 4 选项 |
| `配对` | 至少 1 道 | 2 列匹配 |
| `图表排序` | 至少 1 道 | 流程/时间/逻辑 |
| `材料解析` | 至少 1 道 | 给材料 + 答 |
| `开放论述` | 至少 1 道 | 答案必含 `1~3` + `4~6` + `7~8` 三层给分 |

### §2.5 open_questions 自校

```
algo_confidence = "high" if len(open_questions)==0
                = "medium" if len(open_questions)<=3
                = "low" if len(open_questions)>=4
```

如果 `confidence` 与 algo 不一致 → WARN。

### §2.6 Source 字段

```json
{
  "type":   "academic" | "textbook" | "website" | "video" | "other",
  "source": "资料名（书名/网站名/视频标题）",
  "detail": "章节/页码/URL 描述",
  "url":    "可选 URL"
}
```

---

## §3 K0X.json 字段（子卡 = 知识点卡）

### §3.1 子卡结构

```json
{
  "card_id":     "G-M1-2-K01-001",
  "card_type":   "KNOWLEDGE",
  "chain_role":  "TRIGGER",
  "maturity":    "RAW",
  "front":       "什么是气压梯度力？",
  "back_core":   "气压梯度力是促使空气从高压流向低压的力，大小与水平气压梯度成正比，方向垂直等压线由高压指向低压。",
  "back_detail": "（200-350 字精简版）",
  "concepts":    ["气压梯度力", "水平气压梯度", "高压", "低压"],
  "tags":        ["#domain/自然地理", "#content/气压梯度力", "#考频/★★", "#朝代/现代"],
  "sources":     [
    {"type": "academic", "source": "《大气科学》", "detail": "P23", "url": ""}
  ],
  "parent_card": "G-M1-2-MAIN-001",
  "confidence":  "high"
}
```

### §3.2 字段约束

| 字段 | 类型 | 约束 |
|------|------|------|
| `card_id` | string | `<SUBJ>-M<mod>-<idx>-K<XX>-001`（XX = 01-10） |
| `card_type` | string | `KNOWLEDGE`（最常见） / 其他 5 种 |
| `chain_role` | string | 6 种之一，可与主卡不同 |
| `maturity` | string | 必填 `RAW` |
| `front` | string | 30-100 字，以 `？` 结尾 |
| `back_core` | string | 150-250 字 |
| `back_detail` | string | **200-350 字**（子卡精简版）|
| `concepts` | string[] | **3-5 个**，正文须出现 |
| `tags` | string[] | 必含 `#domain/` `#content/` `#考频/` 三类（朝代可选）|
| `sources` | Source[] | **1-3 条**（子卡比主卡少）|
| `parent_card` | string | **必填** = main.json 的 `card_id` |
| `confidence` | string | 3 选 1 |

### §3.3 子卡与主卡的关系

- 子卡是主卡的**支点**（trigger / background / process / counter / pattern）
- 6-10 张子卡覆盖主卡**长文的不同侧面**
- 子卡背靠背（back_to_back）不重复主卡内容
- 子卡的 `chain_role` 应该与主卡互补

### §3.4 角色组合建议

| 主卡 chain_role | 子卡 chain_role 建议 |
|------------------|----------------------|
| `BACKGROUND` | `TRIGGER` `PROCESS` `COUNTER` `PATTERN` |
| `TRIGGER` | `BACKGROUND` `PROCESS` `RESULT` `COUNTER` |
| `PROCESS` | `BACKGROUND` `TRIGGER` `RESULT` `PATTERN` |

**不要 6 张子卡都用同一角色**（如全 `PROCESS`）—— 这是把长文线性切 6 段，不是真正的子卡。

---

## §4 tags 必含规则

每张卡片的 `tags` 数组**必须包含**：

| 必含 tag | 例子 | 说明 |
|----------|------|------|
| `#domain/<学科域>` | `#domain/自然地理` | 学科下的大类 |
| `#content/<小主题>` | `#content/热力环流` | 卡片讨论的具体小主题 |
| `#考频/<星级>` | `#考频/★★★` | ★★★ = 高频（5 年内 5+ 次）/ ★★ = 中频 / ★ = 低频 |
| `#朝代/<时代>` | `#朝代/现代` 或 `#朝代/无` | 历史/古诗文必填；其他学科填 `#朝代/无` 或省略 |

可选 tag：
- `#source/<出处>`：标注特别重要的来源
- `#level/<难度>`：`#level/基础` / `#level/进阶` / `#level/高阶`

---

## §5 时间表述规范

**禁止用相对时间表述**（校验会标 ERR）：

```
同一时期 / 与此同时 / 不久后 / 同时期 / 同时代
```

**改写方式**：
- 用绝对年份：`1861 年` / `1905 年`
- 用朝代纪年：`咸丰元年` / `光绪二十六年`
- 用世纪：`19 世纪中叶`

软警告（需人工确认）：`同时`

---

## §6 6 步质量自检（人工）

每套卡产出后，autoclaw 操作员**必须**人工过这 6 步：

| 步 | 检查 | 工具 |
|----|------|------|
| 1 | front 是否问号结尾 | 看 |
| 2 | back_core 字数 150-250 | `len(text)` |
| 3 | back_detail 字数 800-1200（主）/ 200-350（子）| `len(text)` |
| 4 | 5 个必含 tag 都有 | 看 |
| 5 | sources 至少 3-8 条（主）/ 1-3 条（子）| `len(sources)` |
| 6 | exam_questions 5-6 道，5 类题型齐全 | 看 |

---

## §7 校验脚本（07_validate.py）

```bash
python -X utf8 autoclaw_kit/07_validate.py 地理/cards/2026-08-16_热力环流与风
```

**输出**：
- 退出码 0 = 全过
- 退出码 1 = 有 ERROR
- 退出码 2 = 只有 WARN

**自动校验 20 项硬指标**（`07_validate.py` 内置）：
1. 目录名格式
2. chain.json 字段完整
3. chain_id 格式
4. chain_id 概念名 = 目录名概念名
5. chain_id 在 _N_concepts.json 清单（如提供）
6. chain 概念元数据（lines/star/module/topic）与清单一致
7. main card_id 格式
8. K0X card_id 格式
9. K0X card_id 序号匹配
10. subject 在合法 6 值中
11. subject 与 chain_id 前缀一致
12. status = trial_production / done
13. generated_at = 目录日期
14. total_cards = 实际 K 数
15. open_questions_count = main.open_questions 长度
16. exam_questions_count = main.exam_questions 长度
17. 6 字段（card_type/chain_role/maturity/confidence + main.front / back_core / back_detail 长度）
18. sources 字段结构（type/source/detail/url）+ 至少 1 条 academic
19. exam_questions 5 题型齐全
20. 开放论述 answer 必含三层给分

**自动校验 10 项自检**：
- 概念在正文中出现
- 无相对时间表述
- tags 必含项
- 等等

---

## §8 命名规约（与 04_chain_id_naming.md 联动）

| 项 | 格式 | 例子 |
|----|------|------|
| 学科目录 | `小写英文` | `geography` / `history` / `politics` |
| 学科前缀 | `大写首字母` | `G` / `H` / `P` |
| 模块号 | `M + 数字` | `M1` `M2` |
| 概念号 | `纯数字` | `1` `2` `3` |
| 概念名 | `中文` | `热力环流与风` |
| chain_id | `<dir>/<SUBJ>-M<mod>-<idx>-<name>` | `geography/G-P1-2-热力环流与风` |
| 主卡 card_id | `<SUBJ>-M<mod>-<idx>-MAIN-001` | `G-M1-2-MAIN-001` |
| 子卡 card_id | `<SUBJ>-M<mod>-<idx>-K<XX>-001` | `G-M1-2-K05-001` |

详见 `04_chain_id_naming.md`。

---

## §9 失败案例（避坑）

### ❌ 错 1：front 没问号
```json
"front": "热力环流的形成机制"
```
**ERR**: `[front问号] xxx 未以问号结尾`

✅ **改**：`"热力环流的形成机制是什么？"`

### ❌ 错 2：back_detail 太短
```json
"back_detail": "（仅 50 字）"
```
**ERR**: `[back_detail长度] xxx 50字 (需800~1200)`

✅ **改**：800-1200 字长文

### ❌ 错 3：缺 `#考频/`
```json
"tags": ["#domain/自然地理", "#content/热力环流", "#朝代/现代"]
```
**ERR**: `[tags] xxx 缺 #考频/...`

✅ **改**：加 `"#考频/★★★"`

### ❌ 错 4：back_detail 末尾重复模板（**严重 · 2026-08-22 实测**）

```json
"back_detail": "...【正文省略】...⚠️ 易错点：\n· ❌...是错误表述——...\n· 秋冬季节霜冻多发生在晴朗夜晚。\n补充说明：本考点在近三年上海等级考中属高频内容，复习时务必结合案例与辨析要点。"
```

**ERR**: `[back_detail重复模板] xxx 末尾含'补充说明：本考点在近三年...'`

✅ **改**：在 `⚠️ 易错点` 段后直接收尾，不要加"补充说明"段。如需总结，融入前文。

> 此类污染 autoclaw 端 LLM 高频输出（截至 2026-08-22 实测 173 套 1010 张卡污染），必须堵在 prompt 源头。

### ❌ 错 5：开放论述缺三层给分
```json
{"type": "开放论述", "answer": "城市热岛是因为..."}
```
**ERR**: `[三层给分] xxx 缺三层给分`

✅ **改**：`"answer": "1~3 城市热岛概念 + 4~6 形成机制 + 7~8 防治建议"`

### ❌ 错 5：子卡 parent_card 错
```json
{
  "card_id": "G-M1-2-K01-001",
  "parent_card": "G-M1-2-MAIN-002"  // ❌ 主卡是 001
}
```
**ERR**: `[parent_card] xxx = G-M1-2-MAIN-002, 主卡 = G-M1-2-MAIN-001`

### ❌ 错 6：chain_id 概念名 ≠ 目录名概念名
```
chain_id: geography/G-P1-2-热力环流
目录名: 2026-08-16_热力环流与风  // ❌ "热力环流" ≠ "热力环流与风"
```
**ERR**: `[概念名] 目录名'热力环流与风' ≠ chain_id概念'热力环流'`

---

## §10 变更记录

| 版本 | 日期 | 改动 |
|------|------|------|
| 1.0 | 2026-08-16 | 首发（6 学科 + 6 链角色 + 6 题型） |
| 1.0.1 | 2026-08-20 | 增加 rujing 端字段映射说明 + 推 rujing 流程 |
| 1.0.2 | 实测发现 | + §2.3 back_detail 末尾禁重复模板硬规则 + §7 错 4 实测错例（堵 LLM 污染源） |

---

**这是 autoclaw 端必须遵守的契约。** 校验通过后才能 git push。
