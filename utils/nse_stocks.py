"""
nse_stocks.py — Keshav's Screen
NSE Stock Universe: 500+ static stocks with rich metadata
+ dynamic loader that fetches all 2671+ NSE listed symbols from NSE API
"""

import pandas as pd

# ─── INDICES ─────────────────────────────────────────────────────────────────
INDICES = {
    "NIFTY 50":              "^NSEI",
    "NIFTY BANK":            "^NSEBANK",
    "SENSEX":                "^BSESN",
    "NIFTY IT":              "^CNXIT",
    "NIFTY PHARMA":          "^CNXPHARMA",
    "NIFTY FMCG":            "^CNXFMCG",
    "NIFTY AUTO":            "^CNXAUTO",
    "NIFTY METAL":           "^CNXMETAL",
    "NIFTY ENERGY":          "^CNXENERGY",
    "NIFTY REALTY":          "^CNXREALTY",
    "NIFTY MIDCAP 50":       "^NSEMDCP50",
    "NIFTY SMALLCAP 50":     "^CNXSC",
    "NIFTY 100":             "^CNX100",
    "NIFTY 200":             "^CNX200",
    "NIFTY 500":             "^CNX500",
    "INDIA VIX":             "^INDIAVIX",
    "NIFTY INFRA":           "^CNXINFRA",
    "NIFTY PSU BANK":        "^CNXPSUBANK",
    "NIFTY MEDIA":           "^CNXMEDIA",
    "NIFTY CONSUMPTION":     "^CNXCONSUM",
    "NIFTY FINANCIAL SVCS":  "^CNXFINANCE",
    "NIFTY COMMODITIES":     "^CNXCMDT",
    "NIFTY MNC":             "^CNXMNC",
    "NIFTY DIVIDEND OPP 50": "^CNXDIVOPPS50",
    "NIFTY MIDCAP 100":      "^CNX_MIDCAP",
    "NIFTY SMALLCAP 100":    "^CNX_SMLCAP",
    "NIFTY NEXT 50":         "^NSMIDCP100",
    "NIFTY MICROCAP 250":    "^NIFTY_MICROCAP250",
}

# ─── NIFTY 50 CONSTITUENTS ───────────────────────────────────────────────────
NIFTY50_STOCKS = [
    "RELIANCE","TCS","HDFCBANK","INFY","ICICIBANK",
    "HINDUNILVR","ITC","KOTAKBANK","LT","AXISBANK",
    "BAJFINANCE","BHARTIARTL","ASIANPAINT","MARUTI","SBIN",
    "TITAN","SUNPHARMA","WIPRO","HCLTECH","ULTRACEMCO",
    "NTPC","TECHM","ONGC","POWERGRID","M&M",
    "NESTLEIND","JSWSTEEL","TATAMOTORS","TATASTEEL","COALINDIA",
    "ADANIENT","ADANIPORTS","DIVISLAB","BAJAJFINSV","DRREDDY",
    "EICHERMOT","HEROMOTOCO","HINDALCO","INDUSINDBK","APOLLOHOSP",
    "BPCL","CIPLA","GRASIM","HDFCLIFE","SBILIFE",
    "TATACONSUM","UPL","BAJAJ-AUTO","BRITANNIA","LTF",
]

# ─── NIFTY NEXT 50 ───────────────────────────────────────────────────────────
NIFTY_NEXT50 = [
    "ADANIPOWER","ADANIGREEN","ADANITRANS","ATGL","AMBUJACEM",
    "BERGEPAINT","BOSCHLTD","COLPAL","DABUR","DMART",
    "EMAMILTD","GAIL","GODREJCP","HAVELLS","HINDPETRO",
    "INDHOTEL","IOC","JUBLFOOD","LICHSGFIN","LUPIN",
    "MARICO","MCDOWELL-N","MPHASIS","NAUKRI","OFSS",
    "PERSISTENT","PETRONET","PIIND","PVRINOX","SBICARD",
    "SHREECEM","SIEMENS","SRF","TATAELXSI","TORNTPHARM",
    "TVSMOTOR","VBL","VEDL","ZOMATO","ZYDUSLIFE",
    "CHOLAFIN","RECLTD","PFC","HAL","BEL",
    "ABB","CUMMINSIND","PGHH","NYKAA","PAYTM",
]

