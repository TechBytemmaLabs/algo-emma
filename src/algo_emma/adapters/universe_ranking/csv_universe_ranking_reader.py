import csv
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from algo_emma.domain.exceptions import UniverseRankingNotAvailableError
from algo_emma.domain.models import RankedAsset
from algo_emma.ports import ForReadingUniverseRanking


class CsvUniverseRankingReader(ForReadingUniverseRanking):
    """Read one daily CSV and restore ranked assets in rank order."""

    def __init__(self, input_directory: Path) -> None:
        self._input_directory = input_directory

    def get_for_date(self, ranking_date: date) -> Sequence[RankedAsset]:
        try:
            file = f"{self._input_directory}/universe_ranking_{ranking_date:%Y%m%d}.csv"

            with open(file, newline="", encoding="utf-8") as f:
                rankings = [
                    RankedAsset(
                        date=date.fromisoformat(row["date"]),
                        symbol=row["symbol"],
                        rank=int(row["rank"]),
                        liquidity_usdt=float(row["liquidity_usdt"]),
                        rate_of_change=float(row["rate_of_change_pct"]) / 100,
                    )
                    for row in csv.DictReader(f)
                ]
        except FileNotFoundError as error:
            raise UniverseRankingNotAvailableError(ranking_date) from error

        if not rankings:
            raise UniverseRankingNotAvailableError(ranking_date)

        return sorted(rankings, key=lambda ranking: ranking.rank)
