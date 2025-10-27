"""User service helpers: loading, saving, duplicate detection, session convenience.

Demo user definition is centralized in domain.constants.DEMO_USER so edits persist.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from dataclasses import asdict
from domain.models import User
from services import persistence
from domain.constants import get_demo_user, save_demo_user
import os
import json

_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
_DATA_DIR = os.path.join(_BASE_DIR, 'data')
_SEED_USERS_PATH = os.path.join(_DATA_DIR, 'seed_users.json')


def _load_seed_users():
    try:
        with open(_SEED_USERS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except Exception:
        return []
    return []


def ensure_demo_user(users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ensure demo user exists only if missing. Does NOT overwrite existing demo record."""
    if not users:
        # If completely empty, bootstrap from seed set (includes demo_user at index 0)
        seed_set = _load_seed_users()
        if seed_set:
            persistence.replace_all('users', seed_set)
            return seed_set
    if not any(u.get('id') == 'demo_user' for u in users):
        users.append(get_demo_user())
        persistence.replace_all('users', users)
    return users


def load_users() -> List[Dict[str, Any]]:
    users = persistence.load_list('users')
    return ensure_demo_user(users)


def save_users(users: List[Dict[str, Any]]):
    """Persist users without clobbering an edited demo user.

    If demo user missing entirely, seed baseline; otherwise keep current demo fields.
    """
    if not any(u.get('id') == 'demo_user' for u in users):
        users.append(get_demo_user())
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


def persist_demo_user_if_changed(updated: Dict[str, Any]):
    """If updated user is demo_user, sync state JSON."""
    if updated.get('id') == 'demo_user':
        save_demo_user(updated)
