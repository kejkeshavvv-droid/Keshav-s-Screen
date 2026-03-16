"""
4____Heatmap.py — Keshav's Screen
Market Heatmap · Treemap · Sector Drill-Down · Index Correlation
Fixes: Issue #12 (all 4 tabs now working), titlefont removed, parallel parallel data fetch
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.nse_stocks import NSE_STOCKS_EXTENDED, INDICES, NIFTY50_STOCKS, yf_ticker, get_index_constituents, get_stocks_by_sector
from utils.data_fetcher import get_ohlcv, fetch_heatmap_data
from utils.styles import inject_css, section_label, PLOTLY_LAYOUT, CHART_COLORS

st.set_page_config(
    page_title="Heatmap — Keshav's Screen",
    page_icon="K",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()

st.markdown('<h2 style="margin-bottom:2px;">Market Heatmap</h2>', unsafe_allow_html=True)
st.markdown(
    '<p style="color:var(--t3);font-size:.85rem;">'
    'Visual market overview — Stock Heatmap · Treemap · Sector Drill-Down · Index Correlation</p>',
    unsafe_allow_html=True,
)

# ─── TABS ─────────────────────────────────────────────────────────────────────
t1, t2, t3, t4 = st.tabs([
    "Stock Heatmap", "Treemap", "Sector Drill-Down", "Index Correlation",
])

# ─── SHARED HELPERS ───────────────────────────────────────────────────────────
UP   = "#16A34A"
DOWN = "#DC2626"

def _pct_color_bg(pct: float) -> tuple[str, str]:
    """(bg_rgba, text_color) for a heatmap cell based on % change."""
    if   pct >  4: return "rgba(22,163,74,0.90)",  "#FFFFFF"
    elif pct >  2: return "rgba(22,163,74,0.65)",  "#FFFFFF"
    elif pct >  0: return "rgba(22,163,74,0.22)",  "#15803D"
    elif pct > -2: return "rgba(220,38,38,0.22)",  "#DC2626"
    elif pct > -4: return "rgba(220,38,38,0.65)",  "#FFFFFF"
    else:          return "rgba(220,38,38,0.90)",  "#FFFFFF"


def _build_grid_heatmap(hdf: pd.DataFrame, cols_per_row: int = 10) -> go.Figure:
    """Build a grid-style heatmap figure from a DataFrame with Symbol and Change%."""
    hdf = hdf.reset_index(drop=True)
    hdf["row"] = hdf.index // cols_per_row
    hdf["col"] = hdf.index % cols_per_row
    n_rows = int(hdf["row"].max()) + 1

    fig = go.Figure()
    for _, row in hdf.iterrows():
        pct = row.get("Change%", 0) or 0
        bg, txt = _pct_color_bg(pct)
        fig.add_shape(
            type="rect",
            x0=row["col"] - 0.47, x1=row["col"] + 0.47,
            y0=row["row"] - 0.47, y1=row["row"] + 0.47,
            fillcolor=bg,
            line=dict(color="#FFFFFF", width=2),
        )
        fig.add_annotation(
            x=row["col"], y=row["row"],
            text=f"<b>{row['Symbol']}</b><br>{pct:+.2f}%",
            showarrow=False,
            font=dict(size=9, color=txt),
            align="center",
        )

    fig.update_layout(
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
    return fig


# ══════════════════════════════════════════════════════
# TAB 1: STOCK HEATMAP
# ══════════════════════════════════════════════════════
with t1:
    h1a, h1b = st.columns([1, 4])
    with h1a:
        hm_universe = st.selectbox("Universe", [
            "NIFTY 50", "NIFTY BANK", "NIFTY IT", "NIFTY PHARMA",
            "NIFTY AUTO", "NIFTY FMCG", "NIFTY METAL", "NIFTY 100",
            "All NSE (top 100)", "Bucket",
        ], key="hm_uni")

        if st.button("Refresh Data", use_container_width=True, key="hm_ref"):
            st.cache_data.clear()
            st.rerun()

    idx_c = get_index_constituents()
    bucket_stocks = st.session_state.get("bucket", [])

    sym_map = {
        "NIFTY 50":        idx_c.get("NIFTY 50", NIFTY50_STOCKS),
        "NIFTY 100":       idx_c.get("NIFTY 50", []) + list(NSE_STOCKS_EXTENDED.keys())[:50],
        "NIFTY BANK":      idx_c.get("NIFTY BANK", []),
        "NIFTY IT":        idx_c.get("NIFTY IT", []),
        "NIFTY PHARMA":    idx_c.get("NIFTY PHARMA", []),
        "NIFTY AUTO":      idx_c.get("NIFTY AUTO", []),
        "NIFTY FMCG":      idx_c.get("NIFTY FMCG", []),
        "NIFTY METAL":     idx_c.get("NIFTY METAL", []),
        "All NSE (top 100)": list(NSE_STOCKS_EXTENDED.keys())[:100],
        "Bucket":          bucket_stocks,
    }
    symbols = sym_map.get(hm_universe, NIFTY50_STOCKS)

    with h1b:
        if not symbols:
            st.info("No stocks in this universe. Try another or add stocks to your bucket.")
        else:
            with st.spinner(f"Loading heatmap for {len(symbols)} stocks (parallel)..."):
                # Use the parallel fetch_heatmap_data from data_fetcher
                hdf = fetch_heatmap_data(tuple(symbols), max_n=80)

            if hdf.empty:
                st.warning("No data loaded. Please try refreshing.")
            else:
                hdf = hdf.sort_values("Sector")
                fig_hm = _build_grid_heatmap(hdf, cols_per_row=10)
                st.plotly_chart(fig_hm, use_container_width=True)

                # Summary stats
                pos = (hdf["Change%"] > 0).sum()
                neg = (hdf["Change%"] < 0).sum()
                avg = hdf["Change%"].mean()
                best  = hdf.loc[hdf["Change%"].idxmax()]
                worst = hdf.loc[hdf["Change%"].idxmin()]

                st.markdown(f"""
                <div style="display:flex;gap:24px;padding:10px 4px;font-size:.82rem;flex-wrap:wrap;">
                  <span style="color:var(--green);font-weight:600;">{pos} Advancing</span>
                  <span style="color:var(--red);font-weight:600;">{neg} Declining</span>
                  <span style="color:var(--t2);">Avg: <b style="color:{'var(--green)' if avg>=0 else 'var(--red)'};">{avg:+.2f}%</b></span>
                  <span style="color:var(--t3);">Best: <b style="color:var(--green);">{best['Symbol']} {best['Change%']:+.2f}%</b></span>
                  <span style="color:var(--t3);">Worst: <b style="color:var(--red);">{worst['Symbol']} {worst['Change%']:+.2f}%</b></span>
                </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
