# autoclaw_kit v1.0

**用途**：autoclaw 端按本套规范产出知识卡片 → push 到 GitHub → rujing APP 自动拉取展示。

**面向对象**：autoclaw 端的知识卡片制作人员（不需懂 rujing / ArkTS / HarmonyOS）。

**关键事实**：
- 知识卡片 v1.0 规范 ✅
- rujing v6.0 端 ✅（已端到端跑通：1 套地理 9 张卡入库）
- autoclaw 端按本规范产出，**零代码对接**

---

## 目录结构

```
autoclaw_kit/
├── 00_README.md               ← 本文件
├── 01_quickstart.md           ← 5 分钟快速上手
├── 02_spec_card_v1.0.md       ← 知识卡片完整规范（必读）
├── 03_push_to_rujing.md       ← 推送到 rujing 流程
├── 04_chain_id_naming.md      ← chain_id / card_id 命名规范
├── 05_templates/              ← chain.json / main.json / K0X.json 模板
├── 06_example/                ← 1 套完整示例（地理 - 热力环流与风）
├── 07_validate.py             ← 校验脚本（20 项硬指标 + 10 项自检）
└── 08_tools/                  ← 转换 + 推送工具
    ├── ru_cardpkg_convert.py  ← autoclaw 卡片 → rujing CardPackage v6.0
    └── _push_to_rujing.py     ← rujing CardPackage → rujing APP
```

---

## 端到端流程

```
[1] autoclaw 端产出 (按 02_spec_card_v1.0.md)
    ↓
[2] git push 到 https://github.com/williamyuliu008/spdt-content-cards.git
    ↓
[3] willi 端 git pull + 跑 07_validate.py (本地校验)
    ↓
[4] 跑 08_tools/ru_cardpkg_convert.py (autoclaw → rujing CardPackage v6.0)
    ↓
[5] 跑 08_tools/_push_to_rujing.py (POST rujing APP /upload 端点)
    ↓
[6] rujing APP 自动入库 + 首页显示新学科入口
```

---

## 一句话总结

**autoclaw 端** = 1 套卡片 = 1 目录 = 4 个文件 = `chain.json` + `main.json` + `K01.json ~ K0N.json`

按规范产出后，git push 即可，willi 端全自动处理剩下的事。

---

## 关键约定

| 约定 | 详情 |
|------|------|
| **学科** | 6 个 well-known：历史 / 地理 / 政治 / 古诗文 / 书法 / 英语；新学科零代码加入 |
| **主卡 / 子卡** | 1 套 1 主 + 6-10 子；主卡 back_detail 升链长文，exam_questions 升链自测题 |
| **目录命名** | `YYYY-MM-DD_概念名`（如 `2026-08-16_热力环流与风`） |
| **chain_id** | `<学科前缀>/<学科前缀>-M<模块>-<概念号>-<概念名>`（如 `geography/G-P1-2-热力环流与风`） |
| **card_id** | 主卡 `<学科>-M<模>-<号>-MAIN-001` / 子卡 `<学科>-M<模>-<号>-K<序>-001` |
| **考频** | tags 加 `#考频/★★★`（高）/ `★★`（中）/ `★`（低），由 rujing 端 parse |
| **版本** | 首次导入 v1.0.0，update 后递增；version 在 chain.json |

---

## 反馈

发现规范问题 → 直接改 02_spec_card_v1.0.md + 提 issue
推 rujing 失败 → 跑 07_validate.py 看错误 + 看 03_push_to_rujing.md 排错
新学科要加 → 直接用新名字，rujing 端零代码改动

---

v1.0 · 2026-08-20 · 入口 v6.0
