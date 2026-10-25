# Repository Guide

## Project

This repository implements daily crypto market-data ingestion, universe ranking, and a NautilusTrader backtest. Python source lives under `src/algo_emma`; raw and generated data live under `data/` and are excluded from Git.

## Working conventions

- Inspect the existing flow and current checkout before proposing or changing behavior.
- Find the root cause and make the smallest local change that addresses it. Preserve behavior that is already working; avoid unnecessary helpers, layers, and refactors.
- Keep domain rules independent of Nautilus types. Put orchestration in `application`, external I/O and Nautilus integration in `adapters`, and contracts in `ports`.
- Use `uv` and the project environment. Check `uv.lock` and the installed NautilusTrader version before relying on an API; do not assume `latest` documentation matches it.
- Keep financial calculations and timestamps explicit. Watch for look-ahead when deciding which completed daily bar can be used for a signal.
- Do not describe a target strategy rule as implemented unless the current code supports it. Report gaps between the reference strategy and implementation.
- Prefer clear domain names, short docstrings, and focused changes. Run only relevant checks and report what they establish.
- Keep diffs limited to changes required by the request. Do not reformat code or rewrite comments/docstrings unless explicitly requested; preserve surrounding style so review shows only meaningful changes.

## Reference strategy

Strategy #1, Short-Term Momentum, is the target specification documented in [README.md](README.md). Treat it as the reference when discussing intended behavior. The reference strategy status section in the README records known differences; update it when behavior changes.

## Useful commands

```bash
uv sync
uv run pytest
uv run ruff check .
uv run ty check
```

See the README for data-generation and backtest commands.
