# market performance for commodity(gold, crude oil, wheat), equity, rates(yield curve of the US and german bonds), currency(dollar futures)
# Key Metrics / Indicators : Growth, Inflation, Volatility, Yields, Performance Metrics
# Data Visualization : LineCharts, Term Structure Graphs, Heatmaps
# Filters : Time Periods, Asset Classes, Market Regimes
# Layout & Design : – Sidebar for filters (time periods, asset classes, market regimes) , Main panels for visualizations
# Update Frequency : daily
# streamlit run "/Users/valentinfaure/Documents/Academique/SKEMA/M2/FMI/Cours/Python/Code/Dashboard project/Dashboard.py"
# Local URL: http://localhost:8501 Network URL: http://192.168.1.157:8501



import yfinance as yf
import streamlit as st
import plotly.express as px

st.set_page_config(layout="wide")

col1, col2 = st.columns([1, 3])

with col1:
    with st.container(border=True):
        # Stock
        # Liste stocks
        companies = {"Apple":"AAPL","Microsoft":"MSFT","Alphabet":"GOOGL","Amazon":"AMZN","Tesla":"TSLA","Meta":"META","Nvidia":"NVDA","Berkshire Hathaway":"BRK-B","Johnson & Johnson":"JNJ","Visa":"V","Walmart":"WMT","JPMorgan Chase":"JPM","Procter & Gamble":"PG","Disney":"DIS","Netflix":"NFLX","Mastercard":"MA","UnitedHealth":"UNH","Home Depot":"HD","Coca-Cola":"KO","PepsiCo":"PEP"}
        # Création de la liste
        stock = st.selectbox("Stock",list(companies.keys()))


        # Période
        # Liste périodes
        horizon_map = {"1 Month": "1mo","3 Months": "3mo","6 Months": "6mo","1 Year": "1y","5 Years": "5y","10 Years": "10y","20 Years": "20y","Max": "max"}
        # Création des boutons de période
        horizon = st.pills("Time horizon", list(horizon_map.keys()),default="1 Month")


# Importer les données à la période sélectionnée
data = yf.download(companies[stock], period=horizon_map[horizon])["Close"]


with col1:
    with st.container(border=True):
        start_price = data.iloc[0]
        end_price = data.iloc[-1]
        évolution = ((end_price-start_price)/start_price)*100
        st.metric("Growth",value=round(end_price,2), delta=str(round(évolution.item(),2))+"%")

# Créer le graph avec plotly
fig = px.line(data,x=data.index,y=companies[stock], title='Stock Price')


with col2:
    with st.container(border=True): 
        # Interface
        st.plotly_chart(fig)