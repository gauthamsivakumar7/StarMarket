import re
from dataclasses import dataclass
from typing import Literal

from app.schemas.strategy_spec import StrategySpec
from app.services.market_data import registry
from app.services.strategy_compiler_service import collect_symbols, rule_tree_stats

SYMBOL_RE = re.compile(r"^\^?[A-Za-z0-9.\-]{1,15}$")

MAX_UNIVERSE_SIZE = 1
MAX_TOTAL_SYMBOLS = 5
MIN_INDICATOR_WINDOW = 2
MAX_INDICATOR_WINDOW = 250
MAX_RULE_TREE_DEPTH = 6
MAX_RULE_TREE_NODES = 40
MAX_PORTFOLIO_RISK_PCT = 5
MAX_STOP_LOSS_PCT = 50
MAX_POSITION_PCT = 100

Severity = Literal["error", "warning"]


@dataclass
class ValidationIssue:
    severity: Severity
    code: str
    message: str


def validate_spec(spec: StrategySpec) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    issues.extend(_validate_universe(spec))
    issues.extend(_validate_asset_class(spec))
    issues.extend(_validate_indicators(spec))
    issues.extend(_validate_risk(spec))
    issues.extend(_validate_rule_tree(spec))
    issues.extend(_validate_execution(spec))

    return issues


def has_errors(issues: list[ValidationIssue]) -> bool:
    return any(i.severity == "error" for i in issues)


def _validate_universe(spec: StrategySpec) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not spec.universe:
        issues.append(ValidationIssue("error", "empty_universe", "universe must contain at least one symbol"))
    elif len(spec.universe) > MAX_UNIVERSE_SIZE:
        issues.append(
            ValidationIssue(
                "error",
                "universe_too_large",
                f"universe supports at most {MAX_UNIVERSE_SIZE} tradable symbol(s) in this version; "
                f"got {len(spec.universe)}",
            )
        )
    for symbol in spec.universe:
        if not SYMBOL_RE.match(symbol):
            issues.append(ValidationIssue("error", "invalid_symbol", f"'{symbol}' is not a valid symbol"))

    all_symbols = set(spec.universe) | collect_symbols(spec.entry_rule)
    if spec.exit_rule is not None:
        all_symbols |= collect_symbols(spec.exit_rule)
    for symbol in all_symbols:
        if not SYMBOL_RE.match(symbol):
            issues.append(
                ValidationIssue("error", "invalid_symbol", f"'{symbol}' referenced in rules is not a valid symbol")
            )
    if len(all_symbols) > MAX_TOTAL_SYMBOLS:
        issues.append(
            ValidationIssue(
                "error",
                "too_many_symbols",
                f"strategy references {len(all_symbols)} symbols across universe+rules; "
                f"max is {MAX_TOTAL_SYMBOLS}",
            )
        )
    return issues


def _validate_asset_class(spec: StrategySpec) -> list[ValidationIssue]:
    if not registry.is_supported(spec.asset_class):
        return [
            ValidationIssue(
                "error",
                "unsupported_asset_class",
                f"asset_class '{spec.asset_class}' is not yet supported (no data adapter registered)",
            )
        ]
    return []


def _validate_indicators(spec: StrategySpec) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    def walk(node) -> None:
        if hasattr(node, "left"):
            for operand in (node.left, node.right):
                if hasattr(operand, "name") and hasattr(operand, "params"):
                    window = operand.params.get("window")
                    if window is not None and not (MIN_INDICATOR_WINDOW <= window <= MAX_INDICATOR_WINDOW):
                        issues.append(
                            ValidationIssue(
                                "error",
                                "invalid_indicator_window",
                                f"{operand.name} window {window} out of bounds "
                                f"[{MIN_INDICATOR_WINDOW}, {MAX_INDICATOR_WINDOW}]",
                            )
                        )
        else:
            for child in node.children:
                walk(child)

    walk(spec.entry_rule)
    if spec.exit_rule is not None:
        walk(spec.exit_rule)
    return issues


def _validate_risk(spec: StrategySpec) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    r = spec.risk
    if not (0 < r.max_portfolio_risk_pct <= MAX_PORTFOLIO_RISK_PCT):
        issues.append(
            ValidationIssue(
                "error",
                "invalid_max_portfolio_risk",
                f"max_portfolio_risk_pct must be in (0, {MAX_PORTFOLIO_RISK_PCT}]",
            )
        )
    if r.stop_loss_pct is not None and not (0 < r.stop_loss_pct <= MAX_STOP_LOSS_PCT):
        issues.append(
            ValidationIssue(
                "error", "invalid_stop_loss", f"stop_loss_pct must be in (0, {MAX_STOP_LOSS_PCT}]"
            )
        )
    if r.take_profit_pct is not None and r.take_profit_pct <= 0:
        issues.append(ValidationIssue("error", "invalid_take_profit", "take_profit_pct must be positive"))
    if not (0 < r.max_position_pct <= MAX_POSITION_PCT):
        issues.append(
            ValidationIssue(
                "error", "invalid_max_position", f"max_position_pct must be in (0, {MAX_POSITION_PCT}]"
            )
        )
    return issues


def _validate_rule_tree(spec: StrategySpec) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for label, node in (("entry_rule", spec.entry_rule), ("exit_rule", spec.exit_rule)):
        if node is None:
            continue
        depth, count = rule_tree_stats(node)
        if depth > MAX_RULE_TREE_DEPTH:
            issues.append(
                ValidationIssue(
                    "error", "rule_tree_too_deep", f"{label} depth {depth} exceeds max {MAX_RULE_TREE_DEPTH}"
                )
            )
        if count > MAX_RULE_TREE_NODES:
            issues.append(
                ValidationIssue(
                    "error", "rule_tree_too_large", f"{label} has {count} nodes, exceeds max {MAX_RULE_TREE_NODES}"
                )
            )
        issues.extend(_find_degenerate_conditions(node, label))
    return issues


def _find_degenerate_conditions(node, label: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if hasattr(node, "left"):
        if node.left == node.right:
            issues.append(
                ValidationIssue(
                    "error", "degenerate_condition", f"{label} compares an operand to itself"
                )
            )
    else:
        for child in node.children:
            issues.extend(_find_degenerate_conditions(child, label))
    return issues


def _validate_execution(spec: StrategySpec) -> list[ValidationIssue]:
    # order_type is already constrained to MARKET by the Pydantic schema itself;
    # nothing further to check here today.
    return []
