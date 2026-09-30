from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from app.models.backtest_run import BacktestRun, BacktestStatus
from app.schemas.strategy_spec import StrategySpec
from app.services import position_sizing
from app.services.market_data import registry
from app.services.market_data.base import OHLCVBar
from app.services.strategy_compiler_service import compile_strategy

LOOKBACK_BUFFER_DAYS = 400
MAX_DRAWDOWN_REJECT_PCT = Decimal("50")
MIN_BACKTEST_TRADES = 1


async def run_backtest(
    strategy_id: str,
    spec: StrategySpec,
    start_date: date,
    end_date: date,
    starting_cash: Decimal,
) -> BacktestRun:
    run = BacktestRun(
        strategy_id=strategy_id,
        status=BacktestStatus.RUNNING,
        start_date=start_date,
        end_date=end_date,
        starting_cash=starting_cash,
    )

    try:
        compiled = compile_strategy(spec)
        adapter = registry.get_adapter(spec.asset_class)
        buffer_start = start_date - timedelta(days=LOOKBACK_BUFFER_DAYS)

        raw_bars: dict[str, list[OHLCVBar]] = {}
        for symbol in compiled.required_symbols:
            raw_bars[symbol] = await adapter.get_ohlcv(symbol, buffer_start, end_date)

        primary_symbol = spec.universe[0]
        primary_bars = raw_bars[primary_symbol]
        if not primary_bars:
            raise ValueError(f"No historical data returned for '{primary_symbol}'")

        aligned_bars = align_bars(primary_bars, raw_bars)
        ctx = compiled.prepare(aligned_bars)

        metrics, equity_curve, trades = _simulate(
            compiled, ctx, primary_bars, primary_symbol, start_date, starting_cash, spec.risk
        )

        run.status = BacktestStatus.COMPLETED
        run.metrics = metrics
        run.equity_curve = equity_curve
        run.trades = trades
        run.completed_at = datetime.now(timezone.utc)
    except Exception as e:  # noqa: BLE001 - a failed backtest must never 500 the API
        run.status = BacktestStatus.FAILED
        run.error_message = str(e)[:1000]
        run.completed_at = datetime.now(timezone.utc)

    return run


def align_bars(
    primary_bars: list[OHLCVBar], raw_bars: dict[str, list[OHLCVBar]]
) -> dict[str, list[OHLCVBar]]:
    primary_dates = [b.date for b in primary_bars]
    aligned: dict[str, list[OHLCVBar]] = {}
    for symbol, bars in raw_bars.items():
        by_date = {b.date: b for b in bars}
        last_known: OHLCVBar | None = None
        series: list[OHLCVBar] = []
        for d in primary_dates:
            bar = by_date.get(d)
            if bar is not None:
                last_known = bar
                series.append(bar)
            elif last_known is not None:
                series.append(last_known)
            else:
                series.append(
                    OHLCVBar(date=d, open=Decimal(0), high=Decimal(0), low=Decimal(0), close=Decimal(0), volume=0)
                )
        aligned[symbol] = series
    return aligned


