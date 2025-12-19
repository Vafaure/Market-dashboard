import yfinance as yf
import streamlit as st
import plotly.express as px
import numpy as np
import pandas_datareader.data as web
import pandas as pd


st.set_page_config(layout="wide", page_title="Market dashboard")

##### DICT #####

period_dict = {
    "1 Month": "1mo",
    "3 Months": "3mo",
    "6 Months": "6mo",
    "1 Year": "1y",
    "5 Years": "5y",
    "10 Years": "10y",
    "20 Years": "20y",
    "Max": "max"
}


vol_window_dict = {
    "5 Days (1w)": 5,
    "21 Days (1m)": 21,
    "63 Days (3m)": 63,
    "126 Days (6m)": 126,
    "252 Days (1y)": 252,
    "756 Days (3y)": 756,
    "1260 Days (5y)": 1260,
    "2520 Days (10y)": 2520
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
    },
    "Fixed Income": {
        "US 13 Week T-Bill (^IRX)": "^IRX",
        "US 5 Year Yield (^FVX)": "^FVX",
        "US 10 Year Yield (^TNX)": "^TNX",
        "US 30 Year Yield (^TYX)": "^TYX"
    }
}


SERIES = {
    "US_Yields": {
        "US 1M": "DGS1MO",
        "US 3M": "DGS3MO",
        "US 6M": "DGS6MO",
        "US 1Y": "DGS1",
        "US 2Y": "DGS2",
        "US 3Y": "DGS3",
        "US 5Y": "DGS5",
        "US 7Y": "DGS7",
        "US 10Y": "DGS10",
        "US 20Y": "DGS20",
        "US 30Y": "DGS30"
    },
    "Yields_10Y_OECD": {
        "Ireland 10Y": "IRLTLT01USM156N",
        "Italy 10Y": "IRLTLT01ITM156N",
        "Spain 10Y": "IRLTLT01ESM156N",
        "Germany 10Y": "IRLTLT01DEM156N",
        "United Kingdom 10Y": "IRLTLT01GBM156N",
        "Portugal 10Y": "IRLTLT01PTM156N",
        "France 10Y": "IRLTLT01FRM156N",
        "Japan 10Y": "IRLTLT01JPM156N",
        "Greece 10Y": "IRLTLT01GRM156N"
    },
    "Macro_Indicators": {
        "Real GDP": "GDPC1",
        "CPI Inflation": "CPIAUCSL"
    }
}


##### FUNCTIONS #####

def fetch_yfinance_data(tickers, period):
    yfinance_data = yf.download(tickers, period=period)["Close"].ffill().dropna()
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

def get_ticker(equity_choice,commodity_choice,index_choice,forex_choice,
               fixed_income_choice):
    tickers = ([ASSETS["Equity"][name] for name in equity_choice] +
              [ASSETS["Commodity"][name] for name in commodity_choice] +
              [ASSETS["Index"][name] for name in index_choice] +
              [ASSETS["Forex"][name] for name in forex_choice] +
              [ASSETS["Fixed Income"][name] for name in fixed_income_choice])
    return tickers


def yfinance_data_correlation (yfinance_data):
    correlation_data = yfinance_data.corr()
    correlation_fig = px.imshow(correlation_data,text_auto=True,color_continuous_scale="RdYlGn",
                     zmin=-1, zmax=1)
    correlation_fig.update_xaxes(side="top",title=None)
    correlation_fig.update_yaxes(title=None)
    return correlation_fig


def plot_volatility(yfinance_data, window,logscale):
    log_returns = np.log(yfinance_data / yfinance_data.shift(1))
    volatility = round(log_returns.rolling(window=window).std() * np.sqrt(252) * 100,2)
    volatility = volatility.dropna() 
    fig = px.line(volatility,
                  title=f"Historic Volatility ({window} Days Rolling)",
                  log_y=logscale) 
    fig.update_layout(
        yaxis_title="Annualized Volatility (%)", 
        hovermode='x')
    return fig


def fetch_fred_data(start, SERIES):
    all_tickers = []
    for category in SERIES.values():
        all_tickers.extend(category.values())
    fred_data = web.DataReader(all_tickers, "fred", start=start).ffill()
    rename_map = {}
    for category in SERIES.values():
        for name, ticker in category.items():
            rename_map[ticker] = name
    fred_data = fred_data.rename(columns=rename_map)
    return fred_data


def plot_us_maturities_bar(fred_data):
    selected_columns = list(SERIES["US_Yields"].keys())
    latest_data = fred_data[selected_columns].iloc[-1]
    df_plot = latest_data.reset_index()
    df_plot.columns = ['Maturities', 'Yield (%)']
    fig = px.bar(df_plot,
                 x='Maturities',
                 y='Yield (%)',
                 text_auto='.2f',
                 title="US Yields over maturities")
    fig.update_layout(showlegend=False)
    return fig

def plot_oecd_10y_bar(fred_data):
    selected_columns = list(SERIES["Yields_10Y_OECD"].keys())
    latest_data = fred_data[selected_columns].iloc[-1].sort_values(ascending=True)
    df_plot = latest_data.reset_index()
    df_plot.columns = ['Countries', 'Yield (%)']
    fig = px.bar(df_plot,
                 x='Countries',
                 y='Yield (%)',
                 text_auto='.2f',
                 title="OECD 10Y Yields")
    fig.update_layout(showlegend=False)
    return fig

