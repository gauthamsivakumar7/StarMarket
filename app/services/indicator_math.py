"""Pure-Python indicator math on plain float lists (no pandas), matching the
manual style already used in analytics_service.py's rolling mean/volatility.
"""


def sma(closes: list[float], window: int) -> list[float | None]:
    out: list[float | None] = []
    for i in range(len(closes)):
        if i + 1 < window:
            out.append(None)
        else:
            out.append(sum(closes[i + 1 - window : i + 1]) / window)
    return out


def ema(closes: list[float], window: int) -> list[float | None]:
    out: list[float | None] = []
    alpha = 2 / (window + 1)
    prev: float | None = None
    for i, price in enumerate(closes):
        if i + 1 < window:
            out.append(None)
            continue
        if prev is None:
            prev = sum(closes[i + 1 - window : i + 1]) / window
        else:
            prev = alpha * price + (1 - alpha) * prev
        out.append(prev)
    return out


def rsi(closes: list[float], window: int = 14) -> list[float | None]:
    out: list[float | None] = [None] * len(closes)
    if len(closes) <= window:
        return out
    gains = [0.0]
    losses = [0.0]
    for i in range(1, len(closes)):
        change = closes[i] - closes[i - 1]
        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))

    avg_gain = sum(gains[1 : window + 1]) / window
    avg_loss = sum(losses[1 : window + 1]) / window
    out[window] = _rsi_from_averages(avg_gain, avg_loss)

    for i in range(window + 1, len(closes)):
        avg_gain = (avg_gain * (window - 1) + gains[i]) / window
        avg_loss = (avg_loss * (window - 1) + losses[i]) / window
        out[i] = _rsi_from_averages(avg_gain, avg_loss)
    return out


def _rsi_from_averages(avg_gain: float, avg_loss: float) -> float:
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def crosses_above(a: list[float | None], b: list[float | None], i: int) -> bool | None:
    if i < 1:
        return None
    a_now, b_now, a_prev, b_prev = a[i], b[i], a[i - 1], b[i - 1]
    if a_now is None or b_now is None or a_prev is None or b_prev is None:
        return None
    return a_prev <= b_prev and a_now > b_now


def crosses_below(a: list[float | None], b: list[float | None], i: int) -> bool | None:
    if i < 1:
        return None
    a_now, b_now, a_prev, b_prev = a[i], b[i], a[i - 1], b[i - 1]
    if a_now is None or b_now is None or a_prev is None or b_prev is None:
        return None
    return a_prev >= b_prev and a_now < b_now
