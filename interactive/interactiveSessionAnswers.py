import matplotlib.pyplot as plt
import pandas_datareader as web

# Define a function to get the returns of a portfolio using weights,
# a start_date, and end_date
def getReturns(portfolio, weights, start, end):
    # Get portfolio data using web
    price_data = web.get_data_yahoo(portfolio, start=start, end=end)
    # Select Adjusted Close
    price_data = price_data['Adj Close']

    # Store percent change of data
    ret_data = price_data.pct_change()[1:]
    # Store the weighted returns into a new dataframe
    weighted_returns = (weights * ret_data)
    print(weighted_returns.head())

    # Sum of portfolio weighted returns
    port_ret = weighted_returns.sum(axis=1)
    # Cumulative returns using cumprod()
    cumulative_ret = (port_ret + 1).cumprod() * 100
    # Return these cumulative returns
    return cumulative_ret

# Start and end date
start = '2022-04-04'
end = 'today'

# Create a portfolio of tickers
classTickers = ['MS']
# Manually select weights for each ticker
classWts = [1]
# Store the portfolio returns using the function we made
classReturns = getReturns(classTickers, classWts, start, end)

# Create of portfolio of the benchmark (SPY)
benchTickers = ['SPY']
# Assign weight to this portfolio
benchWts = [1]
# Store the benchmark returns using the function we made
benchReturns = getReturns(benchTickers, benchWts, start, end)

# Plotting the cumulative returns of both portfolios
# TODO: add_axes, plot first, set_xlabel, set_ylabel, set_title, plot second, legend, show
fig = plt.figure()
ret_graph = fig.add_axes([0.1,0.1,0.8,0.8])
ret_graph.plot(classReturns)
ret_graph.set_xlabel('Date')
ret_graph.set_ylabel("Cumulative Returns %")
ret_graph.set_title("Portfolio Cumulative Returns vs SPY")

benchReturns.plot(fig=ret_graph)
plt.legend(['Portfolio returns', 'SPY'])
plt.show()