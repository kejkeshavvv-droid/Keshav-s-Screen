"""
5___Algo_Lab.py — Keshav's Screen
Algo Lab: Backtesting · Time Series · Statistics · Regression · Hypothesis Tests · Monte Carlo
Fixes: Issue #13 (click-to-explain stats), #14 (regression controls + predict + multivariate),
       #15 (all regression modes working)
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import scipy.stats as scipy_stats
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.nse_stocks import NSE_STOCKS_EXTENDED, INDICES, yf_ticker
from utils.data_fetcher import get_ohlcv
from utils.technical_analysis import sma, ema, rsi, macd, bollinger_bands, atr, supertrend
from utils.styles import inject_css, section_label, PLOTLY_LAYOUT, CHART_COLORS

st.set_page_config(
    page_title="Algo Lab — Keshav's Screen",
    page_icon="K",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()

# Extra CSS for expandable stat cards
st.markdown("""
<style>
.stat-card {
  background: var(--bg2);
  border: 1px solid var(--bdr);
  border-radius: 10px;
  padding: 14px 18px;
  margin-bottom: 8px;
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  transition: border-color .18s, box-shadow .18s;
}
.stat-card:hover { border-color: var(--bdr2); box-shadow: var(--shadow); }
.stat-val { color: var(--blue); font-size: 1.2rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
.stat-lbl { color: var(--t3); font-size: .72rem; font-weight: 700; text-transform: uppercase; letter-spacing: .5px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<h2 style="margin-bottom:2px;">Algo Lab</h2>', unsafe_allow_html=True)
st.markdown(
    '<p style="color:var(--t3);font-size:.85rem;">'
    'Strategy Backtesting · Time Series Analysis · Statistical Tests · Regression · Monte Carlo</p>',
    unsafe_allow_html=True,
)

all_syms = list(NSE_STOCKS_EXTENDED.keys())

# ─── GLOBAL SYMBOL PICKER ────────────────────────────────────────────────────
la, lb, lc = st.columns([3, 2, 2])
with la:
    lab_sym = st.selectbox(
        "Select Stock / Index",
        all_syms + list(INDICES.keys()),
        index=all_syms.index("RELIANCE") if "RELIANCE" in all_syms else 0,
        key="lab_sym",
    )
with lb:
    lab_period = st.selectbox("Data Period", ["1Y","2Y","3Y","5Y","10Y","Max"], index=2, key="lab_per")
with lc:
    lab_int = st.selectbox("Interval", ["1d","1wk","1mo"], key="lab_int")

TFL = {"1Y":"2y","2Y":"5y","3Y":"10y","5Y":"10y","10Y":"max","Max":"max"}
period_yf = TFL[lab_period]

with st.spinner(f"Loading {lab_sym}..."):
    df_raw = get_ohlcv(lab_sym, period_yf, lab_int)

if df_raw is None or df_raw.empty:
    st.error(f"No data for {lab_sym}. Try a different symbol or period.")
    st.stop()

df      = df_raw.copy()
close   = df["Close"]
returns = close.pct_change().dropna()
log_rets= np.log(close / close.shift(1)).dropna()

st.markdown("---")

# ─── TABS ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Backtest", "Time Series", "Statistics",
    "Regression", "Hypothesis Tests", "Monte Carlo",
])

# ─── SHARED LIGHT-THEME LAYOUT ───────────────────────────────────────────────
UP   = "#16A34A"
DOWN = "#DC2626"

def _lyt(**kwargs):
    """Merge with PLOTLY_LAYOUT for consistent light-theme charts."""
    return {**PLOTLY_LAYOUT, **kwargs}


