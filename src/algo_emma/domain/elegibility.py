from __future__ import annotations

from collections.abc import Sequence

from .models import Bar


def _find_price_breaks(closes: Sequence[float], upward_jump_ratio: float, downward_jump_ratio: float) -> list[int]:
    """
    Find close-to-close jumps that may indicate a token redenomination.

    The returned indexes identify suspicious discontinuities so eligibility can
    require a recovery period before considering the asset.
    """
    if upward_jump_ratio <= 1:
        raise ValueError("upward_jump_ratio must be greater than 1")
    if not 0 < downward_jump_ratio < 1:
        raise ValueError("downward_jump_ratio must be between 0 and 1")

    breaks = []
    for index in range(1, len(closes)):
        ratio = closes[index] / closes[index - 1]
        if ratio > upward_jump_ratio or ratio < downward_jump_ratio:
            breaks.append(index)
    return breaks


def is_eligible_asset(
    bars: list[Bar],
    min_history_bars: int,
    min_bars_after_suspicious_jump: int,
    upward_jump_ratio: float,
    downward_jump_ratio: float,
) -> bool:
    """
    Check that history is long enough and has recovered after a jump.

    An asset is eligible only when it has the required history and enough bars
    after its latest suspicious price break.
    """
    if len(bars) < min_history_bars:
        return False

    breaks = _find_price_breaks(
        [bar.close for bar in bars],
        upward_jump_ratio=upward_jump_ratio,
        downward_jump_ratio=downward_jump_ratio,
    )
    return not (breaks and len(bars) - breaks[-1] <= min_bars_after_suspicious_jump)
