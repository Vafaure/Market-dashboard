import yfinance as yf
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import requests
import io
import matplotlib.pyplot as plt
from fpdf import FPDF
import tempfile
import os
import concurrent.futures

st.set_page_config(layout="wide", page_title="Market dashboard")

# Session State Initialization and Query Parameter Handling
TAPE_TICKERS_MAP = {
    "^GSPC": ("Index", "S&P 500 (^GSPC)"),
    "^FCHI": ("Index", "CAC 40 (^FCHI)"),
    "^VIX": ("Index", "VIX (^VIX)"),
    "EURUSD=X": ("Forex", "EUR/USD (EURUSD=X)"),
    "GC=F": ("Commodity", "Gold (GC=F)"),
    "BZ=F": ("Commodity", "Crude Oil Brent (BZ=F)")
}

if "equity_sel" not in st.session_state:
    st.session_state["equity_sel"] = ["Apple (AAPL)"]
if "commodity_sel" not in st.session_state:
    st.session_state["commodity_sel"] = ["Crude Oil WTI (CL=F)", "Gold (GC=F)"]
if "index_sel" not in st.session_state:
    st.session_state["index_sel"] = ["S&P 500 (^GSPC)"]
if "forex_sel" not in st.session_state:
    st.session_state["forex_sel"] = []

select_ticker_param = st.query_params.get("select_ticker")
if select_ticker_param:
    st.query_params.clear()
    if select_ticker_param in TAPE_TICKERS_MAP:
        category, full_name = TAPE_TICKERS_MAP[select_ticker_param]
        st.session_state["equity_sel"] = []
        st.session_state["commodity_sel"] = []
        st.session_state["index_sel"] = []
        st.session_state["forex_sel"] = []
        
        if category == "Equity":
            st.session_state["equity_sel"] = [full_name]
        elif category == "Commodity":
            st.session_state["commodity_sel"] = [full_name]
        elif category == "Index":
            st.session_state["index_sel"] = [full_name]
        elif category == "Forex":
            st.session_state["forex_sel"] = [full_name]

