from decimal import Decimal

from pydantic import BaseModel


class ForecastResponse(BaseModel):
    horizon_days: int
    predicted_price: float
    model: str = "stub"
