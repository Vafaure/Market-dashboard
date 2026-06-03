import yfinance as yf
import streamlit as st
import plotly.express as px
import numpy as np
# import pandas_datareader.data as web
import pandas as pd
import requests
import io


st.set_page_config(layout="wide", page_title="Market dashboard")

# Force full width and reduce padding
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 0rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 100%;
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


# SERIES = {
#     "US_Yields": {
#         "US 1M": "DGS1MO",
#         "US 3M": "DGS3MO",
#         "US 6M": "DGS6MO",
#         "US 1Y": "DGS1",
#         "US 2Y": "DGS2",
#         "US 3Y": "DGS3",
#         "US 5Y": "DGS5",
#         "US 7Y": "DGS7",
#         "US 10Y": "DGS10",
#         "US 20Y": "DGS20",
#         "US 30Y": "DGS30"
#     },
#     "Yields_10Y_OECD": {
#         "Ireland 10Y": "IRLTLT01USM156N",
#         "Italy 10Y": "IRLTLT01ITM156N",
#         "Spain 10Y": "IRLTLT01ESM156N",
#         "Germany 10Y": "IRLTLT01DEM156N",
#         "United Kingdom 10Y": "IRLTLT01GBM156N",
#         "Portugal 10Y": "IRLTLT01PTM156N",
#         "France 10Y": "IRLTLT01FRM156N",
#         "Japan 10Y": "IRLTLT01JPM156N",
#         "Greece 10Y": "IRLTLT01GRM156N"
#     },
#     "Macro_Indicators": {
#         "Real GDP": "GDPC1",
#         "CPI Inflation": "CPIAUCSL"
#     }
# }

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

@st.cache_data(ttl=3600)
def fetch_yfinance_data(tickers):
    tickers_list = list(tickers)
    yfinance_data = yf.download(tickers_list, period="max", progress=False)["Close"].ffill().dropna()
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
                               x=yfinance_data.index, 
                               y=yfinance_data.columns, 
                               log_y=logscale)
    else:
        yfinance_fig = px.line(yfinance_data_norm,
                               x=yfinance_data_norm.index, 
                               y=yfinance_data_norm.columns, 
                               log_y=logscale)
        yfinance_fig.update_yaxes(tickformat=".0%")
        yfinance_fig.update_layout(hovermode='x')
    return yfinance_fig


def metrics_yfinance_data(yfinance_data):
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


def yfinance_data_correlation (yfinance_data):
    correlation_data = yfinance_data.corr()
    correlation_fig = px.imshow(correlation_data,text_auto=True,color_continuous_scale="RdYlGn",
                     zmin=-1, zmax=1)
    correlation_fig.update_xaxes(side="top",title=None)
    correlation_fig.update_yaxes(title=None)
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
                 color_continuous_scale="Reds")
    fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    fig.update_layout(xaxis_title="Annualized Volatility (%)", yaxis_title="Asset")
    return fig


# def fetch_fred_data(start, SERIES):
#     all_tickers = []
#     for category in SERIES.values():
#         all_tickers.extend(category.values())
#     fred_data = web.DataReader(all_tickers, "fred", start=start).ffill()
#     rename_map = {}
#     for category in SERIES.values():
#         for name, ticker in category.items():
#             rename_map[ticker] = name
#     fred_data = fred_data.rename(columns=rename_map)
#     return fred_data


# def plot_us_maturities_bar(fred_data):
#     selected_columns = list(SERIES["US_Yields"].keys())
#     latest_data = fred_data[selected_columns].iloc[-1]
#     df_plot = latest_data.reset_index()
#     df_plot.columns = ['Maturities', 'Yield (%)']
#     fig = px.bar(df_plot,
#                  x='Maturities',
#                  y='Yield (%)',
#                  text_auto='.2f',
#                  title="US Yields over maturities")
#     fig.update_layout(showlegend=False)
#     return fig

# def plot_oecd_10y_bar(fred_data):
#     selected_columns = list(SERIES["Yields_10Y_OECD"].keys())
#     latest_data = fred_data[selected_columns].iloc[-1].sort_values(ascending=True)
#     df_plot = latest_data.reset_index()
#     df_plot.columns = ['Countries', 'Yield (%)']
#     fig = px.bar(df_plot,
#                  x='Countries',
#                  y='Yield (%)',
#                  text_auto='.2f',
#                  title="OECD 10Y Yields")
#     fig.update_layout(showlegend=False)
#     return fig

