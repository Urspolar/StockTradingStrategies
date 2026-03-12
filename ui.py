import streamlit as st
from strategy import get_recommendation
import pandas as pd

@st.cache_data(ttl=3600)  # Cache results for 1 hour
def get_recommendation_cached(ticker, period='2y'):
    return get_recommendation(ticker, period=period)

st.set_page_config(page_title="Stock Trading Strategy Analyzer", layout="wide")

st.title("📈 Stock Trading Strategy Analyzer")
st.markdown("""
This application analyzes historical stock market data to find simple daily strategies that have historically increased money.
""")

# Sidebar for inputs
st.sidebar.header("Input")
ticker_input = st.sidebar.text_input("Enter Ticker(s) separated by space", value="AAPL TSLA SPY")

# Popular Stocks section in the sidebar
st.sidebar.divider()
st.sidebar.header("🔥 Popular Stocks (Last 6 Months)")
popular_stocks = ["AAPL", "TSLA", "SPY", "MSFT", "NVDA", "AMZN"]
for ticker in popular_stocks:
    res = get_recommendation_cached(ticker, period='6mo')
    if res:
        rec = res['recommended']
        # Use a simpler display for sidebar
        st.sidebar.metric(ticker, f"{rec['total_return']:.2%}", help=f"Best Strategy: {rec['strategy']}")
        st.sidebar.caption(f"Strategy: {rec['strategy']}")

def display_results(ticker, period='2y'):
    res = get_recommendation_cached(ticker, period=period)
    if not res:
        st.error(f"Could not analyze {ticker}. Please check the ticker symbol.")
        return

    st.subheader(f"Results for {ticker}")
    st.write(f"Analyzed over {res['period_days']} market days.")

    rec = res['recommended']

    col1, col2, col3 = st.columns(3)
    col1.metric("Best Strategy", rec['strategy'])
    col2.metric("Total Return", f"{rec['total_return']:.2%}")
    col3.metric("Win Rate", f"{rec['win_rate']:.1%}")

    # Reasoning and Action
    reason = f"Based on the last {res['period_days']} market days, '{rec['strategy']}' had the highest historical return of {rec['total_return']:.2%}. "
    if rec['win_rate'] > 0.55:
        reason += f"It also maintains a strong win rate of {rec['win_rate']:.1%}. "
    else:
        reason += f"While the win rate is {rec['win_rate']:.1%}, the size of the winning trades significantly outweighed the losing ones. "

    st.info(f"**Why:** {reason}")

    action_map = {
        'Overnight': "BUY at Market Close, SELL at next day's Open.",
        'Momentum': "BUY at Market Open if yesterday was positive, SELL at Close.",
        'Mean Reversion': "BUY at Market Open if yesterday was negative, SELL at Close.",
        'Gap Down': "BUY at Market Open if gapped down > 0.5%, SELL at Close.",
        'Weekend Effect': "BUY Friday Close, SELL Monday Open.",
        '3-Day Trend': "BUY at Market Open if last 3 days were positive, SELL at Close.",
        'RSI Reversion': "BUY at Market Open if RSI < 35, SELL at Close.",
        'Intraday': "BUY at Market Open, SELL at same day's Close."
    }

    st.success(f"**Daily Action:** {action_map.get(rec['strategy'], 'BUY at Market Open, SELL at same day Close.')}")

    # Detailed Results Table
    df = pd.DataFrame(res['results'])
    df = df[['strategy', 'description', 'total_return', 'win_rate', 'trade_count']]
    df['total_return'] = df['total_return'].apply(lambda x: f"{x:.2%}")
    df['win_rate'] = df['win_rate'].apply(lambda x: f"{x:.1%}")
    st.table(df)

# Main logic
if ticker_input:
    tickers = [t.strip().upper() for t in ticker_input.split() if t.strip()]
    if not tickers:
        st.warning("Please enter at least one ticker.")
    else:
        if len(tickers) > 1:
            # Selection for multiple tickers as requested
            selected_ticker = st.selectbox("Select a ticker to view results", options=tickers)
            display_results(selected_ticker)
        else:
            display_results(tickers[0])
else:
    st.info("Enter one or more stock tickers in the sidebar to begin analysis.")
