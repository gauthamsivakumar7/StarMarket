from decimal import Decimal

from pydantic import BaseModel


class TradeOrder(BaseModel):
    asset_id: str
    shares: Decimal


class TradeResponse(BaseModel):
    message: str
    position: dict
    cash_balance: Decimal
