# algo-emma

`algo-emma` is a Python project for building daily cryptocurrency universe rankings and evaluating strategies with NautilusTrader.

## Strategy #1: Short-Term Momentum

This is the reference strategy for the project:

- **Assets:** the 20 cryptocurrencies with the highest trading volume, selected daily.
- **Ranking:** rank the selected assets by their rate of change over the previous 10 days (ROC10).
- **Direction and exposure:** long only, with at most 10 simultaneous positions.
- **Entry:** place a buy stop at the previous completed daily high plus `0.75 × ATR(3)`.
- **Exit:** close the position exactly two days after the entry fills.

The stop order waits for price to break above the prior high. If price keeps falling, it may never trigger, so the strategy can stay out of the market. An unfilled order is not a position; the two-day holding period starts on the fill.

### Current implementation status

- Daily rankings select the 20 most liquid eligible assets using the configured moving average of USDT volume, then rank that universe by ROC10. The strategy checks universe membership but does not use rank to prioritize orders when more than 10 candidates compete for slots.
- Entry orders use the daily bar high plus `0.75 × ATR(3)` and expire according to the signal's configured order lifetime.
- The strategy schedules a position close two days after Nautilus reports the position opened. On strategy stop, it also cancels pending orders and requests closure of open positions.
- Position sizing allocates account equity across 10 positions. The current fee assumption is 0.1% maker and taker, stored on catalog instruments; it is configurable during catalog generation. Raw CSV data does not contain fee history.

Backtest returns describe the current implementation and its assumptions. They should not be treated as results for the full reference strategy until rank-based order priority and other strategy semantics match the specification.

## Data and backtests

Install the locked project dependencies:

```bash
uv sync
```

Raw daily CSV data is read from `data/raw/binance_spot_daily` by default. It is not tracked by Git. Build the NautilusTrader Parquet catalog with the default 0.1% maker/taker fee:

```bash
uv run python -m algo_emma.adapters.entrypoints.build_backtest_catalog_data \
  --start-date=2022-01-01 \
  --end-date=2025-12-31
```

Override the fee ratio with `--fee-rate` (for example, `0.00075` for 0.075%). Generated catalog files are written to `data/processed/catalog` by default.

Generate one ranking file per date. Existing files are preserved unless `--overwrite-ranking` is supplied:

```bash
uv run python -m algo_emma.adapters.entrypoints.build_universe_ranking \
  --start-date=2022-01-01 \
  --end-date=2025-12-31 \
  --overwrite-ranking
```

The ranking command stops if a date has no usable market data or produces no eligible assets. Check data coverage before requesting a long range.

Run a backtest using the generated catalog and rankings:

```bash
uv run python -m algo_emma.adapters.entrypoints.run_backtest \
  --start-date=2023-01-01 \
  --end-date=2025-12-31
```

The date range is bounded by available raw market data and ranking files. Daily bars use UTC timestamps; inspect the entrypoint's date conversion when interpreting the effective first and last simulated timestamps.

## Project layout

- `domain`: strategy rules, models, indicators, ranking, and sizing.
- `application`: use cases that coordinate domain operations.
- `ports`: interfaces for market-data and persistence adapters.
- `adapters`: CSV ingestion/output, Parquet catalog writing, NautilusTrader strategy, and command-line entrypoints.

## Checks

```bash
uv run pytest
uv run ruff check .
uv run ty check
```
