#!/usr/bin/env python3
"""
TSM Conditional Buy Strategy

Rules:
  - Monitor TSM price every 60 seconds during market hours
  - If price drops below TRIGGER_PRICE ($359.02), buy 10 shares at market
  - Always verify market is open before placing any order
  - Exit after buy executes (one-time entry trigger)
"""

import requests
from config import BASE_URL, DATA_URL, HEADERS
import time
from datetime import datetime

# ── Credentials ────────────────────────────────────────────────────

# ── Strategy Parameters ─────────────────────────────────────────────
SYMBOL        = "TSM"
TRIGGER_PRICE = 359.02   # buy when price drops below this
BUY_QTY       = 10       # shares to buy at market
POLL_SEC      = 60       # seconds between price checks

# ── Helpers ─────────────────────────────────────────────────────────
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def market_is_open():
    r = requests.get(f"{BASE_URL}/clock", headers=HEADERS)
    if r.status_code == 200:
        clock = r.json()
        if not clock.get("is_open"):
            log(f"Market is CLOSED. Next open: {clock.get('next_open', 'unknown')}")
            return False
        return True
    log("WARNING: Could not verify market hours. Aborting to be safe.")
    return False

def get_price():
    r = requests.get(
        f"{DATA_URL}/stocks/{SYMBOL}/trades/latest",
        headers=HEADERS,
        params={"feed": "iex"}
    )
    if r.status_code == 200:
        return float(r.json()["trade"]["p"])
    return None

def place_market_buy(qty):
    r = requests.post(f"{BASE_URL}/orders", headers=HEADERS, json={
        "symbol": SYMBOL,
        "qty": str(qty),
        "side": "buy",
        "type": "market",
        "time_in_force": "day"
    })
    return r.json()

def print_order(label, o):
    bar = "─" * 56
    print(f"\n{bar}")
    print(f"  {label}")
    print(f"  Order ID  : {o.get('id', o.get('message', 'N/A'))}")
    print(f"  Symbol    : {o.get('symbol', SYMBOL)}")
    print(f"  Side      : {str(o.get('side', 'N/A')).upper()}")
    print(f"  Qty       : {o.get('qty', 'N/A')}")
    print(f"  Type      : {str(o.get('type', 'N/A')).upper()}")
    print(f"  Lmt Price : {o.get('limit_price') or 'MARKET'}")
    print(f"  Status    : {str(o.get('status', 'N/A')).upper()}")
    print(f"{bar}\n")

# ── Main ─────────────────────────────────────────────────────────────
def main():
    log(f"=== TSM Conditional Buy Strategy ===")
    log(f"Watching for TSM to drop below ${TRIGGER_PRICE:.2f} — will buy {BUY_QTY} shares at market")
    log(f"Polling every {POLL_SEC}s — press Ctrl+C to stop\n")

    price = get_price()
    if price:
        pct_away = ((price - TRIGGER_PRICE) / TRIGGER_PRICE) * 100
        log(f"Current TSM price: ${price:.2f}  |  Trigger at ${TRIGGER_PRICE:.2f}  ({pct_away:+.2f}% away)\n")

    try:
        while True:
            if not market_is_open():
                time.sleep(POLL_SEC)
                continue

            price = get_price()
            if not price:
                log("Price fetch failed, retrying...")
                time.sleep(POLL_SEC)
                continue

            pct_away = ((price - TRIGGER_PRICE) / TRIGGER_PRICE) * 100
            log(f"TSM ${price:.2f}  |  Trigger ${TRIGGER_PRICE:.2f}  ({pct_away:+.2f}% away)")

            if price < TRIGGER_PRICE:
                log(f"TRIGGER HIT — TSM ${price:.2f} dropped below ${TRIGGER_PRICE:.2f}. Buying {BUY_QTY} shares...")

                if not market_is_open():
                    log("Market closed at moment of trigger. Will retry next poll.")
                    time.sleep(POLL_SEC)
                    continue

                order = place_market_buy(BUY_QTY)
                print_order(f"BUY  |  {BUY_QTY} shares TSM  |  Market  |  Triggered at ${price:.2f}", order)
                log("Entry complete. Strategy done.")
                break

            time.sleep(POLL_SEC)

    except KeyboardInterrupt:
        log("Strategy stopped manually. No order was placed.")

if __name__ == "__main__":
    main()
