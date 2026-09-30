from decimal import Decimal

from app.schemas.strategy_spec import RiskParams

HUNDRED = Decimal("100")


def size_position(equity: Decimal, price: Decimal, risk: RiskParams) -> Decimal:
    """Shares to buy given account equity, current price, and risk params.
    Shared by the backtester and live plan generation so sizing never diverges
    between simulated and live execution."""
    if price <= 0 or equity <= 0:
        return Decimal("0")

    max_position_value = equity * risk.max_position_pct / HUNDRED
    risk_amount = equity * risk.max_portfolio_risk_pct / HUNDRED

    if risk.stop_loss_pct:
        stop_loss_amount_per_share = price * risk.stop_loss_pct / HUNDRED
        if stop_loss_amount_per_share <= 0:
            position_value = Decimal("0")
        else:
            shares_from_risk = risk_amount / stop_loss_amount_per_share
            position_value = min(shares_from_risk * price, max_position_value)
    else:
        position_value = min(risk_amount, max_position_value)

    shares = position_value / price
    return shares.quantize(Decimal("0.000001"))
