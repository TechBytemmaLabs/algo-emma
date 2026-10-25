from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UniverseRankingConfig:
    """
    Business parameters used to build the daily universe ranking.

    The immutable configuration keeps universe size, indicator periods, and
    eligibility thresholds explicit and validated at construction time.
    """

    universe_size: int = 20
    liquidity_period: int = 25
    rate_of_change_period: int = 10
    minimum_history_bars: int = 25
    minimum_bars_after_suspicious_jump: int = 10
    price_break_up_ratio: float = 10.0
    price_break_down_ratio: float = 0.1

    def __post_init__(self) -> None:
        if self.universe_size <= 0:
            raise ValueError("universe_size must be positive")
        if self.liquidity_period <= 0:
            raise ValueError("liquidity_period must be positive")
        if self.rate_of_change_period <= 0:
            raise ValueError("rate_of_change_period must be positive")
        if self.minimum_history_bars < max(self.liquidity_period, self.rate_of_change_period + 1):
            raise ValueError("minimum_history_bars must cover the liquidity and ROC warmup")
        if self.minimum_bars_after_suspicious_jump < 0:
            raise ValueError("minimum_bars_after_suspicious_jump cannot be negative")
        if self.price_break_up_ratio <= 1:
            raise ValueError("price_break_up_ratio must be greater than 1")
        if not 0 < self.price_break_down_ratio < 1:
            raise ValueError("price_break_down_ratio must be between 0 and 1")


@dataclass(frozen=True)
class PositionSizingConfig:
    """
    Business parameters used to calculate equal capital allocations.

    The immutable configuration defines the maximum number of open positions
    used to divide account equity into equal allocations and validates the
    limit at construction time.
    """

    max_open_positions: int = 10
    entry_cost_buffer_ratio: float = 0.01

    def __post_init__(self) -> None:
        if self.max_open_positions <= 0:
            raise ValueError("max_open_positions must be positive")
        if self.entry_cost_buffer_ratio < 0:
            raise ValueError("entry_cost_buffer_ratio cannot be negative")


@dataclass(frozen=True)
class LongBreakoutEntrySignalConfig:
    """
    Configuration for long breakout entry setups.

    The ATR period determines how volatility is measured. The multiplier scales
    that volatility into a buffer added to the completed ranking day's high to
    calculate the entry stop price.
    """

    average_true_range_multiplier: float = 0.75
    order_lifetime_days: int = 1

    def __post_init__(self) -> None:
        if self.average_true_range_multiplier <= 0:
            raise ValueError("average_true_range_multiplier must be greater than 0")

        if self.order_lifetime_days < 1:
            raise ValueError("order_lifetime_days must be greater or equals than 1")
