import hashlib
import json
import logging
from typing import Type, TypeVar, Optional, Any, Dict
from pydantic import BaseModel
from src.config import settings
from src.ports.workspace_port import GeminiClassifierPort

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger("buenaguard.gemini_client")

class GeminiClient(GeminiClassifierPort):
    """Wrapper for Google AI Studio Gemini API with structured outputs and zero-billing mock mode."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        mock_mode: Optional[bool] = None,
    ):
        self.api_key = api_key if api_key is not None else settings.get_gemini_api_key()
        self.model_name = model_name or settings.GEMINI_MODEL
        
        # Determine whether to run in mock mode
        if mock_mode is not None:
            self.is_mock_mode = mock_mode
        else:
            self.is_mock_mode = (settings.WORKSPACE_MODE == "MOCK") or not bool(self.api_key)
            
        self._genai_client = None
        if not self.is_mock_mode and self.api_key:
            self._init_live_client()

    def _init_live_client(self):
        """Initialize Google GenAI client if package is available."""
        try:
            from google import genai
            self._genai_client = genai.Client(api_key=self.api_key)
            logger.info("Initialized live Gemini Client with model %s", self.model_name)
        except ImportError:
            logger.warning("google-genai package not found. Defaulting to mock mode.")
            self.is_mock_mode = True
        except Exception as e:
            logger.error("Failed to initialize Google GenAI client: %s. Defaulting to mock mode.", str(e))
            self.is_mock_mode = True

    def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        mock_response: Optional[Dict[str, Any]] = None,
        system_instruction: Optional[str] = None,
    ) -> T:
        """
        Generate structured Pydantic output using Gemini or deterministic mock fallback.
        Strictly avoids logging raw prompt content to preserve GDPR compliance.
        """
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12]
        logger.debug("Executing Gemini structured generation (prompt SHA256: %s, schema: %s)",
                     prompt_hash, response_schema.__name__)

        if self.is_mock_mode or self._genai_client is None:
            return self._generate_mock(response_schema, mock_response)

        try:
            # Live call using google-genai SDK
            from google.genai import types
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
                system_instruction=system_instruction,
                temperature=0.1
            )
            response = self._genai_client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )
            raw_text = response.text
            data = json.loads(raw_text)
            return response_schema.model_validate(data)
        except Exception as e:
            logger.warning("Live Gemini API call failed (%s). Falling back to mock response.", str(e))
            return self._generate_mock(response_schema, mock_response)

    def _generate_mock(self, response_schema: Type[T], mock_response: Optional[Dict[str, Any]]) -> T:
        """Produce a validated Pydantic model in mock mode."""
        if mock_response is not None:
            return response_schema.model_validate(mock_response)
        
        # If no explicit mock payload provided, construct minimal valid model
        try:
            return response_schema.model_validate({})
        except Exception:
            # Fallback for models with required fields
            return response_schema.model_construct()

    def classify_document(self, text: str) -> Dict[str, Any]:
        """Classify document sensitivity and extract DLP violations."""
        from src.services.pii_prefilter import PIIPreFilter
        redaction = PIIPreFilter().sanitize(text)
        return {
            "has_pii": redaction.has_pii,
            "detected_types": redaction.detected_types,
            "risk_level": "CRITICAL" if redaction.has_pii else "LOW"
        }

    def recommend_onboarding_ou(self, ticket: Any) -> Dict[str, Any]:
        """Analyze employee ticket and determine least-privilege OU and security flags."""
        dept = getattr(ticket, "department", "") or ""
        role = getattr(ticket, "jobTitle", "") or ""
        dept_l = dept.lower()
        role_l = role.lower()
        if "finance" in dept_l or any(k in role_l for k in ["payroll", "tax", "cfo"]):
            return {"recommended_ou": "/Executive_Finance", "smime_required": True}
        elif "engineer" in dept_l or any(k in role_l for k in ["engineer", "developer", "cloud"]):
            return {"recommended_ou": "/Engineering", "smime_required": False}
        elif "contractor" in dept_l or "consultant" in role_l:
            return {"recommended_ou": "/Contractors", "smime_required": False}
        return {"recommended_ou": "/", "smime_required": False}
