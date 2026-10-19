import pytest
from src.services.pii_prefilter import PIIPreFilter
from src.services.pii_pre_filter import PIIPreFilter as PIIPreFilterAlias

def test_pii_prefilter_alias_compatibility():
    """Verify alias pii_pre_filter matches pii_prefilter."""
    assert PIIPreFilterAlias is PIIPreFilter

def test_pii_prefilter_german_iban_tokenization():
    """Verify German IBAN detection and replacement with zero raw PII leakage."""
    filter = PIIPreFilter()
    sample_text = "Bitte überweisen Sie das Gehalt an DE89370400440532013000 oder DE12500105170648489890."
    result = filter.sanitize(sample_text)
    
    assert result.has_pii is True
    assert "IBAN" in result.detected_types
    assert "DE89370400440532013000" not in result.sanitized_text
    assert "DE12500105170648489890" not in result.sanitized_text
    assert "[REDACTED_IBAN_1]" in result.sanitized_text
    assert "[REDACTED_IBAN_2]" in result.sanitized_text

def test_pii_prefilter_steuer_id_detection():
    """Verify German 11-digit Steuer-ID tokenization."""
    filter = PIIPreFilter()
    sample_text = "Die steuerliche Identifikationsnummer (Steuer-ID) lautet 12345678901."
    result = filter.sanitize(sample_text)
    
    assert result.has_pii is True
    assert "STEUER_ID" in result.detected_types
    assert "12345678901" not in result.sanitized_text
    assert "[REDACTED_STEUER_ID_1]" in result.sanitized_text

def test_pii_prefilter_passport_detection():
    """Verify German passport number detection and redaction."""
    filter = PIIPreFilter()
    sample_text = "Reisepassnummer: C01X00T47 ausgestellt in Berlin."
    result = filter.sanitize(sample_text)
    
    assert result.has_pii is True
    assert "PASSPORT" in result.detected_types
    assert "C01X00T47" not in result.sanitized_text
    assert "[REDACTED_PASSPORT_1]" in result.sanitized_text

def test_pii_prefilter_email_detection():
    """Verify email address tokenization."""
    filter = PIIPreFilter()
    sample_text = "Kontaktieren Sie uns unter security-lead@buenacloud.de für Audit-Berichte."
    result = filter.sanitize(sample_text)
    
    assert result.has_pii is True
    assert "EMAIL" in result.detected_types
    assert "security-lead@buenacloud.de" not in result.sanitized_text
    assert "[REDACTED_EMAIL_1]" in result.sanitized_text

def test_pii_prefilter_salary_detection():
    """Verify salary and compensation figures redaction."""
    filter = PIIPreFilter()
    sample_text = "Das vereinbarte Bruttojahresgehalt beträgt 120.000 € plus 15.000 EUR Bonus."
    result = filter.sanitize(sample_text)
    
    assert result.has_pii is True
    assert "SALARY" in result.detected_types
    assert "120.000 €" not in result.sanitized_text
    assert "15.000 EUR" not in result.sanitized_text
    assert "[REDACTED_SALARY_1]" in result.sanitized_text

def test_pii_prefilter_clean_text_no_pii():
    """Verify text without PII is unmodified and marked clean."""
    filter = PIIPreFilter()
    sample_text = "Dies ist ein unbedenklicher Projektbericht über die Google Workspace Bereitstellung."
    result = filter.sanitize(sample_text)
    
    assert result.has_pii is False
    assert len(result.detected_types) == 0
    assert result.sanitized_text == sample_text

def test_pii_prefilter_all_in_one_and_reversibility():
    """Verify multi-PII document redaction and secure in-memory reversal."""
    filter = PIIPreFilter()
    sample_text = (
        "Mitarbeiter: max.mustermann@buenacloud.de, Pass: C02Y88A12, "
        "Steuer-ID: 98765432109, IBAN: DE44500105175555555555, Gehalt: 95.000 €."
    )
    result = filter.sanitize(sample_text)
    
    assert result.has_pii is True
    assert set(result.detected_types) == {"EMAIL", "PASSPORT", "STEUER_ID", "IBAN", "SALARY"}
    # Verify no raw PII in sanitized text
    for pii in ["max.mustermann@buenacloud.de", "C02Y88A12", "98765432109", "DE44500105175555555555", "95.000 €"]:
        assert pii not in result.sanitized_text
        
    # Verify reconstruction/detokenization works with token map
    restored = filter.detokenize(result.sanitized_text, result.token_map)
    assert restored == sample_text

def test_pii_prefilter_repr_zero_pii_leakage():
    """Verify Rule 4: repr(result) does not leak raw PII stored in token_map."""
    filter = PIIPreFilter()
    sample_text = "Gehalt ist 120.000 € und IBAN DE89370400440532013000"
    result = filter.sanitize(sample_text)
    
    repr_str = repr(result)
    assert "DE89370400440532013000" not in repr_str
    assert "120.000 €" not in repr_str
    assert "token_map" not in repr_str
