"""
data_fetcher.py — Keshav's Screen
High-performance data layer:
  - ThreadPoolExecutor for parallel batch fetching (10x speedup)
  - NSE direct API for near-real-time live prices
  - yfinance for OHLCV historical data (robust, cached)
  - Smart TTL caching at every layer
"""

import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import requests
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

# ─── Import from local utils ─────────────────────────────────────────────────
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
try:
    from nse_stocks import NSE_STOCKS_EXTENDED, INDICES, yf_ticker, load_nse_universe
except ImportError:
    from utils.nse_stocks import NSE_STOCKS_EXTENDED, INDICES, yf_ticker, load_nse_universe

# ─── NSE SESSION (for live data) ─────────────────────────────────────────────

_NSE_HEADERS = {
    'User-Agent':      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept':          'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer':         'https://www.nseindia.com/',
    'Origin':          'https://www.nseindia.com',
    'Connection':      'keep-alive',
}

_nse_session: requests.Session | None = None
_nse_session_time: float = 0.0
_NSE_SESSION_TTL = 300  # 5 min session refresh


def _get_nse_session() -> requests.Session:
    """Return a warmed-up NSE session (reuses if still valid)"""
    global _nse_session, _nse_session_time
    now = time.time()
    if _nse_session is None or (now - _nse_session_time) > _NSE_SESSION_TTL:
        s = requests.Session()
        s.headers.update(_NSE_HEADERS)
        try:
            s.get('https://www.nseindia.com', timeout=6)
        except Exception:
            pass
        _nse_session = s
        _nse_session_time = now
    return _nse_session


def _nse_quote_live(symbol: str) -> dict | None:
    """
    Fetch live quote from NSE API.
    Returns dict with price/change/pct or None on failure.
    """
    try:
        sess = _get_nse_session()
        url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol.upper()}"
        resp = sess.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            pd_ = data.get("priceInfo", {})
            ltp = pd_.get("lastPrice")
            pc = pd_.get("previousClose") or ltp
            chg = (ltp - pc) if ltp and pc else 0
            pct = (chg / pc * 100) if pc else 0
            return {
                "price": ltp,
                "change": chg,
                "pct": pct,
                "open": pd_.get("open"),
                "high": pd_.get("intraDayHighLow", {}).get("max"),
                "low": pd_.get("intraDayHighLow", {}).get("min"),
                "prev_close": pc,
                "source": "NSE",
            }
    except Exception:
        pass
    return None


def _yf_quote_live(symbol: str) -> dict | None:
    """Fallback live quote via yfinance fast_info"""
    try:
        t = yf.Ticker(yf_ticker(symbol))
        fi = t.fast_info
        p = getattr(fi, "last_price", None)
        pc = getattr(fi, "previous_close", p) or p
        chg = (p - pc) if (p and pc) else 0
        pct = (chg / pc * 100) if pc else 0
        return {
            "price": p,
            "change": chg,
            "pct": pct,
            "high": getattr(fi, "year_high", None),
            "low": getattr(fi, "year_low", None),
            "prev_close": pc,
            "source": "yfinance",
        }
    except Exception:
        return None


# ─── OHLCV ───────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def get_ohlcv(symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """Fetch OHLCV data. Cached 60s."""
    try:
        ticker = yf_ticker(symbol)
        df = yf.download(ticker, period=period, interval=interval,
                         auto_adjust=True, progress=False, timeout=15)
        if df.empty:
            return pd.DataFrame()
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]
        df.index = pd.to_datetime(df.index)
        return df.dropna(subset=["Close"])
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=60)
def get_ohlcv_batch(symbols: list, period: str = "1y", interval: str = "1d") -> dict:
    """Batch OHLCV download for multiple symbols in a single yfinance call."""
    result = {}
    tickers = [yf_ticker(s) for s in symbols]
    try:
        raw = yf.download(tickers, period=period, interval=interval,
                          auto_adjust=True, group_by="ticker", progress=False, timeout=30)
        for s, t in zip(symbols, tickers):
            try:
                if len(symbols) == 1:
                    df = raw.copy()
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = [c[0] for c in df.columns]
                else:
                    lvl0 = raw.columns.get_level_values(0) if isinstance(raw.columns, pd.MultiIndex) else []
                    df = raw[t].copy() if t in lvl0 else pd.DataFrame()
                df.index = pd.to_datetime(df.index)
                result[s] = df.dropna(subset=["Close"]) if not df.empty else pd.DataFrame()
            except Exception:
                result[s] = pd.DataFrame()
    except Exception:
        # Individual fallback
        for s in symbols:
            result[s] = get_ohlcv(s, period, interval)
    return result


