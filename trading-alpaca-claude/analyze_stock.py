#!/usr/bin/env python3
"""
analyze_stock.py — Full Technical Analysis Report
Usage: python3 analyze_stock.py TICKER
       python3 analyze_stock.py SBLK
       python3 analyze_stock.py TSLA
"""

import sys
import warnings
import numpy as np
from datetime import datetime

warnings.filterwarnings("ignore")

try:
    import yfinance as yf
    import pandas as pd
except ImportError:
    print("Missing library. Run: pip3 install yfinance")
    sys.exit(1)

TICKER       = sys.argv[1].upper() if len(sys.argv) > 1 else "AAPL"
ACCOUNT_SIZE = float(sys.argv[2]) if len(sys.argv) > 2 else 10000
RISK_PCT     = 0.01  # 1% portfolio risk per trade

# ── Data Fetch ───────────────────────────────────────────────────────

def fetch(ticker, period, interval):
    df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [c.strip() for c in df.columns]
    return df.dropna()

# ── Indicators (all manual) ──────────────────────────────────────────

def sma(series, n):
    return series.rolling(n).mean()

def ema(series, n):
    return series.ewm(span=n, adjust=False).mean()

def rsi(close, n=14):
    delta = close.diff()
    gain  = delta.clip(lower=0).rolling(n).mean()
    loss  = (-delta.clip(upper=0)).rolling(n).mean()
    rs    = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def macd(close, fast=12, slow=26, signal=9):
    line   = ema(close, fast) - ema(close, slow)
    sig    = ema(line, signal)
    hist   = line - sig
    return line, sig, hist

def stoch(high, low, close, k=14, d=3):
    lo = low.rolling(k).min()
    hi = high.rolling(k).max()
    pct_k = 100 * (close - lo) / (hi - lo).replace(0, np.nan)
    pct_d = pct_k.rolling(d).mean()
    return pct_k, pct_d

def atr(high, low, close, n=20):
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(n).mean(), tr

def adx(high, low, close, n=14):
    plus_dm  = high.diff().clip(lower=0)
    minus_dm = (-low.diff()).clip(lower=0)
    _, tr_s  = atr(high, low, close, n)
    tr_sm    = tr_s.rolling(n).mean()
    plus_di  = 100 * plus_dm.rolling(n).mean()  / tr_sm.replace(0, np.nan)
    minus_di = 100 * minus_dm.rolling(n).mean() / tr_sm.replace(0, np.nan)
    dx       = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return dx.rolling(n).mean(), plus_di, minus_di

def bollinger(close, n=20, k=2):
    mid   = sma(close, n)
    std   = close.rolling(n).std()
    upper = mid + k * std
    lower = mid - k * std
    pct_b = (close - lower) / (upper - lower).replace(0, np.nan)
    return upper, mid, lower, pct_b

# ── Support / Resistance ─────────────────────────────────────────────

def find_sr(high, low, close, window=8, tol=0.02):
    h = high.values
    l = low.values
    n = len(h)
    pivot_highs, pivot_lows = [], []

    for i in range(window, n - window):
        if h[i] == max(h[i - window: i + window + 1]):
            pivot_highs.append(float(h[i]))
        if l[i] == min(l[i - window: i + window + 1]):
            pivot_lows.append(float(l[i]))

    def cluster(pts):
        if not pts:
            return []
        pts = sorted(pts)
        groups = [[pts[0]]]
        for p in pts[1:]:
            if (p - groups[-1][-1]) / groups[-1][-1] < tol:
                groups[-1].append(p)
            else:
                groups.append([p])
        return [round(sum(g) / len(g), 2) for g in groups if len(g) >= 2]

    cur = float(close.iloc[-1])
    support    = sorted([s for s in cluster(pivot_lows)  if s < cur * 0.999], reverse=True)
    resistance = sorted([r for r in cluster(pivot_highs) if r > cur * 1.001])
    return support, resistance

# ── Candlestick Patterns ─────────────────────────────────────────────

