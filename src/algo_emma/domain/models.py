from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING, NamedTuple

from algo_emma.domain.config import LongBreakoutEntrySignalConfig

if TYPE_CHECKING:
    from algo_emma.domain.indicators import AverageTrueRange


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


class RankingCandidate(NamedTuple):
    symbol: str
    liquidity: float
    rate_of_change: float


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


@dataclass(frozen=True)
class LongBreakoutEntrySignal:
    """Stop-entry details for the reference short-term momentum strategy."""

    symbol: str
    stop_price: float
    reference_date: date
    expires_at: datetime

    @classmethod
    def from_bar(
        cls,
        bar: Bar,
        average_true_range: AverageTrueRange,
        config: LongBreakoutEntrySignalConfig | None = None,
    ) -> LongBreakoutEntrySignal:
        config = config or LongBreakoutEntrySignalConfig()
        expires_at = datetime.combine(
            bar.date + timedelta(days=config.order_lifetime_days + 1),
            datetime.min.time(),
            tzinfo=UTC,
        )
        return cls(
            symbol=bar.symbol,
            reference_date=bar.date,
            expires_at=expires_at,
            stop_price=bar.high + config.average_true_range_multiplier * average_true_range,
        )


@dataclass(frozen=True)
class SmaTrendSignal:
    """Entry or exit decision based on a daily close and its 200-day average."""

    symbol: str
    reference_date: date
    should_enter: bool
    should_exit: bool

    @classmethod
    def from_bar(
        cls,
        bar: Bar,
        moving_average: float,
        is_asset_ranked: bool,
        has_open_position: bool,
    ) -> SmaTrendSignal:
        return cls(
            symbol=bar.symbol,
            reference_date=bar.date,
            should_enter=is_asset_ranked and not has_open_position and bar.close > moving_average,
            should_exit=has_open_position and bar.close < moving_average,
        )
