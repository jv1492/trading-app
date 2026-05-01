#!/usr/bin/env python3
"""
Stock Technical Analysis Dashboard
Run: streamlit run dashboard.py
"""

import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import plotly.graph_objects as go
from datetime import datetime

# ── Breakout screener universe (~180 liquid US stocks) ────────────────
SCAN_UNIVERSE = [
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA","AVGO","JPM","V",
    "MA","UNH","XOM","LLY","JNJ","WMT","PG","HD","MRK","COST","ABBV","CVX",
    "BAC","NFLX","CRM","AMD","ACN","TMO","PEP","KO","ORCL","MCD","ABT","NKE",
    "DHR","CSCO","TXN","NEE","ADBE","INTC","LIN","UNP","PM","AMGN","LOW","MDT",
    "HON","UPS","RTX","QCOM","ELV","GS","MS","SBUX","INTU","T","DE","AXP",
    "CAT","ISRG","BKNG","GILD","SPGI","BLK","SYK","ADI","REGN","MDLZ","VRTX",
    "SCHW","CB","PLD","CI","AMAT","MU","LRCX","PANW","KLAC","SNPS","CDNS",
    "CME","ICE","MMC","AON","MCO","TRV","ALL","PGR","AFL","MET","PRU",
    "DUK","SO","AEP","SRE","D","EXC","XEL","WEC","ES","ETR",
    "AMT","PLD","CCI","EQIX","PSA","SPG","O","WELL","DLR","AVB",
    "FCX","NEM","GOLD","AA","CLF","X","RS","CMC","NUE","STLD",
    "SLB","HAL","BKR","OXY","COP","DVN","FANG","MRO","APA","EOG",
    "GE","MMM","EMR","ETN","PH","ROK","IR","AME","GWW","FTV",
    "TSM","ASML","SAP","TM","SONY","BABA","JD","PDD","SE","MELI",
    "COIN","HOOD","SQ","PYPL","AFRM","SOFI","NU","ADYEY",
    "UBER","LYFT","DASH","ABNB","BKNG","EXPE","MAR","HLT","H",
    "DIS","CMCSA","WBD","PARA","FOX","NYT","SPOT","TTWO","EA","ATVI",
    "CVS","WBA","MCK","ABC","CAH","HCA","THC","UHS","CNC","MOH",
    "F","GM","STLA","TM","HMC","RIVN","LCID","NIO","LI","XPEV",
    "WFC","C","USB","PNC","TFC","CFG","KEY","RF","FITB","HBAN",
    "PLTR","AI","SNOW","DDOG","NET","ZS","CRWD","OKTA","S","FTNT",
    "ZM","DOCN","DBX","BOX","TWLO","MDB","ESTC","CFLT","GTLB","PATH",
]

