from typing import Optional, List, Dict
from domain.models import User, Club
from utils.ids import create_id_with_prefix
import datetime as _dt
from collections import defaultdict
import random


from collections import Counter


def get_primary_interest(users: List[User]) -> Optional[str]:
    """
    Determines the primary interest of a group of users.
    The primary interest is the one with the highest frequency.
    Ties are broken lexicographically.
    """
    if not users:
        return None

    all_interests = [interest for user in users for interest in user.interests]
    if not all_interests:
        return None

    counts = Counter(all_interests)
    max_count = 0
    primary = None

    # Find the max frequency and handle ties lexicographically
    for interest, count in sorted(counts.items()):
        if count > max_count:
            max_count = count
            primary = interest

    return primary


def get_common_interests(users: List[User]) -> set[str]:
    """Computes the set of interests shared by all users in a list."""
    if not users:
        return set()

    interest_sets = [set(u.interests) for u in users]

    common = interest_sets[0].copy()
    for interests in interest_sets[1:]:
        common.intersection_update(interests)

    return common


DEMO_SIMPLE = False  # Toggle: if True, use simplified canned explanations.


def _personality_mix(users: List[User]) -> str:
    traits = [u.personality_trait for u in users]
    unique = sorted(set(traits))
    if len(unique) == 1:
        return f"동일 성향({unique[0]})"
    return ",".join(unique)


def _rank_diversity(users: List[User]) -> int:
    return len({u.rank for u in users})


def _build_user_explanations(group_users: List[User], common_interests: set[str]) -> Dict[str, Dict[str, str]]:
    personality_mix = _personality_mix(group_users)
    rank_div = _rank_diversity(group_users)
    all_interests_sorted = sorted(common_interests)
    for_display_interests = ", ".join(
        all_interests_sorted) if all_interests_sorted else "(없음)"
    explanations: Dict[str, Dict[str, str]] = {}
    legacy_group_str = (
        f"공통 관심사 ({len(common_interests)}개): {for_display_interests}. 직급 다양성: {rank_div}개. 성향 조합: {personality_mix}."
    )
    for u in group_users:
        explanations[u.id] = {
            "그룹": legacy_group_str,  # backward compatibility
            "공통관심사": for_display_interests,
            "직급다양성": f"{rank_div}개",
            "성향조합": personality_mix,
            "요약": f"{len(common_interests)}개 관심사 공유 / 직급 {rank_div}개 / 성향 {personality_mix}" if common_interests else f"직급 {rank_div}개 / 성향 {personality_mix}"
        }
    return explanations


def compute_matches(users: List[User], target_size: int = 5, run_id: Optional[str] = None) -> List[Club]:
    """
    Computes matches based on hard constraints and greedy grouping.
    1. Buckets users by (region, personality_trait).
    2. Forms clubs within each bucket.
    3. Enforces that all members of a club share at least one interest.
    4. Greedily groups users to maximize rank diversity.
    """
    if not users:
        return []
    assert len(users) >= 5, "Matching requires at least 5 users"

    user_map = {u.id: u for u in users}
    buckets = defaultdict(list)
    for user in users:
        buckets[(user.region, user.personality_trait)].append(user)

    all_clubs = []

    for (region, personality), bucket_users in buckets.items():
        if len(bucket_users) < target_size:
            continue

        unassigned_ids = {u.id for u in bucket_users}

        while len(unassigned_ids) >= target_size:
            # Seed a new club with a random user
            seed_id = random.choice(list(unassigned_ids))
            unassigned_ids.remove(seed_id)

            group_ids = [seed_id]

            # Find candidates who could potentially join the group
            candidates = list(unassigned_ids)

            while len(group_ids) < target_size and candidates:
                group_users = [user_map[uid] for uid in group_ids]

                # Filter candidates to those who share at least one interest with the current group
                potential_candidates = []
                current_common_interests = get_common_interests(group_users)
                if not current_common_interests:  # Should not happen after the first user
                    # In case the seed user has no interests, we can't form a club
                    break

                for cand_id in candidates:
                    if current_common_interests & set(user_map[cand_id].interests):
                        potential_candidates.append(cand_id)

                if not potential_candidates:
                    break  # No more valid candidates to add

                # Select the best candidate to add, prioritizing rank diversity
                current_ranks = {user_map[uid].rank for uid in group_ids}

                best_candidate_id = None
                # Find a candidate with a new rank
                for cand_id in potential_candidates:
                    if user_map[cand_id].rank not in current_ranks:
                        best_candidate_id = cand_id
                        break

                # If no candidate with a new rank is found, pick a random one from the valid candidates
                if best_candidate_id is None:
                    best_candidate_id = random.choice(potential_candidates)

                group_ids.append(best_candidate_id)
                unassigned_ids.remove(best_candidate_id)
                candidates.remove(best_candidate_id)

            # Final check: if a full group was formed, create the club
            if len(group_ids) == target_size:
                final_group_users = [user_map[uid] for uid in group_ids]
                # This check is redundant if the loop logic is correct, but good for safety
                if get_common_interests(final_group_users):
                    leader_id = group_ids[0]
                    primary_interest = get_primary_interest(final_group_users)

                    club_name = f"{region} {primary_interest} {personality} 팀"

                    new_club = Club(
                        id=create_id_with_prefix('club'),
                        name=club_name,
                        member_ids=group_ids,
                        leader_id=leader_id,
                        primary_interest=primary_interest,
                        match_run_id=run_id
                    )
                    all_clubs.append(new_club)
                else:
                    # This case is unlikely, but if it happens, dissolve the group
                    # and return users to the unassigned pool for the next iteration.
                    unassigned_ids.update(group_ids)
            else:
                # Failed to form a full group, return users to the pool
                unassigned_ids.update(group_ids)
                # Break to avoid infinite loop if we can't form any more groups
                break

    # Finalize club objects with timestamps and explanations
    now = _dt.datetime.now(_dt.timezone.utc).isoformat().replace('+00:00', 'Z')
    for club in all_clubs:
        club.created_at = now
        club.updated_at = now
        group_users = [user_map[uid] for uid in club.member_ids]
        common_interests = get_common_interests(group_users)
        # Hybrid mode: optionally supply simple canned explanation for pure demo
        if DEMO_SIMPLE:
            explanation_str = "데모: 관심사 기반/직급 균형으로 자동 구성된 그룹입니다."
            club.explanations = {u.id: {"그룹": explanation_str}
                                 for u in group_users}
            club.match_score_breakdown = {
                "shared_interest_count": len(common_interests),
                "rank_diversity_count": _rank_diversity(group_users)
            }
        else:
            club.explanations = _build_user_explanations(
                group_users, common_interests)
            club.match_score_breakdown = {
                "shared_interest_count": len(common_interests),
                "rank_diversity_count": _rank_diversity(group_users),
                "personality_mix": _personality_mix(group_users)
            }

    return all_clubs
