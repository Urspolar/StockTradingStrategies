import yfinance as yf
import pandas as pd
import numpy as np

def fetch_data(ticker, period='2y'):
    """
    Fetches historical data for a ticker and handles formatting.
    """
    try:
        data = yf.download(ticker, period=period, progress=False)
        if data.empty:
            return None
        # Handle MultiIndex columns if present (common in newer yfinance versions)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None

def calculate_rsi(series, period=14):
    """
    Simple RSI calculation.
    """
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def backtest_overnight(data):
    """
    Strategy: Buy at market Close, sell at next day's Open.
    """
    if data is None or len(data) < 2:
        return None
    returns = (data['Open'].shift(-1) - data['Close']) / data['Close']
    returns = returns.dropna()
    return format_result('Overnight', 'Buy Close, Sell next Open', returns, "BUY at Market Close, SELL at next day's Open.")

def backtest_intraday(data):
    """
    Strategy: Buy at market Open, sell at same day's Close.
    """
    if data is None or len(data) < 1:
        return None
    returns = (data['Close'] - data['Open']) / data['Open']
    return format_result('Intraday', 'Buy Open, Sell same Close', returns, "BUY at Market Open, SELL at same day's Close.")

def backtest_momentum(data):
    """
    Strategy: Buy at Open, sell at Close if previous day was positive.
    """
    if data is None or len(data) < 2:
        return None
    prev_ret = (data['Close'].shift(1) - data['Open'].shift(1)) / data['Open'].shift(1)
    today_ret = (data['Close'] - data['Open']) / data['Open']
    trades = today_ret[prev_ret > 0]
    return format_result('Momentum', 'Buy Open, Sell Close if prev day +', trades, "BUY at Market Open if yesterday was positive, SELL at Close.")

def backtest_mean_reversion(data):
    """
    Strategy: Buy at Open, sell at Close if previous day was negative.
    """
    if data is None or len(data) < 2:
        return None
    prev_ret = (data['Close'].shift(1) - data['Open'].shift(1)) / data['Open'].shift(1)
    today_ret = (data['Close'] - data['Open']) / data['Open']
    trades = today_ret[prev_ret < 0]
    return format_result('Mean Reversion', 'Buy Open, Sell Close if prev day -', trades, "BUY at Market Open if yesterday was negative, SELL at Close.")

def backtest_gap_down(data):
    """
    Strategy: Buy at Open if it gaps down from previous close, sell at Close.
    """
    if data is None or len(data) < 2:
        return None
    gap = (data['Open'] - data['Close'].shift(1)) / data['Close'].shift(1)
    today_ret = (data['Close'] - data['Open']) / data['Open']
    trades = today_ret[gap < -0.005]
    return format_result('Gap Down', 'Buy Open if Gap < -0.5%, Sell Close', trades, "BUY at Market Open if gapped down > 0.5%, SELL at Close.")

def backtest_weekend_effect(data):
    """
    Strategy: Buy Friday Close, Sell Monday Open.
    """
    if data is None or len(data) < 2:
        return None
    # Day 4 is Friday, Day 0 is Monday
    data = data.copy()
    data['Day'] = data.index.dayofweek
    # Shift open to get the 'next trading day' open
    data['Next_Open'] = data['Open'].shift(-1)
    # Filter where today is Friday
    friday_data = data[data['Day'] == 4]
    returns = (friday_data['Next_Open'] - friday_data['Close']) / friday_data['Close']
    returns = returns.dropna()
    return format_result('Weekend Effect', 'Buy Friday Close, Sell Monday Open', returns, "BUY Friday Close, SELL Monday Open.")

def backtest_three_day_trend(data):
    """
    Strategy: Buy Open, Sell Close if last 3 days were positive.
    """
    if data is None or len(data) < 4:
        return None
    daily_ret = (data['Close'] - data['Open']) / data['Open']
    trend = (daily_ret.shift(1) > 0) & (daily_ret.shift(2) > 0) & (daily_ret.shift(3) > 0)
    trades = daily_ret[trend]
    return format_result('3-Day Trend', 'Buy Open, Sell Close if 3 days +', trades, "BUY at Market Open if last 3 days were positive, SELL at Close.")

