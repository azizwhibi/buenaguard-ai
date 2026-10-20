import os
import pytest
from pydantic import ValidationError

def test_config_defaults_and_env_loading(monkeypatch):
    """Verify that Settings loads default zero-billing mock mode and environment overrides."""
    # Ensure clean environment for default testing
    monkeypatch.delenv("WORKSPACE_MODE", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    
    from src.config import Settings
    
    settings = Settings(_env_file=None)
    assert settings.WORKSPACE_MODE == "MOCK", "WORKSPACE_MODE must default to MOCK for zero-billing"
    assert settings.GEMINI_MODEL in ["gemini-2.5-flash", "gemini-3.5-flash-lite"]
    assert settings.PORT == 8000
    assert settings.LOG_LEVEL == "INFO"

def test_config_env_overrides(monkeypatch):
    """Verify that Settings accepts valid environment variable overrides."""
    monkeypatch.setenv("WORKSPACE_MODE", "LIVE")
    monkeypatch.setenv("GEMINI_API_KEY", "test_gemini_key_12345")
    monkeypatch.setenv("PORT", "9090")
    
    from src.config import Settings
    
    settings = Settings(_env_file=None)
    assert settings.WORKSPACE_MODE == "LIVE"
    assert settings.get_gemini_api_key() == "test_gemini_key_12345"
    assert settings.PORT == 9090

def test_config_invalid_mode_raises(monkeypatch):
    """Verify that an invalid WORKSPACE_MODE raises a Pydantic ValidationError."""
    monkeypatch.setenv("WORKSPACE_MODE", "UNSUPPORTED_MODE")
    
    from src.config import Settings
    
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
