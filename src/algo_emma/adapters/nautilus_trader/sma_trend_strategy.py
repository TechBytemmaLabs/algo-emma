from datetime import date

from nautilus_trader.accounting.accounts.base import Account as NautilusAccount  # ty: ignore[unresolved-import]
from nautilus_trader.config import StrategyConfig
from nautilus_trader.core.datetime import unix_nanos_to_dt
from nautilus_trader.indicators import SimpleMovingAverage as NautilusSimpleMovingAverage
from nautilus_trader.model import (
    Bar as NautilusBar,
    BarType as NautilusBarType,
    Currency as NautilusCurrency,
    InstrumentId,
    Venue as NautilusVenue,
)
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.trading import Strategy

from algo_emma.application.generate_sma_trend_signal import GenerateSmaTrendSignal
from algo_emma.domain.exceptions import UniverseRankingNotAvailableError
from algo_emma.domain.models import Bar, BarType, SmaTrendSignal
from algo_emma.domain.position_sizing import calculate_entry_quantity, can_open_position


class SmaTrendStrategyConfig(StrategyConfig, frozen=True):
    venue: NautilusVenue
    quote_currency: NautilusCurrency
    bar_types: tuple[NautilusBarType, ...]


class SmaTrendStrategy(Strategy):
    """
    Buy ranked assets when their daily close is above the 200-day moving average.

    After a daily bar closes, enter with a market buy if the asset is ranked
    and its close is above SMA(200). While a position is open, exit with a
    market order when the close falls below the average.

    For example, if BTC closes at 105,000 USDT and SMA(200) is 100,000 USDT,
    the strategy buys at market. If BTC later closes at 98,000 USDT while
    SMA(200) is still 100,000 USDT, the strategy closes the position.

    The comparisons are strict: a close equal to SMA(200) does not trigger
    either an entry or an exit.
    """

    def __init__(
        self,
        config: SmaTrendStrategyConfig,
        signal_generator: GenerateSmaTrendSignal,
        trading_start_date: date,
    ) -> None:
        super().__init__(config)
        self.signal_generator = signal_generator
        self.trading_start_date = trading_start_date
        self.account: NautilusAccount | None = None
        self.simple_media_averages = {}

    def on_start(self) -> None:
        self.account = self.portfolio.account(venue=self.config.venue)
        if self.account is None:
            raise RuntimeError(f"Account not found: {self.config.venue}")

        for bar_type in self.config.bar_types:
            indicator = NautilusSimpleMovingAverage(period=200)
            self.simple_media_averages[bar_type.instrument_id] = indicator
            self.register_indicator_for_bars(bar_type, indicator)
            self.subscribe_bars(bar_type)

    def on_stop(self) -> None:
        for bar_type in self.config.bar_types:
            self.cancel_all_orders(bar_type.instrument_id)
            self.close_all_positions(bar_type.instrument_id)

    def on_bar(self, bar: NautilusBar) -> None:
        instrument_id = bar.bar_type.instrument_id
        symbol = instrument_id.symbol.value
        reference_date = unix_nanos_to_dt(bar.ts_event).date()
        if reference_date < self.trading_start_date:
            return

        indicator = self.simple_media_averages[instrument_id]
        if not indicator.initialized:
            return

        current_bar = Bar(
            type=BarType.Daily,
            symbol=symbol,
            date=reference_date,
            open=bar.open.as_double(),
            high=bar.high.as_double(),
            low=bar.low.as_double(),
            close=bar.close.as_double(),
            volume=0,
            volume_usdt=0,
        )
        has_open_position = not self.portfolio.is_flat(instrument_id)
        try:
            signal = self.signal_generator.execute(
                current_bar=current_bar,
                moving_average=indicator.value,
                has_open_position=has_open_position,
            )
        except UniverseRankingNotAvailableError:
            self.log.warning(f"{symbol}({reference_date}): No universe ranking available; skipping entry")
            return

        if signal.should_exit:
            self.close_all_positions(instrument_id)
            self.log.info(f"{symbol}({reference_date}): Exit condition met; closing position")
        elif signal.should_enter and self.can_submit_entry(instrument_id, signal):
            self.submit_market_entry(instrument_id, signal, current_bar.close)

    def can_submit_entry(self, instrument_id: InstrumentId, signal: SmaTrendSignal) -> bool:
        pending_buy_orders = self.cache.orders_open(venue=self.config.venue, strategy_id=self.id, side=OrderSide.BUY)
        has_pending_buy_order = any(order.instrument_id == instrument_id for order in pending_buy_orders)
        open_positions = self.cache.positions_open(venue=self.config.venue, strategy_id=self.id)
        committed_instruments = {position.instrument_id for position in open_positions}
        committed_instruments.update(order.instrument_id for order in pending_buy_orders)
        equity = self.portfolio.equity(venue=self.config.venue).get(self.config.quote_currency)
        free_balance = self.account.balance_free(self.config.quote_currency)

        if equity is None or free_balance is None:
            self.log.warning(f"{signal.symbol}({signal.reference_date}): Skipping entry because funds are unavailable")
            return False

        return can_open_position(
            has_open_position=not self.portfolio.is_flat(instrument_id),
            has_pending_buy_order=has_pending_buy_order,
            occupied_entry_slots=len(committed_instruments),
            account_equity=equity.as_double(),
            available_quote_balance=free_balance.as_double(),
        )

    def submit_market_entry(self, instrument_id: InstrumentId, signal: SmaTrendSignal, entry_price: float) -> None:
        equity = self.portfolio.equity(venue=self.config.venue).get(self.config.quote_currency)
        instrument = self.cache.instrument(instrument_id)
        if equity is None or instrument is None:
            return

        quantity = instrument.make_qty(
            value=calculate_entry_quantity(equity=equity.as_double(), entry_price=entry_price),
            round_down=True,
        )
        order = self.order_factory.market(
            instrument_id=instrument_id,
            order_side=OrderSide.BUY,
            quantity=quantity,
            reduce_only=False,
        )
        self.submit_order(order)
        self.log.info(f"{signal.symbol}({signal.reference_date}): Submitted market buy at signal close {entry_price}: {order}")
