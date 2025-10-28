import os
import json
import importlib
from services import persistence
from domain.constants import reset_demo_user_state, get_demo_user, save_demo_user

DATA_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'data'))
STATE_PATH = os.path.join(DATA_DIR, 'demo_user_state.json')


def _read(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_signup_demo_update_no_duplicate(monkeypatch):
    """Simulate the two-step signup flow for demo user and ensure:
    - demo_user record is updated in users.json
    - no new user with different id but same employee_number/name is appended
    """
    # 1. Reset state & persistence to a clean demo_user only scenario
    reset_demo_user_state()
    demo_state = get_demo_user()
    persistence.replace_all('users', [demo_state])

    # 2. Import the signup view module fresh (so we can monkeypatch session state like Streamlit)
    signup = importlib.import_module('views.user_signup')

    # 3. Prepare a fake draft (what form_basic would store)
    draft_payload = {
        'name': demo_state['name'],  # same name triggers update logic
        'nickname': 'updatedNick',
        'employee_number': demo_state['employee_number'],
        'region': '부산' if demo_state.get('region') != '부산' else '서울',
        'rank': '대리' if demo_state.get('rank') != '대리' else '사원',
        'interests': ['축구', '보드게임'],
    }

    # Monkeypatch streamlit session_state behavior minimalistically
    class DummySession(dict):
        def pop(self, k, default=None):
            return super().pop(k, default)

        def __getattr__(self, name):
            try:
                return self[name]
            except KeyError:
                raise AttributeError(name)

        def __setattr__(self, name, value):
            self[name] = value

        def __delattr__(self, name):
            if name in self:
                del self[name]
            else:
                raise AttributeError(name)
    dummy_state = DummySession()
    dummy_state['new_user_draft'] = draft_payload
    dummy_state['current_user_id'] = 'demo_user'
    # ensure we skip read-only lock path
    dummy_state['signup_first_visit'] = False
    dummy_state['clear_survey_answers'] = False

    # Fake Streamlit API pieces used in finish block
    class DummyST:
        session_state = dummy_state

        def header(self, *a, **kw):
            pass

        def info(self, *a, **kw):
            pass

        def subheader(self, *a, **kw):
            pass

        def form(self, *a, **kw):
            class F:
                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc, tb):
                    return False

                def form_submit_button(self, *a, **kw):
                    return True  # simulate submit

                def radio(self, *a, **kw):
                    return '중간'
            return F()

        def text_input(self, *a, **kw):
            return draft_payload['name']

        def selectbox(self, *a, **kw):
            return draft_payload['region']

        def multiselect(self, *a, **kw):
            return draft_payload['interests']

        def error(self, *a, **kw):
            raise AssertionError(f"Unexpected error: {a} {kw}")

        def success(self, *a, **kw):
            pass

        def button(self, *a, **kw):
            return False

        def radio(self, *a, **kw):
            return '중간'

        def rerun(self):
            pass

        def form_submit_button(self, *a, **kw):
            # Always simulate clicking submit inside form contexts
            return True

    # Monkeypatch streamlit
    monkeypatch.setitem(signup.__dict__, 'st', DummyST())

    # 4. Prepare survey answers (simulate finish block path). We call classify_personality indirectly.
    # Directly invoke only the finish portion: easier to call view() with session state conditions
    signup.view()

    # 5. Assert only one user remains and fields updated
    users_after = persistence.load_list('users')
    assert len(users_after) == 1, 'Should still have exactly one demo_user'
    updated_demo = users_after[0]
    assert updated_demo['id'] == 'demo_user'
    assert updated_demo['nickname'] == 'updatedNick'
    assert updated_demo['interests'] == ['축구', '보드게임']
    # Region or rank updated
    assert updated_demo['region'] == draft_payload['region']
    assert updated_demo['rank'] == draft_payload['rank']

    # 6. State file also updated
    state = _read(STATE_PATH)
    assert state['nickname'] == 'updatedNick'
    assert state['interests'] == ['축구', '보드게임']
