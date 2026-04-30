# Prompt: Trailing Stop Strategy Setup

## Purpose
Buy an initial position and set up a full trailing stop strategy with dynamic floor management
and ladder-in buy orders on the way down.

## Prompt

```
Set up a trailing stop strategy on [SYMBOL]. Buy [INITIAL_QTY] shares at market price and apply these rules:

STOP LOSS (Floor):
- If the stock drops [STOP_PCT]% from my entry price, sell everything.
- The floor never moves down, only up.

TRAILING FLOOR:
- If the stock goes up [TRAIL_TRIGGER_PCT]% from what I paid, move the stop loss up.
- Move it to [TRAIL_PCT]% below the current price.
- Every time it climbs, move the floor up again.
- The floor only goes up, never down.

LADDER IN (buy the dip):
- If the stock drops [LADDER_1_PCT]%, buy [LADDER_1_QTY] more shares.
- If the stock drops [LADDER_2_PCT]%, buy [LADDER_2_QTY] more shares.
- This way I get better prices on the way down instead of just losing money.

After placing all orders, show me a summary of every order right after it is placed.
```

## Parameters Used (TSLA — 2026-04-29)

| Parameter        | Value         |
|-----------------|---------------|
| Symbol           | TSLA          |
| Initial buy      | 10 shares     |
| Entry price      | $371.94       |
| Stop floor       | $334.75 (-10%)|
| Trail trigger    | $409.13 (+10%)|
| Trail width      | 5% below peak |
| Ladder #1        | 20 shares @ $297.55 (-20%) |
| Ladder #2        | 10 shares @ $260.36 (-30%) |

## Orders Placed

| Order              | Qty | Price   | Type   | Status   | Order ID     |
|--------------------|-----|---------|--------|----------|--------------|
| Initial buy        | 10  | Market  | Market | Accepted | 4d36323c     |
| Ladder buy #1      | 20  | $297.55 | Limit  | Accepted | 479564af     |
| Ladder buy #2      | 10  | $260.36 | Limit  | Accepted | 9d463fda     |

## Script
See: `strategy_tsla.py`

Run setup only (place orders, print summary, no monitoring loop):
```bash
python3 strategy_tsla.py --setup-only
```

Run full strategy (setup + live monitoring + auto stop execution):
```bash
python3 strategy_tsla.py
```
