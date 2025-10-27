"""
This module contains centralized constants used throughout the application,
ensuring a single source of truth for values like regions, ranks, and interests.
"""

# These constants are used across multiple views to ensure consistency.

# List of available regions for users
import os
import json
REGIONS = [
    "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
    "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"
]

# List of available job ranks for users
RANKS = ["사원", "대리", "과장", "차장", "부장"]

# List of available interests for users
INTERESTS = ["축구", "영화보기", "보드게임", "러닝", "독서", "헬스", "요리", "사진", "등산"]

# Hard-coded demo user baseline (always present in session)

_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
_DATA_DIR = os.path.join(_BASE_DIR, 'data')
_DEFAULTS_PATH = os.path.join(_DATA_DIR, 'demo_user_defaults.json')
_STATE_PATH = os.path.join(_DATA_DIR, 'demo_user_state.json')


def _load_json(path: str):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def _write_json(path: str, data: dict):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


_defaults = _load_json(_DEFAULTS_PATH) or {
    'id': 'demo_user', 'name': '데모사용자', 'nickname': 'nemo', 'employee_number': '15000001',
    'region': '서울', 'rank': '사원', 'interests': ['축구', '영화보기'], 'personality_trait': '중간',
    'survey_answers': [2]*7
}
_state = _load_json(_STATE_PATH)
if not _state:
    _state = _defaults.copy()
    _write_json(_STATE_PATH, _state)


def get_demo_user() -> dict:
    """Return current mutable demo user state (re-read file each call)."""
    s = _load_json(_STATE_PATH)
    if s and isinstance(s, dict):
        return s
    return _defaults.copy()


def get_demo_user_defaults() -> dict:
    """Return immutable demo user defaults (always re-read defaults file)."""
    d = _load_json(_DEFAULTS_PATH)
    if d and isinstance(d, dict):
        return d
    return _defaults.copy()


def save_demo_user(updates: dict):
    """Persist new demo user state (select subset of allowed keys)."""
    allowed = {'id', 'name', 'nickname', 'employee_number', 'region',
               'rank', 'interests', 'personality_trait', 'survey_answers'}
    current = get_demo_user()
    current.update({k: v for k, v in updates.items() if k in allowed})
    _write_json(_STATE_PATH, current)
    return current


def reset_demo_user_state():
    """Reset state to defaults."""
    _write_json(_STATE_PATH, _defaults.copy())
    return get_demo_user()


# Backwards-compatible constant snapshot (avoid large refactor). Use get_demo_user() for fresh copy.
DEMO_USER = get_demo_user()
