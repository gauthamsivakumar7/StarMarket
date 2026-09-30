from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class PortfolioPositionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    asset_id: str
    asset_name: str
    shares: Decimal
    avg_cost: Decimal
    current_price: Decimal
    market_value: Decimal
    cost_basis: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_pct: Decimal | None = None


class PortfolioResponse(BaseModel):
    holdings: list[PortfolioPositionResponse]
    total_market_value: Decimal
    total_cost_basis: Decimal
    total_unrealized_pnl: Decimal
    total_unrealized_pnl_pct: Decimal | None = None
