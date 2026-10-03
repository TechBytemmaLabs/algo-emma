import datetime

import pytest

from algo_emma.domain.models import Bar, BarType


@pytest.fixture
def daily_bar():
    def _make_daily_bar(date: datetime.date, open: float, close: float, high: float, low: float) -> Bar:
        return Bar(
            symbol="BTCUSDT",
            type=BarType.Daily,
            date=date,
            open=open,
            close=close,
            high=high,
            low=low,
            volume=1.0,
            volume_usdt=1.0,
        )

    return _make_daily_bar
