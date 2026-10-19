from pathlib import Path
from typing import Literal, Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings for BuenaGuard AI with zero-billing defaults."""
    
    WORKSPACE_MODE: Literal["MOCK", "LIVE"] = Field(
        default="MOCK",
        description="Execution mode: MOCK for offline zero-billing testing, LIVE for Google APIs"
    )
    
    GEMINI_API_KEY: Optional[str] = Field(
        default=None,
        description="Google AI Studio API key. Falls back to geminiapikey.txt if omitted."
    )
    
    GEMINI_MODEL: str = Field(
        default="gemini-2.5-flash",
        description="Primary Gemini model used for DLP classification and OU mapping"
    )
    
    GEMINI_FALLBACK_MODELS: List[str] = Field(
        default_factory=lambda: ["gemini-2.0-flash", "gemini-1.5-flash"],
        description="Fallback Gemini models if primary is unavailable"
    )
    
    GOOGLE_OAUTH_CREDENTIALS: str = Field(
        default="credentials.json",
        description="Path to Google OAuth 2.0 desktop client credentials file"
    )
    
    GOOGLE_OAUTH_TOKEN: str = Field(
        default="token.json",
        description="Path to stored OAuth refresh token file"
    )
    
    HOST: str = Field(default="0.0.0.0", description="FastAPI server host")
    PORT: int = Field(default=8000, description="FastAPI server port")
    LOG_LEVEL: str = Field(default="INFO", description="Application log level")
    AUDIT_DB_PATH: str = Field(default="audit_logs.db", description="Path to SQLite audit database")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_gemini_api_key(self) -> Optional[str]:
        """Resolve Gemini API key from environment, settings, or geminiapikey.txt file."""
        if self.GEMINI_API_KEY and self.GEMINI_API_KEY.strip():
            return self.GEMINI_API_KEY.strip()
        
        # Check local geminiapikey.txt
        root_dir = Path(__file__).resolve().parent.parent
        key_file = root_dir / "geminiapikey.txt"
        if key_file.exists():
            try:
                content = key_file.read_text(encoding="utf-8").strip()
                if content:
                    return content
            except Exception:
                pass
        return None

# Singleton settings instance
settings = Settings()
