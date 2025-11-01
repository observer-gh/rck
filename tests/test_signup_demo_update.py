import os
import json
import importlib
import pytest
from services import persistence
from domain.constants import reset_demo_user_state, get_demo_user, save_demo_user

DATA_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'data'))
STATE_PATH = os.path.join(DATA_DIR, 'demo_user_state.json')


def _read(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
