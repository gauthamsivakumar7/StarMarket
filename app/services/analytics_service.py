from decimal import Decimal
from typing import Sequence

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.price_history import PriceHistory


async def get_indicators(
    db: AsyncSession, asset_id: str, limit: int = 60
) -> dict[str, Decimal | None]:
    result = await db.execute(
        select(PriceHistory.price, PriceHistory.created_at)
        .where(PriceHistory.asset_id == asset_id)
        .order_by(desc(PriceHistory.created_at))
        .limit(limit)
    )
    rows = result.all()
    if not rows:
        return {
            "rolling_mean_7": None,
            "rolling_mean_30": None,
            "volatility": None,
            "momentum_pct": None,
        }

    prices = [float(r[0]) for r in reversed(rows)]
    n = len(prices)

    def safe_decimal(v: float | None) -> Decimal | None:
        if v is None:
            return None
        return Decimal(str(round(v, 6)))

    rolling_mean_7 = sum(prices[-7:]) / min(7, n) if n >= 1 else None
    rolling_mean_30 = sum(prices[-30:]) / min(30, n) if n >= 1 else None

    if n < 2:
        volatility = None
    else:
        returns = [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, n)]
        mean_ret = sum(returns) / len(returns)
        variance = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
        volatility = variance ** 0.5 if variance >= 0 else 0

    if n >= 2 and n >= 8:
        p_old = prices[-8]
        p_new = prices[-1]
        momentum_pct = (p_new - p_old) / p_old if p_old != 0 else None
    else:
        momentum_pct = None

    return {
        "rolling_mean_7": safe_decimal(rolling_mean_7),
        "rolling_mean_30": safe_decimal(rolling_mean_30),
        "volatility": safe_decimal(volatility),
        "momentum_pct": safe_decimal(momentum_pct),
    }


async def get_forecast_stub(
    db: AsyncSession, asset_id: str, horizon_days: int = 7
) -> tuple[float, str]:
    result = await db.execute(
        select(PriceHistory.price)
        .where(PriceHistory.asset_id == asset_id)
        .order_by(desc(PriceHistory.created_at))
        .limit(10)
    )
    prices = [float(r[0]) for r in result.all()]
    if len(prices) < 2:
        current = float(prices[0]) if prices else 100.0
        return current, "stub"
    prices = list(reversed(prices))
    slope = (prices[-1] - prices[0]) / (len(prices) - 1) if len(prices) > 1 else 0
    predicted = float(prices[-1]) + slope * horizon_days
    if predicted <= 0:
        predicted = float(prices[-1])
    return predicted, "stub"
