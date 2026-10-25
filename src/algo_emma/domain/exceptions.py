from datetime import date


class UniverseRankingNotAvailableError(Exception):
    """
    The universe ranking is unavailable for the requested date.

    Raised when the daily ranking is missing or empty. Consumers must let
    this exception propagate because the strategy cannot run without a ranking.
    """

    def __init__(self, ranking_date: date) -> None:
        super().__init__(f"No universe ranking available for {ranking_date.isoformat()}")


class InvalidPositionSizingError(ValueError):
    """
    Raised when position sizing inputs are invalid
    """
