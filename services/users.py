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
from utils.paths import resolve_data_file

_SEED_USERS_PATH = resolve_data_file('seed_users.json') or os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..')), 'data', 'seed_users.json')
_DEMO_STATE_PATH = resolve_data_file('demo_user_state.json') or os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..')), 'data', 'demo_user_state.json')


def _load_seed_users():
    if not _SEED_USERS_PATH or not os.path.exists(_SEED_USERS_PATH):
        return []
    try:
        with open(_SEED_USERS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except Exception:
        return []
    return []


def ensure_demo_user(users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ensure demo user exists and force its content to match demo_user_state.json if available.

    Steps:
    1. If users list empty, attempt bootstrap from seed_users.json.
    2. Load demo_user_state.json; fallback to get_demo_user() if missing/invalid.
    3. Overwrite existing demo_user entry or insert it (at front) if absent.
    4. Persist only if a change was applied.
    """
    changed = False
    if not users:
        seed_set = _load_seed_users()
        if seed_set:
            users = seed_set
            changed = True

    # Load state file
    demo_state: Dict[str, Any] = {}
    if _DEMO_STATE_PATH and os.path.exists(_DEMO_STATE_PATH):
        try:
            with open(_DEMO_STATE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and data.get('id') == 'demo_user':
                    demo_state = data
        except Exception:
            demo_state = {}
    else:
        demo_state = {}
    if not demo_state:  # fallback
        demo_state = get_demo_user()

    # Find existing demo_user index
    idx = next((i for i, u in enumerate(users)
               if u.get('id') == 'demo_user'), None)
    if idx is None:
        users.insert(0, demo_state)
        changed = True
    else:
        # Only overwrite if different
        if users[idx] != demo_state:
            users[idx] = demo_state
            changed = True

    if changed:
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
