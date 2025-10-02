import json
import os
import tempfile
import shutil
from typing import List, Dict, Any

DATA_DIR = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..', 'data')
DATA_DIR = os.path.normpath(DATA_DIR)

FILES = {
    'users': 'users.json',
    'clubs': 'clubs.json',
    'activity_reports': 'activity_reports.json'
}


def _path(key: str) -> str:
    return os.path.join(DATA_DIR, FILES[key])


def load_list(key: str) -> List[Dict[str, Any]]:
    file_path = _path(key)
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def atomic_write(key: str, data: List[Dict[str, Any]]):
    file_path = _path(key)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(prefix='tmp_', suffix='.json')
    with os.fdopen(tmp_fd, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    shutil.move(tmp_path, file_path)


def append_item(key: str, item: Dict[str, Any]):
    data = load_list(key)
    data.append(item)
    atomic_write(key, data)


def replace_all(key: str, items: List[Dict[str, Any]]):
    atomic_write(key, items)
