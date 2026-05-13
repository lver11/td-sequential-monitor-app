"""
TD Sequential – Streamlit Dashboard
=====================================
Signaux DeMark 9 & 13 sur actions, ETF, taux d'intérêt, commodities.
Déployez sur Streamlit Community Cloud : https://share.streamlit.io
"""

from __future__ import annotations
import warnings
warnings.filterwarnings("ignore")

import textwrap
from datetime import datetime
from pathlib import Path

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# ──────────────────────────────────────────────
#  CONFIG (modifiable via sidebar)
# ──────────────────────────────────────────────
UNIVERSE = {
    "Actions US": {
        "AAPL" : "Apple Inc.",
        "MSFT" : "Microsoft",
        "GOOGL": "Alphabet",
        "AMZN" : "Amazon",
        "NVDA" : "Nvidia",
        "META" : "Meta Platforms",
        "TSLA" : "Tesla",
        "AMD"  : "AMD",
        "NFLX" : "Netflix",
        "JPM"  : "JPMorgan",
        "GS"   : "Goldman Sachs",
    },
    "ETF": {
        "SPY"  : "SPDR S&P 500",
        "QQQ"  : "Nasdaq-100",
        "IWM"  : "Russell 2000",
        "EEM"  : "MSCI Emerging Markets",
        "TLT"  : "iShares 20Y Treasury",
        "LQD"  : "iShares Investment Grade",
        "GLD"  : "SPDR Gold",
        "SLV"  : "iShares Silver",
        "XLE"  : "Energy Sector",
        "XLF"  : "Financial Sector",
        "XLK"  : "Tech Sector",
        "VTI"  : "Vanguard Total Market",
    },
    "Taux d'intérêt": {
        "^IRX" : "3 mois (T-Bill)",
        "^FVX" : "5 ans",
        "^TNX" : "10 ans",
        "^TYX" : "30 ans",
    },
    "Commodities": {
        "CL=F" : "Pétrole brut (Brent)",
        "GC=F" : "Or",
        "SI=F" : "Argent",
        "HG=F" : "Cuivre",
        "NG=F" : "Gaz naturel",
        "ZC=F" : "Maïs",
        "ZS=F" : "Soja",
        "ZW=F" : "Blé",
        "PL=F" : "Platine",
        "CT=F" : "Coton",
        "KC=F" : "Café",
        "SB=F" : "Sucre",
        "CC=F" : "Cacao",
    },
}

# ──────────────────────────────────────────────
#  TD SEQUENTIAL ENGINE
# ──────────────────────────────────────────────
def fetch_data(ticker: str, period: str = "3mo", interval: str = "1d") -> pd.DataFrame:
    try:
        df = yf.download(ticker, period=period, interval=interval,
                          auto_adjust=True, progress=False, threads=True)
        return df.dropna()
    except Exception:
        return pd.DataFrame()


def compute_td_sequential(df: pd.DataFrame) -> pd.DataFrame:
    n = len(df)
    close = df["Close"].values.astype(float)
    td_buy = np.zeros(n, dtype=float)
    td_sell = np.zeros(n, dtype=float)
    cb_buy = np.zeros(n, dtype=int)
    cb_sell = np.zeros(n, dtype=int)
    exhaust = np.zeros(n, dtype=int)

    phase = "none"
    buy_count, sell_count = 0, 0

    for i in range(1, n):
        if close[i] < close[i - 4]:
            new_phase = "buy"
        elif close[i] > close[i - 4]:
            new_phase = "sell"
        else:
            new_phase = phase

        if new_phase != phase:
            if new_phase == "buy" and phase in ("sell", "none"):
                buy_count, sell_count = 1, 0
            elif new_phase == "sell" and phase in ("buy", "none"):
                sell_count, buy_count = 1, 0
            elif new_phase == "buy":
                buy_count += 1
            else:
                sell_count += 1
            phase = new_phase
        else:
            if phase == "buy":
                buy_count += 1
            elif phase == "sell":
                sell_count += 1

        if phase == "buy" and 0 < buy_count <= 13:
            td_buy[i] = buy_count
        if phase == "sell" and 0 < sell_count <= 13:
            td_sell[i] = sell_count

        # Count 13 validation
        if phase == "buy" and buy_count == 13:
            ok = all(close[j] <= close[i - 13 - 4] for j in range(i - 12, i + 1) if j >= 0)
            if ok:
                cb_buy[i] = 1

        if phase == "sell" and sell_count == 13:
            ok = all(close[j] >= close[i - 13 - 4] for j in range(i - 12, i + 1) if j >= 0)
            if ok:
                cb_sell[i] = 1

        # Exhaustion
        if phase == "buy" and i >= 4 and close[i] > close[i - 4]:
            exhaust[i] = 1
            phase, sell_count, buy_count = "sell", 1, 0
        elif phase == "sell" and i >= 4 and close[i] < close[i - 4]:
            exhaust[i] = 1
            phase, buy_count, sell_count = "buy", 1, 0

    result = df.copy()
    result["td_buy_setup"]  = td_buy
    result["td_sell_setup"] = td_sell
    result["td_count_buy"]  = cb_buy
    result["td_count_sell"] = cb_sell
    result["td_exhaustion"] = exhaust
    return result


