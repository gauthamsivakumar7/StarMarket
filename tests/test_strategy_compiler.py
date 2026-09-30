from datetime import date, timedelta
from decimal import Decimal

from app.schemas.strategy_spec import (
    BooleanOp,
    Condition,
    Constant,
    ExecutionParams,
    IndicatorRef,
    RiskParams,
    StrategySpec,
)
from app.services.market_data.base import OHLCVBar
from app.services.strategy_compiler_service import collect_symbols, compile_strategy, rule_tree_stats


def _bars(closes: list[float]) -> list[OHLCVBar]:
    start = date(2024, 1, 1)
    return [
        OHLCVBar(
            date=start + timedelta(days=i),
            open=Decimal(str(c)),
            high=Decimal(str(c)),
            low=Decimal(str(c)),
            close=Decimal(str(c)),
            volume=1000,
        )
        for i, c in enumerate(closes)
    ]


def _crossover_spec() -> StrategySpec:
    entry = Condition(
        left=IndicatorRef(name="SMA", symbol="TEST", params={"window": 2}),
        op="crosses_above",
        right=IndicatorRef(name="SMA", symbol="TEST", params={"window": 3}),
    )
    return StrategySpec(
        name="test",
        universe=["TEST"],
        asset_class="equity",
        entry_rule=entry,
        risk=RiskParams(max_portfolio_risk_pct=Decimal("1")),
        execution=ExecutionParams(),
    )


def test_compiler_detects_sma_crossover_at_expected_bar():
    spec = _crossover_spec()
    compiled = compile_strategy(spec)
    assert compiled.required_symbols == {"TEST"}

    bars = _bars([10, 10, 10, 10, 20])
    ctx = compiled.prepare({"TEST": bars})

    assert compiled.evaluate_entry(ctx, 2) is None  # SMA(3) has no prior-bar value yet at i=1
    assert compiled.evaluate_entry(ctx, 3) is False
    assert compiled.evaluate_entry(ctx, 4) is True


def test_collect_symbols_includes_context_only_symbols():
    entry = BooleanOp(
        type="and",
        children=[
            Condition(
                left=IndicatorRef(name="SMA", symbol="SPY", params={"window": 20}),
                op="crosses_above",
                right=IndicatorRef(name="SMA", symbol="SPY", params={"window": 50}),
            ),
            Condition(
                left=IndicatorRef(name="CLOSE", symbol="^VIX", params={}),
                op="<",
                right=Constant(value=Decimal("20")),
            ),
        ],
    )
    symbols = collect_symbols(entry)
    assert symbols == {"SPY", "^VIX"}


def test_rule_tree_stats_counts_depth_and_nodes():
    leaf = Condition(
        left=IndicatorRef(name="CLOSE", symbol="SPY", params={}),
        op=">",
        right=Constant(value=Decimal("1")),
    )
    depth, count = rule_tree_stats(leaf)
    assert (depth, count) == (1, 1)

    wrapped = BooleanOp(type="and", children=[leaf, leaf])
    depth, count = rule_tree_stats(wrapped)
    assert depth == 2
    assert count == 3  # the and node + 2 leaves