# def plot_us_yields_line(fred_data):
#     selected_columns = list(SERIES["US_Yields"].keys())
#     data = fred_data[selected_columns]
#     fig = px.line(data,
#                   x=data.index,
#                   y=data.columns,
#                   title="US Yields over time")
#     fig.update_layout(xaxis_title="Date",
#                       yaxis_title="Yield (%)")
#     return fig

# def plot_oecd_10y_line(fred_data):
#     selected_columns = list(SERIES["Yields_10Y_OECD"].keys())
#     data = fred_data[selected_columns]
#     fig = px.line(data,
#                   x=data.index,
#                   y=data.columns,
#                   title="OECD 10Y Yields over time")
#     fig.update_layout(xaxis_title="Date",
#                       yaxis_title="Yield (%)")
#     return fig

# def compute_macro_regime(fred_data):
#     gdp_yoy = fred_data["Real GDP"].pct_change(12)
#     cpi_yoy = fred_data["CPI Inflation"].pct_change(12)
#     gdp_trend = np.sign(gdp_yoy.diff())
#     gdp_trend = gdp_trend.replace(0,np.nan).ffill()
#     cpi_trend = np.sign(cpi_yoy.diff())
#     cpi_trend = cpi_trend.replace(0,np.nan).ffill()
#     regimes = pd.DataFrame({"gdp_yoy":gdp_yoy,"cpi_yoy":cpi_yoy,"gdp_trend":gdp_trend,"cpi_trend":cpi_trend})
#     growth_label=regimes["gdp_trend"].map({1.0:"Rising Growth",-1.0:"Falling Growth"})
#     inflation_label=regimes["cpi_trend"].map({1.0:"Rising Inflation",-1.0:"Falling Inflation"})
#     regimes["regime"]=growth_label + "+" + inflation_label
#     return regimes

# def compute_regime_based_stats(returns,regimes):
#     df = returns.join(regimes["regime"])
#     avg_return = (df.groupby("regime")[returns.columns].mean()*12)*100
#     return avg_return


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
                 title="Euro Area Yield Curve (Animated 10-Year History)")
                 
    fig.update_traces(texttemplate="%{text:.2f}", textposition="top center")
    fig.update_layout(showlegend=False)
    
    # Speed up animation slightly
    if fig.layout.updatemenus:
        fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 150
        
    # Set default to the last frame
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


def plot_ecb_yield_curve_line(ecb_data):
    fig = px.line(ecb_data,
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
    dfs = []
    
    for year in years:
        url = f"https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{year}/all?type=daily_treasury_yield_curve&field_tdr_date_value={year}&page&_format=csv"
        try:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            if resp.status_code == 200:
                df_year = pd.read_csv(io.StringIO(resp.text))
                dfs.append(df_year)
        except Exception:
            continue
            
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
                 title="US Treasury Yield Curve (Animated 10-Year History)")
                 
    fig.update_traces(texttemplate="%{text:.2f}", textposition="top center")
    fig.update_layout(showlegend=False)
    
    # Speed up animation slightly
    if fig.layout.updatemenus:
        fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 150
        
    # Set default to the last frame
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




@st.cache_data(ttl=300)
def get_ticker_tape_html():
    tickers = {"S&P 500": "^GSPC", "CAC 40": "^FCHI", "VIX": "^VIX", "EUR/USD": "EURUSD=X", "Gold": "GC=F", "Brent": "BZ=F"}
    try:
        data = yf.download(list(tickers.values()), period="5d", progress=False)["Close"]
        items = []
        for name, ticker in tickers.items():
            if ticker in data:
                series = data[ticker].dropna()
                if len(series) >= 2:
                    latest = series.iloc[-1]
                    prev = series.iloc[-2]
                    pct_change = (latest - prev) / prev * 100
                    color = "#00c04b" if pct_change >= 0 else "#ff2b2b"
                    arrow = "▲" if pct_change >= 0 else "▼"
                    items.append(f"<span style='margin-right: 40px; font-family: sans-serif;'><b>{name}</b> {latest:.2f} <span style='color: {color};'>{arrow} {abs(pct_change):.2f}%</span></span>")
        return " ".join(items)
    except:
        return ""