def backtest_rsi_reversion(data):
    """
    Strategy: Buy Open, Sell Close if RSI < 35.
    """
    if data is None or len(data) < 15:
        return None
    rsi = calculate_rsi(data['Close'], 14)
    daily_ret = (data['Close'] - data['Open']) / data['Open']
    # If RSI of previous day is low, buy today's open
    trades = daily_ret[rsi.shift(1) < 35]
    return format_result('RSI Reversion', 'Buy Open, Sell Close if RSI < 35', trades, "BUY at Market Open if RSI < 35, SELL at Close.")

def backtest_sma_trend(data):
    """
    Strategy: Buy Open, Sell Close if yesterday's Close > 50-day SMA.
    """
    if data is None or len(data) < 51:
        return None
    sma50 = data['Close'].rolling(window=50).mean()
    daily_ret = (data['Close'] - data['Open']) / data['Open']
    trades = daily_ret[data['Close'].shift(1) > sma50.shift(1)]
    return format_result('SMA Trend', 'Buy Open, Sell Close if Close > SMA50', trades, "BUY at Market Open if yesterday's Close > 50-day SMA, SELL at Close.")

def backtest_bollinger_oversold(data):
    """
    Strategy: Buy Open, Sell Close if yesterday's Close < Lower Bollinger Band (20, 2).
    """
    if data is None or len(data) < 21:
        return None
    ma20 = data['Close'].rolling(window=20).mean()
    std20 = data['Close'].rolling(window=20).std()
    lower_band = ma20 - (2 * std20)
    daily_ret = (data['Close'] - data['Open']) / data['Open']
    trades = daily_ret[data['Close'].shift(1) < lower_band.shift(1)]
    return format_result('Bollinger Oversold', 'Buy Open if Close < Lower BB', trades, "BUY at Market Open if yesterday's Close < Lower Bollinger Band, SELL at Close.")

def backtest_volume_spike(data):
    """
    Strategy: Buy Open, Sell Close if yesterday's Volume > 1.5x 20-day average.
    """
    if data is None or len(data) < 21:
        return None
    vol_avg = data['Volume'].rolling(window=20).mean()
    daily_ret = (data['Close'] - data['Open']) / data['Open']
    trades = daily_ret[data['Volume'].shift(1) > 1.5 * vol_avg.shift(1)]
    return format_result('Volume Spike', 'Buy Open if Volume > 1.5x avg', trades, "BUY at Market Open if yesterday's Volume > 1.5x 20-day avg, SELL at Close.")

def backtest_ema_cross(data):
    """
    Strategy: Buy Open, Sell Close if 9-day EMA > 21-day EMA.
    """
    if data is None or len(data) < 22:
        return None
    ema9 = data['Close'].ewm(span=9, adjust=False).mean()
    ema21 = data['Close'].ewm(span=21, adjust=False).mean()
    daily_ret = (data['Close'] - data['Open']) / data['Open']
    trades = daily_ret[ema9.shift(1) > ema21.shift(1)]
    return format_result('EMA Cross', 'Buy Open if EMA9 > EMA21', trades, "BUY at Market Open if 9-day EMA > 21-day EMA, SELL at Close.")

