"""
6___Indices.py — Keshav's Screen
Indian Market Indices Dashboard: Performance · Deep-Dive · Comparison · All-Indices · Constituents
Fix Issue #16: Rebuilt data pipeline with parallel fetch + robust error handling
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.nse_stocks import INDICES, get_index_constituents, NSE_STOCKS_EXTENDED, yf_ticker
from utils.data_fetcher import get_ohlcv, get_news
from utils.technical_analysis import sma, ema, rsi, macd, bollinger_bands, atr, adx_dmi
from utils.styles import inject_css, section_label, PLOTLY_LAYOUT, CHART_COLORS

st.set_page_config(
    page_title="Indices — Keshav's Screen",
    page_icon="K",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()

st.markdown('<h2 style="margin-bottom:2px;">Indian Market Indices</h2>', unsafe_allow_html=True)
st.markdown(
    '<p style="color:var(--t3);font-size:.85rem;">'
    '28 NSE/BSE indices · Performance · Charts · Comparison · Constituents</p>',
    unsafe_allow_html=True,
)

UP   = "#16A34A"
DOWN = "#DC2626"

# ─── KEY INDEX BANNER (parallel fetch) ───────────────────────────────────────
KEY_INDICES_BANNER = {
    "NIFTY 50":      "^NSEI",
    "SENSEX":        "^BSESN",
    "NIFTY BANK":    "^NSEBANK",
    "NIFTY IT":      "^CNXIT",
    "NIFTY PHARMA":  "^CNXPHARMA",
    "NIFTY FMCG":    "^CNXFMCG",
    "NIFTY AUTO":    "^CNXAUTO",
    "NIFTY METAL":   "^CNXMETAL",
    "NIFTY ENERGY":  "^CNXENERGY",
    "INDIA VIX":     "^INDIAVIX",
    "NIFTY MIDCAP 50":"^NSEMDCP50",
    "NIFTY SMALLCAP 50":"^CNXSC",
}


def _fetch_one_index_price(name: str, ticker: str) -> dict:
    """Fetch a single index price — used by thread pool."""
    try:
        fi = yf.Ticker(ticker).fast_info
        p  = getattr(fi, "last_price",     None)
        pc = getattr(fi, "previous_close", p) or p
        chg = (p - pc) if (p and pc) else 0
        pct = (chg / pc * 100) if pc else 0
        return {"Index": name, "Ticker": ticker, "Price": p,
                "Change": round(chg, 2), "Change%": round(pct, 2)}
    except Exception:
        return {"Index": name, "Ticker": ticker, "Price": None, "Change": 0, "Change%": 0}


@st.cache_data(ttl=30)
def get_all_idx_snap_parallel() -> pd.DataFrame:
    """Parallel snapshot of all tracked indices — cached 30s."""
    rows = []
    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = {ex.submit(_fetch_one_index_price, n, t): n for n, t in INDICES.items()}
        for future in as_completed(futures, timeout=20):
            try:
                rows.append(future.result())
            except Exception:
                pass
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    # Keep original order
    order = list(INDICES.keys())
    df["_sort"] = df["Index"].map({k: i for i, k in enumerate(order)})
    return df.sort_values("_sort").drop(columns=["_sort"]).reset_index(drop=True)


# Fetch banner data
snap_df = get_all_idx_snap_parallel()

# Banner grid (12 key indices)
banner_cols = st.columns(6)
for i, (name, ticker) in enumerate(list(KEY_INDICES_BANNER.items())[:12]):
    row = snap_df[snap_df["Ticker"] == ticker] if not snap_df.empty else pd.DataFrame()
    if not row.empty and row["Price"].iloc[0]:
        p   = float(row["Price"].iloc[0])
        pct = float(row["Change%"].iloc[0])
    else:
        p = 0; pct = 0
    clr     = "var(--green)" if pct >= 0 else "var(--red)"
    clr_bg  = "var(--green-bg)" if pct >= 0 else "var(--red-bg)"
    clr_bdr = "#BBF7D0" if pct >= 0 else "#FCA5A5"
    arr  = "+" if pct >= 0 else ""
    pstr = f"{p:,.2f}" if p else "—"
    with banner_cols[i % 6]:
        st.markdown(f"""
        <div style="background:{clr_bg};border:1px solid {clr_bdr};border-radius:9px;
                    padding:10px 8px;text-align:center;margin-bottom:4px;box-shadow:var(--shadow-sm);">
          <div style="color:var(--t3);font-size:.62rem;font-weight:700;letter-spacing:.6px;text-transform:uppercase;">{name}</div>
          <div style="color:var(--t1);font-size:.88rem;font-weight:700;font-family:'JetBrains Mono',monospace;margin:3px 0;">{pstr}</div>
          <div style="color:{clr};font-size:.75rem;font-weight:600;">{arr}{pct:+.2f}%</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

