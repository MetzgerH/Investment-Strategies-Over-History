import yfinance as yf
import pandas as pd
import numpy as np
from datetime import timedelta
from math import floor

# Parameters
TICKER = "^GSPC"  # S&P 500 index
INITIAL_CASH = 100  # Starting cash for both strategies
DROP_THRESHOLD = 0.10  # 10% drop for Buy-the-Dip
START_YEAR = 1928  # Start year for rolling simulations
WINDOW_YEARS = 30  # Length of each simulation window
NUM_SIMULATIONS = 10000 # Number of samples

# Fetch historical S&P 500 data
data = yf.download(TICKER, start=f"{START_YEAR}-01-01", auto_adjust=False)

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
def simulate_dca(prices, initial_cash, time_frame=12):
    cash = initial_cash
    regular_investment = (1.0*initial_cash) / (time_frame*4)  # Spread cash evenly over given time frame
    shares = 0
    day_count = 0
    for date in prices.index:
        if cash > 0 and day_count% 5 == 0:  # Ensure valid index
            shares += min(cash, regular_investment) / prices.loc[date]
            cash = cash - min(cash, regular_investment)
        day_count += 1
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

# Generate random 30-year spans
results = []
for _ in range(NUM_SIMULATIONS):
    # Generate a random start date within the valid range
    start_date = pd.to_datetime(np.random.choice(prices_data.index[:floor(-252 * WINDOW_YEARS)]))
    end_date = start_date + timedelta(days=365.25 * WINDOW_YEARS)
    
    # Ensure the end date is within the data range
    if end_date > prices_data.index[-1]:
        continue
    
    # Extract the 30-year window
    window_prices = prices_data[start_date:end_date]
    
    # Run simulations
    instant_dump = simulate_dca(window_prices, INITIAL_CASH,0.25)
    dca_three_months = simulate_dca(window_prices, INITIAL_CASH,3)
    dca_half_year = simulate_dca(window_prices, INITIAL_CASH,6)
    dca_year = simulate_dca(window_prices, INITIAL_CASH,12)
    dca_two_years = simulate_dca(window_prices, INITIAL_CASH,24)
    btd_final = simulate_btd(window_prices, INITIAL_CASH, DROP_THRESHOLD)
    
    results.append((start_date, end_date, instant_dump, dca_three_months, dca_half_year, dca_year, dca_two_years, btd_final))

# Convert to DataFrame
df = pd.DataFrame(results, columns=["Start Year", "End Year", "Instant Dump", "DCA 3 Months", "DCA Half Year","DCA Year", "DCA Two Years", "BTD Value"])

# Save results to CSV
csv_filename = "investment_strategy_results.csv"
df.to_csv(csv_filename, index=False)
print(f"\nRolling 30-year strategy comparisons saved to {csv_filename}")


# Print summary statistics
print(df.describe())