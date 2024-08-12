#from search import index
import yfinance as yf
import pandas as pd
from data_download import load_history_data
from collections import defaultdict

class Equity():
    def __init__(self, n: int):
        self.n = n
        self.gains = [0] * n
        self.holdings_arr = [defaultdict(int) for _ in range(n)]
        self.holdings = {}
        self.data : pd.DataFrame = load_history_data()
    
    def buy_stock(self, tkr: str, units : float, date: str):
        price = self.data.loc[date,tkr]
        self.holdings[tkr] = self.holdings.get(tkr,0) + units

        return price * units # cash if needed

    def sell_stock(self, tkr: str, units: float, date: str):
        price = self.data.loc[date,tkr]

        # visually displeasing code
        assert(self.holdings.get(tkr,0) >= units, f"Print failed {tkr} with {units} shares on date: {date}.")

        self.holdings[tkr] = self.holdings.get(tkr,0) - units

        if tkr in self.holdings and self.holdings[tkr] == 0:
            del self.holdings[tkr]

        return price * units # cash if needed

    def buy_stock_map(self, tkr: str, units: float, index: int):
        for i in range(index, self.n):
            self.holdings_arr[i][tkr] += units
    
    def sell_stock_map(self, tkr: str, units: float, index: int):
        for i in range(index, self.n):
            self.holdings_arr[i][tkr] -= units

            share_amt = self.holdings_arr[i][tkr]

            if share_amt == 0:
                del self.holdings_arr[i][tkr]
            elif share_amt < 0:
                raise ValueError(f"YOU FUCKED UP: {tkr} with {units} shares, index: {index}")

    def get_aum_value(self, date : str):
        aum_val = 0

        for tkr, shares in self.holdings.items():
            price = self.data.loc[date,tkr]
            aum_val += price * shares
        
        return aum_val

    def get_aum_value_MAP(self, date :str, holdings : defaultdict):
        aum_val = 0

        for tkr, shares in holdings.items():
            price = self.data.loc[date,tkr]
            aum_val += price * shares
        
        return aum_val
    
    def get_aum_value(self, idx : int):
        aum_val = 0

        for tkr, shares in self.holdings.items():
            price = self.data.iloc[idx][tkr]
            aum_val += price * shares
        
        return aum_val

    def get_aum_value_all(self, dates):
        resAUM = []

        assert(len(dates) == self.n)

        for holdings, date in zip(self.holdings_arr,dates):
            resAUM.append(self.get_aum_value_MAP(date, holdings))
        
        print(resAUM, self.holdings_arr)
        return resAUM

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