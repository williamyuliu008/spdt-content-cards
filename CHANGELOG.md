# 变更记录（CHANGELOG）

> 本项目所有"规范/案例/SOP"变更的历史记录
> 格式：[版本] 日期 — 简述 — 影响范围

---

## v1.0 · 2026-08-16 · 初始版本

**概述**：本项目从 SPDT-004 content 端独立出来，建立**与平台项目解耦的"内容本征层"**架构。

**新增**：
- `00-项目文档/知识卡片产出规范_v1.0_给AI的指令.md` — 33KB，13 章，详细到字段级
- `00-项目文档/_62_concepts.json` — 10.4KB，62 概念清单（含主题线标注、是否主线、是否已完成）
- `00-项目文档/历史参考/SPDT-004_*.md` — 2 份旧 SPDT-004 content 文档（归档保留）
- `历史/cards/2026-08-16_监察谏议制度/` — autoclaw 试制 demo（id=5，主题线 2）
- `历史/cards/2026-08-16_启蒙运动/` — autoclaw 试制 demo（id=52，主题线 3）
- `历史/cards/2026-08-16_全民族抗战/` — autoclaw 试制 demo（id=37，主题线 4+6）
- `_tools/_validate_cards.py` — 12KB，校验器（按规范 §7 20 项硬指标 + §11 自检 10 项 + 与 _62_concepts.json 交叉核对）
- `_tools/_试产测试报告_2026-08-16.html` — 13KB，autoclaw 试产可视化报告
- `README.md` — 9.3KB，项目说明 + 工作流 + 目录结构
- `.gitignore` — 0.7KB，排除历史存档 + 临时文件

**清理**：
- 删除 SPDT-004 content 端 5 个历史目录（`core/` `tools/` `docs/` `reports/` `views/`）—— 用 mavis-trash 软删除，可恢复
- 删除 2 个 SPDT-004 markdown 文档（移入 `00-项目文档/历史参考/`）

**架构决策**：
- 与 SPDT-004 平台项目（`williamyuliu008/subject-ebooks-portfolio`）**解耦**
- 平台项目 = 电子书/HTML/APP 工具链（消费端）
- 内容项目（本仓库）= 规范/案例/卡片 JSON/校验工具（本征层）
- 两套独立演进，通过 Git 同步

**质量验证**：
- autoclaw 试制 3 套（28 个 JSON 文件）全部通过 20 项硬指标，0 错误 0 警告
- 验证脚本：`_tools/_validate_cards.py`

**待办**（v1.1 规划）：
- [ ] 剩余 59 套卡片（autoclaw 持续推）
- [ ] 平台项目消费端：`ru_cardpkg_convert.py`（卡片 JSON → rujing CardPackage）
- [ ] 案例/ 目录正式化（autoclaw 3 件打包成单文件作样板）
- [ ] 规范 v1.1 迭代（试产 5 件后总结经验）

---

*本项目由 willi + Mavis 共同维护。autoclaw 是首个接入的产卡片 AI。*