##### CODE #####

st.title("Market Dashboard")

tape_content = get_ticker_tape_html()
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
        @keyframes scroll-ticker {{
            0% {{ transform: translateX(0); }}
            100% {{ transform: translateX(-100%); }}
        }}
        </style>
        <div class="ticker-wrap">
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
                                       default="Apple (AAPL)")
        commodity_choice = st.multiselect("Commodity", 
                                          ASSETS["Commodity"].keys(),
                                          default=["Crude Oil WTI (CL=F)",
                                                   "Gold (GC=F)"])
        index_choice = st.multiselect("Index",
                                      ASSETS["Index"].keys(),
                                      default="S&P 500 (^GSPC)")
        forex_choice = st.multiselect("Forex", 
                                      ASSETS["Forex"].keys())
        tickers = get_ticker(equity_choice, 
                             commodity_choice, 
                             index_choice, 
                             forex_choice)
        logscale = st.toggle("Log-scale",value=False)
        if len(tickers) == 0:
                    st.toast("Please select at least one ticker to continue.", icon="⚠️")
                    st.stop()




with col2:
    tab1, tab2, tab3, tab5 = st.tabs(["Market Overview",
                                            "Correlation matrix",
                                            "Volatility",
                                            "Data"])
    
    with st.spinner("Processing data..."):
        # Fetch max data for selected tickers
        tickers_tuple = tuple(tickers)
        yfinance_data_max = fetch_yfinance_data(tickers_tuple)
        
        # Slice data based on selected period
        if period_offset is not None:
            start_date_str = (pd.Timestamp.today() - period_offset).strftime('%Y-%m-%d')
            yfinance_data = yfinance_data_max.loc[start_date_str:]
        else:
            yfinance_data = yfinance_data_max
            
        yfinance_fig = plot_yfinance_data(yfinance_data, tickers, logscale)
    
    with tab1:
        st.plotly_chart(yfinance_fig)
        
    with tab2:
        correlation_fig = yfinance_data_correlation(yfinance_data)
        st.plotly_chart(correlation_fig, use_container_width=True)
    
    with tab3:
        vol_fig = plot_volatility(yfinance_data)
        st.plotly_chart(vol_fig, use_container_width=True)

        
    # with tab4:
    #     regimes = compute_macro_regime(fred_data)
    #     returns = yfinance_data.pct_change().dropna()
    #     avg_return=compute_regime_based_stats(returns,regimes)
    #     st.write("Average return (%)")
    #     st.table(avg_return)
    #     if avg_return.empty:
    #         st.warning("**Period too short:** The selected time range is not sufficient to compute macro regimes. Please select a longer period (at least 1 year) to see regime-based statistics.", icon="⚠️")

    with tab5:
        st.dataframe(yfinance_data)
    
    st.write("---")
    metrics_yfinance_data(yfinance_data)
    

st.write("---")
st.subheader("Yield Curves")

with st.spinner("Fetching ECB & US Treasury data..."):
    ecb_data = fetch_ecb_yield_curve()
    govies_data = fetch_ecb_govies_10y()
    ecb_rate_series = fetch_ecb_policy_rate()
    us_treasury_data = fetch_us_treasury_yield_curve()
    fed_rate = fetch_fed_policy_rate()

col_curve, col_govies = st.columns([3, 1])

with col_curve:
    tab_eu, tab_us = st.tabs(["🇪🇺 Euro Area", "🇺🇸 United States"])

    with tab_eu:
        ecb_bar_fig = plot_ecb_yield_curve_bar(ecb_data, ecb_rate_series)
        st.plotly_chart(ecb_bar_fig, use_container_width=True)

    with tab_us:
        us_bar_fig = plot_us_treasury_yield_curve(us_treasury_data, fed_rate)
        st.plotly_chart(us_bar_fig, use_container_width=True)

with col_govies:
    st.markdown("#### EU 10Y Govies")
    latest_govies = govies_data.dropna().iloc[-1].sort_values(ascending=True)
    govies_df = latest_govies.reset_index()
    govies_df.columns = ["Country", "Yield (%)"]
    govies_df["Yield (%)"] = govies_df["Yield (%)"].map("{:.2f} %".format)
    st.dataframe(govies_df, hide_index=True, use_container_width=True)