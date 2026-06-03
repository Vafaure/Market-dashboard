# 📈 Market Dashboard

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

A professional, fully-featured financial dashboard built with Streamlit and Python. It provides interactive visualizations of market performance across equities, commodities, indices, forex, and sovereign yield curves (US Treasury & ECB).

🌍 **[Access the Live App Here](https://market-dashboard-vafaure.streamlit.app)**

---

## ✨ Features

- **Market Overview:** Compare performance of multiple assets across customizable time horizons (from 1 month to 20+ years).
- **Global Top News:** Stay updated with a live feed of the top financial news articles across the US, European, and Asian markets.
- **Yield Curve Animations:** Watch the historical evolution (up to 10 years) of both the US Treasury and Euro Area yield curves through an interactive Plotly slider.
- **Advanced Analytics:** Auto-generated correlation matrices and annualized historical volatility rankings for selected assets.
- **Premium Design:** Features a customized "Cream" aesthetic, with transparent charts, card-based UI elements, and modern typography.

## 🛠️ Data Sources

- **Yahoo Finance (`yfinance`):** Historical price data for stocks, commodities, and FX. Top news aggregation.
- **US Treasury:** Official daily yield curve rates parsed directly from the Treasury's XML and CSV APIs.
- **European Central Bank (ECB):** Euro Area yield curve data fetched from the official ECB Data API.

## 🚀 How to Run Locally

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Vafaure/Market-dashboard.git
   cd Market-dashboard
   ```

2. **Install the requirements:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   streamlit run streamlit_app.py
   ```

---
*Created by [Valentin Fauré](https://www.linkedin.com/in/faure-valentin)*
