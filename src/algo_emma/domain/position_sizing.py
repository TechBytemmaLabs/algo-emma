from algo_emma.domain.config import PositionSizingConfig
from algo_emma.domain.exceptions import InvalidPositionSizingError


def calculate_entry_quantity(equity: float, entry_price: float) -> float:
    config = PositionSizingConfig()

    if equity <= 0:
        raise InvalidPositionSizingError(f"equity must be positive, got {equity}")

    if entry_price <= 0:
        raise InvalidPositionSizingError(f"entry_price mus be positive, got {entry_price}")

    capital_per_position = equity / config.max_open_positions

    return capital_per_position / entry_price


def can_open_position(
    has_open_position: bool,
    has_pending_buy_order: bool,
    occupied_entry_slots: int,
    account_equity: float,
    available_quote_balance: float,
) -> bool:
    config = PositionSizingConfig()

    if has_open_position or has_pending_buy_order:
        return False

    if occupied_entry_slots >= config.max_open_positions:
        return False

    if account_equity <= 0:
        return False

    capital_per_position = account_equity / config.max_open_positions
    required_balance = capital_per_position * (1 + config.entry_cost_buffer_ratio)

    return available_quote_balance >= required_balance
