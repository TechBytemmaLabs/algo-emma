from collections.abc import Sequence
from datetime import date
from typing import Protocol

from algo_emma.domain.models import Bar, RankedAsset


class ForGettingHistoricalMarketData(Protocol):
    def get_between(self, start_date: date, end_date: date) -> Sequence[Bar]:
        """
        Get all daily bars between start_date and end_date.

        The result must contain enough earlier data for the application's indicators and eligibility rules.
        """
        ...

    def get_through(self, end_date: date) -> Sequence[Bar]:
        """
        Get all daily bars through end_date, including warmup history.

        The result must contain enough earlier data for the application's
        indicators and eligibility rules.
        """
        ...


class ForPersistingUniverseRanking(Protocol):
    def store_ranking(self, universe_ranking: Sequence[RankedAsset]) -> None:
        """
        Store the daily universe ranking

        Persits somewhere the universe ranking, so it can be read later without generation at
        run time.
        """
        ...


class ForPersistingBacktestData(Protocol):
    def store_data(self, market_data: Sequence[Bar]) -> None:
        """
        Store backtest's data


        """
        ...