def backtest_macd_signal(data):
    """
    Strategy: Buy Open, Sell Close if MACD > Signal line.
    """
    if data is None or len(data) < 35:
        return None
    exp1 = data['Close'].ewm(span=12, adjust=False).mean()
    exp2 = data['Close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    daily_ret = (data['Close'] - data['Open']) / data['Open']
    trades = daily_ret[macd.shift(1) > signal.shift(1)]
    return format_result('MACD Signal', 'Buy Open if MACD > Signal', trades, "BUY at Market Open if MACD > Signal Line, SELL at Close.")

def backtest_inside_day(data):
    """
    Strategy: Buy Open, Sell Close if yesterday was an inside day.
    """
    if data is None or len(data) < 3:
        return None
    prev_high = data['High'].shift(1)
    prev_low = data['Low'].shift(1)
    pprev_high = data['High'].shift(2)
    pprev_low = data['Low'].shift(2)
    inside_day = (prev_high < pprev_high) & (prev_low > pprev_low)
    daily_ret = (data['Close'] - data['Open']) / data['Open']
    trades = daily_ret[inside_day]
    return format_result('Inside Day', 'Buy Open if yesterday was Inside Day', trades, "BUY at Market Open if yesterday was an Inside Day, SELL at Close.")

def backtest_golden_cross(data):
    """
    Strategy: Buy Open, Sell Close if 50-day SMA > 200-day SMA.
    """
    if data is None or len(data) < 201:
        return None
    sma50 = data['Close'].rolling(window=50).mean()
    sma200 = data['Close'].rolling(window=200).mean()
    daily_ret = (data['Close'] - data['Open']) / data['Open']
    trades = daily_ret[sma50.shift(1) > sma200.shift(1)]
    return format_result('Golden Cross', 'Buy Open if SMA50 > SMA200', trades, "BUY at Market Open if 50-day SMA > 200-day SMA, SELL at Close.")

def format_result(name, desc, trades, action):
    if trades.empty:
        return None
    total_return = (1 + trades).prod() - 1
    win_rate = (trades > 0).mean()
    wins = trades[trades > 0]
    losses = trades[trades < 0]
    return {
        'strategy': name,
        'description': desc,
        'total_return': total_return,
        'win_rate': win_rate,
        'trade_count': len(trades),
        'avg_win': wins.mean() if not wins.empty else 0,
        'avg_loss': losses.mean() if not losses.empty else 0,
        'max_win': trades.max(),
        'max_loss': trades.min(),
        'action': action
    }

def generate_detailed_reasoning(rec, data, ticker):
    """
    Generates a deep analysis of why a strategy performed well.
    """
    if not rec or data is None or data.empty:
        return "Insufficient data for detailed analysis."

    strat_name = rec['strategy']
    total_ret = rec['total_return']
    win_rate = rec['win_rate']
    avg_win = rec['avg_win']
    avg_loss = rec['avg_loss']

    # 1. Market Context: Buy & Hold Comparison
    bh_ret = (data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0]
    comparison = "outperformed" if total_ret > bh_ret else "underperformed"

    # 2. Market Regime Analysis
    sma200 = data['Close'].rolling(window=200).mean()
    if len(data) >= 200:
        pct_above_sma200 = (data['Close'] > sma200).mean()
        if pct_above_sma200 > 0.7:
            regime = "strong long-term uptrend"
        elif pct_above_sma200 < 0.3:
            regime = "long-term downtrend"
        else:
            regime = "sideways or volatile phase"
    else:
        regime = "undetermined trend (short history)"

    # 3. Strategy Type Specific Reasoning
    trend_strats = ['SMA Trend', 'Momentum', '3-Day Trend', 'Volume Spike', 'EMA Cross', 'MACD Signal', 'Golden Cross', 'Inside Day']
    reversion_strats = ['RSI Reversion', 'Bollinger Oversold', 'Mean Reversion', 'Gap Down']
    time_strats = ['Overnight', 'Weekend Effect', 'Intraday']

    strat_type_reason = ""
    if strat_name in trend_strats:
        if "uptrend" in regime:
            strat_type_reason = f"The '{strat_name}' strategy capitalized on the {regime}, effectively riding the positive momentum of {ticker}."
        else:
            strat_type_reason = f"Despite a {regime}, '{strat_name}' managed to find profitable entries by filtering for specific momentum bursts."
    elif strat_name in reversion_strats:
        strat_type_reason = f"'{strat_name}' succeeded by identifying 'oversold' conditions and profiting from {ticker}'s tendency to revert to its mean during the {regime}."
    elif strat_name in time_strats:
        if strat_name == 'Overnight':
            strat_type_reason = f"The 'Overnight' strategy exploited the common 'overnight drift'—where significant price action for {ticker} often occurs between market close and the next day's open."
        elif strat_name == 'Weekend Effect':
            strat_type_reason = f"The 'Weekend Effect' captured the historical tendency for {ticker} to gap at the start of a new week after the Friday close."
        else:
            strat_type_reason = f"'{strat_name}' focused on specific intraday patterns, avoiding the risks and volatility associated with holding positions overnight."

    # 4. Statistical Profile Reasoning
    if win_rate > 0.6:
        stat_reason = f"The strategy's success is driven by high consistency, winning {win_rate:.1%} of the time."
    elif avg_win > abs(avg_loss) * 1.5:
        stat_reason = f"Success was driven by 'fat tails'—the average winning trade ({avg_win:.2%}) was significantly larger than the average loss ({abs(avg_loss):.2%}), more than compensating for a lower win rate."
    else:
        stat_reason = f"The strategy maintained a healthy balance between a {win_rate:.1%} win rate and a favorable risk/reward ratio."

    # Combine all pieces
    reasoning = (
        f"In the tested period, '{strat_name}' achieved a {total_ret:.2%} return, {comparison} a Buy & Hold return of {bh_ret:.2%}. "
        f"{strat_type_reason} "
        f"{stat_reason} "
        f"This strategy was particularly effective because {ticker} exhibited {regime} characteristics over these {len(data)} market days."
    )

    return reasoning

def get_sp500_tickers():
    """
    Scrapes S&P 500 tickers from Wikipedia.
    """
    try:
        import requests
        from io import StringIO
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        resp = requests.get(url, headers=headers)
        tables = pd.read_html(StringIO(resp.text))
        tickers = tables[0]['Symbol'].tolist()
        return [t.replace('.', '-') for t in tickers]
    except Exception as e:
        print(f"Error fetching S&P 500 tickers: {e}")
        # Return a small subset as fallback
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "NFLX", "AMD", "JPM"]

