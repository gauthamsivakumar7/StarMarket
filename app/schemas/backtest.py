from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class BacktestRequest(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    starting_cash: float = 10000.0


class BacktestRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    strategy_id: str
    status: str
    start_date: date
    end_date: date
    starting_cash: Decimal
    metrics: dict | None = None
    equity_curve: list[dict] | None = None
    trades: list[dict] | None = None
    error_message: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None
