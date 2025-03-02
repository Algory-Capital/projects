# -*- coding: utf-8 -*-
"""Copy of VaR & Portfolio Optimization.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1VqimVt5zOF-fDpKNZIIfJ5Nz7Ow8E3LE
"""

# Commented out IPython magic to ensure Python compatibility.
## Data manipulation
import numpy as np
import pandas as pd
from pandas_datareader import data as pdr
import xlrd as xlrd
import csv
import pandas_datareader as web
from matplotlib.ticker import FuncFormatter
from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt import risk_models
from pypfopt import expected_returns
from matplotlib.ticker import FuncFormatter
from scipy.stats import norm

## Plotting
import matplotlib.pyplot as plt
import seaborn
import matplotlib.mlab as mlab

## Statistical calculation
from scipy.stats import norm

## Data fetching
#import fix_yahoo_finance as yf
#import yfinance as yf
import datetime as dt

## Tabular data output
from tabulate import tabulate

# %matplotlib inline

# Data import AAPL  BKS RITM
data = pd.read_excel(".xlsx")
data = data.select_dtypes(include=['number']) #remove the data column in the original dataset

"""$S_{t+1} = S_t + S_t(\mu\Delta$$t$ + $\sigma$$\epsilon\sqrt{\Delta t})$"""

data_return = data.pct_change()
data_return

mean = data_return.mean() # return of asset
vol = data_return.std() #volatility

time3 = 1/(252*3)
time5 = 1/(252*5)
time7 = 1/(252*7)
time2 = 1/(252*2)
time1 = 1/(252)
time6mo = 1/(126)

def MeanTime(t):
    if t==time3:
        mean_time = mean * time3
        return mean_time

    elif t==time5:
        mean_time = mean * time5
        return mean_time

    elif t==time7:
        mean_time = mean * time7
        return mean_time

    elif t==time2:
        mean_time = mean * time2
        return mean_time

    elif t==time1:
        mean_time = mean * time1
        return mean_time

    else:
        mean_time = mean * time6mo
        return mean_time

#mean_time = mean * time # /mu /delta t term in the equation
MeanTime(time7)

#vol_time = vol * np.sqrt(time)  # /sigma /sqrt /delta t term in the equation above

def VolTime(t):
    if t==time3:
        vol_time = vol * np.sqrt(time3)
        return vol_time
    elif t==time5:
        vol_time = vol * np.sqrt(time5)
        return vol_time
    elif t==time7:
        vol_time = vol * np.sqrt(time7)
        return vol_time
    elif t==time2:
        vol_time = vol * np.sqrt(time2)
        return vol_time
    elif t==time1:
        vol_time = vol * np.sqrt(time1)
        return vol_time
    else:
        vol_time = vol * np.sqrt(time6mo)
        return vol_time

VolTime(time7)

iteration = 10
t_interval = 10000 #10000 time intervals, iterate 10 times for each time interval

ran = norm.ppf(np.random.rand(t_interval, iteration)) # /epsilon term in the above equation
ran

ncol = data.shape[1]

for i in range(ncol):#iterate for each equity
    ran_factor = MeanTime(time6mo)[i] + VolTime(time6mo)[i] * ran # /mu*/delta t + /sigma * /epsilon * /sqrt /delta t
    S0 = data.iloc[:,[i]].iloc[-1]
    price_list = np.zeros_like(ran_factor)
    price_list[0] = S0
    for j in range(1, t_interval):
        price_list[j] = price_list[j-1] + price_list[j-1] * ran_factor[j] # the formula
    new_price = pd.DataFrame(price_list)
    #VaR = S0 - np.percentile(new_price, 95)
    VaR95 = np.percentile(new_price, 5)-S0
    VaR99 = np.percentile(new_price, 1)-S0
    VaR95_percent = (np.percentile(new_price, 5)-S0)/S0 #95%
    VaR99_percent = (np.percentile(new_price, 1)-S0)/S0
    print(VaR95) # the printed dollar value is at risk
    print(VaR99)
    print(VaR95_percent)
    print(VaR99_percent)

for i in range(ncol):#iterate for each equity
    ran_factor = MeanTime(time1)[i] + VolTime(time1)[i] * ran # /mu*/delta t + /sigma * /epsilon * /sqrt /delta t
    S0 = data.iloc[:,[i]].iloc[-1]
    price_list = np.zeros_like(ran_factor)
    price_list[0] = S0
    for j in range(1, t_interval):
        price_list[j] = price_list[j-1] + price_list[j-1] * ran_factor[j] # the formula
    new_price = pd.DataFrame(price_list)
    #VaR = S0 - np.percentile(new_price, 95)
    VaR95 = np.percentile(new_price, 5)-S0
    VaR99 = np.percentile(new_price, 1)-S0
    VaR95_percent = (np.percentile(new_price, 5)-S0)/S0 #95%
    VaR99_percent = (np.percentile(new_price, 1)-S0)/S0
    print(VaR95) # the printed dollar value is at risk
    print(VaR99)
    print(VaR95_percent)
    print(VaR99_percent)

#.
#line chart : x_axis: 6mo, 1yr, 2yr, 3yr, 5yr, 7yr; y_axis: VaR99(6mo, 99), VaR99(1yr, 99), VaR99(2yr, 99), etc.


for i in range(ncol):#iterate for each equity
    ran_factor = MeanTime(time7)[i] + VolTime(time7)[i] * ran # /mu*/delta t + /sigma * /epsilon * /sqrt /delta t
    S0 = data.iloc[:,[i]].iloc[-1]
    price_list = np.zeros_like(ran_factor)
    price_list[0] = S0
    for j in range(1, t_interval):
        price_list[j] = price_list[j-1] + price_list[j-1] * ran_factor[j] # the formula
    new_price = pd.DataFrame(price_list)
    #VaR = S0 - np.percentile(new_price, 95)
    VaR95 = np.percentile(new_price, 5)-S0
    VaR99 = np.percentile(new_price, 1)-S0
    VaR95_percent = (np.percentile(new_price, 5)-S0)/S0 #95%
    VaR99_percent = (np.percentile(new_price, 1)-S0)/S0
    print(VaR95) # the printed dollar value is at risk
    print(VaR99)
    print(VaR95_percent)
    print(VaR99_percent)

new_price.pct_change().hist(figsize=(12,12), bins = 100) #histogram of percent change of price

new_price.plot(figsize=(10,10))

"""<font size="5">Mean Reversion</font>"""

# Importing Packages

# For data analytics
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
import seaborn as sns # for heatmap

# For acquiring stock data
import yfinance as yf

# For calculating cointegration
import statsmodels.tsa.stattools as ts
from statsmodels.tsa.stattools import adfuller

