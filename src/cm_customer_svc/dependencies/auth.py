import logging
from fastapi import Request, HTTPException, status

from cm_customer_svc.utils.jwt_utils import decode_access_token
from cm_customer_svc.routers.auth import ACCESS_TOKEN_COOKIE_NAME

logger = logging.getLogger(__name__)


def get_current_user(request: Request) -> str:
    """FastAPI dependency to get current user id from JWT in session cookie.

    Raises HTTPException 401 when missing/invalid/expired.
    Returns the subject (sub) claim as the user identifier.
    """
    # Extract token from cookie
    token = request.cookies.get(ACCESS_TOKEN_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = decode_access_token(token)
        sub = payload.get("sub")
        if not sub:
            # treat missing subject as invalid token
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
        return sub
    except Exception as e:
        # log the original exception with traceback
        logger.error(e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
