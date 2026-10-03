from datetime import date

import pytest

from algo_emma.domain.indicators import AverageTrueRange, RateOfChange, SimpleMovingAverage, TrueRange


def test_sma_returns_average_of_last_values() -> None:
    assert SimpleMovingAverage([1.0, 2.0, 3.0, 4.0], period=2) == 3.5


def test_roc_compares_current_close_with_close_n_periods_ago() -> None:
    assert RateOfChange([1.0, 2.0, 3.0], period=2) == pytest.approx(2.0)


def test_tr_includes_largest_gap_or_intraday_move() -> None:
    assert TrueRange(12.0, 11.0, 9.0) == 3.0


def test_atr_averages_last_true_ranges(daily_bar) -> None:
    bars = [
        daily_bar(date(2024, 1, 1), open=12, close=8, high=14, low=7),
        daily_bar(date(2024, 1, 2), open=8, close=10, high=11, low=7),
        daily_bar(date(2024, 1, 3), open=10, close=13, high=14, low=9),
        daily_bar(date(2024, 1, 4), open=13, close=15, high=15, low=12),
    ]

    assert AverageTrueRange(bars, period=3) == pytest.approx(4.0)


@pytest.mark.parametrize(
    ("indicator", "period"),
    [
        (SimpleMovingAverage, 0),
        (SimpleMovingAverage, -1),
        (RateOfChange, 0),
        (RateOfChange, -1),
        (AverageTrueRange, 0),
        (AverageTrueRange, -1),
    ],
)
def test_indicators_reject_invalid_parameters(indicator, period, daily_bar) -> None:
    bars = [
        daily_bar(date(2024, 1, 1), open=12, close=8, high=14, low=7),
        daily_bar(date(2024, 1, 2), open=8, close=10, high=11, low=7),
        daily_bar(date(2024, 1, 3), open=10, close=13, high=14, low=9),
        daily_bar(date(2024, 1, 4), open=13, close=15, high=15, low=12),
    ]

    with pytest.raises(ValueError):
        indicator(bars, period)
