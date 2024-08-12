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
import matplotlib.pyplot as plt

# linear combination of arrays

class Master:
    def __init__(self, root : str = "", path_aliases = "./Data/aliases.json",path_xl = "./Data/Activity_Summary_Jul_23_2024.xls"):
        self.cur_cash = 100000
        
        with open(os.path.join(root, path_aliases)) as f:
            self.als = json.load(f)
            self.opt_als = self.als['options']
            self.tkr_als = self.als['tickers']

        sd = StockDates()
        self.dates = sd.dates
        self.n_dates = sd.length

        self.aum = [0] * self.n_dates
        self.cashArr = [0] * self.n_dates
        self.total = [0] * self.n_dates

        self.EQUITY = Equity(self.n_dates)
        # two below objects will be used for logging purposes
        self.ETF = ETF(self.n_dates)
        self.DIV = Dividend(self.n_dates)

        # we expect that excel is sorted to avoid amortized O(N^2), although time complexity shouldn't matter here
        self.data = pd.read_excel(os.path.join(root, path_xl),index_col=0) # .sort_values('Actual Settle Date') # .xls
        self.pat = '(^\(\d+.?\d+\)|\d+.?\d+)'

        self.logger = logging.getLogger(__name__)
        fhandler = logging.FileHandler(filename = os.path.join(root, "Data/logs.log"), mode= 'a')
        self.logger.addHandler(fhandler)
        self.logger.setLevel(logging.DEBUG)

        self.div_amt = 0
        self.buy_amt = 0
        self.sell_amt = 0

        self.cur_idx = 0

        self.process_excel()
    
    def inc_cash(self, cash: float , idx : int):
        for i in range(self.cur_idx,idx):
            # fill dates without orders
            self.cashArr[i] = self.cur_cash
            self.aum[i] = self.EQUITY.get_aum_value(idx=idx) #improper implementation
        
        # for i in range(idx, self.n_dates):
        #     self.cashArr[i] += cash
        #     self.aum[i] += self.EQUITY.get_aum_value(idx=idx)

        # update cash at requested date

        # process order here

        self.cur_cash += abs(cash)
        self.cashArr[idx] = self.cur_cash

        self.aum[idx] = self.EQUITY.get_aum_value(idx=idx)

        self.cur_idx = idx + 1

    def dec_cash(self, cash : float, idx: int):
        for i in range(self.cur_idx,idx):
            # fill dates without orders
            self.cashArr[i] = self.cur_cash
            self.aum[i] = self.EQUITY.get_aum_value(idx=idx)

        # update cash at requested date
        assert (self.cur_cash >= cash, f"Failed assertion on cash balance: {self.cashArr}")

        self.cur_cash -= abs(cash)
        self.cashArr[idx] = self.cur_cash

        self.aum[idx] = self.EQUITY.get_aum_value(idx=idx)

        self.cur_idx = idx + 1
    
    def buy_stock(self, tkr : str, units: float, cash: float, idx :int, date : str ):
        self.EQUITY.buy_stock_map(tkr,units,idx)


        for i in range(self.cur_idx,idx):
            # fill dates without orders
            self.cashArr[i] = self.cur_cash
            self.aum[i] = self.EQUITY.get_aum_value(idx=idx) #improper implementation

        # update cash at requested date

        self.EQUITY.buy_stock(tkr,units,date)

        # process order here

        #self.cur_cash += cash
        self.cashArr[idx] = self.cur_cash

        self.aum[idx] = self.EQUITY.get_aum_value(idx=idx)

        self.cur_idx = idx + 1
    
    def sell_stock(self, tkr : str, units: float, cash: float, idx :int, date: str):
        self.EQUITY.sell_stock_map(tkr,units,idx)
    
        for i in range(self.cur_idx,idx):
            # fill dates without orders
            self.cashArr[i] = self.cur_cash
            self.aum[i] = self.EQUITY.get_aum_value(idx=idx)

        # update cash at requested date
        assert (self.cur_cash >= cash, f"Failed assertion on cash balance: {self.cashArr}")

        self.EQUITY.sell_stock(tkr,units, date)

        #self.cur_cash -= cash
        self.cashArr[idx] = self.cur_cash

        self.aum[idx] = self.EQUITY.get_aum_value(idx=idx)

        self.cur_idx = idx + 1
        pass

    def process_excel(self):
        for _, row in self.data.iterrows():
            self.process_order(ord = row)

        for i in range(self.cur_idx, self.n_dates):
            # fill dates without orders
            self.cashArr[i] = self.cur_cash
            if i == self.n_dates - 1:
                self.aum[i] = self.aum[i-1]
                continue
            self.aum[i] = self.EQUITY.get_aum_value(idx=i)


        self.aum = self.EQUITY.get_aum_value_all(self.dates)
        print(self.aum)
        for i, (cash, aum) in enumerate(zip(self.cashArr, self.aum)):
            self.total[i] = cash + aum
        
        self.total = Master.round_all(self.total)

    def process_order(self, ord : pd.Series):
        '''
        Parse everything
        '''

        order_name = ord['Security Name']
        transact_type = ord['Transaction Type']
        date : str = ord['Actual Settle Date']
        units :str = ord['Units']
        price : str = str(ord['Price']) # per unit price
        amt : str = ord['Amount']
        commission : str = ord['Commision Expenses']
        settlement_policy = ord['Settlement Policy']

        units = self.string_to_float(units)
        amt = self.string_to_float(amt, True)
        price = self.string_to_float(price)
        commission = self.string_to_float(commission)

        if order_name in self.tkr_als:
            tkr = self.tkr_als[order_name]
        
        elif order_name in self.opt_als:
            tkr = self.opt_als[order_name]['asset']
            print("Found ticker: ", tkr)
            return # TMP RETURN
        
        else:
            raise ValueError ("Error with order name: ", order_name)

        # don't double count
        # if tkr == "CASH" and settlement_policy == "Un-projected Actual":
        #     return

        try:
            date_idx = index(date, self.dates)
        except Exception as e:
            raise ValueError(f"Error with date: {date} - {str(e)}")

        # (^\(\d+\)|\d+)

        if commission > 0:
            self.dec_cash(cash = commission, idx = date_idx)

        if tkr == "CASH":
            if transact_type == "Buy":
                self.inc_cash(cash = amt, idx = date_idx)
            
            elif transact_type == "Sell":
                self.dec_cash(cash = amt, idx = date_idx)
            
            return

        if transact_type == "Dividend":
            self.DIV.process_dividend(date,tkr,amt,units)
            # self.inc_cash(cash = amt, idx = date_idx)

            self.div_amt += amt
            pass
        
        # we have never exercised ITM calls/options, so lumping them with Buy/Sell for now
        # otherwise, best solution is to check if "PUT" or "CALL" in string or if is in opt_aliases
        elif transact_type == "Buy":
            #self.inc_cash(cash = amt, idx = date_idx)
            #self.EQUITY.buy_stock(tkr,units,date)
            self.buy_stock(tkr,units,cash = amt, idx=date_idx, date=date)

            self.buy_amt += amt
            pass
            
        elif transact_type == "Sell":
            #self.dec_cash(cash = amt, idx = date_idx)
            #self.EQUITY.sell_stock(tkr,units,date)
            self.sell_stock(tkr,units,cash = amt, idx=date_idx, date=date)

            self.sell_amt += amt
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
    #print(master.total)

    print(master.aum)
    print(master.EQUITY.holdings)
    zipped_res = [(d,t) for d,t in zip(master.dates, master.total)]

    df_data = pd.DataFrame(data= master.total, columns=["TOTAL"], index = master.dates)
    df_data["CASH"] = master.cashArr
    df_data["AUM"] = master.aum

    df_data.to_csv("dbbackup/ResetFromCSV/Data/Debug/debug.csv")

    plot = df_data.plot(title="DEBUG")
    plt.tight_layout()
    plt.savefig("dbbackup/ResetFromCSV/Data/Debug/debug.png")

    # norm
    df_data = pd.DataFrame(data= master.total, columns=["TOTAL"], index = master.dates)

    plot = df_data.plot(title="DEBUG_2")
    plt.tight_layout()
    plt.savefig("dbbackup/ResetFromCSV/Data/Debug/debug_2.png")

    input("DKF")

    master.logger.info(f"Result of reset:\n\n{zipped_res}\n\n")

    #print(master.cashArr)
    # 'c:\\Users\\Alexa\\OneDrive - Emory University\\Desktop\\Emory Club Projects\\Algory\\projects\\api\\dbbackup\\ResetFromCSV'

    master.logger.info(f"Div: {master.div_amt:.2f}. Sell: {master.sell_amt:.2f}. Buy: {master.buy_amt:.2f}. Current Cash: {master.cur_cash}. Equity Total: {master.EQUITY.get_aum_value(-1)}.")

    master.logger.info(master.cashArr)
    master.logger.info("FINISHED RUN")
    pass