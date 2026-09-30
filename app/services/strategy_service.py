from dataclasses import asdict
from datetime import date, timedelta

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.backtest_run import BacktestRun, BacktestStatus
from app.models.strategy import Strategy, StrategyStatus
from app.models.user import User
from app.schemas.strategy_spec import StrategySpec
from app.services import instrument_resolution_service, llm_client
from app.services import strategy_validation_service as validation
from app.services.backtest_service import run_backtest as _run_backtest

SYSTEM_PROMPT = """You translate a plain-language trading thesis into a strict JSON strategy \
specification. Output ONLY JSON matching the provided schema, no prose.

Rules:
- universe: list of exactly one ticker symbol to trade (e.g. ["SPY"]).
- asset_class: one of equity, crypto, prediction_market, commodity, yield. Infer from the thesis; \
default to "equity" for stocks/ETFs/indices.
- entry_rule / exit_rule: a boolean expression tree. Each node is either:
  {"type": "condition", "left": <operand>, "op": "crosses_above"|"crosses_below"|">"|"<"|">="|"<="|"==", "right": <operand>}
  {"type": "and"|"or"|"not", "children": [<node>, ...]}
  An operand is either:
  {"type": "indicator", "name": "SMA"|"EMA"|"RSI"|"CLOSE"|"VOLUME", "symbol": "SPY", "params": {"window": 20}}
  {"type": "constant", "value": 20}
- risk: {"max_portfolio_risk_pct": <0-5>, "stop_loss_pct": <optional>, "take_profit_pct": <optional>, \
"max_position_pct": <0-100>}
- execution: {"order_type": "MARKET"} — MARKET is the only supported order type.

Example thesis: "Universe: SPY. Entry: SMA(close,20) crosses_above SMA(close,50) AND VIX < 20. \
Risk: max_portfolio_risk=1%, stop_loss=2%. Execution: MARKET."
Example output:
{"name": "SPY SMA crossover with VIX filter", "universe": ["SPY"], "asset_class": "equity",
 "entry_rule": {"type": "and", "children": [
   {"type": "condition",
    "left": {"type": "indicator", "name": "SMA", "symbol": "SPY", "params": {"window": 20}},
    "op": "crosses_above",
    "right": {"type": "indicator", "name": "SMA", "symbol": "SPY", "params": {"window": 50}}},
   {"type": "condition",
    "left": {"type": "indicator", "name": "CLOSE", "symbol": "^VIX", "params": {}},
    "op": "<",
    "right": {"type": "constant", "value": 20}}
 ]},
 "exit_rule": null,
 "risk": {"max_portfolio_risk_pct": 1, "stop_loss_pct": 2, "max_position_pct": 100},
 "execution": {"order_type": "MARKET"}}
"""

BACKTEST_LOOKBACK_YEARS = 2


class StrategyServiceError(Exception):
    def __init__(self, message: str, status_code: int = 422, issues: list[dict] | None = None):
        self.message = message
        self.status_code = status_code
        self.issues = issues or []


async def create_strategy_from_thesis(db: AsyncSession, user: User, thesis_text: str, name: str | None) -> Strategy:
    schema = StrategySpec.model_json_schema()
    spec = await _generate_and_validate_spec(thesis_text, schema)

    issues = validation.validate_spec(spec)
    if validation.has_errors(issues):
        raise StrategyServiceError(
            "Generated strategy failed validation",
            issues=[asdict(i) for i in issues],
        )

    strategy = Strategy(
        user_id=user.id,
        name=name or spec.name,
        thesis_text=thesis_text,
        asset_class=spec.asset_class,
        canonical_spec=spec.model_dump(mode="json"),
        validation_issues=[asdict(i) for i in issues] or None,
        status=StrategyStatus.DRAFT,
    )
    db.add(strategy)
    await db.commit()
    await db.refresh(strategy)
    return strategy


async def _generate_and_validate_spec(thesis_text: str, schema: dict) -> StrategySpec:
    try:
        raw = await llm_client.generate_structured(SYSTEM_PROMPT, thesis_text, schema, "strategy_spec")
        return StrategySpec.model_validate(raw)
    except (llm_client.LLMError, ValidationError) as first_error:
        try:
            repair_prompt = (
                f"{thesis_text}\n\nYour previous output failed validation with this error:\n"
                f"{first_error}\nFix it and resend valid JSON only."
            )
            raw = await llm_client.generate_structured(SYSTEM_PROMPT, repair_prompt, schema, "strategy_spec")
            return StrategySpec.model_validate(raw)
        except (llm_client.LLMError, ValidationError) as second_error:
            raise StrategyServiceError(
                f"Could not translate thesis into a valid strategy: {second_error}"
            ) from second_error


async def resolve_strategy(db: AsyncSession, strategy: Strategy) -> Strategy:
    spec = StrategySpec.model_validate(strategy.canonical_spec)
    try:
        resolved_universe, context_symbols = await instrument_resolution_service.resolve_universe(db, spec)
    except instrument_resolution_service.ResolutionError as e:
        raise StrategyServiceError(str(e)) from e

    strategy.resolved_universe = resolved_universe
    strategy.context_symbols = context_symbols
    strategy.status = StrategyStatus.RESOLVED
    await db.commit()
    await db.refresh(strategy)
    return strategy


async def backtest_strategy(
    db: AsyncSession,
    strategy: Strategy,
    start_date: date | None = None,
    end_date: date | None = None,
    starting_cash: float = 10000.0,
) -> BacktestRun:
    if strategy.status not in (StrategyStatus.RESOLVED, StrategyStatus.BACKTESTED, StrategyStatus.ACTIVE, StrategyStatus.PAUSED):
        raise StrategyServiceError("Strategy must be resolved before it can be backtested", status_code=409)

    spec = StrategySpec.model_validate(strategy.canonical_spec)
    end = end_date or date.today()
    start = start_date or (end - timedelta(days=365 * BACKTEST_LOOKBACK_YEARS))

    run = await _run_backtest(strategy.id, spec, start, end, starting_cash=_to_decimal(starting_cash))
    db.add(run)
    if run.status == BacktestStatus.COMPLETED:
        strategy.status = StrategyStatus.BACKTESTED
    await db.commit()
    await db.refresh(run)
    return run


async def activate_strategy(db: AsyncSession, strategy: Strategy) -> Strategy:
    if strategy.status not in (StrategyStatus.BACKTESTED, StrategyStatus.PAUSED):
        raise StrategyServiceError(
            "Strategy needs at least one completed backtest before it can be activated", status_code=409
        )
    strategy.status = StrategyStatus.ACTIVE
    await db.commit()
    await db.refresh(strategy)
    return strategy


async def pause_strategy(db: AsyncSession, strategy: Strategy) -> Strategy:
    strategy.status = StrategyStatus.PAUSED
    await db.commit()
    await db.refresh(strategy)
    return strategy


def _to_decimal(value: float):
    from decimal import Decimal

    return Decimal(str(value))
