# rujing Patch · /data/local/tmp/ 临时导入支持

> **目的**：让 rujing APP 支持从 `/data/local/tmp/rujing_cards.json` 临时导入卡片（hdc push 路径）
> **状态**：✅ 源码已改（archived ImportPage.ets）· ⏸️ 等待 SDK 重装后编译
> **作者**：Mavis · 2026-08-16

---

## 1. 改了什么

3 处插入到 `ImportPage.ets`（archived 路径 `D:\9_archive\92_products_migration\SPDT-001_Harmony\apps\rujing\entry\src\main\ets\pages\ImportPage.ets`）：

| 位置 | 改动 |
|:---|:---|
| State 字段（line 47 后） | 加 4 个 `@State`：`tempImportResult` / `isTempImporting` / `tempImportedCards` / `tempImportedChains` |
| build() UI 块（line 407 后） | 加一个新 Column 块（橙色"临时导入"按钮 + 结果显示） |
| do 方法（line 727 后） | 加 `async doTempImport()` 方法（用 `fileIo.openSync` 读 /data/local/tmp/） |

完整 diff 对比：见 `ImportPage_v1.ets`（原版）vs `ImportPage_v2.ets`（改后）。

---

## 2. 怎么用

### 步骤 1：本机（Mavis）推 JSON

```powershell
# 1. 用 _tools/ru_cardpkg_convert.py 把卡片转 rujing 格式
python -X utf8 _tools\ru_cardpkg_convert.py `
  --card-dir 历史\cards\2026-08-16_xxx `
  --output D:\tmp\rujing_xxx.json

# 2. hdc push 到手机
hdc file send D:\tmp\rujing_xxx.json /data/local/tmp/rujing_cards.json
```

### 步骤 2：手机端 rujing 点按钮

1. 打开 rujing APP
2. 首页 → "导入"（导入页）
3. 滚到底部 → 找到**橙色"临时导入（hdc push 路径）"区块**
4. 点"导入临时 JSON"
5. 看到 toast "临时 JSON N 张卡片已导入" + 状态文本

### 步骤 3：回到首页看链/卡

导入页 → "返回首页" → 在"链列表"里看到新链（H-M1-5-监察谏议制度 等）

---

## 3. 编译指南（SDK 装上后）

### 3.1 装 DevEco SDK

SDK 原本在 `D:\9_infra\DevEco\6.1\sdk`，但已被清空。需要重装：
- DevEco Studio 5.0+ （含 6.1 SDK）
- 安装路径建议：`D:\9_infra\DevEco\6.1\`

### 3.2 编译 + 部署

```powershell
# 1. 进入 rujing 源
cd D:\9_archive\92_products_migration\SPDT-001_Harmony\apps\rujing

# 2. (如果 SDK 路径变了)改 build-cli.ps1 的 SDK 路径
# 旧：$env:DEVECO_SDK_HOME = 'D:\9_infra\DevEco\6.1\sdk'
# 新：$env:DEVECO_SDK_HOME = '<你的 SDK 路径>'

# 3. 编译 + 装到手机
.\build-cli.ps1 -deploy
```

### 3.3 验证

1. 手机 rujing 启动 → 导入页
2. 滚到最底下 → 应该看到"临时导入"按钮
3. 走"步骤 1" 推 JSON + "步骤 2" 点按钮 → 看到"OK: N 张卡片" 

---

## 4. 关键文件清单

| 文件 | 用途 | 状态 |
|:---|:---|:---|
| `ImportPage_v1.ets` | 原版备份 | ✅ 暂存 |
| `ImportPage_v2.ets` | 改后版（含临时导入按钮） | ✅ 暂存 |
| `D:\9_archive\...\ImportPage.ets` | archived 源（已改） | ✅ 已应用 |
| `D:\tmp\rujing_xxx.json` | 临时输出（ru_cardpkg_convert.py 产物） | 按需 |

---

## 5. 已知限制

- **HAP 未重新编译**：SDK 没装，无法生成新 HAP
- **手机里仍是 7-27 HAP**（无新按钮）：用户能看 rujing 跑起来 + 内置内容（墨骨山河/历史 v3 等），但看不到新按钮
- **新流程暂停**：等 SDK 装上后跑 `build-cli.ps1 -deploy`

---

## 6. 关联文档

- `D:\4_data\knowledge_cards\_tools\ru_cardpkg_convert.py` — 卡片 JSON 转换器
- `D:\4_data\knowledge_cards\_tools\push_to_rujing.ps1` — hdc 推送脚本
- `D:\4_data\knowledge_cards\00-项目文档\知识卡片产出规范_v1.0_给AI的指令.md` — autoclaw 规范
- `D:\4_data\knowledge_cards\00-项目文档\MANIFEST.yaml` — 项目控制中枢

---

*Patch v2.1 · 2026-08-16 · Mavis*
