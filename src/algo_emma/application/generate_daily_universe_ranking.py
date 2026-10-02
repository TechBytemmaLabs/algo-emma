from collections.abc import Sequence
from datetime import date, timedelta

from algo_emma.domain.models import RankedAsset
from algo_emma.domain.universe_ranker import UniverseRanker
from algo_emma.ports import ForGettingHistoricalMarketData, ForPersistingUniverseRanking


class GenerateDailyUniverseRanking:
    """
    Application use case for generating and persisting the daily universe ranking.

    It fetches the historical data, generates ranking service and store it somewhere else.
    """

    def __init__(
        self,
        market_data_reader: ForGettingHistoricalMarketData,
        universe_ranking_writer: ForPersistingUniverseRanking,
        universe_ranker: UniverseRanker,
    ) -> None:
        self._universe_ranking_writer = universe_ranking_writer
        self._market_data_reader = market_data_reader
        self._universe_ranker = universe_ranker

    def execute(self, ranking_date: date) -> Sequence[RankedAsset]:
        start_date = ranking_date - timedelta(days=31)

        market_data = self._market_data_reader.get_between(start_date=start_date, end_date=ranking_date)
        if not len(market_data):
            raise RuntimeError(f"No market data found for {start_date} and {ranking_date}")

        universe_ranking = self._universe_ranker.rank_assets(ranking_date=ranking_date, market_data=market_data)
        if not len(universe_ranking):
            raise RuntimeError(f"No ranking generated for {ranking_date}")

        self._universe_ranking_writer.store_ranking(universe_ranking=universe_ranking)

        return universe_ranking
