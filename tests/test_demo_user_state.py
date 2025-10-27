import os
import json
from services import persistence
from services import admin as admin_svc
from domain.constants import get_demo_user, save_demo_user, reset_demo_user_state

DATA_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'data'))
STATE_PATH = os.path.join(DATA_DIR, 'demo_user_state.json')
DEFAULTS_PATH = os.path.join(DATA_DIR, 'demo_user_defaults.json')


def _read(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _write(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _ensure_demo_in_persistence():
    users = persistence.load_list('users')
    if not any(u.get('id') == 'demo_user' for u in users):
        users.append(get_demo_user())
        persistence.replace_all('users', users)
    return users


def test_reset_demo_user_state():
    reset_demo_user_state()  # ensure defaults applied
    defaults = _read(DEFAULTS_PATH)
    state = _read(STATE_PATH)
    assert defaults == state, 'State should equal defaults after reset'


def test_save_demo_user_direct_updates_state():
    reset_demo_user_state()
    updated = {'name': '데모사용자수정', 'region': '부산'}
    save_demo_user(updated)
    state = _read(STATE_PATH)
    assert state['name'] == '데모사용자수정'
    assert state['region'] == '부산'
    # revert
    reset_demo_user_state()


def test_admin_update_persists_state():
    reset_demo_user_state()
    _ensure_demo_in_persistence()
    users = persistence.load_list('users')
    demo = next(u for u in users if u['id'] == 'demo_user')
    original_rank = demo['rank']
    new_rank = '대리' if original_rank != '대리' else '사원'
    admin_svc.update_user_profile('demo_user', {'name': demo['name'], 'employee_number': demo['employee_number'], 'region': demo['region'],
                                  'rank': new_rank, 'interests': demo['interests'], 'survey_answers': demo.get('survey_answers', [2]*7)}, users)
    state = _read(STATE_PATH)
    assert state['rank'] == new_rank
    # revert
    reset_demo_user_state()