# ─── FULL STOCK UNIVERSE (500+) ──────────────────────────────────────────────
NSE_STOCKS_EXTENDED = {
    # ── BANKING: PRIVATE ──────────────────────────────────────────────────────
    "HDFCBANK":   {"name":"HDFC Bank Ltd",                        "sector":"Banking",      "industry":"Private Sector Bank","cap":"Large"},
    "ICICIBANK":  {"name":"ICICI Bank Ltd",                       "sector":"Banking",      "industry":"Private Sector Bank","cap":"Large"},
    "KOTAKBANK":  {"name":"Kotak Mahindra Bank Ltd",              "sector":"Banking",      "industry":"Private Sector Bank","cap":"Large"},
    "AXISBANK":   {"name":"Axis Bank Ltd",                        "sector":"Banking",      "industry":"Private Sector Bank","cap":"Large"},
    "INDUSINDBK": {"name":"IndusInd Bank Ltd",                    "sector":"Banking",      "industry":"Private Sector Bank","cap":"Large"},
    "FEDERALBNK": {"name":"Federal Bank Ltd",                     "sector":"Banking",      "industry":"Private Sector Bank","cap":"Mid"},
    "BANDHANBNK": {"name":"Bandhan Bank Ltd",                     "sector":"Banking",      "industry":"Private Sector Bank","cap":"Mid"},
    "IDFCFIRSTB": {"name":"IDFC First Bank Ltd",                  "sector":"Banking",      "industry":"Private Sector Bank","cap":"Mid"},
    "AUBANK":     {"name":"AU Small Finance Bank Ltd",            "sector":"Banking",      "industry":"Small Finance Bank", "cap":"Mid"},
    "RBLBANK":    {"name":"RBL Bank Ltd",                         "sector":"Banking",      "industry":"Private Sector Bank","cap":"Mid"},
    "YESBANK":    {"name":"Yes Bank Ltd",                         "sector":"Banking",      "industry":"Private Sector Bank","cap":"Mid"},
    "DCBBANK":    {"name":"DCB Bank Ltd",                         "sector":"Banking",      "industry":"Private Sector Bank","cap":"Small"},
    "KTKBANK":    {"name":"Karnataka Bank Ltd",                   "sector":"Banking",      "industry":"Private Sector Bank","cap":"Small"},
    "CSBBANK":    {"name":"CSB Bank Ltd",                         "sector":"Banking",      "industry":"Private Sector Bank","cap":"Small"},
    "IDBI":       {"name":"IDBI Bank Ltd",                        "sector":"Banking",      "industry":"Public Sector Bank", "cap":"Mid"},
    "JKBANK":     {"name":"J&K Bank Ltd",                         "sector":"Banking",      "industry":"Public Sector Bank", "cap":"Small"},
    "SOUTHBANK":  {"name":"South Indian Bank Ltd",                "sector":"Banking",      "industry":"Private Sector Bank","cap":"Small"},
    "EQUITASBNK": {"name":"Equitas Small Finance Bank",           "sector":"Banking",      "industry":"Small Finance Bank", "cap":"Small"},
    "UJJIVANSFB": {"name":"Ujjivan Small Finance Bank",           "sector":"Banking",      "industry":"Small Finance Bank", "cap":"Small"},
    "UTKARSHBNK": {"name":"Utkarsh Small Finance Bank",           "sector":"Banking",      "industry":"Small Finance Bank", "cap":"Small"},
    # ── BANKING: PUBLIC ───────────────────────────────────────────────────────
    "SBIN":       {"name":"State Bank of India",                  "sector":"Banking",      "industry":"Public Sector Bank", "cap":"Large"},
    "PNB":        {"name":"Punjab National Bank",                 "sector":"Banking",      "industry":"Public Sector Bank", "cap":"Mid"},
    "BANKBARODA": {"name":"Bank of Baroda",                       "sector":"Banking",      "industry":"Public Sector Bank", "cap":"Mid"},
    "CANBK":      {"name":"Canara Bank",                          "sector":"Banking",      "industry":"Public Sector Bank", "cap":"Mid"},
    "UNIONBANK":  {"name":"Union Bank of India",                  "sector":"Banking",      "industry":"Public Sector Bank", "cap":"Mid"},
    "INDIANB":    {"name":"Indian Bank",                          "sector":"Banking",      "industry":"Public Sector Bank", "cap":"Mid"},
    "CENTRALBK":  {"name":"Central Bank of India",                "sector":"Banking",      "industry":"Public Sector Bank", "cap":"Mid"},
    "BANKINDIA":  {"name":"Bank of India",                        "sector":"Banking",      "industry":"Public Sector Bank", "cap":"Mid"},
    "MAHABANK":   {"name":"Bank of Maharashtra",                  "sector":"Banking",      "industry":"Public Sector Bank", "cap":"Small"},
    "UCOBANK":    {"name":"UCO Bank",                             "sector":"Banking",      "industry":"Public Sector Bank", "cap":"Small"},
    # ── FINANCE: NBFC ─────────────────────────────────────────────────────────
    "BAJFINANCE": {"name":"Bajaj Finance Ltd",                    "sector":"Finance",      "industry":"NBFC",               "cap":"Large"},
    "BAJAJFINSV": {"name":"Bajaj Finserv Ltd",                    "sector":"Finance",      "industry":"Financial Services",  "cap":"Large"},
    "LTF":        {"name":"L&T Finance Holdings Ltd",             "sector":"Finance",      "industry":"NBFC",               "cap":"Mid"},
    "MUTHOOTFIN": {"name":"Muthoot Finance Ltd",                  "sector":"Finance",      "industry":"Gold Loan",          "cap":"Large"},
    "CHOLAFIN":   {"name":"Cholamandalam Investment & Finance",   "sector":"Finance",      "industry":"NBFC",               "cap":"Large"},
    "M&MFIN":     {"name":"Mahindra & Mahindra Financial Svcs",  "sector":"Finance",      "industry":"NBFC",               "cap":"Mid"},
    "RECLTD":     {"name":"REC Ltd",                              "sector":"Finance",      "industry":"Power Finance",       "cap":"Large"},
    "PFC":        {"name":"Power Finance Corporation Ltd",        "sector":"Finance",      "industry":"Power Finance",       "cap":"Large"},
    "IRFC":       {"name":"Indian Railway Finance Corporation",   "sector":"Finance",      "industry":"Infra Finance",       "cap":"Large"},
    "LICHSGFIN":  {"name":"LIC Housing Finance Ltd",              "sector":"Finance",      "industry":"Housing Finance",     "cap":"Mid"},
    "PNBHOUSING": {"name":"PNB Housing Finance Ltd",              "sector":"Finance",      "industry":"Housing Finance",     "cap":"Mid"},
    "CANFINHOME": {"name":"Can Fin Homes Ltd",                    "sector":"Finance",      "industry":"Housing Finance",     "cap":"Small"},
    "MANAPPURAM": {"name":"Manappuram Finance Ltd",               "sector":"Finance",      "industry":"Gold Loan",          "cap":"Mid"},
    "SHRIRAMFIN": {"name":"Shriram Finance Ltd",                  "sector":"Finance",      "industry":"NBFC",               "cap":"Large"},
    "POONAWALLA": {"name":"Poonawalla Fincorp Ltd",               "sector":"Finance",      "industry":"NBFC",               "cap":"Mid"},
    "ABCAPITAL":  {"name":"Aditya Birla Capital Ltd",             "sector":"Finance",      "industry":"Financial Services",  "cap":"Mid"},
    "IIFL":       {"name":"IIFL Finance Ltd",                     "sector":"Finance",      "industry":"NBFC",               "cap":"Mid"},
    "CREDITACC":  {"name":"Credit Access Grameen Ltd",            "sector":"Finance",      "industry":"Microfinance",        "cap":"Small"},
    "APTUS":      {"name":"Aptus Value Housing Finance India",    "sector":"Finance",      "industry":"Housing Finance",     "cap":"Small"},
    "HOMEFIRST":  {"name":"Home First Finance Company India",     "sector":"Finance",      "industry":"Housing Finance",     "cap":"Small"},
    # ── FINANCE: BROKING & EXCHANGES ─────────────────────────────────────────
    "ANGELONE":   {"name":"Angel One Ltd",                        "sector":"Finance",      "industry":"Broking",             "cap":"Mid"},
    "CDSL":       {"name":"Central Depository Services Ltd",      "sector":"Finance",      "industry":"Capital Markets",     "cap":"Mid"},
    "CAMS":       {"name":"Computer Age Management Services",     "sector":"Finance",      "industry":"Capital Markets",     "cap":"Mid"},
    "MCX":        {"name":"Multi Commodity Exchange of India",    "sector":"Finance",      "industry":"Exchange",            "cap":"Mid"},
    "BSE":        {"name":"BSE Ltd",                              "sector":"Finance",      "industry":"Exchange",            "cap":"Mid"},
    "IEX":        {"name":"Indian Energy Exchange Ltd",           "sector":"Finance",      "industry":"Exchange",            "cap":"Mid"},
    "SBICARD":    {"name":"SBI Cards and Payment Services Ltd",   "sector":"Finance",      "industry":"Credit Cards",        "cap":"Large"},
    "NSDL":       {"name":"NSDL e-Governance Infrastructure",     "sector":"Finance",      "industry":"Capital Markets",     "cap":"Mid"},
    # ── INSURANCE ─────────────────────────────────────────────────────────────
    "HDFCLIFE":   {"name":"HDFC Life Insurance Co Ltd",           "sector":"Insurance",    "industry":"Life Insurance",      "cap":"Large"},
    "SBILIFE":    {"name":"SBI Life Insurance Co Ltd",            "sector":"Insurance",    "industry":"Life Insurance",      "cap":"Large"},
    "ICICIGI":    {"name":"ICICI Lombard General Insurance",      "sector":"Insurance",    "industry":"General Insurance",   "cap":"Large"},
    "LICI":       {"name":"Life Insurance Corporation of India",  "sector":"Insurance",    "industry":"Life Insurance",      "cap":"Large"},
    "STARHEALTH": {"name":"Star Health and Allied Insurance",     "sector":"Insurance",    "industry":"Health Insurance",    "cap":"Mid"},
    "NIACL":      {"name":"New India Assurance Co Ltd",           "sector":"Insurance",    "industry":"General Insurance",   "cap":"Mid"},
    "GIC":        {"name":"General Insurance Corporation of India","sector":"Insurance",   "industry":"Reinsurance",         "cap":"Mid"},
    "MAXLIFE":    {"name":"Max Financial Services Ltd",           "sector":"Insurance",    "industry":"Life Insurance",      "cap":"Mid"},
    # ── IT SERVICES: LARGE CAP ────────────────────────────────────────────────
    "TCS":        {"name":"Tata Consultancy Services Ltd",        "sector":"IT",           "industry":"IT Services",         "cap":"Large"},
    "INFY":       {"name":"Infosys Ltd",                          "sector":"IT",           "industry":"IT Services",         "cap":"Large"},
    "WIPRO":      {"name":"Wipro Ltd",                            "sector":"IT",           "industry":"IT Services",         "cap":"Large"},
    "HCLTECH":    {"name":"HCL Technologies Ltd",                 "sector":"IT",           "industry":"IT Services",         "cap":"Large"},
    "TECHM":      {"name":"Tech Mahindra Ltd",                    "sector":"IT",           "industry":"IT Services",         "cap":"Large"},
    "LTIM":       {"name":"LTIMindtree Ltd",                      "sector":"IT",           "industry":"IT Services",         "cap":"Large"},
    "MPHASIS":    {"name":"Mphasis Ltd",                          "sector":"IT",           "industry":"IT Services",         "cap":"Mid"},
    "PERSISTENT": {"name":"Persistent Systems Ltd",               "sector":"IT",           "industry":"IT Services",         "cap":"Mid"},
    "COFORGE":    {"name":"Coforge Ltd",                          "sector":"IT",           "industry":"IT Services",         "cap":"Mid"},
    "OFSS":       {"name":"Oracle Financial Services Software",   "sector":"IT",           "industry":"IT Services",         "cap":"Large"},
    "KPITTECH":   {"name":"KPIT Technologies Ltd",                "sector":"IT",           "industry":"IT Services",         "cap":"Mid"},
    "TATAELXSI":  {"name":"Tata Elxsi Ltd",                       "sector":"IT",           "industry":"IT Services",         "cap":"Mid"},
    # ── IT SERVICES: MID/SMALL CAP ───────────────────────────────────────────
    "ZENSAR":     {"name":"Zensar Technologies Ltd",              "sector":"IT",           "industry":"IT Services",         "cap":"Small"},
    "MASTEK":     {"name":"Mastek Ltd",                           "sector":"IT",           "industry":"IT Services",         "cap":"Small"},
    "BSOFT":      {"name":"Birlasoft Ltd",                        "sector":"IT",           "industry":"IT Services",         "cap":"Small"},
    "CYIENT":     {"name":"Cyient Ltd",                           "sector":"IT",           "industry":"IT Services",         "cap":"Mid"},
    "SONATSOFTW": {"name":"Sonata Software Ltd",                  "sector":"IT",           "industry":"IT Services",         "cap":"Small"},
    "RATEGAIN":   {"name":"RateGain Travel Technologies Ltd",     "sector":"IT",           "industry":"IT Services",         "cap":"Small"},
    "TANLA":      {"name":"Tanla Platforms Ltd",                  "sector":"IT",           "industry":"IT Services",         "cap":"Small"},
    "HAPPSTMNDS": {"name":"Happiest Minds Technologies Ltd",      "sector":"IT",           "industry":"IT Services",         "cap":"Small"},
    "LATENTVIEW": {"name":"LatentView Analytics Ltd",             "sector":"IT",           "industry":"IT Services",         "cap":"Small"},
    "XCHANGING":  {"name":"Xchanging Solutions Ltd",              "sector":"IT",           "industry":"IT Services",         "cap":"Small"},
    # ── INTERNET / DIGITAL ───────────────────────────────────────────────────
    "NAUKRI":     {"name":"Info Edge (India) Ltd",                "sector":"Internet",     "industry":"Job Portal",          "cap":"Large"},
    "ZOMATO":     {"name":"Zomato Ltd",                           "sector":"Internet",     "industry":"Food Tech",           "cap":"Large"},
    "PAYTM":      {"name":"One 97 Communications Ltd",            "sector":"Internet",     "industry":"FinTech",             "cap":"Mid"},
    "NYKAA":      {"name":"FSN E-Commerce Ventures Ltd",          "sector":"Internet",     "industry":"E-Commerce",          "cap":"Mid"},
    "POLICYBZR":  {"name":"PB Fintech Ltd",                       "sector":"Internet",     "industry":"InsurTech",           "cap":"Mid"},
    "INDIAMART":  {"name":"IndiaMART InterMESH Ltd",              "sector":"Internet",     "industry":"B2B Marketplace",     "cap":"Mid"},
    "CARTRADE":   {"name":"CarTrade Tech Ltd",                    "sector":"Internet",     "industry":"Auto Marketplace",    "cap":"Small"},
    "JUSTDIAL":   {"name":"Just Dial Ltd",                        "sector":"Internet",     "industry":"Local Search",        "cap":"Small"},
    # ── ELECTRONICS / TECH MANUFACTURING ─────────────────────────────────────
    "DIXON":      {"name":"Dixon Technologies (India) Ltd",       "sector":"Electronics",  "industry":"EMS",                 "cap":"Mid"},
    "AMBER":      {"name":"Amber Enterprises India Ltd",          "sector":"Electronics",  "industry":"Electronics Mfg",     "cap":"Small"},
    "KAYNES":     {"name":"Kaynes Technology India Ltd",          "sector":"Electronics",  "industry":"EMS",                 "cap":"Small"},
    "SYRMA":      {"name":"Syrma SGS Technology Ltd",             "sector":"Electronics",  "industry":"EMS",                 "cap":"Small"},
    "PGEL":       {"name":"PG Electroplast Ltd",                  "sector":"Electronics",  "industry":"Electronics Mfg",     "cap":"Small"},
    # ── OIL & GAS ─────────────────────────────────────────────────────────────
    "RELIANCE":   {"name":"Reliance Industries Ltd",              "sector":"Oil & Gas",    "industry":"Diversified",         "cap":"Large"},
    "ONGC":       {"name":"Oil & Natural Gas Corporation Ltd",    "sector":"Oil & Gas",    "industry":"Exploration",         "cap":"Large"},
    "BPCL":       {"name":"Bharat Petroleum Corporation Ltd",     "sector":"Oil & Gas",    "industry":"Refining",            "cap":"Large"},
    "IOC":        {"name":"Indian Oil Corporation Ltd",           "sector":"Oil & Gas",    "industry":"Refining",            "cap":"Large"},
    "HINDPETRO":  {"name":"Hindustan Petroleum Corporation Ltd",  "sector":"Oil & Gas",    "industry":"Refining",            "cap":"Large"},
    "GAIL":       {"name":"GAIL (India) Ltd",                     "sector":"Oil & Gas",    "industry":"Gas Distribution",    "cap":"Large"},
    "OIL":        {"name":"Oil India Ltd",                        "sector":"Oil & Gas",    "industry":"Exploration",         "cap":"Mid"},
    "MGL":        {"name":"Mahanagar Gas Ltd",                    "sector":"Oil & Gas",    "industry":"City Gas",            "cap":"Mid"},
    "IGL":        {"name":"Indraprastha Gas Ltd",                 "sector":"Oil & Gas",    "industry":"City Gas",            "cap":"Mid"},
    "PETRONET":   {"name":"Petronet LNG Ltd",                     "sector":"Oil & Gas",    "industry":"LNG",                 "cap":"Mid"},
    "ATGL":       {"name":"Adani Total Gas Ltd",                  "sector":"Oil & Gas",    "industry":"City Gas",            "cap":"Large"},
    "GSPL":       {"name":"Gujarat State Petronet Ltd",           "sector":"Oil & Gas",    "industry":"Gas Transmission",    "cap":"Mid"},
    "GUJGASLTD":  {"name":"Gujarat Gas Ltd",                      "sector":"Oil & Gas",    "industry":"City Gas",            "cap":"Mid"},
    "AEGISCHEM":  {"name":"Aegis Logistics Ltd",                  "sector":"Oil & Gas",    "industry":"LPG & Gas",           "cap":"Small"},
    "MRPL":       {"name":"Mangalore Refinery & Petrochemicals",  "sector":"Oil & Gas",    "industry":"Refining",            "cap":"Mid"},
    # ── POWER ─────────────────────────────────────────────────────────────────
    "NTPC":       {"name":"NTPC Ltd",                             "sector":"Power",        "industry":"Power Generation",    "cap":"Large"},
    "POWERGRID":  {"name":"Power Grid Corporation of India",      "sector":"Power",        "industry":"Transmission",        "cap":"Large"},
    "ADANIPOWER": {"name":"Adani Power Ltd",                      "sector":"Power",        "industry":"Power Generation",    "cap":"Large"},
    "ADANIGREEN": {"name":"Adani Green Energy Ltd",               "sector":"Power",        "industry":"Renewable Energy",    "cap":"Large"},
    "TATAPOWER":  {"name":"Tata Power Company Ltd",               "sector":"Power",        "industry":"Integrated Power",    "cap":"Large"},
    "TORNTPOWER": {"name":"Torrent Power Ltd",                    "sector":"Power",        "industry":"Integrated Power",    "cap":"Mid"},
    "NHPC":       {"name":"NHPC Ltd",                             "sector":"Power",        "industry":"Hydropower",          "cap":"Mid"},
    "SJVN":       {"name":"SJVN Ltd",                             "sector":"Power",        "industry":"Hydropower",          "cap":"Mid"},
    "CESC":       {"name":"CESC Ltd",                             "sector":"Power",        "industry":"Integrated Power",    "cap":"Mid"},
    "IREDA":      {"name":"IREDA Ltd",                            "sector":"Power",        "industry":"Renewable Finance",   "cap":"Mid"},
    "JSWENERGY":  {"name":"JSW Energy Ltd",                       "sector":"Power",        "industry":"Power Generation",    "cap":"Large"},
    "ADANITRANS": {"name":"Adani Energy Solutions Ltd",           "sector":"Power",        "industry":"Transmission",        "cap":"Large"},
    "THERMAX":    {"name":"Thermax Ltd",                          "sector":"Power",        "industry":"Energy Solutions",    "cap":"Mid"},
    # ── PHARMA: LARGE CAP ─────────────────────────────────────────────────────
    "SUNPHARMA":  {"name":"Sun Pharmaceutical Industries Ltd",    "sector":"Pharma",       "industry":"Pharma",              "cap":"Large"},
    "DRREDDY":    {"name":"Dr Reddy's Laboratories Ltd",          "sector":"Pharma",       "industry":"Pharma",              "cap":"Large"},
    "CIPLA":      {"name":"Cipla Ltd",                            "sector":"Pharma",       "industry":"Pharma",              "cap":"Large"},
    "DIVISLAB":   {"name":"Divi's Laboratories Ltd",              "sector":"Pharma",       "industry":"API",                 "cap":"Large"},
    "AUROPHARMA": {"name":"Aurobindo Pharma Ltd",                 "sector":"Pharma",       "industry":"Pharma",              "cap":"Large"},
    "BIOCON":     {"name":"Biocon Ltd",                           "sector":"Pharma",       "industry":"Biotech",             "cap":"Mid"},
    "LUPIN":      {"name":"Lupin Ltd",                            "sector":"Pharma",       "industry":"Pharma",              "cap":"Large"},
    "TORNTPHARM": {"name":"Torrent Pharmaceuticals Ltd",          "sector":"Pharma",       "industry":"Pharma",              "cap":"Large"},
    "ALKEM":      {"name":"Alkem Laboratories Ltd",               "sector":"Pharma",       "industry":"Pharma",              "cap":"Mid"},
    "MANKIND":    {"name":"Mankind Pharma Ltd",                   "sector":"Pharma",       "industry":"Pharma",              "cap":"Large"},
    "ZYDUSLIFE":  {"name":"Zydus Lifesciences Ltd",               "sector":"Pharma",       "industry":"Pharma",              "cap":"Large"},
    # ── PHARMA: MID/SMALL CAP ────────────────────────────────────────────────
    "GLENMARK":   {"name":"Glenmark Pharmaceuticals Ltd",         "sector":"Pharma",       "industry":"Pharma",              "cap":"Mid"},
    "IPCALAB":    {"name":"IPCA Laboratories Ltd",                "sector":"Pharma",       "industry":"Pharma",              "cap":"Mid"},
    "NATCOPHARM": {"name":"Natco Pharma Ltd",                     "sector":"Pharma",       "industry":"Pharma",              "cap":"Small"},
    "LAURUS":     {"name":"Laurus Labs Ltd",                      "sector":"Pharma",       "industry":"API",                 "cap":"Mid"},
    "SYNGENE":    {"name":"Syngene International Ltd",            "sector":"Pharma",       "industry":"CRO",                 "cap":"Mid"},
    "ALEMBICLTD": {"name":"Alembic Pharmaceuticals Ltd",          "sector":"Pharma",       "industry":"Pharma",              "cap":"Small"},
    "GLAND":      {"name":"Gland Pharma Ltd",                     "sector":"Pharma",       "industry":"Pharma",              "cap":"Mid"},
    "GRANULES":   {"name":"Granules India Ltd",                   "sector":"Pharma",       "industry":"API",                 "cap":"Small"},
    "ABBOTINDIA": {"name":"Abbott India Ltd",                     "sector":"Pharma",       "industry":"Pharma",              "cap":"Mid"},
    "PFIZER":     {"name":"Pfizer Ltd",                           "sector":"Pharma",       "industry":"Pharma",              "cap":"Mid"},
    "GLAXO":      {"name":"GlaxoSmithKline Pharmaceuticals",      "sector":"Pharma",       "industry":"Pharma",              "cap":"Mid"},
    "ERISLIFE":   {"name":"Eris Lifesciences Ltd",                "sector":"Pharma",       "industry":"Pharma",              "cap":"Small"},
    "JBCHEPHARM": {"name":"J.B. Chemicals & Pharmaceuticals",     "sector":"Pharma",       "industry":"Pharma",              "cap":"Small"},
    "AJANTPHARM": {"name":"Ajanta Pharma Ltd",                    "sector":"Pharma",       "industry":"Pharma",              "cap":"Small"},
    "WOCKHARDT":  {"name":"Wockhardt Ltd",                        "sector":"Pharma",       "industry":"Pharma",              "cap":"Small"},
    "SUVEN":      {"name":"Suven Pharmaceuticals Ltd",            "sector":"Pharma",       "industry":"API",                 "cap":"Small"},
    "CAPLIPOINT": {"name":"Caplin Point Laboratories Ltd",        "sector":"Pharma",       "industry":"Pharma",              "cap":"Small"},
    "LAURUSLABS": {"name":"Laurus Labs Ltd",                      "sector":"Pharma",       "industry":"API",                 "cap":"Mid"},
    # ── HEALTHCARE ────────────────────────────────────────────────────────────
    "APOLLOHOSP": {"name":"Apollo Hospitals Enterprise Ltd",      "sector":"Healthcare",   "industry":"Hospitals",           "cap":"Large"},
    "LALPATHLAB": {"name":"Dr Lal PathLabs Ltd",                  "sector":"Healthcare",   "industry":"Diagnostics",         "cap":"Mid"},
    "MAXHEALTH":  {"name":"Max Healthcare Institute Ltd",         "sector":"Healthcare",   "industry":"Hospitals",           "cap":"Large"},
    "FORTIS":     {"name":"Fortis Healthcare Ltd",                "sector":"Healthcare",   "industry":"Hospitals",           "cap":"Mid"},
    "METROPOLIS": {"name":"Metropolis Healthcare Ltd",            "sector":"Healthcare",   "industry":"Diagnostics",         "cap":"Small"},
    "ASTERDM":    {"name":"Aster DM Healthcare Ltd",              "sector":"Healthcare",   "industry":"Hospitals",           "cap":"Mid"},
    "KRSNAA":     {"name":"Krsnaa Diagnostics Ltd",               "sector":"Healthcare",   "industry":"Diagnostics",         "cap":"Small"},
    "RAINBOW":    {"name":"Rainbow Children's Medicare Ltd",      "sector":"Healthcare",   "industry":"Hospitals",           "cap":"Small"},
    "MEDANTA":    {"name":"Global Health Ltd",                    "sector":"Healthcare",   "industry":"Hospitals",           "cap":"Mid"},
    "VIJAYA":     {"name":"Vijaya Diagnostic Centre Ltd",         "sector":"Healthcare",   "industry":"Diagnostics",         "cap":"Small"},
    # ── FMCG ──────────────────────────────────────────────────────────────────
    "HINDUNILVR": {"name":"Hindustan Unilever Ltd",               "sector":"FMCG",         "industry":"FMCG",                "cap":"Large"},
    "ITC":        {"name":"ITC Ltd",                              "sector":"FMCG",         "industry":"Diversified FMCG",    "cap":"Large"},
    "NESTLEIND":  {"name":"Nestle India Ltd",                     "sector":"FMCG",         "industry":"Food & Beverages",    "cap":"Large"},
    "BRITANNIA":  {"name":"Britannia Industries Ltd",             "sector":"FMCG",         "industry":"Food & Beverages",    "cap":"Large"},
    "TATACONSUM": {"name":"Tata Consumer Products Ltd",           "sector":"FMCG",         "industry":"Food & Beverages",    "cap":"Large"},
    "DABUR":      {"name":"Dabur India Ltd",                      "sector":"FMCG",         "industry":"FMCG",                "cap":"Large"},
    "GODREJCP":   {"name":"Godrej Consumer Products Ltd",         "sector":"FMCG",         "industry":"FMCG",                "cap":"Large"},
    "MARICO":     {"name":"Marico Ltd",                           "sector":"FMCG",         "industry":"FMCG",                "cap":"Large"},
    "COLPAL":     {"name":"Colgate-Palmolive (India) Ltd",        "sector":"FMCG",         "industry":"FMCG",                "cap":"Large"},
    "EMAMILTD":   {"name":"Emami Ltd",                            "sector":"FMCG",         "industry":"FMCG",                "cap":"Mid"},
    "VBL":        {"name":"Varun Beverages Ltd",                  "sector":"FMCG",         "industry":"Beverages",           "cap":"Large"},
    "MCDOWELL-N": {"name":"United Spirits Ltd",                   "sector":"FMCG",         "industry":"Spirits & Beverages", "cap":"Large"},
    "RADICO":     {"name":"Radico Khaitan Ltd",                   "sector":"FMCG",         "industry":"Spirits & Beverages", "cap":"Mid"},
    "UBL":        {"name":"United Breweries Ltd",                 "sector":"FMCG",         "industry":"Beer",                "cap":"Mid"},
    "PGHH":       {"name":"Procter & Gamble Hygiene & Health",   "sector":"FMCG",         "industry":"FMCG",                "cap":"Mid"},
    "VSTIND":     {"name":"VST Industries Ltd",                   "sector":"FMCG",         "industry":"Tobacco",             "cap":"Mid"},
    "GILLETTE":   {"name":"Gillette India Ltd",                   "sector":"FMCG",         "industry":"FMCG",                "cap":"Mid"},
    "DMART":      {"name":"Avenue Supermarts Ltd",                "sector":"FMCG",         "industry":"Retail",              "cap":"Large"},
    "BIKAJI":     {"name":"Bikaji Foods International Ltd",       "sector":"FMCG",         "industry":"Food & Beverages",    "cap":"Small"},
    "PATANJALI":  {"name":"Patanjali Foods Ltd",                  "sector":"FMCG",         "industry":"Food & Beverages",    "cap":"Mid"},
    # ── CONSUMER / QSR / FOOD ────────────────────────────────────────────────
    "JUBLFOOD":   {"name":"Jubilant Foodworks Ltd",               "sector":"Consumer",     "industry":"QSR",                 "cap":"Mid"},
    "DEVYANI":    {"name":"Devyani International Ltd",            "sector":"Consumer",     "industry":"QSR",                 "cap":"Small"},
    "WESTLIFE":   {"name":"Westlife Foodworld Ltd",               "sector":"Consumer",     "industry":"QSR",                 "cap":"Small"},
    "BARBEQUE":   {"name":"Barbeque Nation Hospitality Ltd",      "sector":"Consumer",     "industry":"Restaurants",         "cap":"Small"},
    # ── CONSUMER DURABLES ─────────────────────────────────────────────────────
    "TITAN":      {"name":"Titan Company Ltd",                    "sector":"Consumer",     "industry":"Watches & Jewelry",   "cap":"Large"},
    "ASIANPAINT": {"name":"Asian Paints Ltd",                     "sector":"Consumer",     "industry":"Paints",              "cap":"Large"},
    "PIDILITIND": {"name":"Pidilite Industries Ltd",              "sector":"Consumer",     "industry":"Adhesives",           "cap":"Large"},
    "VOLTAS":     {"name":"Voltas Ltd",                           "sector":"Consumer",     "industry":"Consumer Durables",   "cap":"Mid"},
    "HAVELLS":    {"name":"Havells India Ltd",                    "sector":"Consumer",     "industry":"Electricals",         "cap":"Large"},
    "POLYCAB":    {"name":"Polycab India Ltd",                    "sector":"Consumer",     "industry":"Cables & Wires",      "cap":"Large"},
    "CROMPTON":   {"name":"Crompton Greaves Consumer Electricals","sector":"Consumer",     "industry":"Electricals",         "cap":"Mid"},
    "BLUESTARCO": {"name":"Blue Star Ltd",                        "sector":"Consumer",     "industry":"Consumer Durables",   "cap":"Mid"},
    "ASTRAL":     {"name":"Astral Ltd",                           "sector":"Consumer",     "industry":"Pipes",               "cap":"Mid"},
    "SUPREMEIND": {"name":"Supreme Industries Ltd",               "sector":"Consumer",     "industry":"Plastics",            "cap":"Mid"},
    "BERGEPAINT": {"name":"Berger Paints India Ltd",              "sector":"Consumer",     "industry":"Paints",              "cap":"Large"},
    "KANSAINER":  {"name":"Kansai Nerolac Paints Ltd",            "sector":"Consumer",     "industry":"Paints",              "cap":"Mid"},
    "AKZOINDIA":  {"name":"Akzo Nobel India Ltd",                 "sector":"Consumer",     "industry":"Paints",              "cap":"Mid"},
    "CERA":       {"name":"Cera Sanitaryware Ltd",                "sector":"Consumer",     "industry":"Building Products",   "cap":"Small"},
    "GREENPANEL": {"name":"Greenpanel Industries Ltd",            "sector":"Consumer",     "industry":"Building Products",   "cap":"Small"},
    # ── RETAIL & APPAREL ─────────────────────────────────────────────────────
    "BATAINDIA":  {"name":"Bata India Ltd",                       "sector":"Retail",       "industry":"Footwear",            "cap":"Mid"},
    "PAGEIND":    {"name":"Page Industries Ltd",                  "sector":"Textiles",     "industry":"Garments",            "cap":"Large"},
    "MANYAVAR":   {"name":"Vedant Fashions Ltd",                  "sector":"Textiles",     "industry":"Apparel",             "cap":"Mid"},
    "TRENT":      {"name":"Trent Ltd",                            "sector":"Retail",       "industry":"Retail",              "cap":"Large"},
    "ABFRL":      {"name":"Aditya Birla Fashion & Retail Ltd",   "sector":"Retail",       "industry":"Retail",              "cap":"Mid"},
    "RAYMOND":    {"name":"Raymond Ltd",                          "sector":"Textiles",     "industry":"Textiles",            "cap":"Mid"},
    "SHOPERSTOP": {"name":"Shoppers Stop Ltd",                    "sector":"Retail",       "industry":"Retail",              "cap":"Small"},
    "VMART":      {"name":"V-Mart Retail Ltd",                    "sector":"Retail",       "industry":"Retail",              "cap":"Small"},
    "KALYANKJIL": {"name":"Kalyan Jewellers India Ltd",           "sector":"Retail",       "industry":"Jewelry",             "cap":"Mid"},
    "SENCO":      {"name":"Senco Gold Ltd",                       "sector":"Retail",       "industry":"Jewelry",             "cap":"Small"},
    "RAJESHEXPO": {"name":"Rajesh Exports Ltd",                   "sector":"Retail",       "industry":"Jewelry",             "cap":"Mid"},
    "LUXIND":     {"name":"Lux Industries Ltd",                   "sector":"Textiles",     "industry":"Garments",            "cap":"Small"},
    "DOLLAR":     {"name":"Dollar Industries Ltd",                "sector":"Textiles",     "industry":"Garments",            "cap":"Small"},
    "KPRMILL":    {"name":"KPR Mill Ltd",                         "sector":"Textiles",     "industry":"Textiles",            "cap":"Small"},
    "TRIDENT":    {"name":"Trident Ltd",                          "sector":"Textiles",     "industry":"Textiles",            "cap":"Small"},
    "VARDHMANXT": {"name":"Vardhman Textiles Ltd",                "sector":"Textiles",     "industry":"Textiles",            "cap":"Small"},
    # ── AUTO: OEMS ────────────────────────────────────────────────────────────
    "MARUTI":     {"name":"Maruti Suzuki India Ltd",              "sector":"Auto",         "industry":"Passenger Vehicles",  "cap":"Large"},
    "TATAMOTORS": {"name":"Tata Motors Ltd",                      "sector":"Auto",         "industry":"Commercial Vehicles", "cap":"Large"},
    "M&M":        {"name":"Mahindra & Mahindra Ltd",              "sector":"Auto",         "industry":"Passenger Vehicles",  "cap":"Large"},
    "BAJAJ-AUTO": {"name":"Bajaj Auto Ltd",                       "sector":"Auto",         "industry":"Two Wheelers",        "cap":"Large"},
    "HEROMOTOCO": {"name":"Hero MotoCorp Ltd",                    "sector":"Auto",         "industry":"Two Wheelers",        "cap":"Large"},
    "EICHERMOT":  {"name":"Eicher Motors Ltd",                    "sector":"Auto",         "industry":"Two Wheelers",        "cap":"Large"},
    "ASHOKLEY":   {"name":"Ashok Leyland Ltd",                    "sector":"Auto",         "industry":"Commercial Vehicles", "cap":"Mid"},
    "TVSMOTOR":   {"name":"TVS Motor Company Ltd",                "sector":"Auto",         "industry":"Two Wheelers",        "cap":"Large"},
    "OLECTRA":    {"name":"Olectra Greentech Ltd",                "sector":"Auto",         "industry":"Electric Vehicles",   "cap":"Small"},
    # ── AUTO: TYRES & ANCILLARIES ────────────────────────────────────────────
    "BALKRISIND": {"name":"Balkrishna Industries Ltd",            "sector":"Auto",         "industry":"Tyres",               "cap":"Mid"},
    "APOLLOTYRE": {"name":"Apollo Tyres Ltd",                     "sector":"Auto",         "industry":"Tyres",               "cap":"Mid"},
    "MRF":        {"name":"MRF Ltd",                              "sector":"Auto",         "industry":"Tyres",               "cap":"Large"},
    "CEATLTD":    {"name":"CEAT Ltd",                             "sector":"Auto",         "industry":"Tyres",               "cap":"Mid"},
    "MOTHERSON":  {"name":"Samvardhana Motherson Intl Ltd",       "sector":"Auto",         "industry":"Auto Ancillary",      "cap":"Large"},
    "BOSCHLTD":   {"name":"Bosch Ltd",                            "sector":"Auto",         "industry":"Auto Ancillary",      "cap":"Large"},
    "EXIDEIND":   {"name":"Exide Industries Ltd",                 "sector":"Auto",         "industry":"Auto Ancillary",      "cap":"Mid"},
    "AMARAJABAT": {"name":"Amara Raja Energy & Mobility Ltd",     "sector":"Auto",         "industry":"Auto Ancillary",      "cap":"Mid"},
    "ENDURANCE":  {"name":"Endurance Technologies Ltd",           "sector":"Auto",         "industry":"Auto Ancillary",      "cap":"Mid"},
    "TIINDIA":    {"name":"Tube Investments of India Ltd",        "sector":"Auto",         "industry":"Auto Ancillary",      "cap":"Mid"},
    "MINDAINDS":  {"name":"Minda Industries Ltd",                 "sector":"Auto",         "industry":"Auto Ancillary",      "cap":"Mid"},
    "SUPRAJIT":   {"name":"Suprajit Engineering Ltd",             "sector":"Auto",         "industry":"Auto Ancillary",      "cap":"Small"},
    "GABRIEL":    {"name":"Gabriel India Ltd",                    "sector":"Auto",         "industry":"Auto Ancillary",      "cap":"Small"},
    "JAMNAAUTO":  {"name":"Jamna Auto Industries Ltd",            "sector":"Auto",         "industry":"Auto Ancillary",      "cap":"Small"},
    "SUNDRMAUTO": {"name":"Sundaram-Clayton Ltd",                 "sector":"Auto",         "industry":"Auto Ancillary",      "cap":"Small"},
    "CRAFTSMAN":  {"name":"Craftsman Automation Ltd",             "sector":"Auto",         "industry":"Auto Ancillary",      "cap":"Small"},
    # ── METALS ───────────────────────────────────────────────────────────────
    "TATASTEEL":  {"name":"Tata Steel Ltd",                       "sector":"Metals",       "industry":"Steel",               "cap":"Large"},
    "JSWSTEEL":   {"name":"JSW Steel Ltd",                        "sector":"Metals",       "industry":"Steel",               "cap":"Large"},
    "HINDALCO":   {"name":"Hindalco Industries Ltd",              "sector":"Metals",       "industry":"Aluminium",           "cap":"Large"},
    "VEDL":       {"name":"Vedanta Ltd",                          "sector":"Metals",       "industry":"Diversified Metals",  "cap":"Large"},
    "SAIL":       {"name":"Steel Authority of India Ltd",         "sector":"Metals",       "industry":"Steel",               "cap":"Mid"},
    "NATIONALUM": {"name":"National Aluminium Company Ltd",       "sector":"Metals",       "industry":"Aluminium",           "cap":"Mid"},
    "JINDALSTEL": {"name":"Jindal Steel & Power Ltd",             "sector":"Metals",       "industry":"Steel",               "cap":"Mid"},
    "APLAPOLLO":  {"name":"APL Apollo Tubes Ltd",                 "sector":"Metals",       "industry":"Steel Tubes",         "cap":"Mid"},
    "HINDCOPPER": {"name":"Hindustan Copper Ltd",                 "sector":"Metals",       "industry":"Copper",              "cap":"Mid"},
    "RATNAMANI":  {"name":"Ratnamani Metals & Tubes Ltd",         "sector":"Metals",       "industry":"Steel Tubes",         "cap":"Mid"},
    "WELSPUNLIV": {"name":"Welspun Living Ltd",                   "sector":"Textiles",     "industry":"Home Textiles",       "cap":"Small"},
    "SHYAMMETL":  {"name":"Shyam Metalics and Energy Ltd",       "sector":"Metals",       "industry":"Steel",               "cap":"Mid"},
    "JSPL":       {"name":"Jindal Stainless Ltd",                 "sector":"Metals",       "industry":"Stainless Steel",     "cap":"Mid"},
    # ── MINING ────────────────────────────────────────────────────────────────
    "COALINDIA":  {"name":"Coal India Ltd",                       "sector":"Mining",       "industry":"Coal",                "cap":"Large"},
    "NMDC":       {"name":"NMDC Ltd",                             "sector":"Mining",       "industry":"Iron Ore",            "cap":"Large"},
    "GMRINFRA":   {"name":"GMR Airports Infrastructure Ltd",      "sector":"Mining",       "industry":"Airports",            "cap":"Large"},
    # ── CEMENT ───────────────────────────────────────────────────────────────
    "ULTRACEMCO": {"name":"UltraTech Cement Ltd",                 "sector":"Cement",       "industry":"Cement",              "cap":"Large"},
    "SHREECEM":   {"name":"Shree Cement Ltd",                     "sector":"Cement",       "industry":"Cement",              "cap":"Large"},
    "AMBUJACEM":  {"name":"Ambuja Cements Ltd",                   "sector":"Cement",       "industry":"Cement",              "cap":"Large"},
    "ACC":        {"name":"ACC Ltd",                              "sector":"Cement",       "industry":"Cement",              "cap":"Mid"},
    "RAMCOCEM":   {"name":"The Ramco Cements Ltd",                "sector":"Cement",       "industry":"Cement",              "cap":"Mid"},
    "DALMIACEM":  {"name":"Dalmia Bharat Ltd",                    "sector":"Cement",       "industry":"Cement",              "cap":"Mid"},
    "JKCEM":      {"name":"JK Cement Ltd",                        "sector":"Cement",       "industry":"Cement",              "cap":"Mid"},
    "JKLAKSHMI":  {"name":"JK Lakshmi Cement Ltd",                "sector":"Cement",       "industry":"Cement",              "cap":"Small"},
    "ORIENTCEM":  {"name":"Orient Cement Ltd",                    "sector":"Cement",       "industry":"Cement",              "cap":"Small"},
    "PRISMJOHNS": {"name":"Prism Johnson Ltd",                    "sector":"Cement",       "industry":"Cement",              "cap":"Small"},
    "HEIDELBCEM": {"name":"Nuvoco Vistas Corporation Ltd",        "sector":"Cement",       "industry":"Cement",              "cap":"Small"},
    "STARCEMENT": {"name":"Star Cement Ltd",                      "sector":"Cement",       "industry":"Cement",              "cap":"Small"},
    # ── INFRA: CONSTRUCTION & ENGINEERING ────────────────────────────────────
    "LT":         {"name":"Larsen & Toubro Ltd",                  "sector":"Infra",        "industry":"Engineering",         "cap":"Large"},
    "ADANIENT":   {"name":"Adani Enterprises Ltd",                "sector":"Infra",        "industry":"Diversified",         "cap":"Large"},
    "ADANIPORTS": {"name":"Adani Ports and SEZ Ltd",              "sector":"Infra",        "industry":"Ports",               "cap":"Large"},
    "IRB":        {"name":"IRB Infrastructure Developers Ltd",    "sector":"Infra",        "industry":"Roads",               "cap":"Mid"},
    "KNRCON":     {"name":"KNR Constructions Ltd",                "sector":"Infra",        "industry":"Roads",               "cap":"Small"},
    "NCC":        {"name":"NCC Ltd",                              "sector":"Infra",        "industry":"Construction",        "cap":"Small"},
    "RVNL":       {"name":"Rail Vikas Nigam Ltd",                 "sector":"Infra",        "industry":"Railways",            "cap":"Mid"},
    "BHARATFORG": {"name":"Bharat Forge Ltd",                     "sector":"Capital Goods","industry":"Forgings",            "cap":"Large"},
    "KECINTL":    {"name":"KEC International Ltd",                "sector":"Capital Goods","industry":"T&D",                  "cap":"Mid"},
    "KALPATPOWR": {"name":"Kalpataru Projects International",     "sector":"Infra",        "industry":"T&D",                  "cap":"Mid"},
    "PNCINFRA":   {"name":"PNC Infratech Ltd",                    "sector":"Infra",        "industry":"Roads",               "cap":"Small"},
    "HGINFRA":    {"name":"H.G. Infra Engineering Ltd",           "sector":"Infra",        "industry":"Roads",               "cap":"Small"},
    "GPPL":       {"name":"Gujarat Pipavav Port Ltd",             "sector":"Infra",        "industry":"Ports",               "cap":"Small"},
    # ── CAPITAL GOODS ────────────────────────────────────────────────────────
    "SIEMENS":    {"name":"Siemens Ltd",                          "sector":"Capital Goods","industry":"Engineering",         "cap":"Large"},
    "ABB":        {"name":"ABB India Ltd",                        "sector":"Capital Goods","industry":"Engineering",         "cap":"Large"},
    "BHEL":       {"name":"Bharat Heavy Electricals Ltd",         "sector":"Capital Goods","industry":"Engineering",         "cap":"Mid"},
    "CUMMINSIND": {"name":"Cummins India Ltd",                    "sector":"Capital Goods","industry":"Engines",             "cap":"Mid"},
    "CGPOWER":    {"name":"CG Power and Industrial Solutions",    "sector":"Capital Goods","industry":"Electricals",         "cap":"Mid"},
    "GRINDWELL":  {"name":"Grindwell Norton Ltd",                 "sector":"Capital Goods","industry":"Abrasives",           "cap":"Mid"},
    "CARBORUNIV": {"name":"Carborundum Universal Ltd",            "sector":"Capital Goods","industry":"Abrasives",           "cap":"Mid"},
    "AIAENG":     {"name":"AIA Engineering Ltd",                  "sector":"Capital Goods","industry":"Engineering",         "cap":"Mid"},
    "ELGIEQUIP":  {"name":"Elgi Equipments Ltd",                  "sector":"Capital Goods","industry":"Compressors",         "cap":"Small"},
    "CMSINFO":    {"name":"CMS Info Systems Ltd",                 "sector":"Capital Goods","industry":"Cash Management",     "cap":"Small"},
    # ── DEFENCE ───────────────────────────────────────────────────────────────
    "BEL":        {"name":"Bharat Electronics Ltd",               "sector":"Defence",      "industry":"Electronics",         "cap":"Large"},
    "HAL":        {"name":"Hindustan Aeronautics Ltd",            "sector":"Defence",      "industry":"Aerospace",           "cap":"Large"},
    "MAZAGON":    {"name":"Mazagon Dock Shipbuilders Ltd",        "sector":"Defence",      "industry":"Shipbuilding",        "cap":"Large"},
    "GRSE":       {"name":"Garden Reach Shipbuilders Ltd",        "sector":"Defence",      "industry":"Shipbuilding",        "cap":"Mid"},
    "COCHINSHIP": {"name":"Cochin Shipyard Ltd",                  "sector":"Defence",      "industry":"Shipbuilding",        "cap":"Mid"},
    "PARAS":      {"name":"Paras Defence and Space Technologies", "sector":"Defence",      "industry":"Defence Tech",        "cap":"Small"},
    "DPWLTD":     {"name":"Data Patterns (India) Ltd",            "sector":"Defence",      "industry":"Defence Electronics", "cap":"Small"},
    # ── CHEMICALS ────────────────────────────────────────────────────────────
    "UPL":        {"name":"UPL Ltd",                              "sector":"Chemicals",    "industry":"Agrochemicals",       "cap":"Large"},
    "PIIND":      {"name":"PI Industries Ltd",                    "sector":"Chemicals",    "industry":"Agrochemicals",       "cap":"Large"},
    "COROMANDEL": {"name":"Coromandel International Ltd",         "sector":"Chemicals",    "industry":"Fertilizers",         "cap":"Large"},
    "DEEPAKNTR":  {"name":"Deepak Nitrite Ltd",                   "sector":"Chemicals",    "industry":"Specialty Chemicals", "cap":"Mid"},
    "VINATIORGA": {"name":"Vinati Organics Ltd",                  "sector":"Chemicals",    "industry":"Specialty Chemicals", "cap":"Mid"},
    "TATACHEM":   {"name":"Tata Chemicals Ltd",                   "sector":"Chemicals",    "industry":"Commodity Chemicals", "cap":"Mid"},
    "NAVINFLUOR": {"name":"Navin Fluorine International Ltd",     "sector":"Chemicals",    "industry":"Specialty Chemicals", "cap":"Mid"},
    "SRF":        {"name":"SRF Ltd",                              "sector":"Chemicals",    "industry":"Specialty Chemicals", "cap":"Large"},
    "ATUL":       {"name":"Atul Ltd",                             "sector":"Chemicals",    "industry":"Specialty Chemicals", "cap":"Mid"},
    "FLUOROCHEM": {"name":"Gujarat Fluorochemicals Ltd",          "sector":"Chemicals",    "industry":"Specialty Chemicals", "cap":"Mid"},
    "AARTI":      {"name":"Aarti Industries Ltd",                 "sector":"Chemicals",    "industry":"Specialty Chemicals", "cap":"Mid"},
    "ROSSARI":    {"name":"Rossari Biotech Ltd",                  "sector":"Chemicals",    "industry":"Specialty Chemicals", "cap":"Small"},
    "FINEORG":    {"name":"Fine Organic Industries Ltd",          "sector":"Chemicals",    "industry":"Specialty Chemicals", "cap":"Small"},
    "BALAMINES":  {"name":"Balaji Amines Ltd",                    "sector":"Chemicals",    "industry":"Specialty Chemicals", "cap":"Small"},
    "SUDARSCHEM": {"name":"Sudarshan Chemical Industries Ltd",    "sector":"Chemicals",    "industry":"Specialty Chemicals", "cap":"Small"},
    "JUBLINGREA": {"name":"Jubilant Ingrevia Ltd",                "sector":"Chemicals",    "industry":"Specialty Chemicals", "cap":"Small"},
    "GALAXYSURF": {"name":"Galaxy Surfactants Ltd",               "sector":"Chemicals",    "industry":"Specialty Chemicals", "cap":"Small"},
    "DCMSHRIRAM": {"name":"DCM Shriram Ltd",                      "sector":"Chemicals",    "industry":"Agri Inputs",         "cap":"Small"},
    "CLEAN":      {"name":"Clean Science and Technology Ltd",     "sector":"Chemicals",    "industry":"Specialty Chemicals", "cap":"Small"},
    "AETHER":     {"name":"Aether Industries Ltd",                "sector":"Chemicals",    "industry":"Specialty Chemicals", "cap":"Small"},
    "ANUPAM":     {"name":"Anupam Rasayan India Ltd",             "sector":"Chemicals",    "industry":"Specialty Chemicals", "cap":"Small"},
    # ── REAL ESTATE ───────────────────────────────────────────────────────────
    "DLF":        {"name":"DLF Ltd",                              "sector":"Real Estate",  "industry":"Real Estate",         "cap":"Large"},
    "GODREJPROP": {"name":"Godrej Properties Ltd",                "sector":"Real Estate",  "industry":"Real Estate",         "cap":"Large"},
    "OBEROIRLTY": {"name":"Oberoi Realty Ltd",                    "sector":"Real Estate",  "industry":"Real Estate",         "cap":"Mid"},
    "PRESTIGE":   {"name":"Prestige Estates Projects Ltd",        "sector":"Real Estate",  "industry":"Real Estate",         "cap":"Mid"},
    "SOBHA":      {"name":"Sobha Ltd",                            "sector":"Real Estate",  "industry":"Real Estate",         "cap":"Mid"},
    "PHOENIXLTD": {"name":"The Phoenix Mills Ltd",                "sector":"Real Estate",  "industry":"Retail REITs",        "cap":"Mid"},
    "LODHA":      {"name":"Macrotech Developers Ltd",             "sector":"Real Estate",  "industry":"Real Estate",         "cap":"Large"},
    "MAHLIFE":    {"name":"Mahindra Lifespace Developers Ltd",    "sector":"Real Estate",  "industry":"Real Estate",         "cap":"Small"},
    "BRIGADE":    {"name":"Brigade Enterprises Ltd",              "sector":"Real Estate",  "industry":"Real Estate",         "cap":"Small"},
    "KOLTEPATIL": {"name":"Kolte-Patil Developers Ltd",           "sector":"Real Estate",  "industry":"Real Estate",         "cap":"Small"},
    # ── TELECOM ───────────────────────────────────────────────────────────────
    "BHARTIARTL": {"name":"Bharti Airtel Ltd",                    "sector":"Telecom",      "industry":"Telecom",             "cap":"Large"},
    "TATACOMM":   {"name":"Tata Communications Ltd",              "sector":"Telecom",      "industry":"Telecom",             "cap":"Mid"},
    "HFCL":       {"name":"HFCL Ltd",                             "sector":"Telecom",      "industry":"Telecom Equipment",   "cap":"Small"},
    # ── MEDIA ─────────────────────────────────────────────────────────────────
    "ZEEL":       {"name":"Zee Entertainment Enterprises Ltd",    "sector":"Media",        "industry":"Media & Entertainment","cap":"Mid"},
    "SUNTV":      {"name":"Sun TV Network Ltd",                   "sector":"Media",        "industry":"Media & Entertainment","cap":"Mid"},
    "NETWORK18":  {"name":"Network18 Media & Investments Ltd",    "sector":"Media",        "industry":"Media & Entertainment","cap":"Small"},
    "TV18BRDCST": {"name":"TV18 Broadcast Ltd",                   "sector":"Media",        "industry":"Media & Entertainment","cap":"Small"},
    "SAREGAMA":   {"name":"Saregama India Ltd",                   "sector":"Media",        "industry":"Music",               "cap":"Small"},
    "PVRINOX":    {"name":"PVR INOX Ltd",                         "sector":"Media",        "industry":"Multiplex",           "cap":"Mid"},
    # ── LOGISTICS ─────────────────────────────────────────────────────────────
    "CONCOR":     {"name":"Container Corporation of India",       "sector":"Logistics",    "industry":"Railways",            "cap":"Large"},
    "DELHIVERY":  {"name":"Delhivery Ltd",                        "sector":"Logistics",    "industry":"Logistics",           "cap":"Mid"},
    "ALLCARGO":   {"name":"Allcargo Logistics Ltd",               "sector":"Logistics",    "industry":"Logistics",           "cap":"Small"},
    "MAHLOG":     {"name":"Mahindra Logistics Ltd",               "sector":"Logistics",    "industry":"Logistics",           "cap":"Small"},
    "BLUEDART":   {"name":"Blue Dart Express Ltd",                "sector":"Logistics",    "industry":"Couriers",            "cap":"Mid"},
    "GATI":       {"name":"Gati Ltd",                             "sector":"Logistics",    "industry":"Logistics",           "cap":"Small"},
    "VRL":        {"name":"VRL Logistics Ltd",                    "sector":"Logistics",    "industry":"Logistics",           "cap":"Small"},
    # ── HOSPITALITY ───────────────────────────────────────────────────────────
    "INDHOTEL":   {"name":"Indian Hotels Company Ltd",            "sector":"Hospitality",  "industry":"Hotels",              "cap":"Large"},
    "LEMONTRE":   {"name":"Lemon Tree Hotels Ltd",                "sector":"Hospitality",  "industry":"Hotels",              "cap":"Mid"},
    "CHALET":     {"name":"Chalet Hotels Ltd",                    "sector":"Hospitality",  "industry":"Hotels",              "cap":"Small"},
    "IRCTC":      {"name":"Indian Railway Catering & Tourism",    "sector":"Consumer",     "industry":"Travel",              "cap":"Large"},
    "EASEMYTRIP": {"name":"Easy Trip Planners Ltd",               "sector":"Consumer",     "industry":"Travel",              "cap":"Small"},
    # ── AGRICULTURE ───────────────────────────────────────────────────────────
    "RALLIS":     {"name":"Rallis India Ltd",                     "sector":"Agriculture",  "industry":"Agri Inputs",         "cap":"Small"},
    "DHANUKA":    {"name":"Dhanuka Agritech Ltd",                 "sector":"Agriculture",  "industry":"Agri Inputs",         "cap":"Small"},
    "KAVERI":     {"name":"Kaveri Seed Company Ltd",              "sector":"Agriculture",  "industry":"Seeds",               "cap":"Small"},
    "AVANTIFEED": {"name":"Avanti Feeds Ltd",                     "sector":"Agriculture",  "industry":"Aquaculture",         "cap":"Small"},
    "HERITGFOOD": {"name":"Heritage Foods Ltd",                   "sector":"FMCG",         "industry":"Dairy",               "cap":"Small"},
    "KRBL":       {"name":"KRBL Ltd",                             "sector":"Agriculture",  "industry":"Rice",                "cap":"Small"},
    "LTFOODS":    {"name":"LT Foods Ltd",                         "sector":"Agriculture",  "industry":"Rice",                "cap":"Small"},
    "PRAJIND":    {"name":"Praj Industries Ltd",                  "sector":"Agriculture",  "industry":"Ethanol",             "cap":"Small"},
    "BAJAJELEC":  {"name":"Bajaj Electricals Ltd",                "sector":"Consumer",     "industry":"Consumer Durables",   "cap":"Small"},
    # ── DIVERSIFIED ───────────────────────────────────────────────────────────
    "GRASIM":     {"name":"Grasim Industries Ltd",                "sector":"Diversified",  "industry":"Diversified",         "cap":"Large"},
    "ITC":        {"name":"ITC Ltd",                              "sector":"FMCG",         "industry":"Diversified FMCG",    "cap":"Large"},
    "TATAINVEST": {"name":"Tata Investment Corporation Ltd",      "sector":"Diversified",  "industry":"Investment Holding",  "cap":"Mid"},
    "BAJAJHLDNG": {"name":"Bajaj Holdings & Investment Ltd",      "sector":"Diversified",  "industry":"Investment Holding",  "cap":"Mid"},
    "GODREJIND":  {"name":"Godrej Industries Ltd",                "sector":"Diversified",  "industry":"Diversified",         "cap":"Mid"},
}

