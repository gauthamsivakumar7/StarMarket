from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.deps import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import Token, UserLogin, UserRegister

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token)
async def register(
    data: UserRegister,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    settings = get_settings()
    user = User(
        email=data.email,
        username=data.username,
        password_hash=hash_password(data.password),
        cash_balance=settings.starting_cash,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    expires = timedelta(minutes=settings.access_token_expire_minutes)
    token = create_access_token(data={"sub": str(user.id)}, expires_delta=expires)
    return Token(access_token=token)


@router.post("/login", response_model=Token)
async def login(
    data: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    settings = get_settings()
    expires = timedelta(minutes=settings.access_token_expire_minutes)
    token = create_access_token(data={"sub": str(user.id)}, expires_delta=expires)
    return Token(access_token=token)
