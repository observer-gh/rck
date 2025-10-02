from typing import Optional
from typing import List, Dict, Tuple
from domain.models import User, Club
from utils.ids import create_id_with_prefix
import datetime as _dt


def score(u1: User, u2: User) -> int:
    s = 10 * len(set(u1.interests) & set(u2.interests))
    if u1.region == u2.region:
        s += 5
    if u1.rank == u2.rank:
        s += 3
    if u1.preferred_atmosphere == u2.preferred_atmosphere:
        s += 2
    return s


def compute_matches(users: List[User], target_size: int = 5, run_id: Optional[str] = None) -> List[Club]:
    if not users:
        return []
    # Precompute pair scores
    pair_scores: Dict[Tuple[str, str], int] = {}
    for i, user_a in enumerate(users):
        for user_b in users[i+1:]:
            pair_scores[(user_a.id, user_b.id)] = score(user_a, user_b)

    def pair(a: str, b: str) -> int:
        if (a, b) in pair_scores:
            return pair_scores[(a, b)]
        if (b, a) in pair_scores:
            return pair_scores[(b, a)]
        return 0

    unassigned = set(u.id for u in users)
    clubs_raw: List[List[str]] = []
    # Build index
    user_ids = [u.id for u in users]

    def user_weight(uid: str) -> int:
        return sum(pair(uid, other) for other in unassigned if other != uid)

    while unassigned:
        seed = max(unassigned, key=user_weight)
        group = [seed]
        candidates = list(unassigned - {seed})
        while len(group) < target_size and candidates:
            next_id = max(candidates, key=lambda uid: sum(
                pair(uid, g) for g in group))
            group.append(next_id)
            candidates.remove(next_id)
        for gid in group:
            unassigned.remove(gid)
        clubs_raw.append(group)

    # Redistribute tiny final group (<3) if more than one group exists
    if clubs_raw and len(clubs_raw[-1]) < 3 and len(clubs_raw) > 1:
        leftovers = clubs_raw.pop()
        for leftover_id in leftovers:
            target = max(clubs_raw, key=lambda grp: sum(pair(leftover_id, m)
                         for m in grp))
            target.append(leftover_id)

    # Build Club objects
    clubs: List[Club] = []
    now = _dt.datetime.now(_dt.timezone.utc).isoformat().replace('+00:00', 'Z')

    for group in clubs_raw:
        leader = group[0]
        breakdown = {}
        explanations: dict[str, dict[str, str]] = {}
        for i, user_a in enumerate(group):
            for user_b in group[i+1:]:
                breakdown[f"{user_a}:{user_b}"] = pair(user_a, user_b)
        # Build simple explanation per user
        for uid in group:
            explanations[uid] = {}
        for i, a in enumerate(group):
            for b in group[i+1:]:
                sc = pair(a, b)
                reason_bits = []
                ua = next(u for u in users if u.id == a)
                ub = next(u for u in users if u.id == b)
                common = set(ua.interests) & set(ub.interests)
                if common:
                    reason_bits.append(f"공통관심:{'/'.join(sorted(common))}")
                if ua.region == ub.region:
                    reason_bits.append("지역")
                if ua.rank == ub.rank:
                    reason_bits.append("직급")
                if ua.preferred_atmosphere == ub.preferred_atmosphere:
                    reason_bits.append("분위기")
                explanations[a][b] = ','.join(reason_bits) or '기준없음'
                explanations[b][a] = explanations[a][b]
        clubs.append(Club(id=create_id_with_prefix('club'), member_ids=group, leader_id=leader,
                     match_score_breakdown=breakdown, explanations=explanations, match_run_id=run_id, created_at=now, updated_at=now))
    return clubs
