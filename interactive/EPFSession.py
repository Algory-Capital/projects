# import the modules
import pandas_datareader.data as web
import datetime
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yfin
yfin.pdr_override()

# choose a portfolio of 3 tickers
tickers = ['AAPL', 'BRK-B', 'XLE']

# choose a start date
start_date = datetime.datetime() #yyyy, m, d
end = datetime.datetime.today()

# get the monthly returns


# change into percent change


# calculate metrics


# annualize the metrics


# how many portfolios to sample
n_portfolios

# store mean-variance pairs
mv_pairs = []
w_total = []

# seed np.random


# iterate through every random portfolio
for i in range(n_portfolios):
    # assign weights randomly

    # normalize weights


    # compute return and variance
    returns, var = 0, 0

    for i in range(len(weights)):
        # multiply the random weight by the annualized return


        # calculate the variance



    # Append the portfolio's return and VOLATILITY to the list

print(mv_pairs)

# PLOT

# store mean-value pairs into numpy array to index it


# create a variable for risk-free rate: necessary for calculating Sharpe Ratio


# create returns and volatility list


# Sharpe Ratio list


# Max Sharpe Ratio


# initialize the pyplot
cm = plt.cm.get_cmap('RdBu')
sc = plt.scatter(x, y, c=, vmin=, vmax=, cmap=)
circle
# cbar = plt.colorbar(sc)
# ax = plt.gca()
# ax.add_patch(circle)
# cbar.set_label('Sharpe Ratio')
# plt.xlabel('Volatility (STD)')
# plt.ylabel('Excess Returns (Mean)')
# plt.title('Efficient Portfolio Frontier')
# plt.show()