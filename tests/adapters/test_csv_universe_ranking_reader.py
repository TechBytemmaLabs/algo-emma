from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from algo_emma.adapters.universe_ranking.csv_universe_ranking_reader import CsvUniverseRankingReader
from algo_emma.adapters.universe_ranking.csv_universe_ranking_writer import CsvUniverseRankingWriter
from algo_emma.domain.exceptions import UniverseRankingNotAvailableError
from algo_emma.domain.models import RankedAsset

RANKING_DATE = date(2023, 1, 1)
HEADER = "date,symbol,rank,liquidity_usdt,rate_of_change_pct\n"


def test_reads_requested_day_and_returns_converted_assets_in_rank_order(tmp_path: Path) -> None:
    (tmp_path / "universe_ranking_20230101.csv").write_text(
        HEADER + "2023-01-01,ETHUSDT,2,500.25,5.00\n2023-01-01,BTCUSDT,1,1000.50,-1.22\n",
        encoding="utf-8",
    )
    (tmp_path / "universe_ranking_20230102.csv").write_text(
        HEADER + "2023-01-02,XRPUSDT,1,2000.00,0.00\n", encoding="utf-8"
    )
    reader = CsvUniverseRankingReader(tmp_path)

    rankings = reader.get_for_date(RANKING_DATE)
    assert [(asset.date, asset.symbol, asset.rank) for asset in rankings] == [
        (RANKING_DATE, "BTCUSDT", 1),
        (RANKING_DATE, "ETHUSDT", 2),
    ]
    assert [asset.liquidity_usdt for asset in rankings] == pytest.approx([1000.50, 500.25])
    assert [asset.rate_of_change for asset in rankings] == pytest.approx([-0.0122, 0.05])
    assert reader.get_for_date(date(2023, 1, 2)) == [
        RankedAsset(date=date(2023, 1, 2), symbol="XRPUSDT", rank=1, liquidity_usdt=2000.0, rate_of_change=0.0)
    ]


def test_missing_ranking_preserves_message_and_cause(tmp_path: Path) -> None:
    reader = CsvUniverseRankingReader(tmp_path / "missing")

    with pytest.raises(UniverseRankingNotAvailableError) as raised:
        reader.get_for_date(RANKING_DATE)

    assert str(raised.value) == "No universe ranking available for 2023-01-01"
    assert isinstance(raised.value.__cause__, FileNotFoundError)


@pytest.mark.parametrize("content", ["", HEADER])
def test_empty_ranking_is_unavailable(tmp_path: Path, content: str) -> None:
    (tmp_path / "universe_ranking_20230101.csv").write_text(content, encoding="utf-8")

    with pytest.raises(UniverseRankingNotAvailableError) as raised:
        CsvUniverseRankingReader(tmp_path).get_for_date(RANKING_DATE)

    assert str(raised.value) == "No universe ranking available for 2023-01-01"


@pytest.mark.parametrize(
    ("content", "error_type"),
    [
        ("date,symbol,rank,liquidity_usdt\n2023-01-01,BTCUSDT,1,1000\n", KeyError),
        (HEADER + "invalid,BTCUSDT,1,1000,5\n", ValueError),
        (HEADER + "2023-01-01,BTCUSDT,invalid,1000,5\n", ValueError),
        (HEADER + "2023-01-01,BTCUSDT,1,invalid,5\n", ValueError),
        (HEADER + "2023-01-01,BTCUSDT,1,1000,invalid\n", ValueError),
        (HEADER + "2023-01-01,BTCUSDT,1,1000\n", TypeError),
    ],
)
def test_invalid_rows_are_not_skipped(tmp_path: Path, content: str, error_type: type[Exception]) -> None:
    (tmp_path / "universe_ranking_20230101.csv").write_text(content, encoding="utf-8")

    with pytest.raises(error_type):
        CsvUniverseRankingReader(tmp_path).get_for_date(RANKING_DATE)


@pytest.mark.parametrize("error_type", [PermissionError, IsADirectoryError])
def test_access_errors_propagate(tmp_path: Path, error_type: type[OSError]) -> None:
    with patch.object(Path, "open", side_effect=error_type("Cannot open ranking")), pytest.raises(error_type):
        CsvUniverseRankingReader(tmp_path).get_for_date(RANKING_DATE)


def test_reads_writer_output_with_stored_precision(tmp_path: Path) -> None:
    reader = CsvUniverseRankingReader(tmp_path)
    writer = CsvUniverseRankingWriter(tmp_path / "universe_ranking_20230101.csv")
    writer.store_ranking(
        [RankedAsset(date=RANKING_DATE, symbol="BTCUSDT", rank=1, liquidity_usdt=1234.567, rate_of_change=-0.012234)]
    )

    rankings = reader.get_for_date(RANKING_DATE)
    assert len(rankings) == 1
    asset = rankings[0]
    assert (asset.date, asset.symbol, asset.rank) == (RANKING_DATE, "BTCUSDT", 1)
    assert asset.liquidity_usdt == pytest.approx(1234.57)
    assert asset.rate_of_change == pytest.approx(-0.0122)
