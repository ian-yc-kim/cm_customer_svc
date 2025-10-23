from fastapi import APIRouter, Depends

from cm_customer_svc.dependencies.auth import get_current_user

users_router = APIRouter()


@users_router.get("/me")
def me(current_user_id: str = Depends(get_current_user)):
    """Return the current authenticated user's id."""
    return {"current_user_id": current_user_id}
