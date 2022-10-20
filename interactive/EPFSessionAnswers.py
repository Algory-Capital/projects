# import the modules
import pandas_datareader.data as web
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
import plotly.graph_objects as go

# choose a portfolio of 3 tickers
tickers = ['AAPL', 'BRK-B', 'XLE']

# choose a start date
start = '2013-01-01'

# get the monthly returns
data = web.get_data_yahoo(tickers, start)
data = data['Adj Close']

# change into percent change
df = data.pct_change()[1:]

# calculate metrics
avg_ret = df.mean()
cov = df.cov()

# annualize the metrics
avg_ret = (1 + avg_ret) ** 252 - 1
cov = cov * 252

# how many portfolios to sample
n_portfolios = 1000

# store mean-variance pairs
mv_pairs = []
w_total = []

# seed np.random
np.random.seed()

# iterate through every random portfolio
for i in range(n_portfolios):
    # assign weights randomly
    weights = np.random.rand(len(tickers))
    # normalize weights
    weights = weights / sum(weights)
    w_total.append(weights)

    # compute return and variance
    returns, var = 0, 0

    for i in range(len(weights)):
        # multiply the random weight by the annualized return
        returns += weights[i] * avg_ret[tickers[i]]

        # calculate the variance
        for j in range(len(tickers)):
            var += weights[i] * weights[j] * cov.loc[tickers[i], tickers[j]]

    # Append the portfolio's return and VOLATILITY to the list
    mv_pairs.append([returns, var ** 0.5])

# PLOT

# store mean-value pairs into numpy array to index it
mv_pairs = np.array(mv_pairs)

#create x and y variables for the scatterplot
vol = mv_pairs[:, 1]
port_returns = mv_pairs[:, 0]

# create a variable for risk-free rate: necessary for calculating Sharpe Ratio
rf = 0

# Sharpe Ratio list
sr = (port_returns-rf)/vol

cm = plt.cm.get_cmap('RdBu')
sc = plt.scatter(vol, port_returns, c=sr, vmin=min(sr), vmax=max(sr), cmap=cm)
plt.colorbar(sc)
plt.show()