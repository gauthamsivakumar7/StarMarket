"""Deterministic, hand-built OHLCV data for strategy-pipeline tests. No network,
no real market data — a V-shaped price path (decline then climb) guarantees a
clean, single SMA(5)/SMA(10) crossover during the climb leg."""
from datetime import date, timedelta
from decimal import Decimal

from app.services import indicator_math
from app.services.market_data.base import MarketDataAdapter, OHLCVBar

CANNED_STRATEGY_SPEC = {
    "name": "SPY SMA crossover with VIX filter",
    "universe": ["SPY"],
    "asset_class": "equity",
    "entry_rule": {
        "type": "and",
        "children": [
            {
                "type": "condition",
                "left": {"type": "indicator", "name": "SMA", "symbol": "SPY", "params": {"window": 5}},
                "op": "crosses_above",
                "right": {"type": "indicator", "name": "SMA", "symbol": "SPY", "params": {"window": 10}},
            },
            {
                "type": "condition",
                "left": {"type": "indicator", "name": "CLOSE", "symbol": "^VIX", "params": {}},
                "op": "<",
                "right": {"type": "constant", "value": 20},
            },
        ],
    },
    "exit_rule": None,
    "risk": {"max_portfolio_risk_pct": 1, "stop_loss_pct": 2, "max_position_pct": 100},
    "execution": {"order_type": "MARKET"},
}


def _make_bar(d: date, close: Decimal) -> OHLCVBar:
    return OHLCVBar(date=d, open=close, high=close + 1, low=close - 1, close=close, volume=1_000_000)


def _build_spy_closes() -> list[Decimal]:
    closes: list[Decimal] = []
    price = Decimal("100")
    for i in range(20):  # decline: 100 -> 81
        price = Decimal("100") - Decimal(i)
        closes.append(price)
    base = price
    for i in range(1, 41):  # climb: base -> base+120
        closes.append(base + Decimal(3 * i))
    return closes


def _dates(n: int, start: date = date(2024, 1, 2)) -> list[date]:
    return [start + timedelta(days=i) for i in range(n)]


def _crossover_index(closes: list[Decimal]) -> int:
    floats = [float(c) for c in closes]
    sma5 = indicator_math.sma(floats, 5)
    sma10 = indicator_math.sma(floats, 10)
    for i in range(len(floats)):
        if indicator_math.crosses_above(sma5, sma10, i):
            return i
    raise AssertionError("synthetic series has no SMA crossover; fixture construction is broken")


def build_spy_vix_bars() -> dict[str, list[OHLCVBar]]:
    """Full series: decline, then a climb long enough for a crossover plus
    several trailing bars so a backtest has room to force-close a trade."""
    closes = _build_spy_closes()
    dates = _dates(len(closes))
    spy_bars = [_make_bar(d, c) for d, c in zip(dates, closes)]
    vix_bars = [_make_bar(d, Decimal("15")) for d in dates]  # always < 20, never gates the signal
    return {"SPY": spy_bars, "^VIX": vix_bars}


def build_spy_vix_bars_at_crossover() -> dict[str, list[OHLCVBar]]:
    """Same series truncated so the LAST bar is exactly the crossover bar —
    used to deterministically make a live /evaluate call fire 'right now'."""
    full = build_spy_vix_bars()
    idx = _crossover_index(_build_spy_closes())
    return {symbol: bars[: idx + 1] for symbol, bars in full.items()}


class FakeMarketDataAdapter(MarketDataAdapter):
    def __init__(self, bars_by_symbol: dict[str, list[OHLCVBar]]):
        self.bars_by_symbol = bars_by_symbol

    async def get_ohlcv(self, symbol: str, start: date, end: date) -> list[OHLCVBar]:
        return self.bars_by_symbol.get(symbol, [])

    async def get_latest_price(self, symbol: str) -> Decimal:
        bars = self.bars_by_symbol.get(symbol, [])
        if not bars:
            raise ValueError(f"no synthetic data for symbol '{symbol}'")
        return bars[-1].close
