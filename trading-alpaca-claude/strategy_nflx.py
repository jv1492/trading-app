#!/usr/bin/env python3
"""
Netflix (NFLX) — Simple Market Buy
Buys 2 shares of NFLX at market price.
Run: python3 strategy_nflx.py
"""

import requests
from config import BASE_URL, DATA_URL, HEADERS
from datetime import datetime

# ── Credentials ─────────────────────────────────────────────────────

# ── Order Parameters ─────────────────────────────────────────────────
SYMBOL = "NFLX"
QTY    = 2

# ── Helpers ──────────────────────────────────────────────────────────
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def market_is_open():
    r = requests.get(f"{BASE_URL}/clock", headers=HEADERS)
    if r.status_code != 200:
        log("WARNING: Could not verify market hours. Aborting to be safe.")
        return False, None
    clock = r.json()
    return clock.get("is_open", False), clock

def print_order(o):
    bar = "─" * 56
    print(f"\n{bar}")
    print(f"  ORDER SUBMITTED")
    print(f"  Order ID  : {o.get('id', o.get('message', 'N/A'))}")
    print(f"  Symbol    : {o.get('symbol', SYMBOL)}")
    print(f"  Side      : {str(o.get('side', 'N/A')).upper()}")
    print(f"  Qty       : {o.get('qty', 'N/A')}")
    print(f"  Type      : {str(o.get('type', 'N/A')).upper()}")
    print(f"  Status    : {str(o.get('status', 'N/A')).upper()}")
    print(f"{bar}\n")

# ── Main ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    log(f"=== NFLX Buy — {QTY} shares ===\n")

    is_open, clock = market_is_open()
    if not is_open:
        next_open = (clock or {}).get("next_open", "unknown")
        log(f"Market is CLOSED. Next open: {next_open}")
        log("Aborting — will not place orders while market is closed.")
        raise SystemExit(1)

    log(f"Market is OPEN. Placing market buy: {QTY} shares {SYMBOL}...")

    r = requests.post(
        f"{BASE_URL}/orders",
        headers=HEADERS,
        json={
            "symbol":        SYMBOL,
            "qty":           str(QTY),
            "side":          "buy",
            "type":          "market",
            "time_in_force": "day",
        },
    )

    order = r.json()
    if r.status_code in (200, 201):
        print_order(order)
        log("Order placed successfully.")
    else:
        log(f"ERROR {r.status_code}: {order.get('message', order)}")
        raise SystemExit(1)
