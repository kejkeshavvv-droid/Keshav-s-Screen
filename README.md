# 📊 Kejriwal's Screen — Indian Market Terminal

> Real-time NSE/BSE stock screener, charting platform, and quantitative analytics terminal
> built entirely in Python/Streamlit.

---

## ✨ Feature Overview

| Module | What's inside |
|--------|---------------|
| **🏠 Home** | Live index banner (8 indices) · NIFTY 50 intraday chart · Top gainers/losers · Sector heatmap bar chart · Market news feed |
| **📊 Screener** | AI natural-language prompt (Claude-powered) · 30+ manual fundamental filters · 12 preset screens · Technical filters (RSI, MACD, SMA, Supertrend) · CSV export · Add-to-Bucket |
| **📈 Charts** | Candlestick / Heikin-Ashi / Line / Area / OHLC · 50+ indicator overlays (SMA, EMA, HMA, VWAP, BB, Keltner, Donchian, Ichimoku, Supertrend, PSAR) · 15 sub-panels (RSI, MACD, ADX/DMI, Stochastic, Williams %R, CCI, ROC, MFI, TSI, OBV, CMF, ATR, HV, Aroon, Volume) · Pivot Points (Standard / Fibonacci / Camarilla) · Fibonacci Retracement · Support & Resistance · 13 Candlestick patterns · Signal summary (Buy/Sell/Neutral) · Fundamentals + News tab |
| **🪣 Bucket** | Live snapshot cards · Normalised performance chart vs NIFTY benchmark · Fundamental comparison table · Radar chart · Pearson/Spearman/Kendall correlation matrix · Rolling correlation · Risk dashboard (Sharpe, Sortino, Max DD, VaR 95%, CVaR, Beta, Skewness, Kurtosis) · Risk-Return scatter · Drawdown chart |
| **🌡️ Heatmap** | Grid heatmap (color-coded by 1D change) · Plotly Treemap with sector grouping · Sector drill-down with index chart + constituent performance · Inter-index correlation matrix |
| **🔬 Algo Lab** | **Backtester** — 9 strategies (SMA/EMA Crossover, RSI MR, MACD Cross, Bollinger Band Bounce, Supertrend, Golden Cross, RSI+MACD Combo, Dual EMA+ATR Stop) with equity curve, drawdown, signal chart, metrics vs Buy & Hold · **Time Series** — Return distribution, Q-Q plot, 10 descriptive stats, rolling return/vol/Sharpe, ACF/PACF · **Statistics** — Calendar year returns, monthly returns heatmap · **Regression** — Price vs Time (polynomial), Beta vs NIFTY 50, Lag regression · **Hypothesis Tests** — Shapiro-Wilk, Jarque-Bera, D'Agostino, ADF, KPSS, t-test, Runs test, Ljung-Box, Welch, Mann-Whitney, Levene, KS (two-sample) · **Monte Carlo** — GBM + Bootstrap, configurable simulations, confidence bands, final value distribution |
| **📰 Indices** | 24 NSE/BSE indices · Full performance summary table (1D/1W/1M/3M/6M/1Y/Vol/MaxDD) · Deep-dive chart with TA overlays · Multi-index comparison · All-indices snapshot table · Index constituents with grid heatmap |

---

## 🛠️ Tech Stack

- **Python 3.10+**
- **Streamlit** — UI framework
- **yfinance** — Real-time NSE/BSE market data
- **Plotly** — Interactive charts
- **pandas / numpy** — Data processing
- **scipy / statsmodels** — Statistical tests
- **anthropic** — AI-powered screener (optional)

---

## 📂 Project Structure

```
kejriwal_screen/
├── app.py                      ← Home dashboard (entry point)
├── requirements.txt
├── .streamlit/
│   └── config.toml             ← Dark terminal theme
├── pages/
│   ├── 1_📊_Screener.py
│   ├── 2_📈_Charts.py
│   ├── 3_🪣_Bucket.py
│   ├── 4_🌡️_Heatmap.py
│   ├── 5_🔬_Algo_Lab.py
│   └── 6_📰_Indices.py
└── utils/
    ├── __init__.py
    ├── styles.py               ← Shared CSS + Plotly theme
    ├── nse_stocks.py           ← 194 stocks, 24 indices, sector metadata
    ├── data_fetcher.py         ← yfinance wrappers with smart caching
    ├── technical_analysis.py  ← All TA indicators built from scratch
    └── screener_engine.py      ← AI + rule-based query parser
```

