# streamlit run "/Users/valentinfaure/Documents/Academique/SKEMA/M2/FMI/Cours/Python/Code/Dashboard project/Dashboard.py"
# Local URL: http://localhost:8501 Network URL: http://192.168.1.157:8501

import yfinance as yf
import streamlit as st
import plotly.express as px


st.set_page_config(layout="wide")

col1, col2 = st.columns([1, 3])

companies = {"Apple":"AAPL","Microsoft":"MSFT","Alphabet":"GOOGL","Amazon":"AMZN","Tesla":"TSLA","Meta":"META","Nvidia":"NVDA","Berkshire Hathaway":"BRK-B","Johnson & Johnson":"JNJ","Visa":"V","Walmart":"WMT","JPMorgan Chase":"JPM","Procter & Gamble":"PG","Disney":"DIS","Netflix":"NFLX","Mastercard":"MA","UnitedHealth":"UNH","Home Depot":"HD","Coca-Cola":"KO","PepsiCo":"PEP"}
horizon_map = {"1 Month": "1mo","3 Months": "3mo","6 Months": "6mo","1 Year": "1y","5 Years": "5y","10 Years": "10y","20 Years": "20y","Max": "max"}


with col1:
    with st.container(border=True):
        stock_names = st.multiselect("Stock",list(companies.keys()), default="Apple")
        horizon = st.pills("Time horizon", list(horizon_map.keys()),default="1 Month")

# Convert the list of stock names to a list of ticker symbols
tickers = [companies[name] for name in stock_names]

# Importer les données à la période sélectionnée
data = yf.download(tickers, period=horizon_map[horizon])["Close"]


#with col1:
 #   with st.container(border=True):
  #      start_price = data.iloc[0]
   #     end_price = data.iloc[-1]
    #    évolution = ((end_price-start_price)/start_price)*100
     #   st.metric("Growth", value=f"${end_price.item():,.2f}", delta=f"{évolution.item():,.2f}%")


# Créer le graph avec plotly
fig = px.line(data,x=data.index,y=tickers, title='Stock Price')


with col2:
    with st.container(border=True): 
        # Interface
        st.plotly_chart(fig)