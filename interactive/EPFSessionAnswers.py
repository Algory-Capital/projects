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
start_date = datetime.datetime(2022, 1, 1)
end = datetime.datetime.today()

# get the monthly returns
data = web.get_data_yahoo(tickers, start_date, end)
data = data['Adj Close']

# change into percent change
df = data.pct_change()[1:]
print(df)

# calculate metrics
avg_ret = df.mean()
cov = df.cov()

# annualize the metrics
avg_ret = (1 + avg_ret) ** 252 -1
cov = cov * 252

# how many portfolios to sample
n_portfolios = 1000

# store mean-variance pairs
mv_pairs = []
w_total = []

# seed np.random
np.random.seed(123)

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
print(mv_pairs)

# PLOT

# store mean-value pairs into numpy array to index it
mv_pairs = np.array(mv_pairs)
# create a variable for risk-free rate: necessary for calculating Sharpe Ratio
rf = 0.02

# create returns and volatility list
vol = mv_pairs[:, 1]
port_returns = mv_pairs[:, 0]

# Sharpe Ratio list
sr = (port_returns-rf)/vol

# Max Sharpe Ratio
max_sr = mv_pairs[np.where(sr == max(sr))[0][0]]

# initialize the pyplot
cm = plt.cm.get_cmap('RdBu')
sc = plt.scatter(vol, port_returns-rf, c=sr, vmin=min(sr), vmax=max(sr), cmap=cm)
cbar = plt.colorbar(sc)
circle = plt.Circle((max_sr[1], max_sr[0]-rf), 0.01, color='r', fill=False)
ax = plt.gca()
# ax.add_patch(circle)
cbar.set_label('Sharpe Ratio')
plt.xlabel('Volatility (STD)')
plt.ylabel('Excess Returns (Mean)')
plt.title('Efficient Portfolio Frontier')
plt.show()