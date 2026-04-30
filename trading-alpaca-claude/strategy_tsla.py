#!/usr/bin/env python3
"""
TSLA Trailing Stop Strategy

Rules:
  - Buy 10 shares at market
  - Stop loss: sell EVERYTHING if price drops 10% from peak (floor never moves down)
  - Trailing: once price is up 10% from entry, trail 5% below peak
  - Ladder in: buy 20 shares at -20%, buy 10 shares at -30% from entry
"""

import requests
import time
from datetime import datetime

# ── Credentials ────────────────────────────────────────────────────
BASE_URL   = "https://paper-api.alpaca.markets/v2"
DATA_URL   = "https://data.alpaca.markets/v2"
API_KEY    = "PK5TSOUE524H625IZGF3BJZEBF"
SECRET_KEY = "HbQseBQaXpEFHDE21zZCSQUi2GhhWfWnmUKZqC1Vvh2x"
HEADERS    = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": SECRET_KEY,
    "Content-Type": "application/json"
}

# ── Strategy Parameters ─────────────────────────────────────────────
SYMBOL        = "TSLA"
INITIAL_QTY   = 10
STOP_PCT      = 0.10   # sell all if price drops 10% from peak
TRAIL_TRIGGER = 0.10   # start trailing after +10% gain from entry
TRAIL_PCT     = 0.05   # trail 5% below peak once activated
LADDER_1_DROP = 0.20   # -20% from entry → buy 20 more shares
LADDER_2_DROP = 0.30   # -30% from entry → buy 10 more shares
LADDER_1_QTY  = 20
LADDER_2_QTY  = 10
POLL_SEC      = 30     # seconds between price checks

# ── Helpers ─────────────────────────────────────────────────────────
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def post(path, data):
    r = requests.post(f"{BASE_URL}{path}", headers=HEADERS, json=data)
    return r.json()

def get_price():
    r = requests.get(
        f"{DATA_URL}/stocks/{SYMBOL}/trades/latest",
        headers=HEADERS,
        params={"feed": "iex"}
    )
    if r.status_code == 200:
        return float(r.json()["trade"]["p"])
    return None

def market_order(qty, side):
    return post("/orders", {
        "symbol": SYMBOL, "qty": str(qty),
        "side": side, "type": "market", "time_in_force": "day"
    })

def limit_order(qty, side, price):
    return post("/orders", {
        "symbol": SYMBOL, "qty": str(qty), "side": side,
        "type": "limit", "limit_price": f"{price:.2f}", "time_in_force": "gtc"
    })

def close_position():
    r = requests.delete(f"{BASE_URL}/positions/{SYMBOL}", headers=HEADERS)
    return r.json() if r.content else {"status": "closed"}

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

# ── Setup: Place all orders ──────────────────────────────────────────
def setup():
    log(f"=== TSLA Trailing Stop Strategy — Setup ===\n")

    # Step 1: Market buy 10 shares
    log("Placing initial market buy: 10 shares TSLA")
    buy = market_order(INITIAL_QTY, "buy")
    print_order("BUY  |  10 shares TSLA  |  Market", buy)

    time.sleep(3)

    entry = get_price()
    if not entry:
        log("ERROR: Could not fetch entry price.")
        return None

    log(f"Entry price confirmed: ${entry:.2f}")

    # Step 2: Calculate price levels
    stop_floor = round(entry * (1 - STOP_PCT), 2)
    trail_on   = round(entry * (1 + TRAIL_TRIGGER), 2)
    l1_price   = round(entry * (1 - LADDER_1_DROP), 2)
    l2_price   = round(entry * (1 - LADDER_2_DROP), 2)

    print(f"\n{'═'*56}")
    print(f"  PRICE LEVELS  (entry = ${entry:.2f})")
    print(f"  ─────────────────────────────────────────────────")
    print(f"  Initial stop floor  : ${stop_floor:<8.2f}  (-{STOP_PCT*100:.0f}%)")
    print(f"  Trailing activates  : ${trail_on:<8.2f}  (+{TRAIL_TRIGGER*100:.0f}% from entry)")
    print(f"  Trail width (once on): {TRAIL_PCT*100:.0f}% below peak")
    print(f"  Ladder buy #1       : ${l1_price:<8.2f}  (-{LADDER_1_DROP*100:.0f}%) → {LADDER_1_QTY} shares")
    print(f"  Ladder buy #2       : ${l2_price:<8.2f}  (-{LADDER_2_DROP*100:.0f}%) → {LADDER_2_QTY} shares")
    print(f"{'═'*56}\n")

    # Step 3: Ladder limit buy orders
    log("Placing ladder buy #1 (20 shares at -20%)...")
    l1 = limit_order(LADDER_1_QTY, "buy", l1_price)
    print_order(f"LADDER BUY #1  |  20 shares TSLA  |  ${l1_price:.2f}  (-20%)", l1)

    log("Placing ladder buy #2 (10 shares at -30%)...")
    l2 = limit_order(LADDER_2_QTY, "buy", l2_price)
    print_order(f"LADDER BUY #2  |  10 shares TSLA  |  ${l2_price:.2f}  (-30%)", l2)

    return entry, stop_floor, trail_on

# ── Monitor: Track price and manage trailing stop ────────────────────
def monitor(entry, stop_floor, trail_on):
    peak     = entry
    floor    = stop_floor
    trailing = False

    log(f"Monitoring every {POLL_SEC}s — press Ctrl+C to stop\n")

    try:
        while True:
            price = get_price()
            if not price:
                log("Price fetch failed, retrying...")
                time.sleep(POLL_SEC)
                continue

            if price > peak:
                peak = price

            # Activate trailing mode after +10% gain
            if not trailing and price >= trail_on:
                trailing = True
                log(f"TRAILING MODE ON — price ${price:.2f} crossed +{TRAIL_TRIGGER*100:.0f}% target")

            # Raise floor (never lower it)
            if trailing:
                new_floor = round(peak * (1 - TRAIL_PCT), 2)
                if new_floor > floor:
                    log(f"Floor raised: ${floor:.2f} → ${new_floor:.2f}  (peak ${peak:.2f})")
                    floor = new_floor

            pct = ((price - entry) / entry) * 100
            mode = "TRAILING" if trailing else "FIXED"
            log(f"Price ${price:.2f}  |  Floor ${floor:.2f}  |  Peak ${peak:.2f}  |  {pct:+.2f}%  |  {mode}")

            # Trigger: sell everything
            if price <= floor:
                log(f"STOP TRIGGERED — ${price:.2f} hit floor ${floor:.2f}. Closing full position...")
                result = close_position()
                log(f"Position closed: {result}")
                log("Strategy complete.")
                break

            time.sleep(POLL_SEC)

    except KeyboardInterrupt:
        log("Monitoring stopped manually. Ladder orders remain active.")

# ── Entry point ──────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    result = setup()
    if result and "--setup-only" not in sys.argv:
        entry, stop_floor, trail_on = result
        monitor(entry, stop_floor, trail_on)
