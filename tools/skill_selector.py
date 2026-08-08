# -*- coding: utf-8 -*-
"""
skill_selector.py
SPDT-004 历史写作 Skill 三层漏斗选择器

三层漏斗：
  Layer 1：硬性过滤（准入/禁止条件）
  Layer 2：加权评分（内容标签 × 叙事潜力 × 人物标签 × 史观）
  Layer 3：语境修正（章节位置 + Skill 连续性 + 用户偏好）

用法：
  python skill_selector.py [卡片包.json] [--context JSON] [--top N]

示例：
  python skill_selector.py ../../专题报告_帝国的崩塌_materials_v1.json --context '{"chapter_position":"opening"}'
"""
import json, re, sys, argparse
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────
# 路径配置
# ─────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
# 指向 SPDT-004 根目录（SKILL_REGISTRY.json 所在）
SPD004_ROOT = Path(r"D:\2_products\education\SPDT-004_EduContent\docs\04-Skills")
REGISTRY_PATH = SPD004_ROOT / "SKILL_REGISTRY.json"


# ─────────────────────────────────────────────
# Layer 0：注册表加载
# ─────────────────────────────────────────────

def load_registry() -> dict:
    with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_all_skills(registry: dict) -> list[dict]:
    return registry.get('skills', [])


def get_skill(registry: dict, skill_id: str) -> Optional[dict]:
    return next((s for s in registry['skills'] if s['skill_id'] == skill_id), None)


# ─────────────────────────────────────────────
# Layer 1：硬性过滤
# ─────────────────────────────────────────────

def collect_all_tags(cards: list[dict]) -> set[str]:
    """从卡片集合中提取所有标签（tags + concepts + type推断 + 文本关键词）。"""
    tags = set()
    for c in cards:
        # 顶层 tags 字段
        tags.update(c.get('tags', []))
        # concepts
        for con in c.get('concepts', []):
            tags.add(str(con))
        # type 字段（同时映射为隐含标签）
        t = c.get('type', '')
        if t:
            tags.add(f"#type/{t}")
            # 类型 → 隐含标签映射（Skill Layer 1 硬过滤的 fallback）
            TYPE_TO_TAG = {
                'strategy_cause': 'cause',
                'strategy_impact': 'impact',
                'strategy_turning': 'turning',
                'node': 'node',
                'chain': 'chain',
            }
            if t in TYPE_TO_TAG:
                tags.add(TYPE_TO_TAG[t])
        # front/back 中的关键词
        text = c.get('front', '') + c.get('back', '')
        for kw in ['抉择', '决策', '传记', '制度', '结构', '技术', '工业',
                   '思想', '观念', '普通人', '微观', '社会', '反转', '修正',
                   '世纪', '千年', '多视角', '复调', '碰撞', '中西', '战争',
                   '革命', '改革', '崩溃', '衰落', '兴起']:
            if kw in text:
                tags.add(kw)
    return tags


def collect_card_types(cards: list[dict]) -> dict[str, int]:
    """统计各类型卡片数量。"""
    counts = {}
    for c in cards:
        t = c.get('type', 'unknown')
        counts[t] = counts.get(t, 0) + 1
    return counts


