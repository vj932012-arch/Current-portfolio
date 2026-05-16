import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta  # New library for technical indicators
import plotly.graph_objects as go
from plotly.subplots import make_subplots # Import for multi-plot charting
from datetime import datetime, timedelta

# --- Configuration & Portfolio Data ---
st.set_page_config(page_title="My Portfolio Dashboard", layout="wide")

# Your exact fractional shares and average cost basis from previous session
portfolio = {
    "VTV": {"shares": 3.3689, "average_cost": 207.78},
    "GOOGL": {"shares": 0.3804, "average_cost": 394.25}, 
    "TGT": {"shares": 1.1576, "average_cost": 129.59}
}

st.title("Fractional Share Performance & Rotation Dashboard")
st.markdown("Monitoring precise returns, momentum, and technical indicators, including RSI.")

# --- Custom Styling for Borders (CSS) ---
# This adds subtle borders, padding, and subtle backgrounds to metrics and other components.
st.markdown(
    """
    <style>
    div.stMetric {
        border: 1px solid #e6e9ef;
        border-radius: 0.5rem;
        padding: 1rem;
        background-color: #fcfcfc;
        margin-bottom: 0.5rem;
    }
    div.element-container:has(> iframe) {
        border: 1px solid #ddd;
        border-radius: 0.5rem;
        padding: 0.5rem;
        margin-top: 1rem;
        background-color: white;
    }
    . holdings-info-box {
        border: 1px solid #ddd;
        padding: 15px;
        border-radius: 8px;
        background-color: #f8f9fa;
        margin-bottom: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Enhanced Data Fetching Function ---
@st.cache_data(ttl=3600)
def get_comprehensive_stock_data(tickers, period="1y"):
    """
    Fetches historical Open, High, Low, Close, Volume data (OHLCV) for a single ticker or list.
    """
    data = yf.download(tickers, period=period, group_by='ticker')
    return data

# Pre-fetch comprehensive data for all portfolio holdings (needed for RSI calculation).
tickers = list(portfolio.keys())
all_holdings_data = get_comprehensive_stock_data(tickers, period="1y")

# --- Portfolio Performance Summary ---
st.header("Overall Portfolio Performance")

total_invested = 0
total_current_value = 0

for ticker in tickers:
    # Use 'Close' price for metrics. Multi-level data access: (Ticker, Price Type)
    current_close = all_holdings_data[(ticker, 'Close')].iloc[-1]
    shares = portfolio[ticker]["shares"]
    avg_cost = portfolio[ticker]["average_cost"]
    
    invested = shares * avg_cost
    current_value = shares * current_close
    
    total_invested += invested
    total_current_value += current_value

total_profit_loss = total_current_value - total_invested
total_return_pct = (total_profit_loss / total_invested) * 100 if total_invested > 0 else 0

# Apply styled borders to metrics summary
col1, col2, col3 = st.columns(3)
col1.metric("Total Invested (Cost Basis)", f"${total_invested:.2f}")
col2.metric("Current Portfolio Value", f"${total_current_value:.2f}", f"{total_profit_loss:.2f}")
col3.metric("Total Return (%)", f"{total_return_pct:.2f}%")

st.markdown("---")

# --- Individual Holdings & Technical Indicators ---
st.header("Current Holdings & Key Indicators")

cols = st.columns(len(tickers))

for i, ticker in enumerate(tickers):
    with cols[i]:
        # Wrap content in a styled div for a clean border box.
        st.markdown(f'<div class="holdings-info-box">', unsafe_allow_html=True)
        st.subheader(ticker)
        
        # Core data access from comprehensive pre-fetch.
        ticker_data = all_holdings_data[ticker].copy() # Get DataFrame for single ticker
        current_close_price = ticker_data['Close'].iloc[-1]
        shares = portfolio[ticker]["shares"]
        avg_cost = portfolio[ticker]["average_cost"]
        
        # Core performance metrics
        invested = shares * avg_cost
        current_value = shares * current_close_price
        profit_loss = current_value - invested
        return_pct = (profit_loss / invested) * 100 if invested > 0 else 0
        
        # Technical metrics calculations
        ticker_close_prices = ticker_data['Close']
        high_52 = ticker_close_prices.max()
        low_52 = ticker_close_prices.min()
        ma_50 = ticker_close_prices.tail(50).mean()
        ma_200 = ticker_close_prices.tail(200).mean()
        
        # --- NEW: Precise RSI Calculation using pandas_ta ---
        # This computes the standard 14-period RSI using the Close prices.
        rsi_series = ticker_data.ta.rsi(length=14)
        current_rsi_value = rsi_series.iloc[-1] if not rsi_series.empty else "N/A"
        
        # Display Performance within the styled box
        st.metric(label="Current Price", value=f"${current_close_price:.2f}", delta=f"{return_pct:.2f}% vs Avg Cost")
        st.write(f"**Shares Owned:** {shares}")
        st.write(f"**Average Cost:** ${avg_cost:.2f}")
        st.write(f"**Current Value:** ${current_value:.2f}")
        
        # Technical Indicator Breakdown
        st.markdown("---")
        st.markdown("**Core Indicators:**")
        
        trend_label = "Bullish" if ma_50 > ma_200 else "Bearish"
        trend_icon = "🟢" if trend_label == "Bullish" else "🔴"
        
        st.write(f"- **Moving Average Trend (50 vs 200):** {trend_icon} {trend_label}")
        
        dist_from_52w_high = ((current_close_price - high_52) / high_52) * 100
        st.write(f"- **Distance from 52w High:** {dist_from_52w_high:.2f}%")
        
        # --- NEW: Live RSI Status with actionable context ---
        if isinstance(current_rsi_value, float):
            rsi_status = "Overbought (>70)" if current_rsi_value > 70 else (
                "Oversold (<30)" if current_rsi_value < 30 else "Normal (30-70)"
            )
            rsi_icon = "⚠️" if rsi_status == "Overbought (>70)" else (
                "🟢" if rsi_status == "Oversold (<30)" else "⚖️"
            )
            st.write(f"- **RSI (14-day):** **{current_rsi_value:.2f}** ({rsi_icon} {rsi_status})")
        else:
            st.write(f"- **RSI (14-day):** {current_rsi_value}")
            
        st.markdown('</div>', unsafe_allow_html=True) # Close the styled box

st.markdown("---")

# --- Interactive Charting with Integrated RSI ---
st.header("Interactive Price Trends & Performance vs. Indicators")
selected_ticker = st.selectbox("Select a stock to view detailed trajectory & integrated RSI:", tickers)

# Access historical data for charting and additional technical lines.
selected_stock_hist = all_holdings_data[selected_ticker].copy() # Multi-index data access
selected_stock_hist['MA50'] = selected_stock_hist['Close'].rolling(window=50).mean()
selected_stock_hist['MA200'] = selected_stock_hist['Close'].rolling(window=200).mean()

# Calculate the RSI series for the chart using the comprehensive OHLC data.
selected_stock_hist['RSI'] = selected_stock_hist.ta.rsi(length=14)

# Create Plotly subplots with a large Price chart on top and a smaller RSI chart below,
# sharing the same x-axis (Date) for precise analysis.
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                    vertical_spacing=0.03, # Reduce vertical separation
                    subplot_titles=(f"{selected_ticker} Price Action & MAs vs. Your Avg Cost", "Relative Strength Index (RSI)"),
                    row_heights=[0.7, 0.3]) # Set relative chart sizes

# --- Plot 1: Price Action & Indicators (Row 1) ---
# Current Close Price Line
fig.add_trace(go.Scatter(
    x=selected_stock_hist.index, 
    y=selected_stock_hist['Close'], 
    mode='lines', 
    name='Close Price',
    line=dict(color='#1f77b4', width=2)
), row=1, col=1)

# 50-day Moving Average (EMA) Line
fig.add_trace(go.Scatter(
    x=selected_stock_hist.index, 
    y=selected_stock_hist['MA50'], 
    mode='lines', 
    name='50-Day MA',
    line=dict(color='#ff7f0e', width=1.5, dash='dash')
), row=1, col=1)

# 200-day Moving Average (EMA) Line
fig.add_trace(go.Scatter(
    x=selected_stock_hist.index, 
    y=selected_stock_hist['MA200'], 
    mode='lines', 
    name='200-Day MA',
    line=dict(color='#2ca02c', width=1, dash='dot')
), row=1, col=1)

# Horizontal Line indicating your Average Cost baseline
avg_cost_chart = portfolio[selected_ticker]["average_cost"]
fig.add_trace(go.Scatter(
    x=[selected_stock_hist.index.min(), selected_stock_hist.index.max()],
    y=[avg_cost_chart, avg_cost_chart],
    mode='lines',
    name='Your Avg Cost',
    line=dict(color='#d62728', width=2, dash='dot')
), row=1, col=1)

# --- NEW: Plot 2: RSI Indicator with Overbought/Oversold thresholds (Row 2) ---
# RSI Line
fig.add_trace(go.Scatter(
    x=selected_stock_hist.index, 
    y=selected_stock_hist['RSI'], 
    mode='lines', 
    name='RSI',
    line=dict(color='#9467bd', width=2)
), row=2, col=1)

# Threshold reference lines: 70 (Overbought) and 30 (Oversold).
fig.add_shape(type="line", x0=selected_stock_hist.index.min(), y0=70, x1=selected_stock_hist.index.max(), y1=70,
              line=dict(color="red", width=1, dash="dash"), row=2, col=1)
fig.add_shape(type="line", x0=selected_stock_hist.index.min(), y0=30, x1=selected_stock_hist.index.max(), y1=30,
              line=dict(color="green", width=1, dash="dash"), row=2, col=1)

# Figure Layout configuration for a professional, clean visual style.
fig.update_layout(
    template="plotly_white",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), # Legend positioning
    margin=dict(l=20, r=20, t=50, b=20),
    height=750 # Total figure height
)

# Update Axis labels and standardized RSI range
fig.update_yaxes(title_text="Price (USD)", row=1, col=1)
fig.update_yaxes(title_text="RSI Value", row=2, col=1, range=[0, 100]) # Keep RSI scale fixed

# Set shared X-axis title
fig.update_xaxes(title_text="Date", row=2, col=1)

# Display the final composite chart within an interactive, styled border area.
st.plotly_chart(fig, use_container_width=True)

# --- Rotation Rules Tracker ---
st.header("Rotation Alerts & Catalysts Tracker")
st.info("""
**Active Monitoring Checklist (Mid-2026 Context):**
*   **RSI Utilization:** Use the RSI values on your dashboard (both live metrics and the chart) to confirm other technical signals. For instance, if VTV or GOOGL has a bullish crossover (50 MA > 200 MA) but an RSI well over 70, it suggests caution before immediately allocating new capital at a potential local peak.
*   **VTV Baseline:** Monitor if the upward momentum slows. A breakdown below the 200-day moving average on your chart warrants pausing recurring investments.
*   **GOOGL Premium:** Watch for margin compression news following massive AI CapEx spending.
*   **TGT Support:** Major alert surrounding May 20 earnings. If revenue contracts significantly, evaluate reallocating to stronger big-box peers.
""")
