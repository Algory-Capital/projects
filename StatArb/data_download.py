import yfinance as yf
from pandas_datareader import data as pdr
import pandas as pd
from requests import Session
from requests_cache import CacheMixin,SQLiteCache
from requests_ratelimiter import LimiterMixin, MemoryQueueBucket
from pyrate_limiter import Duration, RequestRate, Limiter
import time
import os

root = "StatArb"

def get_spy_data():
    class CachedLimiterSession(CacheMixin,LimiterMixin,Session): #inherits three classes
        pass

    session = CachedLimiterSession(
        limiter= Limiter(RequestRate(2,Duration.SECOND*5)), #max 2 requests per 5 seconds. Yahoo Finance API seems to rate limit to 2000 requests per hour
        bucket_class = MemoryQueueBucket,
        backend= SQLiteCache(os.path.join(root,'yfinance.cache'))
    )

    tickers = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
    print(tickers.head())

    spy_data = yf.download(tickers.Symbol.to_list(),start='2018-6-12',end='2021-7-12',period="1d",auto_adjust=True,session=session)['Close'] 
    # Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo Intraday data cannot extend last 60 days
    print(spy_data.head())

    spy_data.to_csv(os.path.join(root,'spy.csv'),index=True)


if __name__ == "__main__":
    start_time = time.time()

    get_spy_data()

    print(f'Took {time.time()-start_time} seconds.')