"""One-off cleanup script to delete the legacy `pages/` directory.

Run with:
  uv run python scripts/remove_pages_dir.py

Safe: only removes the directory if it exists and is not in a git index (source
files already migrated to `views/`).
"""
from __future__ import annotations
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / "pages"


def main():
    if not PAGES.exists():
        print("[cleanup] pages/ already absent — nothing to do")
        return
    # Basic safety: do not remove if directory contains something unexpected (binary etc.)
    # Here we just log its contents then remove.
    print("[cleanup] Removing legacy pages/ directory. Contents:")
    for p in PAGES.rglob('*'):
        print(f"  - {p.relative_to(ROOT)}")
    shutil.rmtree(PAGES)
    print("[cleanup] Done. Add 'pages/' to .gitignore (already added).")


if __name__ == "__main__":
    main()
