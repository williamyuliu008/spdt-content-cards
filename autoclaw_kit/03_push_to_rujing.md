# 推送到 rujing 流程

> 本文档是 willi 端（PC）的处理流程，autoclaw 端无需阅读。
> 但理解流程有助于 autoclaw 端把握产出节奏（如定稿时间点）。

---

## §0 推送方要做什么（极简）

```bash
# 1. 准备 1 套卡片（按 02_spec_card_v1.0.md）
# 2. 跑校验
python -X utf8 autoclaw_kit/07_validate.py 地理/cards/2026-08-16_热力环流与风
# 3. git push
cd D:\4_data\knowledge_cards
git add 地理/cards/2026-08-16_热力环流与风/
git commit -m "cards(地理): +热力环流与风(8)，自然地理大气模块试产"
git push origin main
```

**完事。** willi 端自动接收。

---

## §1 willi 端处理流程（PC 端）

### §1.1 接收（git pull）

```bash
cd D:\4_data\knowledge_cards
git pull origin main
```

预期：拉取 autoclaw 推送的 commit。

### §1.2 校验（必做）

```bash
python -X utf8 autoclaw_kit/07_validate.py <学科>/cards/<套卡目录>
```

**校验失败的套卡不进入下一步**，回退给 autoclaw 修正。

### §1.3 转换（autoclaw 格式 → rujing CardPackage v6.0）

```bash
python -X utf8 autoclaw_kit/08_tools/ru_cardpkg_convert.py \
  --card-dir 地理/cards/2026-08-16_热力环流与风 \
  --output D:/4_data/rujing_out/rujing_热力环流与风.json
```

**转换做的事**：
- 主卡 `back_detail` (800-1200字) → `chain.article`（长文）
- 主卡 `exam_questions[]` (5-6道) → `chain.self_test[]`（自测题）
- autoclaw 字段 → rujing CardPackage v6.0 格式
- 加 `version: 1.0.0` + `update_log: [首次导入]`
- 加 `chain_meta` 数组（让 rujing 一次读 chain + cards）

### §1.4 推送（rujing CardPackage → rujing APP）

```bash
python -X utf8 autoclaw_kit/08_tools/_push_to_rujing.py
```

**推送做的事**：
- 启动 PC 端 HTTP server（监听 0.0.0.0:8080）
- 把 rujing_*.json 暴露到 PC 8080
- 调用手机 RujingHttpServer 端 `/upload` 端点
- rujing APP 收到后：
  - 解析 CardPackage
  - 写入本地 DB（chain + cards + article + self_test）
  - 写 article.md 到 filesDir/rujing/articles/
  - 自动触发 Indexed by Index.ets（ForEach getDistinctSubjects）
- 完成后：手机端首页显示新学科入口

### §1.5 验证

```bash
# 看 rujing 端导入结果
curl http://192.168.43.1:18999/subjects
# 预期：["地理": "1 链 / 9 张卡"]
```

---

## §2 端到端跑过的案例（2026-08-18）

**输入**：
- 1 套地理卡（9 张：1 主 + 8 子）
- autoclaw 端产出位置：`D:\4_data\knowledge_cards\地理\cards\2026-08-16_热力环流与风\`

**流程**：
1. `07_validate.py` → 0 错误 0 警告 → PASS
2. `ru_cardpkg_convert.py` → 输出 39KB JSON（含 chain_meta + 9 张卡）
3. `_push_to_rujing.py` → POST 39KB 到 rujing APP /upload
4. 端到端结果：手机端 /subjects 返回 `[地理: 1 链 / 9 张卡]`

**耗时**：全流程 < 5 秒

---

## §3 rujing 端字段映射表（autoclaw → rujing）

| autoclaw 字段 | rujing 字段 | 转换说明 |
|----------------|-------------|----------|
| **chain.chain_id** | chain.chain_id | 去前导 `geography/` |
| **chain.subject** (HISTORY) | chain.subject (历史) | enum 翻译 |
| **chain.chain_type** | chain.chain_type | 直接 |
| **chain.domain** | chain.domain | 直接 |
| **chain.lines** | chain.lines | 直接 |
| **chain.module** | chain.module | 直接 |
| **chain.topic** | chain.topic | 直接 |
| **chain.is_main_line** | chain.is_main_line | 直接 |
| **chain.status** | chain.status | 直接 |
| **main.back_detail** | **chain.article** | **长文升级**（主卡 → 链级）|
| **main.exam_questions** | **chain.self_test** | **自测题升级**（主卡 → 链级）|
| **chain (元数据)** | chain.version = 1.0.0 | 首次导入 |
| **chain (元数据)** | chain.last_updated = now | 时间戳 |
| **chain (元数据)** | chain.update_log = [首次导入] | 审计 |
| main.card_id | card.card_id | 去前导 `geography/` |
| main.card_type (STRATEGY) | card.card_type (心法卡) | 映射 |
| K0X.card_type (KNOWLEDGE) | card.card_type (节点卡) | 映射 |
| main.chain_role (BACKGROUND) | card.chain_role (背景条件) | 中文映射 |
| K0X.chain_role (TRIGGER) | card.chain_role (触发事件) | 中文映射 |
| K0X.parent_card | card.parent_card | 直接 |
| main.sources | card.sources | 直接 |
| K0X.sources | card.sources | 直接 |
| main.exam_questions | card.exam_questions | 保留主卡上 |
| main.open_questions | card.open_questions | 直接 |
| main.confidence | card.confidence | 直接 |
| main.front / back_core / back_detail | card.front / back_core / back_detail | 直接 |
| main.tags | card.tags | 直接 |
| main.maturity (RAW) | card.maturity (生) | 映射 |
| chain.narrative (空) | chain.narrative (空) | 兼容字段 |

---

## §4 rujing 端 4 Tab 展示（v6.0 新增）

rujing APP `ChainReaderPage` 链详情页有 3 个 Tab：

| Tab | 内容 | 来源 |
|-----|------|------|
| **📖 文章** | chain.article 长文 + "开始自测"按钮 | autoclaw main.back_detail |
| **🃏 卡片** | 知识点卡片（1 主 + 8 子）| autoclaw 全套 |
| **✏️ 自测** | 自测题（5-6 道）| autoclaw main.exam_questions |

错题自动入 `wrong_answers` 表，可跨链聚合。

---

## §5 故障排查

| 现象 | 原因 | 解法 |
|------|------|------|
| 校验 5+ 错误 | autoclaw 端没按规范 | 修正字段，重跑 |
| 转换后 JSON < 30KB | 主卡 back_detail 太短 | 主卡长文 ≥ 800 字 |
| POST /upload 500 | JSON 解析失败 | 校验 JSON 格式 |
| 推 rujing 后看不到新学科 | HTTP 超时 | 重启 PC 8080 server |
| 学科显示但点不开 | 链元数据没写 | 检查 chain_meta |
| chain.article 为空 | 主卡 back_detail 缺失 | 必须 800-1200 字 |

---

## §6 批量推送

autoclaw 一次产 10+ 套卡时，willi 端用 `08_tools/_batch_push.py`（待写）：

```bash
python -X utf8 autoclaw_kit/08_tools/_batch_push.py 地理/cards/2026-08-1*
# 自动跑所有 2026-08-1 开头的目录
```

当前单套走 `_push_to_rujing.py`，批量脚本稍后补。
