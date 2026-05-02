#!/usr/bin/env python3
"""
AI Companies Breakout Screener — standalone Streamlit page
Opened from the dashboard sidebar as a new browser tab.
"""

import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

st.set_page_config(
    page_title="AI Screener",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    div[data-testid="stMainBlockContainer"] { padding: 3rem 5rem 5rem 2rem !important; }
    div[data-testid="stMainBlockContainer"] h1 { font-size: 2.25rem !important; }
    .signal-pos { color: #00c896; font-weight: 700; }
    .signal-neg { color: #ff4d6d; font-weight: 700; }
    .section-hdr { color: #7c7cff; font-size: 0.8rem;
                   letter-spacing: 2px; text-transform: uppercase;
                   margin: 24px 0 8px 0; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

AI_UNIVERSE = [
    # AI infrastructure / chips
    "NVDA", "AMD",  "MRVL", "AVGO", "SMCI", "DELL", "ANET",
    # Hyperscalers (major AI platforms)
    "MSFT", "GOOGL","META", "AMZN", "AAPL", "ORCL", "IBM",
    # AI software / SaaS
    "PLTR", "CRM",  "NOW",  "ADBE", "PATH", "GTLB",
    # AI data / cloud infrastructure
    "SNOW", "MDB",  "DDOG", "NET",  "TSLA",
    # Pure-play / emerging AI
    "AI",   "SOUN", "BBAI", "UPST", "RXRX",
]

@st.cache_data(ttl=86400)
def run_ai_scan():
    try:
        raw   = yf.download(AI_UNIVERSE, period="6mo", interval="1d",
                            group_by="ticker", progress=False,
                            auto_adjust=True, threads=True)
        spy_c = yf.download("SPY", period="6mo", interval="1d",
                            progress=False, auto_adjust=True)["Close"].squeeze()
    except Exception:
        return []

    results = []
    for sym in AI_UNIVERSE:
        try:
            df = raw[sym].dropna()
            if len(df) < 60:
                continue
            C = df["Close"].squeeze(); H = df["High"].squeeze(); L = df["Low"].squeeze()
            cur = float(C.iloc[-1])

            s20  = C.rolling(20).mean(); s50 = C.rolling(50).mean()
            s200 = C.rolling(min(200, len(C))).mean()
            s20v, s50v, s200v = float(s20.iloc[-1]), float(s50.iloc[-1]), float(s200.iloc[-1])
            s20_sl = float(s20.iloc[-1] - s20.iloc[-6])
            s50_sl = float(s50.iloc[-1] - s50.iloc[-6])

            d     = C.diff()
            g     = d.clip(lower=0).rolling(14).mean()
            lv    = (-d.clip(upper=0)).rolling(14).mean().replace(0, np.nan)
            rsi_v = float((100 - (100 / (1 + g / lv))).iloc[-1])

            ml   = C.ewm(span=12, adjust=False).mean() - C.ewm(span=26, adjust=False).mean()
            mh_v = float((ml - ml.ewm(span=9, adjust=False).mean()).iloc[-1])

            bb_std = C.rolling(20).std()
            bb_pct = float(((C - (s20 - 2*bb_std)) / (4*bb_std).replace(0, np.nan)).iloc[-1])

            tr      = pd.concat([(H-L),(H-C.shift()).abs(),(L-C.shift()).abs()], axis=1).max(axis=1)
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

            results.append({
                "Ticker": sym, "Price": f"${cur:.2f}", "Score": round(sc, 1),
                "RSI": round(rsi_v, 1), "RS": round(rs_sc, 1),
                "BB %B": round(bb_pct, 2), "ATR %": round(atr_pct, 2),
                "Trend": "↑ UP" if trend_up else "—", "MACD": "▲" if mh_v > 0 else "▼",
            })
        except Exception:
            continue

    return sorted(results, key=lambda x: x["Score"], reverse=True)[:10]


# ── Header ────────────────────────────────────────────────────────────
col_title, col_back = st.columns([4, 1])
with col_title:
    st.title("🤖 AI Companies Screener")
    st.caption("Top 10 AI-focused stocks ranked by breakout score  ·  same criteria as main dashboard")
with col_back:
    try:
        _host = st.context.headers.get("host") or st.context.headers.get("Host") or "localhost:8501"
        _base = f"https://{_host}" if "streamlit.app" in _host else f"http://{_host}"
    except Exception:
        _base = "http://localhost:8501"
    st.markdown(
        f'<a href="{_base}" target="_self" style="display:block;padding:0.4rem 0.75rem;'
        'border-radius:0.5rem;border:1px solid rgba(250,250,250,0.2);'
        'text-decoration:none;color:inherit;text-align:center;font-size:0.875rem">'
        '← Back to Dashboard</a>',
        unsafe_allow_html=True,
    )

st.markdown("---")

# ── Refresh control ───────────────────────────────────────────────────
_, c2 = st.columns([5, 1])
with c2:
    if st.button("🔄 Refresh", use_container_width=True):
        run_ai_scan.clear()
        st.rerun()

with st.spinner("Scanning 30 AI companies..."):
    rows = run_ai_scan()

if not rows:
    st.warning("Could not load data. Try refreshing.")
    st.stop()

# ── Results table ─────────────────────────────────────────────────────
st.markdown('<p class="section-hdr">Top 10 by Breakout Score</p>', unsafe_allow_html=True)

hdr = st.columns([0.4, 1.2, 1, 1.2, 0.8, 0.8, 0.8, 0.8, 0.9, 0.7])
for col, lbl in zip(hdr, ["#", "Ticker", "Price", "Score", "RSI", "RS", "BB %B", "ATR %", "Trend", "MACD"]):
    col.markdown(f"**{lbl}**")
st.markdown("<hr style='margin:4px 0'>", unsafe_allow_html=True)

max_sc = max(r["Score"] for r in rows) or 1
for i, r in enumerate(rows, 1):
    pct   = r["Score"] / max_sc
    color = "#00c896" if pct > 0.75 else ("#ffd166" if pct > 0.5 else "#a0a0b0")
    t_col = "#00c896" if "UP" in r["Trend"] else "#a0a0b0"
    m_col = "#00c896" if r["MACD"] == "▲" else "#ff4d6d"
    bar   = "█" * int(r["Score"]) + "░" * (10 - int(r["Score"]))

    row = st.columns([0.4, 1.2, 1, 1.2, 0.8, 0.8, 0.8, 0.8, 0.9, 0.7])
    row[0].markdown(f"{i}")
    row[1].markdown(f"**{r['Ticker']}**")
    row[2].markdown(r["Price"])
    row[3].markdown(
        f"<span style='color:{color};font-weight:700'>{r['Score']}  {bar}</span>",
        unsafe_allow_html=True,
    )
    row[4].markdown(str(r["RSI"]))
    row[5].markdown(str(r["RS"]))
    row[6].markdown(str(r["BB %B"]))
    row[7].markdown(str(r["ATR %"]))
    row[8].markdown(f"<span style='color:{t_col}'>{r['Trend']}</span>", unsafe_allow_html=True)
    row[9].markdown(f"<span style='color:{m_col}'>{r['MACD']}</span>", unsafe_allow_html=True)

st.markdown("---")

# ── Universe breakdown ────────────────────────────────────────────────
st.markdown('<p class="section-hdr">Universe  (30 tickers)</p>', unsafe_allow_html=True)
c1, c2, c3, c4, c5 = st.columns(5)
groups = {
    "⚙️ Chips / Infra":    ["NVDA","AMD","MRVL","AVGO","SMCI","DELL","ANET"],
    "☁️ Hyperscalers":     ["MSFT","GOOGL","META","AMZN","AAPL","ORCL","IBM"],
    "🧠 AI Software":      ["PLTR","CRM","NOW","ADBE","PATH","GTLB"],
    "🗄️ Data / Cloud":     ["SNOW","MDB","DDOG","NET","TSLA"],
    "🚀 Pure-play AI":     ["AI","SOUN","BBAI","UPST","RXRX"],
}
for col, (label, tickers) in zip([c1, c2, c3, c4, c5], groups.items()):
    col.markdown(f"**{label}**")
    for t in tickers:
        col.caption(t)

st.markdown("---")

# ── Scoring legend ────────────────────────────────────────────────────
st.markdown('<p class="section-hdr">Scoring Criteria  (max 11.5 pts)</p>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    st.markdown("""
| Criterion | Points |
|-----------|--------|
| Trend up (SMA20/50 rising & price above) | +2.0 |
| Price above SMA200 | +1.0 |
| RSI 50–70 (sweet spot) | +2.0 |
| RSI 45–50 (near zone) | +0.5 |
| MACD histogram > 0 | +1.5 |
""")
with c2:
    st.markdown("""
| Criterion | Points |
|-----------|--------|
| BB %B 0.40–0.75 (coiling, room to run) | +2.0 |
| BB %B 0.75–0.88 (upper zone) | +0.5 |
| ATR% < 2.5% (low volatility) | +1.0 |
| RS vs SPY > 60 | +1.5 |
| RS vs SPY > 50 | +0.5 |
""")

st.caption(f"Cached for 24 hours  ·  Last run: {datetime.now().strftime('%Y-%m-%d %H:%M')}  ·  ⚠ Not financial advice")
