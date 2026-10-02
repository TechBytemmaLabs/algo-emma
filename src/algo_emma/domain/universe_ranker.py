from collections.abc import Sequence
from datetime import date
from typing import NamedTuple, Protocol

from algo_emma.domain.config import UniverseRankingConfig
from algo_emma.domain.elegibility import is_eligible_asset
from algo_emma.domain.indicators import RateOfChange, SimpleMovingAverage
from algo_emma.domain.models import Bar, RankedAsset


class RankingCandidate(NamedTuple):
    symbol: str
    liquidity: float
    rate_of_change: float


class UniverseRanker(Protocol):
    def rank_assets(self, ranking_date: date, market_data: Sequence[Bar]) -> Sequence[RankedAsset]:
        """
        Build the universe ranking for one day.

        Implementations must evaluate only data available on or before the
        requested date and return assets ordered by their ranking criteria.
        """


class UniverseRankingService(UniverseRanker):
    """
    Selects most liquid assets and order them by short-term price momentum.

    The service first applies the eligibility rules and liquidity cutoff, then
    orders the selected universe by the configured rate of change.
    """

    def __init__(self, config: UniverseRankingConfig | None = None) -> None:
        self._config = config or UniverseRankingConfig()

    def rank_assets(self, ranking_date: date, market_data: Sequence[Bar]) -> Sequence[RankedAsset]:
        """
        Build the ranking for one date using no data after that date.

        Each symbol is evaluated with its historical bars through `ranking_date`, which
        keeps the ranking deterministic and prevents look-ahead bias.
        """
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
