import os
import pytest

def test_google_live_adapter_scopes_are_read_only():
    """Verify that GoogleLiveAdapter restricts OAuth scopes strictly to read-only."""
    from src.adapters.google_live_adapter import GoogleLiveAdapter
    
    adapter = GoogleLiveAdapter(credentials_path="nonexistent.json", token_path="nonexistent_token.json")
    for scope in adapter.SCOPES:
        assert "readonly" in scope, f"Scope {scope} must be read-only"
        assert "admin" not in scope, f"Scope {scope} must not grant admin privileges"

def test_google_live_adapter_offline_fallback():
    """Verify that GoogleLiveAdapter handles missing credentials gracefully with offline fallback."""
    from src.adapters.google_live_adapter import GoogleLiveAdapter
    
    adapter = GoogleLiveAdapter(credentials_path="nonexistent.json", token_path="nonexistent_token.json")
    assert adapter.is_authenticated is False
    
    # Should safely return offline mock drive files
    files = adapter.list_drive_files()
    assert isinstance(files, list)
    assert len(files) > 0
    assert "name" in files[0]
    assert "id" in files[0]

def test_google_live_adapter_get_file_content_offline():
    """Verify that get_file_content safely returns sample content in offline mode."""
    from src.adapters.google_live_adapter import GoogleLiveAdapter
    
    adapter = GoogleLiveAdapter(credentials_path="nonexistent.json", token_path="nonexistent_token.json")
    content = adapter.get_drive_file_content("mock_doc_101")
    assert isinstance(content, str)
    assert len(content) > 0
