"""View modules for manual routing.

This project intentionally uses a custom router in `app.py` instead of Streamlit's
automatic multi-page system. All page implementations live under `views/` and
expose a `view()` function. The legacy `pages/` directory was removed to prevent
duplicate execution and noisy file watcher warnings ("Received event for non-watched path").

Add any new page as a module with a `view()` callable and register it in
`PAGE_REGISTRY` inside `app.py`.
"""