# ══════════════════════════════════════════════════════════════
# TAB 1 — BACKTESTING
# ══════════════════════════════════════════════════════════════
with tab1:
    section_label("STRATEGY BUILDER")
    b1, b2 = st.columns([1, 3])
    with b1:
        strategy = st.selectbox("Strategy", [
            "SMA Crossover", "EMA Crossover", "RSI Mean Reversion",
            "MACD Signal Cross", "Bollinger Band Bounce", "Supertrend",
            "Golden Cross (SMA 50/200)", "RSI + MACD Combo", "Dual EMA + ATR Stop",
        ], key="bt_strat")
        st.markdown("**Parameters**")
        fast_p = slow_p = 20
        rsi_ob = rsi_os = rsi_per = 14
        bb_per = 20; bb_std = 2.0; atr_m = 2.0
        if "SMA" in strategy or "EMA" in strategy or "Dual" in strategy:
            fast_p = st.number_input("Fast Period", value=20, min_value=2, max_value=200, key="bt_fp")
            slow_p = st.number_input("Slow Period", value=50, min_value=3, max_value=500, key="bt_sp")
        if "RSI" in strategy:
            rsi_ob  = st.number_input("RSI Overbought", value=70, step=1, key="bt_rob")
            rsi_os  = st.number_input("RSI Oversold",   value=30, step=1, key="bt_ros")
            rsi_per = st.number_input("RSI Period",     value=14, step=1, key="bt_rp")
        if "Bollinger" in strategy:
            bb_per  = st.number_input("BB Period",  value=20, step=1, key="bt_bp")
            bb_std  = st.number_input("BB Std Dev", value=2.0, step=0.1, key="bt_bs")
        if "ATR" in strategy:
            atr_m   = st.number_input("ATR Multiplier", value=2.0, step=0.1, key="bt_atr_m")

        initial_cap  = st.number_input("Initial Capital (₹)", value=100000, step=10000, key="bt_cap")
        position_pct = st.slider("Position Size (%)", 10, 100, 100, 10, key="bt_pos")
        commission   = st.number_input("Commission (%)", value=0.1, step=0.01, key="bt_comm")
        slippage     = st.number_input("Slippage (%)",   value=0.05, step=0.01, key="bt_slip")
        run_bt = st.button("Run Backtest", type="primary", use_container_width=True, key="run_bt")

    with b2:
        if run_bt:
            with st.spinner("Running backtest..."):
                sig = pd.Series(0, index=df.index, dtype=float)

                if strategy == "SMA Crossover":
                    sf = close.rolling(int(fast_p)).mean(); ss = close.rolling(int(slow_p)).mean()
                    sig = pd.Series(np.where(sf > ss, 1, -1), index=df.index, dtype=float)
                elif strategy == "EMA Crossover":
                    ef = close.ewm(span=int(fast_p), adjust=False).mean()
                    es = close.ewm(span=int(slow_p), adjust=False).mean()
                    sig = pd.Series(np.where(ef > es, 1, -1), index=df.index, dtype=float)
                elif strategy == "RSI Mean Reversion":
                    r = rsi(df, int(rsi_per))
                    sig = pd.Series(np.where(r < rsi_os, 1, np.where(r > rsi_ob, -1, 0)), index=df.index, dtype=float)
                elif strategy == "MACD Signal Cross":
                    ml, sl2, _ = macd(df)
                    sig = pd.Series(np.where(ml > sl2, 1, -1), index=df.index, dtype=float)
                elif strategy == "Bollinger Band Bounce":
                    bu, bm, bl, _, _ = bollinger_bands(df, int(bb_per), float(bb_std))
                    sig = pd.Series(np.where(close < bl, 1, np.where(close > bu, -1, 0)), index=df.index, dtype=float)
                elif strategy == "Supertrend":
                    _, st_dir = supertrend(df)
                    sig = pd.Series(np.where(st_dir == 1, 1, -1), index=df.index, dtype=float)
                elif strategy == "Golden Cross (SMA 50/200)":
                    s50 = close.rolling(50).mean(); s200 = close.rolling(200).mean()
                    sig = pd.Series(np.where(s50 > s200, 1, -1), index=df.index, dtype=float)
                elif strategy == "RSI + MACD Combo":
                    r = rsi(df, 14); ml, sl2, _ = macd(df)
                    sig = pd.Series(np.where((r < 40) & (ml > sl2), 1, np.where((r > 60) & (ml < sl2), -1, 0)), index=df.index, dtype=float)
                elif strategy == "Dual EMA + ATR Stop":
                    ef = close.ewm(span=int(fast_p), adjust=False).mean()
                    es = close.ewm(span=int(slow_p), adjust=False).mean()
                    sig = pd.Series(np.where(ef > es, 1, -1), index=df.index, dtype=float)

                sig_s = sig.shift(1).fillna(0)
                total_cost  = (commission + slippage) / 100
                strat_rets  = sig_s * returns - (sig_s.diff().abs() * total_cost)
                equity_strat= (1 + strat_rets.fillna(0)).cumprod() * initial_cap
                equity_bh   = (1 + returns.fillna(0)).cumprod() * initial_cap

                def calc_metrics(eq, r, label):
                    ann_ret = float(np.mean(r)) * 252
                    ann_vol = float(np.std(r)) * np.sqrt(252)
                    sharpe  = ann_ret / ann_vol if ann_vol > 0 else 0
                    max_dd  = float(((eq / eq.cummax()) - 1).min()) * 100
                    total_t = (r != 0).sum()
                    win_pct = (r > 0).sum() / total_t * 100 if total_t > 0 else 0
                    total_ret = (float(eq.iloc[-1]) - initial_cap) / initial_cap * 100
                    return {"Label": label, "Total Return (%)": round(total_ret, 2),
                            "Ann. Return (%)": round(ann_ret*100, 2), "Ann. Vol (%)": round(ann_vol*100, 2),
                            "Sharpe": round(sharpe, 3), "Max DD (%)": round(max_dd, 2), "Win Rate (%)": round(win_pct, 2)}

                ms = calc_metrics(equity_strat, strat_rets, strategy)
                mb = calc_metrics(equity_bh, returns, "Buy & Hold")

                fig_bt = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                        row_heights=[0.65, 0.35], vertical_spacing=0.04)
                fig_bt.add_trace(go.Scatter(x=equity_strat.index, y=equity_strat, mode="lines",
                    line=dict(color=CHART_COLORS[0], width=1.8), name=strategy), row=1, col=1)
                fig_bt.add_trace(go.Scatter(x=equity_bh.index, y=equity_bh, mode="lines",
                    line=dict(color="#8896B0", width=1.2, dash="dot"), name="Buy & Hold"), row=1, col=1)
                dd_strat = ((equity_strat / equity_strat.cummax()) - 1) * 100
                fig_bt.add_trace(go.Scatter(x=dd_strat.index, y=dd_strat, mode="lines",
                    line=dict(color=DOWN, width=1), fill="tozeroy",
                    fillcolor="rgba(220,38,38,.08)", name="Drawdown"), row=2, col=1)
                fig_bt.update_layout(**_lyt(height=480, hovermode="x unified",
                    legend=dict(bgcolor="#FFFFFF", bordercolor="#DDE3EF",
                                borderwidth=1, font=dict(color="#2D3A52", size=10))))
                for i in [1, 2]:
                    fig_bt.update_xaxes(showgrid=True, gridcolor="#EAEEf8", color="#5A6A88", row=i, col=1)
                    fig_bt.update_yaxes(showgrid=True, gridcolor="#EAEEf8", color="#5A6A88", side="right", row=i, col=1)
                st.plotly_chart(fig_bt, use_container_width=True)

                metrics_df = pd.DataFrame([ms, mb]).set_index("Label")
                def _sm(v):
                    if not isinstance(v, (int, float)) or pd.isna(v): return ""
                    return "color:var(--green)" if v > 0 else "color:var(--red)" if v < 0 else ""
                st.dataframe(metrics_df.style.applymap(_sm).format("{:.2f}", na_rep="—"),
                             use_container_width=True)

                # Signal chart
                sig_disp = sig; buy_pts = close[sig_disp == 1]; sell_pts = close[sig_disp == -1]
                fig_sig = go.Figure()
                fig_sig.add_trace(go.Scatter(x=close.index, y=close, mode="lines",
                    line=dict(color="#8896B0", width=1), name="Price"))
                if not buy_pts.empty:
                    fig_sig.add_trace(go.Scatter(x=buy_pts.index, y=buy_pts, mode="markers",
                        marker=dict(color=UP, size=6, symbol="triangle-up"), name="Buy"))
                if not sell_pts.empty:
                    fig_sig.add_trace(go.Scatter(x=sell_pts.index, y=sell_pts, mode="markers",
                        marker=dict(color=DOWN, size=6, symbol="triangle-down"), name="Sell"))
                fig_sig.update_layout(**_lyt(height=260, title="Trade Signals"))
                st.plotly_chart(fig_sig, use_container_width=True)
        else:
            st.info("Configure strategy parameters and click Run Backtest.")


