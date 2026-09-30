"""Compiles a validated StrategySpec into something that can be evaluated
against aligned OHLCV bar series. Pure, asset-class-agnostic: operates only on
symbol -> list[OHLCVBar], never on the spec's asset_class.
"""
from dataclasses import dataclass, field

from app.schemas.strategy_spec import BooleanOp, Condition, Constant, IndicatorRef, RuleNode, StrategySpec
from app.services import indicator_math
from app.services.market_data.base import OHLCVBar

_SERIES_INDICATORS = {"SMA": indicator_math.sma, "EMA": indicator_math.ema, "RSI": indicator_math.rsi}


def collect_symbols(node: RuleNode) -> set[str]:
    """All symbols referenced anywhere in a rule tree (not just the universe)."""
    symbols: set[str] = set()
    _walk_symbols(node, symbols)
    return symbols


def _walk_symbols(node: RuleNode, out: set[str]) -> None:
    if isinstance(node, Condition):
        for operand in (node.left, node.right):
            if isinstance(operand, IndicatorRef):
                out.add(operand.symbol)
    elif isinstance(node, BooleanOp):
        for child in node.children:
            _walk_symbols(child, out)


def rule_tree_stats(node: RuleNode) -> tuple[int, int]:
    """(max_depth, node_count) — used by the validator to reject pathological trees."""
    return _stats(node, depth=1)


def _stats(node: RuleNode, depth: int) -> tuple[int, int]:
    if isinstance(node, Condition):
        return depth, 1
    max_depth, count = depth, 1
    for child in node.children:
        child_depth, child_count = _stats(child, depth + 1)
        max_depth = max(max_depth, child_depth)
        count += child_count
    return max_depth, count


def _indicator_key(ref: IndicatorRef) -> tuple:
    return (ref.symbol, ref.name, tuple(sorted(ref.params.items())))


@dataclass
class StrategyContext:
    bars_by_symbol: dict[str, list[OHLCVBar]]
    _closes: dict[str, list[float]] = field(init=False)
    _volumes: dict[str, list[float]] = field(init=False)
    _series_cache: dict[tuple, list[float | None]] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self._closes = {s: [float(b.close) for b in bars] for s, bars in self.bars_by_symbol.items()}
        self._volumes = {s: [float(b.volume) for b in bars] for s, bars in self.bars_by_symbol.items()}

    def length(self, symbol: str) -> int:
        return len(self.bars_by_symbol.get(symbol, []))

    def indicator_series(self, ref: IndicatorRef) -> list[float | None]:
        key = _indicator_key(ref)
        if key in self._series_cache:
            return self._series_cache[key]

        if ref.symbol not in self._closes:
            raise KeyError(f"No bar data resolved for symbol '{ref.symbol}'")
        closes = self._closes[ref.symbol]

        if ref.name == "CLOSE":
            series: list[float | None] = list(closes)
        elif ref.name == "VOLUME":
            series = list(self._volumes[ref.symbol])
        elif ref.name in _SERIES_INDICATORS:
            window = ref.params.get("window", 20)
            series = _SERIES_INDICATORS[ref.name](closes, window)
        else:
            raise ValueError(f"Unsupported indicator '{ref.name}'")

        self._series_cache[key] = series
        return series

    def _operand_series(self, operand: IndicatorRef | Constant, length: int) -> list[float | None]:
        if isinstance(operand, Constant):
            return [float(operand.value)] * length
        return self.indicator_series(operand)

    def eval_node(self, node: RuleNode, i: int) -> bool | None:
        if isinstance(node, Condition):
            return self._eval_condition(node, i)
        if node.type == "not":
            result = self.eval_node(node.children[0], i)
            return None if result is None else (not result)
        results = [self.eval_node(child, i) for child in node.children]
        if node.type == "and":
            if any(r is False for r in results):
                return False
            if any(r is None for r in results):
                return None
            return True
        if node.type == "or":
            if any(r is True for r in results):
                return True
            if any(r is None for r in results):
                return None
            return False
        raise ValueError(f"Unknown boolean op '{node.type}'")

    def _eval_condition(self, cond: Condition, i: int) -> bool | None:
        primary_symbol = _primary_symbol(cond)
        length = self.length(primary_symbol) if primary_symbol else i + 1
        left = self._operand_series(cond.left, length)
        right = self._operand_series(cond.right, length)
        if i >= len(left) or i >= len(right):
            return None

        if cond.op == "crosses_above":
            return indicator_math.crosses_above(left, right, i)
        if cond.op == "crosses_below":
            return indicator_math.crosses_below(left, right, i)

        l_val, r_val = left[i], right[i]
        if l_val is None or r_val is None:
            return None
        if cond.op == ">":
            return l_val > r_val
        if cond.op == "<":
            return l_val < r_val
        if cond.op == ">=":
            return l_val >= r_val
        if cond.op == "<=":
            return l_val <= r_val
        if cond.op == "==":
            return l_val == r_val
        raise ValueError(f"Unknown comparison op '{cond.op}'")


def _primary_symbol(cond: Condition) -> str | None:
    for operand in (cond.left, cond.right):
        if isinstance(operand, IndicatorRef):
            return operand.symbol
    return None


@dataclass
class CompiledStrategy:
    spec: StrategySpec
    required_symbols: set[str]

    def prepare(self, bars_by_symbol: dict[str, list[OHLCVBar]]) -> StrategyContext:
        missing = self.required_symbols - set(bars_by_symbol)
        if missing:
            raise KeyError(f"Missing bar data for required symbols: {sorted(missing)}")
        return StrategyContext(bars_by_symbol)

    def evaluate_entry(self, ctx: StrategyContext, i: int) -> bool | None:
        return ctx.eval_node(self.spec.entry_rule, i)

    def evaluate_exit(self, ctx: StrategyContext, i: int) -> bool | None:
        if self.spec.exit_rule is None:
            return None
        return ctx.eval_node(self.spec.exit_rule, i)


def compile_strategy(spec: StrategySpec) -> CompiledStrategy:
    symbols = set(spec.universe) | collect_symbols(spec.entry_rule)
    if spec.exit_rule is not None:
        symbols |= collect_symbols(spec.exit_rule)
    return CompiledStrategy(spec=spec, required_symbols=symbols)