# ── Page Config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="Julio's Stock Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    div[data-testid="stMainBlockContainer"] { padding: 3rem 5rem 5rem 2rem !important; }
    div[data-testid="stMainBlockContainer"] h1 { font-size: 2.25rem !important; }
    .metric-card {
        background: #1e1e2e; border-radius: 10px;
        padding: 16px; text-align: center; margin: 4px 0;
    }
    div [data-testid="stMarkdownContainer"] h2 {border: 1px solid red; padding: 0.5rem;}
    .signal-pos  { color: #00c896; font-weight: 700; }
    .signal-neg  { color: #ff4d6d; font-weight: 700; }
    .signal-neu  { color: #a0a0b0; font-weight: 700; }
    .section-hdr { color: #7c7cff; font-size: 0.8rem;
                   letter-spacing: 2px; text-transform: uppercase;
                   margin: 24px 0 8px 0; font-weight: 600; }
    .trade-box   { background: #12122a; border-left: 4px solid #7c7cff;
                   border-radius: 6px; padding: 16px; margin: 8px 0; }
    div[data-testid="stMetricValue"] { font-size: 1.5rem !important; }
    div[data-testid="stMetricLabel"] { font-size: 0.75rem !important;
                                       color: #a0a0b0 !important; }
    section[data-testid="stSidebar"] h1 {margin-top:-3rem; border: 0px solid red; }
    .subtitle { font-size: 1.2rem !important; font-weight: 600; margin-top: -1rem !important; color: inherit; }
</style>
""", unsafe_allow_html=True)

def st_subtitle(text):
    st.markdown(f'<p class="subtitle">{text}</p>', unsafe_allow_html=True)

# ── Indicator Calculations ────────────────────────────────────────────

def fetch(ticker, period, interval):
    df = yf.download(ticker, period=period, interval=interval,
                     progress=False, auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [c.strip() for c in df.columns]
    return df.dropna()

def sma(s, n):   return s.rolling(n).mean()
def ema(s, n):   return s.ewm(span=n, adjust=False).mean()

def rsi(close, n=14):
    d = close.diff()
    g = d.clip(lower=0).rolling(n).mean()
    l = (-d.clip(upper=0)).rolling(n).mean()
    return 100 - (100 / (1 + g / l.replace(0, np.nan)))

def macd(close, f=12, s=26, sig=9):
    line = ema(close, f) - ema(close, s)
    sl   = ema(line, sig)
    return line, sl, line - sl

def stoch(H, L, C, k=14, d=3):
    lo, hi = L.rolling(k).min(), H.rolling(k).max()
    pk = 100 * (C - lo) / (hi - lo).replace(0, np.nan)
    return pk, pk.rolling(d).mean()

def calc_atr(H, L, C, n=20):
    tr = pd.concat([(H-L), (H-C.shift()).abs(), (L-C.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean(), tr

def calc_adx(H, L, C, n=14):
    pdm  = H.diff().clip(lower=0)
    mdm  = (-L.diff()).clip(lower=0)
    _, tr = calc_atr(H, L, C, n)
    trsm = tr.rolling(n).mean()
    pdi  = 100 * pdm.rolling(n).mean() / trsm.replace(0, np.nan)
    mdi  = 100 * mdm.rolling(n).mean() / trsm.replace(0, np.nan)
    dx   = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    return dx.rolling(n).mean()

def bollinger(C, n=20, k=2):
    mid = sma(C, n); std = C.rolling(n).std()
    up, lo = mid + k*std, mid - k*std
    return up, mid, lo, (C - lo) / (up - lo).replace(0, np.nan)

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

def detect_candles(O, H, L, C, label):
    res = []
    if len(C) < 3: return res
    o,h,l,c   = float(O.iloc[-1]),float(H.iloc[-1]),float(L.iloc[-1]),float(C.iloc[-1])
    o2,h2,l2,c2 = float(O.iloc[-2]),float(H.iloc[-2]),float(L.iloc[-2]),float(C.iloc[-2])
    body  = abs(c-o);   body2 = abs(c2-o2)
    rng   = h-l or 1e-9
    uw    = h - max(c,o); lw = min(c,o) - l
    bull,bear,bull2,bear2 = c>o, c<o, c2>o2, c2<o2
    def add(name, det, sent): res.append((label, name, det, sent))
    add("Doji",             rng>0 and body/rng<0.1, "neutral")
    add("Hammer",           lw>2*body and uw<body*.5 and bear2, "bullish")
    add("Shooting Star",    uw>2*body and lw<body*.5 and bull2, "bearish")
    add("Bullish Engulfing",bear2 and bull and o<=c2 and c>=o2 and body>body2, "bullish")
    add("Bearish Engulfing",bull2 and bear and o>=c2 and c<=o2 and body>body2, "bearish")
    add("Bullish Harami",   bear2 and bull and o>c2 and c<o2 and body<body2*.6, "bullish")
    add("Bearish Harami",   bull2 and bear and o<c2 and c>o2 and body<body2*.6, "bearish")
    add("Inside Bar",       h<h2 and l>l2, "neutral")
    add("Dark Cloud Cover", bull2 and bear and o>c2 and c<(o2+c2)/2, "bearish")
    add("Piercing Line",    bear2 and bull and o<l2 and c>(o2+c2)/2, "bullish")
    add("Hanging Man",      lw>2*body and uw<body*.5 and bull2, "bearish")
    add("Inverted Hammer",  uw>2*body and lw<body*.5 and bear2, "bullish")
    return res

def detect_chart_patterns(H, L, C):
    pats = []
    h,l,c = H.values[-60:], L.values[-60:], C.values[-60:]
    n = len(c)
    if n >= 20:
        m1 = int(np.argmin(l[:n//2]));  m2 = int(np.argmin(l[n//2:])) + n//2
        if m2>m1 and abs(l[m1]-l[m2])/l[m1]<0.03 and max(h[m1:m2])>l[m1]*1.05:
            pats.append(("Daily","Double Bottom", True, "bullish"))
        x1 = int(np.argmax(h[:n//2]));  x2 = int(np.argmax(h[n//2:])) + n//2
        if x2>x1 and abs(h[x1]-h[x2])/h[x1]<0.03 and min(l[x1:x2])<h[x1]*.97:
            pats.append(("Daily","Double Top", True, "bearish"))
    if n >= 20:
        pm = (c[-10:].max()-c[-10:].min())/c[-10:].max()
        mv = (c[-20:-10].max()-c[-20:-10].min())/c[-20:-10].max()
        if mv > 0.05 and pm < mv*0.5 and c[-1] > c[-10]:
            pats.append(("Daily","Bull Flag", True, "bullish"))
    if n >= 30:
        if (max(h[-5:])-min(l[-5:]))/c[-1] < (max(h[-30:])-min(l[-30:]))/c[-1]*0.4:
            pats.append(("Daily","Squeeze / Consolidation", True, "neutral"))
    return pats

@st.cache_data(ttl=300)
def run_analysis(ticker, account_size):
    daily  = fetch(ticker, "1y",  "1d")
    weekly = fetch(ticker, "2y",  "1wk")
    spy    = fetch("SPY",  "1y",  "1d")
    if daily.empty: return None

    try:
        info     = yf.Ticker(ticker).info
        co_name  = info.get("longName", ticker)
        sector   = info.get("sector",   "N/A")
        industry = info.get("industry", "N/A")
    except Exception:
        co_name = ticker; sector = industry = "N/A"

    O,H,L,C,V = daily["Open"],daily["High"],daily["Low"],daily["Close"],daily["Volume"]
    cur = float(C.iloc[-1])

    sma20  = sma(C,20);  sma20v  = float(sma20.iloc[-1])
    sma50  = sma(C,50);  sma50v  = float(sma50.iloc[-1])
    sma200 = sma(C,200); sma200v = float(sma200.iloc[-1])
    sma20_sl  = float(sma20.iloc[-1]  - sma20.iloc[-6])
    sma50_sl  = float(sma50.iloc[-1]  - sma50.iloc[-6])
    sma200_sl = float(sma200.iloc[-1] - sma200.iloc[-11])

    rsi_s           = rsi(C);     rsi_v = float(rsi_s.iloc[-1])
    ml, ms, mh      = macd(C);   macd_v = float(ml.iloc[-1]); macd_hist = float(mh.iloc[-1])
    sk, sd          = stoch(H,L,C); stoch_v = float(sk.iloc[-1])
    atr_s, _        = calc_atr(H,L,C); atr_v = float(atr_s.iloc[-1]); atr_pct = atr_v/cur*100
    adx_v           = float(calc_adx(H,L,C).iloc[-1])
    bb_up,_,bb_lo,bb_pct_s = bollinger(C)
    bb_upv = float(bb_up.iloc[-1]); bb_lov = float(bb_lo.iloc[-1]); bb_pct_v = float(bb_pct_s.iloc[-1])

    high_52w = float(H.max()); low_52w = float(L.min())
    rng_pct  = (cur-low_52w)/(high_52w-low_52w)*100 if high_52w!=low_52w else 50
    avg_vol  = float(V.rolling(20).mean().iloc[-1])
    last_vol = float(V.iloc[-1])
    vol_ratio = last_vol/avg_vol if avg_vol else 1
    mo_high  = float(H.iloc[-20:].max()); mo_low = float(L.iloc[-20:].min())

    try:
        cmb   = pd.concat([C.rename("s"), spy["Close"].rename("spy")], axis=1).dropna()
        sr    = float((cmb["s"].iloc[-1]-cmb["s"].iloc[0])/cmb["s"].iloc[0])
        spyr  = float((cmb["spy"].iloc[-1]-cmb["spy"].iloc[0])/cmb["spy"].iloc[0])
        rs_vs = (sr-spyr)*100
        rs_sc = round(min(99,max(1,50+rs_vs*1.2)),1)
    except Exception:
        rs_vs = 0.0; rs_sc = 50.0

    short_t = ("UP"   if cur>sma50v  and sma50_sl >0 and cur>sma20v
               else "DOWN" if cur<sma50v and sma50_sl<0 else "NEUTRAL")
    long_t  = ("UP"   if cur>sma200v and sma200_sl>0
               else "DOWN" if cur<sma200v and sma200_sl<0 else "NEUTRAL")

    support, resistance = find_sr(H,L,C)
    d_candles = detect_candles(O,H,L,C,"Daily")
    w_candles = detect_candles(weekly["Open"],weekly["High"],weekly["Low"],weekly["Close"],"Weekly")
    c_pats    = detect_chart_patterns(H,L,C)
    all_pats  = d_candles + w_candles + c_pats

    entry      = round(float(H.iloc[-10:].max())*1.002, 2)
    near_sup   = support[0] if support else round(cur*0.95, 2)
    stop_loss  = round(near_sup*0.995, 2)
    risk_sh    = entry - stop_loss
    distance   = round((risk_sh/entry)*100, 2) if entry else 0
    shares     = int((account_size*0.01)/risk_sh) if risk_sh>0 else 0
    cap_use    = shares*entry
    cap_pct    = round((cap_use/account_size)*100, 2) if account_size else 0
    target     = resistance[0] if resistance else round(cur*1.10, 2)
    reward     = round(((target-entry)/entry)*100, 2) if entry else 0
    rr         = round(reward/distance, 2) if distance else 0

    # Score
    sc = 0.0
    if cur>sma20v  and sma20_sl >0: sc += 0.75
    if cur>sma50v  and sma50_sl >0: sc += 1.0
    if cur>sma200v and sma200_sl>0: sc += 1.25
    if 45<rsi_v<70:   sc += 0.75
    if rsi_v>50:       sc += 0.25
    if macd_hist>0:    sc += 1.0
    if stoch_v>50:     sc += 0.5
    if adx_v>20:       sc += 0.5
    sc += min(2.0, rs_sc/50.0)
    if avg_vol>200000:       sc += 0.5
    if 0.3<vol_ratio<0.85:   sc += 0.5
    if 0.3<bb_pct_v<0.75:   sc += 0.5
    tech_score = round(min(10.0, sc), 1)

    return dict(
        ticker=ticker, co_name=co_name, sector=sector, industry=industry,
        cur=cur, high_52w=high_52w, low_52w=low_52w, rng_pct=rng_pct,
        mo_high=mo_high, mo_low=mo_low, avg_vol=avg_vol, last_vol=last_vol, vol_ratio=vol_ratio,
        sma20v=sma20v, sma50v=sma50v, sma200v=sma200v,
        sma20_sl=sma20_sl, sma50_sl=sma50_sl, sma200_sl=sma200_sl,
        rsi_v=rsi_v, macd_v=macd_v, macd_hist=macd_hist,
        stoch_v=stoch_v, atr_v=atr_v, atr_pct=atr_pct,
        adx_v=adx_v, bb_upv=bb_upv, bb_lov=bb_lov, bb_pct_v=bb_pct_v,
        rs_sc=rs_sc, rs_vs=rs_vs, short_t=short_t, long_t=long_t,
        tech_score=tech_score, support=support, resistance=resistance,
        all_pats=all_pats,
        entry=entry, stop_loss=stop_loss, near_sup=near_sup,
        risk_sh=risk_sh, distance=distance, shares=shares,
        cap_use=cap_use, cap_pct=cap_pct, target=target, reward=reward, rr=rr,
        close_hist=C, volume_hist=V, rsi_hist=rsi_s, macd_hist_ser=mh,
    )

# ── Market Data Feeds ────────────────────────────────────────────────

@st.cache_data(ttl=300)
def get_most_active():
    try:
        r = requests.get(
            "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved"
            "?scrIds=most_actives&count=15",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=5
        )
        quotes = r.json()["finance"]["result"][0]["quotes"]
        return [
            {
                "symbol": q.get("symbol", ""),
                "price":  q.get("regularMarketPrice", 0),
                "chg":    q.get("regularMarketChangePercent", 0),
            }
            for q in quotes if q.get("symbol") and "-" not in q.get("symbol", "")
        ]
    except Exception:
        return []

@st.cache_data(ttl=300)
def get_trending():
    try:
        r = requests.get(
            "https://query1.finance.yahoo.com/v1/finance/trending/US",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=5
        )
        symbols = [q["symbol"] for q in r.json()["finance"]["result"][0]["quotes"]]
        # Filter out crypto symbols (contain -)
        symbols = [s for s in symbols if "-" not in s][:15]
        tickers = yf.Tickers(" ".join(symbols))
        rows = []
        for sym in symbols:
            try:
                fi    = tickers.tickers[sym].fast_info
                price = getattr(fi, "last_price",     None)
                prev  = getattr(fi, "previous_close", None)
                chg   = ((price - prev) / prev * 100) if price and prev else 0.0
                rows.append({"symbol": sym, "price": price, "chg": chg})
            except Exception:
                pass
        return rows
    except Exception:
        return []

@st.cache_data(ttl=86400)
def run_breakout_scan():
    tickers = list(dict.fromkeys(SCAN_UNIVERSE))
    try:
        raw = yf.download(tickers, period="6mo", interval="1d",
                          group_by="ticker", progress=False,
                          auto_adjust=True, threads=True)
        spy_c = yf.download("SPY", period="6mo", interval="1d",
                             progress=False, auto_adjust=True)["Close"]
    except Exception:
        return []

    results = []
    for sym in tickers:
        try:
            df = raw[sym].dropna() if len(tickers) > 1 else raw.dropna()
            if len(df) < 60: continue
            C, H, L, V = df["Close"], df["High"], df["Low"], df["Volume"]
            cur = float(C.iloc[-1])
            if cur < 20: continue
            avg_vol = float(V.rolling(50).mean().iloc[-1])
            if avg_vol < 500_000: continue

            s20  = C.rolling(20).mean()
            s50  = C.rolling(50).mean()
            s200 = C.rolling(min(200, len(C))).mean()
            s20v, s50v, s200v = float(s20.iloc[-1]), float(s50.iloc[-1]), float(s200.iloc[-1])
            s20_sl = float(s20.iloc[-1] - s20.iloc[-6])
            s50_sl = float(s50.iloc[-1] - s50.iloc[-6])

            d    = C.diff()
            g    = d.clip(lower=0).rolling(14).mean()
            lv   = (-d.clip(upper=0)).rolling(14).mean()
            rsi_v = float(100 - (100 / (1 + g / lv.replace(0, np.nan))).iloc[-1])

            ml   = C.ewm(span=12, adjust=False).mean() - C.ewm(span=26, adjust=False).mean()
            mh_v = float((ml - ml.ewm(span=9, adjust=False).mean()).iloc[-1])

            bb_std = C.rolling(20).std()
            bb_lo  = s20 - 2 * bb_std
            bb_hi  = s20 + 2 * bb_std
            bb_pct = float(((C - bb_lo) / (bb_hi - bb_lo).replace(0, np.nan)).iloc[-1])

            tr      = pd.concat([(H-L),(H-C.shift()).abs(),(L-C.shift()).abs()], axis=1).max(axis=1)
            atr_pct = float(tr.rolling(20).mean().iloc[-1] / cur * 100)

            try:
                cmb  = pd.concat([C.rename("s"), spy_c.rename("spy")], axis=1).dropna()
                sr   = float((cmb["s"].iloc[-1]  - cmb["s"].iloc[0])   / cmb["s"].iloc[0])
                spyr = float((cmb["spy"].iloc[-1] - cmb["spy"].iloc[0]) / cmb["spy"].iloc[0])
                rs_sc = round(min(99, max(1, 50 + (sr - spyr) * 100 * 1.2)), 1)
            except Exception:
                rs_sc = 50.0

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

            results.append({
                "Ticker": sym,
                "Price":  f"${cur:.2f}",
                "Score":  round(sc, 1),
                "RSI":    round(rsi_v, 1),
                "RS":     round(rs_sc, 1),
                "BB %B":  round(bb_pct, 2),
                "ATR %":  round(atr_pct, 2),
                "Trend":  "↑ UP" if trend_up else "—",
                "MACD":   "▲" if mh_v > 0 else "▼",
            })
        except Exception:
            continue

    return sorted(results, key=lambda x: x["Score"], reverse=True)[:25]

@st.cache_data(ttl=3600)
def get_analyst_data(ticker):
    try:
        t   = yf.Ticker(ticker)
        rec = t.recommendations
        apt = t.analyst_price_targets
        cur = t.fast_info.last_price or 0

        if rec is not None and not rec.empty:
            r  = rec.iloc[-1]
            sb = int(r.get("strongBuy",  0))
            b  = int(r.get("buy",        0))
            h  = int(r.get("hold",       0))
            s  = int(r.get("sell",       0))
            ss = int(r.get("strongSell", 0))
        else:
            sb = b = h = s = ss = 0

        total = sb + b + h + s + ss
        return {
            "total":         total,
            "buy_count":     sb + b,
            "hold_count":    h,
            "sell_count":    s + ss,
            "buy_pct":       (sb + b) / total * 100 if total else 0,
            "hold_pct":      h        / total * 100 if total else 0,
            "sell_pct":      (s + ss) / total * 100 if total else 0,
            "high_target":   apt.get("high",   0) if apt else 0,
            "median_target": apt.get("median", 0) if apt else 0,
            "low_target":    apt.get("low",    0) if apt else 0,
            "cur_price":     cur,
        }
    except Exception:
        return None

# ── Sidebar ───────────────────────────────────────────────────────────
if "selected_ticker" not in st.session_state:
    st.session_state["selected_ticker"] = "TSLA"

with st.sidebar:
    st.title("📈 Julio Cesar")
    st_subtitle("Stock Analyzer")
    st.markdown("---")

    # Quick picks — update session state and rerun so text input reflects the value
    st.markdown("**Quick picks:**")
    quick = ["TSLA","TSM","NVDA","AAPL","META","MSFT","AMD","SBLK"]
    cols  = st.columns(2)
    for i, q in enumerate(quick):
        if cols[i % 2].button(q, use_container_width=True, key=f"q_{q}"):
            st.session_state["selected_ticker"] = q
            st.rerun()

    st.markdown("---")
    # Text input bound to session state via key — reflects quick-pick clicks automatically
    ticker_input = st.text_input(
        "Ticker Symbol", key="selected_ticker", max_chars=6
    ).upper().strip()

    account_size = st.number_input("Account Size ($)", min_value=1000, max_value=10_000_000,
                                   value=10_000, step=1000)
    analyze_btn  = st.button("Analyze", type="primary", use_container_width=True)
    st.markdown("---")
    st.caption("Data: Yahoo Finance · Indicators calculated in Python")
    st.caption("⚠ Not financial advice")

# ── Main ──────────────────────────────────────────────────────────────
if analyze_btn or "last_ticker" not in st.session_state:
    st.session_state["last_ticker"] = ticker_input
    st.session_state["account"]     = account_size

ticker = st.session_state.get("last_ticker", "TSLA")
acct   = st.session_state.get("account", 10000)

with st.spinner(f"Fetching & analyzing {ticker}..."):
    d = run_analysis(ticker, acct)

if d is None:
    st.error(f"No data found for **{ticker}**. Check the ticker symbol.")
    st.stop()

# ── Header ────────────────────────────────────────────────────────────
st.title(f"{d['co_name']}  `{d['ticker']}`")
st.caption(f"{d['sector']} / {d['industry']}  ·  Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}")
st.markdown("---")

# ── Top KPIs ──────────────────────────────────────────────────────────
st.markdown('<p class="section-hdr">Current Price | Technical Rating</p>', unsafe_allow_html=True)
k1,k2,k3,k4,k5 = st.columns(5)
score_color = "normal" if d["tech_score"] >= 7 else ("off" if d["tech_score"] < 4 else "normal")
k1.metric("Current Price",   f"${d['cur']:.2f}")
k2.metric("Tech Rating",     f"{d['tech_score']}/10",
          f"{'▲' if d['tech_score']>=7 else '▼'} {'Strong' if d['tech_score']>=7 else 'Weak'}")
k3.metric("Rel. Strength",   f"{d['rs_sc']:.0f}/99",
          f"{d['rs_vs']:+.1f}% vs SPY")
k4.metric("52W Position",    f"{d['rng_pct']:.1f}%",
          f"H ${d['high_52w']:.2f}  L ${d['low_52w']:.2f}")
k5.metric("RSI (14)",        f"{d['rsi_v']:.1f}",
          "Overbought" if d['rsi_v']>70 else ("Oversold" if d['rsi_v']<30 else "Neutral"))

st.markdown("---")

# ── Trade Setup ───────────────────────────────────────────────────────
st.markdown('<p class="section-hdr">Example Trade Setup</p>', unsafe_allow_html=True)
st.warning("⚠ Auto-generated — not financial advice. Always set your own entry and exit points.")

t1,t2,t3,t4,t5,t6 = st.columns(6)
t1.metric("Entry",     f"${d['entry']:.2f}",   "Buy stop above 10d high")
t2.metric("Stop Loss", f"${d['stop_loss']:.2f}", f"Below support ${d['near_sup']:.2f}")
t3.metric("Target",    f"${d['target']:.2f}",  "Nearest resistance")
t4.metric("Distance",  f"{d['distance']:.2f}%", f"${d['risk_sh']:.2f}/share")
t5.metric("Reward",    f"{d['reward']:.2f}%",  f"R/R  1:{d['rr']:.1f}")
t6.metric("Shares",    f"{d['shares']}",
          f"${d['cap_use']:,.0f} ({d['cap_pct']:.1f}% acct)")

# ── Price Chart + Volume ───────────────────────────────────────────────
st.markdown('<p class="section-hdr">Price History (1 Year)</p>', unsafe_allow_html=True)
chart_df = pd.DataFrame({
    "Price":   d["close_hist"],
    "SMA 20":  d["close_hist"].rolling(20).mean(),
    "SMA 50":  d["close_hist"].rolling(50).mean(),
    "SMA 200": d["close_hist"].rolling(200).mean(),
}).dropna()
st.line_chart(chart_df, height=280)

col_vol, col_rsi = st.columns(2)
with col_vol:
    st.markdown('<p class="section-hdr">Volume</p>', unsafe_allow_html=True)
    st.bar_chart(d["volume_hist"], height=150)
with col_rsi:
    st.markdown('<p class="section-hdr">RSI (14)</p>', unsafe_allow_html=True)
    rsi_df = d["rsi_hist"].dropna().to_frame(name="RSI")
    rsi_df["70"] = 70; rsi_df["30"] = 30
    st.line_chart(rsi_df, height=150)

st.markdown("---")

# ── Indicators Table + S/R ────────────────────────────────────────────
col_ind, col_sr = st.columns([3, 1])

with col_ind:
    st.markdown('<p class="section-hdr">Technical Indicator Signals</p>', unsafe_allow_html=True)

    def sig(pos, neg=False):
        if pos:    return "✅ POSITIVE"
        if neg:    return "❌ NEGATIVE"
        return "⚪ NEUTRAL"

    cur = d["cur"]
    rows = [
        ("Long Term Trend",   d["long_t"],
         sig(d["long_t"]=="UP", d["long_t"]=="DOWN"),
         f"Price {'above' if cur>d['sma200v'] else 'below'} SMA200 ({'rising' if d['sma200_sl']>0 else 'falling'})"),
        ("Short Term Trend",  d["short_t"],
         sig(d["short_t"]=="UP", d["short_t"]=="DOWN"),
         f"Price {'above' if cur>d['sma50v'] else 'below'} SMA50"),
        ("Relative Strength", f"{d['rs_sc']:.1f}",
         sig(d["rs_sc"]>70, d["rs_sc"]<40),
         f"Outperforms {d['rs_sc']:.0f}% of market  ({d['rs_vs']:+.1f}% vs SPY)"),
        ("SMA (20)",          f"{'↑' if d['sma20_sl']>0 else '↓'} ${d['sma20v']:.2f}",
         sig(cur>d['sma20v'] and d['sma20_sl']>0, cur<d['sma20v'] and d['sma20_sl']<0),
         f"Price {'above' if cur>d['sma20v'] else 'below'} {'rising' if d['sma20_sl']>0 else 'falling'} SMA(20)"),
        ("SMA (50)",          f"{'↑' if d['sma50_sl']>0 else '↓'} ${d['sma50v']:.2f}",
         sig(cur>d['sma50v'] and d['sma50_sl']>0, cur<d['sma50v'] and d['sma50_sl']<0),
         f"Price {'above' if cur>d['sma50v'] else 'below'} {'rising' if d['sma50_sl']>0 else 'falling'} SMA(50)"),
        ("SMA (200)",         f"{'↑' if d['sma200_sl']>0 else '↓'} ${d['sma200v']:.2f}",
         sig(cur>d['sma200v'] and d['sma200_sl']>0, cur<d['sma200v'] and d['sma200_sl']<0),
         f"Price {'above' if cur>d['sma200v'] else 'below'} {'rising' if d['sma200_sl']>0 else 'falling'} SMA(200)"),
        ("RSI (14)",          f"{d['rsi_v']:.2f}",
         sig(d['rsi_v']>55, d['rsi_v']<40),
         "Overbought" if d['rsi_v']>70 else ("Oversold" if d['rsi_v']<30 else "Neutral momentum")),
        ("MACD (12,26,9)",    f"{d['macd_v']:.3f}",
         sig(d['macd_hist']>0, d['macd_hist']<0),
         f"Histogram {d['macd_hist']:+.3f} — {'bullish' if d['macd_hist']>0 else 'bearish'} momentum"),
        ("Stochastics (14,3)",f"{d['stoch_v']:.2f}",
         sig(d['stoch_v']>55, d['stoch_v']<35),
         "Overbought" if d['stoch_v']>80 else ("Oversold" if d['stoch_v']<20 else "Neutral")),
        ("ATR % (20)",        f"{d['atr_pct']:.2f}%",
         "⚪ " + ("HIGH VOL" if d['atr_pct']>4 else ("MED VOL" if d['atr_pct']>2 else "LOW VOL")),
         f"${d['atr_v']:.2f} avg daily range"),
        ("ADX (14)",          f"{d['adx_v']:.2f}",
         sig(d['adx_v']>25),
         "Strong trend" if d['adx_v']>30 else ("Building" if d['adx_v']>20 else "No clear trend")),
        ("Bollinger %B",      f"{d['bb_pct_v']:.2f}",
         sig(0.3<d['bb_pct_v']<0.75, d['bb_pct_v']>0.95 or d['bb_pct_v']<0.05),
         f"Band  ${d['bb_lov']:.2f} – ${d['bb_upv']:.2f}"),
    ]
    ind_df = pd.DataFrame(rows, columns=["Indicator", "Value", "Signal", "Comment"])
    st.dataframe(ind_df, use_container_width=True, hide_index=True, height=430)

with col_sr:
    st.markdown('<p class="section-hdr">Support & Resistance</p>', unsafe_allow_html=True)
    st.markdown(f"**Current: ${d['cur']:.2f}**")
    st.markdown("**Resistance** ↑")
    for r in d["resistance"][:4]:
        pct = ((r - d["cur"]) / d["cur"]) * 100
        st.markdown(f"&nbsp;&nbsp;`${r:.2f}` +{pct:.1f}%")
    st.markdown("**Support** ↓")
    for s in d["support"][:5]:
        pct = ((s - d["cur"]) / d["cur"]) * 100
        st.markdown(f"&nbsp;&nbsp;`${s:.2f}` {pct:.1f}%")

st.markdown("---")

# ── Analyst Forecasts ────────────────────────────────────────────────
st.markdown('<p class="section-hdr">Analyst Forecasts</p>', unsafe_allow_html=True)
analyst = get_analyst_data(ticker)

if analyst and analyst["total"] > 0:
    fa_left, fa_right = st.columns([1, 1])

    with fa_left:
        st.markdown(f"**{analyst['total']} Analyst Ratings**")
        fig = go.Figure(data=[go.Pie(
            labels=["Buy", "Hold", "Sell"],
            values=[analyst["buy_count"], analyst["hold_count"], analyst["sell_count"]],
            hole=0.6,
            marker_colors=["#00c896", "#ffd166", "#ff4d6d"],
            textinfo="label+percent",
            textfont_size=13,
        )])
        fig.update_layout(
            showlegend=False,
            margin=dict(t=10, b=10, l=10, r=10),
            height=260,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#d0d0e0",
            annotations=[dict(
                text=f"<b>{analyst['buy_pct']:.0f}%</b><br>Buy",
                x=0.5, y=0.5, font_size=16, showarrow=False, font_color="#00c896"
            )],
        )
        st.plotly_chart(fig, use_container_width=True)

    with fa_right:
        st.markdown("**1-Year Price Forecast**")
        cur_p = analyst["cur_price"]
        for label, val in [
            ("High",   analyst["high_target"]),
            ("Median", analyst["median_target"]),
            ("Low",    analyst["low_target"]),
        ]:
            if val and cur_p:
                pct  = (val - cur_p) / cur_p * 100
                sign = "+" if pct >= 0 else ""
                col  = "#00c896" if pct >= 0 else "#ff4d6d"
                st.markdown(
                    f"<div style='background:#1e1e2e;border-radius:8px;padding:12px 16px;"
                    f"margin:6px 0;display:flex;justify-content:space-between;align-items:center'>"
                    f"<div style='color:#a0a0b0;font-size:.85rem'>{label}</div>"
                    f"<div><span style='font-weight:700;font-size:1.1rem'>${val:.2f}</span>"
                    f"&nbsp;<span style='color:{col};font-size:.85rem'>{sign}{pct:.2f}%</span></div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
else:
    st.caption("No analyst data available for this ticker.")

st.markdown("---")

# ── Shared card renderer ──────────────────────────────────────────────
def _pick_ticker(sym):
    st.session_state["selected_ticker"] = sym

def render_stock_cards(rows, key_prefix, yahoo_link=False):
    if not rows:
        st.caption("Could not load data.")
        return
    cols = st.columns(len(rows))
    for i, row in enumerate(rows):
        sym   = row["symbol"]
        price = row["price"]
        chg   = row["chg"]
        color = "#00c896" if chg >= 0 else "#ff4d6d"
        arrow = "▲" if chg >= 0 else "▼"
        cols[i].markdown(
            f"<div style='background:#1e1e2e;border-radius:8px;padding:10px 6px;"
            f"text-align:center;margin:2px'>"
            f"<div style='font-weight:700;font-size:.9rem'>{sym}</div>"
            f"<div style='font-size:.8rem;color:#d0d0e0'>${price:.2f}</div>"
            f"<div style='color:{color};font-size:.8rem;font-weight:600'>"
            f"{arrow} {abs(chg):.2f}%</div></div>",
            unsafe_allow_html=True
        )
        if yahoo_link:
            cols[i].link_button("↗", url=f"https://finance.yahoo.com/quote/{sym}/",
                                 use_container_width=True)
        else:
            cols[i].button("↗", key=f"{key_prefix}_{sym}", help=f"Analyze {sym}",
                           use_container_width=True,
                           on_click=_pick_ticker, args=(sym,))

# ── Most Active ───────────────────────────────────────────────────────
st.markdown('<p class="section-hdr">⚡ Most Active  —  Yahoo Finance</p>', unsafe_allow_html=True)
render_stock_cards(get_most_active(), "ma", yahoo_link=True)

st.markdown("---")

# ── Trending Now ──────────────────────────────────────────────────────
st.markdown('<p class="section-hdr">🔥 Trending Now  —  Yahoo Finance</p>', unsafe_allow_html=True)
render_stock_cards(get_trending(), "tr", yahoo_link=True)

st.markdown("---")

# ── Patterns ──────────────────────────────────────────────────────────
st.markdown('<p class="section-hdr">Candlestick & Chart Patterns</p>', unsafe_allow_html=True)
detected     = [p for p in d["all_pats"] if p[2]]
not_detected = [p for p in d["all_pats"] if not p[2]]

if detected:
    pcols = st.columns(min(4, len(detected)))
    for i, (tf, name, _, sentiment) in enumerate(detected):
        icon = "✅" if sentiment=="bullish" else ("❌" if sentiment=="bearish" else "⚪")
        pcols[i % 4].markdown(
            f"<div style='background:#1e1e2e;border-radius:8px;padding:12px;text-align:center;"
            f"margin:4px'><div style='font-size:1.5rem'>{icon}</div>"
            f"<div style='font-weight:600;font-size:.85rem'>{name}</div>"
            f"<div style='color:#a0a0b0;font-size:.75rem'>{tf} · {sentiment.upper()}</div></div>",
            unsafe_allow_html=True
        )
else:
    st.info("No significant patterns detected on the current bars.")

if not_detected:
    with st.expander("Not active patterns"):
        seen = set()
        unique = [p[1] for p in not_detected if not (p[1] in seen or seen.add(p[1]))]
        st.caption(",  ".join(unique))

st.markdown("---")

# ── Breakout Screener ─────────────────────────────────────────────────
st.markdown('<p class="section-hdr">🔍 Breakout Screener  —  Top Technical Setups</p>', unsafe_allow_html=True)
st.caption(f"Scans ~{len(SCAN_UNIVERSE)} liquid US stocks · Price > $20 · Avg Vol > 500K · Cached daily")

sc_col1, sc_col2 = st.columns([1, 5])
run_scan = sc_col1.button("▶ Run Scan", type="primary", use_container_width=True)
sc_col2.caption("Scores each stock on trend alignment, RSI 50–70, MACD, Bollinger consolidation, and relative strength vs SPY. Takes ~30–60s.")

if run_scan:
    run_breakout_scan.clear()

if run_scan or "scan_done" in st.session_state:
    st.session_state["scan_done"] = True
    with st.spinner("Scanning breakout setups across the universe... (~30–60s on first run)"):
        scan_results = run_breakout_scan()

    if scan_results:
        st.success(f"Top {len(scan_results)} breakout setups found — sorted by score")

        score_col = [r["Score"] for r in scan_results]
        max_score = max(score_col) if score_col else 1

        header = st.columns([1.2, 1, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8])
        for col, label in zip(header, ["Ticker","Price","Score","RSI","RS","BB %B","ATR %","Trend","MACD","Chart"]):
            col.markdown(f"**{label}**")
        st.markdown("<hr style='margin:4px 0'>", unsafe_allow_html=True)

        for r in scan_results:
            score_pct = r["Score"] / max_score
            bar_color = "#00c896" if score_pct > 0.75 else ("#ffd166" if score_pct > 0.5 else "#a0a0b0")
            trend_color = "#00c896" if "UP" in r["Trend"] else "#a0a0b0"
            macd_color  = "#00c896" if r["MACD"] == "▲" else "#ff4d6d"

            row = st.columns([1.2, 1, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8])
            row[0].markdown(f"**{r['Ticker']}**")
            row[1].markdown(r["Price"])
            row[2].markdown(f"<span style='color:{bar_color};font-weight:700'>{r['Score']}</span>", unsafe_allow_html=True)
            row[3].markdown(r["RSI"])
            row[4].markdown(r["RS"])
            row[5].markdown(r["BB %B"])
            row[6].markdown(r["ATR %"])
            row[7].markdown(f"<span style='color:{trend_color}'>{r['Trend']}</span>", unsafe_allow_html=True)
            row[8].markdown(f"<span style='color:{macd_color}'>{r['MACD']}</span>", unsafe_allow_html=True)
            row[9].button("↗", key=f"sc_{r['Ticker']}", use_container_width=True,
                          on_click=_pick_ticker, args=(r["Ticker"],))
    else:
        st.warning("No results returned — try again or check your connection.")
