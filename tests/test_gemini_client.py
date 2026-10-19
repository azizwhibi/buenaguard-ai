import pytest
from pydantic import BaseModel, Field
from typing import List

class SampleAnalysisSchema(BaseModel):
    category: str
    risk_level: str
    detected_items: List[str] = Field(default_factory=list)
    recommendation: str

def test_gemini_client_initialization_with_and_without_key():
    """Verify GeminiClient initialization handles explicit key and None cleanly."""
    from src.adapters.gemini_client import GeminiClient
    
    # Initialize with mock mode forced
    client_mock = GeminiClient(api_key=None, mock_mode=True)
    assert client_mock.is_mock_mode is True
    assert client_mock.model_name == "gemini-2.5-flash"

def test_gemini_client_structured_generation_mock_mode():
    """Verify structured Pydantic output generation in deterministic mock mode."""
    from src.adapters.gemini_client import GeminiClient
    
    client = GeminiClient(api_key=None, mock_mode=True)
    prompt = "Analyze this sample contract for German GDPR violations."
    
    mock_payload = {
        "category": "GDPR_CONTRACT_SCAN",
        "risk_level": "HIGH",
        "detected_items": ["IBAN", "Steuer-ID"],
        "recommendation": "Restrict Drive link to internal domain only."
    }
    
    result = client.generate_structured(
        prompt=prompt,
        response_schema=SampleAnalysisSchema,
        mock_response=mock_payload
    )
    
    assert isinstance(result, SampleAnalysisSchema)
    assert result.category == "GDPR_CONTRACT_SCAN"
    assert result.risk_level == "HIGH"
    assert "IBAN" in result.detected_items
    assert "Steuer-ID" in result.detected_items

def test_gemini_client_sanitizes_logs(caplog):
    """Verify that GeminiClient log output does not expose raw prompt content."""
    import logging
    from src.adapters.gemini_client import GeminiClient
    
    client = GeminiClient(api_key=None, mock_mode=True)
    sensitive_prompt = "Confidential customer IBAN DE89370400440532013000 and Salary 150000 EUR"
    
    with caplog.at_level(logging.DEBUG):
        client.generate_structured(
            prompt=sensitive_prompt,
            response_schema=SampleAnalysisSchema,
            mock_response={
                "category": "FINANCE",
                "risk_level": "CRITICAL",
                "detected_items": ["IBAN"],
                "recommendation": "Revoke link"
            }
        )
    
    # Raw IBAN should NOT appear anywhere in the captured logs
    for record in caplog.records:
        assert "DE89370400440532013000" not in record.message
