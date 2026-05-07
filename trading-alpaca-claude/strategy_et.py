#!/usr/bin/env python3
"""
Energy Transfer (ET) — Bracket Buy Strategy
Buys ~$1,000 worth of ET at $19.82 with an automatic stop loss at $19.79.
Uses a bracket order so the stop loss is placed automatically on fill.
Run: python3 strategy_et.py
"""

import requests
import math
from datetime import datetime
from config import BASE_URL, DATA_URL, HEADERS

# ── Strategy Parameters ──────────────────────────────────────────────
SYMBOL      = "ET"
BUDGET      = 1_000.00   # dollars to invest
LIMIT_PRICE = 19.82      # buy when ET reaches this price
STOP_PRICE  = 19.77      # stop loss — exit if price falls here after fill

# Calculate shares from budget (floor to stay within budget)
QTY         = math.floor(BUDGET / LIMIT_PRICE)
COST        = QTY * LIMIT_PRICE
RISK_PER_SH = round(LIMIT_PRICE - STOP_PRICE, 2)
TOTAL_RISK  = round(RISK_PER_SH * QTY, 2)

# ── Helpers ──────────────────────────────────────────────────────────
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_current_price():
    r = requests.get(
        f"{DATA_URL}/stocks/{SYMBOL}/trades/latest",
        headers=HEADERS,
        params={"feed": "iex"},
    )
    if r.status_code == 200:
        return float(r.json()["trade"]["p"])
    return None

def market_is_open():
    r = requests.get(f"{BASE_URL}/clock", headers=HEADERS)
    if r.status_code != 200:
        log("WARNING: Could not verify market hours.")
        return False, None
    clock = r.json()
    return clock.get("is_open", False), clock

def print_order(o):
    bar = "─" * 56
    print(f"\n{bar}")
    print(f"  ORDER SUBMITTED")
    print(f"  Order ID     : {o.get('id', o.get('message', 'N/A'))}")
    print(f"  Symbol       : {o.get('symbol', SYMBOL)}")
    print(f"  Side         : BUY")
    print(f"  Qty          : {QTY} shares  (~${COST:.2f})")
    print(f"  Entry limit  : ${LIMIT_PRICE:.2f}")
    print(f"  Stop loss    : ${STOP_PRICE:.2f}  (-${RISK_PER_SH:.2f}/share)")
    print(f"  Max risk     : ${TOTAL_RISK:.2f}  ({TOTAL_RISK/COST*100:.2f}% of position)")
    print(f"  Time In Force: GTC  (active until filled or cancelled)")
    print(f"  Status       : {str(o.get('status', 'N/A')).upper()}")
    print(f"{bar}\n")

# ── Main ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    log(f"=== ET Bracket Buy Strategy ===\n")
    log(f"  Budget       : ${BUDGET:,.2f}")
    log(f"  Shares       : {QTY}  (${COST:.2f} at ${LIMIT_PRICE:.2f})")
    log(f"  Entry limit  : ${LIMIT_PRICE:.2f}")
    log(f"  Stop loss    : ${STOP_PRICE:.2f}  (max risk ${TOTAL_RISK:.2f})")

    price = get_current_price()
    if price:
        diff = price - LIMIT_PRICE
        pct  = diff / price * 100
        log(f"  Current price: ${price:.2f}  ({diff:+.2f} / {pct:+.2f}% from entry)\n")

    is_open, clock = market_is_open()
    if not is_open:
        next_open = (clock or {}).get("next_open", "unknown")
        log(f"Market is CLOSED — next open: {next_open}")
        log("NOTE: GTC bracket orders can be placed while market is closed.\n")

    log(f"Placing GTC bracket order: {QTY} shares {SYMBOL} @ ${LIMIT_PRICE:.2f} | stop ${STOP_PRICE:.2f}...")

    r = requests.post(
        f"{BASE_URL}/orders",
        headers=HEADERS,
        json={
            "symbol":        SYMBOL,
            "qty":           str(QTY),
            "side":          "buy",
            "type":          "limit",
            "limit_price":   f"{LIMIT_PRICE:.2f}",
            "time_in_force": "gtc",
            "order_class":   "oto",
            "stop_loss":     {"stop_price": f"{STOP_PRICE:.2f}"},
        },
    )

    order = r.json()
    if r.status_code in (200, 201):
        print_order(order)
        log("Bracket order is live.")
        log(f"  → Fills automatically when ET hits ${LIMIT_PRICE:.2f}")
        log(f"  → Stop loss fires automatically at ${STOP_PRICE:.2f} if price drops after fill")
    else:
        log(f"ERROR {r.status_code}: {order.get('message', order)}")
        raise SystemExit(1)
