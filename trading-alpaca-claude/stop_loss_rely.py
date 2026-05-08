#!/usr/bin/env python3
"""
Stop Loss for RELY
Places a stop loss sell order for RELY at calculated stop price.
Run: python3 stop_loss_rely.py
"""

import requests
import pandas as pd
import numpy as np
from config import BASE_URL, DATA_URL, HEADERS
from datetime import datetime
import yfinance as yf

# ── Order Parameters ─────────────────────────────────────────────────
SYMBOL = "RELY"
QTY    = 291  # From portfolio

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

def fetch(ticker, period="3mo", interval="1d"):
    df = yf.download(ticker, period=period, interval=interval,
                     progress=False, auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [c.strip() for c in df.columns]
    return df.dropna()

def find_sr(H, L, C, window=8, tol=0.02):
    h, l, n = H.values, L.values, len(H)
    ph, pl = [], []
    for i in range(window, n - window):
        if h[i] == max(h[i-window:i+window+1]): ph.append(float(h[i]))
        if l[i] == min(l[i-window:i+window+1]): pl.append(float(l[i]))
    def cluster(pts):
        if not pts: return []
        pts = sorted(pts); groups = [[pts[0]]]
        for p in pts[1:]:
            if (p - groups[-1][-1]) / groups[-1][-1] < tol: groups[-1].append(p)
            else: groups.append([p])
        return [round(sum(g)/len(g), 2) for g in groups if len(g) >= 2]
    cur = float(C.iloc[-1])
    return (sorted([s for s in cluster(pl) if s < cur*0.999], reverse=True),
            sorted([r for r in cluster(ph) if r > cur*1.001]))

def calculate_stop_loss(symbol):
    df = fetch(symbol)
    if df.empty:
        log(f"Could not fetch data for {symbol}")
        return None
    H, L, C = df['High'], df['Low'], df['Close']
    support, _ = find_sr(H, L, C)
    cur = float(C.iloc[-1])
    near_sup = support[0] if support else round(cur*0.95, 2)
    stop_loss = round(near_sup * 0.995, 2)
    return stop_loss

def print_order(o):
    bar = "─" * 56
    print(f"\n{bar}")
    print(f"  ORDER SUBMITTED")
    print(f"  Order ID  : {o.get('id', o.get('message', 'N/A'))}")
    print(f"  Symbol    : {o.get('symbol', SYMBOL)}")
    print(f"  Side      : {str(o.get('side', 'N/A')).upper()}")
    print(f"  Qty       : {o.get('qty', 'N/A')}")
    print(f"  Type      : {str(o.get('type', 'N/A')).upper()}")
    print(f"  Stop Price: {o.get('stop_price', 'N/A')}")
    print(f"  Status    : {str(o.get('status', 'N/A')).upper()}")
    print(f"{bar}\n")

# ── Main ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    log(f"=== Stop Loss for {SYMBOL} — {QTY} shares ===\n")

    stop_price = calculate_stop_loss(SYMBOL)
    if stop_price is None:
        log("Could not calculate stop loss. Aborting.")
        raise SystemExit(1)

    log(f"Calculated stop loss for {SYMBOL}: ${stop_price:.2f}")

    is_open, clock = market_is_open()
    if not is_open:
        next_open = (clock or {}).get("next_open", "unknown")
        log(f"Market is CLOSED. Next open: {next_open}")
        log("Aborting — will not place orders while market is closed.")
        raise SystemExit(1)

    log(f"Market is OPEN. Placing stop sell: {QTY} shares {SYMBOL} @ stop ${stop_price:.2f}...")

    r = requests.post(
        f"{BASE_URL}/orders",
        headers=HEADERS,
        json={
            "symbol":        SYMBOL,
            "qty":           str(QTY),
            "side":          "sell",
            "type":          "stop",
            "stop_price":    f"{stop_price:.2f}",
            "time_in_force": "gtc",
        },
    )

    order = r.json()
    if r.status_code in (200, 201):
        print_order(order)
        log("Stop loss order placed successfully.")
    else:
        log(f"ERROR {r.status_code}: {order.get('message', order)}")
        raise SystemExit(1)