# Force full width, custom font, and sleek tabs
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 0rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 100%;
    }
    /* Sleeker tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        padding-top: 10px;
    /* Compact metrics */
    [data-testid="stMetric"] {
        padding: 8px 12px !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.3rem !important;
    }
    [data-testid="stMetric"] canvas {
        max-height: 40px !important;
    }
    /* Clean Table Headers */
    thead tr th {
        background-color: rgba(140, 120, 81, 0.1) !important;
        color: #1a1a1a !important;
        border-bottom: 2px solid #8c7851 !important;
    }
    tbody tr th {
        background-color: transparent !important;
    }
    /* Hide native Streamlit 'Running...' spinner */
    [data-testid="stStatusWidget"] {
        visibility: hidden;
    }
    /* Disable the gray 'stale' effect when rerunning */
    [data-testid="stElementContainer"], 
    [data-testid="stMarkdownContainer"], 
    [data-testid="stBlock"], 
    [data-testid="stVerticalBlock"] {
        opacity: 1 !important;
        transition: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

##### DICT #####

period_offset_dict = {
    "1 Month": pd.DateOffset(months=1),
    "3 Months": pd.DateOffset(months=3),
    "6 Months": pd.DateOffset(months=6),
    "1 Year": pd.DateOffset(years=1),
    "5 Years": pd.DateOffset(years=5),
    "10 Years": pd.DateOffset(years=10),
    "20 Years": pd.DateOffset(years=20),
    "Max": None
}

period_yf_dict = {
    "1 Month": "1mo",
    "3 Months": "3mo",
    "6 Months": "6mo",
    "1 Year": "1y",
    "5 Years": "5y",
    "10 Years": "10y",
    "20 Years": "max",
    "Max": "max"
}


ASSETS = {
    "Equity": {
        "Apple (AAPL)": "AAPL",
        "Microsoft (MSFT)": "MSFT",
        "Alphabet (GOOGL)": "GOOGL",
        "Amazon (AMZN)": "AMZN",
        "Tesla (TSLA)": "TSLA",
        "Meta (META)": "META",
        "Nvidia (NVDA)": "NVDA",
        "Berkshire Hathaway (BRK-B)": "BRK-B",
        "Johnson & Johnson (JNJ)": "JNJ",
        "Visa (V)": "V",
        "Walmart (WMT)": "WMT",
        "JPMorgan Chase (JPM)": "JPM",
        "Procter & Gamble (PG)": "PG",
        "Disney (DIS)": "DIS",
        "Netflix (NFLX)": "NFLX",
        "Mastercard (MA)": "MA",
        "UnitedHealth (UNH)": "UNH",
        "Home Depot (HD)": "HD",
        "Coca-Cola (KO)": "KO",
        "PepsiCo (PEP)": "PEP"
    },
    "Commodity": {
        "Crude Oil WTI (CL=F)": "CL=F",
        "Crude Oil Brent (BZ=F)": "BZ=F",
        "Natural Gas (NG=F)": "NG=F",
        "Gold (GC=F)": "GC=F",
        "Silver (SI=F)": "SI=F",
        "Copper (HG=F)": "HG=F",
        "Corn (ZC=F)": "ZC=F",
        "Wheat (ZW=F)": "ZW=F",
        "Soybeans (ZS=F)": "ZS=F",
        "Coffee (KC=F)": "KC=F"
    },
    "Index": {
        "S&P 500 (^GSPC)": "^GSPC",
        "Dow Jones (^DJI)": "^DJI",
        "NASDAQ 100 (^NDX)": "^NDX",
        "VIX (^VIX)": "^VIX",
        "CAC 40 (^FCHI)": "^FCHI",
        "DAX (^GDAXI)": "^GDAXI",
        "Nikkei 225 (^N225)": "^N225"
    },
    "Forex": {
        "EUR/USD (EURUSD=X)": "EURUSD=X",
        "USD/JPY (JPY=X)": "JPY=X",
        "GBP/USD (GBPUSD=X)": "GBPUSD=X",
        "USD/CHF (CHF=X)": "CHF=X",
        "AUD/USD (AUDUSD=X)": "AUDUSD=X",
        "USD/CAD (CAD=X)": "CAD=X"
    }
}



ECB_MATURITIES = {
    "3M": "SR_3M",
    "6M": "SR_6M",
    "1Y": "SR_1Y",
    "2Y": "SR_2Y",
    "3Y": "SR_3Y",
    "5Y": "SR_5Y",
    "7Y": "SR_7Y",
    "10Y": "SR_10Y",
    "15Y": "SR_15Y",
    "20Y": "SR_20Y",
    "30Y": "SR_30Y"
}

FRED_US_YIELDS = {
    "1M": "DGS1MO",
    "3M": "DGS3MO",
    "6M": "DGS6MO",
    "1Y": "DGS1",
    "2Y": "DGS2",
    "3Y": "DGS3",
    "5Y": "DGS5",
    "7Y": "DGS7",
    "10Y": "DGS10",
    "20Y": "DGS20",
    "30Y": "DGS30"
}

ECB_GOVIES_10Y = {
    "🇩🇪 Germany": "DE",
    "🇫🇷 France": "FR",
    "🇮🇹 Italy": "IT",
    "🇪🇸 Spain": "ES",
    "🇳🇱 Netherlands": "NL",
    "🇧🇪 Belgium": "BE",
    "🇦🇹 Austria": "AT",
    "🇬🇷 Greece": "GR",
    "🇵🇹 Portugal": "PT",
    "🇮🇪 Ireland": "IE",
    "🇫🇮 Finland": "FI"
}


##### FUNCTIONS #####

@st.cache_data(ttl=900)
def fetch_top_news():
    # Tickers for US, Europe, and Asia
    tickers = ["^GSPC", "^STOXX50E", "^N225"]
    parsed_news = []
    seen_titles = set()
    
    for t in tickers:
        try:
            news_items = yf.Ticker(t).news
            if news_items:
                for item in news_items[:3]:
                    content = item.get("content") or {}
                    title = content.get("title") or "No Title"
                    
                    if title in seen_titles or title == "No Title":
                        continue
                        
                    seen_titles.add(title)
                    click_info = content.get("clickThroughUrl")
                    url = click_info.get("url") if click_info and isinstance(click_info, dict) else "#"
                    parsed_news.append({"title": title, "url": url})
        except Exception:
            pass
            
    # Return top 6 items total
    return parsed_news[:6]


@st.cache_data(ttl=3600)
def fetch_yfinance_data(tickers, period="max"):
    tickers_list = list(tickers)
    yfinance_data = yf.download(tickers_list, period=period, progress=False)["Close"].ffill().dropna()
    rename_map = {}
    for category, assets in ASSETS.items():
        for name_displayed, ticker in assets.items():
            rename_map[ticker] = name_displayed
    yfinance_data = yfinance_data.rename(columns=rename_map)
    return yfinance_data


def plot_yfinance_data (yfinance_data, tickers, logscale):
    yfinance_data_norm = yfinance_data / yfinance_data.iloc[0]
    if len(tickers) == 1:
        yfinance_fig = px.line(yfinance_data, 
                               render_mode="webgl",
                               x=yfinance_data.index, 
                               y=yfinance_data.columns, 
                               log_y=logscale,
                               template="plotly_white")
    else:
        yfinance_fig = px.line(yfinance_data_norm,
                               render_mode="webgl",
                               x=yfinance_data_norm.index, 
                               y=yfinance_data_norm.columns, 
                               log_y=logscale,
                               template="plotly_white")
        yfinance_fig.update_yaxes(tickformat=".0%")
        yfinance_fig.update_layout(hovermode='x')
        
    yfinance_fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    return yfinance_fig


def metrics_yfinance_data(yfinance_data):
    st.markdown("""
    <style>
    [data-testid="stMetricValue"] {
        font-size: 1.6rem !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 1.0rem !important;
    }
    [data-testid="stMetricDelta"] {
        font-size: 0.85rem !important;
    }
    </style>
    """, unsafe_allow_html=True)
    columns = yfinance_data.columns  
    last_price = yfinance_data.iloc[-1]
    delta = (yfinance_data.iloc[-1] / yfinance_data.iloc[0] - 1) * 100 
    for i in range(0, len(columns), 5):
        cols = st.columns(5)
        batch_cols = columns[i : i + 5]  
        for j, col_name in enumerate(batch_cols):
            with cols[j]:
                st.metric(
                    label=col_name,
                    value=f"${last_price[col_name]:,.2f}",
                    delta=f"{delta[col_name]:,.2f} %",
                    chart_data=round(
                        (yfinance_data[col_name] / yfinance_data[col_name].iloc[0] - 1) * 100,
                        2),
                    chart_type="area",
                    border=True)

def get_ticker(equity_choice,commodity_choice,index_choice,forex_choice):
    tickers = ([ASSETS["Equity"][name] for name in equity_choice] +
              [ASSETS["Commodity"][name] for name in commodity_choice] +
              [ASSETS["Index"][name] for name in index_choice] +
              [ASSETS["Forex"][name] for name in forex_choice])
    return tickers


def yfinance_data_correlation(yfinance_data):
    correlation_data = yfinance_data.corr()
    correlation_fig = px.imshow(correlation_data, text_auto=True, color_continuous_scale="RdYlGn",
                     zmin=-1, zmax=1, template="plotly_white")
    correlation_fig.update_xaxes(side="top", title=None)
    correlation_fig.update_yaxes(title=None)
    correlation_fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    return correlation_fig


def plot_volatility(yfinance_data):
    log_returns = np.log(yfinance_data / yfinance_data.shift(1))
    volatility = round(log_returns.std() * np.sqrt(252) * 100, 2)
    
    vol_df = volatility.reset_index()
    vol_df.columns = ["Asset", "Volatility (%)"]
    vol_df = vol_df.sort_values(by="Volatility (%)", ascending=True)
    
    fig = px.bar(vol_df, 
                 x="Volatility (%)", 
                 y="Asset", 
                 orientation='h',
                 title="Historic Volatility (Annualized)",
                 text="Volatility (%)",
                 color="Volatility (%)",
                 color_continuous_scale="Reds",
                 template="plotly_white")
    fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    fig.update_layout(xaxis_title="Annualized Volatility (%)", yaxis_title="Asset", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    return fig




@st.cache_data(ttl=3600)
def fetch_ecb_yield_curve():
    start = (pd.Timestamp.today() - pd.DateOffset(years=10)).strftime("%Y-%m-%d")
    maturities_str = "+".join(ECB_MATURITIES.values())
    url = (f"https://data-api.ecb.europa.eu/service/data/YC/"
           f"B.U2.EUR.4F.G_N_A.SV_C_YM.{maturities_str}"
           f"?format=csvdata&startPeriod={start}")
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text))
    reverse_map = {v: k for k, v in ECB_MATURITIES.items()}
    df["Maturity"] = df["DATA_TYPE_FM"].map(reverse_map)
    df["OBS_VALUE"] = pd.to_numeric(df["OBS_VALUE"], errors="coerce")
    df["TIME_PERIOD"] = pd.to_datetime(df["TIME_PERIOD"])
    pivot = df.pivot_table(index="TIME_PERIOD", columns="Maturity",
                           values="OBS_VALUE")
    ordered_cols = [k for k in ECB_MATURITIES.keys() if k in pivot.columns]
    pivot = pivot[ordered_cols]
    return pivot


