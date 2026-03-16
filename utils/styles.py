"""
styles.py — Keshav's Screen
Professional light theme: clean, data-dense, mobile-first design.
No emojis. No dark background. Responsive CSS with mobile breakpoints.
"""
import streamlit as st

# ─── DESIGN TOKENS ───────────────────────────────────────────────────────────
# Light, professional financial terminal — similar to Refinitiv Eikon Light

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ── ROOT VARIABLES ──────────────────────────────────────────────────────── */
:root {
  /* Backgrounds */
  --bg0: #F2F4F8;
  --bg1: #EBEEf5;
  --bg2: #FFFFFF;
  --bg3: #F7F9FD;
  --bg4: #EDF0F7;
  --bg5: #E4E8F2;

  /* Borders */
  --bdr:  #DDE3EF;
  --bdr2: #C8D0E4;
  --bdr3: #A8B4D0;

  /* Text */
  --t1: #0F172A;
  --t2: #2D3A52;
  --t3: #5A6A88;
  --t4: #8896B0;

  /* Brand */
  --blue:       #1D4ED8;
  --blue-mid:   #2563EB;
  --blue-light: #EFF6FF;
  --blue-bdr:   #BFDBFE;

  /* Status */
  --green:      #15803D;
  --green-bg:   #F0FDF4;
  --red:        #DC2626;
  --red-bg:     #FFF0F0;
  --gold:       #D97706;
  --gold-bg:    #FFFBEB;
  --purple:     #6D28D9;
  --teal:       #0E7490;
  --orange:     #EA580C;

  /* Shadows */
  --shadow-sm:  0 1px 2px rgba(15,23,42,.06);
  --shadow:     0 1px 4px rgba(15,23,42,.08), 0 1px 2px rgba(15,23,42,.04);
  --shadow-md:  0 4px 8px rgba(15,23,42,.08), 0 2px 4px rgba(15,23,42,.04);
}

/* ── GLOBAL RESET ────────────────────────────────────────────────────────── */
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }

.stApp                               { background: var(--bg0) !important; }
.main .block-container               { padding: 1rem 1.5rem 3rem; max-width: 100% !important; }
[data-testid="stSidebar"]            { background: var(--bg2) !important; border-right: 1px solid var(--bdr) !important; box-shadow: var(--shadow); }
[data-testid="stSidebar"]>div:first-child { background: var(--bg2) !important; }
[data-testid="stHeader"]             { background: var(--bg2) !important; border-bottom: 1px solid var(--bdr) !important; }

/* ── TYPOGRAPHY ──────────────────────────────────────────────────────────── */
h1, h2, h3, h4          { color: var(--t1) !important; font-family: 'DM Sans', sans-serif !important; font-weight: 600 !important; }
p, li, span             { font-family: 'DM Sans', sans-serif; color: var(--t2); }
.stMarkdown p           { color: var(--t2) !important; line-height: 1.6; }
code, pre               { font-family: 'JetBrains Mono', monospace !important; background: var(--bg4) !important; color: var(--t1) !important; border-radius: 4px; }
[data-testid="stMetricValue"]   { font-family: 'JetBrains Mono', monospace !important; color: var(--t1) !important; font-size: 1.15rem !important; font-weight: 600 !important; }
[data-testid="stMetricLabel"]   { color: var(--t3) !important; font-size: .78rem !important; font-weight: 500 !important; letter-spacing: .3px; text-transform: uppercase; }
[data-testid="stMetricDelta"]   { font-size: .82rem !important; font-weight: 500 !important; }
[data-testid="stMetricDelta"][data-direction="up"]   { color: var(--green) !important; }
[data-testid="stMetricDelta"][data-direction="down"] { color: var(--red) !important; }