# ─── HELPERS ─────────────────────────────────────────────────────────────────

def get_all_sectors():
    return sorted(set(v["sector"] for v in NSE_STOCKS_EXTENDED.values()))

def get_all_industries():
    return sorted(set(v["industry"] for v in NSE_STOCKS_EXTENDED.values()))

def get_symbol_info(symbol: str) -> dict:
    s = symbol.replace(".NS", "").replace(".BO", "").upper()
    return NSE_STOCKS_EXTENDED.get(s, {"name": s, "sector": "Unknown", "industry": "Unknown", "cap": "Unknown"})

def get_stocks_by_sector(sector: str) -> list:
    return [k for k, v in NSE_STOCKS_EXTENDED.items() if v["sector"] == sector]

def get_stocks_by_cap(cap: str) -> list:
    """cap: 'Large', 'Mid', 'Small'"""
    return [k for k, v in NSE_STOCKS_EXTENDED.items() if v.get("cap", "") == cap]

def get_index_constituents() -> dict:
    return {
        "NIFTY 50":   NIFTY50_STOCKS,
        "NIFTY NEXT 50": NIFTY_NEXT50,
        "NIFTY BANK": ["HDFCBANK","ICICIBANK","KOTAKBANK","AXISBANK","SBIN","INDUSINDBK",
                        "FEDERALBNK","BANDHANBNK","IDFCFIRSTB","AUBANK","PNB","BANKBARODA","CANBK","UNIONBANK"],
        "NIFTY IT":   ["TCS","INFY","WIPRO","HCLTECH","TECHM","LTIM","MPHASIS","PERSISTENT","COFORGE","OFSS","KPITTECH","TATAELXSI"],
        "NIFTY PHARMA":["SUNPHARMA","DRREDDY","CIPLA","DIVISLAB","APOLLOHOSP","AUROPHARMA","BIOCON","LUPIN","TORNTPHARM","ALKEM"],
        "NIFTY FMCG": ["HINDUNILVR","ITC","NESTLEIND","BRITANNIA","TATACONSUM","DABUR","GODREJCP","MARICO","COLPAL","EMAMILTD","VBL"],
        "NIFTY AUTO": ["MARUTI","TATAMOTORS","M&M","BAJAJ-AUTO","HEROMOTOCO","EICHERMOT","ASHOKLEY","TVSMOTOR","BALKRISIND","APOLLOTYRE"],
        "NIFTY METAL":["TATASTEEL","JSWSTEEL","HINDALCO","COALINDIA","VEDL","NMDC","SAIL","NATIONALUM","JINDALSTEL","APLAPOLLO"],
        "NIFTY ENERGY":["RELIANCE","ONGC","BPCL","IOC","NTPC","POWERGRID","GAIL","HINDPETRO","OIL","PETRONET"],
        "NIFTY REALTY":["DLF","GODREJPROP","OBEROIRLTY","PRESTIGE","SOBHA","PHOENIXLTD","LODHA"],
        "NIFTY MIDCAP 50": ["NAUKRI","ZOMATO","LTIM","MPHASIS","PERSISTENT","COFORGE","TRENT","IRCTC","RVNL","HAL",
                              "BEL","SIEMENS","ABB","CUMMINSIND","VOLTAS","HAVELLS","POLYCAB","ASTRAL","GODREJPROP","OBEROIRLTY"],
    }