def layer1_hard_filter(skill: dict, cards: list[dict],
                       all_tags: set[str], type_counts: dict) -> dict:
    """
    执行 Layer 1 硬性过滤。

    规则来自 SKILL_REGISTRY.json 的 layer1_hard_filter 字段。
    返回 {"passed": bool, "reasons": list, "details": dict}
    """
    hf = skill.get('layer1_hard_filter', {})
    reasons = []
    details = {}
    passed = True

    # ── require_any_tag：至少有一个在 tags 中 ──
    if 'require_any_tag' in hf:
        required = hf['require_any_tag']
        matched = [t for t in required if t in all_tags or t.lower() in [x.lower() for x in all_tags]]
        details['require_any_tag'] = {'required': required, 'matched': matched}
        if not matched:
            reasons.append(f"require_any_tag: 无匹配（需至少一个：{required}）")
            passed = False

    # ── require_all_tags：全部必须在 tags 中 ──
    if 'require_all_tags' in hf:
        required = hf['require_all_tags']
        matched = [t for t in required if t in all_tags or t.lower() in [x.lower() for x in all_tags]]
        details['require_all_tags'] = {'required': required, 'matched': matched}
        if len(matched) < len(required):
            reasons.append(f"require_all_tags: 缺 {set(required)-set(matched)}")
            passed = False

    # ── forbid_any_tag：有任一则禁止 ──
    if 'forbid_any_tag' in hf:
        forbidden = hf['forbid_any_tag']
        found = [t for t in forbidden if t in all_tags]
        details['forbid_any_tag'] = {'forbidden': forbidden, 'found': found}
        if found:
            reasons.append(f"forbid_any_tag: 发现禁止标签 {found}")
            passed = False

    # ── min_strategy_cause / min_strategy_impact ──
    if 'min_strategy_cause' in hf:
        actual = type_counts.get('strategy_cause', 0)
        details['min_strategy_cause'] = {'required': hf['min_strategy_cause'], 'actual': actual}
        if actual < hf['min_strategy_cause']:
            reasons.append(f"strategy_cause 数量不足：{actual} < {hf['min_strategy_cause']}")
            passed = False

    if 'min_strategy_impact' in hf:
        actual = type_counts.get('strategy_impact', 0)
        details['min_strategy_impact'] = {'required': hf['min_strategy_impact'], 'actual': actual}
        if actual < hf['min_strategy_impact']:
            reasons.append(f"strategy_impact 数量不足：{actual} < {hf['min_strategy_impact']}")
            passed = False

    # ── min_macro_tag ──
    if 'min_macro_tag' in hf:
        macro_keywords = ['#macro-structure', '#macro-micro', '制度', '结构', '宏观']
        matched = [t for t in all_tags if t in macro_keywords or any(kw in t for kw in macro_keywords)]
        details['min_macro_tag'] = {'required': 1, 'matched_count': len(matched)}
        if len(matched) < hf['min_macro_tag']:
            reasons.append(f"缺少宏观结构标签")
            passed = False

    # ── min_actor_tag ──
    if 'min_actor_tag' in hf:
        actor_keywords = ['#actor', '#decision_point', '抉择', '决策', '传记',
                          '人物', '理想主义', '改革者']
        matched = [t for t in all_tags if any(kw in t for kw in actor_keywords)]
        details['min_actor_tag'] = {'required': 1, 'matched_count': len(matched)}
        if len(matched) < hf['min_actor_tag']:
            reasons.append(f"缺少人物/决策标签")
            passed = False

    # ── 通用：implementation_status ≠ planned ──
    # planned 状态的 skill 默认不推荐（除非用户明确指定）
    impl = skill.get('implementation_status', 'planned')
    if impl == 'planned':
        details['implementation_status'] = impl
        # 不作为硬性禁止，但记录在原因中

    return {
        'passed': passed,
        'reasons': reasons,
        'details': details,
        'implementation_status': impl
    }


# ─────────────────────────────────────────────
# Layer 2：加权评分
# ─────────────────────────────────────────────

def extract_card_features(cards: list[dict]) -> dict:
    """从卡片集合提取用于 Layer 2 评分的特征。"""
    all_tags = collect_all_tags(cards)

    # 叙事潜力标签
    narrative_tags = ['#narrative/cause-effect', '#macro-micro', '#decision-point',
                      '#dramatic', '#idealistic-actor', '#rigid-institution',
                      '#civilization-A', '#civilization-B', '#tech-breakthrough',
                      '#intellectual-crisis', '#ordinary-people', '#popular-myth',
                      '#revisionist', '#longue-duree', '#multiple-perspectives']

    # 人物标签
    actor_tags = ['#actor', '#actor-tag', '抉择', '决策', '传记', '人物',
                  '#actor-type/idealistic', '#heroic-triumph']

    # 内容标签（来自 domain_tags + style_tags 的并集）
    content_tags = [t for t in all_tags if any(
        t.startswith(p) for p in ['#domain/', '#style/', '#content/'])
    ]

    # 史观标签
    historiography_tags = [t for t in all_tags if t.startswith('#historiography')]

    return {
        'all_tags': all_tags,
        'narrative_tags': narrative_tags,
        'actor_tags': actor_tags,
        'content_tags': content_tags,
        'historiography_tags': historiography_tags,
        'narrative_match_count': len([t for t in all_tags if t in narrative_tags]),
        'actor_match_count': len([t for t in all_tags if t in actor_tags or any(kw in t for kw in actor_tags)]),
    }


