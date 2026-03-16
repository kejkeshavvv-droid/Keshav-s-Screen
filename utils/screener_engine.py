"""
screener_engine.py — Keshav's Screen
AI-powered NL query parsing:
  - Groq (free tier, llama-3.3-70b) as primary AI — no cost
  - Anthropic Claude as secondary (if key provided)
  - Robust rule-based parser as final fallback
"""

import re
import json
import pandas as pd
import numpy as np


# ─── SYSTEM PROMPT (shared by all AI providers) ──────────────────────────────

_SYSTEM_PROMPT = """You parse stock screening queries into JSON filter objects for NSE Indian stocks.

Supported keys (all optional):
  _pe, _pb, _peg, _ev_ebitda       P/E, P/B, PEG, EV/EBITDA           (raw number)
  _roe, _roa, _npm, _opm           ROE/ROA/Net Margin/OPM              (decimal: 0.15 = 15%)
  _de, _cr, _qr                    D/E, Current Ratio, Quick Ratio     (raw number)
  _divy                            Dividend Yield                      (decimal: 0.03 = 3%)
  _rev_g, _earn_g                  Revenue/Earnings Growth             (decimal: 0.20 = 20%)
  _eps, _beta, _mc                 EPS, Beta, Market Cap in Crores
  _rsi_14                          RSI(14) value 0–100
  _macd_bull                       true/false
  _above_sma50, _above_sma200      true/false
  _supertrend_bull                 true/false
  _near_52w_high                   true/false  (within 5% of 52W high)
  _near_52w_low                    true/false  (within 5% of 52W low)
  _sectors                         list of sector strings e.g. ["IT","Banking"]
  _cap                             "Large", "Mid", or "Small"

Each numeric key maps to {"min":X} or {"max":X} or {"min":X,"max":Y}.
Return ONLY valid JSON, no markdown fences, no explanation."""


# ─── GROQ FREE API ───────────────────────────────────────────────────────────

def _parse_with_groq(query: str, api_key: str) -> dict | None:
    """
    Use Groq's free tier (llama-3.3-70b-versatile) to parse query.
    Free tier: 14,400 req/day, 500k tokens/day — plenty for a screener.
    Get a free key at console.groq.com
    """
    try:
        import requests
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user",   "content": query},
                ],
                "max_tokens": 400,
                "temperature": 0.1,
            },
            timeout=10,
        )
        if resp.status_code == 200:
            raw = resp.json()["choices"][0]["message"]["content"].strip()
            raw = re.sub(r"^```json\s*|```$", "", raw, flags=re.MULTILINE).strip()
            return json.loads(raw)
    except Exception:
        pass
    return None


# ─── ANTHROPIC CLAUDE ────────────────────────────────────────────────────────