# ─── MAIN TABS ────────────────────────────────────────────────────────────────
t1, t2, t3, t4, t5 = st.tabs([
    "Index Dashboard", "Deep-Dive Chart", "Comparison",
    "All Indices Table", "Constituents",
])

# ══════════════════════════════════════════════════════════════
# TAB 1: INDEX DASHBOARD — parallel performance summary
# ══════════════════════════════════════════════════════════════
with t1:
    section_label("ALL INDICES PERFORMANCE SUMMARY")

    @st.cache_data(ttl=300)
    def get_idx_performance_summary_parallel() -> pd.DataFrame:
        """
        Parallel performance summary for all indices.
        Issue #16 fix: replaces sequential loop that timed out.
        """
        def _fetch_one(name: str, ticker: str) -> dict | None:
            try:
                df = get_ohlcv(ticker, "2y", "1d")
                if df is None or df.empty:
                    return None
                c = df["Close"]
                p = float(c.iloc[-1])

                def ret(n):
                    return round((p / float(c.iloc[-n-1]) - 1) * 100, 2) if len(c) > n+1 else None

                return {
                    "Index":        name,
                    "Price":        round(p, 2),
                    "1D (%)":       ret(1),
                    "1W (%)":       ret(5),
                    "1M (%)":       ret(21),
                    "3M (%)":       ret(63),
                    "6M (%)":       ret(126),
                    "1Y (%)":       ret(252),
                    "Ann. Vol (%)": round(float(c.pct_change().dropna().std()) * np.sqrt(252) * 100, 2),
                    "Max DD (%)":   round(float(((c / c.cummax()) - 1).min()) * 100, 2),
                    "52W High":     round(float(c.rolling(252, min_periods=1).max().iloc[-1]), 2),
                    "52W Low":      round(float(c.rolling(252, min_periods=1).min().iloc[-1]), 2),
                }
            except Exception:
                return None

        rows = []
        with ThreadPoolExecutor(max_workers=10) as ex:
            futures = {ex.submit(_fetch_one, n, t): n for n, t in INDICES.items()}
            for future in as_completed(futures, timeout=60):
                try:
                    r = future.result()
                    if r:
                        rows.append(r)
                except Exception:
                    pass
        if not rows:
            return pd.DataFrame()
        df_out = pd.DataFrame(rows)
        order  = list(INDICES.keys())
        df_out["_sort"] = df_out["Index"].map({k: i for i, k in enumerate(order)})
        return df_out.sort_values("_sort").drop(columns=["_sort"]).reset_index(drop=True)

    with st.spinner("Loading performance summary (parallel)..."):
        perf_df = get_idx_performance_summary_parallel()

    if not perf_df.empty:
        def _c_perf(v):
            if pd.isna(v) or not isinstance(v, (int, float)): return "color:var(--t3)"
            return "color:var(--green)" if v > 0 else "color:var(--red)" if v < 0 else "color:var(--t1)"

        pct_cols = [c for c in ["1D (%)","1W (%)","1M (%)","3M (%)","6M (%)","1Y (%)","Max DD (%)"] if c in perf_df.columns]
        fmt = {"Price": "{:,.2f}", **{c: "{:+.2f}%" for c in pct_cols},
               "Ann. Vol (%)": "{:.2f}%", "52W High": "{:,.2f}", "52W Low": "{:,.2f}"}
        fmt = {k: v for k, v in fmt.items() if k in perf_df.columns}

        st.dataframe(
            perf_df.style.applymap(_c_perf, subset=pct_cols).format(fmt, na_rep="—"),
            use_container_width=True, height=520,
        )
        st.download_button("Export CSV", data=perf_df.to_csv(index=False),
                           file_name="keshav_indices_performance.csv", mime="text/csv")

        # 1M performer bar chart
        section_label("TOP & BOTTOM PERFORMERS  —  1 MONTH")
        if "1M (%)" in perf_df.columns:
            m_df = perf_df[["Index","1M (%)"]].dropna().sort_values("1M (%)", ascending=False)
            bc   = ["rgba(22,163,74,.8)" if v >= 0 else "rgba(220,38,38,.8)" for v in m_df["1M (%)"]]
            fig_pm = go.Figure(go.Bar(
                x=m_df["Index"], y=m_df["1M (%)"],
                marker_color=bc,
                text=[f"{v:+.2f}%" for v in m_df["1M (%)"]],
                textposition="outside", textfont=dict(color="#2D3A52", size=9),
            ))
            fig_pm.add_hline(y=0, line=dict(color="#DDE3EF", width=1))
            fig_pm.update_layout(
                **{**PLOTLY_LAYOUT, "height": 320,
                   "xaxis": {**PLOTLY_LAYOUT["xaxis"], "tickangle": -35,
                              "tickfont": dict(size=9), "side": "bottom"},
                   "yaxis": {**PLOTLY_LAYOUT["yaxis"], "ticksuffix": "%"},
                }
            )
            st.plotly_chart(fig_pm, use_container_width=True)
    else:
        st.warning("Could not load performance data. Please check your connection and try refreshing.")
        if st.button("Refresh"):
            st.cache_data.clear(); st.rerun()