def plot_ecb_yield_curve_bar(ecb_data, ecb_rate_series):
    # Resample to Weekly to keep animation fluid and lightweight
    ecb_data_w = ecb_data.resample('W-FRI').last().dropna(how='all')
    ecb_rate_w = ecb_rate_series.resample('W-FRI').last().dropna()
    
    # Melt ECB Data
    df_melted = ecb_data_w.reset_index().melt(id_vars="TIME_PERIOD", var_name="Maturity", value_name="Yield (%)")
    df_melted = df_melted.rename(columns={"TIME_PERIOD": "Date"})
    
    # Create Deposit Rate Dataframe
    dep_df = pd.DataFrame({
        "Date": ecb_rate_w.index,
        "Maturity": "Deposit",
        "Yield (%)": ecb_rate_w.values
    })
    
    # Combine
    df_combined = pd.concat([dep_df, df_melted], ignore_index=True)
    df_combined["Date_str"] = df_combined["Date"].dt.strftime('%Y-%m-%d')
    
    # Order maturities correctly
    maturities_order = ["Deposit"] + list(ecb_data.columns)
    category_orders = {"Maturity": maturities_order}
    
    # Sort logically (not alphabetically) so the line connects properly
    df_combined["Maturity"] = pd.Categorical(df_combined["Maturity"], categories=maturities_order, ordered=True)
    df_combined = df_combined.sort_values(["Date", "Maturity"])
    
    # Stabilize Y-axis during animation
    y_min = df_combined["Yield (%)"].min() - 0.5
    y_max = df_combined["Yield (%)"].max() + 0.5
    
    fig = px.line(df_combined,
                 x="Maturity",
                 y="Yield (%)",
                 animation_frame="Date_str",
                 text="Yield (%)",
                 markers=True,
                 category_orders=category_orders,
                 range_y=[y_min, y_max],
                 title="Euro Area Yield Curve (Animated 10-Year History)",
                 template="plotly_white")
                 
    fig.update_traces(texttemplate="%{text:.2f}", textposition="top center")
    fig.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    
    # Speed up animation slightly
    if fig.layout.updatemenus:
        fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 150
        
    if fig.frames:
        for frame in fig.frames:
            frame_date_str = frame.name
            frame_date = pd.to_datetime(frame_date_str)
            
            is_inverted = False
            spread_val = 0.0
            if frame_date in ecb_data_w.index:
                y10 = ecb_data_w.loc[frame_date, '10Y']
                y2 = ecb_data_w.loc[frame_date, '2Y']
                if pd.notna(y10) and pd.notna(y2):
                    spread_val = y10 - y2
                    is_inverted = spread_val < 0
            
            color = "#ff2b2b" if is_inverted else "#00c04b"
            status_text = f"Inverted Curve (Spread 10Y-2Y: {spread_val:+.2f}%)" if is_inverted else f"Normal Curve (Spread 10Y-2Y: {spread_val:+.2f}%)"
            
            frame.data[0].update(line=dict(color=color))
            
            text_trace = go.Scatter(
                x=["3Y"],
                y=[y_max - 0.3],
                text=[status_text],
                mode="text",
                textfont=dict(color="#31333f", size=14, family="Inter, sans-serif"),
                showlegend=False
            )
            frame.data = (frame.data[0], text_trace)
            
        last_frame = fig.frames[-1]
        last_frame_date_str = last_frame.name
        last_frame_date = pd.to_datetime(last_frame_date_str)
        
        last_inverted = False
        last_spread = 0.0
        if last_frame_date in ecb_data_w.index:
            y10 = ecb_data_w.loc[last_frame_date, '10Y']
            y2 = ecb_data_w.loc[last_frame_date, '2Y']
            if pd.notna(y10) and pd.notna(y2):
                last_spread = y10 - y2
                last_inverted = last_spread < 0
        
        initial_color = "#ff2b2b" if last_inverted else "#00c04b"
        initial_status = f"Inverted Curve (Spread 10Y-2Y: {last_spread:+.2f}%)" if last_inverted else f"Normal Curve (Spread 10Y-2Y: {last_spread:+.2f}%)"
        
        for trace_idx in range(min(len(fig.data), len(last_frame.data))):
            fig.data[trace_idx].x = last_frame.data[trace_idx].x
            fig.data[trace_idx].y = last_frame.data[trace_idx].y
            if hasattr(last_frame.data[trace_idx], 'text'):
                fig.data[trace_idx].text = last_frame.data[trace_idx].text
            fig.data[trace_idx].update(line=dict(color=initial_color))
            
        fig.add_trace(go.Scatter(
            x=["3Y"],
            y=[y_max - 0.3],
            text=[initial_status],
            mode="text",
            textfont=dict(color="#31333f", size=14, family="Inter, sans-serif"),
            showlegend=False
        ))
        
        fig.update_layout(title="Euro Area Yield Curve (Animated 10-Year History)")
        
        if fig.layout.sliders:
            fig.layout.sliders[0].active = len(fig.frames) - 1

    return fig


def plot_ecb_yield_curve_line(ecb_data):
    fig = px.line(ecb_data,
                 render_mode="webgl",
                  x=ecb_data.index,
                  y=ecb_data.columns,
                  title="Euro Area Yields over time")
    fig.update_layout(xaxis_title="Date",
                      yaxis_title="Yield (%)",
                      hovermode="x")
    return fig


@st.cache_data(ttl=3600)
def fetch_ecb_govies_10y():
    start = (pd.Timestamp.today() - pd.DateOffset(months=6)).strftime("%Y-%m-%d")
    country_codes = "+".join(ECB_GOVIES_10Y.values())
    url = (f"https://data-api.ecb.europa.eu/service/data/IRS/"
           f"M.{country_codes}.L.L40.CI.0000.EUR.N.Z"
           f"?format=csvdata&startPeriod={start}")
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text))
    reverse_map = {v: k for k, v in ECB_GOVIES_10Y.items()}
    df["Country"] = df["REF_AREA"].map(reverse_map)
    df["OBS_VALUE"] = pd.to_numeric(df["OBS_VALUE"], errors="coerce")
    df["TIME_PERIOD"] = pd.to_datetime(df["TIME_PERIOD"])
    pivot = df.pivot_table(index="TIME_PERIOD", columns="Country",
                           values="OBS_VALUE")
    ordered_cols = [k for k in ECB_GOVIES_10Y.keys() if k in pivot.columns]
    pivot = pivot[ordered_cols]
    return pivot


@st.cache_data(ttl=3600)
def fetch_ecb_policy_rate():
    start = (pd.Timestamp.today() - pd.DateOffset(years=10)).strftime("%Y-%m-%d")
    url = f"https://data-api.ecb.europa.eu/service/data/FM/D.U2.EUR.4F.KR.DFR.LEV?format=csvdata&startPeriod={start}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text))
    df["TIME_PERIOD"] = pd.to_datetime(df["TIME_PERIOD"])
    return df.set_index("TIME_PERIOD")["OBS_VALUE"]


@st.cache_data(ttl=3600)
def fetch_us_treasury_yield_curve():
    current_year = pd.Timestamp.today().year
    years = list(range(current_year - 10, current_year + 1))
    def fetch_year(year):
        url = f"https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{year}/all?type=daily_treasury_yield_curve&field_tdr_date_value={year}&page&_format=csv"
        try:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            if resp.status_code == 200:
                return pd.read_csv(io.StringIO(resp.text))
        except Exception:
            pass
        return None

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(fetch_year, years)
    
    dfs = [df for df in results if df is not None]
            
    if dfs:
        df = pd.concat(dfs, ignore_index=True)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date").sort_index()
        maturities = ['1 Mo', '2 Mo', '3 Mo', '4 Mo', '6 Mo', '1 Yr', '2 Yr', '3 Yr', '5 Yr', '7 Yr', '10 Yr', '20 Yr', '30 Yr']
        existing_mats = [m for m in maturities if m in df.columns]
        df = df[existing_mats]
        
        # Convert all to numeric (handles "N/A" strings in the CSV)
        for col in existing_mats:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            
        return df
    return pd.DataFrame()


