"""
2___Charts.py — Keshav's Screen
TradingView-style interactive charts with 50+ indicators.
Opens as plain candlestick — all indicators opt-in.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.nse_stocks import NSE_STOCKS_EXTENDED, INDICES, yf_ticker
from utils.data_fetcher import get_ohlcv, get_fundamentals, get_news
from utils.technical_analysis import (
    sma, ema, wma, hma, vwap_rolling,
    rsi, macd, stochastic, williams_r, cci, roc, mfi, tsi,
    atr, bollinger_bands, keltner_channel, donchian_channel,
    historical_volatility, chaikin_volatility,
    adx_dmi, aroon, supertrend, parabolic_sar, ichimoku,
    obv, ad_line, chaikin_money_flow, volume_oscillator, ease_of_movement,
    pivot_points, fibonacci_levels, find_support_resistance,
    detect_patterns, add_all_indicators, get_ta_signal_summary,
)
from utils.styles import inject_css, section_label, PLOTLY_LAYOUT, CHART_COLORS

st.set_page_config(
    page_title="Charts — Keshav's Screen",
    page_icon="K",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()

st.markdown('<h2 style="margin-bottom:2px;">Interactive Charts</h2>', unsafe_allow_html=True)
st.markdown(
    '<p style="color:var(--t3);font-size:.85rem;">'
    'Candlestick · Heikin-Ashi · Line · Area · 50+ TA indicators · Signal summary</p>',
    unsafe_allow_html=True,
)

# ─── SYMBOL & TIMEFRAME ──────────────────────────────────────────────────────
all_syms = list(NSE_STOCKS_EXTENDED.keys())
all_idx  = list(INDICES.keys())
bucket   = st.session_state.get("bucket", [])
# Bucket first, then stocks, then indices — deduped
seen = set()
all_opts = []
for s in (bucket + all_syms + all_idx):
    if s not in seen:
        all_opts.append(s)
        seen.add(s)

c1, c2, c3, c4 = st.columns([3, 2, 2, 3])
with c1:
    default_idx = all_opts.index("RELIANCE") if "RELIANCE" in all_opts else 0
    symbol = st.selectbox("Symbol / Index", all_opts, index=default_idx)
with c2:
    timeframe = st.selectbox("Timeframe", [
        "1Y (1d)", "3M (1d)", "6M (1d)", "2Y (1d)", "Today (5m)",
        "5D (15m)", "1M (1h)", "5Y (1wk)", "Max (1mo)", "Intraday 1m",
    ])
with c3:
    chart_type = st.selectbox("Chart Type", ["Candlestick", "Heikin-Ashi", "Line", "Area", "OHLC"])
with c4:
    compare = st.multiselect("Compare (normalised %)", all_syms, max_selections=4)

TF_MAP = {
    "Today (5m)":    ("5d",  "5m"),
    "5D (15m)":      ("1mo", "15m"),
    "1M (1h)":       ("3mo", "1h"),
    "3M (1d)":       ("6mo", "1d"),
    "6M (1d)":       ("1y",  "1d"),
    "1Y (1d)":       ("2y",  "1d"),
    "2Y (1d)":       ("2y",  "1d"),
    "5Y (1wk)":      ("5y",  "1wk"),
    "Max (1mo)":     ("max", "1mo"),
    "Intraday 1m":   ("1d",  "1m"),
}
period, interval = TF_MAP.get(timeframe, ("2y", "1d"))

# ─── INDICATOR PANEL (all off by default — Issue #8 fix) ─────────────────────
with st.expander("Indicators & Overlays", expanded=False):
    ic1, ic2, ic3, ic4, ic5 = st.columns(5)

    with ic1:
        st.markdown("**Moving Averages**")
        s20  = st.checkbox("SMA 20")           # was value=True → now False
        s50  = st.checkbox("SMA 50")           # was value=True → now False
        s200 = st.checkbox("SMA 200")          # was value=True → now False
        e20  = st.checkbox("EMA 20")
        e50  = st.checkbox("EMA 50")
        h20  = st.checkbox("HMA 20")
        vw   = st.checkbox("VWAP")             # was value=True → now False
        st.markdown("**Trend**")
        _st  = st.checkbox("Supertrend")
        psar = st.checkbox("Parabolic SAR")
        ichi = st.checkbox("Ichimoku Cloud")

    with ic2:
        st.markdown("**Momentum**")
        _rsi  = st.checkbox("RSI")             # was value=True → now False
        rsi_p = st.number_input("RSI period", 2, 50, 14, key="rsi_p")
        _macd = st.checkbox("MACD")            # was value=True → now False
        _stoch= st.checkbox("Stochastic")
        _wr   = st.checkbox("Williams %R")
        _cci  = st.checkbox("CCI")
        _roc  = st.checkbox("ROC")
        _mfi  = st.checkbox("MFI")
        _tsi  = st.checkbox("TSI")

    with ic3:
        st.markdown("**Volatility**")
        _bb  = st.checkbox("Bollinger Bands")  # was value=True → now False
        _kc  = st.checkbox("Keltner Channel")
        _dc  = st.checkbox("Donchian Channel")
        _atr = st.checkbox("ATR")
        _hv  = st.checkbox("Historical Vol")
        st.markdown("**ADX / Trend**")
        _adx  = st.checkbox("ADX / DMI")       # was value=True → now False
        _aroon= st.checkbox("Aroon")

    with ic4:
        st.markdown("**Volume**")
        _vol = st.checkbox("Volume")           # was value=True → now False
        _obv = st.checkbox("OBV")
        _cmf = st.checkbox("CMF")
        _adl = st.checkbox("A/D Line")
        _vo  = st.checkbox("Vol Oscillator")
        _eom = st.checkbox("Ease of Movement")

    with ic5:
        st.markdown("**S&R / Levels**")
        _sr  = st.checkbox("Support & Resistance")  # was value=True → now False
        _piv = st.checkbox("Pivot Points")           # was value=True → now False
        piv_m= st.selectbox("Pivot Method", ["standard", "fibonacci", "camarilla"])
        _fib = st.checkbox("Fibonacci Levels")
        _pat = st.checkbox("Candlestick Patterns")   # was value=True → now False

# ─── FETCH DATA ───────────────────────────────────────────────────────────────
ticker = yf_ticker(symbol)
is_idx = symbol in INDICES

with st.spinner(f"Loading {symbol}..."):
    df = get_ohlcv(ticker, period, interval)

if df is None or df.empty:
    st.error(f"No data for **{symbol}** — period={period}, interval={interval}. Try a different timeframe.")
    st.stop()

# ─── BUILD SUBPANEL LIST ──────────────────────────────────────────────────────
panels = []
if _vol:   panels.append("Volume")
if _rsi:   panels.append("RSI")
if _macd:  panels.append("MACD")
if _adx:   panels.append("ADX")
if _stoch: panels.append("Stoch")
if _wr:    panels.append("Williams")
if _cci:   panels.append("CCI")
if _roc:   panels.append("ROC")
if _mfi:   panels.append("MFI")
if _tsi:   panels.append("TSI")
if _obv:   panels.append("OBV")
if _cmf:   panels.append("CMF")
if _adl:   panels.append("ADL")
if _vo:    panels.append("VolOsc")
if _atr:   panels.append("ATR")
if _hv:    panels.append("HV")
if _aroon: panels.append("Aroon")

n_rows = 1 + len(panels)
h_w = [0.60] + [0.40 / max(len(panels), 1)] * len(panels)
tot = sum(h_w)
h_w = [x / tot for x in h_w]

fig = make_subplots(
    rows=n_rows, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.016,
    row_heights=h_w,
    subplot_titles=[symbol] + panels,
)

# ─── PRICE PANEL ─────────────────────────────────────────────────────────────
UP   = "#16A34A"
DOWN = "#DC2626"


def _draw_candles(df, row=1):
    if chart_type == "Candlestick":
        fig.add_trace(go.Candlestick(
            x=df.index, open=df["Open"], high=df["High"],
            low=df["Low"], close=df["Close"],
            name=symbol,
            increasing_line_color=UP,    decreasing_line_color=DOWN,
            increasing_fillcolor=UP,     decreasing_fillcolor=DOWN,
        ), row=row, col=1)

    elif chart_type == "Heikin-Ashi":
        ha = df.copy()
        ha["HA_C"] = (df["Open"] + df["High"] + df["Low"] + df["Close"]) / 4
        ha["HA_O"] = [(df["Open"].iloc[0] + df["Close"].iloc[0]) / 2] * len(ha)
        for i in range(1, len(ha)):
            ha.loc[ha.index[i], "HA_O"] = (ha["HA_O"].iloc[i-1] + ha["HA_C"].iloc[i-1]) / 2
        ha["HA_H"] = ha[["HA_O", "HA_C", "High"]].max(axis=1)
        ha["HA_L"] = ha[["HA_O", "HA_C", "Low"]].min(axis=1)
        fig.add_trace(go.Candlestick(
            x=ha.index, open=ha["HA_O"], high=ha["HA_H"],
            low=ha["HA_L"], close=ha["HA_C"],
            name="HA", increasing_line_color=UP, decreasing_line_color=DOWN,
            increasing_fillcolor=UP, decreasing_fillcolor=DOWN,
        ), row=row, col=1)

    elif chart_type in ("Line", "Area"):
        lp = float(df["Close"].iloc[-1])
        fp = float(df["Close"].iloc[0])
        lc = UP if lp >= fp else DOWN
        fc = "rgba(22,163,74,.08)" if lp >= fp else "rgba(220,38,38,.08)"
        fig.add_trace(go.Scatter(
            x=df.index, y=df["Close"], mode="lines",
            line=dict(color=lc, width=1.8),
            fill="tozeroy" if chart_type == "Area" else None,
            fillcolor=fc, name=symbol,
        ), row=row, col=1)

    else:  # OHLC
        fig.add_trace(go.Ohlc(
            x=df.index, open=df["Open"], high=df["High"],
            low=df["Low"], close=df["Close"],
            name=symbol,
            increasing_line_color=UP, decreasing_line_color=DOWN,
        ), row=row, col=1)


_draw_candles(df)

# ─── OVERLAYS ────────────────────────────────────────────────────────────────
MA_COLORS = {
    "s20": "#D97706", "s50": "#1D4ED8", "s200": "#7C3AED",
    "e20": "#EA580C", "e50": "#BE185D", "h20": "#0E7490",
    "vw":  "#DC2626",
}

if s20:  fig.add_trace(go.Scatter(x=df.index, y=sma(df,20),  mode="lines", line=dict(color=MA_COLORS["s20"],  width=1.2), name="SMA20"),  row=1, col=1)
if s50:  fig.add_trace(go.Scatter(x=df.index, y=sma(df,50),  mode="lines", line=dict(color=MA_COLORS["s50"],  width=1.4), name="SMA50"),  row=1, col=1)
if s200: fig.add_trace(go.Scatter(x=df.index, y=sma(df,200), mode="lines", line=dict(color=MA_COLORS["s200"], width=1.6), name="SMA200"), row=1, col=1)
if e20:  fig.add_trace(go.Scatter(x=df.index, y=ema(df,20),  mode="lines", line=dict(color=MA_COLORS["e20"],  width=1,  dash="dash"), name="EMA20"), row=1, col=1)
if e50:  fig.add_trace(go.Scatter(x=df.index, y=ema(df,50),  mode="lines", line=dict(color=MA_COLORS["e50"],  width=1.2,dash="dash"), name="EMA50"), row=1, col=1)
if h20:  fig.add_trace(go.Scatter(x=df.index, y=hma(df,20),  mode="lines", line=dict(color=MA_COLORS["h20"],  width=1,  dash="dot"),  name="HMA20"), row=1, col=1)
if vw and "Volume" in df.columns:
    fig.add_trace(go.Scatter(x=df.index, y=vwap_rolling(df,20), mode="lines",
                              line=dict(color=MA_COLORS["vw"], width=1.2, dash="dot"), name="VWAP"), row=1, col=1)

if _bb:
    bu, bm, bl, _, _ = bollinger_bands(df)
    fig.add_trace(go.Scatter(x=df.index, y=bu, mode="lines",
                              line=dict(color="rgba(100,149,237,.5)", width=.8),
                              name="BB U", showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=bl, mode="lines",
                              line=dict(color="rgba(100,149,237,.5)", width=.8),
                              fill="tonexty", fillcolor="rgba(100,149,237,.06)",
                              name="Bollinger"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=bm, mode="lines",
                              line=dict(color="rgba(100,149,237,.4)", width=.6, dash="dot"),
                              name="BB Mid", showlegend=False), row=1, col=1)

if _kc:
    ku, km, kl = keltner_channel(df)
    fig.add_trace(go.Scatter(x=df.index, y=ku, mode="lines",
                              line=dict(color="rgba(234,88,12,.4)", width=.8),
                              showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=kl, mode="lines",
                              line=dict(color="rgba(234,88,12,.4)", width=.8),
                              fill="tonexty", fillcolor="rgba(234,88,12,.04)",
                              name="Keltner"), row=1, col=1)

if _dc:
    du, dm, dl = donchian_channel(df)
    fig.add_trace(go.Scatter(x=df.index, y=du, mode="lines",
                              line=dict(color="rgba(22,163,74,.4)", width=.8),
                              showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=dl, mode="lines",
                              line=dict(color="rgba(22,163,74,.4)", width=.8),
                              fill="tonexty", fillcolor="rgba(22,163,74,.04)",
                              name="Donchian"), row=1, col=1)

if ichi:
    ti, ki, sa, sb, ch = ichimoku(df)
    fig.add_trace(go.Scatter(x=df.index, y=ti, mode="lines", line=dict(color="#EF4444", width=.9), name="Tenkan"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=ki, mode="lines", line=dict(color="#3B82F6", width=1.1), name="Kijun"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=sa, mode="lines", line=dict(color="rgba(22,163,74,.25)", width=.7), showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=sb, mode="lines", line=dict(color="rgba(220,38,38,.25)", width=.7),
                              fill="tonexty", fillcolor="rgba(100,200,100,.06)", name="Cloud"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=ch, mode="lines", line=dict(color="rgba(124,58,237,.4)", width=.8), name="Chikou"), row=1, col=1)

if _st:
    stv, std = supertrend(df)
    bi = df.index[std == 1];  bv = stv[std == 1]
    ri = df.index[std == -1]; rv = stv[std == -1]
    fig.add_trace(go.Scatter(x=bi, y=bv, mode="markers", marker=dict(color=UP,   size=3), name="ST Bull"), row=1, col=1)
    fig.add_trace(go.Scatter(x=ri, y=rv, mode="markers", marker=dict(color=DOWN, size=3), name="ST Bear"), row=1, col=1)

if psar:
    sv, st2 = parabolic_sar(df)
    fig.add_trace(go.Scatter(x=df.index[st2==1],  y=sv[st2==1],  mode="markers",
                              marker=dict(color=UP,   size=4, symbol="triangle-up"),   name="SAR Bull"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index[st2==-1], y=sv[st2==-1], mode="markers",
                              marker=dict(color=DOWN, size=4, symbol="triangle-down"), name="SAR Bear"), row=1, col=1)

if _sr and len(df) > 40:
    sr = find_support_resistance(df)
    for lv in sr.get("resistance", [])[-4:]:
        fig.add_hline(y=lv, line=dict(color="rgba(220,38,38,.4)", width=.8, dash="dash"), row=1, col=1)
    for lv in sr.get("support", [])[-4:]:
        fig.add_hline(y=lv, line=dict(color="rgba(22,163,74,.4)", width=.8, dash="dash"), row=1, col=1)

if _piv and len(df) > 5:
    pp = pivot_points(df, piv_m)
    pc = {"PP":"#D97706","R1":"#EA580C","R2":"#DC2626","R3":"#991B1B","S1":"#0E7490","S2":"#16A34A","S3":"#166534"}
    for lbl, val in pp.items():
        fig.add_hline(y=val, line=dict(color=pc.get(lbl,"#888"), width=.7, dash="dot"),
                      annotation_text=f"{lbl}:{val:.1f}",
                      annotation_position="right",
                      annotation_font=dict(size=8, color=pc.get(lbl,"#888")),
                      row=1, col=1)

if _fib and len(df) > 20:
    fibs = fibonacci_levels(df)
    for lbl, val in fibs.items():
        if lbl not in ("High", "Low"):
            fig.add_hline(y=val, line=dict(color="rgba(217,119,6,.25)", width=.6, dash="dot"),
                          annotation_text=lbl, annotation_position="right",
                          annotation_font=dict(size=8, color="rgba(217,119,6,.6)"),
                          row=1, col=1)

if _pat and chart_type == "Candlestick":
    pats = detect_patterns(df)
    for pname, pmask in pats.items():
        last_idx = df.index[pmask]
        if len(last_idx) > 0:
            last = last_idx[-1]
            lv = float(df.loc[last, "High"]) * 1.006
            fig.add_annotation(x=last, y=lv, text=pname[:4], showarrow=False,
                               font=dict(size=8, color="#D97706"), row=1, col=1)

# ─── COMPARISON OVERLAYS ─────────────────────────────────────────────────────
if compare:
    b0 = float(df["Close"].iloc[0])
    for i, csym in enumerate(compare):
        cdf = get_ohlcv(f"{csym}.NS", period, interval)
        if cdf is not None and not cdf.empty:
            nc = cdf["Close"] / float(cdf["Close"].iloc[0]) * 100
            fig.add_trace(go.Scatter(
                x=cdf.index, y=nc, mode="lines",
                line=dict(color=CHART_COLORS[(i + 2) % len(CHART_COLORS)], width=1.2, dash="dot"),
                name=f"{csym} (norm)",
            ), row=1, col=1)

# ─── SUBPANELS ────────────────────────────────────────────────────────────────
row_n = 2
for panel in panels:

    if panel == "Volume" and "Volume" in df.columns:
        vc = [UP if df["Close"].iloc[i] >= df["Open"].iloc[i] else DOWN for i in range(len(df))]
        fig.add_trace(go.Bar(x=df.index, y=df["Volume"], marker_color=vc, showlegend=False, name="Vol",
                              opacity=0.7), row=row_n, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["Volume"].rolling(20).mean(), mode="lines",
                                  line=dict(color="#D97706", width=.9), name="Avg Vol"), row=row_n, col=1)

    elif panel == "RSI":
        rv = rsi(df, int(rsi_p))
        fig.add_trace(go.Scatter(x=df.index, y=rv, mode="lines",
                                  line=dict(color="#7C3AED", width=1.4), name=f"RSI({int(rsi_p)})"),
                      row=row_n, col=1)
        fig.add_hline(y=70, line=dict(color=DOWN, width=.7, dash="dash"), row=row_n, col=1)
        fig.add_hline(y=30, line=dict(color=UP,   width=.7, dash="dash"), row=row_n, col=1)
        fig.add_hrect(y0=70, y1=100, fillcolor="rgba(220,38,38,.04)",  line_width=0, row=row_n, col=1)
        fig.add_hrect(y0=0,  y1=30,  fillcolor="rgba(22,163,74,.04)", line_width=0, row=row_n, col=1)
        fig.update_yaxes(range=[0, 100], row=row_n, col=1)

    elif panel == "MACD":
        ml, sl2, mh = macd(df)
        mc = [UP if v >= 0 else DOWN for v in mh.fillna(0)]
        fig.add_trace(go.Bar(x=df.index, y=mh, marker_color=mc, showlegend=False, opacity=.7), row=row_n, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=ml, mode="lines", line=dict(color="#1D4ED8", width=1.2), name="MACD"),   row=row_n, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=sl2, mode="lines", line=dict(color=DOWN, width=1),      name="Signal"), row=row_n, col=1)
        fig.add_hline(y=0, line=dict(color="#8896B0", width=.5), row=row_n, col=1)

    elif panel == "ADX":
        adxv, dip, din = adx_dmi(df)
        fig.add_trace(go.Scatter(x=df.index, y=adxv, mode="lines", line=dict(color="#D97706", width=1.4), name="ADX"),  row=row_n, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=dip,  mode="lines", line=dict(color=UP,   width=1),        name="+DI"),  row=row_n, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=din,  mode="lines", line=dict(color=DOWN, width=1),        name="-DI"),  row=row_n, col=1)
        fig.add_hline(y=25, line=dict(color="#8896B0", width=.7, dash="dash"), row=row_n, col=1)

    elif panel == "Stoch":
        sk, sd = stochastic(df)
        fig.add_trace(go.Scatter(x=df.index, y=sk, mode="lines", line=dict(color="#1D4ED8", width=1.2), name="%K"), row=row_n, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=sd, mode="lines", line=dict(color=DOWN,     width=1),   name="%D"), row=row_n, col=1)
        fig.add_hline(y=80, line=dict(color=DOWN, width=.7, dash="dash"), row=row_n, col=1)
        fig.add_hline(y=20, line=dict(color=UP,   width=.7, dash="dash"), row=row_n, col=1)
        fig.update_yaxes(range=[0, 100], row=row_n, col=1)

    elif panel == "Williams":
        wr_v = williams_r(df)
        fig.add_trace(go.Scatter(x=df.index, y=wr_v, mode="lines", line=dict(color="#7C3AED", width=1.2), name="W%R"), row=row_n, col=1)
        fig.add_hline(y=-20, line=dict(color=DOWN, width=.7, dash="dash"), row=row_n, col=1)
        fig.add_hline(y=-80, line=dict(color=UP,   width=.7, dash="dash"), row=row_n, col=1)
        fig.update_yaxes(range=[-100, 0], row=row_n, col=1)

    elif panel == "CCI":
        cci_v = cci(df)
        fig.add_trace(go.Scatter(x=df.index, y=cci_v, mode="lines", line=dict(color="#1D4ED8", width=1.2), name="CCI"), row=row_n, col=1)
        fig.add_hline(y=100,  line=dict(color=DOWN, width=.7, dash="dash"), row=row_n, col=1)
        fig.add_hline(y=-100, line=dict(color=UP,   width=.7, dash="dash"), row=row_n, col=1)

    elif panel == "ROC":
        rv2 = roc(df)
        rc = [UP if v >= 0 else DOWN for v in rv2.fillna(0)]
        fig.add_trace(go.Bar(x=df.index, y=rv2, marker_color=rc, name="ROC", opacity=.7), row=row_n, col=1)
        fig.add_hline(y=0, line=dict(color="#8896B0", width=.5), row=row_n, col=1)

    elif panel == "MFI" and "Volume" in df.columns:
        mfi_v = mfi(df)
        fig.add_trace(go.Scatter(x=df.index, y=mfi_v, mode="lines", line=dict(color="#D97706", width=1.2), name="MFI"), row=row_n, col=1)
        fig.add_hline(y=80, line=dict(color=DOWN, width=.7, dash="dash"), row=row_n, col=1)
        fig.add_hline(y=20, line=dict(color=UP,   width=.7, dash="dash"), row=row_n, col=1)
        fig.update_yaxes(range=[0, 100], row=row_n, col=1)

    elif panel == "TSI":
        tsi_v = tsi(df)
        fig.add_trace(go.Scatter(x=df.index, y=tsi_v, mode="lines", line=dict(color="#BE185D", width=1.2), name="TSI"), row=row_n, col=1)
        fig.add_hline(y=0, line=dict(color="#8896B0", width=.5), row=row_n, col=1)

    elif panel == "OBV" and "Volume" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=obv(df), mode="lines", line=dict(color=UP, width=1), name="OBV"), row=row_n, col=1)

    elif panel == "CMF" and "Volume" in df.columns:
        cv = chaikin_money_flow(df)
        cc = [UP if v >= 0 else DOWN for v in cv.fillna(0)]
        fig.add_trace(go.Bar(x=df.index, y=cv, marker_color=cc, name="CMF", opacity=.7), row=row_n, col=1)
        fig.add_hline(y=0, line=dict(color="#8896B0", width=.5), row=row_n, col=1)

    elif panel == "ADL" and "Volume" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=ad_line(df), mode="lines", line=dict(color="#0E7490", width=1), name="A/D"), row=row_n, col=1)

    elif panel == "VolOsc" and "Volume" in df.columns:
        vo_v = volume_oscillator(df)
        vc2 = [UP if v >= 0 else DOWN for v in vo_v.fillna(0)]
        fig.add_trace(go.Bar(x=df.index, y=vo_v, marker_color=vc2, name="VolOsc", opacity=.7), row=row_n, col=1)
        fig.add_hline(y=0, line=dict(color="#8896B0", width=.5), row=row_n, col=1)

    elif panel == "ATR":
        fig.add_trace(go.Scatter(x=df.index, y=atr(df), mode="lines", line=dict(color="#EA580C", width=1.2), name="ATR"), row=row_n, col=1)

    elif panel == "HV":
        fig.add_trace(go.Scatter(x=df.index, y=historical_volatility(df), mode="lines",
                                  line=dict(color="#BE185D", width=1.2), name="HV(20)"), row=row_n, col=1)

    elif panel == "Aroon":
        au, ad2 = aroon(df)
        fig.add_trace(go.Scatter(x=df.index, y=au,  mode="lines", line=dict(color=UP,   width=1.2), name="Aroon Up"), row=row_n, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=ad2, mode="lines", line=dict(color=DOWN, width=1.2), name="Aroon Dn"), row=row_n, col=1)
        fig.update_yaxes(range=[0, 100], row=row_n, col=1)

    row_n += 1

# ─── CHART LAYOUT ─────────────────────────────────────────────────────────────
chart_h = max(500, n_rows * 170)
fig.update_layout(
    height=chart_h,
    paper_bgcolor="#FFFFFF",
    plot_bgcolor="#F7F9FD",
    font=dict(color="#5A6A88", family="DM Sans, sans-serif", size=10),
    margin=dict(l=0, r=90, t=28, b=8),
    legend=dict(
        bgcolor="rgba(255,255,255,0.95)",
        bordercolor="#DDE3EF",
        borderwidth=1,
        font=dict(size=9, color="#2D3A52"),
        x=.01, y=.99, xanchor="left", yanchor="top",
    ),
    xaxis_rangeslider_visible=False,
    hovermode="x unified",
    hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="#DDE3EF",
                    font=dict(size=11, color="#0F172A", family="JetBrains Mono, monospace")),
)
for i in range(1, n_rows + 1):
    fig.update_xaxes(showgrid=True, gridcolor="#EAEEf8", gridwidth=1,
                     zeroline=False, linecolor="#DDE3EF", color="#5A6A88", row=i, col=1)
    fig.update_yaxes(showgrid=True, gridcolor="#EAEEf8", gridwidth=1,
                     zeroline=False, linecolor="#DDE3EF", color="#5A6A88",
                     side="right", row=i, col=1)
if n_rows > 1:
    fig.update_xaxes(showticklabels=False, row=1, col=1)

# Add subplot title styling
for ann in fig.layout.annotations:
    ann.font.color = "#5A6A88"
    ann.font.size  = 10

st.plotly_chart(fig, use_container_width=True)

# ─── SIGNAL SUMMARY ───────────────────────────────────────────────────────────
st.markdown("---")
section_label("TECHNICAL SIGNAL SUMMARY")

try:
    dfi = add_all_indicators(df)
    sig = get_ta_signal_summary(dfi)

    overall = sig.get("overall", "NEUTRAL")
    oc_map = {
        "STRONG BUY":  ("#16A34A", "#F0FDF4", "#BBF7D0"),
        "BUY":         ("#15803D", "#F0FDF4", "#86EFAC"),
        "NEUTRAL":     ("#D97706", "#FFFBEB", "#FCD34D"),
        "SELL":        ("#DC2626", "#FFF0F0", "#FCA5A5"),
        "STRONG SELL": ("#991B1B", "#FFF0F0", "#F87171"),
    }
    ov_txt, ov_bg, ov_bdr = oc_map.get(overall, ("#5A6A88","#F7F9FD","#DDE3EF"))

    sc1, sc2, sc3, sc4, sc5 = st.columns([2, 1, 1, 1, 4])
    with sc1:
        st.markdown(f"""
        <div style="background:{ov_bg};border:2px solid {ov_bdr};border-radius:10px;
                    padding:16px;text-align:center;">
          <div style="color:var(--t3);font-size:.68rem;font-weight:700;
                      text-transform:uppercase;letter-spacing:1px;">Overall Signal</div>
          <div style="color:{ov_txt};font-size:1.4rem;font-weight:800;
                      margin:6px 0;font-family:'DM Sans',sans-serif;">{overall}</div>
          <div style="color:var(--t4);font-size:.7rem;">
            {sig.get('buy',0)+sig.get('sell',0)+sig.get('neutral',0)} indicators
          </div>
        </div>""", unsafe_allow_html=True)

    for col, cnt, lbl, clr, bg, bdr in [
        (sc2, sig.get('buy',    0), "BUY",     "#16A34A", "#F0FDF4", "#BBF7D0"),
        (sc3, sig.get('neutral',0), "NEUTRAL", "#D97706", "#FFFBEB", "#FCD34D"),
        (sc4, sig.get('sell',   0), "SELL",    "#DC2626", "#FFF0F0", "#FCA5A5"),
    ]:
        with col:
            st.markdown(f"""
            <div style="background:{bg};border:1px solid {bdr};border-radius:8px;
                        padding:12px;text-align:center;">
              <div style="color:{clr};font-size:1.4rem;font-weight:700;
                          font-family:'JetBrains Mono',monospace;">{cnt}</div>
              <div style="color:var(--t3);font-size:.7rem;font-weight:600;
                          text-transform:uppercase;">{lbl}</div>
            </div>""", unsafe_allow_html=True)

    with sc5:
        for sd in sig.get("details", []):
            sig_str = sd.get("signal", "")
            c = UP if sig_str == "BUY" else DOWN if sig_str == "SELL" else "#8896B0"
            v = f" ({sd['value']})" if sd.get("value") is not None else ""
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;padding:4px 10px;
                        background:var(--bg3);border-radius:4px;margin-bottom:3px;
                        border:1px solid var(--bdr);">
              <span style="color:var(--t2);font-size:.8rem;">{sd.get('indicator','')}</span>
              <span style="color:{c};font-size:.8rem;font-weight:600;">{sig_str}{v}</span>
            </div>""", unsafe_allow_html=True)
