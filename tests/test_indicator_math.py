from app.services import indicator_math


def test_sma_basic():
    closes = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = indicator_math.sma(closes, 3)
    assert result == [None, None, 2.0, 3.0, 4.0]


def test_ema_seeds_with_sma_then_smooths():
    closes = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = indicator_math.ema(closes, 3)
    assert result[0] is None and result[1] is None
    assert result[2] == 2.0  # seeded as SMA(3) of [1,2,3]
    assert result[3] is not None and result[3] > result[2]


def test_rsi_all_gains_is_100():
    closes = [float(i) for i in range(1, 20)]  # strictly increasing
    result = indicator_math.rsi(closes, window=14)
    assert result[14] == 100.0


def test_rsi_insufficient_data_is_none():
    closes = [1.0, 2.0, 3.0]
    result = indicator_math.rsi(closes, window=14)
    assert all(v is None for v in result)


def test_crosses_above_detects_single_transition():
    a = [1.0, 1.0, 3.0]
    b = [2.0, 2.0, 2.0]
    assert indicator_math.crosses_above(a, b, 0) is None  # no prior bar
    assert indicator_math.crosses_above(a, b, 1) is False  # still below
    assert indicator_math.crosses_above(a, b, 2) is True  # transition


def test_crosses_above_none_when_missing_history():
    a = [None, 1.0, 3.0]
    b = [2.0, 2.0, 2.0]
    assert indicator_math.crosses_above(a, b, 1) is None


def test_crosses_below_detects_single_transition():
    a = [3.0, 3.0, 1.0]
    b = [2.0, 2.0, 2.0]
    assert indicator_math.crosses_below(a, b, 2) is True
    assert indicator_math.crosses_below(a, b, 1) is False
