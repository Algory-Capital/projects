import yfinance as yf
import datetime
import pandas as pd

# Define the start and end dates
start_date = "2002-01-01"
end_date = "2022-01-01"

# Import packages

# Read and print the stock tickers that make up S&P500
tickers = pd.read_html(
    'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]

# Get the data for this tickers from yahoo finance
data = yf.download(tickers.Symbol.to_list(),'2002-1-1','2022-1-1', auto_adjust=True)['Close']
data.to_csv("market_tester")