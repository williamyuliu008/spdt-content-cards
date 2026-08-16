# SPDT-004 知识卡片系统 — 项目总览

> **版本**：v1.0
> **更新**：2026-08-09
> **定位**：AI 沟通记录 → 电子书 → 卡片集合 全流程验证平台

---

## 1. 项目愿景

> **目标**：构建一条从 AI 沟通记录到电子书章节，再到知识卡片集合的完整自动化管线，
> 并用真实内容（历史/地理/政治/书法）完成端到端验证，形成可复用的智能体集群架构。

### 全流程管线

```
AI沟通记录（剧本/对话）
    ↓  [智能体集群执行]
电子书（Markdown章节）
    ↓  [P1-P5 批次卡片创作]
考点地图（考点点位 v1.x）
    ↓  [卡片提炼 SOP v1.1]
知识卡片（JSON格式 v1.3）
    ↓  [card_auditor.py 验收]
认证卡库（GOLD/SILVER/CERTIFIED）
    ↓  [skill_bridge → skill_selector]
应用场景（考试/写作/素材/费曼）
```

---

## 2. 内容模块现状

### 2.1 学科电子书（电子书阶段）

| 模块 | 书名 | 章节 | 卡片批次 | 覆盖率 | 状态 |
|:---|:---|:---:|:---:|:---:|:---|
| H-M1 | 《千年治乱》 | 4章 | Batch 1-5 | 33/33 = **100%** | ✅ 完成 |
| H-M2 | 《食货之道》 | — | Batch A-C | 16/16 = **100%** | ✅ 完成 |
| G-M1 | 《阶梯山河》 | 5章 | G1-G9 | 48/48 = **100%** | ✅ 完成 |
| P-M1 | 《道路的选择》 | 6章 | P0-P5 + 节段 | 45/44 = **100%** | ✅ 完成 |

> **里程碑**：2026-08-08 夜，四个模块首次同时达到 100% 覆盖率，共 141 张卡片。

### 2.2 知识卡片库（卡片阶段）

**卡库地址**：`D:\4_data\knowledge_cards\`

| 批次 | 数量 | 来源 | 类型 |
|:---|:---:|:---|:---|
| 墨骨山河_Ep01 | 8张 | 颜真卿微剧本 | 历史/书法核心卡 |
| 古史_v4 | 133张 | 高考历史考纲 | 历史分析卡 |
| CAFA楷书 | 3张 | 书法校考 | 书法影响卡 |
| **合计** | **144张** | — | — |

### 2.3 书法校考（书法模块）

- 配置包：`cafa_calligraphy_2026`（meta.json / kb_vocab.json / ability_list.json / answer_templates.json）
- 微剧本：墨骨山河 Ep01（颜真卿+安史之乱）已入库
- 规划：Ep02-08（王羲之/苏轼/阮元/张旭怀素/李斯/康有为/许慎）

---

## 3. 规范体系（SOP + Schema）

### 3.1 核心规范

| 文件 | 版本 | 用途 |
|:---|:---:|:---|
| `card_schema.json` | v1.3 | 卡片格式规范（concepts/tags/sources/materials 四层结构） |
| `SOP_知识卡片提炼.md` | v1.1 | 卡片提炼标准（原子性/自足性/还原测试） |
| `SOP_卡片创作应用.md` | v1.0 | 卡片创作应用标准（Skill链/materials降权/StylePack） |

### 3.2 测试标准

| 文件 | 版本 | 状态 |
|:---|:---:|:---|
| `SPDT-004_知识卡片_测试标准设计.md` | v0.4 | T3 完成 |
| `card_auditor.py` | v1.1 | 运行中 |
| `reports/audit_report.html` | — | 实时生成 |

---

## 4. 质量认证（截至 2026-08-09 T3）

| 维度 | 均分 | 满分 | 评级 |
|:---|:---:|:---:|:---|
| A 格式合规 | 15 | 15 | ✅ 144/144 通过 |
| B 原子性 | 15 | 15 | ✅ 144/144 通过 |
| C 来源可信 | 25.0 | 25 | ✅ 144/144 全覆盖 |
| D 材料完整 | 20.8 | 30 | 🟡 古史_v4=标准卡(20)，核心卡=30 |
| **E 语义可检** | **13.7** | **15** | ✅ 1145词词典规则提取 |
| **综合均分** | **89.5** | 100 | ✅ |

**认证分布**：
- 🏅 GOLD（≥95）：**10张**（7%）
- 🥈 SILVER（≥85）：**131张**（91%）
- 🏅 CERTIFIED（≥75）：**3张**（2%）
- **FAIL（格式未过）：0张**

**叙事潜力标签**：
- narrative_candidate：127张（叙事潜力卡）
- narrative_inert：17张（分析/元数据卡）

---

## 5. 工具链（20个 Python 脚本）

### 卡片管理
| 工具 | 用途 |
|:---|:---|
| `import_card.py` | 单卡/批量入库 + schema 验证 |
| `rebuild_registry.py` | 重建 registry + tag_dictionary |
| `migrate_cards_v1v2_to_v1v3.py` | v1.2→v1.3 迁移 |

### 质量补全
| 工具 | 用途 |
|:---|:---|
| `batch_enrich_sources.py` | sources[] 批量补充（144张全覆盖） |
| `enrich_gushi_concepts.py` | concepts[] 规则提取（1145词/8类别词典） |
| `fix_low_e_cards.py` | 低分卡针对性修复（EP01/CAFA） |
| `enrich_materials.py` | ep01 materials 补全（quote+scene+data） |
| `enrich_gushi.py` | 古史_v4 materials.data 批量提取 |
| `enrich_cafa.py` | CAFA materials 补全 |
| `migrate_gushi_cardids.py` | card_id 中文→ASCII 迁移（G4/C4） |

### 质量审计
| 工具 | 用途 |
|:---|:---|
| `card_auditor.py` | 三层审计（格式/内容/叙事），含 HTML 报告 |
| `tag_audit.py` | 同义异标/materias缺口/inferred未标检测 |
| `analyze_materials.py` | materials 层覆盖率分析 |

### 应用导出
| 工具 | 用途 |
|:---|:---|
| `export_view.py` | 4场景导出（writing/exam/anki/graph） |
| `skill_selector.py` | Skill 筛选（REGISTRY 驱动） |
| `skill_bridge.py` | export_view → skill_selector 一键串联 |
| `card_browser_generator.py` | 静态 HTML 浏览器（无服务器） |

---

## 6. 实施路线图

```
当前进度（2026-08-09）
│
├── [已完成] Phase 1-3 工具链
│     20个脚本，覆盖导入/补全/审计/导出/应用全链路
│
├── [已完成] SOP 规范体系
│     SOP_知识卡片提炼 v1.1 + SOP_卡片创作应用 v1.0
│
├── [已完成] 测试标准 v0.4（T3 完成）
│     card_auditor.py + 认证体系（GOLD/SILVER/CERTIFIED）
│     均分 89.5 / FAIL 0 / 91% SILVER+
│
├── [进行中] T4 叙事潜力 Layer 3
│     narrative_tag 自动分类完成（127 candidate / 17 inert）
│     半自动叙事质量评分待设计
│
├── [规划中] 下一批卡片入库
│     墨骨山河 Ep02-08（王羲之/苏轼/阮元/张旭怀素/李斯/康有为/许慎）
│     古史_v4 K32/K33 缺口（H-M1 4.3节段写作后补）
│
└── [规划中] 对外认证试点
      用 SPDT-004 测试标准验收其他知识卡片项目
