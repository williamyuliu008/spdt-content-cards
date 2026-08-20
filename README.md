# 学习中心 v2.0 · 五科知识卡片平台

> 重构于 2026-08-20 · 作者：Mavis（mavis） · 维护：雪薇
> 配套文档：`2026-0816_统一Schema规范.md` / `2026-0820_聚合方案.md`

---

## 一、怎么用

**双击 `学习中心.html` 即可打开**（file:// 零依赖，不需任何服务器/构建）。

打开后：
- 顶栏切换 5 个学科（古诗文 / 历史 / 地理 / 政治 / 英语）
- 左侧模块树点概念 · 顶部搜索框
- 右侧三 Tab：📖 正文 / 📋 卡片 / ✏ 练习

**快捷键**（点 ⌨ 按钮或按 ? 看）：
- `←` / `→` 或 `j` / `k`：上一/下一概念
- `1` / `2` / `3`：切 Tab
- `f`：收藏 / 取消
- `m`：标记已学
- `/`：聚焦搜索
- `Esc`：关闭弹窗 / 清空搜索

收藏和已学状态保存在 `localStorage`，**换浏览器或清缓存会丢**。

---

## 二、目录结构

```
D:\Z_学习平台\
├── 学习中心.html                 ← UI 壳（38KB，含 CSS+JS）
├── data\
│   ├── curated\                  ← 三件套精写数据（人工维护，质量最高）
│   │   ├── history_curated.js    (7 条)
│   │   ├── geography_curated.js  (19 条)
│   │   ├── politics_curated.js   (23 条)
│   │   ├── guwen_curated.js      (3 条)
│   │   └── english_curated.js    (3 条)
│   └── generated\                ← JSON 自动转换数据（AI 批量生产 + 清洗）
│       ├── history_gen.js        (62 条)
│       ├── geography_gen.js      (49 条)
│       └── politics_gen.js       (61 条)
├── tools\                        ← 转换器（Python 3）
│   ├── json2html_converter.py    ← JSON 卡片 → JS DATA（清洗 AI bug）
│   └── md2html_converter.py      ← Markdown 三件套 → JS DATA
├── _backup\                      ← 旧文件归档（学习中心 v1 + 老 _generated_*.js）
└── README.md                     ← 本文件
```

---

## 三、数据流程

```
┌─────────────────┐     tools/json2html_converter.py     ┌────────────────────┐
│ spdt-content-   │ ──────────────────────────────────▶  │ data/generated/    │
│ cards/历史/地理/政治│  (chain.json + main.json + K*.json)│  history_gen.js     │
└─────────────────┘                                       │  geography_gen.js   │
                                                           │  politics_gen.js    │
                                                           └────────────────────┘
                                                                        ↑
                                                                        │ 加载顺序：先生成后精写
                                                                        │  （精写 key 覆盖生成）
                                                                        ↓
┌─────────────────┐     tools/md2html_converter.py       ┌────────────────────┐
│ D:\B_历史\三件套\ │ ─────────────────────────────────▶  │ data/curated/      │
│ D:\C_地理\三件套\ │  (Markdown → JS, 解析第一/二/三件) │  *_curated.js      │
│ D:\D_政治\三件套\ │                                       │  (历史/地理/政治)   │
│ D:\E_古诗文\三件套\│                                       │  (古诗文/英语)     │
│ D:\F_英语\三件套\ │                                       └────────────────────┘
└─────────────────┘
                                                           ┌────────────────────┐
                                                           │   学习中心.html    │
                                                           │  (UI 壳，零依赖)  │
                                                           └────────────────────┘
```

**加载顺序**：`generated/*.js` 先加载（覆盖 DATA[key]）→ `curated/*.js` 后加载（同 key 覆盖 generated）。这样精写版天然优先于自动版。

---

## 四、怎么更新数据

### A. 某个三件套 Markdown 更新了（人工精写）

```powershell
# 跑全部学科
python tools\md2html_converter.py --all

# 只跑某个学科
python tools\md2html_converter.py --subject 历史
```

**注意**：转换器是**覆盖式**输出，每次跑都会重写整个 JS 文件。HTML 引用了同路径，无需改 HTML。

### B. 某个 JSON 卡片新增/修改了（spdt-content-cards）

```powershell
python tools\json2html_converter.py --all
```

### C. 新增一个学科或概念

1. 在 `D:\X_xx\三件套\` 加 `.md` 文件（按 v1.0 规范）
2. 跑 `python tools\md2html_converter.py --subject Xxx`
3. 在 HTML 的 `SUBJECTS` 数组加配置（key/name/emoji/color/status）
4. 在 HTML 的 `TREES['xxx']` 加模块树
5. 在 HTML 的 `<script src=>` 列表加新的 curated JS
6. 刷新 HTML

---

## 五、命名规范要点

### 5.1 概念名一致性

- **HTML `TREES.xxx` 里的概念名** 必须跟 **`DATA.xxx` 里的 key**（即 Markdown H1 提取的 `concept_name`）**严格一致**
- 不一致会导致侧边栏的"绿点（已入库）"失效、点击无反应
- 解决：curated 概念自动归入底部 `📌 三件套精写` section，但点不了
- 改名后要同步：要么改 TREES、要么改 H1

### 5.2 卡片列数

- 历史 / 地理 / 政治：5 列（[# / 考点 / 核心要点 / 易混辨析 / 角度]）
- 古诗文：6 列（[# / 义项 / 释义 / 课内例句 / 易混辨析 / 迁移要点]）
- 英语：6 列（[# / 语法点 / 规则 / 例句 / 易错辨析 / 考点预判]）
- HTML 渲染时按 `tags.headers` 动态适配，**不丢失列**

### 5.3 状态字段

DATA 条目的 `status` 由转换器自动生成（`"已过审·三件套精写（修订版）（2026-08-16）"`），也支持手工覆盖。

---

## 六、已知的限制

- **跨学科搜索**：当前只搜当前学科的概念名 / 卡片内容，不跨学科（如搜"现代化"只搜当前学科）
- **数据未版本化**：所有 DATA 都在 localStorage（收藏 / 已学），JSON/JS 文件本身不存版本号
- **未做导出**：收藏 / 已学没法导出，浏览器不同步
- **JSON 卡片未含古诗文 / 英语**：spdt-content-cards 仓库目前只有历史/地理/政治三科 JSON 卡片
- **数学暂未启动**：聚合方案 4.4 标注为长期目标

---

## 七、迁移到 V1 的对比

| 维度 | v1（2026-08-17 ~ 19）| v2（2026-08-20 重构）|
|---|---|---|
| 文件大小 | 1.2 MB 单文件 | 38 KB HTML + 1.8 MB 数据 |
| 数据更新 | 手动复制粘贴 | 跑转换器一行命令 |
| 数据源 | inline 死代码 | 外部 JS 模块化 |
| 视觉 | 简洁米黄 | 现代米黄 + 卡片化 |
| 交互 | 静态 | 进度 / 收藏 / 搜索 / 快捷键 |
| Bug | 重复文本、截断 | 转换器自动清洗 |
| 维护 | 改 HTML 风险大 | UI/数据分离 |

---

## 八、下一步

参考 `2026-0820_聚合方案.md` 的 M1-M4 里程碑：
- M1：✅ 三科 DATA 重建（替换 172 条已清洗数据）
- M2：古诗文 JSON 卡片生产（待 spdt-content-cards 支持）
- M3：英语 JSON 卡片生产（待 spdt-content-cards 支持）
- M4：数学概念清单 + 卡片生产（长期）
