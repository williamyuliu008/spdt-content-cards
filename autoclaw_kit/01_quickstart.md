# Quickstart · 5 分钟做出 1 套卡片

> 目标：5 分钟内，按规范产出 1 套知识卡片，git push 完事。

---

## Step 1：确定套卡参数（1 min）

需要确定 4 个参数：

| 参数 | 例子 | 说明 |
|------|------|------|
| 学科前缀 | `G` (地理) | 必查 02_spec §1.1 |
| 模块号 | `1` | 学科内大单元 |
| 概念号 | `2` | 模块内小节号（查 autoclaw 概念清单） |
| 概念名 | `热力环流与风` | 中文，不超过 12 字 |

---

## Step 2：建目录（30 sec）

```bash
mkdir -p 地理/cards/2026-08-16_热力环流与风
cd 地理/cards/2026-08-16_热力环流与风
```

目录命名规则：`YYYY-MM-DD_概念名`（日期是这套卡定稿日）

---

## Step 3：复制模板（30 sec）

```bash
# 从 autoclaw_kit/05_templates/ 复制
cp ../../autoclaw_kit/05_templates/chain.json ./
cp ../../autoclaw_kit/05_templates/main.json ./
cp ../../autoclaw_kit/05_templates/K01.json K01.json
# 复制 N 次（按子卡数，6-10 张）
for i in $(seq 2 8); do cp K01.json K0${i}.json; done
```

---

## Step 4：填字段（2-3 min）

按 02_spec_card_v1.0.md 填：

1. **chain.json**：
   - `chain_id`: `geography/G-P1-2-热力环流与风`（去掉前导 `geography/` 也行，转换器自动处理）
   - `chain_title`: `热力环流与风`
   - `subject`: `GEOGRAPHY`（自动转中文 `地理`）
   - `domain`: `自然地理·大气与气候`
   - `module`: `模块一·自然地理基础`
   - `topic`: `专题1 大气与气候`
   - `status`: `trial_production`（试产）/ `done`（定稿）
   - `is_main_line`: `true`（主线条）/ `false`（辅助线）
   - `total_cards`: `9`（1 主 + 8 子）

2. **main.json**（主卡 = 链长文 + 自测题 source）：
   - `card_id`: `G-M1-2-MAIN-001`
   - `front`: 30-100 字问题，以 `？` 结尾
   - `back_core`: 150-250 字核心答案
   - `back_detail`: **800-1200 字长文**（会升为链 article）
   - `tags`: 必含 `#domain/自然地理` `#content/热力环流` `#考频/★★★` `#朝代/现代` 等
   - `sources[]`: 3-8 条参考资料，至少 1 条 type=academic
   - `exam_questions[]`: **5-6 道题**（会升为链 self_test）
   - `open_questions[]`: 5-10 条存疑（每条 ≤ 50 字）
   - `confidence`: `high`（0 存疑）/ `medium`（1-3 存疑）/ `low`（4+ 存疑）

3. **K01.json ~ K08.json**（子卡）：
   - `card_id`: `G-M1-2-K0X-001`（X = 01-08）
   - `parent_card`: `G-M1-2-MAIN-001`
   - `front`: 30-100 字问题
   - `back_core`: 150-250 字
   - `back_detail`: 200-350 字（子卡精简版）
   - `tags`: 至少 `#domain/` `#content/` `#考频/` 三类
   - `sources[]`: 1-3 条
   - `confidence`: 同上

---

## Step 5：本地校验（30 sec）

```bash
# 回到仓库根
cd ../../..

# 跑校验（传 cards/ 父目录，不是单套）
python -X utf8 autoclaw_kit/07_validate.py 地理/cards
# 或只校验 1 套
python -X utf8 autoclaw_kit/07_validate.py 地理/cards  # 全量
# 单套模式：把套卡复制到一个临时 cards/ 里再跑
```

**期望输出**：`套卡数: 1 | 错误: 0 | 警告: 0`  → PASS

**如果有错**：看 ERROR 行，修正后重跑。

---

## Step 6：git push（30 sec）

```bash
cd D:\4_data\knowledge_cards
git add 地理/cards/2026-08-16_热力环流与风/
git commit -m "cards(地理): +热力环流与风(8)，自然地理大气模块试产"
git push origin main
```

**完事。** willi 端会自动：
1. git pull
2. 跑转换器 + 推送脚本
3. rujing APP 首页出现"地理"入口
4. 1 套 9 张卡入库

---

## 完整示例

直接看 `06_example/2026-08-16_热力环流与风/`（已通过校验，9 张卡齐全）。

---

## 卡壳了？

| 现象 | 怎么办 |
|------|--------|
| 校验有 5+ 错误 | 看 02_spec_card_v1.0.md 对应字段规范 |
| 不知道 `domain/lines/module/topic` 怎么填 | 查 autoclaw 概念清单（如 `_62_concepts.json`） |
| 子卡要不要都不同？ | 是，每张子卡讲一个独立小点 |
| 跨学科概念（如"资本主义萌芽"） | 拆成 2 套卡（历史 1 套 + 政治 1 套），不同 chain_id |
| 不知道考频给几星 | 查高考/校考真题 5 年内出现次数，5+ = ★★★ / 2-4 = ★★ / 1 = ★ |
| git push 权限不够 | 报 willi 加 GitHub collaborator |

---

5 分钟版本就这些。详细规范看 02_spec_card_v1.0.md。