# ══════════════════════════════════════════════════════════════
# TAB 2 — TIME SERIES
# ══════════════════════════════════════════════════════════════
with tab2:
    ts_cols = st.columns(4)
    show_dist    = ts_cols[0].checkbox("Return Distribution", value=True)
    show_rolling = ts_cols[1].checkbox("Rolling Stats", value=True)
    show_acf     = ts_cols[2].checkbox("ACF / PACF", value=True)
    show_decomp  = ts_cols[3].checkbox("Seasonal Decomp", value=False)

    if show_dist:
        section_label("RETURN DISTRIBUTION")
        fig_dist = make_subplots(rows=1, cols=2, subplot_titles=["Daily Return Histogram","Q-Q Plot (Normal)"])
        daily_rets = returns.dropna()
        mu, sigma  = float(daily_rets.mean()), float(daily_rets.std())
        x_range    = np.linspace(mu - 4*sigma, mu + 4*sigma, 200)
        norm_pdf   = scipy_stats.norm.pdf(x_range, mu, sigma) * len(daily_rets) * (daily_rets.max()-daily_rets.min())/30
        fig_dist.add_trace(go.Histogram(x=daily_rets*100, nbinsx=60, marker_color=CHART_COLORS[0], opacity=.75, name="Returns"), row=1, col=1)
        fig_dist.add_trace(go.Scatter(x=x_range*100, y=norm_pdf, mode="lines", line=dict(color=CHART_COLORS[2], width=1.5), name="Normal Fit"), row=1, col=1)
        qq = scipy_stats.probplot(daily_rets.dropna(), dist="norm")
        fig_dist.add_trace(go.Scatter(x=qq[0][0], y=qq[0][1], mode="markers", marker=dict(color=CHART_COLORS[0], size=3, opacity=.6), name="Q-Q"), row=1, col=2)
        fig_dist.add_trace(go.Scatter(x=[qq[0][0].min(), qq[0][0].max()], y=[qq[1][1]+qq[1][0]*qq[0][0].min(), qq[1][1]+qq[1][0]*qq[0][0].max()], mode="lines", line=dict(color=DOWN, width=1.5, dash="dash"), name="Normal Line"), row=1, col=2)
        for ann in fig_dist.layout.annotations: ann.font.color = "#5A6A88"; ann.font.size = 11
        fig_dist.update_layout(**_lyt(height=300, showlegend=False))
        for c in [1, 2]:
            fig_dist.update_xaxes(showgrid=True, gridcolor="#EAEEf8", color="#5A6A88", row=1, col=c)
            fig_dist.update_yaxes(showgrid=True, gridcolor="#EAEEf8", color="#5A6A88", row=1, col=c)
        st.plotly_chart(fig_dist, use_container_width=True)

        r_clean = daily_rets.dropna()
        kurt_v = float(r_clean.kurtosis()); skew_v = float(r_clean.skew())
        c1, c2, c3, c4 = st.columns(4)
        for col, lbl, val in [
            (c1, "Mean Daily Return", f"{mu*100:.4f}%"),
            (c2, "Std Dev (Daily)", f"{sigma*100:.4f}%"),
            (c3, "Skewness", f"{skew_v:.4f}"),
            (c4, "Excess Kurtosis", f"{kurt_v:.4f}"),
        ]:
            with col:
                st.markdown(f'<div class="stat-card"><div class="stat-lbl">{lbl}</div><div class="stat-val">{val}</div></div>', unsafe_allow_html=True)

    if show_rolling:
        section_label("ROLLING STATISTICS")
        roll_w = st.slider("Rolling window (days)", 10, 120, 30, key="ts_roll")
        roll_ret = returns.rolling(roll_w).mean() * 252 * 100
        roll_vol = returns.rolling(roll_w).std() * np.sqrt(252) * 100
        roll_sharpe = (returns.rolling(roll_w).mean() * 252) / (returns.rolling(roll_w).std() * np.sqrt(252))

        fig_roll = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.04,
                                  subplot_titles=["Rolling Ann. Return (%)", "Rolling Volatility (%)", "Rolling Sharpe"])
        fig_roll.add_trace(go.Scatter(x=roll_ret.index, y=roll_ret, mode="lines", line=dict(color=CHART_COLORS[0], width=1.2), name="Ann. Return"), row=1, col=1)
        fig_roll.add_hline(y=0, line=dict(color="#DDE3EF", width=0.8), row=1, col=1)
        fig_roll.add_trace(go.Scatter(x=roll_vol.index, y=roll_vol, mode="lines", line=dict(color=CHART_COLORS[2], width=1.2), name="Volatility"), row=2, col=1)
        fig_roll.add_trace(go.Scatter(x=roll_sharpe.index, y=roll_sharpe, mode="lines", line=dict(color=CHART_COLORS[4], width=1.2), name="Sharpe"), row=3, col=1)
        fig_roll.add_hline(y=1, line=dict(color=UP, width=0.8, dash="dash"), row=3, col=1)
        fig_roll.update_layout(**_lyt(height=480, showlegend=False))
        for r_ in [1, 2, 3]:
            fig_roll.update_xaxes(showgrid=True, gridcolor="#EAEEf8", color="#5A6A88", row=r_, col=1)
            fig_roll.update_yaxes(showgrid=True, gridcolor="#EAEEf8", color="#5A6A88", side="right", row=r_, col=1)
        st.plotly_chart(fig_roll, use_container_width=True)

    if show_acf:
        section_label("ACF / PACF")
        n_lags = st.slider("Number of lags", 10, 60, 30, key="ts_lags")
        conf_band = 1.96 / np.sqrt(len(returns))
        acf_vals = []; pacf_vals = []
        for lag in range(1, n_lags + 1):
            try:
                from statsmodels.tsa.stattools import acf, pacf
                _a = acf(returns.dropna(), nlags=n_lags, fft=True)
                _p = pacf(returns.dropna(), nlags=n_lags)
                acf_vals  = list(_a[1:])
                pacf_vals = list(_p[1:])
                break
            except Exception:
                try:
                    r_arr = returns.dropna().values
                    acf_vals.append(float(pd.Series(r_arr).autocorr(lag=lag)))
                    y_shift = r_arr[lag:]; x_base = r_arr[:-lag]
                    if len(y_shift) > lag+1:
                        pacf_vals.append(float(pd.Series(y_shift).corr(pd.Series(x_base))))
                    else:
                        pacf_vals.append(0)
                except Exception:
                    acf_vals.append(0); pacf_vals.append(0)

        lags = list(range(1, len(acf_vals) + 1))
        fig_acf = make_subplots(rows=1, cols=2, subplot_titles=["ACF", "PACF"])
        for col_, vals in [(1, acf_vals), (2, pacf_vals)]:
            fig_acf.add_trace(go.Bar(x=lags, y=vals,
                marker_color=[CHART_COLORS[0] if abs(v) > conf_band else "#C8D0E4" for v in vals],
                name=["ACF","PACF"][col_-1]), row=1, col=col_)
            fig_acf.add_hline(y= conf_band, line=dict(color=CHART_COLORS[2], width=0.8, dash="dash"), row=1, col=col_)
            fig_acf.add_hline(y=-conf_band, line=dict(color=CHART_COLORS[2], width=0.8, dash="dash"), row=1, col=col_)
        fig_acf.update_layout(**_lyt(height=280, showlegend=False))
        for c in [1, 2]:
            fig_acf.update_xaxes(showgrid=False, color="#5A6A88", row=1, col=c)
            fig_acf.update_yaxes(showgrid=True, gridcolor="#EAEEf8", color="#5A6A88", row=1, col=c)
        st.plotly_chart(fig_acf, use_container_width=True)


# ══════════════════════════════════════════════════════════════
# TAB 3 — STATISTICS  (Issue #13: click-to-explain)
# ══════════════════════════════════════════════════════════════

