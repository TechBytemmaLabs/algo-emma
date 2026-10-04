from collections.abc import Sequence

from algo_emma.domain.models import Bar


class MarketData:
    """
    Helpers to manage market data (sequence of bars)
    """

    @staticmethod
    def group_by_symbol(market_data: Sequence[Bar]) -> dict[str, list[Bar]]:
        bars_by_symbol: dict[str, list[Bar]] = {}

        for bar in market_data:
            bars_by_symbol.setdefault(bar.symbol, []).append(bar)

        return bars_by_symbol
