from datetime import date

from algo_emma.domain.elegibility import _find_price_breaks, is_eligible_asset


def test_find_price_breaks_ignores_normal_price_movements() -> None:
    price_breaks = _find_price_breaks(
        closes=[1.0, 1.1, 1.2, 1, 0.15],
        upward_jump_ratio=10.0,
        downward_jump_ratio=0.1,
    )

    assert price_breaks == []


def test_find_price_breaks_detects_a_big_price_movement() -> None:
    price_breaks = _find_price_breaks(
        closes=[1.0, 1.0, 1.0, 11.0],
        upward_jump_ratio=10.0,
        downward_jump_ratio=0.1,
    )

    assert price_breaks == [3]


def test_is_elegible_rejects_assets_without_enough_history(daily_bar) -> None:
    bars = [
        daily_bar(date(2026, 10, 1), open=10, close=12, high=12.5, low=9.5),
    ]
    assert not is_eligible_asset(
        bars=bars,
        min_history_bars=10,
        min_bars_after_suspicious_jump=10,
        upward_jump_ratio=10.0,
        downward_jump_ratio=0.1,
    )


def test_is_elegible_selects_assets_with_enough_history(daily_bar) -> None:
    bars = [
        daily_bar(date(2026, 10, 1), open=10, close=12, high=12.5, low=9.5),
        daily_bar(date(2026, 10, 1), open=12, close=13, high=13.5, low=10.5),
        daily_bar(date(2026, 10, 1), open=13, close=12, high=14.5, low=12.5),
        daily_bar(date(2026, 10, 1), open=12, close=11, high=12.5, low=11.5),
        daily_bar(date(2026, 10, 1), open=11, close=10, high=11.5, low=9.5),
        daily_bar(date(2026, 10, 1), open=10, close=12, high=12.5, low=9.5),
    ]

    assert is_eligible_asset(
        bars=bars,
        min_history_bars=3,
        min_bars_after_suspicious_jump=10,
        upward_jump_ratio=10.0,
        downward_jump_ratio=0.1,
    )