# ══════════════════════════════════════════════════════════════
# TAB 2: DEEP-DIVE CHART
# ══════════════════════════════════════════════════════════════
with t2:
    dd_a, dd_b = st.columns([1, 4])
    with dd_a:
        sel_idx_dd = st.selectbox("Select Index", list(INDICES.keys()), index=0, key="dd_idx")
        dd_period  = st.selectbox("Period", ["1M","3M","6M","1Y","2Y","5Y","Max"], index=3, key="dd_p")
        dd_chart   = st.selectbox("Chart Type", ["Line","Candlestick","Area"], key="dd_ct")
        show_sma   = st.checkbox("SMA 20/50/200")
        show_bb2   = st.checkbox("Bollinger Bands")
        show_rsi2  = st.checkbox("RSI")
        show_macd2 = st.checkbox("MACD")
        show_adx2  = st.checkbox("ADX")
        show_vol2  = st.checkbox("Volume")
        if st.button("Add to Bucket", key="add_idx_bucket"):
            if "bucket" not in st.session_state: st.session_state["bucket"] = []
            if sel_idx_dd not in st.session_state["bucket"]:
                st.session_state["bucket"].append(sel_idx_dd)
                st.success(f"Added {sel_idx_dd} to Bucket.")

    TFD = {"1M":"3mo","3M":"6mo","6M":"1y","1Y":"2y","2Y":"5y","5Y":"10y","Max":"max"}
    dp  = TFD[dd_period]

    with dd_b:
        idx_ticker2 = INDICES[sel_idx_dd]
        df_idx = get_ohlcv(idx_ticker2, dp, "1d")

        if df_idx is not None and not df_idx.empty:
            panels_dd = []
            if show_rsi2:  panels_dd.append("RSI")
            if show_macd2: panels_dd.append("MACD")
            if show_adx2:  panels_dd.append("ADX")
            if show_vol2 and "Volume" in df_idx.columns: panels_dd.append("Vol")

            n_r = 1 + len(panels_dd)
            hw  = [0.55] + [0.45 / max(len(panels_dd), 1)] * len(panels_dd)
            hw  = [x / sum(hw) for x in hw]

            fig_dd = make_subplots(rows=n_r, cols=1, shared_xaxes=True,
                                    vertical_spacing=.02, row_heights=hw)
            lp = float(df_idx["Close"].iloc[-1]); fp = float(df_idx["Close"].iloc[0])
            lc = UP if lp >= fp else DOWN
            pct_chg = (lp - fp) / fp * 100

            if dd_chart == "Candlestick":
                fig_dd.add_trace(go.Candlestick(
                    x=df_idx.index, open=df_idx["Open"], high=df_idx["High"],
                    low=df_idx["Low"], close=df_idx["Close"], name=sel_idx_dd,
                    increasing_line_color=UP, decreasing_line_color=DOWN,
                    increasing_fillcolor=UP, decreasing_fillcolor=DOWN,
                ), row=1, col=1)
            elif dd_chart == "Area":
                fig_dd.add_trace(go.Scatter(x=df_idx.index, y=df_idx["Close"], mode="lines",
                    line=dict(color=lc, width=1.8),
                    fill="tozeroy",
                    fillcolor=f"{'rgba(22,163,74,.06)' if lc==UP else 'rgba(220,38,38,.06)'}",
                    name=sel_idx_dd), row=1, col=1)
            else:
                fig_dd.add_trace(go.Scatter(x=df_idx.index, y=df_idx["Close"], mode="lines",
                    line=dict(color=lc, width=1.8), name=sel_idx_dd), row=1, col=1)

            if show_sma:
                for period_, clr_ in [(20, CHART_COLORS[2]),(50, CHART_COLORS[0]),(200, CHART_COLORS[4])]:
                    s = sma(df_idx, period_)
                    if not s.dropna().empty:
                        fig_dd.add_trace(go.Scatter(x=df_idx.index, y=s, mode="lines",
                            line=dict(color=clr_, width=1), name=f"SMA{period_}"), row=1, col=1)
            if show_bb2:
                bu, bm, bl, _, _ = bollinger_bands(df_idx)
                fig_dd.add_trace(go.Scatter(x=df_idx.index, y=bu, mode="lines",
                    line=dict(color="rgba(100,149,237,.4)", width=.8), showlegend=False), row=1, col=1)
                fig_dd.add_trace(go.Scatter(x=df_idx.index, y=bl, mode="lines",
                    line=dict(color="rgba(100,149,237,.4)", width=.8),
                    fill="tonexty", fillcolor="rgba(100,149,237,.04)", name="BB"), row=1, col=1)

            row_n = 2
            for panel in panels_dd:
                if panel == "RSI":
                    rv = rsi(df_idx, 14)
                    fig_dd.add_trace(go.Scatter(x=df_idx.index, y=rv, mode="lines",
                        line=dict(color=CHART_COLORS[4], width=1.3), name="RSI"), row=row_n, col=1)
                    fig_dd.add_hline(y=70, line=dict(color=DOWN, width=.7, dash="dash"), row=row_n, col=1)
                    fig_dd.add_hline(y=30, line=dict(color=UP,   width=.7, dash="dash"), row=row_n, col=1)
                    fig_dd.update_yaxes(range=[0, 100], row=row_n, col=1)
                elif panel == "MACD":
                    ml, sl, mh = macd(df_idx)
                    mc_ = ["rgba(22,163,74,.7)" if v >= 0 else "rgba(220,38,38,.7)" for v in mh.fillna(0)]
                    fig_dd.add_trace(go.Bar(x=df_idx.index, y=mh, marker_color=mc_, showlegend=False, opacity=.8), row=row_n, col=1)
                    fig_dd.add_trace(go.Scatter(x=df_idx.index, y=ml, mode="lines",
                        line=dict(color=CHART_COLORS[0], width=1.1), name="MACD"), row=row_n, col=1)
                    fig_dd.add_trace(go.Scatter(x=df_idx.index, y=sl, mode="lines",
                        line=dict(color=DOWN, width=.9), name="Signal"), row=row_n, col=1)
                elif panel == "ADX":
                    adx_v, dip, din = adx_dmi(df_idx)
                    fig_dd.add_trace(go.Scatter(x=df_idx.index, y=adx_v, mode="lines",
                        line=dict(color=CHART_COLORS[2], width=1.3), name="ADX"), row=row_n, col=1)
                    fig_dd.add_trace(go.Scatter(x=df_idx.index, y=dip, mode="lines",
                        line=dict(color=UP, width=1), name="+DI"), row=row_n, col=1)
                    fig_dd.add_trace(go.Scatter(x=df_idx.index, y=din, mode="lines",
                        line=dict(color=DOWN, width=1), name="-DI"), row=row_n, col=1)
                    fig_dd.add_hline(y=25, line=dict(color="#C8D0E4", width=.7, dash="dash"), row=row_n, col=1)
                elif panel == "Vol" and "Volume" in df_idx.columns:
                    vc_ = [UP if df_idx["Close"].iloc[i] >= df_idx["Open"].iloc[i] else DOWN for i in range(len(df_idx))]
                    fig_dd.add_trace(go.Bar(x=df_idx.index, y=df_idx["Volume"],
                        marker_color=vc_, showlegend=False, opacity=.7), row=row_n, col=1)
                row_n += 1

            chart_h = max(420, n_r * 160)
            fig_dd.update_layout(
                height=chart_h, paper_bgcolor="#FFFFFF", plot_bgcolor="#F7F9FD",
                font=dict(color="#5A6A88", family="DM Sans, sans-serif", size=10),
                margin=dict(l=0, r=90, t=32, b=8), hovermode="x unified",
                xaxis_rangeslider_visible=False,
                legend=dict(bgcolor="#FFFFFF", bordercolor="#DDE3EF", borderwidth=1,
                            font=dict(size=9, color="#2D3A52"), x=.01, y=.99),
                title=f"{sel_idx_dd}  ({pct_chg:+.2f}%  over {dd_period})",
                title_font_color="#5A6A88",
            )
            for i in range(1, n_r + 1):
                fig_dd.update_xaxes(showgrid=True, gridcolor="#EAEEf8", color="#5A6A88", row=i, col=1)
                fig_dd.update_yaxes(showgrid=True, gridcolor="#EAEEf8", color="#5A6A88", side="right", row=i, col=1)
            st.plotly_chart(fig_dd, use_container_width=True)

            # Key stats
            c1, c2, c3, c4 = st.columns(4)
            perf_row = perf_df[perf_df["Index"] == sel_idx_dd] if not perf_df.empty else pd.DataFrame()
            for col_, lbl_, val_ in [
                (c1, "Current Price", f"{lp:,.2f}"),
                (c2, f"Change ({dd_period})", f"{pct_chg:+.2f}%"),
                (c3, "52W High",
                 f"{float(perf_row['52W High'].iloc[0]):,.2f}" if not perf_row.empty and "52W High" in perf_row.columns and not pd.isna(perf_row['52W High'].iloc[0]) else "—"),
                (c4, "52W Low",
                 f"{float(perf_row['52W Low'].iloc[0]):,.2f}" if not perf_row.empty and "52W Low" in perf_row.columns and not pd.isna(perf_row['52W Low'].iloc[0]) else "—"),
            ]:
                with col_:
                    st.markdown(f"""
                    <div style="background:var(--bg2);border:1px solid var(--bdr);border-radius:8px;
                                padding:10px 14px;box-shadow:var(--shadow-sm);text-align:center;">
                      <div style="color:var(--t3);font-size:.7rem;font-weight:600;text-transform:uppercase;">{lbl_}</div>
                      <div style="color:var(--t1);font-size:1rem;font-weight:700;
                                  font-family:'JetBrains Mono',monospace;margin-top:3px;">{val_}</div>
                    </div>""", unsafe_allow_html=True)
        else:
            st.warning(f"No data for {sel_idx_dd}. Try a different period or refresh.")


