from collections import deque
from pandas_datareader import data
from datetime import datetime

# only get historical dividends

class DividendObject:
    # probably make this more for logging
    def __init__(self, name, dates):
        self.dates = dates
        self.name = name
        self.qtr_yield = 0

class Dividend:
    def __init__(self, n : int):
        self.divqueue = deque([]) # prob remove
        self.returns = [0] * n
    
    @staticmethod
    def next_quarter(date):
        # prob obsolete, since we can only go off history
        pass

    def push(date, ticker, shares):
        pass

    def process_dividend(self, date : str, tkr : str, amt : float, shares : float):
        pass