# TAB 2: TREEMAP
# ══════════════════════════════════════════════════════
with t2:
    tm_a, tm_b = st.columns([1, 4])
    with tm_a:
        tm_n = st.selectbox("Stocks to show", [50, 100, 150], index=1, key="tm_n")
        st.caption("Groups by sector, sized by market cap, colored by daily change.")

    with tm_b:
        with st.spinner("Building treemap (parallel fetch)..."):
            tree_df = fetch_heatmap_data(
                tuple(list(NSE_STOCKS_EXTENDED.keys())),
                max_n=tm_n,
            )

        if tree_df.empty:
            st.warning("No data loaded. Please try refreshing.")
        else:
            tree_df["MCap_safe"] = tree_df["MCap_Cr"].clip(lower=0.1)
            tree_df["AbsChg"]    = tree_df["Change%"].abs().clip(lower=0.01)

            sector_agg = tree_df.groupby("Sector").agg(
                SectorChange=("Change%",  "mean"),
                TotalMktCap =("MCap_Cr",  "sum"),
            ).reset_index()

            labels  = list(tree_df["Symbol"]) + list(sector_agg["Sector"]) + ["NSE Market"]
            parents = list(tree_df["Sector"]) + ["NSE Market"] * len(sector_agg) + [""]
            values  = list(tree_df["MCap_safe"].fillna(1)) + \
                      list(sector_agg["TotalMktCap"].fillna(1)) + \
                      [tree_df["MCap_safe"].sum()]
            color_v = list(tree_df["Change%"]) + list(sector_agg["SectorChange"]) + [0]
            text_l  = [f"{r['Symbol']}<br>{r['Change%']:+.2f}%" for _, r in tree_df.iterrows()] + \
                      [f"{r['Sector']}<br>{r['SectorChange']:+.2f}%" for _, r in sector_agg.iterrows()] + \
                      ["NSE"]

            fig_tm = go.Figure(go.Treemap(
                labels=labels,
                parents=parents,
                values=values,
                customdata=color_v,
                text=text_l,
                textinfo="text",
                marker=dict(
                    colors=color_v,
                    colorscale=[
                        [0,    "#B91C1C"],
                        [0.35, "#DC2626"],
                        [0.5,  "#F3F4F6"],
                        [0.65, "#16A34A"],
                        [1,    "#14532D"],
                    ],
                    cmid=0, cmin=-5, cmax=5,
                    # ── FIX: no titlefont — use title=dict(font=...) ──
                    colorbar=dict(
                        tickvals=[-5,-3,-1,0,1,3,5],
                        ticktext=["-5%","-3%","-1%","0","+1%","+3%","+5%"],
                        tickfont=dict(color="#5A6A88"),
                        title=dict(text="Change%", font=dict(color="#5A6A88")),
                        bgcolor="#FFFFFF",
                        bordercolor="#DDE3EF",
                        thickness=12,
                    ),
                    line=dict(width=1.5, color="#FFFFFF"),
                ),
                branchvalues="total",
                hovertemplate="<b>%{label}</b><br>Change: %{customdata:+.2f}%<extra></extra>",
                textfont=dict(family="DM Sans, sans-serif", size=11, color="#0F172A"),
            ))
            fig_tm.update_layout(
                height=600,
                paper_bgcolor="#FFFFFF",
                margin=dict(l=0, r=0, t=10, b=0),
            )
            st.plotly_chart(fig_tm, use_container_width=True)


