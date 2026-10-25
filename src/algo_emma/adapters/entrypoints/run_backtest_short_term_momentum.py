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

from algo_emma.adapters.nautilus_trader.short_term_momentum_strategy import (
    ShortTermMomentumStrategy,
    ShortTermMomentumStrategyConfig,
)
from algo_emma.adapters.universe_ranking.csv_universe_ranking_reader import CsvUniverseRankingReader
from algo_emma.application.generate_long_breakout_entry_signal import GenerateLongBreakoutEntrySignal

ROOT = Path(__file__).resolve().parents[4]
DEFAULT_CATALOG_DIR = ROOT / "data" / "processed" / "catalog"
DEFAULT_RANKING_DIR = ROOT / "data" / "processed" / "universe_ranking"
DEFAULT_START_DATE = datetime.fromisoformat("2023-01-01")
DEFAULT_END_DATE = datetime.fromisoformat("2025-01-01")


def main(argv: Sequence[str] | None = None) -> int:
    parser = ArgumentParser(description="Run the short-tem momentum strategy backtest")
    parser.add_argument("--catalog-directory", type=Path, default=DEFAULT_CATALOG_DIR)
    parser.add_argument("--ranking-directory", type=Path, default=DEFAULT_RANKING_DIR)
    parser.add_argument("--start-date", type=date.fromisoformat, default=DEFAULT_START_DATE)
    parser.add_argument("--end-date", type=date.fromisoformat, default=DEFAULT_END_DATE)
    args = parser.parse_args(argv)

    if (args.start_date is None) != (args.end_date is None):
        parser.error("--start-date and --end-date must be provided together")
    if args.start_date is not None and args.end_date < args.start_date:
        parser.error("--end-date must be on or after --start-date")

    engine = BacktestEngine(config=BacktestEngineConfig())

    try:
        start_date = args.start_date + timedelta(days=1)
        start_date = datetime.combine(start_date, time.min, tzinfo=UTC)
        end_date = args.end_date + timedelta(days=1)
        end_date = datetime.combine(end_date, time.min, tzinfo=UTC)

        catalog = ParquetDataCatalog(path=args.catalog_directory)
        instruments = catalog.instruments()
        if not instruments:
            raise RuntimeError(f"No instruments found in catalog: {args.catalog_directory}")

        bar_types = [
            BarType.from_str(f"{instrument.id}-1-DAY-LAST-EXTERNAL")
            for instrument in instruments
            # if instrument.symbol.value == "BTCUSDT"
        ]
        bars = catalog.bars(
            bar_types=[str(bar_type) for bar_type in bar_types],
            start=start_date,
            end=end_date,
        )

        if not bars:
            raise RuntimeError(f"No bars found in catalog: {args.catalog_directory}")

        universe_ranking_reader = CsvUniverseRankingReader(input_directory=args.ranking_directory)
        entry_signal_generator = GenerateLongBreakoutEntrySignal(universe_ranking_reader=universe_ranking_reader)

        venue = Venue("BINANCE")
        quote_currency = Currency.from_str("USDT")
        config = ShortTermMomentumStrategyConfig(bar_types=tuple(bar_types), venue=venue, quote_currency=quote_currency)
        strategy = ShortTermMomentumStrategy(config=config, entry_signal_generator=entry_signal_generator)

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
        engine.add_strategy(strategy)

        engine.run()
    except Exception as e:
        print(e)
        return 1
    finally:
        engine.dispose()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
