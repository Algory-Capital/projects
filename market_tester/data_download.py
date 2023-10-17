import yfinance as yf
import datetime
import pandas as pd

def download_stock_data(start_date, end_date):
    # Read and print the stock tickers that make up S&P500
    #needs to get backtesting wiki data
    tickers = pd.read_html(
        'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]

    # Get the data for these tickers from Yahoo Finance
    data = yf.download(tickers.Symbol.to_list(), start_date, end_date, auto_adjust=True)['Close']
    filename = f"s&p500 {start_date} to {end_date}.csv"
    data.to_csv(filename)
    return filename