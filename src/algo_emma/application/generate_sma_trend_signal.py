from algo_emma.domain.models import Bar, SmaTrendSignal
from algo_emma.ports import ForReadingUniverseRanking


class GenerateSmaTrendSignal:
    """Generate an SMA trend decision, checking the daily universe for entries."""

    def __init__(self, universe_ranking_reader: ForReadingUniverseRanking) -> None:
        self._universe_ranking_reader = universe_ranking_reader

    def execute(self, current_bar: Bar, moving_average: float, has_open_position: bool) -> SmaTrendSignal:
        is_asset_ranked = False
        if not has_open_position:
            rankings = self._universe_ranking_reader.get_for_date(current_bar.date)
            is_asset_ranked = any(asset.symbol == current_bar.symbol for asset in rankings)

        return SmaTrendSignal.from_bar(
            bar=current_bar,
            moving_average=moving_average,
            is_asset_ranked=is_asset_ranked,
            has_open_position=has_open_position,
        )