def layer2_weighted_score(skill: dict, cards: list[dict], features: dict) -> dict:
    """
    执行 Layer 2 加权评分。
    权重来自 SKILL_REGISTRY.json 的 layer2_weights 字段。

    评分维度：
      维度1（35%）：内容标签匹配（#domain/ #style/）
      维度2（30%）：叙事潜力标签匹配（#decision-point #narrative/cause-effect 等）
      维度3（20%）：人物标签匹配（#actor 相关）
      维度4（15%）：史观兼容性（#historiography/）

    特殊加成：
      - Skill 的 style_tags 与卡片 tags 精确或模糊匹配 → +0.10
      - compatible_card_packages 命中 → +0.05
    """
    weights = skill.get('layer2_weights', {
        'content_tag_match': 0.35,
        'narrative_potential': 0.30,
        'actor_tag': 0.20,
        'historiography': 0.15
    })

    all_tags = features['all_tags']
    skill_domain = set(skill.get('domain_tags', []))
    skill_style = set(skill.get('style_tags', []))

    # ── 维度1：内容标签匹配 ──
    # 精确匹配 + 子标签匹配（支持 #历史/唐/XXX 匹配 #domain/历史）
    def tag_matches_parent(child_tag, parent_tags):
        for pt in parent_tags:
            if child_tag == pt:
                return True
            # 子标签匹配（如 #历史/唐/安史之乱 → #domain/历史）
            if child_tag.startswith(pt + '/') or pt.startswith(child_tag + '/'):
                return True
            # 共享前缀（如 #历史/唐/XXX 与 #domain/历史 共享 #历史）
            pt_parts = pt.split('/')
            ct_parts = child_tag.split('/')
            if len(pt_parts) >= 2 and len(ct_parts) >= 2 and pt_parts[0] == ct_parts[0]:
                return True
        return False

    overlap = 0
    for ct in all_tags:
        if ct in skill_domain or ct in skill_style:
            overlap += 1
        elif tag_matches_parent(ct, skill_domain) or tag_matches_parent(ct, skill_style):
            overlap += 0.5  # 子标签部分匹配
    denom = len(skill_domain.union(skill_style)) or 1
    dim_content = min(overlap / denom, 1.0)

    # ── 维度2：叙事潜力标签匹配 ──
    # 模糊匹配：skill 的 style_tags（如 #decision-point）与卡片的标签做词根比对
    style_overlap = 0
    for st in skill_style:
        st_normalized = st.lower().replace('-', '').replace('_', '')
        for ct in all_tags:
            ct_normalized = ct.lower().replace('-', '').replace('_', '')
            if st_normalized in ct_normalized or ct_normalized in st_normalized:
                style_overlap += 1
    dim_narrative = min(style_overlap / max(len(skill_style), 1), 1.0)

    # ── 维度3：人物标签匹配 ──
    actor_overlap = len([t for t in all_tags if t in features['actor_tags']])
    dim_actor = min(actor_overlap / 1, 1.0)

    # ── 维度4：史观兼容性 ──
    histo_overlap = len([t for t in all_tags if t in features['historiography_tags']])
    dim_histo = min(histo_overlap / 1, 1.0)

    # ── 计算总分 ──
    total = (
        weights['content_tag_match'] * dim_content +
        weights['narrative_potential'] * dim_narrative +
        weights['actor_tag'] * dim_actor +
        weights['historiography'] * dim_histo
    )

    # ── 额外加成：Skill style_tags 模糊命中 ──
    style_bonus = 0.0
    if style_overlap > 0:
        style_bonus = 0.10  # 有 style tag 匹配，加成 0.10

    # ── 额外加成：主题精确匹配 ──
    # 当 skill 的核心概念标签（如 #decision-point）与卡片的标签精确或强语义匹配时，
    # 给予显著加成（0.15），而非靠权重微调
    thematic_keywords = {
        'hist-decisive-moment': ['decision', '抉择', '决策', '传记', '人物'],
        'hist-institution-kills': ['idealistic', '制度', '悲剧', '变法'],
        'hist-reversal': ['反转', '修正', 'revisionist'],
        'hist-macro-micro': ['制度', '结构', '宏观', '微观'],
    }
    thematic_bonus = 0.0
    sid = skill.get('skill_id', '')
    if sid in thematic_keywords:
        kw_list = thematic_keywords[sid]
        for kw in kw_list:
            if kw in all_tags or any(kw in t for t in all_tags):
                thematic_bonus = 0.15
                break

    # ── 额外加成：compatible_card_packages 命中 ──
    package_bonus = 0.0
    compat = skill.get('compatible_card_packages', [])
    if compat:
        for pkg in compat:
            if any(pkg in str(c.get('card_id', '')) or pkg in str(c.get('chain_id', ''))
                   for c in cards):
                package_bonus = 0.05
                break

    final_score = min(total + style_bonus + thematic_bonus + package_bonus, 1.0)

    return {
        'score': round(final_score, 3),
        'dimension_scores': {
            'content_tag_match': {'weight': weights['content_tag_match'], 'raw': round(dim_content, 3)},
            'narrative_potential': {'weight': weights['narrative_potential'], 'raw': round(dim_narrative, 3)},
            'actor_tag': {'weight': weights['actor_tag'], 'raw': round(dim_actor, 3)},
            'historiography': {'weight': weights['historiography'], 'raw': round(dim_histo, 3)},
        },
        'style_overlap': style_overlap,
        'style_bonus': style_bonus,
        'thematic_bonus': thematic_bonus,
        'package_bonus': package_bonus,
        'matched_tags': list(skill_domain.union(skill_style) & all_tags),
    }