def extract_signals(df: pd.DataFrame, ticker: str, name: str = "") -> list:
    signals = []
    n = len(df)
    if n < 15:
        return signals

    close = df["Close"].values.astype(float)

    for i in range(13, n):
        date = df.index[i]
        ci = close[i]

        if df["td_count_buy"].iloc[i]:
            signals.append({"ticker": ticker, "name": name,
                            "date": date.strftime("%Y-%m-%d"),
                            "type": "BUY Count 13", "price": round(ci, 2), "strength": "STRONG"})
        elif df["td_count_sell"].iloc[i]:
            signals.append({"ticker": ticker, "name": name,
                            "date": date.strftime("%Y-%m-%d"),
                            "type": "SELL Count 13", "price": round(ci, 2), "strength": "STRONG"})
        elif df["td_buy_setup"].iloc[i] == 9:
            signals.append({"ticker": ticker, "name": name,
                            "date": date.strftime("%Y-%m-%d"),
                            "type": "BUY Setup 9", "price": round(ci, 2), "strength": "MEDIUM"})
        elif df["td_sell_setup"].iloc[i] == 9:
            signals.append({"ticker": ticker, "name": name,
                            "date": date.strftime("%Y-%m-%d"),
                            "type": "SELL Setup 9", "price": round(ci, 2), "strength": "MEDIUM"})

    return signals


def scan_universe(categories: list, interval: str, lookback: int) -> pd.DataFrame:
    rows = []
    progress_bar = st.progress(0)
    progress_text = st.empty()

    all_targets = {}
    for cat in categories:
        if cat in UNIVERSE:
            all_targets.update(UNIVERSE[cat])

    total = len(all_targets)
    for idx, (ticker, name) in enumerate(all_targets.items()):
        progress_text.text(f"Scanning {ticker}... ({idx + 1}/{total})")
        progress_bar.progress((idx + 1) / total)

        period_map = {"1d": "3mo", "1wk": "6mo", "1mo": "2y"}
        period = period_map.get(interval, "3mo")

        df = fetch_data(ticker, period=period, interval=interval)
        if df.empty:
            continue

        if len(df) > lookback:
            df = df.tail(lookback)

        df_td = compute_td_sequential(df)
        sigs  = extract_signals(df_td, ticker, name)
        rows.extend(sigs)

    progress_bar.empty()
    progress_text.empty()

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows).sort_values(["type", "ticker"])


# ──────────────────────────────────────────────
#  STREAMLIT UI
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="TD Sequential Monitor",
    page_icon="📊",
    layout="wide",
)