---

## 🚀 DEPLOYMENT GUIDE

### Option 1 — Local (Fastest, 3 minutes)

```bash
# 1. Clone / unzip the project
cd kejriwal_screen

# 2. Create a virtual environment
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the terminal
streamlit run app.py
```

Open your browser at **http://localhost:8501**

---

### Option 2 — Streamlit Community Cloud (Free, public URL)

1. Push this folder to a **GitHub repository** (public or private)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **New app** → select your repo
4. Set **Main file path** to `app.py`
5. Click **Deploy**

Your app gets a permanent public URL like `https://yourname-kejriwal-screen.streamlit.app`

**Add API key as a secret (Settings → Secrets):**
```toml
ANTHROPIC_API_KEY = "sk-ant-..."
```

Then in `utils/screener_engine.py`, replace `api_key` with:
```python
import streamlit as st
api_key = st.secrets.get("ANTHROPIC_API_KEY", api_key)
```

---

### Option 3 — Docker (Production)

**`Dockerfile`** (already included below):
```bash
# Build
docker build -t kejriwal-screen .

# Run
docker run -p 8501:8501 kejriwal-screen

# With API key
docker run -p 8501:8501 -e ANTHROPIC_API_KEY=sk-ant-... kejriwal-screen
```

---

### Option 4 — AWS EC2 / GCP VM / DigitalOcean

```bash
# On a fresh Ubuntu 22.04 server:

# 1. Install Python & pip
sudo apt update && sudo apt install -y python3-pip python3-venv nginx

# 2. Clone your repo
git clone https://github.com/YOU/kejriwal-screen.git
cd kejriwal-screen

# 3. Setup venv
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 4. Run with screen/tmux (persistent)
screen -S kejriwal
streamlit run app.py --server.port 8501 --server.address 0.0.0.0

# 5. Configure Nginx reverse proxy (port 80 → 8501)
sudo nano /etc/nginx/sites-available/kejriwal
```

Nginx config:
```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;
    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/kejriwal /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx
```

---

### Option 5 — Heroku

```bash
# Install Heroku CLI, then:
heroku create kejriwal-screen
heroku config:set ANTHROPIC_API_KEY=sk-ant-...
git push heroku main
heroku open
```

`Procfile` (included):
```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

---

## ⚙️ Configuration

### Anthropic API Key (Optional — for AI screening)
Set in the app's **Settings tab**, or as an environment variable:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
streamlit run app.py
```

Without the key, the screener falls back to the built-in rule-based parser (handles ~80% of queries).

### Performance Tuning
Edit `.streamlit/config.toml`:
```toml
[server]
maxUploadSize = 50

[runner]
fastReruns = true        # Faster UI updates

[browser]
gatherUsageStats = false
```

---

## 📈 Usage Guide

### AI Screener Prompts (Examples)
```
RSI below 30
PE below 15 and ROE above 20%
Large cap IT stocks with earnings growth above 25%
Oversold pharma stocks near 52-week low
Debt-free mid cap stocks with dividend yield above 3%
MACD bullish crossover, above SMA 200
High dividend yield PSU stocks with PE below 10
```

### Bucket Workflow
1. Run a screen → click **Add All to Bucket**
2. Navigate to **🪣 Bucket** for detailed comparison
3. Check **Correlation Matrix** tab to identify diversification
4. Use **Risk & Volatility** tab for portfolio risk metrics

### Algo Lab Workflow
1. Select a stock from the top picker
2. Go to **🚀 Backtest** → choose a strategy → **▶ Run Backtest**
3. Use **📈 Time Series** to understand return distribution
4. Run **🧪 Hypothesis Tests** to check for market efficiency
5. Use **🎲 Monte Carlo** for price forecasting scenarios

---

## 📦 requirements.txt

```
streamlit>=1.32.0
yfinance>=0.2.36
pandas>=2.0.0
numpy>=1.24.0
plotly>=5.18.0
scipy>=1.11.0
statsmodels>=0.14.0
anthropic>=0.20.0
requests>=2.31.0
scikit-learn>=1.3.0
ta>=0.10.0
pytz>=2023.3
```

---

## 📜 License

MIT License — free to use, modify, and distribute.

---

*Built with ❤️ — Kejriwal's Screen v1.0*
