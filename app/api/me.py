from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter(tags=["me"])


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        is_admin=current_user.is_admin,
        cash_balance=current_user.cash_balance,
        created_at=current_user.created_at.isoformat() if current_user.created_at else None,
    )
