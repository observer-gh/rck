import os
from typing import Optional


def resolve_data_file(filename: str) -> Optional[str]:
    """Resolve a data file path robustly across local dev and container (/mount/src) layouts.

    Strategy:
    1. Try project-root relative (data/filename) based on this file location.
    2. Try cwd + data/filename (in case working dir is project root).
    3. Try /mount/src/data/filename (Streamlit ephemeral container pattern).
    4. Try parent-of-cwd/data/filename (if app launched from subfolder).
    Returns first existing path or None.
    """
    candidates = []
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    candidates.append(os.path.join(base_dir, 'data', filename))
    cwd = os.getcwd()
    candidates.append(os.path.join(cwd, 'data', filename))
    candidates.append(os.path.join('/mount/src/data', filename))
    parent_cwd = os.path.dirname(cwd)
    candidates.append(os.path.join(parent_cwd, 'data', filename))
    for p in candidates:
        if os.path.exists(p):
            return p
    return None