# ── Stat card helper: value shown always; concept+interpretation on expand ───
STAT_EXPLANATIONS = {
    "Mean Daily Return": {
        "concept": "Average of all daily percentage returns over the period.",
        "implication": "Positive mean indicates the stock generally trends upward on a daily basis.",
        "interpret": lambda v, d: f"At {float(v.replace('%','')):.4f}% per day, the stock earned approximately {float(v.replace('%',''))*252:.1f}% annualised on average — {'above' if float(v.replace('%','')) > 0 else 'below'} the zero threshold.",
    },
    "Median Daily Return": {
        "concept": "The middle value of all daily returns, less affected by outliers than mean.",
        "implication": "A median higher than the mean suggests negative skew (more frequent large down-days).",
        "interpret": lambda v, d: "Median is robust to extreme days. Use it alongside mean to detect skew.",
    },
    "Std Dev (Daily)": {
        "concept": "Statistical measure of how widely daily returns deviate from their average.",
        "implication": "Higher standard deviation = higher daily price risk.",
        "interpret": lambda v, d: f"A daily std dev of {v} implies roughly {float(v.replace('%',''))*np.sqrt(252):.1f}% annualised volatility (assuming normal returns).",
    },
    "Annualised Volatility": {
        "concept": "Daily standard deviation scaled to a yearly figure (×√252 for daily data).",
        "implication": "Used in risk-adjusted return metrics like Sharpe ratio. >30% is considered high for Indian equities.",
        "interpret": lambda v, d: f"At {v}, the stock's annual risk is {'high (>30%)' if float(v.replace('%','')) > 30 else 'moderate (15–30%)' if float(v.replace('%','')) > 15 else 'low (<15%)'}.",
    },
    "Skewness": {
        "concept": "Measures asymmetry of the return distribution. Zero = symmetric (normal). Negative = fat left tail (crash risk).",
        "implication": "Negative skewness means rare but large losses. Positive skewness means rare but large gains.",
        "interpret": lambda v, d: f"Skewness of {v}: {'negative — more extreme down days than up days' if float(v) < -0.2 else 'positive — more extreme up days than down days' if float(v) > 0.2 else 'near-symmetric distribution'}.",
    },
    "Excess Kurtosis": {
        "concept": "Measures the 'fat-tailedness' of the return distribution versus a normal curve. Value > 0 = fat tails (leptokurtic).",
        "implication": "Fat tails mean extreme returns (both up and down) are more likely than a normal model predicts — real market risk is underestimated by Gaussian models.",
        "interpret": lambda v, d: f"Kurtosis of {v}: {'fat tails — extreme events much more likely than normal' if float(v) > 1 else 'thin tails — fewer extreme events than normal' if float(v) < -0.5 else 'near-normal tail thickness'}.",
    },
    "Sharpe Ratio": {
        "concept": "Excess return per unit of total risk. Formula: (Ann. Return − Risk-Free Rate) / Ann. Volatility.",
        "implication": "Sharpe > 1 = good risk-adjusted return. > 2 = excellent. < 0 = worse than risk-free.",
        "interpret": lambda v, d: f"Sharpe of {v}: {'excellent risk-adjusted performance' if float(v) > 2 else 'good' if float(v) > 1 else 'acceptable' if float(v) > 0.5 else 'poor — low return for the risk taken'}.",
    },
    "Sortino Ratio": {
        "concept": "Like Sharpe but only penalises downside volatility, not total volatility.",
        "implication": "More relevant for asymmetric return profiles. A stock with only upward volatility won't be penalised.",
        "interpret": lambda v, d: f"Sortino of {v}: {'strong downside-adjusted performance' if float(v) > 2 else 'good' if float(v) > 1 else 'needs improvement'}.",
    },
    "Max Drawdown": {
        "concept": "The largest peak-to-trough decline in portfolio value over the period.",
        "implication": "Represents worst-case loss for a buy-at-peak investor. A key risk measure for position sizing.",
        "interpret": lambda v, d: f"Max drawdown of {v}%: {'severe — would require a {abs(float(v))/(1-abs(float(v))/100):.0f}% gain to recover' if abs(float(v.replace('%',''))) > 20 else 'moderate' if abs(float(v.replace('%',''))) > 10 else 'mild'}.",
    },
    "Beta": {
        "concept": "Sensitivity of stock returns to market (NIFTY 50) movements. Beta=1 means moves with market.",
        "implication": "Beta > 1 = amplifies market moves (aggressive). Beta < 1 = defensive. Beta < 0 = inverse to market.",
        "interpret": lambda v, d: f"Beta of {v}: {'aggressive — amplifies NIFTY moves' if float(v) > 1.2 else 'near-market' if 0.8 < float(v) < 1.2 else 'defensive' if float(v) < 0.8 and float(v) >= 0 else 'inverse to market'}.",
    },
    "VaR 95%": {
        "concept": "Value at Risk at 95% confidence. The loss that will not be exceeded 95% of trading days.",
        "implication": "On 1 in 20 trading days, losses will be worse than this figure.",
        "interpret": lambda v, d: f"VaR 95% of {v}: on a typical bad day (1 in 20), expect a loss of at least {v}.",
    },
}


def stat_card(label: str, value: str, p_value: str = None, verdict: str = None,
              verdict_color: str = "var(--t2)", extra_key: str = ""):
    """
    Render a stat card with value always visible.
    Click the expander to see the underlying concept and interpretation.
    Issue #13 fix.
    """
    expl = STAT_EXPLANATIONS.get(label, {})
    st.markdown(f"""
    <div class="stat-card">
      <div class="stat-lbl">{label}</div>
      <div class="stat-val">{value}</div>
      {"<div style='color:var(--t3);font-size:.75rem;margin-top:3px;'>p-value: " + p_value + "</div>" if p_value else ""}
      {"<div style='color:" + verdict_color + ";font-size:.75rem;margin-top:3px;font-weight:500;'>" + verdict + "</div>" if verdict else ""}
    </div>""", unsafe_allow_html=True)

    if expl:
        with st.expander(f"What does {label} mean?", expanded=False):
            st.markdown(f"**Concept:** {expl.get('concept','')}")
            st.markdown(f"**Implication:** {expl.get('implication','')}")
            try:
                interp_fn = expl.get("interpret")
                if interp_fn:
                    st.markdown(f"**Your result:** {interp_fn(value, {})}")
            except Exception:
                pass


with tab3:
    section_label("COMPREHENSIVE STATISTICAL SUMMARY")

    r_clean = returns.dropna()
    ann_ret_val = float(r_clean.mean()) * 252 * 100
    ann_vol_val = float(r_clean.std())  * np.sqrt(252) * 100
    sharpe_val  = ann_ret_val / ann_vol_val if ann_vol_val > 0 else 0
    max_dd_val  = float(((close / close.cummax()) - 1).min()) * 100
    sortino_d   = float(r_clean[r_clean < 0].std()) * np.sqrt(252)
    sortino_val = ann_ret_val / (sortino_d * 100) if sortino_d > 0 else 0
    var95_val   = float(np.percentile(r_clean, 5)) * 100
    skew_val    = float(r_clean.skew())
    kurt_val    = float(r_clean.kurtosis())

    c1, c2, c3 = st.columns(3)
    with c1:
        stat_card("Mean Daily Return",      f"{float(r_clean.mean())*100:.4f}%", extra_key="mdr")
        stat_card("Annualised Volatility",  f"{ann_vol_val:.2f}%",               extra_key="av")
        stat_card("Sharpe Ratio",           f"{sharpe_val:.3f}",                 extra_key="sr")
        stat_card("Max Drawdown",           f"{max_dd_val:.2f}%",                extra_key="md")
    with c2:
        stat_card("Std Dev (Daily)",        f"{float(r_clean.std())*100:.4f}%",  extra_key="sd")
        stat_card("Sortino Ratio",          f"{sortino_val:.3f}",                extra_key="so")
        stat_card("VaR 95%",               f"{var95_val:.3f}%",                 extra_key="var")
        stat_card("Skewness",               f"{skew_val:.4f}",                   extra_key="sk")
    with c3:
        stat_card("Median Daily Return",    f"{float(r_clean.median())*100:.4f}%",extra_key="medr")
        stat_card("Excess Kurtosis",        f"{kurt_val:.4f}",                   extra_key="ku")

        # Beta vs NIFTY
        try:
            ndf = get_ohlcv("^NSEI", period_yf, lab_int)
            if ndf is not None and not ndf.empty:
                nr = ndf["Close"].pct_change().dropna()
                al = pd.concat([r_clean.rename("s"), nr.rename("n")], axis=1).dropna()
                if len(al) > 20:
                    beta_v = al.cov().iloc[0,1] / al["n"].var()
                    stat_card("Beta", f"{beta_v:.3f}", extra_key="beta")
        except Exception:
            pass

    # Calendar returns
    st.markdown("---")
    section_label("CALENDAR YEAR RETURNS")
    cal_df = pd.DataFrame({"Close": close})
    cal_df["Year"] = cal_df.index.year
    yearly = cal_df.groupby("Year")["Close"].apply(
        lambda x: (x.iloc[-1] / x.iloc[0] - 1) * 100 if len(x) > 1 else 0
    ).round(2).reset_index().rename(columns={"Close": "Return (%)"})
    fig_yr = go.Figure(go.Bar(
        x=yearly["Year"].astype(str), y=yearly["Return (%)"],
        marker_color=["rgba(22,163,74,.8)" if v >= 0 else "rgba(220,38,38,.8)" for v in yearly["Return (%)"]],
        text=[f"{v:+.1f}%" for v in yearly["Return (%)"]],
        textposition="outside", textfont=dict(color="#2D3A52", size=10),
    ))
    fig_yr.add_hline(y=0, line=dict(color="#DDE3EF", width=1))
    fig_yr.update_layout(**_lyt(height=280, title="Annual Returns"))
    st.plotly_chart(fig_yr, use_container_width=True)

    # Monthly heatmap
    if len(cal_df) > 60:
        section_label("MONTHLY RETURNS HEATMAP")
        monthly = cal_df.groupby(["Year", "Month"])["Close"].apply(
            lambda x: (x.iloc[-1] / x.iloc[0] - 1) * 100 if len(x) > 1 else 0
        ).unstack("Month")
        monthly.columns = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][:len(monthly.columns)]
        fig_mh = go.Figure(go.Heatmap(
            z=monthly.values, x=monthly.columns.tolist(), y=monthly.index.astype(str).tolist(),
            colorscale=[[0,"#B91C1C"],[0.5,"#F3F4F6"],[1,"#15803D"]],
            zmid=0,
            text=[[f"{v:.1f}%" if not np.isnan(v) else "" for v in row] for row in monthly.values],
            texttemplate="%{text}", textfont=dict(size=9, color="#0F172A"),
            colorbar=dict(tickfont=dict(color="#5A6A88"),
                          title=dict(text="Ret%", font=dict(color="#5A6A88"))),
        ))
        fig_mh.update_layout(**_lyt(height=max(250, len(monthly)*28+60)))
        st.plotly_chart(fig_mh, use_container_width=True)


