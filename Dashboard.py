# cd "/Users/valentinfaure/Documents/Academique/SKEMA/M2/FMI/Cours/Python/Code/Dashboard project"
# streamlit run Dashboard.py

import yfinance as yf
import streamlit as st
import plotly.express as px

st.set_page_config(layout="wide")

st.title("Market Dashboard")

col1, col2 = st.columns([1, 3])

companies = {"Apple":"AAPL","Microsoft":"MSFT","Alphabet":"GOOGL","Amazon":"AMZN","Tesla":"TSLA","Meta":"META",
             "Nvidia":"NVDA","Berkshire Hathaway":"BRK-B","Johnson & Johnson":"JNJ","Visa":"V","Walmart":"WMT",
             "JPMorgan Chase":"JPM","Procter & Gamble":"PG","Disney":"DIS","Netflix":"NFLX","Mastercard":"MA",
             "UnitedHealth":"UNH","Home Depot":"HD","Coca-Cola":"KO","PepsiCo":"PEP"}

horizon_map = {"1 Month": "1mo","3 Months": "3mo","6 Months": "6mo","1 Year": "1y",
               "5 Years": "5y","10 Years": "10y","20 Years": "20y","Max": "max"}

with col1:
    with st.container(border=True):
        stock_names = st.multiselect("Stock", list(companies.keys()), default=["Apple"])
        horizon = st.pills("Time horizon", list(horizon_map.keys()), default="1 Month")

tickers = [companies[name] for name in stock_names]


data = yf.download(tickers, period=horizon_map[horizon])["Close"]


#missing_values = data.isnull().sum


if len(tickers) == 1:
    fig = px.line(data, x=data.index, y=data.columns, title="Stock price")
else:
    data_norm = (data.pct_change().fillna(0) + 1).cumprod()
    data_percent = (data_norm-1)*100
    fig = px.line(data_percent, x=data_percent.index, y=data_percent.columns, title="Normelized performances")
    fig.update_yaxes(ticksuffix="%")
    #fig.update_yaxes(type="log")


with col1:
    with st.container(border=True):
        if len(tickers)==1:
            start_price = data.iloc[0] 
            end_price = data.iloc[-1] 
            évolution = ((end_price-start_price)/start_price)*100
            st.metric("Growth", value=f"${end_price.item():,.2f}", delta=f"{évolution.item():,.2f}%")
        else:
            perf = (data.iloc[-1] / data.iloc[0] - 1) * 100
            best = perf.idxmax()
            worst = perf.idxmin()
            col_best, col_worst = st.columns(2)
            with col_best:
                st.metric("Best growth",value=f"{best}",delta=f"{perf[best]:,.2f}%")
            with col_worst:
                st.metric("Worst growth", value=f"{worst}",delta=f"{perf[worst]:,.2f}%")
                

with col2:
    with st.container(border=True):
        st.plotly_chart(fig)
       
st.markdown("### Raw data")
data