# ── Header ───────────────────────────────────
st.markdown("""
<style>
  .main-header { font-size: 2rem; font-weight: 800; color: #4A90E2; margin-bottom: 0.1rem; }
  .subtitle   { color: #8b949e; font-size: 0.9rem; margin-bottom: 1.5rem; }
  footer, .stApp > header { visibility: hidden; }
  .stApp > div { background: #0d1117; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">📊 TD Sequential Monitor</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Signaux DeMark 9 & 13 — Actions, ETF, Taux, Commodities</div>', unsafe_allow_html=True)

# ── Sidebar controls ─────────────────────────
st.sidebar.header("Configuration")

all_cats = list(UNIVERSE.keys())
selected_cats = st.sidebar.multiselect(
    "Categories a scanner",
    all_cats,
    default=["Actions US", "ETF", "Commodities"],
)

interval = st.sidebar.selectbox("Intervalle", ["1d", "1wk", "1mo"], index=0)
lookback = st.sidebar.slider("Lookback (barres)", 20, 200, 60)

st.sidebar.markdown("---")
st.sidebar.markdown("**Parametres DeMark**")
st.sidebar.info("Setup: 9 barres | Count 13: 13 barres | Close override: 4 barres")

st.sidebar.markdown("---")
st.sidebar.markdown("**Legende**")
st.sidebar.markdown("🟢 **STRONG** = Count 13 confirme\n🟡 **MEDIUM** = Setup 9 en attente")

# ── Run button ────────────────────────────────
run = st.sidebar.button("Lancer le scan", type="primary", use_container_width=True)

if not run:
    st.info("Configure les parametres et clique sur **Lancer le scan** pour commencer.")
    st.stop()

if not selected_cats:
    st.error("Selectionne au moins une categorie.")
    st.stop()

# ── Scan ──────────────────────────────────────
scan_info = st.empty()
scan_info.info(f"Scan en cours sur {len(selected_cats)} categorie(s) — {interval} — {lookback} barres")

df_signals = scan_universe(selected_cats, interval, lookback)
scan_info.empty()

# ── Results ───────────────────────────────────
if df_signals.empty:
    st.warning("Aucun signal trouve. Essaie d'augmenter le lookback ou de changer d'intervalle.")
else:
    buy_count    = len(df_signals[df_signals["type"].str.contains("BUY",  na=False)])
    sell_count   = len(df_signals[df_signals["type"].str.contains("SELL", na=False)])
    count13      = len(df_signals[df_signals["type"].str.contains("13",  na=False)])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total signaux", len(df_signals))
    col2.metric("BUY",          buy_count)
    col3.metric("SELL",         sell_count)
    col4.metric("Count 13 forts", count13)

    st.markdown("---")
    st.subheader(f"Signaux — {len(df_signals)} trouve(s)")

    # Group by type
    for signal_type in ["BUY Count 13", "SELL Count 13", "BUY Setup 9", "SELL Setup 9"]:
        sub = df_signals[df_signals["type"] == signal_type]
        if sub.empty:
            continue

        icon  = "🟢" if "BUY" in signal_type else "🔴"
        color = "#3fb950" if "BUY" in signal_type else "#f85149"
        badge = "STRONG" if "13" in signal_type else "MEDIUM"
        badge_bg = "#238636" if badge == "STRONG" else "#9e6a03"

        with st.expander(f"{icon} {signal_type}  [{len(sub)}]", expanded=True):
            for _, row in sub.iterrows():
                badge_html = f'<span style="background:{badge_bg};color:#fff;padding:2px 8px;border-radius:4px;font-size:0.75rem;font-weight:700">{badge}</span>'
                st.markdown(
                    f"""
                    <div style="background:#161b22;border-left:4px solid {color};padding:0.6rem 1rem;border-radius:6px;margin-bottom:0.4rem;display:flex;justify-content:space-between;align-items:center">
                      <div>
                        <span style="font-weight:700;font-size:1rem">{row['ticker']}</span>
                        <span style="color:#8b949e;margin-left:0.5rem">{row['name']}</span>
                      </div>
                      <div style="text-align:right">
                        <span style="font-size:1.1rem;font-weight:700">${row['price']:.2f}</span>
                        <span style="color:#8b949e;margin-left:1rem">{row['date']}</span>
                        {badge_html}
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # ── Export CSV ────────────────────────────
    csv = df_signals.to_csv(index=False).encode("utf-8")
    ts  = datetime.now().strftime("%Y%m%d_%H%M")
    st.download_button(
        "Telecharger CSV",
        csv,
        f"td_sequential_{ts}.csv",
        mime="text/csv",
        use_container_width=True,
    )

st.sidebar.markdown("---")
st.caption(f"Mis a jour: {datetime.now().strftime('%d/%m/%Y %H:%M')} | Donnees: Yahoo Finance")