from argparse import ArgumentParser
from collections.abc import Sequence
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path

from nautilus_trader.backtest.config import BacktestEngineConfig
from nautilus_trader.backtest.models import MakerTakerFeeModel
from nautilus_trader.backtest.node import BacktestEngine
from nautilus_trader.model import BarType, Currency, Money, Venue
from nautilus_trader.model.enums import AccountType, OmsType
from nautilus_trader.persistence.catalog import ParquetDataCatalog

from algo_emma.adapters.nautilus_trader.sma_trend_strategy import SmaTrendStrategy, SmaTrendStrategyConfig
from algo_emma.adapters.universe_ranking.csv_universe_ranking_reader import CsvUniverseRankingReader
from algo_emma.application.generate_sma_trend_signal import GenerateSmaTrendSignal

ROOT = Path(__file__).resolve().parents[4]
DEFAULT_CATALOG_DIR = ROOT / "data" / "processed" / "catalog"
DEFAULT_RANKING_DIR = ROOT / "data" / "processed" / "universe_ranking"
DEFAULT_START_DATE = date(2023, 1, 1)
DEFAULT_END_DATE = date(2025, 1, 1)
SMA_WARMUP_DAYS = 201


def main(argv: Sequence[str] | None = None) -> int:
    parser = ArgumentParser(description="Run the SMA(200) trend strategy backtest")
    parser.add_argument("--catalog-directory", type=Path, default=DEFAULT_CATALOG_DIR)
    parser.add_argument("--ranking-directory", type=Path, default=DEFAULT_RANKING_DIR)
    parser.add_argument("--start-date", type=date.fromisoformat, default=DEFAULT_START_DATE)
    parser.add_argument("--end-date", type=date.fromisoformat, default=DEFAULT_END_DATE)
    args = parser.parse_args(argv)

    if args.end_date < args.start_date:
        parser.error("--end-date must be on or after --start-date")

    engine = BacktestEngine(config=BacktestEngineConfig())
    try:
        trading_start_date = args.start_date + timedelta(days=1)
        start = datetime.combine(trading_start_date - timedelta(days=SMA_WARMUP_DAYS), time.min, tzinfo=UTC)
        end = datetime.combine(args.end_date + timedelta(days=1), time.min, tzinfo=UTC)
        catalog = ParquetDataCatalog(path=args.catalog_directory)
        instruments = catalog.instruments()
        if not instruments:
            raise RuntimeError(f"No instruments found in catalog: {args.catalog_directory}")

        bar_types = [BarType.from_str(f"{instrument.id}-1-DAY-LAST-EXTERNAL") for instrument in instruments]
        bars = catalog.bars(bar_types=[str(bar_type) for bar_type in bar_types], start=start, end=end)
        if not bars:
            raise RuntimeError(f"No bars found in catalog: {args.catalog_directory}")

        venue = Venue("BINANCE")
        quote_currency = Currency.from_str("USDT")
        engine.add_venue(
            venue=venue,
            oms_type=OmsType.NETTING,
            account_type=AccountType.CASH,
            base_currency=None,
            starting_balances=[Money(100_000.0, quote_currency)],
            fee_model=MakerTakerFeeModel(),
        )
        for instrument in instruments:
            engine.add_instrument(instrument)
        engine.add_data(bars)

        strategy = SmaTrendStrategy(
            config=SmaTrendStrategyConfig(
                bar_types=tuple(bar_types), venue=venue, quote_currency=quote_currency
            ),
            signal_generator=GenerateSmaTrendSignal(
                universe_ranking_reader=CsvUniverseRankingReader(input_directory=args.ranking_directory)
            ),
            trading_start_date=trading_start_date,
        )
        engine.add_strategy(strategy)
        engine.run()
    except Exception as error:
        print(error)
        return 1
    finally:
        engine.dispose()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
