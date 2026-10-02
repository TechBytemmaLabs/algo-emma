from argparse import ArgumentParser
from collections.abc import Sequence
from datetime import date, timedelta
from pathlib import Path

from algo_emma.adapters.crypto_data_download.cdd_market_data_reader import CDDMarketDataReader
from algo_emma.adapters.universe_ranking.csv_universe_ranking_writer import CsvUniverseRankingWriter
from algo_emma.application.generate_daily_universe_ranking import GenerateDailyUniverseRanking
from algo_emma.domain.universe_ranker import UniverseRankingService

ROOT = Path(__file__).resolve().parents[4]
DEFAULT_RAW_DATA_DIR = ROOT / "data" / "raw" / "binance_spot_daily"
DEFAULT_OUTPUT_DIR = ROOT / "data" / "processed"


def main(argv: Sequence[str] | None = None) -> int:
    args_parser = ArgumentParser(description="Build the universe ranking of the given day")

    args_parser.add_argument("--start-date", type=date.fromisoformat, default=date.today())
    args_parser.add_argument("--end-date", type=date.fromisoformat, default=date.today())
    args_parser.add_argument("--raw-data-directory", type=Path, default=DEFAULT_RAW_DATA_DIR)
    args_parser.add_argument("--output-file", type=Path, default=None)
    args_parser.add_argument("--overwrite-ranking", action="store_true", default=False)
    args = args_parser.parse_args(argv)

    if args.start_date > args.end_date:
        args_parser.error("--start-date must be on or before --end-date")

    ranking_date = args.start_date

    while ranking_date <= args.end_date:
        print(f"Generating universe ranking for {ranking_date}")
        try:
            output_path = args.output_file or Path(
                f"{DEFAULT_OUTPUT_DIR}/universe_ranking_{ranking_date.strftime('%Y%m%d')}.csv"
            )
            universe_ranker = UniverseRankingService()
            market_data_reader = CDDMarketDataReader(args.raw_data_directory)
            universe_ranking_writer = CsvUniverseRankingWriter(
                output_path=output_path, overwrite_ranking=args.overwrite_ranking
            )

            use_case = GenerateDailyUniverseRanking(
                universe_ranker=universe_ranker,
                market_data_reader=market_data_reader,
                universe_ranking_writer=universe_ranking_writer,
            )
            universe_ranking = use_case.execute(ranking_date=ranking_date)
            ranking_date += timedelta(days=1)

            print(f"Wrote {len(universe_ranking)} universe ranking rows to {output_path}")
        except Exception as e:
            print(e)
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
