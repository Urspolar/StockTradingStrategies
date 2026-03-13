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

def format_result(name, desc, trades, action):
    if trades.empty:
        return None
    total_return = (1 + trades).prod() - 1
    win_rate = (trades > 0).mean()
    return {
        'strategy': name,
        'description': desc,
        'total_return': total_return,
        'win_rate': win_rate,
        'trade_count': len(trades),
        'action': action
    }

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
        backtest_volume_spike(data)
    ]
    
    valid_strategies = [s for s in strategies if s is not None]
    if not valid_strategies:
        return None
    
    best = max(valid_strategies, key=lambda x: x['total_return'])
    
    return {
        'ticker': ticker,
        'period_days': len(data),
        'results': valid_strategies,
        'recommended': best
    }