# ══════════════════════════════════════════════════════
# TAB 3: SECTOR DRILL-DOWN
# ══════════════════════════════════════════════════════
with t3:
    # Map sectors to their NSE index tickers
    SECTOR_INDEX_MAP = {
        "Banking":    ("NIFTY BANK",   "^NSEBANK"),
        "IT":         ("NIFTY IT",     "^CNXIT"),
        "Pharma":     ("NIFTY PHARMA", "^CNXPHARMA"),
        "FMCG":       ("NIFTY FMCG",   "^CNXFMCG"),
        "Auto":       ("NIFTY AUTO",   "^CNXAUTO"),
        "Metals":     ("NIFTY METAL",  "^CNXMETAL"),
        "Oil & Gas":  ("NIFTY ENERGY", "^CNXENERGY"),
        "Real Estate":("NIFTY REALTY", "^CNXREALTY"),
        "Power":      ("NIFTY ENERGY", "^CNXENERGY"),
        "Infra":      ("NIFTY INFRA",  "^CNXINFRA"),
        "Capital Goods":("NIFTY INFRA","^CNXINFRA"),
    }
    avail_sectors = sorted(set(SECTOR_INDEX_MAP.keys()) & set(
        v["sector"] for v in NSE_STOCKS_EXTENDED.values()
    ))

    sdd_a, sdd_b = st.columns([1, 3])
    with sdd_a:
        sel_sector = st.selectbox("Select Sector", avail_sectors, key="sdd_sec")
        sdd_period = st.selectbox("Period", ["1M","3M","6M","1Y"], index=2, key="sdd_per")

    TFS = {"1M":"3mo","3M":"6mo","6M":"1y","1Y":"2y"}
    sp  = TFS[sdd_period]

    idx_name, idx_ticker = SECTOR_INDEX_MAP.get(sel_sector, ("NIFTY 50", "^NSEI"))

    with sdd_b:
        # Sector index performance chart
        sdf = get_ohlcv(idx_ticker, sp, "1d")
        if sdf is not None and not sdf.empty:
            lp = float(sdf["Close"].iloc[-1])
            fp = float(sdf["Close"].iloc[0])
            is_up = lp >= fp
            clr_line = UP if is_up else DOWN
            clr_fill = "rgba(22,163,74,.06)" if is_up else "rgba(220,38,38,.06)"
            pct_chg  = (lp - fp) / fp * 100

            fig_si = go.Figure()
            fig_si.add_trace(go.Scatter(
                x=sdf.index, y=sdf["Close"], mode="lines",
                line=dict(color=clr_line, width=1.8),
                fill="tozeroy", fillcolor=clr_fill,
                name=idx_name,
            ))
            fig_si.update_layout(
                **{**PLOTLY_LAYOUT,
                   "height": 220,
                   "title": f"{idx_name} — {sdd_period}  ({pct_chg:+.2f}%)",
                   "showlegend": False,
                }
            )
            st.plotly_chart(fig_si, use_container_width=True)
        else:
            st.info(f"No index data for {idx_name}.")

    # Sector constituents performance — using parallel fetch
    sec_stocks = get_stocks_by_sector(sel_sector)
    if sec_stocks:
        with st.spinner(f"Fetching {sel_sector} stocks (parallel)..."):
            sec_data = fetch_heatmap_data(tuple(sec_stocks), max_n=30)

        if not sec_data.empty:
            sec_data = sec_data.sort_values("Change%", ascending=False)

            # Bar chart
            fig_sb = go.Figure(go.Bar(
                x=sec_data["Symbol"], y=sec_data["Change%"],
                marker_color=[
                    "rgba(22,163,74,0.8)" if v >= 0 else "rgba(220,38,38,0.8)"
                    for v in sec_data["Change%"]
                ],
                text=[f"{v:+.2f}%" for v in sec_data["Change%"]],
                textposition="outside",
                textfont=dict(color="#2D3A52", size=10),
            ))
            fig_sb.add_hline(y=0, line=dict(color="#DDE3EF", width=1))
            fig_sb.update_layout(
                **{**PLOTLY_LAYOUT,
                   "height": 320,
                   "title": f"{sel_sector} Stocks — Today",
                   "xaxis": {**PLOTLY_LAYOUT["xaxis"], "tickangle": -35},
                   "yaxis": {**PLOTLY_LAYOUT["yaxis"], "ticksuffix": "%"},
                }
            )
            st.plotly_chart(fig_sb, use_container_width=True)

            # Grid heatmap for sector stocks (Issue #12 — sector heatmap now works)
            section_label(f"{sel_sector.upper()} STOCKS HEATMAP")
            fig_sec_hm = _build_grid_heatmap(sec_data, cols_per_row=min(len(sec_data), 8))
            st.plotly_chart(fig_sec_hm, use_container_width=True)

            # Performance table
            disp_sec = sec_data[["Symbol","Name","Change%","Price","MCap_Cr"]].copy()
            disp_sec.rename(columns={"MCap_Cr": "Mkt Cap (Cr)"}, inplace=True)

            def _c_sec(v):
                if pd.isna(v): return "color:var(--t3)"
                return "color:var(--green)" if v > 0 else "color:var(--red)"

            st.dataframe(
                disp_sec.style.applymap(_c_sec, subset=["Change%"])
                               .format({"Change%": "{:+.2f}%",
                                        "Price":   "₹{:.2f}",
                                        "Mkt Cap (Cr)": "{:,.0f}"}, na_rep="—"),
                use_container_width=True, height=350,
            )
    else:
        st.info(f"No constituent stocks found for {sel_sector} in the current universe.")


