import pytest
from src.services.pii_pre_filter import PIIPreFilter

def test_pii_prefilter_unseparated_salary_and_lowercase():
    """Verify detection of unseparated numbers and lowercase currency (e.g. 95000 €, 80000 eur)."""
    filter = PIIPreFilter()
    sample = "Das Einstiegsgehalt liegt bei 95000 € und der Bonus bei 15000 eur."
    result = filter.sanitize(sample)
    
    assert result.has_pii is True
    assert "SALARY" in result.detected_types
    assert "95000 €" not in result.sanitized_text
    assert "15000 eur" not in result.sanitized_text
    assert "[REDACTED_SALARY_1]" in result.sanitized_text
    assert "[REDACTED_SALARY_2]" in result.sanitized_text

def test_pii_prefilter_spaced_steuer_id():
    """Verify German Steuer-ID formatted with official tax office spaces (e.g. 12 345 678 901)."""
    filter = PIIPreFilter()
    sample = "Steuer-ID laut Finanzamt: 12 345 678 901 oder 123 456 789 01."
    result = filter.sanitize(sample)
    
    assert result.has_pii is True
    assert "STEUER_ID" in result.detected_types
    assert "12 345 678 901" not in result.sanitized_text
    assert "123 456 789 01" not in result.sanitized_text

def test_pii_prefilter_credit_card_detection():
    """Verify payment card numbers formatted with dashes or spaces."""
    filter = PIIPreFilter()
    sample = "Kreditkarte zur Verifizierung: 4532-0150-1234-5678 oder 4532 0150 1234 9999."
    result = filter.sanitize(sample)
    
    assert result.has_pii is True
    assert "CREDIT_CARD" in result.detected_types
    assert "4532-0150-1234-5678" not in result.sanitized_text
    assert "4532 0150 1234 9999" not in result.sanitized_text
    assert "[REDACTED_CREDIT_CARD_1]" in result.sanitized_text

def test_pii_prefilter_eu_sepa_iban_detection():
    """Verify non-German EU IBANs like Italian contractor IBANs in tenant fixtures."""
    filter = PIIPreFilter()
    sample = "Contractor IBAN: IT60X0542811101000000123456 oder FR1420041010050500013M02606."
    result = filter.sanitize(sample)
    
    assert result.has_pii is True
    assert "IBAN" in result.detected_types
    assert "IT60X0542811101000000123456" not in result.sanitized_text
    assert "FR1420041010050500013M02606" not in result.sanitized_text

def test_passport_does_not_falsely_redact_standard_english_words():
    """Verify common 9-letter English words (DOCUMENTS, EXCELLENT) are NOT flagged as passports."""
    filter = PIIPreFilter()
    sample = "PLEASE REVIEW THE EXCELLENT DOCUMENTS AND CONFIRMED AGREEMENTS."
    result = filter.sanitize(sample)
    
    # Must NOT flag as passport
    assert "PASSPORT" not in result.detected_types
    assert "DOCUMENTS" in result.sanitized_text
    assert "EXCELLENT" in result.sanitized_text
