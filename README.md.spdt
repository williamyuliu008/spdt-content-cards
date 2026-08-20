# 知识卡片内容项目（SPDT-Content-Cards）

> **本项目 = 内容本征层**（与 SPDT-004 平台项目**解耦**）
> 平台项目：[`williamyuliu008/subject-ebooks-portfolio`](https://github.com/williamyuliu008/subject-ebooks-portfolio)（电子书、HTML、rujing APP 工具链）
> 内容项目：**本仓库**（规范、案例、SOP、卡片 JSON、校验工具）
> 关系：内容项目产卡片 JSON → 推 Git → 平台项目拉取后做消费端转换 → 推 rujing APP

---

## 1. 项目目的

把"知识卡片内容生产"从 SPDT-004 平台项目中**独立**出来，让：
- **作者/AI** 专注于"内容本征"（规范、案例、卡片 JSON）
- **平台/工程师** 专注于"消费端"（电子书、HTML、APP 工具链）

两套独立演进，通过 **Git 同步** 解耦。

---

## 2. 工作流

```
┌─────────────────────────────────────────────────────────────┐
│ [作者/AI（任意一台电脑，含 autoclaw）]                          │
│   ↓ 读 知识卡片产出规范 v1.0                                     │
│   ↓ 按规范产 JSON 卡片                                          │
│   ↓ 推 Git（本仓库）                                            │
└─────────────────────────────────────────────────────────────┘
                          ↓ git push
┌─────────────────────────────────────────────────────────────┐
│ [本仓库] GitHub williamyuliu008/spdt-content-cards           │
│   ├── 规范/案例/SOP 持续更新                                      │
│   ├── 历史/cards/ 等学科子目录（每套卡片 1 个目录）                  │
│   └── _tools/ 校验器                                            │
└─────────────────────────────────────────────────────────────┘
                          ↓ git pull
┌─────────────────────────────────────────────────────────────┐
│ [本机 Mavis]                                                    │
│   ↓ 跑 _validate_cards.py 校验新卡片                              │
│   ↓ 写推 rujing 脚本（消费端，在平台项目里）                          │
│   ↓ push-to-rujing → rujing APP                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 目录结构

```
spdt-content-cards/
├── README.md                              # 本文件
├── CHANGELOG.md                           # 规范/案例变更记录
├── .gitignore                             # 排除规则
│
├── 00-项目文档/                           # 规范 + 概念清单 + 上游参考
│   ├── 知识卡片产出规范_v1.0_给AI的指令.md  # AI 必读的"产出规范"
│   └── _62_concepts.json                  # 62 概念清单（约束产出范围）
│
├── 历史/                                  # 学科子目录（未来：地理/政治/古文/英文）
│   └── cards/                             # autoclaw 试制 3 套 + 未来 57 套
│       ├── 2026-08-16_监察谏议制度/
│       │   ├── chain.json                 # 链元数据
│       │   ├── main.json                  # 主卡（叙事+练习+存疑）
│       │   ├── K01.json ~ K08.json        # 子卡（考点表每行 1 张）
│       ├── 2026-08-16_启蒙运动/
│       │   ├── chain.json + main.json + K01~K07.json
│       └── 2026-08-16_全民族抗战/
│           ├── chain.json + main.json + K01~K07.json
│
├── _tools/                                # 内容项目自己的工具
│   ├── _validate_cards.py                 # 校验脚本（按规范 §7 20 项硬指标）
│   └── _试产测试报告_2026-08-16.html       # 试产报告（autoclaw 产出）
│
├── 案例/                                  # （待建）正式样板
│   └── （规划中：autoclaw 3 件打包成单文件，作为 v1.0 正式案例）
│
├── docs/                                  # 历史存档（不上 Git）
│   └── B_历史/                            # autoclaw 试制前的 B_历史工程
│
├── core/                                  # 历史存档（不上 Git）
│
├── reports/                               # 历史存档（不上 Git）
│
├── tools/                                 # 历史存档（不上 Git）
│
└── views/                                 # 历史存档（不上 Git）
```

---

## 4. 协作方式

### 4.1 另一台电脑（autoclaw 或其他 AI）如何贡献

1. **clone 本仓库**：
   ```bash
   git clone https://github.com/williamyuliu008/spdt-content-cards.git
   cd spdt-content-cards
   ```

2. **必读**：
   - `00-项目文档/知识卡片产出规范_v1.0_给AI的指令.md`（33KB，详细到字段级）
   - `历史/cards/` 下的 3 件 autoclaw 试制样板（看实际产出格式）

3. **产出新卡片**：
   - 读 `_62_concepts.json`，选未做的概念（`done: false`）
   - 按规范产出 1 套 = `chain.json` + `main.json` + 6~10 张 `K0N.json`
   - 放到 `历史/cards/2026-XX-XX_{概念名}/` 目录
   - 跑校验：`python _tools/_validate_cards.py`
   - 全过后 commit + push

4. **commit 规范**：
   ```bash
   git add 历史/cards/2026-08-16_xxx/
   git commit -m "feat(历史): 新增 xxx 卡片 · 7 张 K 卡 + 1 主卡"
   git push origin main
   ```

### 4.2 本机如何消费

1. **拉新内容**：
   ```bash
   git pull origin main
   ```

2. **校验**：
   ```bash
   cd spdt-content-cards
   python _tools/_validate_cards.py
   ```

3. **推 rujing**（消费端转换）：
   - 在 SPDT-004 平台项目（`subject-ebooks-portfolio`）里写 `ru_cardpkg_convert.py`
   - 把本仓库的 `历史/cards/*/main.json` 转为 rujing CardPackage JSON
   - 调用 `push-to-rujing.ps1`

---

## 5. 规范版本与变更

- **v1.0（2026-08-16）**：初版。基于 B_历史 7 件样板 + SPDT-004 v1.3 schema + rujing CardPackage 三方融合
- **v1.1（规划）**：试产 5 件 demo 后迭代，预期新增/调整：
  - 字段约束细化
  - 题型分布的最小集
  - 跨学科 schema 通用化

变更记录见 `CHANGELOG.md`。

---

## 6. 工具说明

### 6.1 `_tools/_validate_cards.py`

**用途**：按规范 §7 质量硬指标 20 项 + §11 自检 10 项 + 与 `_62_concepts.json` 交叉核对，**全自动**校验 1 个或多个套卡目录。

**用法**：
```bash
# 校验整个 cards 目录
python _tools/_validate_cards.py

# 校验指定目录
python _tools/_validate_cards.py 历史/cards/2026-08-16_xxx/
```

**退出码**：
- `0` = 全部通过
- `1` = 有错误
- `2` = 有警告（无错误）

**校验项**（节选）：
- 文件数（1 chain + 1 main + 6~10 K 卡）
- 字段完整性（主卡 13 字段、子卡 12 字段）
- front 30-100 字 + 问号结尾
- back_core 150-250 字
- back_detail 800-1200（主卡）/ 200-350（子卡）
- exam_questions 5-6 道 + 5 种题型 + 开放题三层给分
- open_questions 5-10 条 + 单条 ≤50 字
- confidence 与存疑条数一致性
- 时间相对表述扫描（"同一时期"等禁用词）
- UTF-8 无 BOM
- JSON 合法性
- chain_id 格式 + 与 _62_concepts.json 交叉

---

## 7. 与 SPDT-004 平台项目的关系

| 维度 | 本项目（内容） | 平台项目（subject-ebooks-portfolio） |
|:---|:---|:---|
| **关注点** | 规范、案例、卡片 JSON、校验 | 电子书、HTML、APP、工具链 |
| **更新频率** | 高（每月数十件） | 低（每季度一迭代） |
| **贡献者** | 作者、AI（autoclaw 等） | 工程师 |
| **依赖方向** | 无外部依赖 | 依赖本项目（拉卡片 → 推 rujing） |

**解耦的好处**：
- 内容更新不污染平台代码
- 平台重构不影响内容生产
- 多学科可并行（历史/地理/政治各自子目录）

---

## 8. 当前状态（2026-08-16）

- ✅ 项目结构已建（`00-项目文档/` `历史/cards/` `_tools/`）
- ✅ 规范 v1.0 已写（33KB）
- ✅ 62 概念清单已存（10.4KB）
- ✅ autoclaw 试制 3 套卡片（全过 20 项校验）
  - 监察谏议制度（id=5，主题线 2 制度与治理）
  - 启蒙运动（id=52，主题线 3 文明互动）
  - 全民族抗战（id=37，主题线 4+6 社会转型+时政）
- ⏳ 剩余 59 套待产（autoclaw 后续推）
- ⏳ 平台项目消费端转换工具待写（`ru_cardpkg_convert.py`）

---

*本项目由 willi + Mavis 共同维护。autoclaw 是首个接入的产卡片 AI。*
