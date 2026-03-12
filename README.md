# Daily Stock Trading Strategy App

This application analyzes historical stock market data to find simple daily strategies that have historically increased money. It compares two primary daily strategies and recommends the best one for each stock.

## Strategies Analyzed

1.  **Overnight Strategy**: Buying a stock at the market close and selling it at the next day's market open.
2.  **Intraday Strategy**: Buying a stock at the market open and selling it at the same day's market close.
3.  **Momentum Strategy**: Buying at the open and selling at the close, but only if the previous day's return was positive.
4.  **Mean Reversion Strategy**: Buying at the open and selling at the close, but only if the previous day's return was negative.
5.  **Gap Down Strategy**: Buying at the open if the stock gapped down by more than 0.5% from the previous close, and selling at the close.
6.  **Weekend Effect**: Buying on Friday's close and selling on Monday's open to capture weekend gaps.
7.  **3-Day Trend**: Buying at the open and selling at the close only if the previous three days were positive (trend continuation).
8.  **RSI Reversion**: Buying at the open and selling at the close if the 14-day RSI is below 35 (oversold bounce).

## How it Works

The app fetches the last 2 years of historical data for the provided tickers using `yfinance`. It calculates the total return and win rate for both strategies and recommends the one with the highest historical total return.

## Installation

1.  Ensure you have Python 3 installed.
2.  Install the required dependencies:
    ```bash
    python3 -m pip install -r requirements.txt
    ```

*Troubleshooting: If you get a `ModuleNotFoundError`, ensure you are using the same Python version for installing and running (e.g., always use `python3`).*

## Usage

Run the app from the terminal and provide the stock tickers as arguments:

```bash
python3 app.py AAPL TSLA SPY MSFT
```

Alternatively, you can run it without arguments and follow the prompt:

```bash
python3 app.py
```

## Example Output

```text
Ticker   | Strategy                       | Total Return    | Win Rate  
------------------------------------------------------------------------
AAPL     | Intraday (Buy Open, Sell Close) |       57.61% |    53.59%
TSLA     | Overnight (Buy Close, Sell Open) |       94.81% |    56.49%
```

## Strategy Analysis & Future Outlook

### Consistency
Historical analysis over the last 10 years shows that while specific year-to-year performance varies, certain stocks exhibit persistent "behavioral signatures." For example:
- **Index ETFs (SPY/QQQ)**: Often show an "Overnight Edge" where the majority of gains happen between the previous day's close and the next day's open.
- **High Momentum Stocks (AAPL/TSLA)**: Frequently alternate between strong intraday trends and overnight gaps depending on market volatility and retail interest.

### Future Performance
No strategy is guaranteed to work in the future. However, these strategies are based on structural market features:
- **Overnight Strategy**: Relies on the fact that market-moving news often occurs after hours and that liquidity is lower, leading to price gaps.
- **Intraday Strategy**: Relies on the continuation of momentum during regular trading hours.

The "persistence" of these strategies (how often the best strategy one year remains the best the next year) typically ranges from 45% to 75% depending on the asset.

## Disclaimer

**Trading stocks involves significant risk of loss.** This application provides historical analysis for educational purposes only. Past performance is not indicative of future results. Always conduct your own research and consider consulting with a financial advisor before making investment decisions. 

**Note on Returns:** The calculations provided by this app are gross returns and do not account for trading commissions, platform fees, taxes, or slippage. In a real-world scenario, these factors would significantly reduce the net returns of any strategy.
