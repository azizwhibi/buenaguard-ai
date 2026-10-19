from pathlib import Path
import pytest

def test_subagent_markdown_structure():
    """Verify that Antigravity subagent persona prompt files exist and contain required role directives."""
    agents_dir = Path("agents")
    assert agents_dir.exists(), "agents/ directory must exist"

    # 1. Security Auditor Persona
    sec_file = agents_dir / "security-auditor.md"
    assert sec_file.exists(), "agents/security-auditor.md must exist"
    sec_text = sec_file.read_text(encoding="utf-8")
    assert "GDPR" in sec_text or "DSGVO" in sec_text
    assert "PII" in sec_text
    assert "OAuth" in sec_text
    assert "Rule 4" in sec_text or "Zero Raw PII" in sec_text

    # 2. Test Engineer Persona
    qa_file = agents_dir / "test-engineer.md"
    assert qa_file.exists(), "agents/test-engineer.md must exist"
    qa_text = qa_file.read_text(encoding="utf-8")
    assert "pytest" in qa_text.lower()
    assert "coverage" in qa_text.lower()
    assert "90%" in qa_text or ">= 90" in qa_text
    assert "mock" in qa_text.lower() or "isolation" in qa_text.lower()

    # 3. Code Reviewer Persona
    rev_file = agents_dir / "code-reviewer.md"
    assert rev_file.exists(), "agents/code-reviewer.md must exist"
    rev_text = rev_file.read_text(encoding="utf-8")
    assert "Hexagonal" in rev_text
    assert "Ponytail" in rev_text
    assert "Pydantic" in rev_text
