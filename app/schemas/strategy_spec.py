from decimal import Decimal
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

IndicatorName = Literal["SMA", "EMA", "RSI", "CLOSE", "VOLUME"]
ComparisonOp = Literal["crosses_above", "crosses_below", ">", "<", ">=", "<=", "=="]
AssetClass = Literal["equity", "crypto", "prediction_market", "commodity", "yield"]
OrderType = Literal["MARKET"]


class Constant(BaseModel):
    type: Literal["constant"] = "constant"
    value: Decimal


class IndicatorRef(BaseModel):
    type: Literal["indicator"] = "indicator"
    name: IndicatorName
    symbol: str
    params: dict[str, int] = Field(default_factory=dict)


Operand = Annotated[Union[IndicatorRef, Constant], Field(discriminator="type")]


class Condition(BaseModel):
    type: Literal["condition"] = "condition"
    left: Operand
    op: ComparisonOp
    right: Operand


class BooleanOp(BaseModel):
    type: Literal["and", "or", "not"]
    children: list["RuleNode"]


RuleNode = Annotated[Union[Condition, BooleanOp], Field(discriminator="type")]
BooleanOp.model_rebuild()


class RiskParams(BaseModel):
    max_portfolio_risk_pct: Decimal
    stop_loss_pct: Decimal | None = None
    take_profit_pct: Decimal | None = None
    max_position_pct: Decimal = Decimal("100")


class ExecutionParams(BaseModel):
    order_type: OrderType = "MARKET"


class StrategySpec(BaseModel):
    name: str
    universe: list[str]
    asset_class: AssetClass
    entry_rule: RuleNode
    exit_rule: RuleNode | None = None
    risk: RiskParams
    execution: ExecutionParams
    timeframe: Literal["1d"] = "1d"
