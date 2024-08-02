#from search import index
import yfinance as yf
import pandas as pd
from data_download import load_history_data


class Equity():
    def __init__(self, n: int):
        self.gains = [0] * n
        self.holdings = {}
        self.data : pd.DataFrame = load_history_data()
    
    def buy_stock(self, tkr: str, units : float, date: str):
        price = self.data.loc[date,tkr]
        self.holdings[tkr] = self.holdings.get(tkr,0) + units

        return price * units # cash if needed

    def sell_stock(self, tkr: str, units: float, date: str):
        price = self.data.loc[date,tkr]

        # visually displeasing code
        assert(self.holdings.get(tkr,0) >= units)

        self.holdings[tkr] = self.holdings.get(tkr,0) - units

        if tkr in self.holdings and self.holdings[tkr] == 0:
            del self.holdings[tkr]

        return price * units # cash if needed

    def get_aum_value(self, date : str):
        aum_val = 0

        for tkr, shares in self.holdings.items():
            price = self.data.loc[date,tkr]
            aum_val += price * shares
        
        return aum_val
    
    def get_aum_value(self, idx : int):
        aum_val = 0

        for tkr, shares in self.holdings.items():
            price = self.data.iloc[idx][tkr]
            aum_val += price * shares
        
        return aum_val

class ETF:
    def __init__(self, n: int):
        self.gains = [0] * n
        self.holdings = {}
    
    def buy_stock(self, tkr: str, units : float, date: str):
        #i = index(date)
        pass

    def sell_stock(self, tkr: str, units: float, date: str):
        #i = index(date)
        pass