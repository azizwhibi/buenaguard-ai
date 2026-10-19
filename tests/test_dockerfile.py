from pathlib import Path
import pytest
import yaml

def test_dockerfile_best_practices():
    """Verify Dockerfile follows Cloud Run best practices (non-root user, dynamic port, lean base)."""
    dockerfile_path = Path("Dockerfile")
    assert dockerfile_path.exists(), "Dockerfile must exist"
    content = dockerfile_path.read_text(encoding="utf-8")

    # Base image
    assert "FROM python:" in content
    assert "slim" in content or "alpine" in content

    # Non-root user
    assert "USER " in content
    assert "USER root" not in content.splitlines()[-1]

    # Dynamic PORT binding
    assert "PORT" in content
    assert "8080" in content

    # Entrypoint starts uvicorn
    assert "uvicorn" in content.lower() or "granian" in content.lower()
    assert "src.main:app" in content

def test_dockerignore_excludes_secrets():
    """Verify .dockerignore excludes confidential credentials and developer artifacts."""
    dockerignore_path = Path(".dockerignore")
    assert dockerignore_path.exists(), ".dockerignore must exist"
    lines = dockerignore_path.read_text(encoding="utf-8").splitlines()
    cleaned = [line.strip() for line in lines if line.strip() and not line.startswith("#")]

    expected_exclusions = [
        "credentials.json",
        "geminiapikey.txt",
        "token.json",
        ".git",
        "audit_logs.db",
    ]
    for exclusion in expected_exclusions:
        assert any(exclusion in line for line in cleaned), f"Expected '{exclusion}' in .dockerignore"

def test_cloudrun_yaml_configuration():
    """Verify cloudrun.yaml adheres to Google Cloud Run service specification."""
    cloudrun_path = Path("cloudrun.yaml")
    assert cloudrun_path.exists(), "cloudrun.yaml must exist"
    data = yaml.safe_load(cloudrun_path.read_text(encoding="utf-8"))

    assert data.get("kind") == "Service"
    assert "serving.knative.dev" in data.get("apiVersion", "")

    spec = data.get("spec", {}).get("template", {}).get("spec", {})
    containers = spec.get("containers", [])
    assert len(containers) >= 1

    container = containers[0]
    ports = container.get("ports", [])
    assert any(p.get("containerPort") == 8080 for p in ports)

    # Health probe
    probe = container.get("startupProbe") or container.get("livenessProbe")
    assert probe is not None
    assert probe.get("httpGet", {}).get("path") == "/health"
