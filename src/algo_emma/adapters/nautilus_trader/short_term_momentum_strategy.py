from datetime import timedelta
from functools import partial

from nautilus_trader.accounting.accounts.base import Account as NautilusAccount  # ty: ignore[unresolved-import]
from nautilus_trader.common.events import TimeEvent
from nautilus_trader.config import StrategyConfig
from nautilus_trader.core.datetime import unix_nanos_to_dt
from nautilus_trader.indicators import AverageTrueRange as NautilusAverageTrueRange
from nautilus_trader.model import (
    Bar as NautilusBar,
    BarType as NautilusBarType,
    Currency as NautilusCurrency,
    PositionId,
    Venue as NautilusVenue,
)
from nautilus_trader.model.enums import OrderSide, TimeInForce, TriggerType
from nautilus_trader.model.events import PositionOpened as NautilusPositionOpened
from nautilus_trader.trading import Strategy

from algo_emma.application.generate_long_breakout_entry_signal import GenerateLongBreakoutEntrySignal
from algo_emma.domain.exceptions import UniverseRankingNotAvailableError
from algo_emma.domain.indicators import AverageTrueRange
from algo_emma.domain.models import Bar, BarType, LongBreakoutEntrySignal
from algo_emma.domain.position_sizing import calculate_entry_quantity, can_open_position


class ShortTermMomentumStrategyConfig(StrategyConfig, frozen=True):
    venue: NautilusVenue
    quote_currency: NautilusCurrency
    bar_types: tuple[NautilusBarType, ...]


