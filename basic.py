import yfinance as yf
import pandas as pd
import numpy as np

# Parameters
TICKER = "^GSPC"  # S&P 500 index
INITIAL_CASH = 100  # Starting cash for both strategies
DROP_THRESHOLD = 0.10  # 10% drop for Buy-the-Dip
START_YEAR = 1924  # Start year for rolling simulations
WINDOW_YEARS = 30  # Length of each simulation window

# Fetch historical S&P 500 data
data = yf.download(TICKER, start=f"{START_YEAR}-01-01", end="2024-01-01", auto_adjust=False)

prices_data = None

# Use Adjusted Close if available, otherwise fall back to Close
if "Adj Close" in data.columns:
    prices_data = data["Adj Close"]
elif "Close" in data.columns:
    prices_data = data["Close"]
else:
    raise ValueError("Neither 'Adj Close' nor 'Close' found in data. Check ticker or data source.")

# Ensure prices_data is a Series
if isinstance(prices_data, pd.DataFrame):
    prices_data = prices_data.squeeze()  # Convert single-column DataFrame to Series

# Function to simulate Dollar-Cost Averaging (DCA)
def simulate_dca(prices, initial_cash):
    cash = initial_cash
    monthly_investment = initial_cash / 12  # Spread cash evenly over first 3 years
    shares = 0
    resampled_prices = prices.resample('ME').last()  # Resample to monthly frequency
    for date in resampled_prices.index:
        if date in prices.index and cash > 0:  # Ensure valid index
            shares += min(cash, monthly_investment) / prices.loc[date]  # FIX: Use .loc instead of .at
            cash = cash - min(cash, monthly_investment)
    return shares * prices.iloc[-1]

# Function to simulate Buy-the-Dip (BTD)
def simulate_btd(prices, initial_cash, drop_threshold):
    cash = initial_cash
    shares = 0
    last_high = prices.iloc[0]

    for price_value in prices.tolist():
        if price_value > last_high:
            last_high = price_value
        elif price_value <= last_high * (1 - drop_threshold) and cash > 0:  # 10% drop
            shares += cash / price_value
            cash = 0  # Fully invested

    return shares * prices.iloc[-1]

# Run rolling 30-year simulations
results = []
for start in range(START_YEAR, 2024 - WINDOW_YEARS):
    window_prices = prices_data[f"{start}-01-01":f"{start + WINDOW_YEARS}-01-01"]

    dca_final = simulate_dca(window_prices, INITIAL_CASH)
    btd_final = simulate_btd(window_prices, INITIAL_CASH, DROP_THRESHOLD)
    
    results.append((start, start + WINDOW_YEARS, dca_final, btd_final))

# Convert to DataFrame
df = pd.DataFrame(results, columns=["Start Year", "End Year", "DCA Value", "BTD Value"])

# Save results to CSV
csv_filename = "investment_strategy_results.csv"
df.to_csv(csv_filename, index=False)

# Print summary statistics
print(df.describe())

# Show head-to-head results
print(f"\nRolling 30-year strategy comparisons saved to {csv_filename}")
