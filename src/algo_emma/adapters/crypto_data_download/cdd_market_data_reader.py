import csv
from collections.abc import Sequence
from datetime import UTC, date, datetime
from pathlib import Path

from algo_emma.domain.models import Bar, BarType
from algo_emma.ports import ForGettingHistoricalMarketData


class CDDMarketDataReader(ForGettingHistoricalMarketData):
    """
    Read CryptoDataDownload daily CSV files into domain bars.

    This adapter translates CDD's file format, timestamps, and symbol-specific
    volume columns into the technology-independent `DailyBar` model.
    """

    def __init__(self, raw_data_directory: Path) -> None:
        self._raw_data_directory = raw_data_directory

    def get_between(self, start_date: date, end_date: date) -> Sequence[Bar]:
        print(f"Requesting data between {start_date} and {end_date}")

        bars = [
            bar
            for path in sorted(self._raw_data_directory.glob("*_d.csv"))
            for bar in self._read_file(path)
            if start_date <= bar.date <= end_date
        ]

        return sorted(bars, key=lambda bar: (bar.date, bar.symbol))

    @staticmethod
    def _read_file(path: Path) -> Sequence[Bar]:
        with path.open(newline="", encoding="utf-8") as file:
            next(file)
            reader = csv.DictReader(file)

            volume_columns = [
                column for column in reader.fieldnames or [] if column.startswith("Volume ") and column != "Volume USDT"
            ]

            if len(volume_columns) != 1:
                raise ValueError(f"Expected one base-volume column in {path.name}, found {volume_columns}")

            return [
                Bar(
                    type=BarType.Daily,
                    symbol=row["Symbol"],
                    date=datetime.fromtimestamp(int(row["Unix"]) / 1000, tz=UTC).date(),
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=float(row[volume_columns[0]]),
                    volume_usdt=float(row["Volume USDT"]),
                )
                for row in reader
            ]
