from decimal import Decimal

from pydantic import BaseModel


class IndicatorsResponse(BaseModel):
    rolling_mean_7: Decimal | None
    rolling_mean_30: Decimal | None
    volatility: Decimal | None
    momentum_pct: Decimal | None
