import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- Configuration & Portfolio Data ---
st.set_page_config(page_title="My Portfolio Dashboard", layout="wide")

# Plug in your exact fractional shares and average cost here.
# The numbers below are approximations for $700 in VTV, $300 in GOOGL, and $300 in TGT.
portfolio = {
    "VTV": {"shares": 3.3689, "average_cost": 207.78},
    "GOOGL": {"shares": 0.3804, "average_cost": 394.25}, 
    "TGT": {"shares": 1.1576, "average_cost": 129.59}    
}

st.title("Fractional Share Performance Dashboard")
st.markdown("Monitoring precise returns, momentum, and technical indicators.")

# --- Data Fetching Function ---
@st.cache_data(ttl=3600)
def get_stock_data(tickers):
    end_date = datetime.today()
    start_date = end_date - timedelta(days=365)
    data = yf.download(tickers, start=start_date, end=end_date)
    return data['Close']

# Fetch data for all tickers
tickers = list(portfolio.keys())
close_prices = get_stock_data(tickers)

# --- Portfolio Performance Summary ---
st.header("Overall Portfolio Performance")

total_invested = 0
total_current_value = 0

for ticker in tickers:
    current_price = close_prices[ticker].iloc[-1]
    shares = portfolio[ticker]["shares"]
    avg_cost = portfolio[ticker]["average_cost"]
    
    invested = shares * avg_cost
    current_value = shares * current_price
    
    total_invested += invested
    total_current_value += current_value

total_profit_loss = total_current_value - total_invested
total_return_pct = (total_profit_loss / total_invested) * 100 if total_invested > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Total Invested (Cost Basis)", f"${total_invested:.2f}")
col2.metric("Current Portfolio Value", f"${total_current_value:.2f}", f"{total_profit_loss:.2f}")
col3.metric("Total Return (%)", f"{total_return_pct:.2f}%")

st.markdown("---")

# --- Individual Holdings & Indicators ---
st.header("Current Holdings & Technical Indicators")

cols = st.columns(len(tickers))

for i, ticker in enumerate(tickers):
    with cols[i]:
        st.subheader(ticker)
        
        # Calculations
        current_price = close_prices[ticker].iloc[-1]
        shares = portfolio[ticker]["shares"]
        avg_cost = portfolio[ticker]["average_cost"]
        
        invested = shares * avg_cost
        current_value = shares * current_price
        
        profit_loss = current_value - invested
        return_pct = (profit_loss / invested) * 100 if invested > 0 else 0
        
        high_52 = close_prices[ticker].max()
        low_52 = close_prices[ticker].min()
        ma_50 = close_prices[ticker].tail(50).mean()
        ma_200 = close_prices[ticker].tail(200).mean()
        
        # Display Performance
        st.metric(label="Current Price", value=f"${current_price:.2f}", delta=f"{return_pct:.2f}% vs Avg Cost")
        st.write(f"**Shares Owned:** {shares}")
        st.write(f"**Average Cost:** ${avg_cost:.2f}")
        st.write(f"**Current Value:** ${current_value:.2f}")
        
        # Technical Indicator breakdown
        st.markdown("---")
        st.markdown("**Technical Indicators:**")
        
        trend = "🟢 Bullish" if ma_50 > ma_200 else "🔴 Bearish"
        st.write(f"- **50-Day MA:** ${ma_50:.2f}")
        st.write(f"- **200-Day MA:** ${ma_200:.2f}")
        st.write(f"- **Trend (50 vs 200):** {trend}")
        
        drawdown_from_high = ((current_price - high_52) / high_52) * 100
        st.write(f"- **Distance from 52w High:** {drawdown_from_high:.2f}%")

st.markdown("---")

# --- Interactive Charting ---
st.header("Interactive Price Trends")
selected_ticker = st.selectbox("Select a stock to view its trajectory vs. Your Average Cost:", tickers)

fig = go.Figure()
# Current Price Line
fig.add_trace(go.Scatter(
    x=close_prices.index, 
    y=close_prices[selected_ticker], 
    mode='lines', 
    name='Close Price',
    line=dict(color='#1f77b4', width=2)
))

# 50-day MA Line
fig.add_trace(go.Scatter(
    x=close_prices.index, 
    y=close_prices[selected_ticker].rolling(window=50).mean(), 
    mode='lines', 
    name='50-Day MA',
    line=dict(color='#ff7f0e', width=1, dash='dash')
))

# Average Cost Horizontal Line
avg_cost = portfolio[selected_ticker]["average_cost"]
fig.add_trace(go.Scatter(
    x=[close_prices.index.min(), close_prices.index.max()],
    y=[avg_cost, avg_cost],
    mode='lines',
    name='Your Average Cost',
    line=dict(color='green', width=2, dash='dot')
))

fig.update_layout(
    title=f"{selected_ticker} - 1 Year Price Action vs. Average Cost",
    xaxis_title="Date",
    yaxis_title="Price (USD)",
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)
