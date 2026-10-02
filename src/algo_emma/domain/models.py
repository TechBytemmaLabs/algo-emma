from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum


class BarType(Enum):
    """
    Represents different types of bar data.
    """

    Daily = "Daily"
    Weekly = "Weekly"
    Hourly = "Hourly"


@dataclass(frozen=True)
class Bar:
    """
    Immutable OHLCV data for one symbol.

    It is the technology-independent market-data model used by the ranking
    domain and by adapters that load or persist historical bars.
    """

    type: BarType
    symbol: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float
    volume_usdt: float


@dataclass(frozen=True)
class RankedAsset:
    """
    Immutable ranking result for one symbol on one trading day.

    It contains the values needed to inspect the universe selection and to
    persist the resulting ranking for later analysis.
    """

    date: date
    symbol: str
    rank: int
    rate_of_change: float
    liquidity_usdt: float
