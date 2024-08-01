import yfinance as yf
from datetime import datetime

# utilize spaghetti to generate stock market dates
class StockDates:
    def __init__(self, start_date = "2022-08-01", fmt = "%Y/%m/%d"):
        dates = yf.download("SPY", start_date).index

        self.dates = list(dates.map(lambda x : datetime.strftime(x,fmt)).values)
        self.length = len(self.dates)

        print(self.dates)
        pass
