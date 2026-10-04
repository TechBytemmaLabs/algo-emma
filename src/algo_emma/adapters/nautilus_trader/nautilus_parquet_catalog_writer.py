from collections.abc import Sequence
from datetime import UTC, datetime, time
from decimal import Decimal
from pathlib import Path

from nautilus_trader.model import Bar as NautilusBar, BarType, Currency, InstrumentId, Price, Quantity, Symbol
from nautilus_trader.model.instruments import CurrencyPair
from nautilus_trader.persistence.catalog import ParquetDataCatalog

from algo_emma.domain.market_data import MarketData
from algo_emma.domain.models import Bar
from algo_emma.ports import ForPersistingBacktestData


class NautilusParquetCatalogWriter(ForPersistingBacktestData):
    def __init__(self, path: Path) -> None:
        self._catalog = ParquetDataCatalog(path=path)

    def store_data(self, market_data: Sequence[Bar]) -> None:
        instruments = []
        nautilus_bars = []

        for symbol, bars in MarketData.group_by_symbol(market_data).items():
            if not symbol.endswith("USDT"):
                raise RuntimeError(f"Unsupported symbol: {symbol}")

            base_symbol = symbol.removesuffix("USDT")
            instrument = CurrencyPair(
                instrument_id=InstrumentId.from_str(f"{symbol}.BINANCE"),
                raw_symbol=Symbol(symbol),
                base_currency=Currency.from_str(base_symbol),
                quote_currency=Currency.from_str("USDT"),
                price_precision=8,
                size_precision=8,
                price_increment=Price.from_str("0.00000001"),
                size_increment=Quantity.from_str("0.00000001"),
                ts_event=0,
                ts_init=0,
                lot_size=Quantity.from_int(1),
                margin_init=Decimal("0"),
                margin_maint=Decimal("0"),
            )
            instruments.append(instrument)

            bar_type = BarType.from_str(f"{instrument.id}-1-DAY-LAST-EXTERNAL")
            bars = sorted(bars, key=lambda bar: bar.date)

            for bar in bars:
                timestamp = int(datetime.combine(bar.date, time.min, tzinfo=UTC).timestamp() * 1_000_000_000)
                try:
                    volume = Quantity.from_decimal(Decimal(f"{bar.volume:.8f}"))
                except ValueError as e:
                    if "exceeds max" not in str(e):
                        raise
                    volume = Quantity.from_decimal(Decimal(f"{0:.8f}"))

                nautilus_bar = NautilusBar(
                    bar_type=bar_type,
                    open=Price.from_decimal(Decimal(f"{bar.open:.8f}")),
                    close=Price.from_decimal(Decimal(f"{bar.close:.8f}")),
                    high=Price.from_decimal(Decimal(f"{bar.high:.8f}")),
                    low=Price.from_decimal(Decimal(f"{bar.low:.8f}")),
                    volume=volume,
                    ts_event=timestamp,
                    ts_init=timestamp + 86_400_000_000_000,
                )
                nautilus_bars.append(nautilus_bar)

        if not instruments:
            return

        self._catalog.write_data(instruments)
        self._catalog.write_data(nautilus_bars)
