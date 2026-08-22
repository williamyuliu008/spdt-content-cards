# chain_id / card_id 命名规范

> 命名必须唯一、可追溯、跨学科一致。
> autoclaw 端和 rujing 端共用同一套命名规则。

---

## §1 学科前缀表

| 学科目录（chain_id 前导）| 学科前缀（card_id 首字母）| 中文名 | Subject enum |
|--------------------------|---------------------------|--------|--------------|
| `history` | `H` | 历史 | `HISTORY` |
| `geography` | `G` | 地理 | `GEOGRAPHY` |
| `politics` | `P` | 政治 | `POLITICS` |
| `guwen` | `W` | 古诗文 | `GUWEN` |
| `calligraphy` | `C` | 书法 | `CALLIGRAPHY` |
| `english` | `E` | 英语 | `ENGLISH` |
| `biology` | `B` | 生物 | `BIOLOGY` |
| `chemistry` | `M` | 化学 | `CHEMISTRY` |
| `physics` | `Y` | 物理 | `PHYSICS` |

**新增学科**：
- autoclaw 端在 `_N_concepts.json` 加新学科
- chain_id 用新 `<dir>/<SUBJ>-M<mod>-<idx>-<name>` 格式
- rujing 端零代码改动（Subject 已经是 string type）

---

## §2 chain_id 格式

```
<学科目录>/<学科前缀>-M<模块号>-<概念号>-<概念名>
└────┬───┘ └──────────┬──────────┘ └─┬─┘ └┬┘ └──┬──┘
   dir            short_id       mod  idx   name
```

### §2.1 例子

| 链 | chain_id |
|----|----------|
| 历史 - 监察谏议制度 | `history/H-M1-1-监察谏议制度` |
| 地理 - 热力环流与风 | `geography/G-P1-2-热力环流与风` |
| 政治 - 社会主义核心价值观 | `politics/P-M1-1-社会主义核心价值观` |
| 古诗文 - 炼字三步法 | `guwen/W-M1-1-炼字三步法` |
| 书法 - 颜真卿祭侄文稿 | `calligraphy/C-M1-1-颜真卿祭侄文稿` |
| 英语 - 虚拟语气 | `english/E-M1-1-虚拟语气` |
| 生物 - 细胞分裂 | `biology/B-M1-1-细胞分裂` |
| 化学 - 化学键 | `chemistry/M-M1-1-化学键` |
| 物理 - 牛顿第二定律 | `physics/Y-M1-1-牛顿第二定律` |

### §2.2 字段说明

- **`<dir>`**: 学科目录名（**小写英文**）
- **`<学科前缀>`**: 学科首字母大写（**与 dir 映射**）
- **`M<模块号>`**: 模块号，从 1 开始
- **`<概念号>`**: 模块内概念编号，从 1 开始（同一模块内唯一）
- **`<概念名>`**: 中文概念名，2-12 字，**与目录名末尾概念名一致**

### §2.3 短链 ID（rujing 端使用）

rujing 端存的是去前导 dir 的短链 ID：

```
chain.chain_id = "G-P1-2-热力环流与风"  (rujing 端，去掉 "geography/" 前缀)
```

但 autoclaw 端的 chain_id 保留前导（明确归属学科）：

```
chain.chain_id = "geography/G-P1-2-热力环流与风"  (autoclaw 端)
```

**转换器自动去掉前导**。autoclaw 端可以两种都用，但建议保留前导更清晰。

---

## §3 card_id 格式

### §3.1 主卡

```
<学科前缀>-M<模块号>-<概念号>-MAIN-001
```

例子：
- `G-M1-2-MAIN-001`（地理模块1概念2的主卡）
- `H-M1-1-MAIN-001`（历史模块1概念1的主卡）

### §3.2 子卡

```
<学科前缀>-M<模块号>-<概念号>-K<XX>-001
```

其中 `K<XX>` 中 XX 是子卡序号（01-10），001 是版本号。

例子：
- `G-M1-2-K01-001`（地理模块1概念2的第1张子卡）
- `G-M1-2-K05-001`（第5张子卡）
- `G-M1-2-K10-001`（第10张子卡，最多数量）

### §3.3 验证正则

```javascript
// 主卡
/^[HGPEWCMYB]-M\d+-\d+-MAIN-001$/

// 子卡
/^[HGPEWCMYB]-M\d+-\d+-K\d{2}-001$/
```

校验失败的 card_id → ERR。

---

## §4 命名冲突检查

**同模块同概念号不能重名**：
- `G-M1-2-热力环流` 和 `G-M1-2-热力环流与风` ❌ 冲突
- 解决：概念号升级（2→3）或合并

**跨模块可同名**：
- `G-M1-2-热力环流` 和 `G-M2-2-热力环流` ✅ 允许（不同模块有同名概念）

**跨学科完全独立**：
- `H-M1-1-演化` 和 `G-M1-1-演化` ✅ 允许（不同学科）

---

## §5 命名检查清单（autoclaw 端）

每套卡产出后，autoclaw 操作员检查：

| 检查项 | 通过条件 |
|--------|----------|
| 目录名 = `YYYY-MM-DD_<概念名>` | 概念名中文 2-12 字 |
| chain_id 前导 dir 在学科表中 | dir ∈ {history, geography, politics, guwen, calligraphy, english, biology, chemistry, physics} |
| chain_id 概念名 = 目录名概念名 | 完全一致（含标点） |
| 主卡 card_id 末段 = `-MAIN-001` | 正则 |
| 子卡 card_id 末段 = `-K01-001` ~ `-K10-001` | 正则 |
| 子卡数量 6-10 张 | K01-K06 至少，K10 上限 |
| K0X 序号与文件名 K0X.json 一致 | K01.json → card_id 末段 K01 |

---

## §6 autoclaw 概念清单（_N_concepts.json）

autoclaw 端必须维护一个概念清单文件（按学科）：

```
历史/
  _62_concepts.json    ← 历史 62 个概念
地理/
  _N_concepts.json     ← 地理 N 个概念
```

**格式**（参考历史 _62_concepts.json）：

```json
[
  {
    "id": 1,
    "name": "热力环流与风",
    "lines": ["大气受热", "热力环流"],
    "star": true,
    "module": "模块一·自然地理基础",
    "topic": "专题1 大气与气候"
  },
  ...
]
```

校验脚本会用这个清单交叉核对 chain.json 的元数据是否一致。

---

## §7 命名 FAQ

### Q: 我想给英语加个"虚拟语气"链，怎么命名？

```
目录：english/cards/2026-08-20_虚拟语气/
chain_id: english/E-M1-1-虚拟语气
主卡 card_id: E-M1-1-MAIN-001
子卡 card_id: E-M1-1-K01-001 ... K06-001
```

### Q: 链有别名（如"炼字三步法"也叫"诗眼三步法"）？

- chain_title 可写"炼字三步法（诗眼三步法）"
- chain_id 末段用一个：`guwen/W-M1-1-炼字三步法`
- 别名在 tags 加：`#alias/诗眼三步法`

### Q: 子卡内容跨链怎么记？

- 链元数据加 `related_chains: ["<其他 chain_id>"]`
- 不影响子卡命名

### Q: 模块号用完了（M9 → M10）？

- 升模块号即可：`M10` `M11` ...
- 模块号无上限
