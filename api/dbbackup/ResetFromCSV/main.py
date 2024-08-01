# run everything

import logging
import pandas as pd
from dividend import Dividend
from search import index
from equityetf import Equity, ETF
from dates import StockDates
import json
import re
from typing import List
import os

# linear combination of arrays

class Master:
    def __init__(self, root : str = "", path_aliases = "./Data/aliases.json",path_xl = "./Data/Activity_Summary_Jul_23_2024.xls"):
        self.cur_cash = 100000
        self.cur_idx = 0
        
        with open(os.path.join(root, path_aliases)) as f:
            self.als = json.load(f)
            self.opt_als = self.als['options']
            self.tkr_als = self.als['tickers']

        sd = StockDates()
        self.dates = sd.dates
        self.n_dates = sd.length

        self.aum = [0] * self.n_dates
        self.cashArr = [0] * self.n_dates

        self.EQUITY = Equity(self.n_dates)
        self.ETF = Equity(self.n_dates)
        self.DIV = Dividend(self.n_dates)

        # we expect that excel is sorted to avoid amortized O(N^2), although time complexity shouldn't matter here
        self.data = pd.read_excel(os.path.join(root, path_xl),index_col=0) # .xls
        self.pat = '(^\(\d+.?\d+\)|\d+.?\d+)'

        self.logger = logging.getLogger()

        self.process_excel()
    
    def inc_cash(self, cash: float , idx : int):
        for i in range(self.cur_idx,idx):
            # fill dates without orders
            self.cashArr[i] = self.cur_cash

        # update cash at requested date

        self.cur_cash += cash
        self.cashArr[idx] = self.cur_cash

        self.cur_idx = idx + 1

    def dec_cash(self, cash : float, idx: int):
        for i in range(self.cur_idx,idx):
            # fill dates without orders
            self.cashArr[i] = self.cur_cash

        # update cash at requested date
        assert (self.cur_cash >= cash)

        self.cur_cash -= cash
        self.cashArr[idx] = self.cur_cash

        self.cur_idx = idx + 1

    def process_excel(self):
        for _, row in self.data.iterrows():
            self.process_order(ord = row)
            
        self.linear_combination()

        for i in range(self.cur_idx, self.n_dates):
            # fill dates without orders
            self.cashArr[i] = self.cur_cash
        
        self.cashArr = Master.round_all(self.cashArr)

    def process_order(self, ord : pd.Series):
        order_name = ord['Security Name']
        transact_type = ord['Transaction Type']
        date : str = ord['Actual Settle Date']
        units :str = ord['Units']
        price : str = str(ord['Price']) # per unit price
        amt : str = ord['Amount']

        units = self.string_to_float(units)
        amt = self.string_to_float(amt, True)
        price = self.string_to_float(price)

        print(amt)

        if order_name in self.tkr_als:
            tkr = self.tkr_als[order_name]
        
        elif order_name in self.opt_als:
            tkr = self.opt_als[order_name]['asset']
        
        else:
            raise ValueError ("Error with order name: ", order_name)

        date_idx = index(date, self.dates)

        # (^\(\d+\)|\d+)

        if tkr == "CASH":
            if amt > 0:
                self.inc_cash(cash = amt, idx = date_idx)
            
            elif amt < 0:
                self.dec_cash(cash = amt, idx = date_idx)
            
            return

        if transact_type == "Dividend":
            self.DIV.process_dividend(date,tkr,amt,units)
            self.inc_cash(cash = amt, idx = date_idx)
            pass
        
        # we have never exercised ITM calls/options, so lumping them with Buy/Sell for now
        # otherwise, best solution is to check if "PUT" or "CALL" in string or if is in opt_aliases
        elif transact_type == "Buy":
            self.inc_cash(cash = amt, idx = date_idx)
            pass
            
        elif transact_type == "Sell":
            self.dec_cash(cash = amt, idx = date_idx)
            pass
        
        else:
            raise ValueError("Improper transact_type: ", transact_type)

    def fill(self,idx : int, arr : List[float]):
        pass

    def linear_combination(self,*arrs):
        # switch from arrays to numpy arrays
        pass
    
    def string_to_float(self, x : str, signed : bool = False, var_name = "UNLISTED"):
        if x == "":
            raise ValueError()
        
        # remove commas
        x = x.replace(',','')

        if not re.fullmatch(self.pat, x):
            # invalid format for amt
            raise ValueError(f"Invalid Format for variable {var_name} : {x}")

        tmp = x
        res : float = float(x.strip("()"))

        # spaghetti if condition
        if signed and tmp != x[0] == "(":
            return -res
        
        return res
    
    @staticmethod
    def round_all(a: List[float]):
        a = [round(x,2) for x in a]
        return a

if __name__ == "__main__":
    print(os.getcwd())

    master = Master("dbbackup/ResetFromCSV")
    print(master.cashArr)

    #print(master.cashArr)
    # 'c:\\Users\\Alexa\\OneDrive - Emory University\\Desktop\\Emory Club Projects\\Algory\\projects\\api\\dbbackup\\ResetFromCSV'
    pass