# ─────────────────────────────────────────────
# Layer 3：语境修正
# ─────────────────────────────────────────────

CONTEXT_RULES: dict = {
    "chapter_position": {
        "opening": {
            "boost": ["hist-decisive-moment", "hist-traceability-causality", "hist-civilization-clash"],
            "reason": "开篇需要建立宏观框架或人物引入"
        },
        "middle": {
            "boost": ["hist-macro-micro", "hist-institution-kills"],
            "reason": "中间章节需要深入分析"
        },
        "closing": {
            "boost": ["hist-long-duration", "hist-reversal"],
            "reason": "结尾需要反思和升维"
        }
    },
    "previous_skill": {
        "hist-macro-micro": {
            "boost_next": ["hist-institution-kills", "hist-traceability-causality"],
            "penalize": ["hist-decisive-moment"],
            "reason": "微观→结构分析的自然延伸"
        },
        "hist-decisive-moment": {
            "boost_next": ["hist-traceability-causality", "hist-institution-kills", "hist-reversal"],
            "penalize": ["hist-decisive-moment"],
            "reason": "抉择→因果涟漪或制度反思"
        },
        "hist-traceability-causality": {
            "boost_next": ["hist-reversal", "hist-decisive-moment"],
            "penalize": [],
            "reason": "因果链后的认知反转"
        }
    }
}


def layer3_context_modification(skill: dict,
                                  layer2_score: float,
                                  user_context: dict) -> dict:
    """
    执行 Layer 3 语境修正。
    基于章节位置、Skill 连续性、用户风格偏好调整得分。
    """
    skill_id = skill['skill_id']
    modifications = []
    delta = 0.0

    # ── 章节位置修正 ──
    pos = user_context.get('chapter_position')
    if pos and pos in CONTEXT_RULES['chapter_position']:
        rule = CONTEXT_RULES['chapter_position'][pos]
        if skill_id in rule.get('boost', []):
            delta += 0.08
            modifications.append(f"[位置-boost] {rule['reason']} (+0.08)")
        else:
            # 没有被 boost 但在中间/结尾位置，不惩罚
            pass

    # ── Skill 连续性修正 ──
    prev = user_context.get('previous_skill')
    if prev and prev in CONTEXT_RULES['previous_skill']:
        rule = CONTEXT_RULES['previous_skill'][prev]
        if skill_id in rule.get('boost_next', []):
            delta += 0.06
            modifications.append(f"[连续-boost] 接续 {prev}：{rule['reason']} (+0.06)")
        elif skill_id in rule.get('penalize', []):
            delta -= 0.05
            modifications.append(f"[连续-penalty] {skill_id} 不适合接续 {prev} (-0.05)")

    # ── 用户风格偏好覆盖 ──
    preferred = user_context.get('user_style_preference')
    if preferred and preferred in skill.get('preferred_style_packs', []):
        delta += 0.05
        modifications.append(f"[偏好] 用户偏好 {preferred}，Skill 匹配 (+0.05)")

    # ── 禁用偏好惩罚 ──
    disallowed = user_context.get('disallowed_style_packs', [])
    if disallowed:
        # 简单处理：如果禁用列表中有完全冲突的文风包
        pass

    # ── 计算修正后得分 ──
    final_score = min(max(layer2_score + delta, 0.0), 1.0)

    return {
        'delta': round(delta, 3),
        'final_score': round(final_score, 3),
        'modifications': modifications,
        'reason': modifications[-1] if modifications else "无语境修正"
    }