def detect_candles(o_s, h_s, l_s, c_s, label):
    results = []
    if len(c_s) < 3:
        return results

    o, h, l, c   = float(o_s.iloc[-1]), float(h_s.iloc[-1]), float(l_s.iloc[-1]), float(c_s.iloc[-1])
    o2, h2, l2, c2 = float(o_s.iloc[-2]), float(h_s.iloc[-2]), float(l_s.iloc[-2]), float(c_s.iloc[-2])

    body         = abs(c - o)
    body2        = abs(c2 - o2)
    rng          = h - l or 0.0001
    upper_wick   = h - max(c, o)
    lower_wick   = min(c, o) - l
    bull, bear   = c > o, c < o
    bull2, bear2 = c2 > o2, c2 < o2

    def add(name, detected, sentiment):
        results.append((label, name, detected, sentiment))

    add("Doji",             rng > 0 and body / rng < 0.1,                                                         "neutral")
    add("Hammer",           lower_wick > 2 * body and upper_wick < body * 0.5 and bear2,                          "bullish")
    add("Shooting Star",    upper_wick > 2 * body and lower_wick < body * 0.5 and bull2,                          "bearish")
    add("Bullish Engulfing",bear2 and bull and o <= c2 and c >= o2 and body > body2,                               "bullish")
    add("Bearish Engulfing",bull2 and bear and o >= c2 and c <= o2 and body > body2,                               "bearish")
    add("Bullish Harami",   bear2 and bull and o > c2 and c < o2 and body < body2 * 0.6,                          "bullish")
    add("Bearish Harami",   bull2 and bear and o < c2 and c > o2 and body < body2 * 0.6,                          "bearish")
    add("Inside Bar",       h < h2 and l > l2,                                                                     "neutral")
    add("Dark Cloud Cover", bull2 and bear and o > c2 and c < (o2 + c2) / 2,                                      "bearish")
    add("Piercing Line",    bear2 and bull and o < l2 and c > (o2 + c2) / 2,                                      "bullish")
    add("Hanging Man",      lower_wick > 2 * body and upper_wick < body * 0.5 and bull2,                          "bearish")
    add("Inverted Hammer",  upper_wick > 2 * body and lower_wick < body * 0.5 and bear2,                          "bullish")
    return results

# ── Chart Patterns ───────────────────────────────────────────────────