# ══════════════════════════════════════════════════════════════
# TAB 3: COMPARISON
# ══════════════════════════════════════════════════════════════
with t3:
    cmp_a, cmp_b = st.columns([1, 4])
    with cmp_a:
        cmp_sel = st.multiselect(
            "Select Indices to Compare",
            list(INDICES.keys()),
            default=["NIFTY 50","NIFTY BANK","NIFTY IT","NIFTY PHARMA"],
            key="cmp_sel",
        )
        cmp_period = st.selectbox("Period", ["1M","3M","6M","1Y","2Y","5Y","Max"], index=3, key="cmp_p")
        cmp_base   = st.checkbox("Normalise to 100 (base period start)", value=True)
        cmp_log    = st.checkbox("Log scale Y-axis")

    TFC2 = {"1M":"3mo","3M":"6mo","6M":"1y","1Y":"2y","2Y":"5y","5Y":"10y","Max":"max"}
    cmp_pf = TFC2[cmp_period]

    with cmp_b:
        if not cmp_sel:
            st.info("Select at least one index to compare.")
        else:
            fig_cmp = go.Figure()
            cmp_perf = []
            for i, name in enumerate(cmp_sel):
                df_c = get_ohlcv(INDICES[name], cmp_pf, "1d")
                if df_c is not None and not df_c.empty:
                    base = float(df_c["Close"].iloc[0])
                    y = df_c["Close"] / base * 100 if cmp_base else df_c["Close"]
                    fig_cmp.add_trace(go.Scatter(
                        x=df_c.index, y=y, mode="lines",
                        line=dict(color=CHART_COLORS[i % len(CHART_COLORS)], width=1.6),
                        name=name,
                    ))
                    cmp_perf.append({"Index": name, "Return %": round((float(df_c["Close"].iloc[-1])/base-1)*100, 2)})

            fig_cmp.update_layout(
                **{**PLOTLY_LAYOUT,
                   "height": 440,
                   "yaxis": {**PLOTLY_LAYOUT["yaxis"],
                              "type": "log" if cmp_log else "linear",
                              "ticksuffix": "%" if cmp_base else ""},
                }
            )
            st.plotly_chart(fig_cmp, use_container_width=True)

            if cmp_perf:
                cmp_df = pd.DataFrame(cmp_perf).sort_values("Return %", ascending=False)
                fig_ret = go.Figure(go.Bar(
                    x=cmp_df["Index"], y=cmp_df["Return %"],
                    marker_color=["rgba(22,163,74,.8)" if v >= 0 else "rgba(220,38,38,.8)" for v in cmp_df["Return %"]],
                    text=[f"{v:+.2f}%" for v in cmp_df["Return %"]],
                    textposition="outside", textfont=dict(color="#2D3A52", size=10),
                ))
                fig_ret.add_hline(y=0, line=dict(color="#DDE3EF", width=1))
                fig_ret.update_layout(**{**PLOTLY_LAYOUT, "height": 260,
                    "xaxis": {**PLOTLY_LAYOUT["xaxis"], "tickangle": -20, "side": "bottom"},
                    "yaxis": {**PLOTLY_LAYOUT["yaxis"], "ticksuffix": "%"},
                })
                st.plotly_chart(fig_ret, use_container_width=True)


