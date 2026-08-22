# 08_tools/ - 转换 + 推送工具

## 文件清单

| 文件 | 用途 |
|------|------|
| `ru_cardpkg_convert.py` | autoclaw 卡片 JSON → rujing CardPackage v6.0 |
| `_push_to_rujing.py`    | rujing CardPackage → rujing APP（POST /upload） |

---

## ru_cardpkg_convert.py

**作用**：把 autoclaw 规范 v1.0 卡片（chain.json + main.json + K*.json）转换为 rujing 端可接收的 CardPackage v6.0 格式。

**转换做的事**：
- 主卡 `back_detail` (800-1200字) → `chain.article`（**长文升级**）
- 主卡 `exam_questions[]` (5-6道) → `chain.self_test[]`（**自测题升级**）
- autoclaw 字段 → rujing CardPackage 字段映射
- 加 `version: 1.0.0` + `update_log: [首次导入]`
- 加 `chain_meta[]` 数组（让 rujing 端一次读 chain + cards）

**用法**：

```bash
# 单套转换
python -X utf8 ru_cardpkg_convert.py \
  --card-dir D:\4_data\knowledge_cards\地理\cards\2026-08-16_热力环流与风 \
  --output D:\4_data\rujing_out\rujing_热力环流与风.json

# 输出示例
[转换] 读 D:\4_data\knowledge_cards\地理\cards\2026-08-16_热力环流与风
[输出] D:\4_data\rujing_out\rujing_热力环流与风.json (39306 字节)
[统计] 主卡: 1 / 子卡: 8 / 链: 1
[链元数据] G-P1-2-热力环流与风 / 地理 / 因果链
[v6.0] article=1147 字 / self_test=4 题 / version=1.0.0
[v6.0] domain=自然地理·大气与气候 / lines=[2] / module=...
[链元数据] D:\4_data\rujing_out\chain_meta_2026-08-16_热力环流与风.json
```

**输入**：1 套卡片目录（10 个文件）
**输出**：1 个 rujing CardPackage JSON（~40KB）+ 1 个 chain_meta JSON

---

## _push_to_rujing.py

**作用**：把 rujing CardPackage JSON 推送到手机端 rujing APP。

**用法**：

```bash
# 推最近 1 个（默认）
python -X utf8 _push_to_rujing.py

# 推指定文件
python -X utf8 _push_to_rujing.py D:\4_data\rujing_out\rujing_xxx.json

# 推所有
python -X utf8 _push_to_rujing.py /all

# 列出可推送
python -X utf8 _push_to_rujing.py /list
```

**输出示例**：

```
=== 推送 rujing CardPackage ===
文件: D:\4_data\rujing_out\rujing_热力环流与风.json  (39306 bytes)
目标: http://192.168.43.1:18999/upload

✅ status: 200  (耗时 0.4s)
response: {"status":"imported","cards":9,"chains":1}

import_result:
{
  "cards": 9,
  "chains": 1,
  "time": 1787057107054,
  "result": "OK: 9 cards / 1 chains"
}

subjects:
{
  "subjects": [{"subject": "地理", "chain_count": 1, "card_count": 9, ...}]
}
```

---

## 完整流程（autoclaw 端 git push 后）

```bash
# willi 端接收（git pull）
cd D:\4_data\knowledge_cards
git pull

# 1. 校验
python -X utf8 autoclaw_kit/07_validate.py 地理/cards/2026-08-16_热力环流与风
# 预期: PASS

# 2. 转换
python -X utf8 autoclaw_kit/08_tools/ru_cardpkg_convert.py \
  --card-dir 地理/cards/2026-08-16_热力环流与风 \
  --output D:\4_data\rujing_out\rujing_热力环流与风.json

# 3. 推送
python -X utf8 autoclaw_kit/08_tools/_push_to_rujing.py
# 预期: imported 9 cards / 1 chain

# 4. 看效果
# 手机端 rujing app 首页 → 看到"地理"入口
# 点开 → 看到 1 链 → 9 张卡
```

总耗时 < 5 秒。

---

## 故障排查

| 现象 | 原因 | 解法 |
|------|------|------|
| `Connection refused 192.168.43.1:18999` | 手机 rujing app 没启 / 网络断 | 检查手机 + PC 同网络 |
| `HTTP 500 Unexpected Text in JSON` | rujing CardPackage JSON 损坏 | 重新跑 `ru_cardpkg_convert.py` |
| `imported 0 cards` | chain_meta.article / self_test 缺失 | 检查 main.json back_detail ≥ 800 字 |
| `subjects: []` 推完 | rujing 端没启动 / archive 没跑 | 检查 rujing app |
| 推送后手机看不到新学科 | subject 拼写错 | 用 HISTORY/GEOGRAPHY 等 enum |
| `urllib.error.URLError` | Python 3.14 兼容问题 | 用 `-X utf8` 启动 |
