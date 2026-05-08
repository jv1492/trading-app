#!/usr/bin/env python3
"""
Calculate Stop Losses for Portfolio
Creates an Excel file with stop loss values for each position.
Run: python3 calculate_stop_losses.py
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# ── Portfolio Data ───────────────────────────────────────────────────
portfolio = [
    {"symbol": "AAPL", "quantity": 79.001},
    {"symbol": "IAUM", "quantity": 100},
    {"symbol": "NVDA", "quantity": 45.021},
    {"symbol": "MSFT", "quantity": 50.852},
    {"symbol": "CPRX", "quantity": 100},
    {"symbol": "PLTR", "quantity": 40},
    {"symbol": "RELY", "quantity": 291.46},
    {"symbol": "ET", "quantity": 178.481},
    {"symbol": "NVDY", "quantity": 376.861},
    {"symbol": "PLTY", "quantity": 103.66},
    {"symbol": "CWBHF", "quantity": 2275},
]

# ── Helpers ──────────────────────────────────────────────────────────
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
        return None, None, None
    H, L, C = df['High'], df['Low'], df['Close']
    support, _ = find_sr(H, L, C)
    cur = float(C.iloc[-1])
    near_sup = support[0] if support else round(cur*0.95, 2)
    stop_loss = round(near_sup * 0.995, 2)
    return cur, near_sup, stop_loss

# ── Main ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Calculating stop losses for portfolio...")

    results = []
    for pos in portfolio:
        symbol = pos["symbol"]
        qty = pos["quantity"]
        print(f"Processing {symbol}...")
        cur_price, near_sup, stop_loss = calculate_stop_loss(symbol)
        if stop_loss is None:
            print(f"  Could not calculate for {symbol}")
            continue
        results.append({
            "Symbol": symbol,
            "Quantity": qty,
            "Current Price": cur_price,
            "Nearest Support": near_sup,
            "Stop Loss Price": stop_loss,
            "Risk per Share": round(cur_price - stop_loss, 2),
            "Total Risk": round((cur_price - stop_loss) * qty, 2),
        })

    df = pd.DataFrame(results)
    filename = f"portfolio_stop_losses_{datetime.now().strftime('%Y%m%d')}.xlsx"
    df.to_excel(filename, index=False)
    print(f"\nSaved to {filename}")
    print(df)