@st.cache_data(ttl=3600)
def fetch_fed_policy_rate():
    end_date = pd.Timestamp.today().strftime("%Y-%m-%d")
    start_date = (pd.Timestamp.today() - pd.DateOffset(years=11)).strftime("%Y-%m-%d")
    url = f"https://markets.newyorkfed.org/api/rates/unsecured/effr/search.json?startDate={start_date}&endDate={end_date}"
    resp = requests.get(url, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        rates = data.get("refRates", [])
        if rates:
            df = pd.DataFrame(rates)
            df["effectiveDate"] = pd.to_datetime(df["effectiveDate"])
            df = df.set_index("effectiveDate").sort_index()
            return df["percentRate"]
    return pd.Series(dtype=float)


@st.cache_data(ttl=3600)
def fetch_ecb_inflation():
    start = (pd.Timestamp.today() - pd.DateOffset(years=10)).strftime("%Y-%m")
    url = (f"https://data-api.ecb.europa.eu/service/data/ICP/"
           f"M.U2.N.000000.4.ANR"
           f"?format=csvdata&startPeriod={start}")
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            df = pd.read_csv(io.StringIO(resp.text))
            df["TIME_PERIOD"] = pd.to_datetime(df["TIME_PERIOD"])
            df["OBS_VALUE"] = pd.to_numeric(df["OBS_VALUE"], errors="coerce")
            df = df.sort_values("TIME_PERIOD")
            df = df.set_index("TIME_PERIOD")
            return df["OBS_VALUE"]
    except Exception:
        pass
    return pd.Series(dtype=float)


@st.cache_data(ttl=3600)
def fetch_us_inflation():
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL"
    try:
        resp = requests.get(url, headers={"User-Agent": "curl/8.4.0"}, timeout=10)
        if resp.status_code == 200:
            df = pd.read_csv(io.StringIO(resp.text))
            date_col = "DATE" if "DATE" in df.columns else "observation_date"
            df[date_col] = pd.to_datetime(df[date_col])
            df["CPIAUCSL"] = pd.to_numeric(df["CPIAUCSL"], errors="coerce")
            df = df.sort_values(date_col).set_index(date_col)
            # Calculate YoY inflation (percent change over 12 months)
            inflation = df["CPIAUCSL"].pct_change(12) * 100
            # Keep last 10 years
            ten_years_ago = pd.Timestamp.today() - pd.DateOffset(years=10)
            inflation = inflation[inflation.index >= ten_years_ago].dropna()
            return inflation
    except Exception:
        pass
    return pd.Series(dtype=float)





@st.cache_data(ttl=3600)
def fetch_japan_yield_curve():
    url = "https://www.mof.go.jp/english/jgbs/reference/interest_rate/historical/jgbcme_all.csv"
    try:
        resp = requests.get(url, verify=False, timeout=10)
        df = pd.read_csv(io.StringIO(resp.content.decode('shift_jis', errors='ignore')), skiprows=1)
        df.rename(columns={"Date": "TIME_PERIOD"}, inplace=True)
        df = df.dropna(subset=["TIME_PERIOD"])
        df["TIME_PERIOD"] = pd.to_datetime(df["TIME_PERIOD"], errors='coerce')
        df = df.dropna(subset=["TIME_PERIOD"])
        df.set_index("TIME_PERIOD", inplace=True)
        yield_cols = [c for c in df.columns if c.endswith('Y')]
        df = df[yield_cols]
        for c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
        return df.dropna(how='all')
    except Exception as e:
        return pd.DataFrame()


def plot_japan_yield_curve(japan_data):
    if japan_data.empty:
        return px.line(title="Data not available")
        
    ten_years_ago = pd.Timestamp.today() - pd.DateOffset(years=10)
    japan_data_10y = japan_data[japan_data.index >= ten_years_ago]
        
    japan_data_w = japan_data_10y.resample('W-FRI').last().dropna(how='all')
    japan_data_w.index.name = "Date"
    
    df_melted = japan_data_w.reset_index().melt(id_vars="Date", var_name="Maturity", value_name="Yield (%)")
    df_melted["Date_str"] = df_melted["Date"].dt.strftime('%Y-%m-%d')
    df_combined = df_melted.dropna(subset=["Yield (%)"])
    
    maturities_order = list(japan_data.columns)
    category_orders = {"Maturity": maturities_order}
    
    df_combined["Maturity"] = pd.Categorical(df_combined["Maturity"], categories=maturities_order, ordered=True)
    df_combined = df_combined.sort_values(["Date", "Maturity"])
    
    y_min = df_combined["Yield (%)"].min() - 0.5
    y_max = df_combined["Yield (%)"].max() + 0.5
    
    fig = px.line(df_combined,
                 x="Maturity",
                 y="Yield (%)",
                 animation_frame="Date_str",
                 text="Yield (%)",
                 markers=True,
                 category_orders=category_orders,
                 range_y=[y_min, y_max],
                 title="Japan Yield Curve (Animated 10-Year History)",
                 template="plotly_white")
                 
    fig.update_traces(texttemplate="%{text:.2f}", textposition="top center")
    fig.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    
    if fig.layout.updatemenus:
        fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 150
        
    if fig.frames:
        last_frame = fig.frames[-1]
        for trace_idx in range(min(len(fig.data), len(last_frame.data))):
            fig.data[trace_idx].x = last_frame.data[trace_idx].x
            fig.data[trace_idx].y = last_frame.data[trace_idx].y
            if hasattr(last_frame.data[trace_idx], 'text'):
                fig.data[trace_idx].text = last_frame.data[trace_idx].text
        if fig.layout.sliders:
            fig.layout.sliders[0].active = len(fig.frames) - 1
            
    return fig


def plot_single_inflation(inflation_data, color, title_prefix="Inflation"):
    if inflation_data.empty:
        return px.line(title="Data not available")
    df = inflation_data.reset_index()
    df.columns = ["Date", "Inflation (%)"]
    latest_val = df["Inflation (%)"].iloc[-1]
    
    fig = px.bar(df, x="Date", y="Inflation (%)", template="plotly_white")
    fig.update_layout(
        title=f"{title_prefix} (Latest: {latest_val:.1f}%)",
        title_font=dict(size=16, color="#1a1a1a"),
        xaxis_title="", 
        yaxis_title="Inflation (%)", 
        showlegend=False, 
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=40, b=0), 
        height=300
    )
    
    fig.update_traces(marker_color=color)
    
    fig.add_hline(y=2.0, line_dash="dash", line_color="#00c04b", annotation_text="Target (2%)", annotation_position="top right")
    return fig


