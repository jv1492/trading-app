# Prompt Library — Alpaca Trading

A reference library of every prompt and agent instruction used in this project.
Add a new file here each time a new strategy, order type, or agent is introduced.

## Prompts

| # | File | Description |
|---|------|-------------|
| 01 | [01_buy_market_order.md](01_buy_market_order.md) | Place a single market buy order via Alpaca API |
| 02 | [02_trailing_stop_strategy.md](02_trailing_stop_strategy.md) | Full trailing stop setup: buy, floor, trailing, ladder-in |
| 03 | [03_scheduled_monitor.md](03_scheduled_monitor.md) | Remote agent prompt for hourly strategy monitoring during market hours |
| 04 | [04_buy_tsm.md](04_buy_tsm.md) | TSM live data pull + conditional buy entry below $359.02 |
| 05 | [05_watchlist.md](05_watchlist.md) | Personal watchlist + top 5 semiconductors + top 5 AI companies |

## Naming Convention

```
[##]_[short_description].md
```

- `##` — two-digit sequence number (01, 02, 03 ...)
- `short_description` — snake_case, describes what the prompt does

## What to Include in Each Prompt File

- **Purpose** — one sentence on what it does
- **Prompt** — the exact text given to Claude (with placeholders for params)
- **Parameters Used** — the actual values for the most recent run
- **Orders / Results** — IDs, prices, statuses from real executions
- **Script** — link to any associated script file
- **Notes** — gotchas, limitations, follow-up ideas
