"""
This service module contains the business logic for the admin dashboard.
It is responsible for data manipulation, analytics, and other admin-specific functions,
keeping the view layer clean and focused on UI rendering.
"""
import datetime as dt
from dataclasses import asdict
import time
import csv
import io

from services import persistence, activity, matching, users as user_svc
from domain.models import User, MatchRun
from utils.ids import create_id_with_prefix
from services.survey import classify_personality
from demo import sample_data

def get_user_map():
    """Returns a dictionary mapping user IDs to user objects."""
    return {u['id']: u for u in persistence.load_list('users')}


def get_user_name(user_id, user_map):
    """Safely retrieves a user's name from their ID."""
    user = user_map.get(user_id)
    return user['name'] if user else user_id


def get_club_points_map():
    """Calculates the total verified points for each club."""
    reports = persistence.load_list('activity_reports')
    points = {}
    for r in reports:
        if r.get('status') == 'Verified':
            points[r['club_id']] = points.get(r['club_id'], 0) + int(r.get('points_awarded', 0))
    return points


def get_system_analytics():
    """Gathers and computes key analytics for the entire system."""
    users_all = persistence.load_list('users')
    clubs_all = persistence.load_list('clubs')
    runs_all = persistence.load_list('match_runs')
    reports_all = persistence.load_list('activity_reports')

    active_clubs = sum(1 for c in clubs_all if c.get('status') == 'Active')
    pending_reports = sum(1 for r in reports_all if r.get('status') == 'Pending')
    verified_reports = sum(1 for r in reports_all if r.get('status') == 'Verified')
    club_points = get_club_points_map()
    total_points = sum(club_points.values())

    analytics = {
        "total_users": len(users_all),
        "total_clubs": len(clubs_all),
        "active_clubs": active_clubs,
        "total_match_runs": len(runs_all),
        "pending_reports": pending_reports,
        "verified_reports": verified_reports,
        "total_points_awarded": total_points,
        "avg_rank_diversity": 0,
        "avg_interest_variety": 0,
    }

    if clubs_all and users_all:
        rank_diversities = [len({m['rank'] for m in users_all if m['id'] in c['member_ids']}) for c in clubs_all if c['member_ids']]
        interest_varieties = [len({i for m in users_all if m['id'] in c['member_ids'] for i in m['interests']}) for c in clubs_all if c['member_ids']]

        if rank_diversities:
            analytics["avg_rank_diversity"] = sum(rank_diversities) / len(rank_diversities)
        if interest_varieties:
            analytics["avg_interest_variety"] = sum(interest_varieties) / len(interest_varieties)

    return analytics

def get_top_clubs_by_points(limit=5):
    """Returns the top N clubs sorted by their verified points."""
    club_points = get_club_points_map()
    if not club_points:
        return []

    clubs_map = {c['id']: c for c in persistence.load_list('clubs')}
    user_map = get_user_map()

    top_club_items = sorted(club_points.items(), key=lambda item: item[1], reverse=True)[:limit]

    top_clubs = []
    for club_id, points in top_club_items:
        club = clubs_map.get(club_id)
        if club:
            leader_name = get_user_name(club['leader_id'], user_map)
            top_clubs.append({"name": f"{leader_name} 팀", "points": points})

    return top_clubs


def update_user_profile(user_id, updates, all_users):
    """Updates a user's profile after validation."""
    user = next((u for u in all_users if u['id'] == user_id), None)
    if not user:
        raise ValueError("User not found")

    # Validate for duplicates before updating
    if user_svc.is_duplicate_user(updates['name'], updates['region'], all_users, exclude_id=user_id):
        raise ValueError("중복 사용자 (이름+지역) 존재. 변경 취소.")

    new_answers = updates.get('survey_answers', user.get('survey_answers'))
    updates['personality_trait'] = classify_personality(new_answers)

    user.update(updates)
    persistence.replace_all('users', all_users)
    return user


def delete_user(user_id, all_users):
    """Deletes a user from the system."""
    users_after_deletion = [u for u in all_users if u['id'] != user_id]
    if len(users_after_deletion) == len(all_users):
        raise ValueError("User not found for deletion")
    persistence.replace_all('users', users_after_deletion)

def run_new_matching(target_size):
    """Executes a new matching run for all users."""
    users_raw = persistence.load_list('users')
    if len(users_raw) < target_size:
        raise ValueError(f"매칭을 실행하려면 최소 {target_size}명의 사용자가 필요합니다.")

    user_objs = [User(**u) for u in users_raw]
    run_id = create_id_with_prefix('run')

    clubs = matching.compute_matches(user_objs, target_size=target_size, run_id=run_id)
    clubs_dicts = [asdict(c) for c in clubs]

    existing_clubs = persistence.load_list('clubs')
    existing_clubs.extend(clubs_dicts)
    persistence.replace_all('clubs', existing_clubs)

    runs = persistence.load_list('match_runs')
    run_meta = MatchRun(
        id=run_id,
        created_at=utc_now_iso(),
        target_size=target_size,
        user_count=len(users_raw),
        club_count=len(clubs_dicts)
    )
    runs.append(asdict(run_meta))
    persistence.replace_all('match_runs', runs)

    return run_id, len(clubs_dicts)

def activate_club(club_id, chat_link, all_clubs):
    """Activates a club and sets its chat link."""
    club = next((c for c in all_clubs if c['id'] == club_id), None)
    if not club:
        raise ValueError("Club not found")

    club['status'] = 'Active'
    club['chat_link'] = chat_link if chat_link else ''
    club['updated_at'] = utc_now_iso()

    persistence.replace_all('clubs', all_clubs)
    return True

def generate_sample_users_and_match(num_users=9, target_size=5):
    """Generates sample users, adds them, and runs matching."""
    users_raw = persistence.load_list('users')
    new_users = [asdict(u) for u in sample_data.make_users(num_users)]
    users_all = users_raw + new_users
    persistence.replace_all('users', users_all)

    # Now run matching with the combined user list
    run_id, club_count = run_new_matching(target_size)
    return run_id, club_count

def add_sample_users(num_users=15):
    """Adds a specified number of sample users to the system."""
    users = persistence.load_list('users')
    new_users = [asdict(u) for u in sample_data.make_users(num_users)]
    users.extend(new_users)
    persistence.replace_all('users', users)

def export_to_csv(data_key: str):
    """Exports data for a given key to a CSV string."""
    data = persistence.load_list(data_key)
    if not data:
        return ""

    output = io.StringIO()
    # Ensure all dicts have the same keys for the header
    fieldnames = sorted(list(set(key for item in data for key in item.keys())))
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(data)
    return output.getvalue()


def reset_all_data():
    """Deletes all transactional data (clubs, reports, runs) and resets users."""
    for key in ['clubs', 'activity_reports', 'match_runs']:
        persistence.replace_all(key, [])

    # Reset users but re-add demo user
    persistence.replace_all('users', [])
    user_svc.load_users() # This ensures the demo user is recreated


def utc_now_iso():
    """Returns the current UTC time in ISO 8601 format."""
    return dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z')