def detect_chart_patterns(high, low, close):
    patterns = []
    h = high.values[-60:]
    l = low.values[-60:]
    c = close.values[-60:]
    n = len(c)

    # Double Bottom: two lows within 3% of each other, separated by a peak
    if n >= 20:
        min1_idx = int(np.argmin(l[:n//2]))
        min2_idx = int(np.argmin(l[n//2:])) + n//2
        if abs(l[min1_idx] - l[min2_idx]) / l[min1_idx] < 0.03:
            mid_high = max(h[min1_idx:min2_idx]) if min2_idx > min1_idx else 0
            if mid_high > l[min1_idx] * 1.05:
                patterns.append(("Daily", "Double Bottom", True, "bullish"))

    # Double Top: two highs within 3% of each other
    if n >= 20:
        max1_idx = int(np.argmax(h[:n//2]))
        max2_idx = int(np.argmax(h[n//2:])) + n//2
        if abs(h[max1_idx] - h[max2_idx]) / h[max1_idx] < 0.03:
            mid_low = min(l[max1_idx:max2_idx]) if max2_idx > max1_idx else 999999
            if mid_low < h[max1_idx] * 0.97:
                patterns.append(("Daily", "Double Top", True, "bearish"))

    # Bull Flag: strong up move then tight consolidation
    if n >= 20:
        pole_high = max(c[-20:-10])
        pole_low  = min(c[-20:-10])
        flag_high = max(c[-10:])
        flag_low  = min(c[-10:])
        pole_move = (pole_high - pole_low) / pole_low if pole_low else 0
        flag_range = (flag_high - flag_low) / flag_high if flag_high else 0
        if pole_move > 0.05 and flag_range < pole_move * 0.5 and c[-1] > c[-10]:
            patterns.append(("Daily", "Bull Flag", True, "bullish"))

    # Squeeze: Bollinger Bands narrowing (low volatility)
    if n >= 30:
        recent_range  = (max(h[-5:])  - min(l[-5:]))  / c[-1]
        earlier_range = (max(h[-30:]) - min(l[-30:])) / c[-1]
        if recent_range < earlier_range * 0.4:
            patterns.append(("Daily", "Squeeze / Consolidation", True, "neutral"))

    return patterns

# ── Scoring ──────────────────────────────────────────────────────────

def score_stock(price, sma20v, sma50v, sma200v, sma20_slope, sma50_slope, sma200_slope,
                rsi_v, macd_hist_v, stoch_kv, adx_v, rs_score, avg_vol, vol_ratio, bb_pct_v):
    s = 0.0
    # Trend vs MAs (3 pts)
    if price > sma20v  and sma20_slope  > 0: s += 0.75
    if price > sma50v  and sma50_slope  > 0: s += 1.0
    if price > sma200v and sma200_slope > 0: s += 1.25
    # Momentum (3 pts)
    if 45 < rsi_v < 70:   s += 0.75
    if rsi_v > 50:         s += 0.25
    if macd_hist_v > 0:    s += 1.0
    if stoch_kv > 50:      s += 0.5
    if adx_v > 20:         s += 0.5
    # Relative strength (2 pts)
    s += min(2.0, rs_score / 50.0)
    # Liquidity + volume (1 pt)
    if avg_vol > 200000:   s += 0.5
    if 0.3 < vol_ratio < 0.85: s += 0.5  # lower vol during consolidation = good
    # Bollinger position (1 pt)
    if 0.3 < bb_pct_v < 0.75: s += 0.5
    return round(min(10.0, s), 1)

# ── Signal Label ─────────────────────────────────────────────────────

def sig_label(condition_pos, condition_neg=None):
    if condition_pos:
        return "POSITIVE", "✅"
    if condition_neg and condition_neg:
        return "NEGATIVE", "❌"
    return "NEUTRAL", "⚪"

# ── Main ─────────────────────────────────────────────────────────────

def main():
    print(f"\n  Fetching data for {TICKER}...")

    daily  = fetch(TICKER, "1y",  "1d")
    weekly = fetch(TICKER, "2y",  "1wk")
    spy    = fetch("SPY",  "1y",  "1d")

    if daily.empty:
        print(f"  ERROR: No data found for {TICKER}. Check the ticker symbol.")
        sys.exit(1)

    try:
        info    = yf.Ticker(TICKER).fast_info
        co_name = getattr(info, 'exchange', TICKER)
        mktcap  = getattr(info, 'market_cap', 0)
    except Exception:
        co_name = TICKER
        mktcap  = 0

    try:
        slow_info = yf.Ticker(TICKER).info
        co_name   = slow_info.get("longName", TICKER)
        sector    = slow_info.get("sector", "N/A")
        industry  = slow_info.get("industry", "N/A")
    except Exception:
        sector = industry = "N/A"

    O  = daily["Open"]
    H  = daily["High"]
    L  = daily["Low"]
    C  = daily["Close"]
    V  = daily["Volume"]

    cur = float(C.iloc[-1])

    # ── Indicators ──────────────────────────────────────────────────
    sma20  = sma(C, 20);   sma20v  = float(sma20.iloc[-1])
    sma50  = sma(C, 50);   sma50v  = float(sma50.iloc[-1])
    sma200 = sma(C, 200);  sma200v = float(sma200.iloc[-1])

    sma20_slope  = float(sma20.iloc[-1]  - sma20.iloc[-6])
    sma50_slope  = float(sma50.iloc[-1]  - sma50.iloc[-6])
    sma200_slope = float(sma200.iloc[-1] - sma200.iloc[-11])

    rsi_s            = rsi(C);       rsi_v    = float(rsi_s.iloc[-1])
    macd_l, macd_sig, macd_h = macd(C)
    macd_val         = float(macd_l.iloc[-1])
    macd_hist_v      = float(macd_h.iloc[-1])
    stoch_k, stoch_d = stoch(H, L, C)
    stoch_kv         = float(stoch_k.iloc[-1])
    stoch_dv         = float(stoch_d.iloc[-1])
    atr_s, _         = atr(H, L, C);  atr_v = float(atr_s.iloc[-1])
    atr_pct          = (atr_v / cur) * 100
    adx_s, pdi, mdi  = adx(H, L, C);  adx_v = float(adx_s.iloc[-1])
    bb_up, bb_mid_s, bb_lo, bb_pct_s = bollinger(C)
    bb_upv   = float(bb_up.iloc[-1])
    bb_lov   = float(bb_lo.iloc[-1])
    bb_pct_v = float(bb_pct_s.iloc[-1])

    high_52w = float(H.max())
    low_52w  = float(L.min())
    rng_pct  = (cur - low_52w) / (high_52w - low_52w) * 100 if high_52w != low_52w else 50

    avg_vol  = float(V.rolling(20).mean().iloc[-1])
    last_vol = float(V.iloc[-1])
    vol_ratio = last_vol / avg_vol if avg_vol else 1

    # Monthly range (last 20 trading days)
    mo_high = float(H.iloc[-20:].max())
    mo_low  = float(L.iloc[-20:].min())

    # Relative strength vs SPY (align on common dates)
    try:
        combined  = pd.concat([C.rename("stock"), spy["Close"].rename("spy")], axis=1).dropna()
        if len(combined) >= 50:
            stock_ret = float((combined["stock"].iloc[-1] - combined["stock"].iloc[0]) / combined["stock"].iloc[0])
            spy_ret   = float((combined["spy"].iloc[-1]   - combined["spy"].iloc[0])   / combined["spy"].iloc[0])
            rs_vs_spy = (stock_ret - spy_ret) * 100
            rs_score  = round(min(99, max(1, 50 + rs_vs_spy * 1.2)), 1)
        else:
            rs_vs_spy, rs_score = 0.0, 50.0
    except Exception:
        rs_vs_spy, rs_score = 0.0, 50.0

    # Trend classification
    short_trend = ("UP"   if cur > sma50v  and sma50_slope  > 0 and cur > sma20v
               else "DOWN" if cur < sma50v  and sma50_slope  < 0
               else "NEUTRAL")
    long_trend  = ("UP"   if cur > sma200v and sma200_slope > 0
               else "DOWN" if cur < sma200v and sma200_slope < 0
               else "NEUTRAL")

    # ── Patterns ────────────────────────────────────────────────────
    daily_candles  = detect_candles(O, H, L, C, "Daily")
    weekly_candles = detect_candles(weekly["Open"], weekly["High"],
                                    weekly["Low"],  weekly["Close"], "Weekly")
    chart_pats     = detect_chart_patterns(H, L, C)
    all_patterns   = daily_candles + weekly_candles + chart_pats
    detected       = [p for p in all_patterns if p[2]]
    not_detected   = [p for p in all_patterns if not p[2]]

    # ── Support / Resistance ─────────────────────────────────────────
    support, resistance = find_sr(H, L, C)

    # ── Trade Setup ──────────────────────────────────────────────────
    entry       = round(float(H.iloc[-10:].max()) * 1.002, 2)
    nearest_sup = support[0] if support else round(cur * 0.95, 2)
    stop_loss   = round(nearest_sup * 0.995, 2)
    risk_share  = entry - stop_loss
    distance    = round((risk_share / entry) * 100, 2) if entry else 0
    shares      = int((ACCOUNT_SIZE * RISK_PCT) / risk_share) if risk_share > 0 else 0
    capital_use = shares * entry
    capital_pct = round((capital_use / ACCOUNT_SIZE) * 100, 2) if ACCOUNT_SIZE else 0

    # Nearest resistance for target
    target = resistance[0] if resistance else round(cur * 1.10, 2)
    reward = round(((target - entry) / entry) * 100, 2) if entry else 0
    rr     = round(reward / distance, 2) if distance else 0

    # ── Technical Score ──────────────────────────────────────────────
    tech_score = score_stock(cur, sma20v, sma50v, sma200v,
                             sma20_slope, sma50_slope, sma200_slope,
                             rsi_v, macd_hist_v, stoch_kv, adx_v,
                             rs_score, avg_vol, vol_ratio, bb_pct_v)

    # ── Print Report ─────────────────────────────────────────────────
    W   = 68
    bar = "═" * W
    thn = "─" * W

    def trend_icon(t):
        return "✅ POSITIVE" if t == "UP" else ("❌ NEGATIVE" if t == "DOWN" else "⚪ NEUTRAL")

    filled = "●" * int(tech_score)
    empty  = "○" * (10 - int(tech_score))

    print(f"\n{bar}")
    print(f"  {co_name} ({TICKER})")
    print(f"  {sector} / {industry}")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{bar}")

    print(f"\n  TECHNICAL RATING  {tech_score}/10  [{filled}{empty}]")
    print(f"  Relative Strength {rs_score:.1f} — outperforms {rs_score:.0f}% of market")

    print(f"\n  {thn}")
    print(f"  PRICE SNAPSHOT")
    print(f"  {thn}")
    print(f"  Current Price     : ${cur:.2f}")
    print(f"  52-Week High      : ${high_52w:.2f}   ({((cur/high_52w)-1)*100:+.1f}%)")
    print(f"  52-Week Low       : ${low_52w:.2f}   ({((cur/low_52w)-1)*100:+.1f}%)")
    range_label = "(upper ✓)" if rng_pct > 70 else ("(lower)" if rng_pct < 30 else "(mid)")
    print(f"  52-Week Position  : {rng_pct:.1f}%  {range_label}")
    print(f"  Monthly Range     : ${mo_low:.2f} – ${mo_high:.2f}")
    print(f"  Avg Volume (20d)  : {avg_vol:,.0f}")
    print(f"  Last Volume       : {last_vol:,.0f}  ({vol_ratio:.2f}x avg)")

    print(f"\n  {thn}")
    print(f"  TECHNICAL INDICATOR SIGNALS")
    print(f"  {thn}")
    print(f"  {'Indicator':<28} {'Value':>10}  Signal       Comment")
    print(f"  {'─'*28} {'─'*10}  {'─'*11} {'─'*22}")

    def row(name, val_str, icon, sig, comment):
        print(f"  {name:<28} {val_str:>10}  {icon} {sig:<10} {comment}")

    row("Long Term Trend",    long_trend,
        "✅" if long_trend=="UP" else ("❌" if long_trend=="DOWN" else "⚪"),
        trend_icon(long_trend).split()[1],
        f"Price {'above' if cur>sma200v else 'below'} SMA200 ({'rising' if sma200_slope>0 else 'falling'})")

    row("Short Term Trend",   short_trend,
        "✅" if short_trend=="UP" else ("❌" if short_trend=="DOWN" else "⚪"),
        trend_icon(short_trend).split()[1],
        f"Price {'above' if cur>sma50v else 'below'} SMA50 ({'rising' if sma50_slope>0 else 'falling'})")

    row("Relative Strength",  f"{rs_score:.1f}",
        "✅" if rs_score>70 else ("❌" if rs_score<40 else "⚪"),
        "POSITIVE" if rs_score>70 else ("NEGATIVE" if rs_score<40 else "NEUTRAL"),
        f"vs SPY: stock {'+' if rs_vs_spy>0 else ''}{rs_vs_spy:.1f}%")

    for label, val, thresh_up, slope, ref in [
        ("SMA(20)",  sma20v,  sma20v,  sma20_slope,  "SMA(20)"),
        ("SMA(50)",  sma50v,  sma50v,  sma50_slope,  "SMA(50)"),
        ("SMA(200)", sma200v, sma200v, sma200_slope, "SMA(200)"),
    ]:
        up = cur > val and slope > 0
        dn = cur < val and slope < 0
        row(f"SMA({ref.split('(')[1]}",
            f"{'↑' if slope>0 else '↓'} ${val:.2f}",
            "✅" if up else ("❌" if dn else "⚪"),
            "POSITIVE" if up else ("NEGATIVE" if dn else "NEUTRAL"),
            f"Price {'above' if cur>val else 'below'} {'rising' if slope>0 else 'falling'} {ref}")

    row("RSI(14)",            f"{rsi_v:.2f}",
        "✅" if rsi_v>55 else ("❌" if rsi_v<40 else "⚪"),
        "POSITIVE" if rsi_v>55 else ("NEGATIVE" if rsi_v<40 else "NEUTRAL"),
        "Overbought" if rsi_v>70 else ("Oversold" if rsi_v<30 else "Neutral momentum"))

    row("MACD(12,26,9)",      f"{macd_val:.3f}",
        "✅" if macd_hist_v>0 else "❌",
        "POSITIVE" if macd_hist_v>0 else "NEGATIVE",
        f"Histogram {'+' if macd_hist_v>0 else ''}{macd_hist_v:.3f} — {'bullish' if macd_hist_v>0 else 'bearish'} momentum")

    row("Stochastics(14,3)",  f"{stoch_kv:.2f}",
        "✅" if stoch_kv>55 else ("❌" if stoch_kv<35 else "⚪"),
        "POSITIVE" if stoch_kv>55 else ("NEGATIVE" if stoch_kv<35 else "NEUTRAL"),
        "Overbought" if stoch_kv>80 else ("Oversold" if stoch_kv<20 else "Neutral"))

    vol_label = "HIGH VOLATILITY" if atr_pct>4 else ("MED VOLATILITY" if atr_pct>2 else "LOW VOLATILITY")
    row("ATR%(20)",           f"{atr_pct:.2f}%",
        "⚪", vol_label, f"${atr_v:.2f} avg true range per day")

    row("ADX(14)",            f"{adx_v:.2f}",
        "✅" if adx_v>25 else "⚪",
        "POSITIVE" if adx_v>25 else "NEUTRAL",
        "Strong trend" if adx_v>30 else ("Trend building" if adx_v>20 else "No clear trend"))

    row("Bollinger %B",       f"{bb_pct_v:.2f}",
        "✅" if 0.3<bb_pct_v<0.75 else ("❌" if bb_pct_v>0.95 or bb_pct_v<0.05 else "⚪"),
        "POSITIVE" if 0.3<bb_pct_v<0.75 else ("NEGATIVE" if bb_pct_v>0.95 else "NEUTRAL"),
        f"Band: ${bb_lov:.2f} – ${bb_upv:.2f}")

    # ── Support / Resistance ─────────────────────────────────────────
    print(f"\n  {thn}")
    print(f"  SUPPORT & RESISTANCE  (current: ${cur:.2f})")
    print(f"  {thn}")

    if resistance:
        print(f"  Resistance:")
        for r in resistance[:4]:
            pct = ((r - cur) / cur) * 100
            print(f"    ${r:<8.2f}  +{pct:.1f}% away")
    print()
    if support:
        print(f"  Support:")
        for s in support[:5]:
            pct = ((s - cur) / cur) * 100
            print(f"    ${s:<8.2f}  {pct:.1f}% away")

    # ── Candlestick & Chart Patterns ─────────────────────────────────
    print(f"\n  {thn}")
    print(f"  CANDLESTICK & CHART PATTERNS")
    print(f"  {thn}")

    if detected:
        print(f"  Detected ({len(detected)}):")
        for tf, pname, _, sentiment in detected:
            icon = "✅" if sentiment=="bullish" else ("❌" if sentiment=="bearish" else "⚪")
            print(f"    {icon}  {pname:<28} ({tf})  {sentiment.upper()}")
    else:
        print(f"  No significant patterns on current bars.")

    if not_detected:
        names = ", ".join(p[1] for p in not_detected[:10])
        print(f"\n  Not active: {names}")

    # ── Trade Setup ──────────────────────────────────────────────────
    print(f"\n  {thn}")
    print(f"  EXAMPLE TRADE SETUP")
    print(f"  ⚠  Auto-generated — not financial advice. Set your own entry & exit.")
    print(f"  {thn}")
    print(f"  Entry       : ${entry:.2f}   (buy stop above 10-day high)")
    print(f"  Stop Loss   : ${stop_loss:.2f}  (just below nearest support ${nearest_sup:.2f})")
    print(f"  Target      : ${target:.2f}  (nearest resistance)")
    print(f"  Distance    : {distance:.2f}%  (${risk_share:.2f} risk/share)")
    print(f"  Reward      : {reward:.2f}%  → Risk/Reward  1:{rr:.1f}")
    print(f"  Shares      : {shares}  (1% risk on ${ACCOUNT_SIZE:,.0f} account)")
    print(f"  Capital     : ${capital_use:,.2f}  ({capital_pct:.1f}% of account)")
    print(f"\n{bar}\n")


if __name__ == "__main__":
    main()
