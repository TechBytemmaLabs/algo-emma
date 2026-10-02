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
