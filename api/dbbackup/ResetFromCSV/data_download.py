import yfinance as yf
from pandas_datareader import data as pdr
import pandas as pd
from datetime import datetime
from requests import Session
from requests_cache import CacheMixin, SQLiteCache
from requests_ratelimiter import LimiterMixin, MemoryQueueBucket
from pyrate_limiter import Duration, RequestRate, Limiter
import time
import os
import json
from typing import List

root = "./dbbackup/ResetFromCSV/Data"
start_date = '2022-08-01'

def get_spy_data(start_date="2022-08-01", end_date=datetime.strftime(datetime.now(),"%Y-%m-%d"), csv=True):
    class CachedLimiterSession(
        CacheMixin, LimiterMixin, Session
    ):  # inherits three classes
        pass

    session = CachedLimiterSession(
        limiter=Limiter(
            RequestRate(2, Duration.SECOND * 5)
        ),  # max 2 requests per 5 seconds. Yahoo Finance API seems to rate limit to 2000 requests per hour
        bucket_class=MemoryQueueBucket,
        backend=SQLiteCache(os.path.join(root, "yfinance.cache")),
    )

    tickers = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[
        0
    ]
    print(tickers.head())

    spy_data = yf.download(
        tickers.Symbol.to_list(),
        start=start_date,
        end=end_date,
        period="1d",
        auto_adjust=True,
        session=session,
    )["Close"]
    # Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo Intraday data cannot extend last 60 days
    spy_data.dropna(axis=1, how="any", inplace=True)
    print(start_date, end_date)
    print(spy_data.head())
    print(spy_data.tail())

    if csv:
        spy_data.to_csv(os.path.join(root, "spy.csv"), index=True)

    return spy_data

def preprocess_tickers(tkrs : List[str]):
    rep = {
        "BRK.B" : "BRK-B"
    }
    tkrs.remove('CASH')
    tkrs += ['^VIX','SPY', 'QQQ']
    tkrs = list(map(lambda x : rep.get(x,x), tkrs))

    return tkrs

def get_tickers_data(tickers : List[str], start_date="2022-08-01", end_date=datetime.strftime(datetime.now(),"%Y-%m-%d"), csv=True):
    
    # tickers = preprocess_tickers(tickers)

    spy_data = yf.download(
        tickers = tickers,
        start=start_date,
        end=end_date,
        period="1d",
        auto_adjust=True,
    )["Close"]
    # Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo Intraday data cannot extend last 60 days
    print(start_date, end_date)
    print(spy_data.head())
    print(spy_data.tail())

    if csv:
        spy_data.to_csv(os.path.join(root, "spy_index.csv"), index=True)

    return spy_data

def get_tickers(path : str = "aliases.json") -> List[str]:
    with open(os.path.join(root,path)) as f:
        tkrs = json.load(f)['tickers'].values()
    
    return preprocess_tickers(list(tkrs))

def load_history_data():
    tickers = get_tickers()

    data = get_tickers_data(tickers)
    return data

if __name__ == "__main__":
    start_time = time.time()

    tickers = get_tickers()
    print(tickers)
    input("Input to continue")

    get_tickers_data(tickers)

    print(f"Took {time.time()-start_time} seconds.")
