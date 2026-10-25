from algo_emma.domain.indicators import AverageTrueRange
from algo_emma.domain.models import Bar, LongBreakoutEntrySignal
from algo_emma.ports import ForReadingUniverseRanking


class GenerateEntrySignal:
    def __init__(
        self,
        universe_ranking_reader: ForReadingUniverseRanking,
    ):
        self._universe_ranking_reader = universe_ranking_reader

    def execute(self, current_bar: Bar, average_true_range: AverageTrueRange) -> LongBreakoutEntrySignal | None:
        universe_ranking = self._universe_ranking_reader.get_for_date(current_bar.date)

        is_asset_ranked = any(asset.symbol == current_bar.symbol for asset in universe_ranking)
        if not is_asset_ranked:
            return None

        return LongBreakoutEntrySignal.from_bar(bar=current_bar, average_true_range=average_true_range)
