#!/usr/bin/env python3
"""
NextEra Energy (NEE) — Limit Buy Strategy
Places a GTC limit buy order at $98.95.
Order stays active until filled or manually cancelled.
Run: python3 strategy_nee.py
"""

import requests
from config import BASE_URL, DATA_URL, HEADERS
from datetime import datetime

# ── Credentials ─────────────────────────────────────────────────────

# ── Strategy Parameters ──────────────────────────────────────────────
SYMBOL      = "NEE"
QTY         = 2
LIMIT_PRICE = 98.95   # buy when price reaches this level

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
    print(f"  Order ID    : {o.get('id', o.get('message', 'N/A'))}")
    print(f"  Symbol      : {o.get('symbol', SYMBOL)}")
    print(f"  Side        : {str(o.get('side', 'N/A')).upper()}")
    print(f"  Qty         : {o.get('qty', 'N/A')}")
    print(f"  Type        : LIMIT")
    print(f"  Limit Price : ${LIMIT_PRICE:.2f}")
    print(f"  Time In Force: GTC  (active until filled or cancelled)")
    print(f"  Status      : {str(o.get('status', 'N/A')).upper()}")
    print(f"{bar}\n")

# ── Main ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    log(f"=== NEE Limit Buy Strategy ===\n")
    log(f"  Target price : ${LIMIT_PRICE:.2f}")
    log(f"  Qty          : {QTY} shares")

    # Show current price for context
    price = get_current_price()
    if price:
        diff = price - LIMIT_PRICE
        pct  = diff / price * 100
        log(f"  Current price: ${price:.2f}  ({diff:+.2f} / {pct:+.2f}% from target)\n")

    is_open, clock = market_is_open()
    if not is_open:
        next_open = (clock or {}).get("next_open", "unknown")
        log(f"Market is CLOSED — next open: {next_open}")
        log("NOTE: GTC limit orders can be placed while market is closed.")
        log("      The order will be queued and execute when the price is reached.\n")

    log(f"Placing GTC limit buy: {QTY} shares {SYMBOL} @ ${LIMIT_PRICE:.2f}...")

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
        },
    )

    order = r.json()
    if r.status_code in (200, 201):
        print_order(order)
        log("Order is live. It will fill automatically when NEE reaches $98.95.")
        log("To cancel: go to Alpaca dashboard or run a cancel script with the order ID above.")
    else:
        log(f"ERROR {r.status_code}: {order.get('message', order)}")
        raise SystemExit(1)
