from pathlib import Path


def test_python_jose_dependency_present():
    content = Path("pyproject.toml").read_text(encoding="utf-8")
    # Ensure python-jose and its cryptography extra are present
    assert "python-jose" in content
    assert "cryptography" in content
