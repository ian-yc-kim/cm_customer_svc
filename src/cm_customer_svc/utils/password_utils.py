from passlib.context import CryptContext
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Use a PBKDF2_SHA256 backend to avoid environment-specific bcrypt backend issues
_ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain password using passlib.

    Raises ValueError on invalid input or hashing failure.
    """
    try:
        if not isinstance(password, str) or not password:
            raise ValueError("password must be a non-empty string")
        hashed = _ctx.hash(password)
        return hashed
    except Exception as e:
        logger.error(e, exc_info=True)
        raise ValueError("failed to hash password") from e


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against the hashed value.

    Returns False on verification failure or internal error.
    """
    try:
        if not isinstance(plain_password, str) or not isinstance(hashed_password, str):
            return False
        return _ctx.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(e, exc_info=True)
        return False
