import matplotlib.pyplot as plt
import pandas_datareader as web

# Define a function to get the returns of a portfolio using weights,
# a start_date, and end_date
def getReturns(start, end, portfolio, weights):
    # Get portfolio data using web
    price_data = web.get_data_yahoo(portfolio, start=start, end=end)
    print(price_data)
    # Select Adjusted Close
    price_data = price_data['Adj Close']

    # Store percent change of data
    ret_data = price_data.pct_change()[1:]
    # Store the weighted returns into a new dataframe
    weighted_returns = (weights * ret_data)
    print(weighted_returns)
    # Sum of portfolio weighted returns
    port_ret = weighted_returns.sum(axis=1)
    # Cumulative returns using cumprod()
    cumulative_ret = (port_ret + 1).cumprod() * 100
    # Return these cumulative returns
    return cumulative_ret

# Start and end date
start = '2002-01-01'
end = 'today'
# Create a portfolio of tickers
classTicker = ['PANW', 'GME', 'AMC', 'AMZN', 'TSLA', 'BB', 'MS']
# Manually select weights for each ticker
classWts = [0.1, 0.2, 0.1, 0.05, 0.05, 0.25, 0.25]
# Store the portfolio returns using the function we made
classReturns = getReturns(start, end, classTicker, classWts)

# Create of portfolio of the benchmark (SPY)
benchTicker = ['SPY']
# Assign weight to this portfolio
benchWts = [1]
# Store the benchmark returns using the function we made
benchReturns = getReturns(start, end, benchTicker, benchWts)

# Plotting the cumulative returns of both portfolios
# TODO: add_axes, plot first, set_xlabel, set_ylabel, set_title, plot second, legend, show
fig = plt.figure()
ret_graph = fig.add_axes([0.1, 0.1, 0.8, 0.8])
ret_graph.plot(classReturns)
ret_graph.set_xlabel('Date')
ret_graph.set_ylabel("Cumulative Returns %")
ret_graph.set_title("Portfolio Cumulative Returns vs SPY")

benchReturns.plot(fig=ret_graph)
plt.legend(['Portfolio returns', 'SPY'])
plt.show()