# ─── LIVE PRICE (SINGLE) ─────────────────────────────────────────────────────

@st.cache_data(ttl=15)
def get_live_price(symbol: str) -> dict:
    """Single-stock live price. NSE primary → yfinance fallback. Cached 15s."""
    # Try NSE live first for equity symbols
    if symbol not in INDICES:
        data = _nse_quote_live(symbol)
        if data and data.get("price"):
            return data
    # Fallback to yfinance
    data = _yf_quote_live(symbol)
    return data or {}


# ─── LIVE PRICE BATCH (PARALLEL) ─────────────────────────────────────────────

def _fetch_single_price_yf(sym: str) -> tuple[str, dict]:
    """Worker: fetch one price via yfinance (for thread pool)"""
    try:
        t = yf.Ticker(yf_ticker(sym))
        fi = t.fast_info
        p = getattr(fi, "last_price", None)
        pc = getattr(fi, "previous_close", p) or p
        if p and pc:
            chg = p - pc
            pct = chg / pc * 100
            return sym, {
                "price": round(p, 2),
                "change": round(chg, 2),
                "pct": round(pct, 2),
                "prev_close": round(pc, 2),
                "mktcap": getattr(fi, "market_cap", None),
            }
    except Exception:
        pass
    return sym, {}


@st.cache_data(ttl=30)
def get_live_prices_batch(symbols: tuple) -> dict:
    """
    Parallel live prices for a list of symbols.
    Uses ThreadPoolExecutor — 10–20x faster than sequential fetching.
    symbols must be a tuple (hashable for Streamlit cache).
    Cached 30s.
    """
    result = {}
    with ThreadPoolExecutor(max_workers=20) as ex:
        futures = {ex.submit(_fetch_single_price_yf, sym): sym for sym in symbols}
        for future in as_completed(futures, timeout=25):
            try:
                sym, data = future.result()
                if data:
                    result[sym] = data
            except Exception:
                pass
    return result


@st.cache_data(ttl=60)
def get_indices_snapshot() -> pd.DataFrame:
    """Snapshot of all tracked indices — parallel fetch. Cached 60s."""
    symbols = list(INDICES.keys())
    rows = []

    def _fetch_idx(name: str, ticker: str) -> dict:
        try:
            t = yf.Ticker(ticker)
            fi = t.fast_info
            p = getattr(fi, "last_price", None)
            pc = getattr(fi, "previous_close", p) or p
            chg = (p - pc) if (p and pc) else 0
            pct = (chg / pc * 100) if pc else 0
            return {"Index": name, "Ticker": ticker, "Price": p,
                    "Change": round(chg, 2), "Change%": round(pct, 2)}
        except Exception:
            return {"Index": name, "Ticker": ticker, "Price": None, "Change": 0, "Change%": 0}

    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = {ex.submit(_fetch_idx, n, t): n for n, t in INDICES.items()}
        for future in as_completed(futures, timeout=20):
            try:
                rows.append(future.result())
            except Exception:
                pass

    return pd.DataFrame(rows) if rows else pd.DataFrame()