except Exception:
    st.info("Computing technical signals...")

# ─── FUNDAMENTALS & NEWS ──────────────────────────────────────────────────────
if not is_idx:
    st.markdown("---")
    tab_f, tab_n = st.tabs(["Fundamentals", "News"])

    with tab_f:
        with st.spinner("Loading fundamentals..."):
            fund = get_fundamentals(symbol)
        if fund:
            r1, r2, r3 = st.columns(3)
            metrics = [
                ("P/E Ratio",      fund.get("pe_ratio"),                          ""),
                ("P/B Ratio",      fund.get("pb_ratio"),                          ""),
                ("ROE",            (fund.get("roe") or 0) * 100,                  "%"),
                ("Net Margin",     (fund.get("net_margin") or 0) * 100,           "%"),
                ("D/E Ratio",      fund.get("debt_to_equity"),                    ""),
                ("Dividend Yield", (fund.get("dividend_yield") or 0) * 100,       "%"),
                ("EV/EBITDA",      fund.get("ev_ebitda"),                         ""),
                ("Beta",           fund.get("beta"),                              ""),
                ("Market Cap",     (fund.get("market_cap") or 0) / 1e7,          " Cr"),
            ]
            for i, (lbl, val, sfx) in enumerate(metrics):
                with [r1, r2, r3][i % 3]:
                    if val is not None:
                        st.metric(lbl, f"{float(val):.2f}{sfx}")
                    else:
                        st.metric(lbl, "N/A")

            desc = fund.get("description", "")
            if desc:
                with st.expander("Company Description"):
                    st.write(desc[:1400] + ("..." if len(desc) > 1400 else ""))

    with tab_n:
        news = get_news(symbol, 8)
        if news:
            for art in news:
                title = art.get("title", "")
                url   = art.get("link", "#")
                pub   = art.get("publisher", "")
                ts    = art.get("providerPublishTime", 0)
                dt    = datetime.fromtimestamp(ts).strftime("%d %b %Y  %H:%M") if ts else ""
                st.markdown(f"""
                <div class="ks-card" style="border-left:3px solid var(--blue);margin-bottom:7px;">
                  <a href="{url}" target="_blank"
                     style="color:var(--t1);text-decoration:none;font-size:.88rem;
                            font-weight:600;display:block;line-height:1.5;">{title}</a>
                  <div style="color:var(--t3);font-size:.72rem;margin-top:4px;">
                    <span style="color:var(--blue);font-weight:600;">{pub}</span>
                    &nbsp;•&nbsp; {dt}
                  </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("No news available for this symbol.")
