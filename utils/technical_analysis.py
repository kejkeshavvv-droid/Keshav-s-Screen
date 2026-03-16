"""
Technical Analysis Library
All indicators computed from scratch using pandas/numpy — no external TA libraries required.
Covers: Moving Averages, Momentum, Volatility, Volume, Trend, Patterns, S&R
"""

import pandas as pd
import numpy as np


# ══════════════════════════════════════════════════════════════════════════════
# MOVING AVERAGES
# ══════════════════════════════════════════════════════════════════════════════

def sma(df: pd.DataFrame, period: int = 20) -> pd.Series:
    return df["Close"].rolling(window=period).mean()

def ema(df: pd.DataFrame, period: int = 20) -> pd.Series:
    return df["Close"].ewm(span=period, adjust=False).mean()

def wma(df: pd.DataFrame, period: int = 20) -> pd.Series:
    w = np.arange(1, period + 1)
    return df["Close"].rolling(period).apply(lambda x: np.dot(x, w) / w.sum(), raw=True)

def hma(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """Hull Moving Average = WMA(2*WMA(n/2) - WMA(n), sqrt(n))"""
    half = pd.DataFrame({"Close": wma(df, period // 2) * 2 - wma(df, period)})
    return wma(half, int(np.sqrt(period)))

def dema(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """Double EMA"""
    e1 = ema(df, period)
    e2 = e1.ewm(span=period, adjust=False).mean()
    return 2 * e1 - e2

def tema(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """Triple EMA"""
    e1 = ema(df, period)
    e2 = e1.ewm(span=period, adjust=False).mean()
    e3 = e2.ewm(span=period, adjust=False).mean()
    return 3 * e1 - 3 * e2 + e3

def vwap(df: pd.DataFrame) -> pd.Series:
    """Cumulative VWAP (resets daily — best for intraday)"""
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    return (tp * df["Volume"]).cumsum() / df["Volume"].cumsum()

def vwap_rolling(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """Rolling VWAP over `period` bars"""
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    return (tp * df["Volume"]).rolling(period).sum() / df["Volume"].rolling(period).sum()


# ══════════════════════════════════════════════════════════════════════════════
# VOLATILITY
# ══════════════════════════════════════════════════════════════════════════════

def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    hl  = df["High"] - df["Low"]
    hc  = (df["High"] - df["Close"].shift()).abs()
    lc  = (df["Low"]  - df["Close"].shift()).abs()
    tr  = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.ewm(span=period, adjust=False).mean()

def bollinger_bands(df: pd.DataFrame, period: int = 20, std: float = 2.0):
    m = sma(df, period)
    s = df["Close"].rolling(period).std()
    upper = m + std * s
    lower = m - std * s
    width = (upper - lower) / m.replace(0, np.nan)
    pct_b = (df["Close"] - lower) / (upper - lower).replace(0, np.nan)
    return upper, m, lower, width, pct_b

def keltner_channel(df: pd.DataFrame, period: int = 20, mult: float = 2.0):
    mid   = ema(df, period)
    band  = atr(df, period) * mult
    return mid + band, mid, mid - band

def donchian_channel(df: pd.DataFrame, period: int = 20):
    upper = df["High"].rolling(period).max()
    lower = df["Low"].rolling(period).min()
    mid   = (upper + lower) / 2
    return upper, mid, lower

def historical_volatility(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """Annualised HV (%)"""
    lr = np.log(df["Close"] / df["Close"].shift(1))
    return lr.rolling(period).std() * np.sqrt(252) * 100

def chaikin_volatility(df: pd.DataFrame, period: int = 10) -> pd.Series:
    hl = df["High"] - df["Low"]
    e  = hl.ewm(span=period, adjust=False).mean()
    return (e - e.shift(period)) / e.shift(period).replace(0, np.nan) * 100


# ══════════════════════════════════════════════════════════════════════════════
# MOMENTUM
# ══════════════════════════════════════════════════════════════════════════════

def rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    d    = df["Close"].diff()
    gain = d.clip(lower=0)
    loss = (-d).clip(lower=0)
    ag   = gain.ewm(com=period - 1, min_periods=period).mean()
    al   = loss.ewm(com=period - 1, min_periods=period).mean()
    rs   = ag / al.replace(0, np.nan)
    return 100 - 100 / (1 + rs)

def macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, sig: int = 9):
    e1 = df["Close"].ewm(span=fast, adjust=False).mean()
    e2 = df["Close"].ewm(span=slow, adjust=False).mean()
    ml = e1 - e2
    sl = ml.ewm(span=sig, adjust=False).mean()
    return ml, sl, ml - sl

def stochastic(df: pd.DataFrame, k: int = 14, d: int = 3, smooth: int = 3):
    lo   = df["Low"].rolling(k).min()
    hi   = df["High"].rolling(k).max()
    ks   = (df["Close"] - lo) / (hi - lo).replace(0, np.nan) * 100
    ks_s = ks.rolling(smooth).mean()
    ds   = ks_s.rolling(d).mean()
    return ks_s, ds

def williams_r(df: pd.DataFrame, period: int = 14) -> pd.Series:
    hi = df["High"].rolling(period).max()
    lo = df["Low"].rolling(period).min()
    return -100 * (hi - df["Close"]) / (hi - lo).replace(0, np.nan)

def cci(df: pd.DataFrame, period: int = 20) -> pd.Series:
    tp   = (df["High"] + df["Low"] + df["Close"]) / 3
    ma   = tp.rolling(period).mean()
    mad  = tp.rolling(period).apply(lambda x: np.mean(np.abs(x - x.mean())), raw=True)
    return (tp - ma) / (0.015 * mad.replace(0, np.nan))

def roc(df: pd.DataFrame, period: int = 12) -> pd.Series:
    return (df["Close"] - df["Close"].shift(period)) / df["Close"].shift(period).replace(0, np.nan) * 100

def momentum(df: pd.DataFrame, period: int = 10) -> pd.Series:
    return df["Close"] - df["Close"].shift(period)

def mfi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    tp   = (df["High"] + df["Low"] + df["Close"]) / 3
    rmf  = tp * df["Volume"]
    pos  = rmf.where(tp > tp.shift(1), 0)
    neg  = rmf.where(tp <= tp.shift(1), 0)
    pmf  = pos.rolling(period).sum()
    nmf  = neg.rolling(period).sum()
    mfr  = pmf / nmf.replace(0, np.nan)
    return 100 - 100 / (1 + mfr)

def tsi(df: pd.DataFrame, long: int = 25, short: int = 13) -> pd.Series:
    d   = df["Close"].diff()
    ds  = d.ewm(span=long, adjust=False).mean().ewm(span=short, adjust=False).mean()
    dsa = d.abs().ewm(span=long, adjust=False).mean().ewm(span=short, adjust=False).mean()
    return 100 * ds / dsa.replace(0, np.nan)


# ══════════════════════════════════════════════════════════════════════════════
# TREND
# ══════════════════════════════════════════════════════════════════════════════

def adx_dmi(df: pd.DataFrame, period: int = 14):
    """Returns ADX, +DI, -DI"""
    pdm = df["High"].diff().clip(lower=0)
    ndm = (-df["Low"].diff()).clip(lower=0)
    pdm = pdm.where(pdm > ndm, 0)
    ndm = ndm.where(ndm > pdm, 0)
    a   = atr(df, period)
    pdi = 100 * pdm.ewm(span=period, adjust=False).mean() / a.replace(0, np.nan)
    ndi = 100 * ndm.ewm(span=period, adjust=False).mean() / a.replace(0, np.nan)
    dx  = 100 * (pdi - ndi).abs() / (pdi + ndi).replace(0, np.nan)
    return dx.ewm(span=period, adjust=False).mean(), pdi, ndi

def aroon(df: pd.DataFrame, period: int = 25):
    au = df["High"].rolling(period + 1).apply(lambda x: x.argmax() / period * 100, raw=True)
    ad = df["Low"].rolling(period + 1).apply(lambda x: x.argmin() / period * 100, raw=True)
    return au, ad

def supertrend(df: pd.DataFrame, period: int = 7, mult: float = 3.0):
    hl2 = (df["High"] + df["Low"]) / 2
    av  = atr(df, period)
    ub  = hl2 + mult * av
    lb  = hl2 - mult * av
    st  = pd.Series(np.nan, index=df.index)
    dir_ = pd.Series(1,    index=df.index)
    for i in range(1, len(df)):
        if df["Close"].iloc[i] > ub.iloc[i - 1]:
            dir_.iloc[i] = 1
        elif df["Close"].iloc[i] < lb.iloc[i - 1]:
            dir_.iloc[i] = -1
        else:
            dir_.iloc[i] = dir_.iloc[i - 1]
        st.iloc[i] = lb.iloc[i] if dir_.iloc[i] == 1 else ub.iloc[i]
    return st, dir_

def parabolic_sar(df: pd.DataFrame, af0: float = 0.02, af_step: float = 0.02, af_max: float = 0.2):
    high, low, close = df["High"].values, df["Low"].values, df["Close"].values
    n   = len(close)
    sar = np.full(n, np.nan)
    ep  = np.full(n, np.nan)
    af  = np.full(n, af0)
    tr  = np.ones(n)          # 1=up, -1=down
    sar[0] = low[0]; ep[0] = high[0]
    for i in range(1, n):
        if tr[i - 1] == 1:
            sar[i] = min(sar[i - 1] + af[i - 1] * (ep[i - 1] - sar[i - 1]),
                         low[i - 1], low[max(0, i - 2)])
            if low[i] < sar[i]:
                tr[i] = -1; sar[i] = ep[i - 1]; ep[i] = low[i]; af[i] = af0
            else:
                tr[i] = 1
                if high[i] > ep[i - 1]:
                    ep[i] = high[i]; af[i] = min(af[i - 1] + af_step, af_max)
                else:
                    ep[i] = ep[i - 1]; af[i] = af[i - 1]
        else:
            sar[i] = max(sar[i - 1] + af[i - 1] * (ep[i - 1] - sar[i - 1]),
                         high[i - 1], high[max(0, i - 2)])
            if high[i] > sar[i]:
                tr[i] = 1; sar[i] = ep[i - 1]; ep[i] = high[i]; af[i] = af0
            else:
                tr[i] = -1
                if low[i] < ep[i - 1]:
                    ep[i] = low[i]; af[i] = min(af[i - 1] + af_step, af_max)
                else:
                    ep[i] = ep[i - 1]; af[i] = af[i - 1]
    return pd.Series(sar, index=df.index), pd.Series(tr, index=df.index)

def ichimoku(df: pd.DataFrame, tenkan: int = 9, kijun: int = 26, senkou_b: int = 52, disp: int = 26):
    def mid(h, l, p): return (h.rolling(p).max() + l.rolling(p).min()) / 2
    t  = mid(df["High"], df["Low"], tenkan)
    k  = mid(df["High"], df["Low"], kijun)
    sa = ((t + k) / 2).shift(disp)
    sb = mid(df["High"], df["Low"], senkou_b).shift(disp)
    ch = df["Close"].shift(-disp)
    return t, k, sa, sb, ch


# ══════════════════════════════════════════════════════════════════════════════
# VOLUME
# ══════════════════════════════════════════════════════════════════════════════

def obv(df: pd.DataFrame) -> pd.Series:
    d   = np.sign(df["Close"].diff().fillna(0))
    return (d * df["Volume"]).cumsum()

def ad_line(df: pd.DataFrame) -> pd.Series:
    mfm = ((df["Close"] - df["Low"]) - (df["High"] - df["Close"])) / \
          (df["High"] - df["Low"]).replace(0, np.nan)
    return (mfm * df["Volume"]).cumsum()

def chaikin_money_flow(df: pd.DataFrame, period: int = 20) -> pd.Series:
    mfm = ((df["Close"] - df["Low"]) - (df["High"] - df["Close"])) / \
          (df["High"] - df["Low"]).replace(0, np.nan)
    return (mfm * df["Volume"]).rolling(period).sum() / df["Volume"].rolling(period).sum()

def volume_oscillator(df: pd.DataFrame, fast: int = 5, slow: int = 10) -> pd.Series:
    ef = df["Volume"].ewm(span=fast, adjust=False).mean()
    es = df["Volume"].ewm(span=slow, adjust=False).mean()
    return (ef - es) / es.replace(0, np.nan) * 100

def ease_of_movement(df: pd.DataFrame, period: int = 14) -> pd.Series:
    dist = ((df["High"] + df["Low"]) / 2) - ((df["High"].shift() + df["Low"].shift()) / 2)
    br   = (df["Volume"] / 1e6) / (df["High"] - df["Low"]).replace(0, np.nan)
    return (dist / br.replace(0, np.nan)).rolling(period).mean()

def negative_volume_index(df: pd.DataFrame) -> pd.Series:
    pct = df["Close"].pct_change().fillna(0)
    nvi = pd.Series(1000.0, index=df.index)
    for i in range(1, len(df)):
        nvi.iloc[i] = nvi.iloc[i-1] * (1 + pct.iloc[i]) \
                      if df["Volume"].iloc[i] < df["Volume"].iloc[i-1] else nvi.iloc[i-1]
    return nvi


# ══════════════════════════════════════════════════════════════════════════════
# SUPPORT & RESISTANCE
# ══════════════════════════════════════════════════════════════════════════════

def find_support_resistance(df: pd.DataFrame, window: int = 10) -> dict:
    c = df["Close"]
    highs, lows = [], []
    for i in range(window, len(c) - window):
        sl = c.iloc[i - window: i + window + 1]
        if c.iloc[i] == sl.max(): highs.append(float(c.iloc[i]))
        if c.iloc[i] == sl.min(): lows.append(float(c.iloc[i]))

    def cluster(lvls, tol=0.015):
        if not lvls: return []
        lvls = sorted(lvls)
        groups = [[lvls[0]]]
        for l in lvls[1:]:
            if (l - groups[-1][-1]) / max(groups[-1][-1], 1) < tol:
                groups[-1].append(l)
            else:
                groups.append([l])
        return [float(np.mean(g)) for g in groups]

    return {"resistance": cluster(highs), "support": cluster(lows)}


def pivot_points(df: pd.DataFrame, method: str = "standard") -> dict:
    H, L, C = df["High"].iloc[-1], df["Low"].iloc[-1], df["Close"].iloc[-1]
    pp = (H + L + C) / 3
    if method == "standard":
        return {"PP": pp, "R1": 2*pp-L, "R2": pp+(H-L), "R3": H+2*(pp-L),
                "S1": 2*pp-H, "S2": pp-(H-L), "S3": L-2*(H-pp)}
    if method == "fibonacci":
        rng = H - L
        return {"PP": pp, "R1": pp+0.382*rng, "R2": pp+0.618*rng, "R3": pp+1.0*rng,
                "S1": pp-0.382*rng, "S2": pp-0.618*rng, "S3": pp-1.0*rng}
    if method == "camarilla":
        rng = H - L
        return {"PP": pp, "R1": C+rng*1.1/12, "R2": C+rng*1.1/6, "R3": C+rng*1.1/4,
                "S1": C-rng*1.1/12, "S2": C-rng*1.1/6, "S3": C-rng*1.1/4}
    return {}


def fibonacci_levels(df: pd.DataFrame, lookback: int = 50) -> dict:
    hi = df["High"].rolling(lookback).max().iloc[-1]
    lo = df["Low"].rolling(lookback).min().iloc[-1]
    rng = hi - lo
    return {"High": hi, "23.6%": hi-0.236*rng, "38.2%": hi-0.382*rng,
            "50.0%": hi-0.500*rng, "61.8%": hi-0.618*rng, "76.4%": hi-0.764*rng, "Low": lo}


# ══════════════════════════════════════════════════════════════════════════════
# CANDLESTICK PATTERNS
# ══════════════════════════════════════════════════════════════════════════════

def detect_patterns(df: pd.DataFrame) -> dict:
    o, h, l, c = df["Open"], df["High"], df["Low"], df["Close"]
    body = c - o
    body_abs = body.abs()
    uw = h - c.where(c >= o, o)
    lw = o.where(c >= o, c) - l
    rng = h - l

    patterns = {
        "Doji":              body_abs / rng.replace(0, np.nan) < 0.1,
        "Hammer":            (lw > 2 * body_abs) & (uw < body_abs) & (body_abs > 0),
        "Shooting Star":     (uw > 2 * body_abs) & (lw < body_abs) & (body_abs > 0),
        "Bullish Engulfing": (body.shift() < 0) & (body > 0) & (o <= c.shift()) & (c >= o.shift()),
        "Bearish Engulfing": (body.shift() > 0) & (body < 0) & (o >= c.shift()) & (c <= o.shift()),
        "Marubozu Bull":     (body > 0) & (uw < body_abs * 0.05) & (lw < body_abs * 0.05),
        "Marubozu Bear":     (body < 0) & (uw < body_abs * 0.05) & (lw < body_abs * 0.05),
        "Morning Star":      (body.shift(2) < -body_abs.shift(2) * 0.5) &
                             (body_abs.shift(1) < body_abs.shift(2) * 0.3) &
                             (body > body_abs * 0.5),
        "Evening Star":      (body.shift(2) > body_abs.shift(2) * 0.5) &
                             (body_abs.shift(1) < body_abs.shift(2) * 0.3) &
                             (body < -body_abs * 0.5),
        "Three White Soldiers": (body > 0) & (body.shift() > 0) & (body.shift(2) > 0) &
                                (c > c.shift()) & (c.shift() > c.shift(2)),
        "Three Black Crows":    (body < 0) & (body.shift() < 0) & (body.shift(2) < 0) &
                                (c < c.shift()) & (c.shift() < c.shift(2)),
        "Spinning Top":      (body_abs / rng.replace(0, np.nan) < 0.3) &
                             (uw > body_abs) & (lw > body_abs),
    }
    return patterns


# ══════════════════════════════════════════════════════════════════════════════
# ALL-IN-ONE + SIGNAL SUMMARY
# ══════════════════════════════════════════════════════════════════════════════

def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty or len(df) < 30:
        return df
    df = df.copy()
    for p in [5, 10, 20, 50, 100, 200]:
        df[f"SMA_{p}"] = sma(df, p)
        df[f"EMA_{p}"] = ema(df, p)
    if "Volume" in df.columns:
        df["VWAP"]  = vwap_rolling(df, 20)
        df["OBV"]   = obv(df)
        df["CMF"]   = chaikin_money_flow(df)
        df["ADL"]   = ad_line(df)
        df["MFI"]   = mfi(df)
        df["VO"]    = volume_oscillator(df)
    for p in [9, 14, 21]:
        df[f"RSI_{p}"] = rsi(df, p)
    ml, sl, mh = macd(df)
    df["MACD"] = ml; df["MACD_Signal"] = sl; df["MACD_Hist"] = mh
    df["Stoch_K"], df["Stoch_D"]   = stochastic(df)
    df["Williams_R"]               = williams_r(df)
    df["CCI"]                      = cci(df)
    df["ROC"]                      = roc(df)
    df["ADX"], df["DI+"], df["DI-"]= adx_dmi(df)
    df["BB_U"], df["BB_M"], df["BB_L"], df["BB_W"], df["BB_B"] = bollinger_bands(df)
    df["ATR"]                      = atr(df)
    df["HV_20"]                    = historical_volatility(df, 20)
    df["ST"], df["ST_Dir"]         = supertrend(df)
    df["PSAR"], df["PSAR_Trend"]   = parabolic_sar(df)
    ti, ki, sa, sb, ch             = ichimoku(df)
    df["ICH_T"] = ti; df["ICH_K"] = ki
    df["ICH_SA"] = sa; df["ICH_SB"] = sb; df["ICH_CH"] = ch
    df["KC_U"], df["KC_M"], df["KC_L"] = keltner_channel(df)
    df["DC_U"], df["DC_M"], df["DC_L"] = donchian_channel(df)
    df["AU"], df["AD"]             = aroon(df)
    return df


def get_ta_signal_summary(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return {"overall": "NEUTRAL", "buy": 0, "sell": 0, "neutral": 0, "details": []}
    row = df.iloc[-1]
    signals = []

    def s(name, sig, val=None):
        signals.append({"indicator": name, "signal": sig,
                        "value": round(float(val), 2) if val is not None else None})

    # RSI
    r14 = row.get("RSI_14")
    if r14 is not None:
        s("RSI(14)", "BUY" if r14 < 30 else "SELL" if r14 > 70 else "NEUTRAL", r14)
    # MACD
    if not pd.isna(row.get("MACD", np.nan)) and not pd.isna(row.get("MACD_Signal", np.nan)):
        s("MACD", "BUY" if row["MACD"] > row["MACD_Signal"] else "SELL")
    # SMAs
    for p in [20, 50, 200]:
        k = f"SMA_{p}"
        if k in row.index and not pd.isna(row[k]):
            s(f"SMA({p})", "BUY" if row["Close"] > row[k] else "SELL", row[k])
    # Stoch
    sk = row.get("Stoch_K")
    if sk is not None:
        s("Stoch %K", "BUY" if sk < 20 else "SELL" if sk > 80 else "NEUTRAL", sk)
    # ADX
    adx_v = row.get("ADX")
    if adx_v is not None:
        s("ADX(14)", "STRONG TREND" if adx_v > 25 else "WEAK TREND", adx_v)
    # Supertrend
    if not pd.isna(row.get("ST_Dir", np.nan)):
        s("Supertrend", "BUY" if row["ST_Dir"] == 1 else "SELL")
    # BB %B
    bb = row.get("BB_B")
    if bb is not None:
        s("BB %B", "BUY" if bb < 0 else "SELL" if bb > 1 else "NEUTRAL", bb)
    # Williams %R
    wr = row.get("Williams_R")
    if wr is not None:
        s("Williams %R", "BUY" if wr < -80 else "SELL" if wr > -20 else "NEUTRAL", wr)

    buy  = sum(1 for x in signals if x["signal"] in ("BUY",))
    sell = sum(1 for x in signals if x["signal"] in ("SELL",))
    neut = len(signals) - buy - sell
    overall = ("STRONG BUY" if buy >= sell + 3 else
               "BUY"        if buy > sell else
               "STRONG SELL" if sell >= buy + 3 else
               "SELL"        if sell > buy else "NEUTRAL")
    return {"overall": overall, "buy": buy, "sell": sell, "neutral": neut, "details": signals}