def plot_us_treasury_yield_curve(us_data, fed_rate_series):
    if us_data.empty or fed_rate_series.empty:
        return px.line(title="Data not available")
        
    # Resample to Weekly to keep animation fluid and lightweight
    us_data_w = us_data.resample('W-FRI').last().dropna(how='all')
    fed_rate_w = fed_rate_series.resample('W-FRI').last().dropna()
    
    # Align dates to avoid frames with only the Fed Rate
    common_dates = us_data_w.index.intersection(fed_rate_w.index)
    us_data_w = us_data_w.loc[common_dates]
    fed_rate_w = fed_rate_w.loc[common_dates]
    
    # Restaure the index name to "Date" in case the intersection stripped it
    us_data_w.index.name = "Date"
    
    # Melt US Data
    df_melted = us_data_w.reset_index().melt(id_vars="Date", var_name="Maturity", value_name="Yield (%)")
    
    # Create Fed Rate Dataframe
    fed_df = pd.DataFrame({
        "Date": fed_rate_w.index,
        "Maturity": "Fed Rate",
        "Yield (%)": fed_rate_w.values
    })
    
    # Combine and drop NaNs to ensure the line connects all available points
    df_combined = pd.concat([fed_df, df_melted], ignore_index=True).dropna(subset=["Yield (%)"])
    df_combined["Date_str"] = df_combined["Date"].dt.strftime('%Y-%m-%d')
    
    # Order maturities correctly
    maturities_order = ["Fed Rate"] + list(us_data.columns)
    category_orders = {"Maturity": maturities_order}
    
    # Sort logically so the line connects properly
    df_combined["Maturity"] = pd.Categorical(df_combined["Maturity"], categories=maturities_order, ordered=True)
    df_combined = df_combined.sort_values(["Date", "Maturity"])
    
    # Stabilize Y-axis during animation
    y_min = df_combined["Yield (%)"].min() - 0.5
    y_max = df_combined["Yield (%)"].max() + 0.5
    
    fig = px.line(df_combined,
                 x="Maturity",
                 y="Yield (%)",
                 animation_frame="Date_str",
                 text="Yield (%)",
                 markers=True,
                 category_orders=category_orders,
                 range_y=[y_min, y_max],
                 title="US Treasury Yield Curve (Animated 10-Year History)",
                 template="plotly_white")
                 
    fig.update_traces(texttemplate="%{text:.2f}", textposition="top center")
    fig.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    
    # Speed up animation slightly
    if fig.layout.updatemenus:
        fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 150
        
    # Set default to the last frame
    if fig.frames:
        for frame in fig.frames:
            frame_date_str = frame.name
            frame_date = pd.to_datetime(frame_date_str)
            
            is_inverted = False
            spread_val = 0.0
            if frame_date in us_data_w.index:
                y10 = us_data_w.loc[frame_date, '10 Yr']
                y2 = us_data_w.loc[frame_date, '2 Yr']
                if pd.notna(y10) and pd.notna(y2):
                    spread_val = y10 - y2
                    is_inverted = spread_val < 0
            
            color = "#ff2b2b" if is_inverted else "#00c04b"
            status_text = f"Inverted Curve (Spread 10Y-2Y: {spread_val:+.2f}%)" if is_inverted else f"Normal Curve (Spread 10Y-2Y: {spread_val:+.2f}%)"
            
            frame.data[0].update(line=dict(color=color))
            
            text_trace = go.Scatter(
                x=["3 Yr"],
                y=[y_max - 0.3],
                text=[status_text],
                mode="text",
                textfont=dict(color="#31333f", size=14, family="Inter, sans-serif"),
                showlegend=False
            )
            frame.data = (frame.data[0], text_trace)
            
        last_frame = fig.frames[-1]
        last_frame_date_str = last_frame.name
        last_frame_date = pd.to_datetime(last_frame_date_str)
        
        last_inverted = False
        last_spread = 0.0
        if last_frame_date in us_data_w.index:
            y10 = us_data_w.loc[last_frame_date, '10 Yr']
            y2 = us_data_w.loc[last_frame_date, '2 Yr']
            if pd.notna(y10) and pd.notna(y2):
                last_spread = y10 - y2
                last_inverted = last_spread < 0
        
        initial_color = "#ff2b2b" if last_inverted else "#00c04b"
        initial_status = f"Inverted Curve (Spread 10Y-2Y: {last_spread:+.2f}%)" if last_inverted else f"Normal Curve (Spread 10Y-2Y: {last_spread:+.2f}%)"
        
        for trace_idx in range(min(len(fig.data), len(last_frame.data))):
            fig.data[trace_idx].x = last_frame.data[trace_idx].x
            fig.data[trace_idx].y = last_frame.data[trace_idx].y
            if hasattr(last_frame.data[trace_idx], 'text'):
                fig.data[trace_idx].text = last_frame.data[trace_idx].text
            fig.data[trace_idx].update(line=dict(color=initial_color))
            
        fig.add_trace(go.Scatter(
            x=["3 Yr"],
            y=[y_max - 0.3],
            text=[initial_status],
            mode="text",
            textfont=dict(color="#31333f", size=14, family="Inter, sans-serif"),
            showlegend=False
        ))
        
        fig.update_layout(title="US Treasury Yield Curve (Animated 10-Year History)")
        
        if fig.layout.sliders:
            fig.layout.sliders[0].active = len(fig.frames) - 1
            
    return fig




@st.cache_data(ttl=300)
def fetch_global_market_data():
    tickers = ["^FCHI", "^GSPC", "BZ=F", "GC=F", "^VIX", "EURUSD=X", "JPY=X", "GBPUSD=X", "CHF=X", "EURGBP=X"]
    data = yf.download(tickers, period="1y", progress=False)["Close"].ffill()
    return data

def get_ticker_tape_html(global_data):
    tickers = {"S&P 500": "^GSPC", "CAC 40": "^FCHI", "VIX": "^VIX", "EUR/USD": "EURUSD=X", "Gold": "GC=F", "Brent": "BZ=F"}
    try:
        items = []
        for name, ticker in tickers.items():
            if ticker in global_data.columns:
                series = global_data[ticker].dropna()
                if len(series) >= 2:
                    latest = series.iloc[-1]
                    prev = series.iloc[-2]
                    pct_change = (latest - prev) / prev * 100
                    color = "#00c04b" if pct_change >= 0 else "#ff2b2b"
                    arrow = "▲" if pct_change >= 0 else "▼"
                    items.append(f"<a href='/?select_ticker={ticker}' target='_self' style='text-decoration: none; color: inherit; margin-right: 40px; font-family: sans-serif; display: inline-block;'><b>{name}</b> {latest:.2f} <span style='color: {color};'>{arrow} {abs(pct_change):.2f}%</span></a>")
        return " ".join(items)
    except:
        return ""