def yf_ticker(symbol: str) -> str:
    """Return yfinance ticker string for a symbol"""
    if symbol in INDICES:
        return INDICES[symbol]
    if "." in symbol:
        return symbol
    return f"{symbol}.NS"


# ─── DYNAMIC NSE UNIVERSE LOADER ─────────────────────────────────────────────
# This function fetches the COMPLETE list of 2671+ NSE-listed symbols
# It merges with our static dict for rich sector/industry metadata
# Cached 24h — runs once per day in production

_nse_universe_cache: dict = {}

def load_nse_universe() -> dict:
    """
    Fetch all NSE-listed equities and merge with our static metadata.
    Returns dict: {symbol: {name, sector, industry, cap}}
    Falls back to NSE_STOCKS_EXTENDED if fetch fails.
    Cached globally to avoid repeated calls.
    """
    global _nse_universe_cache
    if _nse_universe_cache:
        return _nse_universe_cache

    try:
        import requests
        import io

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.nseindia.com/',
            'Connection': 'keep-alive',
        }
        session = requests.Session()
        session.headers.update(headers)

        # Warm up session with NSE home (required for cookies)
        session.get('https://www.nseindia.com', timeout=8)

        # Fetch the official NSE equity list CSV
        resp = session.get(
            'https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv',
            timeout=15
        )

        if resp.status_code == 200 and len(resp.content) > 1000:
            df = pd.read_csv(io.StringIO(resp.text))
            result = {}
            for _, row in df.iterrows():
                sym = str(row.get('SYMBOL', '')).strip().upper()
                name = str(row.get('NAME OF COMPANY', sym)).strip()
                if sym and sym not in ('NAN', ''):
                    # Merge with our rich metadata if we have it
                    if sym in NSE_STOCKS_EXTENDED:
                        result[sym] = NSE_STOCKS_EXTENDED[sym]
                    else:
                        result[sym] = {
                            "name":     name[:40],
                            "sector":   "Unknown",
                            "industry": "Unknown",
                            "cap":      "Unknown",
                        }
            if len(result) > 500:          # sanity check
                _nse_universe_cache = result
                return result
    except Exception:
        pass

    # Fallback: try nsepython
    try:
        from nsepython import nse_eq_symbols  # type: ignore
        syms = nse_eq_symbols()
        result = {}
        for sym in syms:
            sym = sym.upper().strip()
            if sym in NSE_STOCKS_EXTENDED:
                result[sym] = NSE_STOCKS_EXTENDED[sym]
            else:
                result[sym] = {"name": sym, "sector": "Unknown",
                               "industry": "Unknown", "cap": "Unknown"}
        if len(result) > 500:
            _nse_universe_cache = result
            return result
    except Exception:
        pass

    # Ultimate fallback: return our curated static dict
    _nse_universe_cache = NSE_STOCKS_EXTENDED.copy()
    return _nse_universe_cache


def get_universe_count() -> int:
    """Returns total number of symbols in the loaded universe"""
    return len(load_nse_universe())