# ─────────────────────────────────────────────
# 主入口
# ─────────────────────────────────────────────

def select_skill(cards: list[dict],
                 user_context: Optional[dict] = None) -> dict:
    """
    三层漏斗主函数。

    参数：
        cards: 卡片集合（list[dict]），也支持 dict（自动提取 cards 字段）
        user_context: 用户语境（dict），可选键：
    """
    if user_context is None:
        user_context = {}

    # ── 容错：cards 可能是 dict，自动提取 cards 字段 ──
    if isinstance(cards, dict):
        cards = (cards.get('cards') or cards.get('materials_cards') or
                 [v for v in cards.values() if isinstance(v, list)] or
                 [v for v in cards.values() if isinstance(v, dict)] or [])

    # ── 用户直接指定 skill，跳过选择 ──
    if user_context.get('target_skill'):
        registry = load_registry()
        skill = get_skill(registry, user_context['target_skill'])
        if not skill:
            return {'error': f"未找到 skill: {user_context['target_skill']}"}
        return {
            'recommended_skill': skill['skill_id'],
            'score': 0.0,
            'final_score': 0.0,
            'alternatives': [],
            'layer1_result': {'passed': True, 'reasons': ['用户指定']},
            'layer2_result': {'score': 0.0},
            'layer3_result': {'final_score': 0.0},
            'recommendation_reason': f"用户直接指定：{skill['skill_id']}"
        }

    registry = load_registry()
    all_skills = get_all_skills(registry)
    all_tags = collect_all_tags(cards)
    type_counts = collect_card_types(cards)
    features = extract_card_features(cards)

    results = []

    for skill in all_skills:
        sid = skill['skill_id']

        # ── Layer 1 ──
        l1 = layer1_hard_filter(skill, cards, all_tags, type_counts)
        if not l1['passed']:
            results.append({
                'skill_id': sid,
                'skill_name': skill['skill_name'],
                'layer1': l1,
                'layer2': None,
                'layer3': None,
                'final_score': 0.0,
                'eliminated': True,
                'elimination_reason': '; '.join(l1['reasons']) if l1['reasons'] else '未通过硬过滤'
            })
            continue

        # ── Layer 2 ──
        l2 = layer2_weighted_score(skill, cards, features)
        layer2_score = l2['score']

        # ── Layer 3 ──
        l3 = layer3_context_modification(skill, layer2_score, user_context)
        final_score = l3['final_score']

        results.append({
            'skill_id': sid,
            'skill_name': skill['skill_name'],
            'layer1': l1,
            'layer2': l2,
            'layer3': l3,
            'score': layer2_score,
            'final_score': final_score,
            'eliminated': False,
            'implementation_status': skill.get('implementation_status', 'unknown')
        })

    # ── 排序：final_score 降序，排除 eliminated ──
    passed = [r for r in results if not r['eliminated']]
    passed.sort(key=lambda x: x['final_score'], reverse=True)

    if not passed:
        # 全被 Layer 1 过滤，fallback 到最高分的 planned skill
        fallback = sorted(results, key=lambda x: x['final_score'], reverse=True)
        return {
            'recommended_skill': fallback[0]['skill_id'],
            'score': fallback[0].get('score', 0.0),
            'final_score': fallback[0].get('final_score', 0.0),
            'alternatives': [],
            'recommendation_reason': "无通过 Layer 1 的 Skill，Fallback 到最高分",
            'warning': "所有 Skill 均未通过 Layer 1 硬过滤",
            'all_results': results
        }

    # ── 构建推荐结果 ──
    best = passed[0]
    alternatives = passed[1:5]  # 最多返回 4 个备选

    # 生成推荐理由
    reasons = []
    if best['layer2'] and best['layer2'].get('matched_tags'):
        reasons.append(f"标签匹配：{', '.join(best['layer2']['matched_tags'][:3])}")
    if best['layer3'] and best['layer3'].get('modifications'):
        reasons.append(f"语境加成：{best['layer3']['modifications'][-1]}")
    if best['implementation_status'] == 'stable':
        reasons.append("（stable 状态）")

    return {
        'recommended_skill': best['skill_id'],
        'skill_name': best['skill_name'],
        'score': best['score'],
        'final_score': best['final_score'],
        'alternatives': [
            {
                'skill_id': r['skill_id'],
                'skill_name': r['skill_name'],
                'final_score': r['final_score']
            }
            for r in alternatives
        ],
        'layer1_result': {
            'skill_id': best['skill_id'],
            'passed': best['layer1']['passed'],
            'implementation_status': best['layer1'].get('implementation_status')
        },
        'layer2_result': {
            'score': best['score'],
            'dimension_scores': best['layer2']['dimension_scores'] if best['layer2'] else {},
            'package_bonus': best['layer2']['package_bonus'] if best['layer2'] else 0
        },
        'layer3_result': {
            'delta': best['layer3']['delta'],
            'final_score': best['layer3']['final_score'],
            'modifications': best['layer3']['modifications']
        },
        'recommendation_reason': '；'.join(reasons),
        'all_results': results
    }


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def main():
    global REGISTRY_PATH
    parser = argparse.ArgumentParser(description='SPDT-004 Skill Selector（三层漏斗）')
    parser.add_argument('cards_file', nargs='?', help='卡片包 JSON 文件路径')
    parser.add_argument('--context', '-c', default='{}',
                        help='用户语境 JSON 字符串，如 \'{"chapter_position":"opening"}\'')
    parser.add_argument('--top', '-n', type=int, default=1,
                        help='返回 top N 推荐（默认 1）')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='显示完整结果（含被过滤的 Skill）')
    parser.add_argument('--registry', '-r', default=None,
                        help=f'注册表路径（默认：{REGISTRY_PATH}）')
    args = parser.parse_args()

    # ── 注册表路径 ──
    if args.registry:
        REGISTRY_PATH = Path(args.registry)
    elif not REGISTRY_PATH.exists():
        REGISTRY_PATH = SCRIPT_DIR.parent / "SKILL_REGISTRY.json"

    # ── 加载卡片 ──
    if args.cards_file:
        cards_path = Path(args.cards_file)
        if not cards_path.exists():
            print(f"[ERROR] 卡片文件不存在: {cards_path}")
            sys.exit(1)
        with open(cards_path, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        # 自动识别卡片数组的 key（支持 cards / materials_cards / 顶层数组）
        if isinstance(raw, list):
            cards = raw
        elif isinstance(raw, dict):
            cards = (raw.get('cards') or raw.get('materials_cards') or
                     [v for v in raw.values() if isinstance(v, list)] or
                     [v for v in raw.values() if isinstance(v, dict)] or [])
            if not cards:
                print(f"[ERROR] 无法从文件中解析卡片数据（已知keys: {list(raw.keys())[:5]}）")
                sys.exit(1)
        else:
            cards = []
        print(f"[INFO] 已加载 {len(cards)} 张卡片")
    else:
        # 无输入文件时，用空卡片集测试（只检查注册表结构）
        cards = []
        print("[WARN] 未提供卡片文件，显示注册表摘要")
        registry = load_registry()
        for s in registry['skills']:
            print(f"  {s['skill_id']:35s} [{s['implementation_status']:10s}] {s['skill_name']}")
        sys.exit(0)

    # ── 解析语境 ──
    try:
        user_context = json.loads(args.context)
    except json.JSONDecodeError:
        user_context = {}

    # ── 执行选择 ──
    result = select_skill(cards, user_context)

    # ── 输出 ──
    print()
    print("=" * 60)
    print(f"[推荐] Skill: {result.get('recommended_skill', 'N/A')}"
          f" ({result.get('skill_name', '')})")
    print(f"[分数] Layer2={result.get('score', 0):.1%}  Layer3修正={result.get('final_score', 0):.1%}")
    print(f"[理由] {result.get('recommendation_reason', 'N/A')}")
    print()

    if result.get('alternatives'):
        print("== 备选 Skill ==")
        for i, alt in enumerate(result['alternatives'][:args.top - 1], 1):
            print(f"  {i}. {alt['skill_id']:30s} {alt['skill_name']:20s} {alt['final_score']:.1%}")

    if result.get('warning'):
        print(f"\n[WARN] {result['warning']}")

    # ── Verbose：显示完整结果 ──
    if args.verbose:
        print()
        print("== 完整结果 ==")
        for r in result.get('all_results', []):
            status = "[FILTERED]" if r['eliminated'] else "[PASS]"
            elim = f" ({r.get('elimination_reason', '')})" if r['eliminated'] else ""
            print(f"  {status:12s} {r['skill_id']:35s} {r['skill_name']:15s}"
                  f" 最终分={r['final_score']:.1%} {elim}")

    print()
    print("=" * 60)


if __name__ == '__main__':
    main()
