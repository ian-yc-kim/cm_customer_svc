from pathlib import Path


def test_api_md_exists_and_contains_session_endpoints():
    p = Path("API.md")
    assert p.exists(), "API.md must exist in repository root"
    text = p.read_text(encoding="utf8").lower()

    # Essential endpoint signatures
    assert "post /api/auth/login" in text or "/api/auth/login" in text
    assert "post /api/auth/logout" in text or "/api/auth/logout" in text
    assert "get /api/users/me" in text or "/api/users/me" in text

    # Cookie security flags and attributes
    assert "httponly" in text
    assert "secure" in text
    assert "samesite" in text
    assert "max-age" in text or "max age" in text

    # Examples and request/response references
    assert "{ \"username\": \"string\", \"password\": \"string\" }" in p.read_text(encoding="utf8") or "username" in text
    assert "{ \"message\": \"login successful\" }" in p.read_text(encoding="utf8") or "login successful" in text

    # Ensure cookie name is documented
    assert "access_token" in text
