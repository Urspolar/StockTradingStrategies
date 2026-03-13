import streamlit as st
from strategy import get_recommendation
import pandas as pd

@st.cache_data(ttl=3600)  # Cache results for 1 hour
def get_recommendation_cached(ticker, period='2y'):
    return get_recommendation(ticker, period=period)

@st.cache_data(ttl=86400) # Cache for 24 hours
def get_top_performers_cached(n=10, period='6mo'):
    from strategy import get_top_performers
    return get_top_performers(n=n, period=period)

st.set_page_config(page_title="Stock Trading Strategy Analyzer", layout="wide")

st.title("📈 Stock Trading Strategy Analyzer")
st.markdown("""
This application analyzes historical stock market data to find simple daily strategies that have historically increased money.
""")

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
    st.info(f"**Why:** {rec.get('reasoning', 'Best historical performance.')}")

    st.success(f"**Daily Action:** {rec.get('action', 'BUY at Market Open, SELL at same day Close.')}")

    # Detailed Results Table
    df = pd.DataFrame(res['results'])
    df = df[['strategy', 'description', 'total_return', 'win_rate', 'trade_count']]
    df['total_return'] = df['total_return'].apply(lambda x: f"{x:.2%}")
    df['win_rate'] = df['win_rate'].apply(lambda x: f"{x:.1%}")

    # Rename columns for better display
    df.columns = ['Strategy', 'Description', 'Return', 'Win%', 'Trades']
    df.index = df.index + 1
    st.table(df)

# Sidebar for inputs
st.sidebar.header("Input")
ticker_input = st.sidebar.text_input("Enter Ticker(s) separated by space", value="AAPL TSLA SPY")
analyze_button = st.sidebar.button("Analyze")

if ticker_input:
    tickers = ticker_input.upper().split()
    if not tickers:
        st.sidebar.warning("Please enter at least one ticker.")
    else:
        if len(tickers) > 1:
            selected_ticker = st.sidebar.selectbox("Select Ticker to View", options=tickers)
        else:
            selected_ticker = tickers[0]
            st.sidebar.info(f"Selected: **{selected_ticker}**")

        num_days = st.sidebar.number_input("Number of days for analysis", value=730, min_value=1, step=1)
        period = f"{num_days}d"

        display_results(selected_ticker, period=period)

st.sidebar.divider()
st.sidebar.header("🏆 Top 10 S&P 500 Performers (6mo)")

with st.sidebar:
    with st.spinner("Calculating S&P 500 performance..."):
        top_performers = get_top_performers_cached(n=10, period='6mo')

    for item in top_performers:
        ticker = item['ticker']
        price_perf = item['performance']

        # Get best strategy for this ticker
        res = get_recommendation_cached(ticker, period='6mo')
        if res:
            rec = res['recommended']
            st.metric(ticker, f"{price_perf:.2%}", help=f"Best Strategy: {rec['strategy']} ({rec['total_return']:.2%})")
            st.caption(f"Best: {rec['strategy']} ({rec['total_return']:.2%})")
