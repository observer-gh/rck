"""User service helpers: loading, saving, duplicate detection, session convenience.

Demo user definition is centralized in domain.constants.DEMO_USER so edits persist.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from dataclasses import asdict
from domain.models import User
from services import persistence
from domain.constants import DEMO_USER


def ensure_demo_user(users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ensure demo user exists only if missing. Does NOT overwrite existing demo record."""
    if not any(u.get('id') == DEMO_USER['id'] for u in users):
        users.append(DEMO_USER.copy())
        persistence.replace_all('users', users)
    return users


def load_users() -> List[Dict[str, Any]]:
    users = persistence.load_list('users')
    return ensure_demo_user(users)


def save_users(users: List[Dict[str, Any]]):
    """Persist users without clobbering an edited demo user.

    If demo user missing entirely, seed baseline; otherwise keep current demo fields.
    """
    if not any(u.get('id') == DEMO_USER['id'] for u in users):
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
