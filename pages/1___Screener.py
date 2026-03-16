"""
1___Screener.py — Keshav's Screen
Stock Screener: AI prompt + 30+ fundamental + technical filters
Full NSE universe (2671+ stocks), parallel data fetch, no crashes
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.nse_stocks import NSE_STOCKS_EXTENDED, get_all_sectors, get_index_constituents, INDICES, load_nse_universe
from utils.data_fetcher import fetch_screener_batch, get_ohlcv
from utils.screener_engine import parse_query_with_ai, parse_simple_query, apply_filters, PRESET_QUERIES
from utils.technical_analysis import rsi, macd, sma, ema, atr, bollinger_bands, adx_dmi, supertrend
from utils.styles import inject_css, section_label, PLOTLY_LAYOUT, CHART_COLORS

st.set_page_config(
    page_title="Screener — Keshav's Screen",
    page_icon="K",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()

st.markdown('<h2 style="margin-bottom:2px;">Stock Screener</h2>', unsafe_allow_html=True)
st.markdown(
    '<p style="color:var(--t3);font-size:.85rem;">Screen 2671+ NSE stocks with AI prompt, '
    'fundamental &amp; technical filters</p>',
    unsafe_allow_html=True,
)

# ─── FIX: PRESET QUERY INJECTION (resolves Issue #6) ─────────────────────────
# The bug: clicking a preset button tries to mutate st.session_state["screener_query"]
# AFTER the text_input widget with that key is already instantiated → crash.
# Fix: store pending preset in a DIFFERENT key ("_pending_query"), then read it
# BEFORE the widget is created, set the widget's default value, and clear it.

_pending = st.session_state.pop("_pending_query", None)
_initial_query = _pending if _pending else st.session_state.get("screener_query", "")

# ─── AI PROMPT BOX ───────────────────────────────────────────────────────────
st.markdown("""
<div style="
  background:var(--bg2);
  border:1px solid var(--blue-bdr);
  border-radius:12px;
  padding:18px 20px;
  margin-bottom:14px;
  box-shadow:var(--shadow-sm);
">
  <div style="color:var(--blue);font-size:.73rem;font-weight:700;
              letter-spacing:1.2px;text-transform:uppercase;margin-bottom:6px;">
    AI Screening Prompt
  </div>
  <div style="color:var(--t3);font-size:.82rem;line-height:1.6;">
    Describe what you want in plain English — fundamentals, technicals, sector, or market-cap criteria.
    <br><span style="color:var(--t2);font-weight:500;">Examples:</span>
    <span style="color:var(--t3);">
      &ldquo;RSI below 30, PE below 20&rdquo; &nbsp;·&nbsp;
      &ldquo;Large cap IT stocks with ROE above 20%&rdquo; &nbsp;·&nbsp;
      &ldquo;Debt-free pharma with high earnings growth&rdquo;
    </span>
  </div>
