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

        models_to_try = [self.model_name] + [m for m in settings.GEMINI_FALLBACK_MODELS if m != self.model_name]
        last_error = None
        for model in models_to_try:
            try:
                from google.genai import types
                config = types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema,
                    system_instruction=system_instruction,
                    temperature=0.1
                )
                response = self._genai_client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config
                )
                raw_text = response.text
                data = json.loads(raw_text)
                return response_schema.model_validate(data)
            except Exception as e:
                last_error = e
                logger.warning("Gemini model %s call failed (%s). Trying next fallback.", model, str(e))
        
        logger.warning("All live Gemini models failed (last error: %s). Falling back to mock response.", str(last_error))
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
        """Classify document sensitivity and extract DLP violations using Gemini or prefilter."""
        from src.services.pii_prefilter import PIIPreFilter
        redaction = PIIPreFilter().sanitize(text)

        if not self.is_mock_mode and self._genai_client:
            from pydantic import BaseModel, Field

            class GeminiDLPAnalysis(BaseModel):
                has_pii: bool = False
                detected_types: List[str] = Field(default_factory=list)
                risk_level: str = "LOW"
                gdpr_articles: List[str] = Field(default_factory=list)
                remediation: str = ""

            prompt = (
                "You are an expert Google Workspace Data Loss Prevention and GDPR compliance auditor for BuenaCloud GmbH.\n"
                "Analyze the following sanitized document text (where sensitive values like IBANs and Tax IDs are pre-tokenized):\n\n"
                f"--- BEGIN DOCUMENT ---\n{redaction.sanitized_text[:2000]}\n--- END DOCUMENT ---\n\n"
                "Identify any remaining sensitive customer secrets, financial data, or compliance risks.\n"
                "Provide risk_level (CRITICAL, HIGH, MEDIUM, or LOW), relevant GDPR articles (e.g. Art. 6, Art. 9, Art. 32, Art. 83), "
                "and concrete remediation recommendations."
            )
            mock_fallback = {
                "has_pii": redaction.has_pii,
                "detected_types": redaction.detected_types,
                "risk_level": "CRITICAL" if redaction.has_pii else "LOW",
                "gdpr_articles": [
                    "Art. 6 (Lawfulness of Processing)",
                    "Art. 32 (Security of Processing)",
                    "Art. 83 (Administrative Fines)",
                ] if redaction.has_pii else [],
                "remediation": "Revoke public sharing and restrict access." if redaction.has_pii else "Document complies with standards.",
            }
            try:
                res = self.generate_structured(prompt, GeminiDLPAnalysis, mock_response=mock_fallback)
                all_detected = sorted(list(set(redaction.detected_types + res.detected_types)))
                return {
                    "has_pii": redaction.has_pii or res.has_pii,
                    "detected_types": all_detected,
                    "risk_level": res.risk_level.upper() if res.risk_level else ("CRITICAL" if redaction.has_pii else "LOW"),
                    "gdpr_articles": res.gdpr_articles,
                    "remediation": res.remediation,
                }
            except Exception as e:
                logger.warning("Live Gemini classify_document fallback: %s", str(e))

        return {
            "has_pii": redaction.has_pii,
            "detected_types": redaction.detected_types,
            "risk_level": "CRITICAL" if redaction.has_pii else "LOW",
        }

    def recommend_onboarding_ou(self, ticket: Any) -> Dict[str, Any]:
        """Analyze employee ticket and determine least-privilege OU and security flags using Gemini or policies."""
        dept = getattr(ticket, "department", "") or ""
        role = getattr(ticket, "jobTitle", "") or getattr(ticket, "job_title", "") or ""
        dept_l = dept.lower()
        role_l = role.lower()

        default_ou = "/"
        smime_req = False
        if "finance" in dept_l or any(k in role_l for k in ["payroll", "tax", "cfo"]):
            default_ou = "/Executive_Finance"
            smime_req = True
        elif "engineer" in dept_l or any(k in role_l for k in ["engineer", "developer", "cloud"]):
            default_ou = "/Engineering"
        elif "contractor" in dept_l or "consultant" in role_l:
            default_ou = "/Contractors"

        if not self.is_mock_mode and self._genai_client:
            from pydantic import BaseModel

            class OURecommendation(BaseModel):
                recommended_ou: str
                smime_required: bool
                reasoning: str = ""

            prompt = (
                "You are BuenaGuard AI's zero-trust HR onboarding copilot for BuenaCloud GmbH.\n"
                f"Candidate Department: {dept}\n"
                f"Candidate Role / Job Title: {role}\n\n"
                "Organizational Units:\n"
                "- '/Executive_Finance': Handles salaries, bank transfers, contracts. MANDATORY S/MIME, 2SV required.\n"
                "- '/Engineering': Infrastructure, software developers, devops. Standard 2SV, no S/MIME mandatory.\n"
                "- '/Contractors': External vendors, consultants. Zero-trust restricted, internal access only.\n"
                "- '/': General staff / Other roles.\n\n"
                "Assign the single strictest least-privilege OU from the allowed list and whether S/MIME email encryption is mandatory."
            )
            mock_fallback = {
                "recommended_ou": default_ou,
                "smime_required": smime_req,
                "reasoning": "Determined via least-privilege policy",
            }
            try:
                res = self.generate_structured(prompt, OURecommendation, mock_response=mock_fallback)
                valid_ous = ["/Executive_Finance", "/Engineering", "/Contractors", "/"]
                target_ou = res.recommended_ou if res.recommended_ou in valid_ous else default_ou
                return {
                    "recommended_ou": target_ou,
                    "smime_required": res.smime_required if target_ou == "/Executive_Finance" else res.smime_required,
                    "reasoning": res.reasoning,
                }
            except Exception as e:
                logger.warning("Live Gemini recommend_onboarding_ou fallback: %s", str(e))

        return {"recommended_ou": default_ou, "smime_required": smime_req}
