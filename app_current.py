import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- Configuration & Portfolio Data ---
st.set_page_config(page_title="My Portfolio Dashboard", layout="wide")

# Your current active holdings and invested capital
portfolio = {
    "VTV": 700,
    "GOOGL": 300,
    "TGT": 300
}

st.title("Capital Appreciation Tracking Dashboard")
st.markdown("Monitoring momentum, moving averages, and technical indicators for active capital rotations.")

# --- Data Fetching Function ---
@st.cache_data(ttl=3600) # Caches data for 1 hour to avoid API rate limits
def get_stock_data(tickers):
    end_date = datetime.today()
    start_date = end_date - timedelta(days=365) # Pull 1 year of data for 52-wk metrics
    data = yf.download(tickers, start=start_date, end=end_date)
    return data['Close']

# Fetch data for all tickers in the portfolio
tickers = list(portfolio.keys())
close_prices = get_stock_data(tickers)

# --- Indicator Calculations & Display ---
st.header("Current Holdings & Indicators")

cols = st.columns(len(tickers))

for i, ticker in enumerate(tickers):
    with cols[i]:
        st.subheader(ticker)
        
        # Calculate Indicators
        current_price = close_prices[ticker].iloc[-1]
        invested = portfolio[ticker]
        estimated_shares = invested / current_price # Approximation based on initial capital
        current_value = estimated_shares * current_price
        
        high_52 = close_prices[ticker].max()
        low_52 = close_prices[ticker].min()
        ma_50 = close_prices[ticker].tail(50).mean()
        ma_200 = close_prices[ticker].tail(200).mean()
        
        # Display Core Metrics
        st.metric(label="Current Price", value=f"${current_price:.2f}")
        st.write(f"**Allocated Capital:** ${invested}")
        
        # Technical Indicator breakdown
        st.markdown("---")
        st.markdown("**Capital Appreciation Indicators:**")
        
        # 50 vs 200 SMA (Momentum indicator)
        trend = "🟢 Bullish" if ma_50 > ma_200 else "🔴 Bearish"
        st.write(f"- **50-Day MA:** ${ma_50:.2f}")
        st.write(f"- **200-Day MA:** ${ma_200:.2f}")
        st.write(f"- **Trend (50 vs 200):** {trend}")
        
        # 52-Week Range
        st.write(f"- **52-Week High:** ${high_52:.2f}")
        st.write(f"- **52-Week Low:** ${low_52:.2f}")
        
        # Proximity to 52-week high (Good for setting rotation rules)
        drawdown_from_high = ((current_price - high_52) / high_52) * 100
        st.write(f"- **Distance from 52w High:** {drawdown_from_high:.2f}%")

st.markdown("---")

# --- Interactive Charting ---
st.header("Interactive Price Trends")
selected_ticker = st.selectbox("Select a stock to view its 1-year trajectory:", tickers)

# Build a Plotly chart for the selected stock
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=close_prices.index, 
    y=close_prices[selected_ticker], 
    mode='lines', 
    name='Close Price',
    line=dict(color='#1f77b4', width=2)
))

# Add the 50-day moving average overlay
fig.add_trace(go.Scatter(
    x=close_prices.index, 
    y=close_prices[selected_ticker].rolling(window=50).mean(), 
    mode='lines', 
    name='50-Day MA',
    line=dict(color='#ff7f0e', width=1, dash='dash')
))

fig.update_layout(
    title=f"{selected_ticker} - 1 Year Price Action vs. 50-Day MA",
    xaxis_title="Date",
    yaxis_title="Price (USD)",
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)

# --- Rotation Rules Tracker ---
st.header("Rotation Alerts & Catalysts")
st.info("""
**Active Monitoring Checklist:**
*   **VTV:** Monitor if the 50-day moving average drops below the 200-day moving average. If yield drops and momentum slows, consider rotating new monthly inflows to dividend-growth alternatives.
*   **GOOGL:** Watch closely for margin compression news due to AI CapEx spending. 
*   **TGT:** High alert around mid-May earnings. If top-line revenue contracts significantly, evaluate reallocating to stronger big-box peers.
""")
