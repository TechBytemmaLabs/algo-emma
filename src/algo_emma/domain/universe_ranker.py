from collections.abc import Sequence
from datetime import date
from typing import Protocol

from algo_emma.domain.config import UniverseRankingConfig
from algo_emma.domain.elegibility import is_eligible_asset
from algo_emma.domain.indicators import RateOfChange, SimpleMovingAverage
from algo_emma.domain.models import Bar, RankedAsset, RankingCandidate


class UniverseRanker(Protocol):
    """Builds a daily ranking from eligible assets and available market data.

    Implementations evaluate historical data through `ranking_date`, discard
    ineligible assets, and select the most liquid ones. They calculate liquidity
    and rate of change, keep the configured number of assets with the highest
    liquidity, and assign consecutive ranks starting at 1.
    """

    def rank_assets(self, ranking_date: date, market_data: Sequence[Bar]) -> Sequence[RankedAsset]: ...


class UniverseRankingService(UniverseRanker):
    def __init__(self, config: UniverseRankingConfig | None = None) -> None:
        self._config = config or UniverseRankingConfig()

    def rank_assets(self, ranking_date: date, market_data: Sequence[Bar]) -> Sequence[RankedAsset]:
        ranking_candidates: list[RankingCandidate] = []

        for symbol, bars in self.group_bars_by_symbol(market_data).items():
            if not is_eligible_asset(
                bars=bars,
                min_history_bars=self._config.minimum_history_bars,
                min_bars_after_suspicious_jump=self._config.minimum_bars_after_suspicious_jump,
                upward_jump_ratio=self._config.price_break_up_ratio,
                downward_jump_ratio=self._config.price_break_down_ratio,
            ):
                continue

            volumes = [bar.volume_usdt for bar in bars]
            closes = [bar.close for bar in bars]

            liquidity = SimpleMovingAverage(values=volumes, period=self._config.liquidity_period)
            rate_of_change = RateOfChange(closes=closes, period=self._config.rate_of_change_period)

            ranking_candidates.append(RankingCandidate(symbol, liquidity, rate_of_change))

        ranking_candidates = sorted(ranking_candidates, key=lambda candidate: (-candidate.liquidity, candidate.symbol))
        ranking_candidates = ranking_candidates[: self._config.universe_size]

        return [
            RankedAsset(
                rank=rank,
                date=ranking_date,
                symbol=symbol,
                rate_of_change=rate_of_change,
                liquidity_usdt=liquidity,
            )
            for rank, (symbol, liquidity, rate_of_change) in enumerate(ranking_candidates, start=1)
        ]

    @staticmethod
    def group_bars_by_symbol(bars: Sequence[Bar]) -> dict[str, list[Bar]]:
        bars_by_symbol: dict[str, list[Bar]] = {}

        for bar in bars:
            bars_by_symbol.setdefault(bar.symbol, []).append(bar)

        return bars_by_symbol
