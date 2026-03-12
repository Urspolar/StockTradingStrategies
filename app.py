import sys
import argparse
import subprocess
from strategy import get_recommendation

def run_cli(tickers):
    if not tickers:
        user_input = input("Enter tickers separated by spaces (e.g., AAPL TSLA SPY): ")
        tickers = user_input.split()
    
    if not tickers:
        print("No tickers provided. Exiting.")
        return

    print(f"\nAnalyzing {len(tickers)} tickers across multiple strategies...\n")
    
    for ticker in tickers:
        ticker = ticker.upper()
        res = get_recommendation(ticker)
        if not res:
            print(f"Could not analyze {ticker}. Skipping.\n")
            continue

        print(f"\n--- Results for {ticker} ({res['period_days']} market days tested) ---")
        header = f"{'Strategy':<15} | {'Description':<35} | {'Return':<10} | {'Win%':<6} | {'Trades':<6}"
        print(header)
        print("-" * len(header))

        for s in res['results']:
            print(f"{s['strategy']:<15} | {s['description']:<35} | {s['total_return']:>10.2%} | {s['win_rate']:>6.1%} | {s['trade_count']:>6}")

        rec = res['recommended']
        print(f"\n>> BEST STRATEGY: {rec['strategy']}")
        
        # Reasoning
        reason = f"Based on the last {res['period_days']} market days, '{rec['strategy']}' had the highest historical return of {rec['total_return']:.2%}. "
        if rec['win_rate'] > 0.55:
            reason += f"It also maintains a strong win rate of {rec['win_rate']:.1%}. "
        else:
            reason += f"While the win rate is {rec['win_rate']:.1%}, the size of the winning trades significantly outweighed the losing ones. "
        
        print(f">> WHY: {reason}")
        
        print(f"\n>> DAILY ACTION: ", end="")
        if rec['strategy'] == 'Overnight':
            print(f"BUY at Market Close, SELL at next day's Open.")
        elif rec['strategy'] == 'Momentum':
            print(f"BUY at Market Open if yesterday was positive, SELL at Close.")
        elif rec['strategy'] == 'Mean Reversion':
            print(f"BUY at Market Open if yesterday was negative, SELL at Close.")
        elif rec['strategy'] == 'Gap Down':
            print(f"BUY at Market Open if gapped down > 0.5%, SELL at Close.")
        elif rec['strategy'] == 'Weekend Effect':
            print(f"BUY Friday Close, SELL Monday Open.")
        elif rec['strategy'] == '3-Day Trend':
            print(f"BUY at Market Open if last 3 days were positive, SELL at Close.")
        elif rec['strategy'] == 'RSI Reversion':
            print(f"BUY at Market Open if RSI < 35, SELL at Close.")
        else:
            print(f"BUY at Market Open, SELL at same day's Close.")
        print("-" * 80)

    print("\nDisclaimer: Trading stocks involves significant risk. This app provides historical analysis and is not financial advice.")
    print("Note: Returns do not account for transaction costs, commissions, or slippage.")

def main():
    parser = argparse.ArgumentParser(description="Stock Trading Strategy Analyzer")
    parser.add_argument("tickers", nargs="*", help="Stock tickers to analyze")
    parser.add_argument("--ui", action="store_true", help="Run the Streamlit UI")

    args = parser.parse_args()

    if args.ui or not args.tickers:
        print("Launching UI...")
        subprocess.run([sys.executable, "-m", "streamlit", "run", "ui.py"])
    else:
        print("="*80)
        print("   STOCK TRADING STRATEGY ANALYZER (CLI)")
        print("="*80)
        run_cli(args.tickers)

if __name__ == "__main__":
    main()