def get_top_performers(n=10, period='6mo'):
    """
    Calculates the top n performers in the S&P 500 for a given period.
    """
    tickers = get_sp500_tickers()

    # Download data for all tickers, only the Close column
    data = yf.download(tickers, period=period, progress=False, actions=False)

    if data.empty:
        return []

    # Extract Close prices
    if isinstance(data.columns, pd.MultiIndex):
        close_data = data['Close']
    elif 'Close' in data.columns:
        close_data = data['Close']
    else:
        # If only one ticker was returned or it's not a MultiIndex
        close_data = data

    performance = {}
    for ticker in close_data.columns:
        series = close_data[ticker].dropna()
        if len(series) > 1:
            perf = (series.iloc[-1] - series.iloc[0]) / series.iloc[0]
            performance[ticker] = perf

    sorted_perf = sorted(performance.items(), key=lambda x: x[1], reverse=True)
    top_n = sorted_perf[:n]

    return [{'ticker': t, 'performance': p} for t, p in top_n]

def get_recommendation(ticker, period='2y'):
    """
    Analyzes a ticker and returns all strategy results.
    """
    data = fetch_data(ticker, period=period)
    if data is None:
        return None
    
    strategies = [
        backtest_overnight(data),
        backtest_intraday(data),
        backtest_momentum(data),
        backtest_mean_reversion(data),
        backtest_gap_down(data),
        backtest_weekend_effect(data),
        backtest_three_day_trend(data),
        backtest_rsi_reversion(data),
        backtest_sma_trend(data),
        backtest_bollinger_oversold(data),
        backtest_volume_spike(data),
        backtest_ema_cross(data),
        backtest_macd_signal(data),
        backtest_inside_day(data),
        backtest_golden_cross(data)
    ]
    
    valid_strategies = [s for s in strategies if s is not None]
    if not valid_strategies:
        return None
    
    best = max(valid_strategies, key=lambda x: x['total_return'])
    
    # Generate detailed reasoning for the best strategy
    best['reasoning'] = generate_detailed_reasoning(best, data, ticker)

    return {
        'ticker': ticker,
        'period_days': len(data),
        'results': valid_strategies,
        'recommended': best
    }
