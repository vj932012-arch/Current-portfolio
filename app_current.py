import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
import plotly.express as px  
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# --- Configuration & Portfolio Data ---
st.set_page_config(page_title="My Portfolio Dashboard", layout="wide")

# Your exact fractional shares and average cost basis
portfolio = {
    "VTV": {"shares": 3.3689, "average_cost": 207.78},
    "GOOGL": {"shares": 0.3804, "average_cost": 394.25}, 
    "TGT": {"shares": 1.1576, "average_cost": 129.59}
}

st.title("Active Portfolio & Rotation Dashboard")
st.markdown("Monitoring returns, momentum, and dynamic catalysts for active rotations.")

# --- Custom Styling for Dynamic Light/Dark Themes (CSS) ---
st.markdown(
    """
    <style>
    div.stMetric {
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 0.5rem;
        padding: 1rem;
        background-color: var(--secondary-background-color); 
        margin-bottom: 0.5rem;
    }
    div.element-container:has(> iframe) {
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 0.5rem;
        padding: 0.5rem;
        margin-top: 1rem;
        background-color: transparent;
    }
    .holdings-info-box {
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 15px;
        border-radius: 8px;
        background-color: var(--secondary-background-color);
        margin-bottom: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Enhanced Data Fetching Functions ---
@st.cache_data(ttl=900) 
def get_comprehensive_stock_data(tickers, period="1y"):
    return yf.download(tickers, period=period, group_by='ticker')

@st.cache_data(ttl=3600) 
def get_fundamental_data(ticker):
    try:
        info = yf.Ticker(ticker).info
        
        # ETFs use 'trailingPE', Stocks use 'forwardPE'
        fwd_pe = info.get('forwardPE') or info.get('trailingPE') or 'N/A'
        
        # ETFs use 'yield', Stocks use 'dividendYield'
        div_yield = info.get('dividendYield') or info.get('yield') or 0
        
        if isinstance(fwd_pe, float): 
            fwd_pe = round(fwd_pe, 2)
            
        # Safely handle yfinance's inconsistent decimal vs percentage returns
        if div_yield and div_yield > 0:
            if div_yield > 1: # If yfinance already returned it as 2.5 instead of 0.025
                div_yield_str = f"{div_yield:.2f}%"
            else:
                div_yield_str = f"{div_yield * 100:.2f}%"
        else:
            div_yield_str = "N/A"
            
        return fwd_pe, div_yield_str
    except Exception:
        return "N/A", "N/A"

# Pre-fetch comprehensive data for all portfolio holdings
tickers = list(portfolio.keys())
all_holdings_data = get_comprehensive_stock_data(tickers, period="1y")

# --- Portfolio Performance & Allocation Summary ---
st.header("Overall Portfolio Status")

total_invested = 0
total_current_value = 0
allocation_data = []

for ticker in tickers:
    current_close = all_holdings_data[(ticker, 'Close')].iloc[-1]
    shares = portfolio[ticker]["shares"]
    avg_cost = portfolio[ticker]["average_cost"]
    
    invested = shares * avg_cost
    current_value = shares * current_close
    
    total_invested += invested
    total_current_value += current_value
    allocation_data.append({"Asset": ticker, "Value": current_value})

total_profit_loss = total_current_value - total_invested
total_return_pct = (total_profit_loss / total_invested) * 100 if total_invested > 0 else 0

# Metrics Layout
col1, col2, col3 = st.columns(3)
col1.metric("Total Invested (Cost Basis)", f"${total_invested:.2f}")
col2.metric("Current Portfolio Value", f"${total_current_value:.2f}", f"{total_profit_loss:.2f}")
col3.metric("Total Return (%)", f"{total_return_pct:.2f}%")

st.markdown("---")

# Portfolio Concentration Visualization
st.subheader("Current Capital Allocation")
df_alloc = pd.DataFrame(allocation_data)
fig_pie = px.pie(df_alloc, values='Value', names='Asset', hole=0.4, 
                 color_discrete_sequence=px.colors.qualitative.Pastel)
fig_pie.update_layout(height=350, margin=dict(t=20, b=20, l=0, r=0))
st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")

# --- Individual Holdings & Technical Indicators ---
st.header("Current Holdings & Key Indicators")

cols = st.columns(len(tickers))

for i, ticker in enumerate(tickers):
    with cols[i]:
        st.markdown(f'<div class="holdings-info-box">', unsafe_allow_html=True)
        st.subheader(ticker)
        
        # Core data access
        ticker_data = all_holdings_data[ticker].copy() 
        current_close_price = ticker_data['Close'].iloc[-1]
        shares = portfolio[ticker]["shares"]
        avg_cost = portfolio[ticker]["average_cost"]
        
        invested = shares * avg_cost
        current_value = shares * current_close_price
        profit_loss = current_value - invested
        return_pct = (profit_loss / invested) * 100 if invested > 0 else 0
        
        ticker_close_prices = ticker_data['Close']
        high_52 = ticker_close_prices.max()
        ma_50 = ticker_close_prices.tail(50).mean()
        ma_200 = ticker_close_prices.tail(200).mean()
        
        rsi_series = ticker_data.ta.rsi(length=14)
        current_rsi_value = rsi_series.iloc[-1] if not rsi_series.empty else "N/A"
        
        # Automated Fundamentals
        fwd_pe, div_yield = get_fundamental_data(ticker)
        
        st.metric(label="Current Price", value=f"${current_close_price:.2f}", delta=f"{return_pct:.2f}% vs Avg Cost")
        st.write(f"**Shares Owned:** {shares}")
        st.write(f"**Average Cost:** ${avg_cost:.2f}")
        st.write(f"**Current Value:** ${current_value:.2f}")
        
        st.markdown("---")
        st.markdown("**Fundamentals:**")
        st.write(f"- **Forward P/E:** {fwd_pe}")
        st.write(f"- **Dividend Yield:** {div_yield}")
        
        st.markdown("---")
        st.markdown("**Core Technicals:**")
        
        trend_label = "Bullish" if ma_50 > ma_200 else "Bearish"
        st.write(f"- **Trend (50v200):** {'🟢' if trend_label == 'Bullish' else '🔴'} {trend_label}")
        st.write(f"- **Dist from 52w High:** {((current_close_price - high_52) / high_52) * 100:.2f}%")
        
        if isinstance(current_rsi_value, float):
            rsi_status = "Overbought" if current_rsi_value > 70 else ("Oversold" if current_rsi_value < 30 else "Normal")
            rsi_icon = "⚠️" if rsi_status == "Overbought" else ("🟢" if rsi_status == "Oversold" else "⚖️")
            st.write(f"- **RSI (14d):** **{current_rsi_value:.1f}** ({rsi_icon} {rsi_status})")
            
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# --- Dynamic Traffic Light Alert System ---
st.header("🚦 Active Action Alerts")
alerts_triggered = False

for ticker in tickers:
    ticker_data = all_holdings_data[ticker].copy()
    current_rsi = ticker_data.ta.rsi(length=14).iloc[-1]
    ma_50 = ticker_data['Close'].tail(50).mean()
    ma_200 = ticker_data['Close'].tail(200).mean()
    
    # RSI Alerts
    if current_rsi > 70:
        st.warning(f"**{ticker}:** Overbought (RSI: {current_rsi:.1f}). Consider pausing monthly DCA buys to avoid buying a local peak.")
        alerts_triggered = True
    elif current_rsi < 30:
        st.success(f"**{ticker}:** Oversold (RSI: {current_rsi:.1f}). This may present a discounted entry point for your next rotation.")
        alerts_triggered = True
        
    # Moving Average Alerts
    if ma_50 < ma_200:
        st.error(f"**{ticker}:** Bearish Trend (50MA below 200MA). Monitor closely for structural weakness before adding capital.")
        alerts_triggered = True

if not alerts_triggered:
    st.info("No active technical alerts across your portfolio. Current trends are stable.")

st.markdown("---")

# --- Interactive Charting ---
st.header("Interactive Price Trends & Integrated RSI")
selected_ticker = st.selectbox("Select a stock to view detailed trajectory:", tickers)

selected_stock_hist = all_holdings_data[selected_ticker].copy() 
selected_stock_hist['MA50'] = selected_stock_hist['Close'].rolling(window=50).mean()
selected_stock_hist['MA200'] = selected_stock_hist['Close'].rolling(window=200).mean()
selected_stock_hist['RSI'] = selected_stock_hist.ta.rsi(length=14)

fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                    vertical_spacing=0.03, 
                    subplot_titles=(f"{selected_ticker} Price Action & MAs vs. Avg Cost", "Relative Strength Index (RSI)"),
                    row_heights=[0.7, 0.3]) 

# Row 1: Price Action
fig.add_trace(go.Scatter(x=selected_stock_hist.index, y=selected_stock_hist['Close'], mode='lines', name='Close Price', line=dict(color='#1f77b4', width=2)), row=1, col=1)
fig.add_trace(go.Scatter(x=selected_stock_hist.index, y=selected_stock_hist['MA50'], mode='lines', name='50-Day MA', line=dict(color='#ff7f0e', width=1.5, dash='dash')), row=1, col=1)
fig.add_trace(go.Scatter(x=selected_stock_hist.index, y=selected_stock_hist['MA200'], mode='lines', name='200-Day MA', line=dict(color='#2ca02c', width=1, dash='dot')), row=1, col=1)

avg_cost_chart = portfolio[selected_ticker]["average_cost"]
fig.add_trace(go.Scatter(x=[selected_stock_hist.index.min(), selected_stock_hist.index.max()], y=[avg_cost_chart, avg_cost_chart], mode='lines', name='Your Avg Cost', line=dict(color='#d62728', width=2, dash='dot')), row=1, col=1)

# Row 2: RSI
fig.add_trace(go.Scatter(x=selected_stock_hist.index, y=selected_stock_hist['RSI'], mode='lines', name='RSI', line=dict(color='#9467bd', width=2)), row=2, col=1)
fig.add_shape(type="line", x0=selected_stock_hist.index.min(), y0=70, x1=selected_stock_hist.index.max(), y1=70, line=dict(color="red", width=1, dash="dash"), row=2, col=1)
fig.add_shape(type="line", x0=selected_stock_hist.index.min(), y0=30, x1=selected_stock_hist.index.max(), y1=30, line=dict(color="green", width=1, dash="dash"), row=2, col=1)

fig.update_layout(template="plotly_white", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), margin=dict(l=20, r=20, t=50, b=20), height=750)
fig.update_yaxes(title_text="Price (USD)", row=1, col=1)
fig.update_yaxes(title_text="RSI Value", row=2, col=1, range=[0, 100]) 
fig.update_xaxes(title_text="Date", row=2, col=1)

st.plotly_chart(fig, use_container_width=True)
