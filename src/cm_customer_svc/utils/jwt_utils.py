from typing import Any, Dict
from datetime import datetime, timedelta, timezone
import logging

from jose import jwt, JWTError

from cm_customer_svc.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

logger = logging.getLogger(__name__)


def create_access_token(data: Dict[str, Any]) -> str:
    """Create a JWT access token with iat and exp claims.

    data: payload dict (e.g., {"sub": user_id})
    returns encoded JWT string
    """
    to_encode = data.copy()
    now = datetime.now(tz=timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # use unix timestamps for compatibility
    to_encode.update({"iat": int(now.timestamp()), "exp": int(expire.timestamp())})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate JWT token. Raises jose.JWTError on failure."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logging.error(e, exc_info=True)
        raise