# ══════════════════════════════════════════════════════
# TAB 4: INDEX CORRELATION
# ══════════════════════════════════════════════════════
with t4:
    section_label("INTER-INDEX CORRELATION MATRIX")

    ic_a, ic_b = st.columns([1, 4])
    with ic_a:
        ic_period = st.selectbox("Period", ["3M","6M","1Y","2Y"], index=2, key="ic_p")
        ic_method = st.selectbox("Method", ["Pearson","Spearman"], key="ic_m")

        KEY_INDICES_CORR = {
            "NIFTY 50":     "^NSEI",
            "SENSEX":       "^BSESN",
            "NIFTY BANK":   "^NSEBANK",
            "NIFTY IT":     "^CNXIT",
            "NIFTY PHARMA": "^CNXPHARMA",
            "NIFTY FMCG":   "^CNXFMCG",
            "NIFTY AUTO":   "^CNXAUTO",
            "NIFTY METAL":  "^CNXMETAL",
            "NIFTY ENERGY": "^CNXENERGY",
            "NIFTY REALTY": "^CNXREALTY",
            "INDIA VIX":    "^INDIAVIX",
        }
        sel_idx = st.multiselect(
            "Select Indices",
            list(KEY_INDICES_CORR.keys()),
            default=list(KEY_INDICES_CORR.keys())[:8],
            key="ic_sel",
        )

    TFI = {"3M":"6mo","6M":"1y","1Y":"2y","2Y":"5y"}
    ip  = TFI[ic_period]

    if len(sel_idx) < 2:
        st.info("Select at least 2 indices to compute correlation.")
    else:
        with ic_b:
            with st.spinner("Fetching index data..."):
                idx_prices = {}
                for name in sel_idx:
                    df = get_ohlcv(KEY_INDICES_CORR[name], ip, "1d")
                    if df is not None and not df.empty:
                        idx_prices[name] = df["Close"].pct_change().dropna()

            if len(idx_prices) < 2:
                st.warning("Could not fetch enough index data. Try a different period.")
            else:
                idx_df   = pd.DataFrame(idx_prices).dropna()
                corr_idx = idx_df.corr(method=ic_method.lower())

                # ── FIX Issue #12: use title=dict(font=...) not titlefont ──
                fig_ic = go.Figure(go.Heatmap(
                    z=corr_idx.values,
                    x=corr_idx.columns.tolist(),
                    y=corr_idx.index.tolist(),
                    colorscale=[[0,"#1D4ED8"],[0.5,"#F3F4F6"],[1,"#DC2626"]],
                    zmid=0, zmin=-1, zmax=1,
                    text=[[f"{v:.2f}" for v in row] for row in corr_idx.values],
                    texttemplate="%{text}",
                    textfont=dict(size=11, color="#0F172A"),
                    colorbar=dict(
                        tickfont=dict(color="#5A6A88"),
                        title=dict(text="Corr", font=dict(color="#5A6A88")),  # FIX: was titlefont
                        bgcolor="#FFFFFF",
                        bordercolor="#DDE3EF",
                        borderwidth=1,
                    ),
                ))
                fig_ic.update_layout(
                    **{**PLOTLY_LAYOUT,
                       "height": 500,
                       "title": f"{ic_method} Correlation — {ic_period}",
                       "xaxis": {**PLOTLY_LAYOUT["xaxis"], "tickangle": -30},
                    }
                )
                st.plotly_chart(fig_ic, use_container_width=True)

                # Normalised performance comparison
                section_label("NORMALISED PERFORMANCE COMPARISON")
                fig_np = go.Figure()
                for i, name in enumerate(sel_idx):
                    df = get_ohlcv(KEY_INDICES_CORR[name], ip, "1d")
                    if df is not None and not df.empty:
                        norm = df["Close"] / float(df["Close"].iloc[0]) * 100
                        fig_np.add_trace(go.Scatter(
                            x=df.index, y=norm, mode="lines",
                            line=dict(color=CHART_COLORS[i % len(CHART_COLORS)], width=1.5),
                            name=name,
                        ))
                fig_np.update_layout(
                    **{**PLOTLY_LAYOUT,
                       "height": 340,
                       "yaxis": {**PLOTLY_LAYOUT["yaxis"], "ticksuffix": ""},
                    }
                )
                st.plotly_chart(fig_np, use_container_width=True)

                # Strongest and weakest correlations
                section_label("TOP CORRELATIONS")
                pairs_ic = []
                syms_ic  = corr_idx.columns.tolist()
                for i in range(len(syms_ic)):
                    for j in range(i + 1, len(syms_ic)):
                        v = corr_idx.iloc[i, j]
                        pairs_ic.append({
                            "Index A": syms_ic[i],
                            "Index B": syms_ic[j],
                            "Correlation": round(v, 4),
                        })
                if pairs_ic:
                    pic_df = pd.DataFrame(pairs_ic).sort_values("Correlation", key=abs, ascending=False)
                    st.dataframe(pic_df.head(10), use_container_width=True, height=280)
