# import the modules
import pandas_datareader.data as pdr
import pandas as pd
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import yfinance as yfin # For my beta version of MacOS - Not necessary
yfin.pdr_override()

# choose a portfolio of 7 tickers
tickers = ['BRK-B','AAPL','RITM','JPM','MSFT','GT', 'CCL']

# Set the end date
end = dt.datetime.now()

# choose a start date time delta
start = end - dt.timedelta(days=300)

# get the monthly returns
data = pdr.get_data_yahoo(tickers, start)
data = data['Adj Close']

# Get the percent change
data = data.pct_change()

# Calculate the mean and covariance matrices
mean = data.mean()
cov = data.cov()

# Initialize random weights
weights = np.random.random(len(mean))
weights = weights / np.sum(weights)

# Initialize Monte Carlo variables
numSims = 100
days = 100
initialPortfolio = 100000

# Initialize a returns matrix for each stock, with however many days you plan to run it
meanRets = np.full(shape=(days, len(weights)), fill_value=mean)
print(meanRets)
meanRets = meanRets.T
print(meanRets)

portfolioSims = np.full(shape=(days, numSims), fill_value=0.0)


# Run the simulations
for i in range(numSims):
    # Generate random data (no correlation) using normal distribution
    Z = np.random.normal(size=(days, len(weights)))

    # Use Cholesky Decomp to determine Lower Triangle Matrix to associate random data with covariance of the stocks
    L = np.linalg.cholesky(cov)
    dailyRets = meanRets + np.inner(L, Z)

    # Record portfolio daily returns
    portfolioSims[:, i] = np.cumprod(np.inner(weights, dailyRets.T) + 1) * initialPortfolio

# Plot the simulations
plt.plot(portfolioSims)
plt.ylabel('Portfolio Value ($)')
plt.xlabel('Days')
plt.title('MC Simulation')

# Get the last return for each simulation
portResults = pd.Series(portfolioSims[-1, :])

# Get the Value at Risk for alpha = 0.05
var = np.percentile(portResults, 5)

# Get the Conditional Value at Risk for alpha = 0.05
belowVar = portResults <= var

var = initialPortfolio - var
cvar = initialPortfolio - portResults[belowVar].mean()

print(initialPortfolio - var)
print(initialPortfolio - cvar)

plt.axhline(y=initialPortfolio - var, color='b', linestyle='dashed', label='var')
plt.axhline(y=initialPortfolio - cvar, color='r', linestyle='dashed', label='cvar')
plt.legend(loc='upper center')
plt.show()