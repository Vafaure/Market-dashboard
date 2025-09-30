# cd "/Users/valentinfaure/Documents/Academique/SKEMA/M2/FMI/Cours/Python/Code/Dashboard project"
# streamlit run Dashboard.py

import yfinance as yf
import streamlit as st
import plotly.express as px

# Dictionnaires

period_dict = {"1 Month": "1mo","3 Months": "3mo","6 Months": "6mo",
               "1 Year": "1y","5 Years": "5y","10 Years": "10y",
               "20 Years": "20y","Max": "max"}

equity_dict = {"Apple":"AAPL","Microsoft":"MSFT","Alphabet":"GOOGL",
               "Amazon":"AMZN","Tesla":"TSLA","Meta":"META","Nvidia":"NVDA",
               "Berkshire Hathaway":"BRK-B","Johnson & Johnson":"JNJ",
               "Visa":"V","Walmart":"WMT","JPMorgan Chase":"JPM",
               "Procter & Gamble":"PG","Disney":"DIS","Netflix":"NFLX",
               "Mastercard":"MA","UnitedHealth":"UNH","Home Depot":"HD",
               "Coca-Cola":"KO","PepsiCo":"PEP"}

commodity_dict = {"Crude Oil WTI": "CL=F","Crude Oil Brent": "BZ=F",
                  "Natural Gas": "NG=F","Heating Oil": "HO=F",
                  "Gasoline RBOB": "RB=F","Gold": "GC=F","Silver": "SI=F",
                  "Platinum": "PL=F","Palladium": "PA=F","Copper": "HG=F",
                  "Corn": "ZC=F","Wheat": "ZW=F","Soybeans": "ZS=F",
                  "Oats": "ZO=F","Coffee": "KC=F","Cocoa": "CC=F",
                  "Cotton": "CT=F","Sugar": "SB=F","Live Cattle": "LE=F",
                  "Feeder Cattle": "GF=F","Lean Hogs": "HE=F"}

index_dict = {"S&P 500": "^GSPC","Dow Jones Industrial Average": "^DJI",
              "NASDAQ 100": "^NDX","Russell 2000": "^RUT","VIX": "^VIX",
              "Euro Stoxx 50": "^STOXX50E","FTSE 100": "^FTSE","DAX": "^GDAXI",
              "CAC 40": "^FCHI","IBEX 35": "^IBEX","Nikkei 225": "^N225",
              "Hang Seng": "^HSI","Shanghai Composite": "000001.SS",
              "KOSPI": "^KS11"}

forex_dict = {"EUR/USD": "EURUSD=X","USD/JPY": "JPY=X","GBP/USD": "GBPUSD=X",
              "USD/CHF": "CHF=X","AUD/USD": "AUDUSD=X","NZD/USD": "NZDUSD=X",
              "USD/CAD": "CAD=X","EUR/GBP": "EURGBP=X","EUR/JPY": "EURJPY=X",
              "EUR/CHF": "EURCHF=X","GBP/JPY": "GBPJPY=X",
              "AUD/JPY": "AUDJPY=X","USD/CNY": "CNY=X","USD/HKD": "HKD=X",
              "USD/SGD": "SGD=X","USD/INR": "INR=X","USD/BRL": "BRL=X",
              "USD/ZAR": "ZAR=X","USD/MXN": "MXN=X"}

fixed_income_dict = {"US 13 Week T-Bill Yield": "^IRX",
                     "US 5 Year Treasury Yield": "^FVX",
                     "US 10 Year Treasury Yield": "^TNX",
                     "US 30 Year Treasury Yield": "^TYX"}

# Functions

def get_data(ticker,period_choice):
    period_code = period_dict[period_choice]
    return yf.download(ticker, period=period_code, auto_adjust=True)["Close"]

def preprocess(data_raw):
    return data_raw.ffill().dropna()

def get_ticker(equity_choice,commodity_choice,index_choice,forex_choice,
               fixed_income_choice):
    ticker = ([equity_dict[name] for name in equity_choice] +
              [commodity_dict[name] for name in commodity_choice] +
              [index_dict[name] for name in index_choice] +
              [forex_dict[name] for name in forex_choice] +
              [fixed_income_dict[name] for name in fixed_income_choice])
    return ticker


def normalize(data):
    if logscale==True:
        return data / data.iloc[0]
    else:
        return data / data.iloc[0] - 1
    

def plot_data(data, data_norm, ticker, logscale):
    if len(ticker) == 1:
        fig = px.line(data, x=data.index, y=data.columns, 
                      log_y=logscale)
    else:
        if logscale==True:
            fig = px.line(data_norm, x=data_norm.index, y=data_norm.columns, 
                          log_y=logscale)
        else:
            fig = px.line(data_norm, x=data_norm.index, y=data_norm.columns, 
                          log_y=logscale).update_yaxes(tickformat=".0%")
    fig.update_layout(hovermode='x')
    return fig


def perf_metrics(data):
    return (data.iloc[-1] / data.iloc[0] - 1) * 100

def show_metrics(data, ticker):
    perf = perf_metrics(data)
    if len(ticker) == 1:
        st.metric("Quote", value=f"${data.iloc[-1].item():,.2f}", 
                  delta=f"{perf.item():,.2f} %")
    elif len(ticker) > 1:
        best = perf.idxmax()
        worst = perf.idxmin()
        col1, col2, col3, col4, col5, col6, col7= st.columns(7)
        with col1:
            st.metric("Best growth", value=best, 
                      delta=f"{perf.loc[best]:,.2f} %")
        with col2:
            st.metric("Worst growth", value=worst, 
                      delta=f"{perf.loc[worst]:,.2f} %")


# Dashboard
st.set_page_config(layout="wide",page_title = "Market dashboard")
st.title("Market Dashboard")
col1, col2 = st.columns([1,3])

with col1:
    with st.container(border=True):
        st.markdown("#### Parameters")
        period_choice = st.pills("Period", period_dict.keys(),
                                 default="1 Month")
    
        equity_choice = st.multiselect("Equity", equity_dict.keys(), 
                                       default="Apple")
        commodity_choice = st.multiselect("Commodity", commodity_dict.keys())
        index_choice = st.multiselect("Index", index_dict.keys())
        forex_choice = st.multiselect("Forex", forex_dict.keys())
        fixed_income_choice = st.multiselect("Fixed income",
                                             fixed_income_dict.keys())
    
        logscale = st.toggle("Log-scale",value=False)
        ticker = get_ticker(equity_choice, commodity_choice, index_choice, 
                            forex_choice, fixed_income_choice)
        if len(ticker) == 0:
            st.warning("⚠️ Please select at least one ticker")
            st.stop()

data_raw = get_data(ticker, period_choice)
data = preprocess(data_raw)
data_norm = normalize(data)

with col2:
    fig = plot_data(data, data_norm, ticker, logscale)
    st.plotly_chart(fig)
    st.markdown("#### Metrics")
    metrics_display = show_metrics(data,ticker)

st.dataframe(data)