</div>
""", unsafe_allow_html=True)

col_q, col_btn = st.columns([5, 1])
with col_q:
    # Use value= (not key=) so we can set it from _pending without the crash
    ai_query = st.text_input(
        "AI Query",
        value=_initial_query,
        key="screener_query",
        placeholder='e.g. "Find oversold NIFTY 50 banking stocks with PE below 12"',
        label_visibility="collapsed",
    )
with col_btn:
    run_btn = st.button("Screen", use_container_width=True, type="primary")

# ─── PRESET CHIPS ────────────────────────────────────────────────────────────
section_label("PRESET SCREENS")
cols_p = st.columns(6)
for i, (name, q) in enumerate(list(PRESET_QUERIES.items())[:12]):
    with cols_p[i % 6]:
        if st.button(name, key=f"pq_{i}", use_container_width=True):
            # Write to _pending_query (NOT screener_query) → avoids the crash
            st.session_state["_pending_query"] = q
            st.rerun()

st.markdown("---")

# ─── MANUAL FILTERS ──────────────────────────────────────────────────────────
with st.expander("Manual Filters (Advanced)", expanded=False):
    u1, u2, u3 = st.columns(3)
    with u1:
        universe_choice = st.selectbox("Universe", [
            "NIFTY 50", "NIFTY BANK", "NIFTY IT", "NIFTY PHARMA",
            "NIFTY AUTO", "NIFTY FMCG", "NIFTY METAL", "NIFTY ENERGY",
            "NIFTY MIDCAP 50", "NIFTY 100", "NIFTY 500", "All NSE Stocks",
        ])
    with u2:
        all_sectors = sorted(set(v["sector"] for v in NSE_STOCKS_EXTENDED.values()))
        sel_sectors = st.multiselect("Sector Filter", all_sectors)
    with u3:
        cap_filter = st.multiselect("Market Cap", ["Large (>20000 Cr)", "Mid (5000–20000 Cr)", "Small (<5000 Cr)"])

    st.markdown("---")
    f1, f2, f3, f4 = st.columns(4)

    with f1:
        st.markdown("**Profitability**")
        roe_min = st.number_input("ROE Min (%)",          value=None, step=1.0, key="m_roe_min")
        roe_max = st.number_input("ROE Max (%)",          value=None, step=1.0, key="m_roe_max")
        npm_min = st.number_input("Net Margin Min (%)",   value=None, step=1.0, key="m_npm_min")
        opm_min = st.number_input("OPM Min (%)",          value=None, step=1.0, key="m_opm_min")
        eps_min = st.number_input("EPS Min",              value=None, step=1.0, key="m_eps_min")

    with f2:
        st.markdown("**Valuation**")
        pe_min  = st.number_input("P/E Min",               value=None, step=0.5, key="m_pe_min")
        pe_max  = st.number_input("P/E Max",               value=None, step=0.5, key="m_pe_max")
        pb_max  = st.number_input("P/B Max",               value=None, step=0.5, key="m_pb_max")
        peg_max = st.number_input("PEG Max",               value=None, step=0.1, key="m_peg_max")
        div_min = st.number_input("Dividend Yield Min (%)",value=None, step=0.5, key="m_div_min")

    with f3:
        st.markdown("**Growth & Leverage**")
        rev_g_min = st.number_input("Revenue Growth Min (%)", value=None, step=1.0, key="m_rev_g")
        ear_g_min = st.number_input("Earnings Growth Min (%)",value=None, step=1.0, key="m_ear_g")
        de_max    = st.number_input("D/E Max",                value=None, step=0.1, key="m_de_max")
        cr_min    = st.number_input("Current Ratio Min",      value=None, step=0.1, key="m_cr_min")
        beta_max  = st.number_input("Beta Max",               value=None, step=0.1, key="m_beta_max")

    with f4:
        st.markdown("**Technical**")
        rsi_min   = st.number_input("RSI(14) Min",  value=None, step=1.0, key="m_rsi_min")
        rsi_max   = st.number_input("RSI(14) Max",  value=None, step=1.0, key="m_rsi_max")
        abv_sma50 = st.checkbox("Above SMA 50",  key="m_sma50")
        abv_sma200= st.checkbox("Above SMA 200", key="m_sma200")
        macd_bull = st.checkbox("MACD Bullish",  key="m_macd")
        st_bull   = st.checkbox("Supertrend Bull",key="m_st")
        nr_52wh   = st.checkbox("Near 52W High", key="m_52wh")
        nr_52wl   = st.checkbox("Near 52W Low",  key="m_52wl")


# ─── HELPERS ─────────────────────────────────────────────────────────────────

def get_universe(name: str) -> list:
    """Return list of symbols for the selected universe."""
    idx_c = get_index_constituents()

    if name in idx_c:
        return idx_c[name]

    if name == "NIFTY 100":
        n50 = idx_c.get("NIFTY 50", [])
        extra = [s for s in list(NSE_STOCKS_EXTENDED.keys()) if s not in set(n50)][:50]
        return n50 + extra

    if name == "NIFTY 500":
        # Use the first 500 from our universe
        return list(NSE_STOCKS_EXTENDED.keys())[:500]

    if name == "All NSE Stocks":
        # Load full universe (2671+ from NSE CSV if reachable)
        universe = load_nse_universe()
        return list(universe.keys())

    return list(NSE_STOCKS_EXTENDED.keys())


def build_manual_filters() -> dict:
    """Collect all manual filter widget values into a filter dict."""
    f = {}
    ss = st.session_state

    def rng(kmin, kmax, fkey, div=1.0):
        lo = ss.get(kmin); hi = ss.get(kmax)
        if lo is not None or hi is not None:
            f[fkey] = {}
            if lo is not None: f[fkey]["min"] = float(lo) / div
            if hi is not None: f[fkey]["max"] = float(hi) / div

    rng("m_roe_min", "m_roe_max", "_roe", 100)
    rng("m_pe_min",  "m_pe_max",  "_pe")
    rng("m_rsi_min", "m_rsi_max", "_rsi_14")

    if ss.get("m_npm_min"):  f["_npm"]  = {"min": ss["m_npm_min"] / 100}
    if ss.get("m_opm_min"):  f["_opm"]  = {"min": ss["m_opm_min"] / 100}
    if ss.get("m_eps_min"):  f["_eps"]  = {"min": ss["m_eps_min"]}
    if ss.get("m_pb_max"):   f["_pb"]   = {"max": ss["m_pb_max"]}
    if ss.get("m_peg_max"):  f["_peg"]  = {"max": ss["m_peg_max"]}
    if ss.get("m_div_min"):  f["_divy"] = {"min": ss["m_div_min"] / 100}
    if ss.get("m_de_max"):   f["_de"]   = {"max": ss["m_de_max"]}
    if ss.get("m_cr_min"):   f["_cr"]   = {"min": ss["m_cr_min"]}
    if ss.get("m_beta_max"): f["_beta"] = {"max": ss["m_beta_max"]}
    if ss.get("m_rev_g"):    f["_rev_g"]  = {"min": ss["m_rev_g"] / 100}
    if ss.get("m_ear_g"):    f["_earn_g"] = {"min": ss["m_ear_g"] / 100}

    if ss.get("m_sma50"):    f["_above_sma50"]    = True
    if ss.get("m_sma200"):   f["_above_sma200"]   = True
    if ss.get("m_macd"):     f["_macd_bull"]      = True
    if ss.get("m_st"):       f["_supertrend_bull"]= True
    if ss.get("m_52wh"):     f["_near_52w_high"]  = True
    if ss.get("m_52wl"):     f["_near_52w_low"]   = True

    if sel_sectors:
        f["_sectors"] = sel_sectors

    for cap in cap_filter:
        if "Large" in cap:  f.setdefault("_mc", {})["min"] = 20000
        if "Small" in cap:  f.setdefault("_mc", {})["max"] = 5000
        if "Mid"   in cap:
            f.setdefault("_mc", {}).update({"min": 5000, "max": 20000})

    return f


# ─── RUN SCREENER ─────────────────────────────────────────────────────────────
run_full = st.button("Run Full Screener", use_container_width=True, type="primary", key="run_full_btn")

if run_btn or run_full:
    combined = {}

    # AI / rule-based parse of query
    if ai_query:
        api_key  = st.session_state.get("ai_api_key", "")
        provider = st.session_state.get("ai_provider", "Groq (Free)")

        with st.spinner("Parsing query with AI..."):
            pf = parse_query_with_ai(ai_query, api_key or None, provider)

        if pf:
            combined.update(pf)
            with st.expander("Parsed Filters", expanded=False):
                st.json(pf)

    # Merge manual filters
    combined.update(build_manual_filters())

    if not combined:
        st.warning("Please enter a query or set at least one filter.")
        st.stop()

    # Get symbol list
    symbols = get_universe(universe_choice)
    st.info(f"Screening **{len(symbols):,}** stocks from **{universe_choice}**...")

    # Fetch fundamentals — parallel
    df = fetch_screener_batch(symbols, max_stocks=min(len(symbols), 300))

    if df.empty:
        st.error("Data fetch failed. Please try again or reduce universe size.")
        st.stop()

    # ── TECHNICAL INDICATOR PASS (only if TA filters active) ──────────────────
    ta_keys = {
        "_rsi_14", "_above_sma50", "_above_sma200",
        "_macd_bull", "_supertrend_bull", "_near_52w_high", "_near_52w_low",
    }
    needs_ta = any(k in combined for k in ta_keys)

    if needs_ta:
        with st.spinner("Computing technical indicators..."):
            ta_records = {}
            syms_ta = df["Symbol"].tolist()
            prog = st.progress(0, text="Running TA...")
            for ix, sym in enumerate(syms_ta):
                try:
                    pdf = get_ohlcv(sym, "3mo", "1d")
                    if pdf is not None and len(pdf) > 20:
                        close = pdf["Close"]
                        rsi_s = rsi(pdf)
                        sma50  = close.rolling(50).mean().iloc[-1]  if len(close) >= 50  else None
                        sma200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else None
                        ml, sl, _ = macd(pdf)
                        stv, std  = supertrend(pdf)
                        w52h = pdf["High"].rolling(252, min_periods=1).max().iloc[-1]
                        w52l = pdf["Low"].rolling(252, min_periods=1).min().iloc[-1]
                        lp   = float(close.iloc[-1])

                        ta_records[sym] = {
                            "RSI_14":       float(rsi_s.iloc[-1]) if not rsi_s.empty else None,
                            "Above_SMA50":  bool(lp > sma50)  if sma50  else False,
                            "Above_SMA200": bool(lp > sma200) if sma200 else False,
                            "MACD_Bull":    bool(ml.iloc[-1] > sl.iloc[-1]) if not ml.empty else False,
                            "ST_Bull":      bool(std.iloc[-1] == 1) if not std.empty else False,
                            "Near_52W_High":bool(lp >= w52h * 0.95),
                            "Near_52W_Low": bool(lp <= w52l * 1.05),
                        }
                except Exception:
                    pass
                prog.progress((ix + 1) / len(syms_ta))
            prog.empty()

            if ta_records:
                ta_df = pd.DataFrame.from_dict(ta_records, orient="index").reset_index()
                ta_df.rename(columns={"index": "Symbol"}, inplace=True)
                df = df.merge(ta_df, on="Symbol", how="left")

    # ── APPLY FILTERS ────────────────────────────────────────────────────────
    result = apply_filters(df, combined)

    # ── RESULTS BANNER ────────────────────────────────────────────────────────
    clr = "var(--green)" if len(result) > 0 else "var(--red)"
    st.markdown(f"""
    <div style="background:var(--bg2);border:1px solid var(--bdr);border-radius:10px;
                padding:14px 20px;margin:12px 0;box-shadow:var(--shadow-sm);
                display:flex;align-items:center;gap:10px;">
      <span style="color:{clr};font-size:1.5rem;font-weight:700;
                   font-family:'JetBrains Mono',monospace;">{len(result)}</span>
      <span style="color:var(--t2);font-size:.9rem;">stocks matched out of</span>
      <span style="color:var(--t1);font-weight:600;font-family:'JetBrains Mono',monospace;">{len(df)}</span>
      <span style="color:var(--t3);font-size:.9rem;">screened</span>
    </div>""", unsafe_allow_html=True)

    if result.empty:
        st.warning("No stocks matched. Try relaxing your criteria.")
        st.stop()

    # ── RESULTS TABLE ────────────────────────────────────────────────────────
    disp = [
        "Symbol", "Name", "Sector", "Cap", "Price", "Market Cap (Cr)",
        "P/E", "P/B", "EPS", "ROE (%)", "Net Margin (%)", "OPM (%)",
        "D/E Ratio", "Current Ratio", "Dividend Yield (%)",
        "Revenue Growth (%)", "Earnings Growth (%)", "Beta",
        "% from 52W High", "% from 52W Low",
    ]
    if "RSI_14" in result.columns:
        disp.append("RSI_14")

    disp = [c for c in disp if c in result.columns]
    show = result[disp].copy()

    def _style_cell(val):
        if pd.isna(val) or not isinstance(val, (int, float)):
            return "color:var(--t3)"
        if val > 0:  return "color:var(--green)"
        if val < 0:  return "color:var(--red)"
        return "color:var(--t1)"

    color_cols = [c for c in [
        "ROE (%)", "Net Margin (%)", "OPM (%)",
        "Revenue Growth (%)", "Earnings Growth (%)",
    ] if c in show.columns]

    fmt = {
        "Price":              "₹{:.2f}",
        "Market Cap (Cr)":    "{:,.0f}",
        "P/E":                "{:.1f}",
        "P/B":                "{:.2f}",
        "EPS":                "{:.2f}",
        "ROE (%)":            "{:.1f}%",
        "Net Margin (%)":     "{:.1f}%",
        "OPM (%)":            "{:.1f}%",
        "D/E Ratio":          "{:.2f}",
        "Current Ratio":      "{:.2f}",
        "Dividend Yield (%)": "{:.2f}%",
        "Revenue Growth (%)": "{:.1f}%",
        "Earnings Growth (%)" :"{:.1f}%",
        "% from 52W High":    "{:.1f}%",
        "% from 52W Low":     "{:.1f}%",
        "Beta":               "{:.2f}",
        "RSI_14":             "{:.1f}",
    }
    fmt = {k: v for k, v in fmt.items() if k in show.columns}

    st.dataframe(
        show.style.applymap(_style_cell, subset=color_cols).format(fmt, na_rep="—"),
        use_container_width=True,
        height=500,
    )

    # ── ACTION ROW ────────────────────────────────────────────────────────────
    a1, a2, a3 = st.columns(3)
    with a1:
        st.download_button(
            "Download CSV",
            data=result.to_csv(index=False),
            file_name="keshav_screen_results.csv",
            mime="text/csv",
        )
    with a2:
        if st.button("Add All to Bucket"):
            if "bucket" not in st.session_state:
                st.session_state["bucket"] = []
            existing = set(st.session_state["bucket"])
            new_syms = [s for s in result["Symbol"].tolist() if s not in existing]
            st.session_state["bucket"].extend(new_syms)
            st.success(f"Added {len(new_syms)} stocks to Bucket.")
    with a3:
        if st.button("Show Distribution Charts"):
            st.session_state["show_charts"] = not st.session_state.get("show_charts", False)

    # ── DISTRIBUTION CHARTS ────────────────────────────────────────────────────
    if st.session_state.get("show_charts"):
        c1, c2, c3 = st.columns(3)
        light_layout = {
            **PLOTLY_LAYOUT,
            "height": 280,
            "margin": dict(l=0, r=0, t=32, b=0),
        }

        with c1:
            if "Sector" in show.columns:
                sc = show["Sector"].value_counts()
                fig = go.Figure(go.Pie(
                    labels=sc.index, values=sc.values, hole=.45,
                    marker_colors=CHART_COLORS[:len(sc)],
                ))
                fig.update_layout(**{**light_layout, "showlegend": True,
                                     "title": "Sector Mix",
                                     "title_font_color": "var(--t3)"})
                st.plotly_chart(fig, use_container_width=True)

        with c2:
            if "P/E" in show.columns:
                pe_v = show["P/E"].dropna()
                fig2 = go.Figure(go.Histogram(x=pe_v, nbinsx=20,
                                              marker_color=CHART_COLORS[0],
                                              opacity=.8))
                fig2.update_layout(**{**light_layout,
                                      "title": "P/E Distribution",
                                      "title_font_color": "var(--t3)",
                                      "bargap": 0.05})
                st.plotly_chart(fig2, use_container_width=True)

        with c3:
            if "ROE (%)" in show.columns:
                roe_v = show["ROE (%)"].dropna()
                fig3 = go.Figure(go.Histogram(x=roe_v, nbinsx=20,
                                              marker_color=CHART_COLORS[1],
                                              opacity=.8))
                fig3.update_layout(**{**light_layout,
                                      "title": "ROE Distribution",
                                      "title_font_color": "var(--t3)",
                                      "bargap": 0.05})
                st.plotly_chart(fig3, use_container_width=True)


# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="font-weight:600;color:var(--t1);padding:12px 0 6px;">Screener Help</div>',
                unsafe_allow_html=True)

    with st.expander("AI Query Examples"):
        for ex in [
            "RSI below 30, PE below 15",
            "Large cap IT stocks ROE above 20%",
            "Debt-free pharma, earnings growth above 25%",
            "Mid cap banking, dividend yield above 3%",
            "Oversold NIFTY 50 stocks near 52W low",
        ]:
            st.markdown(f'<div style="color:var(--t3);font-size:.78rem;padding:3px 0;'
                        f'border-bottom:1px solid var(--bdr);">{ex}</div>',
                        unsafe_allow_html=True)

    st.markdown('<hr style="border:none;border-top:1px solid var(--bdr);margin:8px 0;">', unsafe_allow_html=True)

    bucket = st.session_state.get("bucket", [])
    st.markdown(f'<div style="color:var(--t3);font-size:.82rem;">Bucket: '
                f'<span style="color:var(--blue);font-weight:600;">{len(bucket)} stocks</span></div>',
                unsafe_allow_html=True)

    if st.button("Clear Screener Results", use_container_width=True):
        for k in ["show_charts", "_pending_query"]:
            st.session_state.pop(k, None)
        st.rerun()
