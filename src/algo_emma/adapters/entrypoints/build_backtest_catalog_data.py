from __future__ import annotations

from argparse import ArgumentParser
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from algo_emma.adapters.crypto_data_download.cdd_market_data_reader import CDDMarketDataReader
from algo_emma.adapters.nautilus_trader.parquet_catalog_writer import ParquetCatalogWriter
from algo_emma.application.generate_market_data_catalog import GenerateBacktestDataCatalog

ROOT = Path(__file__).resolve().parents[4]
DEFAULT_RAW_DATA_DIR = ROOT / "data" / "raw" / "binance_spot_daily"
DEFAULT_CATALOG_DIR = ROOT / "data" / "processed" / "catalog"


def main(argv: Sequence[str] | None = None) -> int:
    args_parser = ArgumentParser(description="Build the universe ranking of the given day")

    args_parser.add_argument("--raw-data-directory", type=Path, default=DEFAULT_RAW_DATA_DIR)
    args_parser.add_argument("--catalog-output-directory", type=Path, default=DEFAULT_CATALOG_DIR)
    args_parser.add_argument("--start-date", type=date.fromisoformat, default=None)
    args_parser.add_argument("--end-date", type=date.fromisoformat, default=date.today())
    args = args_parser.parse_args(argv)

    if args.start_date is not None and args.start_date > args.end_date:
        args_parser.error("--start-date must be on or efore --end-date")

    try:
        print(f"Building market data catalog for {DEFAULT_RAW_DATA_DIR}")

        market_data_reader = CDDMarketDataReader(args.raw_data_directory)
        catalog_writer = ParquetCatalogWriter(args.catalog_output_directory)

        use_case = GenerateBacktestDataCatalog(
            market_data_reader=market_data_reader,
            catalog_writer=catalog_writer,
        )
        use_case.execute(
            end_date=args.end_date,
            start_date=args.start_date,
        )

        print(f"Wrote parquet catalog dato in {args.catalog_output_directory}")
    except Exception as e:
        print(e)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
