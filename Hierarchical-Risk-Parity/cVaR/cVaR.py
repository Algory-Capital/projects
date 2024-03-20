"""
@Project ：Hierarchical-Risk-Parity 
@File    ：cVaR
@Author  ：Jiuru Lyu
@Date    ：2024/03/12
"""

# Importing the libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
import datetime as dt

# Data Collection
# get data
def getData(ticker, start, end):
    """
    Get data from Yahoo Finance
    :param ticker: the ticker of the stock
    :param start: the start date of inquiry
    :param end: the end date of inquiry
    :return: the returns, maximum returns, and covariance matrix
    """
    data = yf.download(ticker, start=start, end=end);
    data = data["Close"]
    returns = data.pct_change()
    meanReturns = returns.mean()
    covMatrix = returns.cov()
    return returns, meanReturns, covMatrix

# portfolio performance
def portfolioPerformance(weights, meanReturns, covMatrix, Time):
    """
    Calculate the portfolio performance
    :param weights: the weights of the portfolio
    :param meanReturns: the mean returns of the portfolio
    :param covMatrix: the covariance matrix of the portfolio
    :param Time:tThe time frame of selection
    :return: returns and standard deviation
    """
    returns = np.sum(meanReturns * weights) * Time
    std = np.sqrt(np.dot(weights.T, np.dot(covMatrix, weights))) * np.sqrt(Time)
    return returns, std

# Preparation
df = pd.read_csv("../current_values.csv")
stocks = df["Ticker"].tolist()
endDate = dt.datetime.now()
startDate = endDate - dt.timedelta(days=365)

returns, meanReturns, covMatrix = getData(stocks, startDate, endDate)
returns = returns.dropna()

weights = df["Percentage of Portfolio"].tolist()
for i in range(len(weights)):
    weights[i] = float(weights[i].strip("%"))/100

weights /= np.sum(weights)

returns["portfolio"] = returns.dot(weights)


# Monte Carlo
mc_sims = 10000 # number of simulations
T = 365       # number of trading days

meanM = np.full(shape=(T, len(weights)), fill_value=meanReturns)
meanM = meanM.T

portfolio_sims = np.full(shape=(T, mc_sims), fill_value=0.0)

initialPortfolio = 100000

for m in range(0, mc_sims):
    # Monte Carlo main loop
    Z = np.random.normal(size=(T, len(weights)))
    L = np.linalg.cholesky(covMatrix)
    dailyReturns = meanM + np.inner(L, Z)
    portfolio_sims[:, m] = np.cumprod(np.inner(weights, dailyReturns.T) + 1) * initialPortfolio

# Plotting part
plt.plot(portfolio_sims)
plt.ylabel("Portfolio Value")
plt.xlabel("Trading Days")
plt.title("Monte Carlo Simulation of Portfolio")
plt.show()
plt.savefig("monte_carlo_simulation.png")

# Calculate the VaR and CVaR
def mcVaR(returns, alpha=5):
    """
    Args:
        returns (panda series): daily returns of the portfolio
        alpha (int): significance level

    Returns:
        float: conditional value at risk
    """

    if isinstance(returns, pd.Series):
        return np.percentile(returns, alpha)
    else:
        raise TypeError("Expected returns to be a pandas series")


# Use mcVaR to calculate the VaR and CVaR
def mcCVaR(returns, alpha=5):
    """
    Args:
        returns (panda series): daily returns of the portfolio
        alpha (int): significance level

    Returns:
        float: conditional value at risk
    """

    if isinstance(returns, pd.Series):
        belowVaR = returns <= mcVaR(returns, alpha)
        return returns[belowVaR].mean()
    else:
        raise TypeError("Expected returns to be a pandas series")



portResults = pd.Series(portfolio_sims[-1, :])

VaR = initialPortfolio - np.percentile(portResults, 5)
CVaR = initialPortfolio - mcCVaR(portResults, 5)

print(f"Value at Risk: {VaR}")
print(f"Conditional Value at Risk: {CVaR}")