# ══════════════════════════════════════════════════════════════
# TAB 4: ALL INDICES TABLE
# ══════════════════════════════════════════════════════════════
with t4:
    section_label("ALL TRACKED INDICES")
    if not snap_df.empty:
        def _c2(v):
            if pd.isna(v) or not isinstance(v, (int, float)): return "color:var(--t3)"
            return "color:var(--green)" if v > 0 else "color:var(--red)" if v < 0 else "color:var(--t1)"

        disp = snap_df[["Index","Ticker","Price","Change","Change%"]].copy()
        st.dataframe(
            disp.style.applymap(_c2, subset=["Change","Change%"])
                      .format({"Price":"{:,.2f}","Change":"{:+.2f}","Change%":"{:+.2f}%"}, na_rep="—"),
            use_container_width=True, height=700,
        )
        if st.button("Add All to Bucket"):
            if "bucket" not in st.session_state: st.session_state["bucket"] = []
            existing = set(st.session_state["bucket"])
            new_items = [i for i in snap_df["Index"].tolist() if i not in existing]
            st.session_state["bucket"].extend(new_items)
            st.success(f"Added {len(new_items)} indices to Bucket.")
    else:
        st.warning("Could not load index data.")
        if st.button("Retry"):
            st.cache_data.clear(); st.rerun()


