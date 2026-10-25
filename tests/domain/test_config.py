import pytest

from algo_emma.domain.config import LongBreakoutEntrySignalConfig, UniverseRankingConfig


@pytest.mark.parametrize(
    ("config", "value"),
    [
        ("universe_size", 0),
        ("liquidity_period", 0),
        ("rate_of_change_period", 0),
        ("minimum_bars_after_suspicious_jump", -1),
        ("price_break_up_ratio", 1.0),
        ("price_break_down_ratio", 0.0),
        ("price_break_down_ratio", 1.0),
    ],
)
def test_universe_ranking_config_rejects_invalid_parameters(config: str, value: int) -> None:
    with pytest.raises(ValueError, match=config):
        UniverseRankingConfig(**{config: value})


@pytest.mark.parametrize(
    ("config", "value"),
    [
        ("average_true_range_period", 0),
        ("average_true_range_period", -1),
        ("average_true_range_multiplier", 0),
        ("average_true_range_multiplier", -1),
    ],
)
def test_long_breakout_entry_setup_config_rejcts_invalid_parameters(config: str, value: int) -> None:
    with pytest.raises(ValueError, match=config):
        LongBreakoutEntrySignalConfig(**{config: value})