def _parse_with_claude(query: str, api_key: str) -> dict | None:
    """Use Claude (if Anthropic key provided) to parse query."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",   # cheapest, fast
            max_tokens=400,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": query}],
        )
        raw = msg.content[0].text.strip()
        raw = re.sub(r"^```json\s*|```$", "", raw, flags=re.MULTILINE).strip()
        return json.loads(raw)
    except Exception:
        pass
    return None


# ─── GEMINI FREE API ─────────────────────────────────────────────────────────

def _parse_with_gemini(query: str, api_key: str) -> dict | None:
    """
    Google Gemini Flash free tier (1M tokens/day free).
    Get a free key at aistudio.google.com
    """
    try:
        import requests
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "systemInstruction": {"parts": [{"text": _SYSTEM_PROMPT}]},
                "contents": [{"parts": [{"text": query}]}],
                "generationConfig": {"maxOutputTokens": 400, "temperature": 0.1},
            },
            timeout=10,
        )
        if resp.status_code == 200:
            raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            raw = re.sub(r"^```json\s*|```$", "", raw, flags=re.MULTILINE).strip()
            return json.loads(raw)
    except Exception:
        pass
    return None


# ─── MAIN PARSE ENTRY POINT ──────────────────────────────────────────────────

def parse_query_with_ai(query: str, api_key: str = None, provider: str = "Groq (Free)") -> dict:
    """
    Route query to the selected AI provider, fallback to rule-based parser.
    provider: "Groq (Free)" | "Anthropic Claude" | "Google Gemini" | "OpenAI Compatible"
    """
    result = None

    if api_key:
        if provider == "Groq (Free)":
            result = _parse_with_groq(query, api_key)
        elif provider == "Anthropic Claude":
            result = _parse_with_claude(query, api_key)
        elif provider == "Google Gemini":
            result = _parse_with_gemini(query, api_key)

    # Fallback: rule-based parser (no API needed)
    if result is None:
        result = parse_simple_query(query)

    return result or {}


# Keep old name for backward compatibility
def parse_query_with_claude(query: str, api_key: str = None) -> dict:
    """Backward-compatible wrapper."""
    return parse_query_with_ai(query, api_key, provider="Anthropic Claude")


# ─── RULE-BASED QUERY PARSER ─────────────────────────────────────────────────

_SECTOR_MAP = {
    "it":                 "IT",
    "technology":         "IT",
    "tech":               "IT",
    "software":           "IT",
    "internet":           "Internet",
    "fintech":            "Internet",
    "pharma":             "Pharma",
    "pharmaceutical":     "Pharma",
    "healthcare":         "Healthcare",
    "hospital":           "Healthcare",
    "diagnostics":        "Healthcare",
    "bank":               "Banking",
    "banking":            "Banking",
    "psu bank":           "Banking",
    "finance":            "Finance",
    "nbfc":               "Finance",
    "insurance":          "Insurance",
    "fmcg":               "FMCG",
    "consumer staples":   "FMCG",
    "beverages":          "FMCG",
    "auto":               "Auto",
    "automobile":         "Auto",
    "automotive":         "Auto",
    "ev":                 "Auto",
    "tyre":               "Auto",
    "metal":              "Metals",
    "steel":              "Metals",
    "aluminium":          "Metals",
    "mining":             "Mining",
    "coal":               "Mining",
    "energy":             "Oil & Gas",
    "oil":                "Oil & Gas",
    "gas":                "Oil & Gas",
    "refinery":           "Oil & Gas",
    "power":              "Power",
    "renewable":          "Power",
    "solar":              "Power",
    "utility":            "Power",
    "cement":             "Cement",
    "real estate":        "Real Estate",
    "realty":             "Real Estate",
    "housing":            "Real Estate",
    "infra":              "Infra",
    "infrastructure":     "Infra",
    "construction":       "Infra",
    "capital goods":      "Capital Goods",
    "engineering":        "Capital Goods",
    "defence":            "Defence",
    "defense":            "Defence",
    "chemical":           "Chemicals",
    "specialty chemical": "Chemicals",
    "agrochemical":       "Chemicals",
    "telecom":            "Telecom",
    "media":              "Media",
    "entertainment":      "Media",
    "logistics":          "Logistics",
    "hospitality":        "Hospitality",
    "hotel":              "Hospitality",
    "consumer":           "Consumer",
    "durables":           "Consumer",
    "retail":             "Retail",
    "textile":            "Textiles",
    "apparel":            "Textiles",
}


def parse_simple_query(query: str) -> dict:
    """Rule-based NL → filter dict. Handles ~85% of common queries without any API."""
    f = {}
    q = query.lower()

    # ── Numeric filter extractor ──────────────────────────────────────────────
    def _num(text, pattern, field):
        for op_pat, comp in [
            (r'(?:below|under|less\s*than|<=?|max(?:imum)?)\s*(\d+(?:\.\d+)?)', "max"),
            (r'(?:above|over|greater\s*than|>=?|min(?:imum)?)\s*(\d+(?:\.\d+)?)', "min"),
            (r'between\s*(\d+(?:\.\d+)?)\s*(?:and|to|-)\s*(\d+(?:\.\d+)?)', "range"),
        ]:
            m = re.search(pattern + r'\s*' + op_pat, text)
            if m:
                groups = [g for g in m.groups() if g is not None]
                if not groups:
                    continue
                f.setdefault(field, {})
                if comp == "range" and len(groups) >= 2:
                    f[field]["min"] = float(groups[-2])
                    f[field]["max"] = float(groups[-1])
                else:
                    f[field][comp] = float(groups[-1])

    _num(q, r'rsi\s*(?:\(\s*\d+\s*\))?',               "_rsi_14")
    _num(q, r'p/?e\s*(?:ratio)?',                        "_pe")
    _num(q, r'p/?b\s*(?:ratio)?',                        "_pb")
    _num(q, r'peg\s*(?:ratio)?',                         "_peg")
    _num(q, r'ev/?ebitda',                               "_ev_ebitda")
    _num(q, r'roe',                                      "_roe_raw")
    _num(q, r'roa',                                      "_roa_raw")
    _num(q, r'net\s*(?:profit\s*)?margin',               "_npm_raw")
    _num(q, r'operating\s*(?:profit\s*)?margin|opm',     "_opm_raw")
    _num(q, r'd/?e\s*(?:ratio)?|debt\s*(?:to)?\s*equity',"_de")
    _num(q, r'current\s*ratio',                          "_cr")
    _num(q, r'dividend(?:\s*yield)?',                    "_divy_raw")
    _num(q, r'revenue\s*growth',                         "_rev_g_raw")
    _num(q, r'earnings?\s*growth|profit\s*growth',       "_earn_g_raw")
    _num(q, r'eps',                                      "_eps")
    _num(q, r'beta',                                     "_beta")
    _num(q, r'market\s*cap(?:italisation)?',             "_mc")

    # ── Percent-to-decimal conversions ───────────────────────────────────────
    for raw_key, dec_key in [
        ("_roe_raw", "_roe"), ("_roa_raw", "_roa"),
        ("_npm_raw", "_npm"), ("_opm_raw", "_opm"),
        ("_divy_raw", "_divy"), ("_rev_g_raw", "_rev_g"),
        ("_earn_g_raw", "_earn_g"),
    ]:
        if raw_key in f:
            entry = f.pop(raw_key)
            f[dec_key] = {k: v / 100 for k, v in entry.items()}

    # ── Keyword shortcuts ─────────────────────────────────────────────────────
    if any(x in q for x in ["oversold", "deeply oversold"]):
        f.setdefault("_rsi_14", {})["max"] = 30
    if "overbought" in q:
        f.setdefault("_rsi_14", {})["min"] = 70
    if any(x in q for x in ["debt free", "zero debt", "no debt", "debt-free"]):
        f["_de"] = {"max": 0.1}
    if any(x in q for x in ["high dividend", "high yield"]):
        f.setdefault("_divy", {})["min"] = 0.03
    if "quality" in q:
        f.setdefault("_roe", {})["min"] = 0.15
        f.setdefault("_de", {})["max"] = 0.5
    if "value" in q and "_pe" not in f:
        f.setdefault("_pe", {})["max"] = 20
    if any(x in q for x in ["growth stock", "high growth"]):
        f.setdefault("_earn_g", {})["min"] = 0.20
    if "profitable" in q:
        f.setdefault("_npm", {})["min"] = 0.05

    # ── Market cap ───────────────────────────────────────────────────────────
    if any(x in q for x in ["large cap", "largecap", "large-cap"]):
        f.setdefault("_mc", {})["min"] = 20000
    elif any(x in q for x in ["mid cap", "midcap", "mid-cap"]):
        f.setdefault("_mc", {})["min"] = 5000
        f.setdefault("_mc", {}).setdefault("max", 20000)
    elif any(x in q for x in ["small cap", "smallcap", "small-cap"]):
        f.setdefault("_mc", {})["max"] = 5000

    # ── Technical shortcuts ───────────────────────────────────────────────────
    if any(x in q for x in ["above sma 50", "above sma50", "sma 50 bullish"]):
        f["_above_sma50"] = True
    if any(x in q for x in ["above sma 200", "above sma200", "sma 200 bullish"]):
        f["_above_sma200"] = True
    if any(x in q for x in ["macd bullish", "macd crossover", "macd buy"]):
        f["_macd_bull"] = True
    if any(x in q for x in ["supertrend bull", "supertrend buy"]):
        f["_supertrend_bull"] = True
    if any(x in q for x in ["near 52 week high", "52w high", "52-week high"]):
        f["_near_52w_high"] = True
    if any(x in q for x in ["near 52 week low", "52w low", "52-week low"]):
        f["_near_52w_low"] = True

    # ── Sector detection ─────────────────────────────────────────────────────
    sectors = []
    for kw, sec in sorted(_SECTOR_MAP.items(), key=lambda x: -len(x[0])):  # longest match first
        if kw in q and sec not in sectors:
            sectors.append(sec)
            break  # one sector per query (avoid false double-matches)
    if sectors:
        f["_sectors"] = sectors

    # ── Index constituent filter ──────────────────────────────────────────────
    indices = []
    for idx in ["nifty 50", "nifty bank", "nifty it", "nifty pharma",
                "nifty fmcg", "nifty auto", "nifty metal", "nifty energy",
                "nifty midcap", "sensex"]:
        if idx in q:
            indices.append(idx.upper())
    if indices:
        f["_indices"] = indices

    return f


# ─── FILTER APPLICATION ──────────────────────────────────────────────────────

def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Apply parsed filter dict to screener DataFrame."""
    if df.empty:
        return df

    mask = pd.Series(True, index=df.index)

    # Raw numeric columns (stored as-is in df)
    _NUM_MAP = {
        "_pe":   "P/E",
        "_pb":   "P/B",
        "_peg":  "PEG",
        "_de":   "D/E Ratio",
        "_cr":   "Current Ratio",
        "_beta": "Beta",
        "_eps":  "EPS",
        "_mc":   "Market Cap (Cr)",
    }

    # Percent columns (stored as % values in df, e.g. 15.0 = 15%)
    _PCT_MAP = {
        "_roe":    "ROE (%)",
        "_roa":    "ROA (%)",
        "_npm":    "Net Margin (%)",
        "_opm":    "OPM (%)",
        "_divy":   "Dividend Yield (%)",
        "_rev_g":  "Revenue Growth (%)",
        "_earn_g": "Earnings Growth (%)",
    }

    for key, col in _NUM_MAP.items():
        entry = filters.get(key)
        if entry and isinstance(entry, dict) and col in df.columns:
            if "min" in entry:
                mask &= df[col].fillna(float("-inf")) >= entry["min"]
            if "max" in entry:
                mask &= df[col].fillna(float("inf"))  <= entry["max"]

    for key, col in _PCT_MAP.items():
        entry = filters.get(key)
        if entry and isinstance(entry, dict) and col in df.columns:
            mult = 100  # stored as % in df, filter values are decimal
            if "min" in entry:
                mask &= df[col].fillna(float("-inf")) >= entry["min"] * mult
            if "max" in entry:
                mask &= df[col].fillna(float("inf"))  <= entry["max"] * mult

    # Sectors
    if "_sectors" in filters and "Sector" in df.columns:
        mask &= df["Sector"].isin(filters["_sectors"])

    # Cap filter
    if "_cap" in filters and "Cap" in df.columns:
        cap_val = filters["_cap"]
        if isinstance(cap_val, str):
            mask &= df["Cap"].str.contains(cap_val, case=False, na=False)

    # RSI (requires TA computation pass to have added RSI_14 column)
    entry = filters.get("_rsi_14")
    if entry and isinstance(entry, dict) and "RSI_14" in df.columns:
        if "min" in entry:
            mask &= df["RSI_14"].fillna(float("-inf")) >= entry["min"]
        if "max" in entry:
            mask &= df["RSI_14"].fillna(float("inf"))  <= entry["max"]

    # Boolean TA flags
    for flag, col in [
        ("_above_sma50",      "Above_SMA50"),
        ("_above_sma200",     "Above_SMA200"),
        ("_macd_bull",        "MACD_Bull"),
        ("_supertrend_bull",  "ST_Bull"),
        ("_near_52w_high",    "Near_52W_High"),
        ("_near_52w_low",     "Near_52W_Low"),
    ]:
        if filters.get(flag) and col in df.columns:
            mask &= df[col].fillna(False)

    return df[mask].reset_index(drop=True)


# ─── PRESET SCREENS ──────────────────────────────────────────────────────────

PRESET_QUERIES = {
    "Quality Compounders":  "ROE above 20%, debt to equity below 0.5, net margin above 15%",
    "Deep Value":           "PE below 12, PB below 1.5, dividend yield above 2.5%",
    "High Growth":          "revenue growth above 25%, earnings growth above 25%",
    "Oversold RSI":         "RSI below 30",
    "Dividend Kings":       "dividend yield above 4%, PE below 20, ROE above 10%",
    "Golden Cross":         "above SMA 50, above SMA 200",
    "PSU Value":            "PE below 10, dividend yield above 3%, large cap",
    "Mid Cap Growth":       "mid cap, earnings growth above 20%, ROE above 15%",
    "Debt Free Growth":     "debt free, ROE above 15%, net margin above 10%",
    "Turnaround Bets":      "earnings growth above 30%, PE below 20, small cap",
    "GARP":                 "PEG below 1, ROE above 15%, earnings growth above 10%",
    "52W Low Bounce":       "near 52 week low, RSI below 40",
}
