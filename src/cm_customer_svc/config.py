import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def _get_env_bool(name: str, default: bool) -> bool:
    """Read an environment variable and interpret common truthy/falsey values.

    On any error, log and return default.
    """
    val = os.getenv(name)
    if val is None:
        return default
    try:
        v = val.strip().lower()
        return v in ("1", "true", "t", "yes", "y")
    except Exception as e:
        logging.error(e, exc_info=True)
        return default


def _get_env_int(name: str, default: int) -> int:
    """Parse environment variable as int. On failure, log and return default."""
    val = os.getenv(name)
    if val is None:
        return default
    try:
        return int(val)
    except Exception as e:
        logging.error(e, exc_info=True)
        return default


# Existing DB and service settings
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///:memory:")
SERVICE_PORT: int = _get_env_int("SERVICE_PORT", 8000)

# JWT and session cookie settings
SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key")
ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = _get_env_int("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24)

SECURE_COOKIE: bool = _get_env_bool("SECURE_COOKIE", True)
HTTP_ONLY_COOKIE: bool = _get_env_bool("HTTP_ONLY_COOKIE", True)
SAMESITE_COOKIE: str = os.getenv("SAMESITE_COOKIE", "Lax")
