from __future__ import annotations

import csv
from collections.abc import Sequence
from pathlib import Path

from algo_emma.domain.models import RankedAsset
from algo_emma.ports import ForPersistingUniverseRanking


class CsvUniverseRankingWriter(ForPersistingUniverseRanking):
    """Write ranked assets to an auditable CSV file.

    The adapter converts domain ranking results into a stable tabular format
    that can be inspected or consumed by later analysis.
    """

    def __init__(self, output_path: Path, overwrite_ranking: bool = False) -> None:
        self._output_path = output_path
        self.overwrite_ranking = overwrite_ranking

    def store_ranking(self, universe_ranking: Sequence[RankedAsset]) -> None:
        mode = "w" if self.overwrite_ranking else "x"

        self._output_path.parent.mkdir(parents=True, exist_ok=True)

        with self._output_path.open(mode=mode, newline="", encoding="utf-8") as file:

            writer = csv.writer(file)
            writer.writerow(
                ["date", "symbol", "rank", "liquidity_usdt", "rate_of_change_pct"]
            )
            writer.writerows(
                [
                    ranked_asset.date.isoformat(),
                    ranked_asset.symbol,
                    ranked_asset.rank,
                    f"{ranked_asset.liquidity_usdt:.2f}",
                    f"{ranked_asset.rate_of_change * 100:.2f}",
                ]
                for ranked_asset in universe_ranking
            )