# ══════════════════════════════════════════════════════════════
# TAB 4 — REGRESSION  (Issues #14 #15: all modes + predict + multivariate)
# ══════════════════════════════════════════════════════════════
with tab4:
    section_label("REGRESSION ANALYSIS")

    reg_a, reg_b = st.columns([1, 3])
    with reg_a:
        reg_type = st.selectbox("Regression Type", [
            "Price vs Time (Trend)",
            "Returns vs Lagged Returns",
            "Price vs NIFTY 50 (Beta)",
            "Price vs Volume",
            "Multivariate (up to 5 securities)",
        ], key="reg_t")
        reg_degree = st.selectbox("Polynomial Degree (for trend)", [1, 2, 3], key="reg_d")

        # Issue #14: per-regression time controls
        st.markdown("**Time Controls**")
        reg_period_sel = st.selectbox("Regression Period", ["1Y","2Y","3Y","5Y","Max"], index=1, key="reg_period")
        reg_int_sel    = st.selectbox("Candle Interval",   ["1d","1wk","1mo"], key="reg_int")
        TFR2 = {"1Y":"2y","2Y":"5y","3Y":"10y","5Y":"10y","Max":"max"}
        reg_pf = TFR2[reg_period_sel]

        # Prediction controls
        st.markdown("**Prediction**")
        predict_horizon = st.number_input("Predict N days ahead", value=30, min_value=1, max_value=365, step=5, key="reg_pred_h")
        show_predict    = st.checkbox("Show prediction", value=True, key="reg_show_pred")

        # Multivariate securities
        if "Multivariate" in reg_type:
            st.markdown("**Independent Variables (up to 5)**")
            multi_syms = st.multiselect(
                "Select 1–5 securities",
                [s for s in all_syms if s != lab_sym],
                default=["NIFTY 50" if "NIFTY 50" in INDICES else all_syms[1]],
                max_selections=5,
                key="reg_multi_syms",
            )

        # Lag control
        if reg_type == "Returns vs Lagged Returns":
            lag_val = st.number_input("Lag (days)", value=1, min_value=1, max_value=60, key="reg_lag_val")

        run_reg = st.button("Run Regression", key="run_reg", type="primary")

    with reg_b:
        if run_reg:
            # Fetch data for the selected regression period/interval
            df_reg = get_ohlcv(lab_sym, reg_pf, reg_int_sel)
            if df_reg is None or df_reg.empty:
                st.error("No data for selected period/interval.")
                st.stop()
            close_reg = df_reg["Close"]
            rets_reg  = close_reg.pct_change().dropna()

            # ── Price vs Time ────────────────────────────────────────────────
            if reg_type == "Price vs Time (Trend)":
                X = np.arange(len(close_reg))
                y = close_reg.values
                coeffs = np.polyfit(X, y, deg=reg_degree)
                y_hat  = np.polyval(coeffs, X)
                residuals = y - y_hat
                r2 = 1 - np.sum(residuals**2) / np.sum((y - y.mean())**2)

                # Prediction
                if show_predict:
                    X_future = np.arange(len(close_reg), len(close_reg) + predict_horizon)
                    y_future = np.polyval(coeffs, X_future)
                    future_dates = pd.date_range(close_reg.index[-1], periods=predict_horizon+1, freq="B")[1:]

                fig_reg = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[.65,.35], vertical_spacing=.04)
                fig_reg.add_trace(go.Scatter(x=close_reg.index, y=y, mode="lines",
                    line=dict(color=CHART_COLORS[0], width=1.3), name="Price"), row=1, col=1)
                fig_reg.add_trace(go.Scatter(x=close_reg.index, y=y_hat, mode="lines",
                    line=dict(color=CHART_COLORS[2], width=1.5, dash="dash"), name=f"Poly-{reg_degree} Fit"), row=1, col=1)
                if show_predict:
                    fig_reg.add_trace(go.Scatter(x=future_dates, y=y_future, mode="lines",
                        line=dict(color=CHART_COLORS[4], width=1.4, dash="dot"), name=f"Forecast {predict_horizon}d"), row=1, col=1)
                    fig_reg.add_vline(x=close_reg.index[-1], line=dict(color="#C8D0E4", width=1, dash="dot"), row=1, col=1)
                fig_reg.add_trace(go.Bar(x=close_reg.index, y=residuals,
                    marker_color=["rgba(22,163,74,.7)" if v >= 0 else "rgba(220,38,38,.7)" for v in residuals],
                    showlegend=False, name="Residuals"), row=2, col=1)
                fig_reg.add_hline(y=0, line=dict(color="#DDE3EF", width=.7), row=2, col=1)
                fig_reg.update_layout(**_lyt(height=440))
                for i in [1, 2]:
                    fig_reg.update_xaxes(showgrid=True, gridcolor="#EAEEf8", color="#5A6A88", row=i, col=1)
                    fig_reg.update_yaxes(showgrid=True, gridcolor="#EAEEf8", color="#5A6A88", side="right", row=i, col=1)
                st.plotly_chart(fig_reg, use_container_width=True)

                stat_card("R² Score", f"{r2:.4f}", extra_key="r2_trend")
                if show_predict:
                    st.markdown(f"""
                    <div class="stat-card">
                      <div class="stat-lbl">Predicted Price in {predict_horizon} trading days</div>
                      <div class="stat-val">₹{y_future[-1]:,.2f}</div>
                      <div style="color:var(--t3);font-size:.75rem;">
                        Based on Poly-{reg_degree} trend extrapolation. Not a financial forecast.
                      </div>
                    </div>""", unsafe_allow_html=True)

            # ── Beta vs NIFTY ────────────────────────────────────────────────
            elif reg_type == "Price vs NIFTY 50 (Beta)":
                ndf = get_ohlcv("^NSEI", reg_pf, reg_int_sel)
                if ndf is not None and not ndf.empty:
                    nr = ndf["Close"].pct_change().dropna()
                    sr = close_reg.pct_change().dropna()
                    aligned = pd.concat([sr.rename("Stock"), nr.rename("NIFTY")], axis=1).dropna()
                    X = aligned["NIFTY"].values; y = aligned["Stock"].values
                    slope, intercept, r_val, p_val, std_err = scipy_stats.linregress(X, y)
                    y_hat = slope * X + intercept

                    fig_beta = go.Figure()
                    fig_beta.add_trace(go.Scatter(x=X*100, y=y*100, mode="markers",
                        marker=dict(color=CHART_COLORS[0], size=4, opacity=.5), name="Daily Returns"))
                    x_line = np.sort(X)
                    fig_beta.add_trace(go.Scatter(x=x_line*100, y=(slope*x_line+intercept)*100,
                        mode="lines", line=dict(color=CHART_COLORS[2], width=2), name="Regression Line"))
                    fig_beta.update_layout(**_lyt(height=400,
                        title=f"Beta Regression: {lab_sym} vs NIFTY 50"))
                    st.plotly_chart(fig_beta, use_container_width=True)

                    rc1, rc2, rc3, rc4 = st.columns(4)
                    for col_, lbl_, val_ in [
                        (rc1, "Beta (Slope)",      f"{slope:.4f}"),
                        (rc2, "Alpha (Ann. %)",     f"{intercept*252*100:.4f}"),
                        (rc3, "R² Score",           f"{r_val**2:.4f}"),
                        (rc4, "P-value",            f"{p_val:.4e}"),
                    ]:
                        with col_:
                            stat_card(lbl_, val_, extra_key=f"beta_{lbl_}")

            # ── Returns vs Lagged Returns ─────────────────────────────────────
            elif reg_type == "Returns vs Lagged Returns":
                lag = int(lag_val)
                r_arr = rets_reg.dropna().values
                y_r = r_arr[lag:]; X_r = r_arr[:-lag]
                slope, intercept, r_val, p_val, _ = scipy_stats.linregress(X_r, y_r)

                fig_lag = go.Figure()
                fig_lag.add_trace(go.Scatter(x=X_r*100, y=y_r*100, mode="markers",
                    marker=dict(color=CHART_COLORS[0], size=3, opacity=.45), name="Returns"))
                x_line = np.linspace(X_r.min(), X_r.max(), 100)
                fig_lag.add_trace(go.Scatter(x=x_line*100, y=(slope*x_line+intercept)*100,
                    mode="lines", line=dict(color=CHART_COLORS[2], width=2), name="Fit"))
                fig_lag.update_layout(**_lyt(height=380,
                    title=f"Return(t) vs Return(t-{lag})"))
                st.plotly_chart(fig_lag, use_container_width=True)

                stat_card("R² Score", f"{r_val**2:.4f}", extra_key="r2_lag")
                stat_card("Slope",    f"{slope:.4f}",    extra_key="slope_lag")
                stat_card("P-value",  f"{p_val:.4e}",    extra_key="p_lag")

            # ── Price vs Volume ───────────────────────────────────────────────
            elif reg_type == "Price vs Volume":
                if "Volume" not in df_reg.columns or df_reg["Volume"].dropna().empty:
                    st.warning("Volume data not available for this symbol.")
                else:
                    vol_s  = df_reg["Volume"].dropna()
                    pr_s   = close_reg.reindex(vol_s.index)
                    aligned = pd.concat([pr_s.rename("Price"), vol_s.rename("Volume")], axis=1).dropna()
                    X = np.log1p(aligned["Volume"].values)
                    y = aligned["Price"].values
                    slope, intercept, r_val, p_val, _ = scipy_stats.linregress(X, y)
                    y_hat = slope * X + intercept

                    fig_vol = go.Figure()
                    fig_vol.add_trace(go.Scatter(x=aligned["Volume"], y=aligned["Price"], mode="markers",
                        marker=dict(color=CHART_COLORS[0], size=4, opacity=.5), name="Data"))
                    sorted_idx = np.argsort(aligned["Volume"].values)
                    fig_vol.add_trace(go.Scatter(
                        x=aligned["Volume"].values[sorted_idx],
                        y=y_hat[sorted_idx],
                        mode="lines", line=dict(color=CHART_COLORS[2], width=2), name="Log-Linear Fit"))
                    fig_vol.update_layout(**_lyt(height=380, title=f"{lab_sym}: Price vs Volume (log scale)"))
                    st.plotly_chart(fig_vol, use_container_width=True)
                    stat_card("R² Score",   f"{r_val**2:.4f}", extra_key="r2_vol")
                    stat_card("Slope",      f"{slope:.4f}",    extra_key="slope_vol")
                    stat_card("P-value",    f"{p_val:.4e}",    extra_key="p_vol")

            # ── Multivariate ─────────────────────────────────────────────────
            elif "Multivariate" in reg_type:
                if not multi_syms:
                    st.warning("Select at least one independent variable.")
                else:
                    from sklearn.linear_model import LinearRegression
                    from sklearn.metrics import r2_score
                    import warnings; warnings.filterwarnings("ignore")

                    # Dependent: selected stock returns
                    y_base = close_reg.pct_change().dropna().rename("Target")

                    # Independent: returns of selected securities + NIFTY
                    X_frames = {"NIFTY 50": get_ohlcv("^NSEI", reg_pf, reg_int_sel)}
                    for s in multi_syms:
                        df_s = get_ohlcv(s, reg_pf, reg_int_sel)
                        if df_s is not None and not df_s.empty:
                            X_frames[s] = df_s

                    X_rets = {}
                    for name_, df_s in X_frames.items():
                        if df_s is not None and not df_s.empty:
                            X_rets[name_] = df_s["Close"].pct_change().dropna()

                    combined = pd.concat([y_base] + [v.rename(k) for k, v in X_rets.items()], axis=1).dropna()
                    if len(combined) < 30:
                        st.warning("Not enough overlapping data. Try a longer period.")
                    else:
                        Y = combined["Target"].values
                        X_mat = combined.drop(columns=["Target"]).values
                        feature_names = combined.drop(columns=["Target"]).columns.tolist()

                        reg_model = LinearRegression().fit(X_mat, Y)
                        Y_hat = reg_model.predict(X_mat)
                        r2_mv = r2_score(Y, Y_hat)
                        residuals_mv = Y - Y_hat

                        # Coefficients chart
                        coef_df = pd.DataFrame({"Feature": feature_names, "Coefficient": reg_model.coef_})
                        coef_df = coef_df.sort_values("Coefficient", key=abs, ascending=False)
                        fig_coef = go.Figure(go.Bar(
                            x=coef_df["Coefficient"], y=coef_df["Feature"], orientation="h",
                            marker_color=["rgba(22,163,74,.8)" if v >= 0 else "rgba(220,38,38,.8)" for v in coef_df["Coefficient"]],
                            text=[f"{v:.4f}" for v in coef_df["Coefficient"]], textposition="outside",
                            textfont=dict(color="#2D3A52", size=10),
                        ))
                        fig_coef.update_layout(**_lyt(height=280, title=f"Regression Coefficients — {lab_sym}",
                            xaxis={**PLOTLY_LAYOUT["xaxis"], "side": "bottom"}))
                        st.plotly_chart(fig_coef, use_container_width=True)

                        # Actual vs predicted scatter
                        fig_avp = go.Figure()
                        fig_avp.add_trace(go.Scatter(x=Y*100, y=Y_hat*100, mode="markers",
                            marker=dict(color=CHART_COLORS[0], size=4, opacity=.5), name="Data"))
                        mn = min(Y.min(), Y_hat.min())*100; mx = max(Y.max(), Y_hat.max())*100
                        fig_avp.add_trace(go.Scatter(x=[mn,mx], y=[mn,mx], mode="lines",
                            line=dict(color=DOWN, width=1.5, dash="dash"), name="Perfect Fit"))
                        fig_avp.update_layout(**_lyt(height=340, title="Actual vs Predicted Returns (%)"))
                        st.plotly_chart(fig_avp, use_container_width=True)

                        c1_, c2_, c3_ = st.columns(3)
                        for col_, lbl_, val_ in [
                            (c1_, "R² Score",      f"{r2_mv:.4f}"),
                            (c2_, "Intercept",     f"{reg_model.intercept_:.6f}"),
                            (c3_, "Features Used", f"{len(feature_names)}"),
                        ]:
                            with col_: stat_card(lbl_, val_, extra_key=f"mv_{lbl_}")

                        # Prediction for next N candles
                        if show_predict:
                            latest_X = X_mat[-1].reshape(1, -1)
                            pred_ret = reg_model.predict(latest_X)[0]
                            pred_price = float(close_reg.iloc[-1]) * (1 + pred_ret) ** predict_horizon
                            st.markdown(f"""
                            <div class="stat-card">
                              <div class="stat-lbl">Extrapolated Price ({predict_horizon} candles ahead)</div>
                              <div class="stat-val">₹{pred_price:,.2f}</div>
                              <div style="color:var(--t3);font-size:.75rem;">
                                Single-candle predicted return of {pred_ret*100:.4f}% compounded {predict_horizon}×. Indicative only.
                              </div>
                            </div>""", unsafe_allow_html=True)
        else:
            st.info("Select regression type and click Run Regression.")


