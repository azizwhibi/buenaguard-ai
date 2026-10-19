import os
import pytest

def test_agents_md_rules_presence():
    """Verify that AGENTS.md exists and contains mandatory architectural and security rules."""
    agents_md_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "AGENTS.md")
    assert os.path.exists(agents_md_path), "AGENTS.md must exist in the root directory"
    
    with open(agents_md_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Core governance keywords and rules required by specification
    required_keywords = [
        "GDPR",
        "PII",
        "drive.readonly",
        "Hexagonal",
        "TDD",
        "zero-billing",
    ]
    for keyword in required_keywords:
        assert keyword.lower() in content.lower(), f"AGENTS.md must include governance directive for '{keyword}'"