```

---

## 7. 关键设计决策

| 决策 | 方案 | 理由 |
|:---|:---|:---|
| 核心格式+多视图 | 单 JSON 源 + 场景导出 | 考试卡轻量≠写作卡丰富 |
| materials 子字段 | 按类型判断填不填 | narrative→全填，exam→data，分析型→空 |
| Card 认证体系 | GOLD/SILVER/CERTIFIED 三档 | 适应不同成熟度阶段 |
| E 维度评分 | 规则提取+评分档分层 | 兼顾叙事卡和分析卡的不同上限 |
| 本地优先存储 | Git + manual OneDrive sync | >500张后升级数据库 |
| 标准规范先行 | SOP先制定，再用自己验证 | 先归纳后演绎，标杆卡库即标准样本 |

---

## 8. 关键文件路径

| 类别 | 路径 |
|:---|:---|
| 卡片库根 | `D:\4_data\knowledge_cards\` |
| 卡库核心 | `D:\4_data\knowledge_cards\core\` |
| 审计报告 | `D:\4_data\knowledge_cards\reports\audit_report.html` |
| Registry | `D:\4_data\knowledge_cards\core\_meta\registry.json` |
| Schema | `D:\2_products\education\SPDT-004_EduContent\docs\04-Skills\card_schema.json` |
| SOP（提炼） | `D:\2_products\education\SPDT-004_EduContent\docs\04-Skills\SOP_知识卡片提炼.md` |
| SOP（应用） | `D:\2_products\education\SPDT-004_EduContent\docs\04-Skills\SOP_卡片创作应用.md` |
| 测试标准 | `D:\2_products\education\SPDT-004_EduContent\docs\04-Skills\SPDT-004_知识卡片_测试标准设计.md` |
| 学科电子书 | `C:\Users\willi\Desktop\我的视野\_学科电子书\` |
| 历史系列 | `C:\Users\willi\Desktop\我的视野\_学科电子书\01-历史主线系列\` |
| 地理系列 | `C:\Users\willi\Desktop\我的视野\_学科电子书\02-地理主线系列\` |
| 政治系列 | `C:\Users\willi\Desktop\我的视野\_学科电子书\03-政治主线系列\` |