# ══════════════════════════════════════════════════════════════
# TAB 5 — HYPOTHESIS TESTS  (click-to-explain via stat_card)
# ══════════════════════════════════════════════════════════════
with tab5:
    section_label("STATISTICAL HYPOTHESIS TESTS")
    r_clean = returns.dropna().values
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("**Normality Tests**")
        sw_s, sw_p = scipy_stats.shapiro(r_clean[:5000])
        v_clr = "var(--red)" if sw_p < 0.05 else "var(--green)"
        stat_card("Shapiro-Wilk Test", f"{sw_s:.4f}",
                  p_value=f"{sw_p:.4e}",
                  verdict=("Reject normality" if sw_p < 0.05 else "Cannot reject normality"),
                  verdict_color=v_clr, extra_key="sw")

        jb_s, jb_p = scipy_stats.jarque_bera(r_clean)
        v_clr2 = "var(--red)" if jb_p < 0.05 else "var(--green)"
        stat_card("Jarque-Bera Test", f"{jb_s:.2f}",
                  p_value=f"{jb_p:.4e}",
                  verdict=("Non-normal distribution" if jb_p < 0.05 else "Normal-like distribution"),
                  verdict_color=v_clr2, extra_key="jb")

        dag_s, dag_p = scipy_stats.normaltest(r_clean)
        stat_card("D'Agostino K² Test", f"{dag_s:.4f}",
                  p_value=f"{dag_p:.4e}",
                  verdict=("Significant departure from normal" if dag_p < 0.05 else "Normal-like"),
                  verdict_color="var(--red)" if dag_p < 0.05 else "var(--green)", extra_key="dag")

    with c2:
        st.markdown("**Stationarity Tests**")
        try:
            from statsmodels.tsa.stattools import adfuller, kpss
            adf_r = adfuller(close.dropna(), autolag="AIC")
            stat_card("ADF Test (Unit Root)", f"{adf_r[0]:.4f}",
                      p_value=f"{adf_r[1]:.4e}",
                      verdict=("Stationary — reject unit root" if adf_r[1] < 0.05 else "Non-stationary (unit root present)"),
                      verdict_color="var(--green)" if adf_r[1] < 0.05 else "var(--red)", extra_key="adf")

            kpss_r = kpss(close.dropna(), regression="c", nlags="auto")
            stat_card("KPSS Test", f"{kpss_r[0]:.4f}",
                      p_value=f"{kpss_r[1]:.3f}",
                      verdict=("Non-stationary" if kpss_r[1] < 0.05 else "Stationary"),
                      verdict_color="var(--red)" if kpss_r[1] < 0.05 else "var(--green)", extra_key="kpss")

            adf_r2 = adfuller(returns.dropna(), autolag="AIC")
            stat_card("ADF on Returns", f"{adf_r2[0]:.4f}",
                      p_value=f"{adf_r2[1]:.4e}",
                      verdict=("Returns stationary" if adf_r2[1] < 0.05 else "Returns non-stationary"),
                      verdict_color="var(--green)" if adf_r2[1] < 0.05 else "var(--red)", extra_key="adf2")
        except Exception as e:
            st.error(f"Stationarity tests failed: {e}")

    with c3:
        st.markdown("**Variance & Randomness Tests**")
        tstat, t_p = scipy_stats.ttest_1samp(r_clean, 0)
        stat_card("One-Sample t-test (μ=0)", f"{tstat:.4f}",
                  p_value=f"{t_p:.4e}",
                  verdict=("Mean return significantly ≠ 0" if t_p < 0.05 else "Mean not significantly different from 0"),
                  verdict_color="var(--green)" if t_p < 0.05 else "var(--t3)", extra_key="ttest")

        med_r = np.median(r_clean)
        rb = (r_clean > med_r).astype(int)
        n_runs_ = 1 + np.sum(np.diff(rb) != 0)
        n1_ = int(rb.sum()); n2_ = len(rb) - n1_
        if n1_ > 0 and n2_ > 0:
            mu_r = (2*n1_*n2_)/(n1_+n2_) + 1
            sg_r = np.sqrt((2*n1_*n2_*(2*n1_*n2_-n1_-n2_)) / ((n1_+n2_)**2*(n1_+n2_-1)))
            z_r  = (n_runs_ - mu_r) / sg_r if sg_r > 0 else 0
            p_r  = 2*(1-scipy_stats.norm.cdf(abs(z_r)))
            stat_card("Runs Test (Randomness)", f"{z_r:.4f}",
                      p_value=f"{p_r:.4f}",
                      verdict=("Non-random — pattern detected" if p_r < 0.05 else "Random walk — no pattern"),
                      verdict_color="var(--red)" if p_r < 0.05 else "var(--green)", extra_key="runs")

        try:
            from statsmodels.stats.diagnostic import acorr_ljungbox
            lb_res = acorr_ljungbox(returns.dropna(), lags=[10], return_df=True)
            lb_s = float(lb_res["lb_stat"].iloc[0]); lb_p = float(lb_res["lb_pvalue"].iloc[0])
            stat_card("Ljung-Box (Autocorrelation)", f"{lb_s:.4f}",
                      p_value=f"{lb_p:.4f}",
                      verdict=("Significant autocorrelation" if lb_p < 0.05 else "No significant autocorrelation"),
                      verdict_color="var(--red)" if lb_p < 0.05 else "var(--green)", extra_key="lb")
        except Exception:
            pass

    st.markdown("---")
    section_label("TWO-SAMPLE COMPARISON")
    tw_a, tw_b = st.columns(2)
    with tw_a:
        comp_sym2 = st.selectbox("Compare with", [s for s in all_syms if s != lab_sym][:80], key="comp2")
        run_two   = st.button("Run Two-Sample Tests", key="two_samp", type="primary")
    with tw_b:
        if run_two:
            df2 = get_ohlcv(comp_sym2, period_yf, lab_int)
            if df2 is not None and not df2.empty:
                r2 = df2["Close"].pct_change().dropna()
                common = pd.concat([returns.rename("A"), r2.rename("B")], axis=1).dropna()
                a_v, b_v = common["A"].values, common["B"].values
                for test_name, stat_v_, p_v_, interpretation in [
                    ("Welch t-test",       *scipy_stats.ttest_ind(a_v, b_v, equal_var=False),
                     lambda p: "Mean returns differ" if p < 0.05 else "Mean returns not significantly different"),
                    ("Mann-Whitney U",     *scipy_stats.mannwhitneyu(a_v, b_v, alternative="two-sided"),
                     lambda p: "Distributions differ" if p < 0.05 else "No significant difference"),
                    ("Levene (Variance)",  *scipy_stats.levene(a_v, b_v),
                     lambda p: "Variances differ" if p < 0.05 else "Variances similar"),
                    ("KS Test",            *scipy_stats.ks_2samp(a_v, b_v),
                     lambda p: "Distributions differ" if p < 0.05 else "Distributions similar"),
                ]:
                    reject = p_v_ < 0.05
                    vc = "var(--red)" if reject else "var(--green)"
                    stat_card(test_name, f"{stat_v_:.4f}",
                              p_value=f"{p_v_:.4e}",
                              verdict=interpretation(p_v_),
                              verdict_color=vc, extra_key=f"two_{test_name}")


