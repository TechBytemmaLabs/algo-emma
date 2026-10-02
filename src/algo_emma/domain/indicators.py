from __future__ import annotations

from collections.abc import Sequence
from typing import Self

from .models import Bar


class SimpleMovingAverage(float):
    """Average of the last values in a series.

    The calculation uses only the requested trailing period and raises an
    error when the input does not contain enough observations.
    """

    def __new__(cls, values: Sequence[float], period: int) -> Self:
        if period <= 0:
            raise ValueError("period must be positive")
        if len(values) < period:
            raise ValueError(f"SMA({period}) needs >= {period} values, got {len(values)}")
        return super().__new__(cls, sum(values[-period:]) / period)


class RateOfChange(float):
    """Percentage price change between now and a previous period.

    It compares the latest close with the close exactly `period` bars earlier,
    requiring one additional observation for the current value.
    """

    def __new__(cls, closes: Sequence[float], period: int) -> Self:
        if period <= 0:
            raise ValueError("period must be positive")
        if len(closes) < period + 1:
            raise ValueError(f"ROC({period}) needs >= {period + 1} values, got {len(closes)}")
        current_close = closes[-1]
        previous_close = closes[-(period + 1)]
        return super().__new__(cls, (current_close - previous_close) / previous_close)


class TrueRange(float):
    """The size of one bar's move, including a gap from the previous close.

    It captures the largest relevant movement between the current high, low,
    and the previous close.
    """

    def __new__(cls, high: float, low: float, previous_close: float) -> Self:
        value = max(high - low, abs(high - previous_close), abs(low - previous_close))
        return super().__new__(cls, value)


class AverageTrueRange(float):
    """Average true range over the last bars in a series.

    It averages the latest true ranges and requires one preceding close to
    calculate the first range in the requested window.
    """

    def __new__(cls, bars: Sequence[Bar], period: int) -> Self:
        if period <= 0:
            raise ValueError("period must be positive")
        if len(bars) < period + 1:
            raise ValueError(f"ATR({period}) needs >= {period + 1} bars, got {len(bars)}")
        true_ranges = [
            TrueRange(bars[i].high, bars[i].low, bars[i - 1].close) for i in range(len(bars) - period, len(bars))
        ]
        return super().__new__(cls, sum(true_ranges) / period)