def _simulate(
    compiled, ctx, primary_bars: list[OHLCVBar], primary_symbol: str, start_date: date, starting_cash: Decimal, risk
) -> tuple[dict, list[dict], list[dict]]:
    cash = starting_cash
    shares = Decimal("0")
    entry_price: Decimal | None = None
    entry_date: date | None = None

    equity_curve: list[dict] = []
    trades: list[dict] = []
    daily_returns: list[float] = []
    prev_equity: Decimal | None = None

    start_index = next((i for i, b in enumerate(primary_bars) if b.date >= start_date), len(primary_bars))

    for i in range(len(primary_bars)):
        bar = primary_bars[i]
        price = bar.close

        if shares > 0:
            stop_price = None
            take_price = None
            if risk.stop_loss_pct:
                stop_price = entry_price * (1 - risk.stop_loss_pct / Decimal("100"))
            if risk.take_profit_pct:
                take_price = entry_price * (1 + risk.take_profit_pct / Decimal("100"))

            exit_reason = None
            exit_price = price
            if stop_price is not None and bar.low <= stop_price:
                exit_reason, exit_price = "stop_loss", stop_price
            elif take_price is not None and bar.high >= take_price:
                exit_reason, exit_price = "take_profit", take_price
            elif i >= start_index and compiled.evaluate_exit(ctx, i):
                exit_reason, exit_price = "exit_rule", price

            if exit_reason:
                proceeds = shares * exit_price
                cash += proceeds
                return_pct = float((exit_price - entry_price) / entry_price * 100)
                trades.append(
                    {
                        "entry_date": entry_date.isoformat(),
                        "entry_price": float(entry_price),
                        "exit_date": bar.date.isoformat(),
                        "exit_price": float(exit_price),
                        "shares": float(shares),
                        "return_pct": return_pct,
                        "exit_reason": exit_reason,
                    }
                )
                shares = Decimal("0")
                entry_price = None
                entry_date = None

        elif i >= start_index and compiled.evaluate_entry(ctx, i):
            equity = cash
            order_shares = position_sizing.size_position(equity, price, risk)
            if order_shares > 0:
                cost = order_shares * price
                if cost <= cash:
                    cash -= cost
                    shares = order_shares
                    entry_price = price
                    entry_date = bar.date

        equity = cash + shares * price
        if i >= start_index:
            if prev_equity is not None and prev_equity > 0:
                daily_returns.append(float((equity - prev_equity) / prev_equity))
            equity_curve.append({"date": bar.date.isoformat(), "equity": float(equity)})
            prev_equity = equity

    if shares > 0:
        final_bar = primary_bars[-1]
        proceeds = shares * final_bar.close
        cash += proceeds
        return_pct = float((final_bar.close - entry_price) / entry_price * 100)
        trades.append(
            {
                "entry_date": entry_date.isoformat(),
                "entry_price": float(entry_price),
                "exit_date": final_bar.date.isoformat(),
                "exit_price": float(final_bar.close),
                "shares": float(shares),
                "return_pct": return_pct,
                "exit_reason": "backtest_end",
            }
        )
        if equity_curve:
            equity_curve[-1]["equity"] = float(cash)

    metrics = _compute_metrics(starting_cash, cash, equity_curve, daily_returns, trades)
    return metrics, equity_curve, trades


def _compute_metrics(
    starting_cash: Decimal, final_cash: Decimal, equity_curve: list[dict], daily_returns: list[float], trades: list[dict]
) -> dict:
    total_return_pct = float((final_cash - starting_cash) / starting_cash * 100) if starting_cash else 0.0

    peak = float(starting_cash)
    max_drawdown_pct = 0.0
    for point in equity_curve:
        peak = max(peak, point["equity"])
        if peak > 0:
            drawdown = (peak - point["equity"]) / peak * 100
            max_drawdown_pct = max(max_drawdown_pct, drawdown)

    if len(daily_returns) >= 2:
        mean_ret = sum(daily_returns) / len(daily_returns)
        variance = sum((r - mean_ret) ** 2 for r in daily_returns) / len(daily_returns)
        stdev = variance ** 0.5
        sharpe_ratio = (mean_ret / stdev * (252 ** 0.5)) if stdev > 0 else 0.0
    else:
        sharpe_ratio = 0.0

    num_trades = len(trades)
    winners = [t for t in trades if t["return_pct"] > 0]
    win_rate = (len(winners) / num_trades * 100) if num_trades else 0.0
    avg_trade_return_pct = (sum(t["return_pct"] for t in trades) / num_trades) if num_trades else 0.0

    return {
        "total_return_pct": total_return_pct,
        "max_drawdown_pct": max_drawdown_pct,
        "sharpe_ratio": sharpe_ratio,
        "win_rate": win_rate,
        "num_trades": num_trades,
        "avg_trade_return_pct": avg_trade_return_pct,
    }
