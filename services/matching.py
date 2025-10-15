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
                if not current_common_interests: # Should not happen after the first user
                    # In case the seed user has no interests, we can't form a club
                    break

                for cand_id in candidates:
                    if current_common_interests & set(user_map[cand_id].interests):
                        potential_candidates.append(cand_id)

                if not potential_candidates:
                    break # No more valid candidates to add

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

        # Build explanation string
        group_users = [user_map[uid] for uid in club.member_ids]
        common_interests = get_common_interests(group_users)
        distinct_ranks = len({u.rank for u in group_users})

        explanation_str = (
            f"공통 관심사 ({len(common_interests)}개): {', '.join(sorted(list(common_interests)))}. "
            f"직급 다양성: {distinct_ranks}개."
        )

        # Adapt to the existing explanation data structure
        club.explanations = {uid: {"그룹": explanation_str} for uid in club.member_ids}
        club.match_score_breakdown = {} # Clear obsolete scores

    return all_clubs