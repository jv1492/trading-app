#!/usr/bin/env python3
"""
Energy Companies Breakout Screener
Run: python3 energy.py

Scores ~30 energy stocks using the same criteria as the dashboard:
  trend alignment, RSI 50-70, MACD, Bollinger consolidation, ATR%, RS vs SPY
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

ENERGY_UNIVERSE = [
    # Oil & Gas Majors
    "XOM",  "CVX",  "COP",  "OXY",
    # Exploration & Production
    "EOG",  "DVN",  "FANG", "MRO",  "APA",  "CTRA",
    # Oil Field Services
    "SLB",  "HAL",  "BKR",
    # Midstream / Pipeline
    "ET",   "WMB",  "KMI",  "EPD",  "TRGP",
    # Refining
    "VLO",  "PSX",  "MPC",
    # Utilities
    "NEE",  "DUK",  "SO",   "AEP",  "EXC",
    # Clean / Renewable Energy
    "ENPH", "FSLR", "PLUG", "BE",
]

def score_ticker(sym, raw, spy_c):
    df = raw[sym].dropna()
    if len(df) < 60:
        return None
    C = df["Close"].squeeze()
    H = df["High"].squeeze()
    L = df["Low"].squeeze()
    cur = float(C.iloc[-1])

    s20  = C.rolling(20).mean()
    s50  = C.rolling(50).mean()
    s200 = C.rolling(min(200, len(C))).mean()
    s20v, s50v, s200v = float(s20.iloc[-1]), float(s50.iloc[-1]), float(s200.iloc[-1])
    s20_sl = float(s20.iloc[-1] - s20.iloc[-6])
    s50_sl = float(s50.iloc[-1] - s50.iloc[-6])

    d    = C.diff()
    g    = d.clip(lower=0).rolling(14).mean()
    lv   = (-d.clip(upper=0)).rolling(14).mean().replace(0, np.nan)
    rsi_v = float((100 - (100 / (1 + g / lv))).iloc[-1])

    ml   = C.ewm(span=12, adjust=False).mean() - C.ewm(span=26, adjust=False).mean()
    mh_v = float((ml - ml.ewm(span=9, adjust=False).mean()).iloc[-1])

    bb_std = C.rolling(20).std()
    bb_lo  = s20 - 2 * bb_std
    bb_hi  = s20 + 2 * bb_std
    bb_pct = float(((C - bb_lo) / (bb_hi - bb_lo).replace(0, np.nan)).iloc[-1])

    tr      = pd.concat([(H-L), (H-C.shift()).abs(), (L-C.shift()).abs()], axis=1).max(axis=1)
    atr_pct = float(tr.rolling(20).mean().iloc[-1] / cur * 100)

    cmb   = pd.concat([C.rename("s"), spy_c.rename("spy")], axis=1).dropna()
    sr    = float((cmb["s"].iloc[-1]  - cmb["s"].iloc[0])   / cmb["s"].iloc[0])
    spyr  = float((cmb["spy"].iloc[-1] - cmb["spy"].iloc[0]) / cmb["spy"].iloc[0])
    rs_sc = round(min(99, max(1, 50 + (sr - spyr) * 100 * 1.2)), 1)

    trend_up = cur > s20v and cur > s50v and s20_sl > 0 and s50_sl > 0

    sc = 0.0
    if trend_up:                sc += 2.0
    if cur > s200v:             sc += 1.0
    if 50 <= rsi_v <= 70:       sc += 2.0
    elif 45 <= rsi_v < 50:      sc += 0.5
    if mh_v > 0:                sc += 1.5
    if 0.4 <= bb_pct <= 0.75:   sc += 2.0
    elif 0.75 < bb_pct <= 0.88: sc += 0.5
    if atr_pct < 2.5:           sc += 1.0
    if rs_sc > 60:              sc += 1.5
    elif rs_sc > 50:            sc += 0.5

    return {
        "ticker":  sym,
        "price":   round(cur, 2),
        "score":   round(sc, 1),
        "rsi":     round(rsi_v, 1),
        "rs":      round(rs_sc, 1),
        "bb_pct":  round(bb_pct, 2),
        "atr_pct": round(atr_pct, 2),
        "trend":   "↑ UP" if trend_up else "—",
        "macd":    "▲" if mh_v > 0 else "▼",
    }

def main():
    print(f"\n{'='*65}")
    print(f"  Energy Companies Breakout Screener — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  Scoring {len(ENERGY_UNIVERSE)} tickers · Same criteria as dashboard")
    print(f"{'='*65}")
    print("  Fetching data...")

    raw   = yf.download(ENERGY_UNIVERSE, period="6mo", interval="1d",
                        group_by="ticker", progress=False,
                        auto_adjust=True, threads=True)
    spy_c = yf.download("SPY", period="6mo", interval="1d",
                        progress=False, auto_adjust=True)["Close"].squeeze()

    results = []
    skipped = []
    for sym in ENERGY_UNIVERSE:
        try:
            r = score_ticker(sym, raw, spy_c)
            if r:
                results.append(r)
        except Exception:
            skipped.append(sym)

    results.sort(key=lambda x: x["score"], reverse=True)
    top10 = results[:10]

    print(f"\n  {'#':<3} {'Ticker':<6} {'Price':>8} {'Score':>6} {'RSI':>5} {'RS':>5} {'BB%B':>6} {'ATR%':>6} {'Trend':>7} {'MACD':>5}")
    print(f"  {'─'*63}")
    for i, r in enumerate(top10, 1):
        score_bar = "█" * int(r["score"]) + "░" * (12 - int(r["score"]))
        print(
            f"  {i:<3} {r['ticker']:<6} ${r['price']:>7.2f} "
            f"{r['score']:>6.1f} {r['rsi']:>5.1f} {r['rs']:>5.1f} "
            f"{r['bb_pct']:>6.2f} {r['atr_pct']:>6.2f} "
            f"{r['trend']:>7} {r['macd']:>5}  {score_bar}"
        )

    print(f"\n  Scoring criteria (max 11.5 pts):")
    print(f"  Trend up (SMA20/50 rising)  +2.0  |  Above SMA200      +1.0")
    print(f"  RSI 50-70 (sweet spot)      +2.0  |  MACD hist > 0     +1.5")
    print(f"  BB %B 0.40-0.75 (coiling)   +2.0  |  ATR% < 2.5%       +1.0")
    print(f"  RS vs SPY > 60              +1.5  |  RS vs SPY > 50    +0.5")
    print(f"\n  Scanned {len(results)} tickers · "
          f"Skipped {len(skipped)}: {', '.join(skipped) if skipped else 'none'}")
    print(f"{'='*65}\n")

if __name__ == "__main__":
    main()
