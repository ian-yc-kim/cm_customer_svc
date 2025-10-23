import importlib
import sys
import logging
from pathlib import Path


def _reload_config():
    name = "cm_customer_svc.config"
    if name in sys.modules:
        del sys.modules[name]
    return importlib.import_module(name)


def test_config_defaults(monkeypatch):
    # ensure related env vars are not set
    for k in [
        "SECRET_KEY",
        "ALGORITHM",
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "SECURE_COOKIE",
        "HTTP_ONLY_COOKIE",
        "SAMESITE_COOKIE",
        "SERVICE_PORT",
    ]:
        monkeypatch.delenv(k, raising=False)

    cfg = _reload_config()

    assert cfg.SECRET_KEY == "super-secret-key"
    assert cfg.ALGORITHM == "HS256"
    assert cfg.ACCESS_TOKEN_EXPIRE_MINUTES == 60 * 24
    assert cfg.SECURE_COOKIE is True
    assert cfg.HTTP_ONLY_COOKIE is True
    assert cfg.SAMESITE_COOKIE == "Lax"


def test_config_env_overrides(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "mysecret")
    monkeypatch.setenv("ALGORITHM", "HS512")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    monkeypatch.setenv("SECURE_COOKIE", "false")
    monkeypatch.setenv("HTTP_ONLY_COOKIE", "false")
    monkeypatch.setenv("SAMESITE_COOKIE", "Strict")
    monkeypatch.setenv("SERVICE_PORT", "9000")

    cfg = _reload_config()

    assert cfg.SECRET_KEY == "mysecret"
    assert cfg.ALGORITHM == "HS512"
    assert cfg.ACCESS_TOKEN_EXPIRE_MINUTES == 30
    assert cfg.SECURE_COOKIE is False
    assert cfg.HTTP_ONLY_COOKIE is False
    assert cfg.SAMESITE_COOKIE == "Strict"
    assert cfg.SERVICE_PORT == 9000


def test_config_invalid_int_fallback(monkeypatch, caplog):
    # set invalid int value and ensure fallback and logging
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "notanint")
    caplog.set_level(logging.ERROR)
    cfg = _reload_config()
    assert cfg.ACCESS_TOKEN_EXPIRE_MINUTES == 60 * 24
    # Ensure an error was logged during parsing
    assert any(record.levelno >= logging.ERROR for record in caplog.records)
