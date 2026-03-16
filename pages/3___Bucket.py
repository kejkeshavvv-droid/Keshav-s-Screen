"""
3___Bucket.py — Keshav's Screen
Watchlist · Performance Comparison · Fundamentals · Correlation · Risk Analytics
Fixes: Issues #9 #10 (titlefont → title.font), #11 (missing bucket heatmap tab)
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import yfinance as yf
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.nse_stocks import NSE_STOCKS_EXTENDED, INDICES, NIFTY50_STOCKS, yf_ticker
from utils.data_fetcher import get_ohlcv, get_fundamentals, get_live_price, get_live_prices_batch
from utils.technical_analysis import rsi, macd, sma, historical_volatility
from utils.styles import inject_css, section_label, PLOTLY_LAYOUT, CHART_COLORS

st.set_page_config(
    page_title="Bucket — Keshav's Screen",
    page_icon="K",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()

st.markdown('<h2 style="margin-bottom:2px;">Stock Bucket</h2>', unsafe_allow_html=True)
st.markdown(
    '<p style="color:var(--t3);font-size:.85rem;">Watchlist · Performance comparison · Correlation · Risk analytics</p>',
    unsafe_allow_html=True,
)

# ─── SESSION STATE ────────────────────────────────────────────────────────────
if "bucket" not in st.session_state:
    st.session_state["bucket"] = [
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
        "BAJFINANCE", "SUNPHARMA", "MARUTI",
    ]

bucket = st.session_state["bucket"]

# ─── BUCKET MANAGEMENT ────────────────────────────────────────────────────────
all_opts = list(NSE_STOCKS_EXTENDED.keys()) + list(INDICES.keys())

m1, m2, m3, m4 = st.columns([4, 1, 1, 1])
with m1:
    add_sym = st.selectbox(
        "Add to Bucket", [""] + all_opts,
        format_func=lambda x: "" if x == "" else
            f"{x}  —  {NSE_STOCKS_EXTENDED.get(x, {}).get('name', INDICES.get(x, x))}",
        key="bucket_add_sel",
    )
with m2:
    if st.button("Add", use_container_width=True) and add_sym and add_sym not in bucket:
        st.session_state["bucket"].append(add_sym)
        st.rerun()
with m3:
    if st.button("Clear All", use_container_width=True):
        st.session_state["bucket"] = []
        st.rerun()
with m4:
    if st.button("Add NIFTY 50", use_container_width=True):
        existing = set(st.session_state["bucket"])
        for s in NIFTY50_STOCKS[:10]:
            if s not in existing:
                st.session_state["bucket"].append(s)
        st.rerun()

if not bucket:
    st.info("Your bucket is empty. Add stocks above, or use the Screener's 'Add to Bucket' button.")
    st.stop()

# ─── REMOVE CHIPS ─────────────────────────────────────────────────────────────
section_label("BUCKET CONTENTS  —  Click to Remove")
chip_cols = st.columns(min(len(bucket), 10))
for i, sym in enumerate(bucket[:10]):
    with chip_cols[i]:
        if st.button(f"x {sym}", key=f"rm_{sym}_{i}", use_container_width=True):
            st.session_state["bucket"].remove(sym)
            st.rerun()
if len(bucket) > 10:
    st.caption(f"...and {len(bucket) - 10} more")

st.markdown("---")

# ─── LIVE SNAPSHOT — PARALLEL FETCH ──────────────────────────────────────────
section_label("LIVE SNAPSHOT")

with st.spinner("Fetching live prices..."):
    live_prices = get_live_prices_batch(tuple(bucket))

snap = []
for sym in bucket:
    lp = live_prices.get(sym, {})
    p   = lp.get("price")
    pct = lp.get("pct", 0)
    chg = lp.get("change", 0)
    meta = NSE_STOCKS_EXTENDED.get(sym, {})
    snap.append({
        "Symbol":    sym,
        "Name":      meta.get("name", sym)[:22],
        "Price":     p,
        "Change":    chg,
        "Change%":   pct,
        "Sector":    meta.get("sector", ""),
        "Mkt Cap (Cr)": lp.get("mktcap", 0) or 0,
    })

snap_df = pd.DataFrame(snap)

# Cards
card_per_row = 5
for row_start in range(0, min(len(snap), 15), card_per_row):
    row_syms = snap[row_start:row_start + card_per_row]
    cols = st.columns(card_per_row)
    for i, s in enumerate(row_syms):
        with cols[i]:
            p   = s.get("Price")
            pct = s.get("Change%", 0)
            clr     = "var(--green)" if pct >= 0 else "var(--red)"
            clr_bg  = "var(--green-bg)"  if pct >= 0 else "var(--red-bg)"
            clr_bdr = "#BBF7D0" if pct >= 0 else "#FCA5A5"
            arr  = "+" if pct >= 0 else ""
            pstr = f"₹{p:,.2f}" if p else "—"
            st.markdown(f"""
            <div style="background:{clr_bg};border:1px solid {clr_bdr};
                        border-radius:9px;padding:10px 8px;text-align:center;
                        box-shadow:var(--shadow-sm);">
              <div style="color:var(--t3);font-size:.62rem;font-weight:700;
                          text-transform:uppercase;letter-spacing:.5px;">{s['Symbol']}</div>
              <div style="color:var(--t1);font-size:1rem;font-weight:700;
                          font-family:'JetBrains Mono',monospace;margin:3px 0;">{pstr}</div>
              <div style="color:{clr};font-size:.78rem;font-weight:600;">{arr}{pct:+.2f}%</div>
              <div style="color:var(--t4);font-size:.62rem;margin-top:2px;">{s.get('Sector','')}</div>
            </div>""", unsafe_allow_html=True)

st.markdown("---")

# ─── ANALYSIS TABS ────────────────────────────────────────────────────────────
t1, t2, t3, t4, t5, t6 = st.tabs([
    "Performance", "Heatmap", "Fundamentals", "Correlation", "Risk", "Summary",
])

# ── TAB 1: PERFORMANCE ────────────────────────────────────────────────────────
with t1:
    pa, pb = st.columns([3, 1])
    with pb:
        perf_period = st.selectbox("Period", ["1M","3M","6M","1Y","2Y","5Y"], index=3, key="perf_p")
        perf_type   = st.selectbox("Display", ["Normalised % (base 100)", "Absolute Price"], key="perf_t")
        show_bm     = st.checkbox("Show NIFTY 50 benchmark", value=True)

    TFP = {"1M":"3mo","3M":"6mo","6M":"1y","1Y":"2y","2Y":"5y","5Y":"10y"}
    period_yf = TFP[perf_period]

    with pa:
        fig_p  = go.Figure()
        returns_data = {}

        if show_bm:
            bdf = get_ohlcv("^NSEI", period_yf, "1d")
            if bdf is not None and not bdf.empty:
                base = float(bdf["Close"].iloc[0])
                vals = bdf["Close"] / base * 100 if "Norm" in perf_type else bdf["Close"]
                fig_p.add_trace(go.Scatter(
                    x=bdf.index, y=vals, mode="lines",
                    line=dict(color="#8896B0", width=1.5, dash="dot"),
                    name="NIFTY 50 (BM)",
                ))
                returns_data["NIFTY 50"] = (float(bdf["Close"].iloc[-1]) - base) / base * 100

        for i, sym in enumerate(bucket[:12]):
            df = get_ohlcv(sym, period_yf, "1d")
            if df is None or df.empty:
                continue
            base = float(df["Close"].iloc[0])
            vals = df["Close"] / base * 100 if "Norm" in perf_type else df["Close"]
            clr  = CHART_COLORS[i % len(CHART_COLORS)]
            fig_p.add_trace(go.Scatter(
                x=df.index, y=vals, mode="lines",
                line=dict(color=clr, width=1.4), name=sym,
            ))
            returns_data[sym] = (float(df["Close"].iloc[-1]) - base) / base * 100

        fig_p.update_layout(
            **{
                **PLOTLY_LAYOUT,
                "height": 400,
                "yaxis": {**PLOTLY_LAYOUT["yaxis"],
                          "ticksuffix": "%" if "Norm" in perf_type else ""},
            }
        )
        st.plotly_chart(fig_p, use_container_width=True)

    # Returns bar chart
    if returns_data:
        sorted_r = dict(sorted(returns_data.items(), key=lambda x: x[1], reverse=True))
        bc = ["rgba(22,163,74,0.8)" if v >= 0 else "rgba(220,38,38,0.8)" for v in sorted_r.values()]
        fig_r = go.Figure(go.Bar(
            x=list(sorted_r.keys()), y=list(sorted_r.values()),
            marker_color=bc,
            text=[f"{v:+.1f}%" for v in sorted_r.values()],
            textposition="outside",
            textfont=dict(color="#2D3A52", size=10),
        ))
        fig_r.update_layout(
            **{**PLOTLY_LAYOUT,
               "height": 250,
               "title": f"Returns — {perf_period}",
               "yaxis": {**PLOTLY_LAYOUT["yaxis"],
                         "ticksuffix": "%", "zeroline": True,
                         "zerolinecolor": "#DDE3EF"},
            }
        )
        st.plotly_chart(fig_r, use_container_width=True)


# ── TAB 2: BUCKET HEATMAP (Issue #11 — new tab) ───────────────────────────────
with t2:
    section_label("BUCKET STOCKS — HEATMAP")
    st.caption("Color intensity shows today's price change. Darker green = bigger gain, darker red = bigger loss.")

    if len(bucket) < 1:
        st.info("Add stocks to your bucket to see the heatmap.")
    else:
        # Reuse the already-fetched live prices
        hm_data = []
        for sym in bucket:
            lp = live_prices.get(sym, {})
            p   = lp.get("price", 0) or 0
            pct = lp.get("pct", 0) or 0
            meta = NSE_STOCKS_EXTENDED.get(sym, {})
            hm_data.append({
                "Symbol":  sym,
                "Name":    meta.get("name", sym)[:18],
                "Sector":  meta.get("sector", "Other"),
                "Change%": round(pct, 2),
                "Price":   round(p, 2),
            })

        hm_df = pd.DataFrame(hm_data).sort_values("Sector")
        n = len(hm_df)
        cols_per_row = min(8, n)

        hm_df["row"] = hm_df.reset_index().index // cols_per_row
        hm_df["col"] = hm_df.reset_index().index % cols_per_row
        n_rows = int(hm_df["row"].max()) + 1

        fig_hm = go.Figure()
        for _, row in hm_df.iterrows():
            pct = row["Change%"]
            # Light theme color scale: white center, green positive, red negative
            if   pct >  4:  bg = "rgba(22,163,74,0.90)";  txt = "#FFFFFF"
            elif pct >  2:  bg = "rgba(22,163,74,0.65)";  txt = "#FFFFFF"
            elif pct >  0:  bg = "rgba(22,163,74,0.25)";  txt = "#15803D"
            elif pct > -2:  bg = "rgba(220,38,38,0.25)";  txt = "#DC2626"
            elif pct > -4:  bg = "rgba(220,38,38,0.65)";  txt = "#FFFFFF"
            else:            bg = "rgba(220,38,38,0.90)";  txt = "#FFFFFF"

            fig_hm.add_shape(
                type="rect",
                x0=row["col"] - 0.47, x1=row["col"] + 0.47,
                y0=row["row"] - 0.47, y1=row["row"] + 0.47,
                fillcolor=bg,
                line=dict(color="#FFFFFF", width=2),
            )
            fig_hm.add_annotation(
                x=row["col"], y=row["row"],
                text=f"<b>{row['Symbol']}</b><br>{pct:+.2f}%",
                showarrow=False,
                font=dict(size=9, color=txt),
                align="center",
            )

        fig_hm.update_layout(
            height=max(200, n_rows * 80 + 40),
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#F7F9FD",
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False,
                       range=[-0.6, cols_per_row - 0.4]),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False,
                       range=[-0.6, n_rows - 0.4], autorange="reversed"),
            showlegend=False,
        )
        st.plotly_chart(fig_hm, use_container_width=True)

        # Summary stats
        pos  = (hm_df["Change%"] > 0).sum()
        neg  = (hm_df["Change%"] < 0).sum()
        flat = len(hm_df) - pos - neg
        avg  = hm_df["Change%"].mean()
        best  = hm_df.loc[hm_df["Change%"].idxmax()]
        worst = hm_df.loc[hm_df["Change%"].idxmin()]

        s1, s2, s3, s4, s5 = st.columns(5)
        for col, lbl, val, clr in [
            (s1, "Advancing",  pos,   "var(--green)"),
            (s2, "Declining",  neg,   "var(--red)"),
            (s3, "Unchanged",  flat,  "var(--t3)"),
            (s4, "Best",   f"{best['Symbol']} {best['Change%']:+.2f}%",  "var(--green)"),
            (s5, "Worst",  f"{worst['Symbol']} {worst['Change%']:+.2f}%","var(--red)"),
        ]:
            with col:
                st.markdown(f"""
                <div class="ks-stat-card" style="text-align:center;">
                  <div style="color:{clr};font-size:1.1rem;font-weight:700;
                               font-family:'JetBrains Mono',monospace;">{val}</div>
                  <div style="color:var(--t3);font-size:.7rem;font-weight:600;
                               text-transform:uppercase;letter-spacing:.5px;">{lbl}</div>
                </div>""", unsafe_allow_html=True)


# ── TAB 3: FUNDAMENTALS ───────────────────────────────────────────────────────
with t3:
    fund_rows = []
    with st.spinner("Fetching fundamentals..."):
        for sym in bucket[:15]:
            try:
                t_ = yf.Ticker(yf_ticker(sym))
                i_ = t_.info
                meta = NSE_STOCKS_EXTENDED.get(sym, {})
                fund_rows.append({
                    "Symbol":          sym,
                    "Name":            (i_.get("longName", sym))[:25],
                    "Sector":          i_.get("sector", meta.get("sector", "")),
                    "Price":           i_.get("currentPrice") or i_.get("regularMarketPrice"),
                    "Market Cap (Cr)": round((i_.get("marketCap") or 0) / 1e7, 0),
                    "P/E":             i_.get("trailingPE"),
                    "P/B":             i_.get("priceToBook"),
                    "PEG":             i_.get("pegRatio"),
                    "EV/EBITDA":       i_.get("enterpriseToEbitda"),
                    "EPS":             i_.get("trailingEps"),
                    "ROE (%)":         round((i_.get("returnOnEquity")   or 0) * 100, 2),
                    "ROA (%)":         round((i_.get("returnOnAssets")   or 0) * 100, 2),
                    "Net Margin (%)":  round((i_.get("profitMargins")    or 0) * 100, 2),
                    "OPM (%)":         round((i_.get("operatingMargins") or 0) * 100, 2),
                    "D/E":             i_.get("debtToEquity"),
                    "Current Ratio":   i_.get("currentRatio"),
                    "Div Yield (%)":   round((i_.get("dividendYield")   or 0) * 100, 2),
                    "Rev Growth (%)":  round((i_.get("revenueGrowth")   or 0) * 100, 2),
                    "EPS Growth (%)":  round((i_.get("earningsGrowth")  or 0) * 100, 2),
                    "Beta":            i_.get("beta"),
                })
            except Exception:
                pass

    if fund_rows:
        fdf = pd.DataFrame(fund_rows)

        def _color_fund(val):
            if pd.isna(val) or not isinstance(val, (int, float)):
                return "color:var(--t3)"
            return "color:var(--green)" if val > 0 else "color:var(--red)" if val < 0 else "color:var(--t1)"

        pct_cols = [c for c in ["ROE (%)", "ROA (%)", "Net Margin (%)", "OPM (%)",
                                 "Rev Growth (%)", "EPS Growth (%)"] if c in fdf.columns]
        fmt_map = {
            "Price": "₹{:.2f}", "Market Cap (Cr)": "{:,.0f}",
            "P/E": "{:.1f}", "P/B": "{:.2f}", "EPS": "{:.2f}",
            "ROE (%)": "{:.1f}%", "ROA (%)": "{:.1f}%",
            "Net Margin (%)": "{:.1f}%", "OPM (%)": "{:.1f}%",
            "D/E": "{:.2f}", "Current Ratio": "{:.2f}",
            "Div Yield (%)": "{:.2f}%", "Rev Growth (%)": "{:.1f}%",
            "EPS Growth (%)": "{:.1f}%", "Beta": "{:.2f}",
        }
        fmt_map = {k: v for k, v in fmt_map.items() if k in fdf.columns}

        st.dataframe(
            fdf.style.applymap(_color_fund, subset=pct_cols).format(fmt_map, na_rep="—"),
            use_container_width=True, height=500,
        )

        # Radar chart
        section_label("MULTI-METRIC RADAR — TOP 5 BY ROE")
        metrics_r = ["ROE (%)", "Net Margin (%)", "OPM (%)", "Rev Growth (%)", "EPS Growth (%)"]
        avail_r   = [m for m in metrics_r if m in fdf.columns]
        if len(avail_r) >= 3:
            top5 = fdf.nlargest(min(5, len(fdf)), "ROE (%)")[["Symbol"] + avail_r].dropna(subset=avail_r)
            if not top5.empty:
                normed = top5.copy()
                for m in avail_r:
                    mn = normed[m].min(); mx = normed[m].max()
                    normed[m] = ((normed[m] - mn) / max(mx - mn, 1e-9)) * 100

                fig_rad = go.Figure()
                for ri, row in normed.iterrows():
                    vals = [float(row[m]) for m in avail_r] + [float(row[avail_r[0]])]
                    clr  = CHART_COLORS[list(normed.index).index(ri) % len(CHART_COLORS)]
                    # Convert hex to rgba for fill
                    fig_rad.add_trace(go.Scatterpolar(
                        r=vals, theta=avail_r + [avail_r[0]],
                        fill="toself",
                        fillcolor=clr + "26",  # ~15% opacity
                        line=dict(color=clr, width=1.5),
                        name=row["Symbol"],
                    ))
                fig_rad.update_layout(
                    polar=dict(
                        bgcolor="#F7F9FD",
                        radialaxis=dict(visible=True, range=[0, 100],
                                        color="#8896B0", gridcolor="#DDE3EF"),
                        angularaxis=dict(color="#5A6A88"),
                    ),
                    height=380,
                    paper_bgcolor="#FFFFFF",
                    legend=dict(bgcolor="#FFFFFF", bordercolor="#DDE3EF",
                                font=dict(color="#2D3A52", size=10)),
                    margin=dict(l=30, r=30, t=10, b=10),
                )
                st.plotly_chart(fig_rad, use_container_width=True)


# ── TAB 4: CORRELATION ────────────────────────────────────────────────────────
with t4:
    c3a, c3b = st.columns([1, 3])
    with c3a:
        corr_period = st.selectbox("Period", ["3M","6M","1Y","2Y"], index=2, key="corr_p")
        corr_method = st.selectbox("Method", ["Pearson","Spearman","Kendall"], key="corr_m")
        use_returns = st.checkbox("Use daily returns (recommended)", value=True)

    TFC = {"3M":"6mo","6M":"1y","1Y":"2y","2Y":"5y"}
    cp  = TFC[corr_period]

    with st.spinner("Building correlation matrix..."):
        price_dict = {}
        for sym in bucket[:15]:
            df = get_ohlcv(sym, cp, "1d")
            if df is not None and not df.empty:
                price_dict[sym] = df["Close"].pct_change().dropna() if use_returns else df["Close"]

    if len(price_dict) >= 2:
        price_frame = pd.DataFrame(price_dict).dropna()
        corr_mat    = price_frame.corr(method=corr_method.lower())

        with c3b:
            # ── FIX Issues #9 & #10: use title=dict(font=...) not titlefont ──
            fig_c = go.Figure(go.Heatmap(
                z=corr_mat.values,
                x=corr_mat.columns.tolist(),
                y=corr_mat.index.tolist(),
                colorscale=[[0,"#DC2626"],[0.5,"#FFFFFF"],[1,"#16A34A"]],
                zmid=0, zmin=-1, zmax=1,
                text=[[f"{v:.2f}" for v in row] for row in corr_mat.values],
                texttemplate="%{text}",
                textfont=dict(size=10, color="#0F172A"),
                colorbar=dict(
                    tickfont=dict(color="#5A6A88"),
                    title=dict(text="Corr", font=dict(color="#5A6A88")),  # FIX: was titlefont
                ),
            ))
            fig_c.update_layout(
                **{**PLOTLY_LAYOUT,
                   "height": 500,
                   "title": f"{corr_method} Correlation — {corr_period}",
                   "xaxis": {**PLOTLY_LAYOUT["xaxis"], "tickangle": -35},
                }
            )
            st.plotly_chart(fig_c, use_container_width=True)

        # Highly correlated pairs
        section_label("HIGHLY CORRELATED PAIRS  (|r| > 0.75)")
        pairs = []
        syms = corr_mat.columns.tolist()
        for i in range(len(syms)):
            for j in range(i + 1, len(syms)):
                v = corr_mat.iloc[i, j]
                if abs(v) > 0.75:
                    pairs.append({"Stock A": syms[i], "Stock B": syms[j],
                                   "Correlation": round(v, 4),
                                   "Type": "Positive" if v > 0 else "Negative"})
        if pairs:
            pairs_df = pd.DataFrame(pairs).sort_values("Correlation", key=abs, ascending=False)
            st.dataframe(pairs_df, use_container_width=True, height=200)
        else:
            st.info("No pairs with |correlation| > 0.75 found.")

        # Rolling correlation
        section_label("ROLLING CORRELATION")
        rc1, rc2 = st.columns(2)
        with rc1:
            sym_a = st.selectbox("Stock A", list(price_dict.keys()), key="rca")
        with rc2:
            sym_b_opts = [s for s in price_dict.keys() if s != sym_a]
            sym_b = st.selectbox("Stock B", sym_b_opts, key="rcb") if sym_b_opts else None

        if sym_b:
            roll_window = st.slider("Rolling window (days)", 10, 90, 30)
            r_corr = price_dict[sym_a].rolling(roll_window).corr(price_dict[sym_b]).dropna()
            fig_rc = go.Figure()
            fig_rc.add_trace(go.Scatter(
                x=r_corr.index, y=r_corr.values, mode="lines",
                line=dict(color="#1D4ED8", width=1.5),
                name=f"Rolling {roll_window}d Corr",
                fill="tozeroy", fillcolor="rgba(29,78,216,.06)",
            ))
            fig_rc.add_hline(y=0,     line=dict(color="#DDE3EF", width=1))
            fig_rc.add_hline(y=0.75,  line=dict(color="#16A34A", width=.7, dash="dash"))
            fig_rc.add_hline(y=-0.75, line=dict(color="#DC2626", width=.7, dash="dash"))
            fig_rc.update_layout(
                **{**PLOTLY_LAYOUT,
                   "height": 250,
                   "title": f"Rolling {roll_window}d Correlation: {sym_a} vs {sym_b}",
                   "yaxis": {**PLOTLY_LAYOUT["yaxis"], "range": [-1.1, 1.1]},
                }
            )
            st.plotly_chart(fig_rc, use_container_width=True)
    else:
        st.warning("Add at least 2 stocks to compute correlations.")


# ── TAB 5: RISK & VOLATILITY ──────────────────────────────────────────────────
with t5:
    risk_period = st.selectbox("Analysis Period", ["6M","1Y","2Y","3Y"], index=1, key="risk_p")
    TFR = {"6M":"1y","1Y":"2y","2Y":"5y","3Y":"10y"}
    rp  = TFR[risk_period]

    risk_rows = []
    with st.spinner("Computing risk metrics..."):
        for sym in bucket[:12]:
            df = get_ohlcv(sym, rp, "1d")
            if df is None or df.empty:
                continue
            rets = df["Close"].pct_change().dropna()
            if len(rets) < 30:
                continue

            ann_ret  = float(np.mean(rets)) * 252
            ann_vol  = float(np.std(rets))  * np.sqrt(252)
            sharpe   = ann_ret / ann_vol if ann_vol > 0 else 0
            max_dd   = float(((df["Close"] / df["Close"].cummax()) - 1).min())
            var_95   = float(np.percentile(rets, 5))
            cvar_95  = float(rets[rets <= var_95].mean())
            skew     = float(rets.skew())
            kurt     = float(rets.kurtosis())
            sortino_d = float(rets[rets < 0].std()) * np.sqrt(252)
            sortino  = ann_ret / sortino_d if sortino_d > 0 else 0

            beta = None
            try:
                ndf = get_ohlcv("^NSEI", rp, "1d")
                if ndf is not None and not ndf.empty:
                    nr = ndf["Close"].pct_change().dropna()
                    aligned = pd.concat([rets, nr], axis=1).dropna()
                    if len(aligned) > 30:
                        cov  = aligned.cov().iloc[0, 1]
                        var_ = aligned.iloc[:, 1].var()
                        beta = cov / var_ if var_ > 0 else None
            except Exception:
                pass

            risk_rows.append({
                "Symbol":            sym,
                "Ann. Return":       round(ann_ret * 100, 2),
                "Ann. Volatility":   round(ann_vol * 100, 2),
                "Sharpe Ratio":      round(sharpe, 2),
                "Sortino Ratio":     round(sortino, 2),
                "Max Drawdown":      round(max_dd * 100, 2),
                "VaR 95% (1d)":      round(var_95 * 100, 3),
                "CVaR 95% (1d)":     round(cvar_95 * 100, 3),
                "Beta":              round(beta, 3) if beta is not None else None,
                "Skewness":          round(skew, 3),
                "Kurtosis":          round(kurt, 3),
            })

    if risk_rows:
        rdf = pd.DataFrame(risk_rows)

        def _color_risk(val, col):
            if pd.isna(val): return "color:var(--t3)"
            if col == "Ann. Return":  return "color:var(--green)" if val > 0 else "color:var(--red)"
            if col == "Sharpe Ratio": return "color:var(--green)" if val > 1 else "color:var(--gold)" if val > 0 else "color:var(--red)"
            if col == "Max Drawdown": return "color:var(--red)" if val < -20 else "color:var(--gold)" if val < -10 else "color:var(--green)"
            return "color:var(--t1)"

        st.dataframe(
            rdf.style
               .applymap(lambda v: _color_risk(v, "Ann. Return"),  subset=["Ann. Return"])
               .applymap(lambda v: _color_risk(v, "Sharpe Ratio"), subset=["Sharpe Ratio"])
               .applymap(lambda v: _color_risk(v, "Max Drawdown"), subset=["Max Drawdown"])
               .format({
                   "Ann. Return": "{:.2f}%", "Ann. Volatility": "{:.2f}%",
                   "Max Drawdown": "{:.2f}%", "VaR 95% (1d)": "{:.3f}%",
                   "CVaR 95% (1d)": "{:.3f}%",
               }, na_rep="—"),
            use_container_width=True, height=380,
        )

        # Risk-Return scatter
        # ── FIX Issues #9 & #10: colorbar uses title=dict(font=...) not titlefont ──
        if len(rdf) >= 2:
            fig_rr = go.Figure()
            fig_rr.add_trace(go.Scatter(
                x=rdf["Ann. Volatility"], y=rdf["Ann. Return"],
                mode="markers+text",
                text=rdf["Symbol"],
                textposition="top center",
                textfont=dict(color="#2D3A52", size=10),
                marker=dict(
                    size=14,
                    color=rdf["Sharpe Ratio"],
                    colorscale=[[0,"#DC2626"],[0.5,"#D97706"],[1,"#16A34A"]],
                    showscale=True,
                    colorbar=dict(
                        title=dict(text="Sharpe", font=dict(color="#5A6A88")),  # FIX: was titlefont
                        tickfont=dict(color="#5A6A88"),
                        bgcolor="#FFFFFF",
                        bordercolor="#DDE3EF",
                        borderwidth=1,
                    ),
                    line=dict(width=1, color="#FFFFFF"),
                ),
                name="Stocks",
            ))
            fig_rr.add_hline(y=0, line=dict(color="#DDE3EF", width=1))
            fig_rr.add_vline(
                x=float(rdf["Ann. Volatility"].mean()),
                line=dict(color="#C8D0E4", width=.8, dash="dash"),
            )
            fig_rr.update_layout(
                **{**PLOTLY_LAYOUT,
                   "height": 380,
                   "title": "Risk-Return Scatter (color = Sharpe ratio)",
                   "xaxis": {**PLOTLY_LAYOUT["xaxis"],
                              "title": "Ann. Volatility (%)", "side": "bottom"},
                   "yaxis": {**PLOTLY_LAYOUT["yaxis"],
                              "title": "Ann. Return (%)", "side": "right"},
                }
            )
            st.plotly_chart(fig_rr, use_container_width=True)

        # Drawdown chart
        section_label("DRAWDOWN CHART")
        fig_dd = go.Figure()
        for i, sym in enumerate(bucket[:6]):
            df = get_ohlcv(sym, rp, "1d")
            if df is not None and not df.empty:
                dd = (df["Close"] / df["Close"].cummax() - 1) * 100
                clr = CHART_COLORS[i % len(CHART_COLORS)]
                fig_dd.add_trace(go.Scatter(
                    x=df.index, y=dd, mode="lines",
                    line=dict(color=clr, width=1.2),
                    fill="tozeroy",
                    fillcolor=clr + "18",  # ~10% opacity
                    name=sym,
                ))
        fig_dd.update_layout(
            **{**PLOTLY_LAYOUT,
               "height": 280,
               "yaxis": {**PLOTLY_LAYOUT["yaxis"], "ticksuffix": "%"},
            }
        )
        st.plotly_chart(fig_dd, use_container_width=True)


# ── TAB 6: SUMMARY TABLE ──────────────────────────────────────────────────────
with t6:
    section_label("COMPLETE BUCKET OVERVIEW")
    if not snap_df.empty:
        # Add fundamentals columns from live data if available
        disp_cols = [c for c in ["Symbol","Name","Sector","Price","Change%","Mkt Cap (Cr)"] if c in snap_df.columns]
        show_snap = snap_df[disp_cols].copy()

        def _cs(v):
            if pd.isna(v) or not isinstance(v, (int, float)): return "color:var(--t3)"
            return "color:var(--green)" if v > 0 else "color:var(--red)"

        fmt_s = {k: v for k, v in {
            "Price": "₹{:.2f}", "Change%": "{:+.2f}%", "Mkt Cap (Cr)": "{:,.0f}",
        }.items() if k in show_snap.columns}

        st.dataframe(
            show_snap.style.applymap(_cs, subset=[c for c in ["Change%"] if c in show_snap.columns])
                           .format(fmt_s, na_rep="—"),
            use_container_width=True, height=600,
        )
        st.download_button(
            "Export Bucket CSV",
            data=snap_df.to_csv(index=False),
            file_name="keshav_bucket.csv",
            mime="text/csv",
        )