# ─── FUNDAMENTALS ────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def get_fundamentals(symbol: str) -> dict:
    """Full fundamental data for one stock. Cached 5 min."""
    try:
        t = yf.Ticker(yf_ticker(symbol))
        i = t.info
        meta = NSE_STOCKS_EXTENDED.get(symbol, {})
        mc = i.get("marketCap") or 0
        return {
            "name":               i.get("longName", meta.get("name", symbol)),
            "sector":             i.get("sector",   meta.get("sector", "")),
            "industry":           i.get("industry", meta.get("industry", "")),
            "description":        i.get("longBusinessSummary", ""),
            "website":            i.get("website", ""),
            "employees":          i.get("fullTimeEmployees"),
            "price":              i.get("currentPrice") or i.get("regularMarketPrice"),
            "prev_close":         i.get("previousClose"),
            "open":               i.get("open"),
            "day_high":           i.get("dayHigh"),
            "day_low":            i.get("dayLow"),
            "52w_high":           i.get("fiftyTwoWeekHigh"),
            "52w_low":            i.get("fiftyTwoWeekLow"),
            "avg_volume":         i.get("averageVolume"),
            "avg_volume_10d":     i.get("averageVolume10days"),
            "volume":             i.get("volume"),
            "pe_ratio":           i.get("trailingPE"),
            "forward_pe":         i.get("forwardPE"),
            "pb_ratio":           i.get("priceToBook"),
            "ps_ratio":           i.get("priceToSalesTrailing12Months"),
            "peg_ratio":          i.get("pegRatio"),
            "ev_ebitda":          i.get("enterpriseToEbitda"),
            "ev_revenue":         i.get("enterpriseToRevenue"),
            "market_cap":         mc,
            "market_cap_cr":      mc / 1e7,
            "enterprise_value":   i.get("enterpriseValue"),
            "eps":                i.get("trailingEps"),
            "forward_eps":        i.get("forwardEps"),
            "book_value":         i.get("bookValue"),
            "revenue_per_share":  i.get("revenuePerShare"),
            "roe":                i.get("returnOnEquity"),
            "roa":                i.get("returnOnAssets"),
            "net_margin":         i.get("profitMargins"),
            "gross_margin":       i.get("grossMargins"),
            "operating_margin":   i.get("operatingMargins"),
            "ebitda_margin":      i.get("ebitdaMargins"),
            "revenue_growth":     i.get("revenueGrowth"),
            "earnings_growth":    i.get("earningsGrowth"),
            "earnings_q_growth":  i.get("earningsQuarterlyGrowth"),
            "debt_to_equity":     i.get("debtToEquity"),
            "current_ratio":      i.get("currentRatio"),
            "quick_ratio":        i.get("quickRatio"),
            "total_cash":         i.get("totalCash"),
            "total_debt":         i.get("totalDebt"),
            "free_cashflow":      i.get("freeCashflow"),
            "operating_cashflow": i.get("operatingCashflow"),
            "total_revenue":      i.get("totalRevenue"),
            "ebitda":             i.get("ebitda"),
            "dividend_yield":     i.get("dividendYield"),
            "dividend_rate":      i.get("dividendRate"),
            "payout_ratio":       i.get("payoutRatio"),
            "ex_dividend_date":   i.get("exDividendDate"),
            "inst_holding":       i.get("heldPercentInstitutions"),
            "insider_holding":    i.get("heldPercentInsiders"),
            "shares_outstanding": i.get("sharesOutstanding"),
            "float_shares":       i.get("floatShares"),
            "beta":               i.get("beta"),
        }
    except Exception:
        return {}


@st.cache_data(ttl=600)
def get_financials(symbol: str) -> dict:
    """Income statement, balance sheet, cash flow. Cached 10 min."""
    try:
        t = yf.Ticker(yf_ticker(symbol))
        return {
            "income_annual":      t.financials,
            "income_quarterly":   t.quarterly_financials,
            "balance_annual":     t.balance_sheet,
            "balance_quarterly":  t.quarterly_balance_sheet,
            "cashflow_annual":    t.cashflow,
            "cashflow_quarterly": t.quarterly_cashflow,
        }
    except Exception:
        return {}


# ─── NEWS ─────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=1800)
def get_news(symbol: str, limit: int = 10) -> list:
    """
    News articles for a symbol.
    Tries yfinance first, then falls back gracefully.
    Cached 30 min.
    """
    articles = []

    # yfinance news
    try:
        t = yf.Ticker(yf_ticker(symbol))
        news = t.news or []
        articles.extend(news[:limit])
    except Exception:
        pass

    return articles[:limit]


@st.cache_data(ttl=1800)
def get_market_news(limit: int = 20) -> list:
    """General market news from multiple sources. Cached 30 min."""
    all_news = []
    seen = set()
    symbols = ["^NSEI", "RELIANCE", "HDFCBANK", "TCS", "INFY"]
    for sym in symbols:
        try:
            t = yf.Ticker(sym)
            for art in (t.news or []):
                title = art.get("title", "")
                if title and title not in seen:
                    seen.add(title)
                    all_news.append(art)
        except Exception:
            pass
    return all_news[:limit]


# ─── BATCH FUNDAMENTALS (Screener) — PARALLEL ─────────────────────────────────