# ══════════════════════════════════════════════════════════════
# TAB 5: CONSTITUENTS
# ══════════════════════════════════════════════════════════════
with t5:
    section_label("INDEX CONSTITUENTS")
    idx_c2 = get_index_constituents()
    c5a, c5b = st.columns([1, 3])

    with c5a:
        sel_const    = st.selectbox("Select Index", list(idx_c2.keys()), key="const_idx")
        const_period = st.selectbox("Period", ["1D","1W","1M","3M","6M","1Y"], index=2, key="const_p")
        show_hmap    = st.checkbox("Show Heatmap", value=True)

    constituents = idx_c2.get(sel_const, [])
    TFC3 = {"1D":"5d","1W":"1mo","1M":"3mo","3M":"6mo","6M":"1y","1Y":"2y"}
    cp3  = TFC3[const_period]

    with c5b:
        if not constituents:
            st.info(f"No constituent data for {sel_const}.")
        else:
            @st.cache_data(ttl=120)
            def fetch_constituent_perf_parallel(syms: tuple, period: str) -> pd.DataFrame:
                """Parallel constituent performance — replaces sequential loop."""
                def _one(sym: str) -> dict | None:
                    try:
                        df_c = get_ohlcv(sym, period, "1d")
                        if df_c is not None and not df_c.empty:
                            lp = float(df_c["Close"].iloc[-1])
                            fp = float(df_c["Close"].iloc[0])
                            pct = (lp / fp - 1) * 100
                            meta = NSE_STOCKS_EXTENDED.get(sym, {})
                            return {"Symbol": sym, "Name": meta.get("name", sym)[:22],
                                    "Sector": meta.get("sector",""), "Return%": round(pct,2), "Price": round(lp,2)}
                    except Exception:
                        return None

                rows = []
                with ThreadPoolExecutor(max_workers=12) as ex:
                    futures = {ex.submit(_one, sym): sym for sym in syms}
                    for future in as_completed(futures, timeout=30):
                        try:
                            r = future.result()
                            if r: rows.append(r)
                        except Exception: pass
                return pd.DataFrame(rows) if rows else pd.DataFrame()

            with st.spinner(f"Fetching {len(constituents)} constituents (parallel)..."):
                const_df = fetch_constituent_perf_parallel(tuple(constituents), cp3)

            if not const_df.empty:
                const_df = const_df.sort_values("Return%", ascending=False)

                if show_hmap:
                    # Grid heatmap (light theme)
                    fig_ch = go.Figure()
                    n_cols = 8
                    n_rows_c = (len(const_df) + n_cols - 1) // n_cols
                    for idx_r, row in const_df.reset_index(drop=True).iterrows():
                        col_pos = idx_r % n_cols
                        row_pos = idx_r // n_cols
                        pct = row["Return%"]
                        if   pct >  4: bg, txt = "rgba(22,163,74,0.90)",  "#FFFFFF"
                        elif pct >  2: bg, txt = "rgba(22,163,74,0.65)",  "#FFFFFF"
                        elif pct >  0: bg, txt = "rgba(22,163,74,0.22)",  "#15803D"
                        elif pct > -2: bg, txt = "rgba(220,38,38,0.22)",  "#DC2626"
                        elif pct > -4: bg, txt = "rgba(220,38,38,0.65)",  "#FFFFFF"
                        else:          bg, txt = "rgba(220,38,38,0.90)",  "#FFFFFF"

                        fig_ch.add_shape(type="rect",
                            x0=col_pos-.46, x1=col_pos+.46, y0=row_pos-.46, y1=row_pos+.46,
                            fillcolor=bg, line=dict(color="#FFFFFF", width=2))
                        fig_ch.add_annotation(x=col_pos, y=row_pos,
                            text=f"<b>{row['Symbol']}</b><br>{pct:+.1f}%",
                            showarrow=False, font=dict(size=9, color=txt), align="center")

                    fig_ch.update_layout(
                        height=max(200, n_rows_c * 72 + 40),
                        paper_bgcolor="#FFFFFF", plot_bgcolor="#F7F9FD",
                        margin=dict(l=0,r=0,t=10,b=0), showlegend=False,
                        xaxis=dict(showgrid=False,showticklabels=False,zeroline=False,range=[-.6,n_cols-.4]),
                        yaxis=dict(showgrid=False,showticklabels=False,zeroline=False,
                                   range=[-.6,n_rows_c-.4],autorange="reversed"),
                    )
                    st.plotly_chart(fig_ch, use_container_width=True)

                # Table
                def _c3(v):
                    if pd.isna(v): return "color:var(--t3)"
                    return "color:var(--green)" if v > 0 else "color:var(--red)"
                st.dataframe(
                    const_df.style.applymap(_c3, subset=["Return%"])
                                  .format({"Return%":"{:+.2f}%","Price":"₹{:.2f}"}, na_rep="—"),
                    use_container_width=True, height=400,
                )
            else:
                st.info("Could not fetch constituent data. Try refreshing.")
