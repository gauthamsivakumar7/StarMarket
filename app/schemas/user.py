from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    email: str
    username: str | None = None


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    is_admin: bool = False
    cash_balance: Decimal
    created_at: str | None = None
