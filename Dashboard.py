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

commodities = {"Crude Oil WTI": "CL=F","Crude Oil Brent": "BZ=F","Natural Gas": "NG=F","Heating Oil": "HO=F",
               "Gasoline RBOB": "RB=F","Gold": "GC=F","Silver": "SI=F","Platinum": "PL=F","Palladium": "PA=F",
               "Copper": "HG=F","Corn": "ZC=F","Wheat": "ZW=F","Soybeans": "ZS=F","Oats": "ZO=F","Coffee": "KC=F",
               "Cocoa": "CC=F","Cotton": "CT=F","Sugar": "SB=F","Live Cattle": "LE=F","Feeder Cattle": "GF=F",
               "Lean Hogs": "HE=F"}


horizon_map = {"1 Month": "1mo","3 Months": "3mo","6 Months": "6mo","1 Year": "1y",
               "5 Years": "5y","10 Years": "10y","20 Years": "20y","Max": "max"}


with col1:
    with st.container(border=True):
        st.markdown("#### Parameters")
        commodities_name = st.multiselect("Commodities", list(commodities.keys()))
        stock_names = st.multiselect("Stock", list(companies.keys()), default=["Apple"])
        horizon = st.pills("Horizon", list(horizon_map.keys()), default="1 Month")
        log_scale = st.toggle("Log scale", value=False)
    


tickers = [companies[name] for name in stock_names] + [commodities[name] for name in commodities_name]
data = yf.download(tickers, period=horizon_map[horizon])["Close"]



with col2:
    if len(tickers) == 1:
        fig = px.line(data, x=data.index, y=data.columns,title=None)
    else:
        data_norm = (data.pct_change().fillna(0) + 1).cumprod()
        if log_scale == True:
            fig = px.line(data_norm, x=data_norm.index, y=data_norm.columns, title="Normalized performances")
            fig.update_yaxes(type="log")
        else:
            data_percent = (data_norm-1)*100
            fig = px.line(data_percent, x=data_percent.index, y=data_percent.columns, title="Normalized performances")
            fig.update_yaxes(ticksuffix="%")

    st.plotly_chart(fig)

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
                
       
st.markdown("### Raw data")
data