# ══════════════════════════════════════════════════════════════
# TAB 6 — MONTE CARLO
# ══════════════════════════════════════════════════════════════
with tab6:
    section_label("MONTE CARLO SIMULATION")
    mc_a, mc_b = st.columns([1, 3])
    with mc_a:
        n_sims   = st.number_input("Simulations", 100, 5000, 500, 100, key="mc_n")
        n_days   = st.number_input("Forecast Days", 30, 1260, 252, 30, key="mc_d")
        mc_model = st.selectbox("Model", ["Geometric Brownian Motion","Bootstrap Resampling"], key="mc_m")
        conf_lvl = st.slider("Confidence Level (%)", 80, 99, 95, key="mc_cl")
        run_mc   = st.button("Run Monte Carlo", key="run_mc", type="primary")

    with mc_b:
        if run_mc:
            with st.spinner(f"Running {n_sims:,} simulations over {n_days} trading days..."):
                mu_d = float(returns.mean()); sig_d = float(returns.std())
                s0 = float(close.iloc[-1])
                sims = np.zeros((n_days, int(n_sims)))
                if mc_model == "Geometric Brownian Motion":
                    rng = np.random.default_rng()
                    z = rng.standard_normal((n_days, int(n_sims)))
                    sims = s0 * np.exp(np.cumsum((mu_d - 0.5*sig_d**2) + sig_d*z, axis=0))
                else:
                    r_arr = returns.dropna().values
                    for j in range(int(n_sims)):
                        boot = np.random.choice(r_arr, size=n_days, replace=True)
                        sims[:, j] = s0 * np.cumprod(1 + boot)

            fig_mc = go.Figure()
            plot_n = min(150, int(n_sims))
            for j in range(plot_n):
                fig_mc.add_trace(go.Scatter(y=sims[:, j], mode="lines",
                    line=dict(color=f"rgba(29,78,216,.05)", width=.5), showlegend=False))

            alpha = (100 - conf_lvl) / 2
            p_lo  = np.percentile(sims, alpha,       axis=1)
            p_hi  = np.percentile(sims, 100-alpha,   axis=1)
            p_med = np.median(sims, axis=1)
            fig_mc.add_trace(go.Scatter(y=p_hi, mode="lines", line=dict(color=UP, width=1.5, dash="dash"), name=f"P{100-alpha:.0f}"))
            fig_mc.add_trace(go.Scatter(y=p_lo, mode="lines", line=dict(color=DOWN, width=1.5, dash="dash"),
                fill="tonexty", fillcolor="rgba(100,100,100,.06)", name=f"P{alpha:.0f}"))
            fig_mc.add_trace(go.Scatter(y=p_med, mode="lines", line=dict(color=CHART_COLORS[2], width=2), name="Median"))
            fig_mc.add_hline(y=s0, line=dict(color="#8896B0", width=1, dash="dot"))
            fig_mc.update_layout(**_lyt(height=400,
                title=f"Monte Carlo ({mc_model}) — {n_days}d Forecast, {n_sims:,} sims",
                xaxis={**PLOTLY_LAYOUT["xaxis"], "title": "Trading Days", "side": "bottom"},
                yaxis={**PLOTLY_LAYOUT["yaxis"], "title": "Price (₹)"},
            ))
            st.plotly_chart(fig_mc, use_container_width=True)

            final_vals = sims[-1, :]
            fig_fv = go.Figure()
            fig_fv.add_trace(go.Histogram(x=final_vals, nbinsx=60, marker_color=CHART_COLORS[0], opacity=.75))
            fig_fv.add_vline(x=s0, line=dict(color=CHART_COLORS[2], width=1.5, dash="dash"))
            fig_fv.add_vline(x=float(np.median(final_vals)), line=dict(color=UP, width=1.5, dash="dot"))
            fig_fv.update_layout(**_lyt(height=240, showlegend=False))
            st.plotly_chart(fig_fv, use_container_width=True)

            mc_cols = st.columns(5)
            for col_, lbl_, val_ in zip(mc_cols, [
                ("Median Final",          f"₹{np.median(final_vals):,.1f}"),
                ("Mean Final",            f"₹{np.mean(final_vals):,.1f}"),
                (f"{conf_lvl}% CI Low",  f"₹{np.percentile(final_vals, (100-conf_lvl)/2):,.1f}"),
                (f"{conf_lvl}% CI High", f"₹{np.percentile(final_vals, 100-(100-conf_lvl)/2):,.1f}"),
                ("Prob > Current",        f"{(final_vals > s0).mean()*100:.1f}%"),
            ]):
                with col_:
                    st.markdown(f'<div class="stat-card"><div class="stat-lbl">{lbl_}</div><div class="stat-val">{val_}</div></div>', unsafe_allow_html=True)
        else:
            st.info("Configure parameters and click Run Monte Carlo.")