def _fetch_one_fundamental(sym: str) -> dict | None:
    """Worker: fetch fundamentals for one stock (used in thread pool)"""
    try:
        t = yf.Ticker(yf_ticker(sym))
        i = t.info
        meta = NSE_STOCKS_EXTENDED.get(sym, {})
        price = i.get("currentPrice") or i.get("regularMarketPrice") or i.get("previousClose") or 0
        mc = (i.get("marketCap") or 0)
        w52h = i.get("fiftyTwoWeekHigh") or price
        w52l = i.get("fiftyTwoWeekLow") or price

        return {
            "Symbol":               sym,
            "Name":                 (i.get("longName") or meta.get("name", sym))[:30],
            "Sector":               i.get("sector",   meta.get("sector", "")),
            "Industry":             i.get("industry", meta.get("industry", "")),
            "Cap":                  meta.get("cap", ""),
            "Price":                round(price, 2),
            "Market Cap (Cr)":      round(mc / 1e7, 0),
            "P/E":                  i.get("trailingPE"),
            "Forward P/E":          i.get("forwardPE"),
            "P/B":                  i.get("priceToBook"),
            "PEG":                  i.get("pegRatio"),
            "EV/EBITDA":            i.get("enterpriseToEbitda"),
            "EPS":                  i.get("trailingEps"),
            "ROE (%)":              round((i.get("returnOnEquity")    or 0) * 100, 2),
            "ROA (%)":              round((i.get("returnOnAssets")    or 0) * 100, 2),
            "Net Margin (%)":       round((i.get("profitMargins")     or 0) * 100, 2),
            "Gross Margin (%)":     round((i.get("grossMargins")      or 0) * 100, 2),
            "OPM (%)":              round((i.get("operatingMargins")  or 0) * 100, 2),
            "D/E Ratio":            i.get("debtToEquity"),
            "Current Ratio":        i.get("currentRatio"),
            "Quick Ratio":          i.get("quickRatio"),
            "Dividend Yield (%)":   round((i.get("dividendYield")     or 0) * 100, 2),
            "Revenue Growth (%)":   round((i.get("revenueGrowth")     or 0) * 100, 2),
            "Earnings Growth (%)":  round((i.get("earningsGrowth")    or 0) * 100, 2),
            "Beta":                 i.get("beta"),
            "52W High":             w52h,
            "52W Low":              w52l,
            "% from 52W High":      round((price - w52h) / w52h * 100, 2) if w52h else None,
            "% from 52W Low":       round((price - w52l) / w52l * 100, 2) if w52l else None,
            "Volume":               i.get("volume"),
            "Avg Volume":           i.get("averageVolume"),
            "Inst Holding (%)":     round((i.get("heldPercentInstitutions") or 0) * 100, 2),
            # Raw filter columns
            "_pe":    i.get("trailingPE"),
            "_pb":    i.get("priceToBook"),
            "_roe":   i.get("returnOnEquity"),
            "_de":    i.get("debtToEquity"),
            "_cr":    i.get("currentRatio"),
            "_divy":  i.get("dividendYield"),
            "_mc":    mc / 1e7,
            "_rev_g": i.get("revenueGrowth"),
            "_earn_g":i.get("earningsGrowth"),
            "_npm":   i.get("profitMargins"),
            "_opm":   i.get("operatingMargins"),
            "_eps":   i.get("trailingEps"),
            "_beta":  i.get("beta"),
            "_peg":   i.get("pegRatio"),
        }
    except Exception:
        return None


def fetch_screener_batch(symbols: list, max_stocks: int = 200,
                          progress_placeholder=None) -> pd.DataFrame:
    """
    Parallel fundamental fetch for screener.
    Uses ThreadPoolExecutor with 15 workers — ~5x faster than sequential.
    Shows a Streamlit progress bar.
    """
    symbols = list(dict.fromkeys(symbols))[:max_stocks]  # dedupe + limit
    rows = []
    total = len(symbols)
    completed = 0

    prog = st.progress(0, text=f"Fetching data for {total} stocks...")

    with ThreadPoolExecutor(max_workers=15) as ex:
        futures = {ex.submit(_fetch_one_fundamental, sym): sym for sym in symbols}
        for future in as_completed(futures, timeout=120):
            try:
                result = future.result()
                if result:
                    rows.append(result)
            except Exception:
                pass
            completed += 1
            pct = completed / total
            prog.progress(pct, text=f"Fetching data: {completed}/{total} stocks...")

    prog.empty()
    return pd.DataFrame(rows) if rows else pd.DataFrame()


# ─── SECTOR PERFORMANCE — PARALLEL ───────────────────────────────────────────

