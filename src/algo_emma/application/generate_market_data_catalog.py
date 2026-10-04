from datetime import date

from algo_emma.ports import ForGettingHistoricalMarketData, ForPersistingBacktestData


class GenerateBacktestDataCatalog:
    """ """

    def __init__(
        self,
        market_data_reader: ForGettingHistoricalMarketData,
        catalog_writer: ForPersistingBacktestData,
    ) -> None:
        self.market_data_reader = market_data_reader
        self.catalog_writer = catalog_writer

    def execute(self, end_date: date, start_date: date | None = None) -> None:
        if start_date is not None and start_date > end_date:
            raise ValueError(f"The start_date={start_date} must be on or before end_date={end_date}")

        if start_date is None:
            market_data = self.market_data_reader.get_through(end_date=end_date)
        else:
            market_data = self.market_data_reader.get_between(start_date=start_date, end_date=end_date)

        self.catalog_writer.store_data(market_data=market_data)
