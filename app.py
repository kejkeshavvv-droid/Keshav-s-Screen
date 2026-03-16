"""
Keshav's Screen — Indian Market Terminal
Home Dashboard: Live indices, NIFTY chart, top movers, sector heat, news
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from utils.nse_stocks import NSE_STOCKS_EXTENDED, INDICES, NIFTY50_STOCKS, load_nse_universe
from utils.data_fetcher import (
    get_ohlcv, get_sector_performance, get_market_news,
    get_live_prices_batch, is_market_open, get_indices_snapshot
)
from utils.styles import inject_css, section_label, PLOTLY_LAYOUT, CHART_COLORS

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Keshav's Screen",
    page_icon="K",
    layout="wide",
    initial_sidebar_state="collapsed",   # mobile-friendly: sidebar off by default
)
inject_css()

# ─── AUTO-REFRESH (30s) ──────────────────────────────────────────────────────
try:
    from streamlit_autorefresh import st_autorefresh   # type: ignore
    st_autorefresh(interval=30_000, limit=None, key="home_autorefresh")
except ImportError:
    pass  # fallback: manual refresh button in sidebar

# ─── MARKET STATUS (server-side) ─────────────────────────────────────────────
market_open = is_market_open()

# ─── HEADER ──────────────────────────────────────────────────────────────────
st.markdown("""
<div style="
  background:#FFFFFF;
  border:1px solid #DDE3EF;
  border-radius:12px;
  padding:18px 24px;
  margin-bottom:12px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  box-shadow:0 1px 4px rgba(15,23,42,.06);
  flex-wrap:wrap;
  gap:10px;
">
  <div>
    <div style="font-family:'DM Sans',sans-serif;font-size:1.55rem;font-weight:700;color:#0F172A;letter-spacing:-.5px;">
      Keshav&#39;s Screen
    </div>
    <div style="color:#5A6A88;font-size:.8rem;margin-top:2px;font-weight:500;">
      Indian Market Terminal &nbsp;|&nbsp; NSE/BSE &nbsp;|&nbsp; 2671+ Stocks &nbsp;|&nbsp; 50+ TA Indicators
    </div>
  </div>
  <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
    <div class="live-badge"><div class="live-dot"></div>LIVE DATA</div>
    <div style="text-align:right;">
      <div id="ks-live-clock" style="font-family:'JetBrains Mono',monospace;font-size:1.2rem;font-weight:600;color:#0F172A;"></div>
      <div style="color:#8896B0;font-size:.72rem;margin-top:1px;">IST</div>
    </div>
    <div style="text-align:right;">
      <div style="font-size:.82rem;font-weight:600;color:{'#15803D' if market_open else '#DC2626'};">
""" + (
    '<span style="color:#15803D;font-weight:700;">Market Open</span>'
    if market_open else
    '<span style="color:#DC2626;font-weight:700;">Market Closed</span>'
) + """
      </div>
      <div style="color:#8896B0;font-size:.7rem;">NSE: 09:15 – 15:30 IST</div>
    </div>
  </div>
</div>

