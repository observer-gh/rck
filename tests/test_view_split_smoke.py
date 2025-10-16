import pytest
from unittest.mock import patch, MagicMock

# Mock streamlit before importing the app
st_mock = MagicMock()

def test_page_registry_structure():
    with patch.dict("sys.modules", {"streamlit": st_mock}):
        from app import PAGE_REGISTRY
    """
    Tests that the PAGE_REGISTRY has the correct structure.
    """
    assert isinstance(PAGE_REGISTRY, dict)
    for key, value in PAGE_REGISTRY.items():
        assert "label" in value
        assert "render_func" in value
        assert "admin" in value
        assert callable(value["render_func"])
        assert isinstance(value["admin"], bool)


def test_admin_pages_are_correctly_flagged():
    with patch.dict("sys.modules", {"streamlit": st_mock}):
        from app import PAGE_REGISTRY
    """
    Tests that only the admin dashboard is flagged as an admin page.
    """
    admin_pages = [key for key, value in PAGE_REGISTRY.items()
                   if value["admin"]]
    assert admin_pages == ["admin_dashboard"]


def test_user_pages_are_correctly_flagged():
    with patch.dict("sys.modules", {"streamlit": st_mock}):
        from app import PAGE_REGISTRY
    """
    Tests that the correct pages are flagged as non-admin (user-facing).
    """
    user_pages = [key for key, value in PAGE_REGISTRY.items()
                  if not value["admin"]]
    # Updated to include newly added 'profile' page
    expected_user_pages = ["user_signup", "profile",
                           "my_club", "activity_report", "demo_script"]
    assert sorted(user_pages) == sorted(expected_user_pages)


def test_all_render_functions_are_callable():
    with patch.dict("sys.modules", {"streamlit": st_mock}):
        from app import PAGE_REGISTRY
    """
    Ensures that every page in the registry points to a callable function.
    """
    for page_key, page_config in PAGE_REGISTRY.items():
        assert callable(
            page_config['render_func']), f"Render function for '{page_key}' is not callable."
