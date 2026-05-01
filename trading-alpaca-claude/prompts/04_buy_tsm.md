# Prompt: TSM Strategy Prompts

## Purpose
All prompts related to Taiwan Semiconductor (TSM) — price research, conditional entry, and strategy setup.

---

## Prompt 1 — Pull Live Price & Bar Data

```
Pull the current TSM price and recent bar data from Alpaca so I have live numbers to work with.
```

### Output Produced (2026-04-29)

| Field           | Value        |
|----------------|--------------|
| Current price  | $393.76      |
| 30-Day High    | $377.99      |
| 30-Day Low     | $313.81      |
| Range Midpoint | $345.90      |
| 7-Day MA       | $356.78      |
| 20-Day MA      | $343.48      |
| 30-Day MA      | $345.60      |
| Support zone   | ~$319.17     |
| Resistance zone| ~$374.56     |
| Avg Daily Vol  | 436,513 shares |

### Key Observations
- TSM broke out +4.2% above its 30-day high — strong momentum
- Bounced +25% from the March 30 low of $313.81
- Price is 10–15% extended above all moving averages
- Old resistance at $370–$374 is now potential support
- Conservative pullback entry zones: $370–$374 (prior resistance) or $345–$350 (near MAs)

### Script Used
```python
# Fetch current price
GET https://data.alpaca.markets/v2/stocks/TSM/trades/latest?feed=iex

# Fetch 30 daily bars (requires explicit start date)
GET https://data.alpaca.markets/v2/stocks/TSM/bars
  ?timeframe=1Day&feed=iex&start=YYYY-MM-DDT00:00:00Z&limit=30
```

---

## Prompt 2 — Conditional Buy Entry

```
Create a strategy_tsm.py that monitors TSM price and buys 10 shares at market
if the price drops below $359.02. Check market hours before placing any order.
```

### Parameters

| Parameter     | Value    |
|--------------|----------|
| Symbol        | TSM      |
| Trigger price | $359.02  |
| Buy qty       | 10 shares|
| Order type    | Market   |
| Market check  | Required |

### Script
See: [strategy_tsm.py](../strategy_tsm.py)

Run:
```bash
python3 strategy_tsm.py
```

---

## Notes
- TSM is an ADR (Taiwan Semi listed on NYSE). Use `feed=iex` for real-time data — SIP feed requires paid subscription on paper accounts.
- Always pass an explicit `start` date when fetching historical bars, otherwise the API returns only the latest bar.
- Market hours must be confirmed via `GET /v2/clock` before placing any order.