@st.cache_data(ttl=300)
def generate_pdf_recap(us_data, ecb_data, fed_rate_series, ecb_rate_series, govies_data, japan_data, global_data, eu_inflation, us_inflation):
    class CustomPDF(FPDF):
        def header(self):
            # Elegant Header
            self.set_fill_color(140, 120, 81) # #8c7851
            self.rect(0, 0, 210, 25, 'F')
            
            self.set_y(8)
            self.set_text_color(255, 255, 255)
            self.set_font("helvetica", "B", 18)
            self.cell(0, 10, "Market Dashboard Recap", align="C")
            
            self.set_text_color(0, 0, 0)
            self.set_y(30) # Fix title overlap

        def footer(self):
            self.set_y(-15)
            self.set_font("helvetica", "I", 8)
            self.set_text_color(128, 128, 128)
            now_str = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
            self.cell(0, 10, f"Prepared by Valentin Fauré - Market Dashboard | Generated at {now_str} | Page {self.page_no()}", align="C")

    tickers = ["^FCHI", "^GSPC", "BZ=F", "GC=F", "^VIX", "EURUSD=X", "JPY=X", "GBPUSD=X", "CHF=X", "EURGBP=X"]
    data = global_data
    
    latest_vals = {}
    deltas_30d = {}
    deltas_1y = {}
    
    for t in tickers:
        if t in data.columns:
            s = data[t].dropna()
            if not s.empty:
                latest = s.iloc[-1]
                latest_vals[t] = latest
                
                prev_1y = s.iloc[0]
                deltas_1y[t] = (latest - prev_1y) / prev_1y * 100 if prev_1y != 0 else 0
                
                prev_30d = s.iloc[-21] if len(s) >= 21 else s.iloc[0]
                deltas_30d[t] = (latest - prev_30d) / prev_30d * 100 if prev_30d != 0 else 0
            else:
                latest_vals[t] = 0.0
                deltas_30d[t] = 0.0
                deltas_1y[t] = 0.0
        else:
            latest_vals[t] = 0.0
            deltas_30d[t] = 0.0
            deltas_1y[t] = 0.0

    # Dynamic Commentary
    sp_30d_return = deltas_30d.get('^GSPC', 0)
    sp_comment = f"Equities show {'positive' if sp_30d_return >= 0 else 'negative'} momentum, with the S&P 500 {'up' if sp_30d_return >= 0 else 'down'} {abs(sp_30d_return):.1f}% over the past 30 days."
    
    us_latest = us_data.dropna(how='all').iloc[-1]
    y10 = us_latest.get('10 Yr', None)
    y2 = us_latest.get('2 Yr', None)
    
    if pd.notna(y10) and pd.notna(y2):
        if y10 < y2:
            curve_comment = "The US Treasury yield curve remains inverted, often viewed as an economic warning sign."
        else:
            curve_comment = "The US Treasury yield curve is positively sloped, reflecting normalized conditions."
    else:
        curve_comment = ""

    commentary = f"{sp_comment} {curve_comment}"

    # US Yield Curve
    plt.figure(figsize=(9, 2.5))
    fed_latest = fed_rate_series.dropna().iloc[-1]
    us_x = ["Fed Rate"] + list(us_latest.index)
    us_y = [fed_latest] + list(us_latest.values)
    
    plt.plot(us_x, us_y, marker='o', color='#004b87', linewidth=2, markersize=6)
    plt.fill_between(us_x, us_y, alpha=0.1, color='#004b87')
    
    us_y_clean = [y for y in us_y if pd.notna(y)]
    if us_y_clean:
        plt.ylim(min(us_y_clean) - 0.5, max(us_y_clean) + 0.8)
        
    for x_val, y_val in zip(us_x, us_y):
        if pd.notna(y_val):
            plt.annotate(f"{y_val:.2f}", (x_val, y_val), textcoords="offset points", xytext=(0,8), ha='center', fontsize=8, color='#004b87', fontweight='bold')
            
    plt.title("US Treasury Yield Curve", fontsize=12, fontweight='bold')
    plt.ylabel("Yield (%)")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.xticks(rotation=45)
    plt.tight_layout()
    us_img_buf = io.BytesIO()
    plt.savefig(us_img_buf, format='png', dpi=150)
    us_img_buf.seek(0)
    plt.close()

    # Euro Yield Curve
    plt.figure(figsize=(9, 2.5))
    ecb_latest = ecb_data.dropna(how='all').iloc[-1]
    depo_latest = ecb_rate_series.dropna().iloc[-1]
    ecb_x = ["Deposit"] + list(ecb_latest.index)
    ecb_y = [depo_latest] + list(ecb_latest.values)
    
    plt.plot(ecb_x, ecb_y, marker='o', color='#003399', linewidth=2, markersize=6)
    plt.fill_between(ecb_x, ecb_y, alpha=0.1, color='#003399')
    
    ecb_y_clean = [y for y in ecb_y if pd.notna(y)]
    if ecb_y_clean:
        plt.ylim(min(ecb_y_clean) - 0.5, max(ecb_y_clean) + 0.8)
        
    for x_val, y_val in zip(ecb_x, ecb_y):
        if pd.notna(y_val):
            plt.annotate(f"{y_val:.2f}", (x_val, y_val), textcoords="offset points", xytext=(0,8), ha='center', fontsize=8, color='#003399', fontweight='bold')

    plt.title("Euro Area Yield Curve", fontsize=12, fontweight='bold')
    plt.ylabel("Yield (%)")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.xticks(rotation=45)
    plt.tight_layout()
    ecb_img_buf = io.BytesIO()
    plt.savefig(ecb_img_buf, format='png', dpi=150)
    ecb_img_buf.seek(0)
    plt.close()

    # Japan Yield Curve
    plt.figure(figsize=(9, 2.5))
    japan_latest = japan_data.dropna(how='all').iloc[-1]
    jp_x = list(japan_latest.index)
    jp_y = list(japan_latest.values)
    
    plt.plot(jp_x, jp_y, marker='o', color='#cc0000', linewidth=2, markersize=6)
    plt.fill_between(jp_x, jp_y, alpha=0.1, color='#cc0000')
    
    jp_y_clean = [y for y in jp_y if pd.notna(y)]
    if jp_y_clean:
        plt.ylim(min(jp_y_clean) - 0.5, max(jp_y_clean) + 0.8)
        
    for x_val, y_val in zip(jp_x, jp_y):
        if pd.notna(y_val):
            plt.annotate(f"{y_val:.2f}", (x_val, y_val), textcoords="offset points", xytext=(0,8), ha='center', fontsize=8, color='#cc0000', fontweight='bold')
            
    plt.title("Japan Government Bond Yield Curve", fontsize=12, fontweight='bold')
    plt.ylabel("Yield (%)")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.xticks(rotation=45)
    plt.tight_layout()
    jp_img_buf = io.BytesIO()
    plt.savefig(jp_img_buf, format='png', dpi=150)
    jp_img_buf.seek(0)
    plt.close()

    pdf = CustomPDF()
    
    # --- COVER PAGE ---
    pdf.add_page()
    pdf.set_y(100)
    pdf.set_text_color(140, 120, 81)
    pdf.set_font("helvetica", "B", 32)
    pdf.cell(0, 15, "Global Macro", align="C", ln=True)
    pdf.cell(0, 15, "& Market Report", align="C", ln=True)
    pdf.set_text_color(100, 100, 100)
    pdf.set_font("helvetica", "I", 14)
    now_str = pd.Timestamp.now().strftime("%B %d, %Y")
    pdf.ln(10)
    pdf.cell(0, 10, f"Prepared on {now_str}", align="C", ln=True)
    pdf.cell(0, 10, "Author: Valentin Fauré", align="C", ln=True)
    
    # --- CONTENT PAGE 1 ---
    pdf.add_page()

    # Commentary
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(140, 120, 81)
    pdf.cell(0, 8, "Market Insight", ln=True)
    pdf.set_text_color(50, 50, 50)
    pdf.set_font("helvetica", "I", 10)
    pdf.multi_cell(0, 5, commentary)
    pdf.ln(2)

    def format_val(val, is_currency=False):
        prefix = "$" if is_currency else ""
        return f"{prefix}{val:,.2f}"

    def format_delta(delta):
        return f"{'+' if delta >= 0 else ''}{delta:.2f}%"

    def get_rgb_color(delta):
        return (0, 150, 0) if delta >= 0 else (200, 0, 0)

    # Tables side-by-side
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(140, 120, 81)
    pdf.cell(100, 8, "Latest Market Overview", ln=False)
    pdf.cell(90, 8, "Top Forex Pairs", ln=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(25, 8, "Asset", border="B")
    pdf.cell(25, 8, "Price", border="B", align="R")
    pdf.cell(20, 8, "30d", border="B", align="R")
    pdf.cell(20, 8, "1Y", border="B", align="R")
    
    pdf.cell(10, 8, "", border=0) # Spacer
    
    pdf.cell(25, 8, "Pair", border="B")
    pdf.cell(25, 8, "Price", border="B", align="R")
    pdf.cell(20, 8, "30d", border="B", align="R")
    pdf.cell(20, 8, "1Y", border="B", align="R", ln=True)
    
    pdf.set_font("helvetica", "", 10)
    
    assets_to_display = [
        ("CAC 40", "^FCHI", False),
        ("S&P 500", "^GSPC", False),
        ("Brent Crude", "BZ=F", True),
        ("Gold", "GC=F", True),
        ("VIX", "^VIX", False)
    ]
    fx_pairs = [
        ("EUR/USD", "EURUSD=X"),
        ("GBP/USD", "GBPUSD=X"),
        ("USD/JPY", "JPY=X"),
        ("USD/CHF", "CHF=X"),
        ("EUR/GBP", "EURGBP=X")
    ]
    
    for (name, ticker, is_curr), (fx_name, fx_ticker) in zip(assets_to_display, fx_pairs):
        val = latest_vals[ticker]
        d30 = deltas_30d[ticker]
        d1y = deltas_1y[ticker]
        
        # Left Table
        pdf.set_text_color(0, 0, 0)
        pdf.cell(25, 8, name, border="B")
        pdf.cell(25, 8, format_val(val, is_curr), border="B", align="R")
        
        pdf.set_text_color(*get_rgb_color(d30))
        pdf.cell(20, 8, format_delta(d30), border="B", align="R")
        
        pdf.set_text_color(*get_rgb_color(d1y))
        pdf.cell(20, 8, format_delta(d1y), border="B", align="R")
        
        pdf.set_text_color(0, 0, 0)
        pdf.cell(10, 8, "", border=0) # Spacer
        
        # Right Table
        if fx_name:
            fx_val = latest_vals[fx_ticker]
            fd30 = deltas_30d[fx_ticker]
            fd1y = deltas_1y[fx_ticker]
            
            pdf.cell(25, 8, fx_name, border="B")
            format_str = f"{fx_val:,.4f}" if fx_name != "USD/JPY" else f"{fx_val:,.2f}"
            pdf.cell(25, 8, format_str, border="B", align="R")
            
            pdf.set_text_color(*get_rgb_color(fd30))
            pdf.cell(20, 8, format_delta(fd30), border="B", align="R")
            
            pdf.set_text_color(*get_rgb_color(fd1y))
            pdf.cell(20, 8, format_delta(fd1y), border="B", align="R", ln=True)
            pdf.set_text_color(0, 0, 0)
        else:
            pdf.cell(25, 8, "", border="B")
            pdf.cell(25, 8, "", border="B", align="R")
            pdf.cell(20, 8, "", border="B", align="R")
            pdf.cell(20, 8, "", border="B", align="R", ln=True)

    # Govies
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(140, 120, 81)
    pdf.cell(0, 8, "Global 10Y Benchmarks", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "", 10)
    
    latest_eu = govies_data.dropna().iloc[-1]
    global_govies = {
        "US": us_data['10 Yr'].dropna().iloc[-1] if not us_data.empty else None,
        "DE": latest_eu.get("🇩🇪 Germany", None),
        "JP": japan_data['10Y'].dropna().iloc[-1] if not japan_data.empty else None,
        "FR": latest_eu.get("🇫🇷 France", None),
        "IT": latest_eu.get("🇮🇹 Italy", None),
    }
    
    govies_items = [(k, v) for k, v in global_govies.items() if v is not None]
    
    if govies_items:
        box_width = 190 / len(govies_items)
        for country, yield_val in govies_items:
            pdf.cell(box_width, 8, f"{country}: {yield_val:.2f}%", border=1, align="C")
    pdf.ln(10)

    # Policy Rates and Inflation
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(140, 120, 81)
    pdf.cell(0, 8, "Macroeconomic Snapshot", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "", 10)
    
    latest_fed = fed_rate_series.dropna().iloc[-1] if not fed_rate_series.empty else 0
    latest_ecb = ecb_rate_series.dropna().iloc[-1] if not ecb_rate_series.empty else 0
    latest_us_inf = us_inflation.iloc[-1] if not us_inflation.empty else 0
    latest_eu_inf = eu_inflation.iloc[-1] if not eu_inflation.empty else 0
    
    pdf.cell(45, 8, f"US Fed Rate: {latest_fed:.2f}%", border=1, align="C")
    pdf.cell(45, 8, f"US Inflation: {latest_us_inf:.1f}%", border=1, align="C")
    pdf.cell(50, 8, f"ECB Depo Rate: {latest_ecb:.2f}%", border=1, align="C")
    pdf.cell(50, 8, f"EU Inflation: {latest_eu_inf:.1f}%", border=1, align="C", ln=True)
    pdf.ln(8)

    pdf.ln(5)
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(140, 120, 81)
    pdf.cell(0, 8, "Yield Curves", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)
    
    pdf.image(us_img_buf, x=20, w=170)
    pdf.ln(2)
    pdf.image(ecb_img_buf, x=20, w=170)
    
    # Japan Curve - follows directly below on the same page
    pdf.ln(2)
    pdf.image(jp_img_buf, x=20, w=170)
    
    return bytes(pdf.output())


##### CODE #####

st.title("Market Dashboard")
st.markdown("""
    <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">
        <span style="font-size: 1.1em; font-weight: 500; color: #555;">By Valentin Fauré</span>
        <a href="https://www.linkedin.com/in/faure-valentin" target="_blank" style="text-decoration: none;">
            <div style="display: flex; align-items: center; justify-content: center; background-color: #0077b5; color: white; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 600; transition: 0.3s; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="14" height="14" fill="currentColor" style="margin-right: 6px;">
                    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                </svg>
                Connect on LinkedIn
            </div>
        </a>
    </div>
""", unsafe_allow_html=True)


global_data = fetch_global_market_data()
tape_content = get_ticker_tape_html(global_data)
if tape_content:
    # Duplicate the content a few times to ensure it covers wide screens
    repeated_content = " ".join([tape_content] * 4)
    st.markdown(f"""
        <style>
        .ticker-wrap {{
            overflow: hidden;
            background-color: rgba(128,128,128,0.1);
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
            display: flex;
            white-space: nowrap;
        }}
        .ticker-content {{
            animation: scroll-ticker 120s linear infinite;
            display: flex;
            flex-shrink: 0;
            font-size: 16px;
        }}
        /* Hover to pause */
        .ticker-wrap:hover .ticker-content {{
            animation-play-state: paused;
        }}
        .ticker-content a {{
            transition: color 0.2s, opacity 0.2s;
        }}
        .ticker-content a:hover {{
            opacity: 0.8;
            color: #8c7851 !important;
            text-decoration: underline !important;
        }}
        @keyframes scroll-ticker {{
            0% {{ transform: translateX(0); }}
            100% {{ transform: translateX(-100%); }}
        }}
        </style>
        <div class="ticker-wrap" title="Hover to pause - Click to view details">
            <div class="ticker-content">
                {repeated_content}
            </div>
            <div class="ticker-content">
                {repeated_content}
            </div>
        </div>
    """, unsafe_allow_html=True)
col1, col2 = st.columns([1,3])

with col1:
    with st.container(border=True):
        st.markdown("#### Parameters")
        period_choice = st.pills("Period", 
                                 period_offset_dict.keys(),
                                 default="1 Year")
        period_offset = period_offset_dict[period_choice]

        equity_choice = st.multiselect("Equity", 
                                       ASSETS["Equity"].keys(), 
                                       key="equity_sel")
        commodity_choice = st.multiselect("Commodity", 
                                          ASSETS["Commodity"].keys(),
                                          key="commodity_sel")
        index_choice = st.multiselect("Index",
                                      ASSETS["Index"].keys(),
                                      key="index_sel")
        forex_choice = st.multiselect("Forex", 
                                      ASSETS["Forex"].keys(),
                                      key="forex_sel")
                                      
        tickers = get_ticker(equity_choice, 
                             commodity_choice, 
                             index_choice, 
                             forex_choice)
                             
        logscale = st.toggle("Log-scale",value=False)

        if len(tickers) == 0:
            st.toast("Please select at least one ticker to continue.", icon="⚠️")
            st.stop()
                    
    @st.fragment
    def render_top_news():
        with st.container(border=True):
            st.markdown("#### Top News")
            news = fetch_top_news()
            if news:
                for n in news:
                    st.markdown(f'''
                        <a href="{n['url']}" target="_blank" style="text-decoration: none; color: inherit;">
                            <div style="padding: 12px; margin-bottom: 12px; border-radius: 8px; background-color: rgba(140, 120, 81, 0.05); border-left: 4px solid #8c7851; transition: background-color 0.2s, transform 0.1s;" onmouseover="this.style.backgroundColor='rgba(140, 120, 81, 0.1)'; this.style.transform='translateX(2px)';" onmouseout="this.style.backgroundColor='rgba(140, 120, 81, 0.05)'; this.style.transform='translateX(0)';">
                                <span style="font-size: 0.9em; font-weight: 500; color: #1a1a1a; line-height: 1.4; display: block;">{n['title']}</span>
                            </div>
                        </a>
                    ''', unsafe_allow_html=True)
            else:
                st.write("No news available.")

    render_top_news()

    @st.fragment
    def render_export_report():
        with st.container(border=True):
            st.markdown("#### Export Report")
            
            us_treasury_data = fetch_us_treasury_yield_curve()
            ecb_data = fetch_ecb_yield_curve()
            fed_rate = fetch_fed_policy_rate()
            ecb_rate_series = fetch_ecb_policy_rate()
            govies_data = fetch_ecb_govies_10y()
            japan_data = fetch_japan_yield_curve()
            eu_inflation = fetch_ecb_inflation()
            us_inflation = fetch_us_inflation()
            
            pdf_bytes = generate_pdf_recap(us_treasury_data, ecb_data, fed_rate, ecb_rate_series, govies_data, japan_data, global_data, eu_inflation, us_inflation)
            
            st.download_button("📄 Download PDF Recap", 
                               data=pdf_bytes, 
                               file_name="market_recap.pdf", 
                               mime="application/pdf",
                               use_container_width=True)

    render_export_report()



with col2:
    tab1, tab2, tab3, tab5 = st.tabs(["Market Overview",
                                      "Correlation matrix",
                                      "Volatility",
                                      "Data"])
    
    with st.spinner("Processing data..."):
        tickers_tuple = tuple(tickers)
        period_yf = period_yf_dict[period_choice]
        yfinance_data_max = fetch_yfinance_data(tickers_tuple, period=period_yf)
        
        # Slice data based on selected period to ensure exact match
        if period_offset is not None:
            start_date_str = (pd.Timestamp.today() - period_offset).strftime('%Y-%m-%d')
            yfinance_data = yfinance_data_max.loc[start_date_str:]
            if yfinance_data.empty: # Fallback in case period_offset is outside yf period
                yfinance_data = yfinance_data_max
        else:
            yfinance_data = yfinance_data_max
            
        yfinance_fig = plot_yfinance_data(yfinance_data, tickers, logscale)
    
    with tab1:
        st.plotly_chart(yfinance_fig)
        latest_date = yfinance_data.index[-1].strftime("%d/%m/%Y at %H:%M")
        data_as_of_html = f"<p style='text-align: right; font-style: italic; color: #8c7851; font-size: 0.85em; margin-top: -20px; opacity: 0.7;'>Data as of {latest_date}</p>"
        st.markdown(data_as_of_html, unsafe_allow_html=True)
        
    with tab2:
        correlation_fig = yfinance_data_correlation(yfinance_data)
        st.plotly_chart(correlation_fig, use_container_width=True)
    
    with tab3:
        vol_fig = plot_volatility(yfinance_data)
        st.plotly_chart(vol_fig, use_container_width=True)

        
    with tab5:
        st.dataframe(yfinance_data)
    
    metrics_yfinance_data(yfinance_data)

    st.write("---")

    with st.spinner("Fetching ECB, US Treasury & JGB data..."):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_ecb = executor.submit(fetch_ecb_yield_curve)
            future_govies = executor.submit(fetch_ecb_govies_10y)
            future_ecb_rate = executor.submit(fetch_ecb_policy_rate)
            future_us = executor.submit(fetch_us_treasury_yield_curve)
            future_fed = executor.submit(fetch_fed_policy_rate)
            future_jp = executor.submit(fetch_japan_yield_curve)
            future_inflation = executor.submit(fetch_ecb_inflation)
            future_us_inflation = executor.submit(fetch_us_inflation)
            
            ecb_data = future_ecb.result()
            govies_data = future_govies.result()
            ecb_rate_series = future_ecb_rate.result()
            us_treasury_data = future_us.result()
            fed_rate = future_fed.result()
            japan_data = future_jp.result()
            inflation_data = future_inflation.result()
            us_inflation_data = future_us_inflation.result()

    st.subheader("Macroeconomics")
    
    with st.expander("Recap"):
        recap_col1, recap_col2, recap_col3 = st.columns([2, 1, 1])
        with recap_col1:
            st.markdown("#### Global 10Y Yields")
            latest_eu = govies_data.dropna().iloc[-1]
            global_govies = {
                "🇺🇸 US": us_treasury_data['10 Yr'].dropna().iloc[-1] if not us_treasury_data.empty else None,
                "🇩🇪 DE": latest_eu.get("🇩🇪 Germany", None),
                "🇯🇵 JP": japan_data['10Y'].dropna().iloc[-1] if not japan_data.empty else None,
                "🇫🇷 FR": latest_eu.get("🇫🇷 France", None),
                "🇮🇹 IT": latest_eu.get("🇮🇹 Italy", None),
            }
            
            valid_govies = {k: v for k, v in global_govies.items() if v is not None}
            sorted_govies = dict(sorted(valid_govies.items(), key=lambda item: item[1], reverse=True))
            
            govies_list = [{"Country": k, "Yield (%)": f"{v:.2f} %"} for k, v in sorted_govies.items()]
            govies_df = pd.DataFrame(govies_list)
            
            styled_df = govies_df.style.hide(axis="index").set_table_styles([{
                'selector': 'th',
                'props': [('background-color', 'rgba(140, 120, 81, 0.1)')]
            }])
            
            st.table(styled_df)
            
        with recap_col2:
            st.markdown("#### Latest Inflation")
            if not inflation_data.empty:
                latest_eu_inf = inflation_data.iloc[-1]
                with st.container(border=True):
                    st.metric(label="🇪🇺 Euro Area", value=f"{latest_eu_inf:.1f} %")
            if not us_inflation_data.empty:
                latest_us_inf = us_inflation_data.iloc[-1]
                with st.container(border=True):
                    st.metric(label="🇺🇸 United States", value=f"{latest_us_inf:.1f} %")
                    
        with recap_col3:
            st.markdown("#### Policy Rates")
            if not ecb_rate_series.empty:
                latest_ecb_rate = ecb_rate_series.iloc[-1]
                with st.container(border=True):
                    st.metric(label="🇪🇺 ECB Deposit Rate", value=f"{latest_ecb_rate:.2f} %")
            if not fed_rate.empty:
                latest_fed_rate = fed_rate.iloc[-1]
                with st.container(border=True):
                    st.metric(label="🇺🇸 FED Funds Rate", value=f"{latest_fed_rate:.2f} %")
        
    tab_eu, tab_us, tab_jp = st.tabs(["🇪🇺 Euro Area", "🇺🇸 United States", "🇯🇵 Japan"])
    with tab_eu:
        ecb_bar_fig = plot_ecb_yield_curve_bar(ecb_data, ecb_rate_series)
        st.plotly_chart(ecb_bar_fig, use_container_width=True)
        
        if not inflation_data.empty:
            eu_fig = plot_single_inflation(inflation_data, "#8c7851", "Euro Area Inflation")
            st.plotly_chart(eu_fig, use_container_width=True)
        else:
            st.warning("Euro Area data not available.")
            
    with tab_us:
        us_bar_fig = plot_us_treasury_yield_curve(us_treasury_data, fed_rate)
        st.plotly_chart(us_bar_fig, use_container_width=True)
        
        if not us_inflation_data.empty:
            us_fig = plot_single_inflation(us_inflation_data, "#8c7851", "United States Inflation")
            st.plotly_chart(us_fig, use_container_width=True)
        else:
            st.warning("US data not available.")
            
    with tab_jp:
        jp_bar_fig = plot_japan_yield_curve(japan_data)
        st.plotly_chart(jp_bar_fig, use_container_width=True)
        
    st.markdown(data_as_of_html, unsafe_allow_html=True)