def plot_us_yields_line(fred_data):
    selected_columns = list(SERIES["US_Yields"].keys())
    data = fred_data[selected_columns]
    fig = px.line(data,
                  x=data.index,
                  y=data.columns,
                  title="US Yields over time")
    fig.update_layout(xaxis_title="Date",
                      yaxis_title="Yield (%)")
    return fig

def plot_oecd_10y_line(fred_data):
    selected_columns = list(SERIES["Yields_10Y_OECD"].keys())
    data = fred_data[selected_columns]
    fig = px.line(data,
                  x=data.index,
                  y=data.columns,
                  title="OECD 10Y Yields over time")
    fig.update_layout(xaxis_title="Date",
                      yaxis_title="Yield (%)")
    return fig

def compute_macro_regime(fred_data):
    gdp_yoy = fred_data["Real GDP"].pct_change(12)
    cpi_yoy = fred_data["CPI Inflation"].pct_change(12)
    
    gdp_trend = np.sign(gdp_yoy.diff())
    gdp_trend = gdp_trend.replace(0,np.nan).ffill()
    
    cpi_trend = np.sign(cpi_yoy.diff())
    cpi_trend = cpi_trend.replace(0,np.nan).ffill()
    
    regimes = pd.DataFrame({"gdp_yoy":gdp_yoy,"cpi_yoy":cpi_yoy,"gdp_trend":gdp_trend,"cpi_trend":cpi_trend})
    
    growth_label=regimes["gdp_trend"].map({1.0:"Rising Growth",-1.0:"Falling Growth"})
    inflation_label=regimes["cpi_trend"].map({1.0:"Rising Inflation",-1.0:"Falling Inflation"})
    
    regimes["regime"]=growth_label + "+" + inflation_label
    
    return regimes

def compute_regime_based_stats(returns,regimes):
    df = returns.join(regimes["regime"])
    avg_return = (df.groupby("regime")[returns.columns].mean()*12)*100
    return avg_return




##### CODE #####

st.title("Market Dashboard")
col1, col2 = st.columns([1,3])

with col1:
    with st.container(border=True):
        st.markdown("#### Parameters")
        period_choice = st.pills("Period", 
                                 period_dict.keys(),
                                 default="1 Year")
        period = period_dict[period_choice]
        window_selection = st.pills(
                "Window (for Volatility Tab)",
                options=vol_window_dict.keys(),
                default="21 Days (1m)")
        window = vol_window_dict[window_selection]
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
        fixed_income_choice = st.multiselect("Fixed income",
                                             ASSETS["Fixed Income"].keys())
        tickers = get_ticker(equity_choice, 
                             commodity_choice, 
                             index_choice, 
                             forex_choice, 
                             fixed_income_choice)
        logscale = st.toggle("Log-scale",value=False)
        if len(tickers) == 0:
                    st.toast("Please select at least one ticker to continue.", icon="⚠️")
                    st.stop()




with col2:
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Market Overview",
                                            "Correlation matrix",
                                            "Volatility",
                                            "Regime",
                                            "Data"])
    
    with st.spinner("Downloading data..."):
        yfinance_data = fetch_yfinance_data(tickers, period)
        fred_data = fetch_fred_data(yfinance_data.index[0], SERIES)
        yfinance_fig = plot_yfinance_data(yfinance_data, tickers, logscale)
    
    with tab1:
        st.plotly_chart(yfinance_fig)
        
    with tab2:
        correlation_fig = yfinance_data_correlation(yfinance_data)
        st.plotly_chart(correlation_fig, use_container_width=True)
    
    with tab3:
        vol_fig = plot_volatility(yfinance_data, window,logscale)
        st.plotly_chart(vol_fig, use_container_width=True)
        if window>len(yfinance_data):
            st.warning("**Window is too large:** The selected rolling window can't be larger than the period. Please select a smaller window.", icon="⚠️")

        
    with tab4:
        regimes = compute_macro_regime(fred_data)
        returns = yfinance_data.pct_change().dropna()
        avg_return=compute_regime_based_stats(returns,regimes)
        st.write("Average return (%)")
        st.table(avg_return)
        if avg_return.empty:
            st.warning("**Period too short:** The selected time range is not sufficient to compute macro regimes. Please select a longer period (at least 1 year) to see regime-based statistics.", icon="⚠️")

    with tab5:
        st.dataframe(yfinance_data)
    
    st.write("---")
    metrics_yfinance_data(yfinance_data)
    

st.write("---")
st.subheader("Macro Overview")


us_maturities_fig = plot_us_maturities_bar(fred_data)
OECD_10Y_fig = plot_oecd_10y_bar(fred_data)
us_historic_fig = plot_us_yields_line(fred_data)
OECD_historic_fig = plot_oecd_10y_line(fred_data)

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(us_maturities_fig)
    st.plotly_chart(us_historic_fig)

with col2:
    st.plotly_chart(OECD_10Y_fig)
    st.plotly_chart(OECD_historic_fig)
    
    
    
    
    
    
    