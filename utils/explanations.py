from collections import Counter
from typing import Dict, Any, List
import math


def build_ai_match_explanation(club: Dict[str, Any], user_map: Dict[str, Any]) -> Dict[str, Any]:
    """Extended AI explanation with diversity metrics and per-member detail.

    Returns dict keys:
      summary: str
      bullets: List[str]
      member_details: List[str]
      metrics: Dict[str, Any]
    """
    member_ids = club.get('member_ids', [])
    member_users = [user_map.get(mid, {}) for mid in member_ids]
    size = len(member_users) or 1

    ranks = [u.get('rank') for u in member_users if u.get('rank')]
    rank_unique = sorted(set(ranks))
    traits = [u.get('personality_trait') for u in member_users if u.get('personality_trait')]
    trait_counts = {t: traits.count(t) for t in sorted(set(traits))}
    interests_list = [u.get('interests', []) for u in member_users]
    flattened = [i for lst in interests_list for i in lst]
    interest_counts = Counter(flattened)
    unique_interests = len(interest_counts)
    primary_interest = club.get('primary_interest') or 'N/A'
    top_interest = interest_counts.most_common(1)[0][0] if interest_counts else primary_interest
    regions = [u.get('region') for u in member_users if u.get('region')]
    region_counts = Counter(regions)
    region_majority = region_counts.most_common(1)[0][0] if region_counts else 'N/A'

    def pct(part: int, whole: int) -> str:
        return f"{int((part/whole)*100)}%" if whole else "0%"

    interest_pct = pct(interest_counts.get(top_interest, 0), len(flattened))

    def shannon(counter: Counter) -> float:
        total = sum(counter.values()) or 1
        return round(-sum((c/total) * math.log(c/total) for c in counter.values() if c), 3)

    interest_shannon = shannon(interest_counts) if interest_counts else 0.0
    trait_shannon = shannon(Counter(traits)) if traits else 0.0
    rank_diversity_score = round(len(rank_unique) / size, 2)

    shared_interest_set = {i for i, c in interest_counts.items() if c > 1}
    member_details: List[str] = []
    for u in member_users:
        nick = u.get('nickname') or u.get('name') or 'user'
        region = u.get('region', 'N/A')
        rank = u.get('rank', 'N/A')
        trait = u.get('personality_trait', 'N/A')
        ints = u.get('interests', []) or []
        shared = [i for i in ints if i in shared_interest_set]
        member_details.append(
            f"{nick} | 지역:{region} | 직급:{rank} | 성향:{trait} | 관심사:{', '.join(ints) or '없음'} | 공유 관심사({len(shared)}): {', '.join(shared) or '-'}"
        )

    summary = (
        f"AI 매칭 요약: 지역 중심 '{region_majority}', 핵심 관심사 '{top_interest}' {interest_pct}, "
        f"직급 다양성 {len(rank_unique)}종 (점수 {rank_diversity_score}), 성향 다양성 지수 {trait_shannon}, 관심사 다양성 지수 {interest_shannon}."
    )

    region_dist = ', '.join(f"{r}:{pct(c, size)}" for r, c in region_counts.items()) or 'N/A'
    top3_interests = ', '.join(f"{i}:{c}" for i, c in interest_counts.most_common(3)) or 'N/A'
    trait_dist = ', '.join(f"{t}:{c}" for t, c in trait_counts.items()) or 'N/A'

    bullets: List[str] = [
        f"📍 지역 분포: {region_dist}",
        f"� 상위 관심사 Top3: {top3_interests}",
        f"� 직급 구성: {', '.join(rank_unique) or 'N/A'} (다양성지수 {rank_diversity_score})",
        f"🧠 성향 분포: {trait_dist} (Shannon {trait_shannon})",
        f"🗂 관심사 고유수: {unique_interests} (Shannon {interest_shannon})",
        f"🤝 공유 관심사 비율: {pct(len(shared_interest_set), unique_interests or 1)}",
        "✅ 다양성과 교집합 균형 → 관계형성 및 지속 활동 잠재력 상승",
    ]

    return {
        'summary': summary,
        'bullets': bullets,
        'member_details': member_details,
        'narrative': (
            f"이 클럽은 '{region_majority}' 지역을 기반으로 공통 관심사 '{top_interest}'를 핵심 연결 고리로 묶여 있습니다. "
            f"직급은 {', '.join(rank_unique) or '단일'}로 구성되어 수평적 대화 환경을 제공하며, 관심사 다양성(Shannon {interest_shannon})은 초기 아이디어 교환을 풍부하게 합니다. "
            f"동시에 공유 관심사 비율 {pct(len(shared_interest_set), unique_interests or 1)}는 팀 결속의 최소 기반을 확보하여 활동 주제를 빠르게 합의할 가능성이 높습니다. "
            f"성향 분포는 {trait_dist}로 과도한 극단 없이 안정적 상호작용을 기대할 수 있습니다. 첫 만남에서는 '{top_interest}' 관련 가벼운 경험 공유 → 추가 관심사 탐색 순으로 진행하면 자연스러운 온보딩이 가능합니다."
        ),
        'metrics': {
            'region_majority': region_majority,
            'region_counts': dict(region_counts),
            'top_interest': top_interest,
            'interest_pct': interest_pct,
            'interest_counts': dict(interest_counts),
            'interest_shannon': interest_shannon,
            'trait_counts': trait_counts,
            'trait_shannon': trait_shannon,
            'rank_unique': rank_unique,
            'rank_diversity_score': rank_diversity_score,
            'total_interests': len(flattened),
            'unique_interests': unique_interests,
            'shared_interest_count': len(shared_interest_set),
        }
    }