<!-- Client-side real-time clock (no server rerun needed) -->
<script>
(function() {
  function pad(n) { return n < 10 ? '0' + n : '' + n; }
  function tick() {
    try {
      var d = new Date();
      var ist = new Date(d.toLocaleString('en-US', {timeZone: 'Asia/Kolkata'}));
      var s = pad(ist.getHours()) + ':' + pad(ist.getMinutes()) + ':' + pad(ist.getSeconds());
      var el = document.getElementById('ks-live-clock');
      if (el) el.textContent = s;
    } catch(e) {}
  }
  tick();
  setInterval(tick, 1000);
})();
</script>
""", unsafe_allow_html=True)

# ─── INDEX BANNER (8 key indices) ────────────────────────────────────────────
section_label("LIVE MARKET INDICES")

BANNER_INDICES = [
    ("NIFTY 50",    "^NSEI"),
    ("SENSEX",      "^BSESN"),
    ("NIFTY BANK",  "^NSEBANK"),
    ("NIFTY IT",    "^CNXIT"),
    ("NIFTY PHARMA","^CNXPHARMA"),
    ("NIFTY FMCG",  "^CNXFMCG"),
    ("NIFTY AUTO",  "^CNXAUTO"),
    ("INDIA VIX",   "^INDIAVIX"),
]

cols = st.columns(len(BANNER_INDICES))
for col, (name, ticker) in zip(cols, BANNER_INDICES):
    with col:
        try:
            fi = yf.Ticker(ticker).fast_info
            p  = getattr(fi, "last_price", None)
            pc = getattr(fi, "previous_close", p) or p
            pct = (p - pc) / pc * 100 if (p and pc) else 0
            clr  = "var(--green)" if pct >= 0 else "var(--red)"
            clr_bg = "var(--green-bg)" if pct >= 0 else "var(--red-bg)"
            clr_bdr = "#86EFAC" if pct >= 0 else "#FCA5A5"
            arr  = "+" if pct >= 0 else ""
            pstr = f"{p:,.2f}" if p else "—"
        except Exception:
            pct = 0; clr = "var(--t3)"; pstr = "—"; arr = ""
            clr_bg = "var(--bg2)"; clr_bdr = "var(--bdr)"

        st.markdown(f"""
        <div style="
          background:{clr_bg};
          border:1px solid {clr_bdr};
          border-radius:9px;
          padding:10px 8px;
          text-align:center;
          box-shadow:var(--shadow-sm);
        ">
          <div style="color:var(--t3);font-size:.62rem;font-weight:700;letter-spacing:.6px;text-transform:uppercase;">{name}</div>
          <div style="color:var(--t1);font-size:.9rem;font-weight:700;font-family:'JetBrains Mono',monospace;margin:3px 0;">{pstr}</div>
          <div style="color:{clr};font-size:.75rem;font-weight:600;">{arr}{pct:+.2f}%</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

# ─── MAIN TABS ────────────────────────────────────────────────────────────────
tab_home, tab_news, tab_cfg = st.tabs(["Dashboard", "News", "Settings"])