class ShortTermMomentumStrategy(Strategy):
    """
    Buy when price breaks above the last daily high, with an ATR buffer.

    When a daily bar closes, check that the asset is in the selected universe
    and place a buy stop at its high + 0.75 * ATR(3). Crypto trades around the
    clock, so the order goes out immediately; there is no wait for an open.

    For example, if BTC's daily high is 60,000 USDT and ATR(3) is 2,000 USDT:
        Stop price = 60,000 + 0.75 * 2,000 = 61,500 USDT.
        At 60,500, the order is still pending. We have not bought BTC.
        At 61,500, the stop triggers a market buy. The fill price may differ.
        Once it fills, we hold BTC and the holding period starts.

    If the entry expires before it fills, we cancel it without opening a
    position. Once we hold BTC, cancelling an order does not sell it; we
    need to sell the full position to close it.

    The intended exit is two days after the buy fills. This time stop still
    needs to be implemented.
    """

    def __init__(
        self,
        config: ShortTermMomentumStrategyConfig,
        entry_signal_generator: GenerateLongBreakoutEntrySignal,
    ) -> None:
        super().__init__(config)

        self.average_true_ranges = {}
        self.account: NautilusAccount | None = None
        self.entry_signal_generator: GenerateLongBreakoutEntrySignal = entry_signal_generator

    def on_start(self) -> None:
        self.account = self.portfolio.account(venue=self.config.venue)
        if not self.account:
            raise RuntimeError(f"Account not found: {self.config.venue}")

        for bar_type in self.config.bar_types:
            indicator = NautilusAverageTrueRange(period=3)
            self.average_true_ranges[bar_type.instrument_id] = indicator
            self.register_indicator_for_bars(bar_type, indicator)
            self.subscribe_bars(bar_type)

    def on_stop(self) -> None:
        for bar_type in self.config.bar_types:
            self.cancel_all_orders(bar_type.instrument_id)
            self.close_all_positions(bar_type.instrument_id)

    def on_bar(self, bar: NautilusBar) -> None:
        instrument_id = bar.bar_type.instrument_id
        symbol = bar.bar_type.instrument_id.symbol.value
        date = unix_nanos_to_dt(bar.ts_event).date()

        if not self.is_atr_indicator_ready(bar):
            return

        atr_indicator = self.average_true_ranges[instrument_id]
        average_true_range = AverageTrueRange.from_value(atr_indicator.value)
        current_bar = Bar(
            type=BarType.Daily,
            symbol=symbol,
            date=date,
            open=bar.open.as_double(),
            close=bar.close.as_double(),
            high=bar.high.as_double(),
            low=bar.low.as_double(),
            volume=0,
            volume_usdt=0,
        )

        self.log.info(f"{symbol}({date}): Processing daily bar {bar}")

        try:
            entry_signal = self.entry_signal_generator.execute(current_bar, average_true_range)
        except UniverseRankingNotAvailableError:
            self.log.warning(f"{symbol}({date}): No universe ranking available; skipping entries for this date")
            return

        if not entry_signal:
            return

        if self.can_submit_entry_order(instrument_id, entry_signal):
            self.submit_long_entry_order(instrument_id, entry_signal)

    def on_position_opened(self, event: NautilusPositionOpened) -> None:
        self.clock.set_time_alert(
            name=f"close_position_{event.position_id}",
            alert_time=unix_nanos_to_dt(event.ts_event) + timedelta(days=2),
            callback=partial(self.submit_long_exit_order, position_id=event.position_id),
        )

    def is_atr_indicator_ready(self, bar) -> bool:
        atr_indicator = self.average_true_ranges[bar.bar_type.instrument_id]
        symbol = bar.bar_type.instrument_id.symbol.value
        date = unix_nanos_to_dt(bar.ts_event).date()

        if not atr_indicator.initialized:
            self.log.warning(f"{symbol}({date}): ATR indicator is warming up")
            return False

        self.log.info(f"{symbol}({date}): ATR value {atr_indicator.value}")
        return True

    def can_submit_entry_order(self, instrument_id: str, entry_signal: LongBreakoutEntrySignal) -> bool:
        symbol = entry_signal.symbol
        date = entry_signal.reference_date
        pending_buy_orders = self.cache.orders_open(venue=self.config.venue, strategy_id=self.id, side=OrderSide.BUY)
        has_pending_buy_order = any(order.instrument_id == instrument_id for order in pending_buy_orders)
        open_positions = self.cache.positions_open(venue=self.config.venue, strategy_id=self.id)
        committed_assets = {position.instrument_id for position in open_positions}
        committed_assets.update(order.instrument_id for order in pending_buy_orders)

        equity = self.portfolio.equity(venue=self.config.venue).get(self.config.quote_currency)
        free_balance = self.account.balance_free(self.config.quote_currency)

        if equity is None or free_balance is None:
            self.log.warning(f"{symbol}({date}): Skipping entry because {equity} or {free_balance} in unavailable")
            return False

        can_open = can_open_position(
            has_open_position=not self.portfolio.is_flat(instrument_id),
            has_pending_buy_order=has_pending_buy_order,
            occupied_entry_slots=len(committed_assets),
            account_equity=equity.as_double(),
            available_quote_balance=free_balance.as_double(),
        )
        if not can_open:
            self.log.info(f"{symbol}({date}): Skipping entry because entry requirements are not met")

        return can_open

    def submit_long_entry_order(self, instrument_id: str, entry_signal: LongBreakoutEntrySignal) -> None:
        equity = self.portfolio.equity(venue=self.config.venue).get(self.config.quote_currency)
        instrument = self.cache.instrument(instrument_id)
        trigger_price = instrument.make_price(value=entry_signal.stop_price)
        raw_quantity = calculate_entry_quantity(equity=equity.as_double(), entry_price=entry_signal.stop_price)
        quantity = instrument.make_qty(value=raw_quantity, round_down=True)

        order = self.order_factory.stop_market(
            instrument_id=instrument_id,
            order_side=OrderSide.BUY,
            quantity=quantity,
            trigger_price=trigger_price,
            trigger_type=TriggerType.LAST_PRICE,
            time_in_force=TimeInForce.GTD,
            expire_time=entry_signal.expires_at,
            reduce_only=False,
        )

        self.submit_order(order)

        self.log.info(f"{entry_signal.symbol}({entry_signal.reference_date}): Submitted buy stop-market order {order}")

    def submit_long_exit_order(self, event: TimeEvent, position_id: PositionId) -> None:
        position = self.cache.position(position_id)
        if not position or position.is_closed:
            return

        symbol = position.instrument_id.symbol.value
        date = unix_nanos_to_dt(event.ts_event).date()

        self.close_position(position)

        self.log.info(f"{symbol}({date}): Closing position {position} after 2 days")
