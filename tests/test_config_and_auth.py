import os
import pytest
from src.config import Settings
from src.adapters.google_live_adapter import GoogleLiveAdapter

def test_oauth_read_only_scopes_enforcement():
    """Verify Rule 5: strictly read-only OAuth scopes are enforced."""
    scopes = GoogleLiveAdapter.SCOPES
    assert "https://www.googleapis.com/auth/drive.readonly" in scopes
    assert "https://www.googleapis.com/auth/spreadsheets.readonly" in scopes
    
    # Assert zero write or admin scopes in default adapter
    for s in scopes:
        assert "drive.readonly" in s or "spreadsheets.readonly" in s
        assert not s.endswith("/drive")
        assert not s.endswith("/spreadsheets")
        assert "admin" not in s

def test_zero_billing_mock_defaults_and_fallback(monkeypatch, tmp_path):
    """Verify Rule 8: zero-billing defaults to MOCK and handles absent credentials gracefully."""
    # Ensure environment variables are clear
    monkeypatch.delenv("WORKSPACE_MODE", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    
    cfg = Settings(
        _env_file=str(tmp_path / "empty.env"),
        GOOGLE_OAUTH_CREDENTIALS=str(tmp_path / "nonexistent_creds.json"),
        GOOGLE_OAUTH_TOKEN=str(tmp_path / "nonexistent_token.json")
    )
    
    # Defaults must be MOCK
    assert cfg.WORKSPACE_MODE == "MOCK"
    
    # Adapter initializes offline without network exceptions
    adapter = GoogleLiveAdapter(
        credentials_path=str(tmp_path / "nonexistent_creds.json"),
        token_path=str(tmp_path / "nonexistent_token.json")
    )
    assert adapter.is_authenticated is False
    
    # Querying files returns offline sample documents
    files = adapter.list_drive_files()
    assert len(files) > 0
    assert any("Schmidt" in f["name"] for f in files)

def test_gemini_key_resolution_graceful(monkeypatch, tmp_path):
    """Verify graceful handling when GEMINI_API_KEY is not set."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    cfg = Settings(
        _env_file=str(tmp_path / "empty.env"),
        GEMINI_API_KEY=None
    )
    key = cfg.get_gemini_api_key()
    # Should either return None or key from local file without throwing exception
    assert key is None or isinstance(key, str)