/* ── TABS ────────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"]     { background: var(--bg2) !important; border-bottom: 2px solid var(--bdr) !important; gap: 0; }
.stTabs [data-baseweb="tab"]          { color: var(--t3) !important; font-weight: 500 !important; font-family: 'DM Sans', sans-serif !important; padding: 10px 18px !important; border-radius: 0 !important; border-bottom: 2px solid transparent !important; transition: all .18s; font-size: .88rem !important; }
.stTabs [data-baseweb="tab"]:hover    { color: var(--t1) !important; background: var(--bg3) !important; }
.stTabs [aria-selected="true"]        { color: var(--blue) !important; border-bottom: 2px solid var(--blue) !important; background: var(--blue-light) !important; font-weight: 600 !important; }

/* ── BUTTONS ─────────────────────────────────────────────────────────────── */
.stButton > button {
  background: var(--bg2) !important;
  border: 1px solid var(--bdr2) !important;
  color: var(--t2) !important;
  border-radius: 7px !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: .85rem !important;
  font-weight: 500 !important;
  transition: all .15s !important;
  padding: 6px 16px !important;
  box-shadow: var(--shadow-sm) !important;
}
.stButton > button:hover   { background: var(--bg4) !important; border-color: var(--blue-mid) !important; color: var(--blue) !important; box-shadow: var(--shadow) !important; }
.stButton > button:active  { transform: translateY(1px); }
.stButton > button[kind="primary"] {
  background: var(--blue) !important;
  border-color: var(--blue) !important;
  color: #FFFFFF !important;
  font-weight: 600 !important;
}
.stButton > button[kind="primary"]:hover { background: #1E40AF !important; border-color: #1E40AF !important; }

/* ── INPUTS ──────────────────────────────────────────────────────────────── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
  background: var(--bg2) !important;
  border: 1px solid var(--bdr2) !important;
  color: var(--t1) !important;
  border-radius: 7px !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: .88rem !important;
  box-shadow: var(--shadow-sm) !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
  border-color: var(--blue-mid) !important;
  box-shadow: 0 0 0 3px rgba(37,99,235,.12) !important;
}
.stSelectbox > div > div       { background: var(--bg2) !important; border: 1px solid var(--bdr2) !important; border-radius: 7px !important; color: var(--t1) !important; box-shadow: var(--shadow-sm) !important; }
.stMultiSelect > div > div     { background: var(--bg2) !important; border: 1px solid var(--bdr2) !important; border-radius: 7px !important; box-shadow: var(--shadow-sm) !important; }
.stTextInput label, .stSelectbox label, .stNumberInput label, .stMultiSelect label {
  color: var(--t3) !important;
  font-size: .78rem !important;
  font-weight: 600 !important;
  letter-spacing: .4px;
  text-transform: uppercase;
}

/* ── EXPANDERS ───────────────────────────────────────────────────────────── */
.streamlit-expanderHeader         { background: var(--bg3) !important; color: var(--t2) !important; border-radius: 8px !important; border: 1px solid var(--bdr) !important; font-weight: 500 !important; }
.streamlit-expanderContent        { background: var(--bg2) !important; border: 1px solid var(--bdr) !important; border-radius: 0 0 8px 8px !important; }

/* ── DATAFRAME ───────────────────────────────────────────────────────────── */
.stDataFrame                      { border: 1px solid var(--bdr) !important; border-radius: 8px !important; overflow: hidden; box-shadow: var(--shadow-sm) !important; }
.stDataFrame thead th             { background: var(--bg4) !important; color: var(--t3) !important; font-size: .73rem !important; font-weight: 700 !important; letter-spacing: .6px; text-transform: uppercase; border-bottom: 2px solid var(--bdr2) !important; }
.stDataFrame tbody td             { color: var(--t1) !important; font-size: .82rem !important; font-family: 'JetBrains Mono', monospace !important; border-bottom: 1px solid var(--bdr) !important; }
.stDataFrame tbody tr:hover td    { background: var(--blue-light) !important; }

/* ── CHECKBOXES & SLIDERS ────────────────────────────────────────────────── */
.stCheckbox span                  { color: var(--t2) !important; font-size: .85rem !important; font-weight: 400 !important; }
.stSlider > div > div > div       { background: var(--blue) !important; }

/* ── PROGRESS ────────────────────────────────────────────────────────────── */
.stProgress > div > div           { background: var(--blue) !important; border-radius: 4px; }
.stProgress                       { background: var(--bg5) !important; border-radius: 4px; }

/* ── ALERTS ──────────────────────────────────────────────────────────────── */
.stSuccess    { background: var(--green-bg) !important; border: 1px solid #86EFAC !important; color: var(--green) !important; border-radius: 8px !important; }
.stWarning    { background: var(--gold-bg) !important;  border: 1px solid #FCD34D !important; border-radius: 8px !important; }
.stError      { background: var(--red-bg) !important;   border: 1px solid #FCA5A5 !important; border-radius: 8px !important; }
.stInfo       { background: var(--blue-light) !important; border: 1px solid var(--blue-bdr) !important; border-radius: 8px !important; }

/* ── SIDEBAR NAV ─────────────────────────────────────────────────────────── */
[data-testid="stSidebarNav"]      { padding-top: 4px; }
[data-testid="stSidebarNav"] a    { color: var(--t3) !important; border-radius: 7px; padding: 8px 12px !important; margin: 1px 4px; display: block; transition: all .15s; font-size: .86rem !important; font-weight: 500 !important; }
[data-testid="stSidebarNav"] a:hover { background: var(--bg4) !important; color: var(--t1) !important; }
[data-testid="stSidebarNav"] a[aria-current="page"] { background: var(--blue-light) !important; color: var(--blue) !important; border-left: 3px solid var(--blue); font-weight: 600 !important; }

/* ── REUSABLE COMPONENTS ─────────────────────────────────────────────────── */
.ks-section-label {
  color: var(--t4);
  font-size: .7rem;
  font-weight: 700;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 18px 0 10px;
}
.ks-section-label::after { content: ''; flex: 1; height: 1px; background: var(--bdr); }

.ks-card {
  background: var(--bg2);
  border: 1px solid var(--bdr);
  border-radius: 10px;
  padding: 14px 18px;
  box-shadow: var(--shadow-sm);
  transition: box-shadow .18s, border-color .18s;
}
.ks-card:hover { box-shadow: var(--shadow); border-color: var(--bdr2); }

.ks-stat-card {
  background: var(--bg2);
  border: 1px solid var(--bdr);
  border-radius: 8px;
  padding: 12px 14px;
  box-shadow: var(--shadow-sm);
}

.ks-badge-blue   { background: var(--blue-light); color: var(--blue);  border: 1px solid var(--blue-bdr); border-radius: 20px; padding: 2px 10px; font-size: .72rem; font-weight: 600; letter-spacing: .3px; }
.ks-badge-green  { background: var(--green-bg);   color: var(--green); border: 1px solid #86EFAC;         border-radius: 20px; padding: 2px 10px; font-size: .72rem; font-weight: 600; }
.ks-badge-red    { background: var(--red-bg);     color: var(--red);   border: 1px solid #FCA5A5;         border-radius: 20px; padding: 2px 10px; font-size: .72rem; font-weight: 600; }
.ks-badge-gold   { background: var(--gold-bg);    color: var(--gold);  border: 1px solid #FCD34D;         border-radius: 20px; padding: 2px 10px; font-size: .72rem; font-weight: 600; }

.ks-mono  { font-family: 'JetBrains Mono', monospace; }

.pos  { color: var(--green) !important; font-weight: 500; }
.neg  { color: var(--red)   !important; font-weight: 500; }
.neut { color: var(--gold)  !important; font-weight: 500; }

/* Live indicator (green dot pulsing) */
.live-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: var(--green-bg);
  border: 1px solid #86EFAC;
  color: var(--green);
  padding: 2px 10px;
  border-radius: 20px;
  font-size: .7rem;
  font-weight: 700;
  letter-spacing: .8px;
  text-transform: uppercase;
}
.live-dot {
  width: 6px;
  height: 6px;
  background: var(--green);
  border-radius: 50%;
  animation: pulse 1.6s infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: .4; transform: scale(.85); }
}

/* ── SCROLLBAR ───────────────────────────────────────────────────────────── */
::-webkit-scrollbar            { width: 5px; height: 5px; }
::-webkit-scrollbar-track      { background: var(--bg4); }
::-webkit-scrollbar-thumb      { background: var(--bdr2); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover{ background: var(--blue-mid); }

/* ── MOBILE RESPONSIVE ───────────────────────────────────────────────────── */
@media (max-width: 768px) {
  .main .block-container             { padding: 0.5rem 0.75rem 2rem !important; }
  h1                                 { font-size: 1.3rem !important; }
  h2                                 { font-size: 1.1rem !important; }
  h3                                 { font-size: 1rem !important; }
  .ks-card                           { padding: 10px 12px; }
  .stTabs [data-baseweb="tab"]       { padding: 8px 10px !important; font-size: .8rem !important; }
  [data-testid="stMetricValue"]      { font-size: .95rem !important; }
  .stDataFrame tbody td              { font-size: .75rem !important; }
}

@media (max-width: 480px) {
  .main .block-container             { padding: 0.25rem 0.5rem 1.5rem !important; }
  .ks-section-label                  { font-size: .65rem; letter-spacing: 1px; }
  .stButton > button                 { font-size: .78rem !important; padding: 5px 10px !important; }
}

/* ── PAGE-WIDE OVERRIDE (pages don't call inject_css — this catches all) ── */
.stApp .stMarkdown a { color: var(--blue) !important; }
.stApp .stMarkdown a:hover { color: #1E40AF !important; }
</style>
"""


def inject_css():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def section_label(text: str):
    st.markdown(f'<div class="ks-section-label">{text}</div>', unsafe_allow_html=True)


def pos_neg_color(val, positive_good: bool = True) -> str:
    """Return CSS color string based on sign."""
    if val is None:
        return "var(--t4)"
    try:
        f = float(val)
        if f > 0: return "var(--green)" if positive_good else "var(--red)"
        if f < 0: return "var(--red)"   if positive_good else "var(--green)"
        return "var(--t3)"
    except Exception:
        return "var(--t3)"


def format_inr(val) -> str:
    """Format a number as Indian currency string."""
    if val is None:
        return "—"
    try:
        f = float(val)
        if f >= 1e7:  return f"₹{f/1e7:.2f} Cr"
        if f >= 1e5:  return f"₹{f/1e5:.2f} L"
        return f"₹{f:,.2f}"
    except Exception:
        return str(val)


def fmt_pct(val, decimals: int = 2) -> str:
    """Format a ratio (0–1) as percentage string."""
    if val is None:
        return "—"
    try:
        return f"{float(val) * 100:.{decimals}f}%"
    except Exception:
        return "—"


def fmt_num(val, decimals: int = 2) -> str:
    if val is None:
        return "—"
    try:
        return f"{float(val):,.{decimals}f}"
    except Exception:
        return "—"


# ─── PLOTLY THEME: LIGHT ─────────────────────────────────────────────────────

PLOTLY_LAYOUT = dict(
    paper_bgcolor="#FFFFFF",
    plot_bgcolor="#F7F9FD",
    font=dict(color="#5A6A88", family="DM Sans, sans-serif", size=11),
    legend=dict(
        bgcolor="rgba(255,255,255,0.95)",
        bordercolor="#DDE3EF",
        borderwidth=1,
        font=dict(size=10, color="#2D3A52"),
    ),
    xaxis=dict(
        showgrid=True,
        gridcolor="#EAEEf8",
        gridwidth=1,
        zeroline=False,
        linecolor="#DDE3EF",
        linewidth=1,
        color="#5A6A88",
        tickfont=dict(size=10),
    ),
    yaxis=dict(
        showgrid=True,
        gridcolor="#EAEEf8",
        gridwidth=1,
        zeroline=False,
        linecolor="#DDE3EF",
        linewidth=1,
        color="#5A6A88",
        side="right",
        tickfont=dict(size=10),
    ),
    hovermode="x unified",
    xaxis_rangeslider_visible=False,
    margin=dict(l=8, r=8, t=32, b=8),
    hoverlabel=dict(
        bgcolor="#FFFFFF",
        bordercolor="#DDE3EF",
        font=dict(size=11, color="#0F172A", family="JetBrains Mono, monospace"),
    ),
)

# Colors for multi-series charts (professional, accessible)
CHART_COLORS = [
    "#1D4ED8",  # Blue (primary)
    "#16A34A",  # Green
    "#DC2626",  # Red
    "#7C3AED",  # Purple
    "#EA580C",  # Orange
    "#0E7490",  # Teal
    "#BE185D",  # Pink
    "#15803D",  # Dark green
    "#1E40AF",  # Dark blue
    "#D97706",  # Amber
    "#065F46",  # Deep teal
    "#9D174D",  # Deep pink
    "#92400E",  # Brown
    "#1E3A5F",  # Navy
    "#4C1D95",  # Deep purple
]

# Candlestick colors
CANDLE_UP   = "#16A34A"
CANDLE_DOWN = "#DC2626"
CANDLE_UP_FILL   = "rgba(22,163,74,0.8)"
CANDLE_DOWN_FILL = "rgba(220,38,38,0.8)"