with tab_home:
    left, right = st.columns([13, 7])

    with left:
        # ── NIFTY 50 INTRADAY CHART ──────────────────────────────────────────
        section_label("NIFTY 50  —  INTRADAY (5-MIN)")
        try:
            ndf = get_ohlcv("^NSEI", "5d", "5m")
            if ndf is not None and not ndf.empty:
                lp = float(ndf["Close"].iloc[-1])
                fp = float(ndf["Close"].iloc[0])
                is_pos = lp >= fp
                lc = "rgba(22,163,74,1)"   if is_pos else "rgba(220,38,38,1)"
                fc = "rgba(22,163,74,.08)" if is_pos else "rgba(220,38,38,.08)"
                chg_pct = (lp - fp) / fp * 100

                fig_n = go.Figure()
                fig_n.add_trace(go.Scatter(
                    x=ndf.index, y=ndf["Close"],
                    mode="lines",
                    line=dict(color=lc, width=1.8),
                    fill="tozeroy", fillcolor=fc,
                    name="NIFTY 50",
                    hovertemplate="%{x|%H:%M}<br><b>%{y:,.2f}</b><extra></extra>",
                ))
                lyt = {**PLOTLY_LAYOUT,
                       "height": 260,
                       "margin": dict(l=0, r=40, t=0, b=0),
                       "showlegend": False,
                       "paper_bgcolor": "#FFFFFF",
                       "plot_bgcolor": "#F7F9FD",
                }
                lyt["xaxis"] = {**PLOTLY_LAYOUT["xaxis"], "tickformat": "%H:%M"}
                lyt["yaxis"] = {**PLOTLY_LAYOUT["yaxis"], "tickformat": ",.0f"}
                fig_n.update_layout(**lyt)
                st.plotly_chart(fig_n, use_container_width=True)

                sign = "+" if is_pos else ""
                clr_m = "var(--green)" if is_pos else "var(--red)"
                st.markdown(f"""
                <div style="display:flex;gap:16px;flex-wrap:wrap;margin-top:-6px;margin-bottom:4px;">
                  <div style="color:var(--t3);font-size:.78rem;">Last: <span style="font-family:'JetBrains Mono',monospace;color:var(--t1);font-weight:600;">₹{lp:,.2f}</span></div>
                  <div style="color:var(--t3);font-size:.78rem;">Change: <span style="color:{clr_m};font-weight:600;">{sign}{chg_pct:.2f}%</span></div>
                </div>""", unsafe_allow_html=True)
        except Exception:
            st.info("Loading NIFTY 50 chart...")

        # ── TOP MOVERS ───────────────────────────────────────────────────────
        section_label("TOP MOVERS  —  NIFTY 50")
        prices = get_live_prices_batch(tuple(NIFTY50_STOCKS[:25]))
        if prices:
            sorted_stocks = sorted(prices.items(), key=lambda x: x[1].get("pct", 0), reverse=True)
            gc, lc_ = st.columns(2)
            with gc:
                st.markdown('<div style="color:var(--green);font-size:.75rem;font-weight:700;margin-bottom:6px;text-transform:uppercase;letter-spacing:.5px;">Top Gainers</div>', unsafe_allow_html=True)
                for sym, d in sorted_stocks[:5]:
                    p = d.get("price", 0)
                    pct = d.get("pct", 0)
                    st.markdown(f"""
                    <div style="display:flex;justify-content:space-between;align-items:center;
                                padding:7px 12px;background:var(--green-bg);
                                border:1px solid #BBF7D0;border-radius:7px;margin-bottom:4px;">
                      <span style="color:var(--t1);font-weight:600;font-size:.84rem;">{sym}</span>
                      <span style="color:var(--t3);font-size:.78rem;font-family:'JetBrains Mono',monospace;">₹{p:,.1f}</span>
                      <span style="color:var(--green);font-weight:700;font-size:.84rem;">+{pct:.2f}%</span>
                    </div>""", unsafe_allow_html=True)
            with lc_:
                st.markdown('<div style="color:var(--red);font-size:.75rem;font-weight:700;margin-bottom:6px;text-transform:uppercase;letter-spacing:.5px;">Top Losers</div>', unsafe_allow_html=True)
                for sym, d in reversed(sorted_stocks[-5:]):
                    p = d.get("price", 0)
                    pct = d.get("pct", 0)
                    st.markdown(f"""
                    <div style="display:flex;justify-content:space-between;align-items:center;
                                padding:7px 12px;background:var(--red-bg);
                                border:1px solid #FCA5A5;border-radius:7px;margin-bottom:4px;">
                      <span style="color:var(--t1);font-weight:600;font-size:.84rem;">{sym}</span>
                      <span style="color:var(--t3);font-size:.78rem;font-family:'JetBrains Mono',monospace;">₹{p:,.1f}</span>
                      <span style="color:var(--red);font-weight:700;font-size:.84rem;">{pct:.2f}%</span>
                    </div>""", unsafe_allow_html=True)

    with right:
        # ── SECTOR HEAT ──────────────────────────────────────────────────────
        section_label("SECTOR PERFORMANCE  —  TODAY")
        try:
            sdf = get_sector_performance()
            if not sdf.empty:
                fig_s = go.Figure(go.Bar(
                    x=sdf["Return%"],
                    y=sdf["Sector"],
                    orientation="h",
                    marker_color=[
                        "rgba(22,163,74,0.8)" if v >= 0 else "rgba(220,38,38,0.8)"
                        for v in sdf["Return%"]
                    ],
                    text=[f"{v:+.2f}%" for v in sdf["Return%"]],
                    textposition="outside",
                    textfont=dict(size=10, color="#2D3A52"),
                ))
                lyt2 = {
                    **PLOTLY_LAYOUT,
                    "height": 340,
                    "margin": dict(l=0, r=60, t=0, b=0),
                    "paper_bgcolor": "#FFFFFF",
                    "plot_bgcolor":  "#F7F9FD",
                }
                lyt2["xaxis"] = dict(showgrid=False, showticklabels=False,
                                     zeroline=True, zerolinecolor="#DDE3EF",
                                     color="#5A6A88")
                lyt2["yaxis"] = dict(color="#2D3A52", showgrid=False,
                                     tickfont=dict(size=11))
                fig_s.update_layout(**lyt2)
                st.plotly_chart(fig_s, use_container_width=True)
        except Exception:
            st.info("Loading sector data...")

        # ── TERMINAL STATS ────────────────────────────────────────────────────
        section_label("TERMINAL STATS")
        try:
            universe_count = len(NSE_STOCKS_EXTENDED)
            try:
                from utils.nse_stocks import get_universe_count
                universe_count = get_universe_count()
            except Exception:
                pass
        except Exception:
            universe_count = 500

        for lbl, val in [
            ("Stocks Covered",     f"{universe_count:,}+"),
            ("Indices Tracked",    f"{len(INDICES)}"),
            ("TA Indicators",      "50+"),
            ("Fundamental Filters","30+"),
            ("Backtest Strategies","9"),
            ("Statistical Tests",  "12+"),
            ("Data Source",        "NSE/BSE Live"),
        ]:
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;padding:6px 12px;
                        background:var(--bg3);border:1px solid var(--bdr);
                        border-radius:6px;margin-bottom:3px;">
              <span style="color:var(--t3);font-size:.82rem;font-weight:500;">{lbl}</span>
              <span style="color:var(--t1);font-family:'JetBrains Mono',monospace;font-size:.82rem;font-weight:600;">{val}</span>
            </div>""", unsafe_allow_html=True)

# ─── NEWS TAB ─────────────────────────────────────────────────────────────────
with tab_news:
    section_label("LATEST MARKET NEWS")
    try:
        news_items = get_market_news(limit=20)
        seen = set()
        count = 0
        for art in news_items:
            title = art.get("title", "")
            if not title or title in seen:
                continue
            seen.add(title)
            url = art.get("link", "#")
            pub = art.get("publisher", "")
            ts  = art.get("providerPublishTime", 0)
            dt  = datetime.fromtimestamp(ts).strftime("%d %b %Y  %H:%M") if ts else ""
            st.markdown(f"""
            <div class="ks-card" style="border-left:3px solid var(--blue);margin-bottom:8px;">
              <a href="{url}" target="_blank"
                 style="color:var(--t1);text-decoration:none;font-size:.9rem;
                        font-weight:600;line-height:1.5;display:block;">{title}</a>
              <div style="color:var(--t3);font-size:.72rem;margin-top:5px;">
                <span style="color:var(--blue);font-weight:600;">{pub}</span>
                &nbsp;•&nbsp; {dt}
              </div>
            </div>""", unsafe_allow_html=True)
            count += 1
        if count == 0:
            st.info("No news available at this time. Try refreshing.")
    except Exception:
        st.info("Loading news...")

# ─── SETTINGS TAB ────────────────────────────────────────────────────────────
with tab_cfg:
    section_label("CONFIGURATION")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**AI Screener API Key**")
        st.caption("Supports Anthropic Claude, Groq (free), or compatible OpenAI format.")
        api_key = st.text_input(
            "API Key",
            type="password",
            value=st.session_state.get("ai_api_key", ""),
            placeholder="sk-ant-... or gsk_...",
            label_visibility="collapsed",
        )
        if api_key:
            st.session_state["ai_api_key"] = api_key
            st.success("API key saved for this session.")

        st.markdown("**AI Provider**")
        provider = st.selectbox(
            "AI Provider",
            ["Groq (Free)", "Anthropic Claude", "OpenAI Compatible"],
            index=0,
            label_visibility="collapsed",
        )
        st.session_state["ai_provider"] = provider

    with c2:
        st.markdown("**Cache & Refresh Intervals**")
        st.markdown("""
        <div class="ks-card" style="font-size:.82rem;">
          <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--bdr);">
            <span style="color:var(--t3);">Live Index Banner</span>
            <span style="color:var(--t1);font-family:'JetBrains Mono',monospace;font-weight:600;">30 s</span></div>
          <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--bdr);">
            <span style="color:var(--t3);">Live Prices (batch)</span>
            <span style="color:var(--t1);font-family:'JetBrains Mono',monospace;font-weight:600;">30 s</span></div>
          <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--bdr);">
            <span style="color:var(--t3);">OHLCV / Charts</span>
            <span style="color:var(--t1);font-family:'JetBrains Mono',monospace;font-weight:600;">60 s</span></div>
          <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--bdr);">
            <span style="color:var(--t3);">Fundamentals</span>
            <span style="color:var(--t1);font-family:'JetBrains Mono',monospace;font-weight:600;">5 min</span></div>
          <div style="display:flex;justify-content:space-between;padding:5px 0;">
            <span style="color:var(--t3);">News Feed</span>
            <span style="color:var(--t1);font-family:'JetBrains Mono',monospace;font-weight:600;">30 min</span></div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    | Module | Description |
    |--------|-------------|
    | **Screener** | AI prompt + 30+ filters; 12 preset screens; full NSE universe |
    | **Charts** | Candlestick/HA/Line/OHLC · 50+ overlays · 15 sub-panels · Signal summary |
    | **Bucket** | Watchlist · Performance · Correlation · Risk-Return scatter |
    | **Heatmap** | Market grid · Treemap · Sector drill-down · Index correlation |
    | **Algo Lab** | 9-strategy backtester · Monte Carlo · Regression · 12 hypothesis tests |
    | **Indices** | 28 indices · Performance table · Deep-dive · Comparison · Constituents |
    """)

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:14px 0 12px;">
      <div style="font-family:'DM Sans',sans-serif;font-size:1rem;font-weight:700;color:#0F172A;">
        Keshav&#39;s Screen</div>
      <div style="color:#8896B0;font-size:.68rem;margin-top:2px;letter-spacing:.4px;text-transform:uppercase;">
        Indian Market Terminal</div>
    </div>
    <hr style="border:none;border-top:1px solid #DDE3EF;margin:0 0 12px;">
    """, unsafe_allow_html=True)

    # Quick lookup
    st.markdown('<div style="color:#8896B0;font-size:.68rem;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:5px;">Quick Lookup</div>', unsafe_allow_html=True)
    ql = st.text_input("", placeholder="Symbol e.g. RELIANCE", label_visibility="collapsed", key="ql_home")
    if ql:
        sym = ql.upper().strip()
        try:
            fi = yf.Ticker(f"{sym}.NS").fast_info
            p  = getattr(fi, "last_price", None)
            pc = getattr(fi, "previous_close", p) or p
            chg = (p - pc) if (p and pc) else 0
            pct = (chg / pc * 100) if pc else 0
            clr = "var(--green)" if pct >= 0 else "var(--red)"
            bgc = "var(--green-bg)" if pct >= 0 else "var(--red-bg)"
            bdr = "#BBF7D0" if pct >= 0 else "#FCA5A5"
            sign = "+" if pct >= 0 else ""
            if p:
                st.markdown(f"""
                <div style="text-align:center;padding:12px;background:{bgc};
                            border:1px solid {bdr};border-radius:9px;margin-bottom:8px;">
                  <div style="color:var(--t3);font-size:.7rem;font-weight:600;text-transform:uppercase;">{sym}</div>
                  <div style="color:var(--t1);font-size:1.3rem;font-weight:700;font-family:'JetBrains Mono',monospace;">₹{p:,.2f}</div>
                  <div style="color:{clr};font-size:.88rem;font-weight:700;">{sign}{chg:+.2f} ({sign}{pct:.2f}%)</div>
                </div>""", unsafe_allow_html=True)
        except Exception:
            st.error("Symbol not found")

    st.markdown('<hr style="border:none;border-top:1px solid #DDE3EF;margin:8px 0;">', unsafe_allow_html=True)

    # Bucket count
    bucket = st.session_state.get("bucket", [])
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;
                padding:8px 12px;background:var(--bg3);border:1px solid var(--bdr);
                border-radius:8px;margin-bottom:8px;">
      <span style="color:var(--t3);font-size:.82rem;font-weight:500;">Bucket</span>
      <span style="background:var(--blue-light);color:var(--blue);padding:2px 9px;
                   border:1px solid var(--blue-bdr);border-radius:12px;
                   font-size:.72rem;font-weight:700;">{len(bucket)} stocks</span>
    </div>""", unsafe_allow_html=True)

    # Market status
    now_str = datetime.utcnow().strftime("%H:%M")
    st.markdown(f"""
    <div style="background:var(--bg3);border:1px solid var(--bdr);border-radius:8px;
                padding:10px 12px;margin-bottom:10px;font-size:.8rem;">
      <div style="color:var(--t4);font-size:.65rem;font-weight:700;letter-spacing:1px;
                  text-transform:uppercase;margin-bottom:6px;">Market Status</div>
      <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
        <span style="color:var(--t3);">NSE Equities</span>
        <span style="color:{'var(--green)' if market_open else 'var(--red)'};font-weight:600;">
          {'Open' if market_open else 'Closed'}</span></div>
      <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
        <span style="color:var(--t3);">Session</span>
        <span style="color:var(--t1);font-family:'JetBrains Mono',monospace;">09:15 – 15:30</span></div>
    </div>""", unsafe_allow_html=True)

    if st.button("Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown(f"""
    <div style="font-size:.65rem;color:var(--t4);text-align:center;margin-top:8px;line-height:1.8;">
      Keshav&#39;s Screen v2.0<br>
      Data: NSE/BSE via Yahoo Finance<br>
      {datetime.utcnow().strftime('%d %b %Y')}
    </div>""", unsafe_allow_html=True)
