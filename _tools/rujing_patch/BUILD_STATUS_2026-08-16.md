# rujing 重编译状态报告（2026-08-16）

> **状态**：重编译**部分进展**但**未完成**（hvigor 5.15.5 vs 6.1.1 不匹配）
> **作者**：Mavis · 2026-08-16

## 1. 进展总结

| 步骤 | 状态 | 备注 |
|:---|:--:|:---|
| 1. SDK 找到 | OK | `D:\tools\ide\DevEco\tools\hvigor\bin\hvigorw.bat` |
| 2. hdc 找到 | OK | `C:\Users\willi\AppData\Local\OpenHarmony\Sdk\26.0.0\toolchains\hdc.exe` |
| 3. build-cli-v2.ps1 写好 | OK | 用 D:\tools\ide\DevEco 路径 |
| 4. junction 建好 | OK | `D:\92_products\SPDT-001_Harmony` -> archived |
| 5. modelVersion 错误 | OK | 改 3 个文件后错误消失 |
| 6. **真编译** | **FAIL** | **降级到 5.x 失败：项目代码用了 6.x API** |
| 7. **回退降级** | OK | 恢复 6.1.1 原值 |

## 2. 核心问题

hvigor **5.15.5** vs **6.1.1** 不匹配：
- `D:\tools\ide\DevEco` 装的是 **hvigor 5.15.5**（OpenHarmony 4.0 工具链）
- rujing 项目要 **hvigor 6.x**（`modelVersion: "6.1.1"`，OpenHarmony 5.0+ API）

降级失败原因：项目代码用了 6.x 专属 API（如 `onPrepared((info: PreparedInfo) => ...)` 接受 info 参数；5.x 的 onPrepared 不接受参数）。

## 3. 解决路径（3 选 1）

### 路径 A：装 DevEco Studio 5.0+（推荐）
下载安装 DevEco Studio 5.0 或更新版本（自带 hvigor 6.x + OpenHarmony 5.0+ API SDK）。
然后跑：
```
cd D:\9_archive\92_products_migration\SPDT-001_Harmony\apps\rujing
.\build-cli-v2.ps1 -deploy
```

### 路径 B：装 hvigor 6.x npm 包（轻量）
```
npm install -g @ohos/hvigor@latest
```
⚠️ 可能缺 OpenHarmony 6.x API SDK。

### 路径 C：保持现状，专注内容生产
接受不重编 rujing 事实，专注：
- autoclaw 继续推 62 套卡片
- 内容项目继续演进
- 卡片 JSON 继续推（SDK 装上后随时可用）

## 4. 关联文件

- `D:\4_data\knowledge_cards\_tools\rujing_patch\README.md` — 使用说明
- `D:\9_archive\92_products_migration\SPDT-001_Harmony\apps\rujing\build-cli-v2.ps1` — 我写的 build 脚本
- `D:\9_archive\92_products_migration\SPDT-001_Harmony\apps\rujing\entry\src\main\ets\pages\ImportPage.ets` — 已加"临时导入"按钮

---

*报告 v1.0 · 2026-08-16 · Mavis*