@st.cache_data(ttl=120)
def get_sector_performance() -> pd.DataFrame:
    """Sector performance using representative stocks — parallel fetch. Cached 2 min."""
    reps = {
        "Banking":     ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS"],
        "IT":          ["TCS.NS",       "INFY.NS",      "WIPRO.NS"],
        "Pharma":      ["SUNPHARMA.NS", "DRREDDY.NS",   "CIPLA.NS"],
        "Auto":        ["MARUTI.NS",    "TATAMOTORS.NS","M&M.NS"],
        "FMCG":        ["HINDUNILVR.NS","ITC.NS",       "NESTLEIND.NS"],
        "Metals":      ["TATASTEEL.NS", "JSWSTEEL.NS",  "HINDALCO.NS"],
        "Energy":      ["RELIANCE.NS",  "ONGC.NS",      "NTPC.NS"],
        "Real Estate": ["DLF.NS",       "GODREJPROP.NS","OBEROIRLTY.NS"],
        "Infra":       ["LT.NS",        "ADANIENT.NS",  "SIEMENS.NS"],
        "Chemicals":   ["UPL.NS",       "PIIND.NS",     "DEEPAKNTR.NS"],
        "Consumer":    ["TITAN.NS",     "ASIANPAINT.NS","HAVELLS.NS"],
        "Cement":      ["ULTRACEMCO.NS","SHREECEM.NS",  "AMBUJACEM.NS"],
    }

    def _fetch_sector_pct(sector: str, stocks: list) -> dict:
        pcts = []
        for s in stocks:
            try:
                t = yf.Ticker(s)
                fi = t.fast_info
                p = getattr(fi, "last_price", None)
                pc = getattr(fi, "previous_close", p) or p
                if p and pc:
                    pcts.append((p - pc) / pc * 100)
            except Exception:
                pass
        return {"Sector": sector,
                "Return%": round(float(np.mean(pcts)), 2) if pcts else 0.0}

    rows = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {ex.submit(_fetch_sector_pct, sec, stks): sec
                   for sec, stks in reps.items()}
        for future in as_completed(futures, timeout=20):
            try:
                rows.append(future.result())
            except Exception:
                pass

    return pd.DataFrame(rows).sort_values("Return%", ascending=False) if rows else pd.DataFrame()


# ─── HEATMAP DATA — PARALLEL ─────────────────────────────────────────────────

@st.cache_data(ttl=120)
def fetch_heatmap_data(symbols: tuple, max_n: int = 100) -> pd.DataFrame:
    """
    Fetch price change data for heatmap — fully parallel.
    symbols: tuple of symbol strings (hashable for cache).
    Cached 2 min.
    """
    syms = list(symbols)[:max_n]
    universe = NSE_STOCKS_EXTENDED

    def _fetch_one(sym: str) -> dict | None:
        try:
            t = yf.Ticker(yf_ticker(sym))
            fi = t.fast_info
            p = getattr(fi, "last_price", None)
            pc = getattr(fi, "previous_close", p) or p
            if not p:
                return None
            pct = (p - pc) / pc * 100 if pc else 0
            mc = getattr(fi, "market_cap", 0) or 0
            meta = universe.get(sym, {})
            return {
                "Symbol":  sym,
                "Name":    meta.get("name", sym)[:22],
                "Sector":  meta.get("sector", "Other"),
                "Change%": round(pct, 2),
                "Price":   round(p, 2),
                "MCap_Cr": round(mc / 1e7, 1),
            }
        except Exception:
            return None

    rows = []
    with ThreadPoolExecutor(max_workers=20) as ex:
        futures = {ex.submit(_fetch_one, sym): sym for sym in syms}
        for future in as_completed(futures, timeout=30):
            try:
                r = future.result()
                if r:
                    rows.append(r)
            except Exception:
                pass

    return pd.DataFrame(rows) if rows else pd.DataFrame()


# ─── OPTIONS ─────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def get_options_chain(symbol: str) -> tuple:
    try:
        t = yf.Ticker(yf_ticker(symbol))
        dates = t.options
        if not dates:
            return {}, []
        chains = {}
        for d in dates[:4]:
            opt = t.option_chain(d)
            chains[d] = {"calls": opt.calls, "puts": opt.puts}
        return chains, list(dates)
    except Exception:
        return {}, []


# ─── UTILITIES ────────────────────────────────────────────────────────────────

def is_market_open() -> bool:
    """Check if NSE market is currently open (IST 09:15 – 15:30, Mon–Fri)"""
    try:
        import pytz
        tz = pytz.timezone("Asia/Kolkata")
        now = datetime.now(tz)
        if now.weekday() >= 5:
            return False
        open_t  = now.replace(hour=9,  minute=15, second=0, microsecond=0)
        close_t = now.replace(hour=15, minute=30, second=0, microsecond=0)
        return open_t <= now <= close_t
    except Exception:
        now = datetime.utcnow() + timedelta(hours=5, minutes=30)
        if now.weekday() >= 5:
            return False
        return (9 * 60 + 15) <= (now.hour * 60 + now.minute) <= (15 * 60 + 30)


def format_inr(val) -> str:
    """Format a number as Indian currency"""
    if val is None:
        return "—"
    try:
        f = float(val)
        if f >= 1e7:   return f"₹{f/1e7:.2f} Cr"
        if f >= 1e5:   return f"₹{f/1e5:.2f} L"
        return f"₹{f:,.2f}"
    except Exception:
        return str(val)
