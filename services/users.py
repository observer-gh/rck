"""User service helpers: loading, saving, duplicate detection, session convenience."""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from dataclasses import asdict
from domain.models import User
from services import persistence

# Persistent demo user (cannot be removed by admin 'erase all').
DEMO_USER = {
    'id': 'demo_user',
    'name': '데모사용자',
    'employee_number': 'D-000',
    'region': '서울',
    'rank': '과장',
    'interests': ['축구', '독서'],
    'personality_trait': 'Neutral',
    'survey_answers': [3, 3, 3, 3],
}


def ensure_demo_user(users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ensure DEMO_USER exists; if missing, append and persist.

    Returns the possibly modified list.
    """
    if not any(u.get('id') == DEMO_USER['id'] for u in users):
        users.append(DEMO_USER.copy())
        # Persist addition so exports include demo user.
        persistence.replace_all('users', users)
    return users


def load_users() -> List[Dict[str, Any]]:
    users = persistence.load_list('users')
    return ensure_demo_user(users)


def save_users(users: List[Dict[str, Any]]):
    # Preserve demo user even if caller forgot to include.
    users = [u for u in users if u.get('id') != DEMO_USER['id']]
    users.append(DEMO_USER.copy())
    persistence.replace_all('users', users)


def is_duplicate_user(name: str, region: str, users: List[Dict[str, Any]], exclude_id: Optional[str] = None) -> bool:
    name_norm = (name or '').strip().lower()
    region_norm = (region or '').strip().lower()
    for u in users:
        if exclude_id and u['id'] == exclude_id:
            continue
        if u.get('name', '').strip().lower() == name_norm and u.get('region', '').strip().lower() == region_norm:
            return True
    return False


def append_user(user: User):
    users = load_users()
    users.append(asdict(user))
    save_users(users)
