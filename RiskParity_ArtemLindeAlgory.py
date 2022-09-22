"""
Artem Linde
Risk Parity
September 16, 2022
Algory Capital
"""

import numpy as np
import pandas as pd
import pandas_datareader as get_data
import datetime
from scipy.optimize import minimize
#optional
import matplotlib.pyplot as plt
import seaborn as sb

def ARC(weights, cov): #Assets risk contributions
    #print(np.multiply(weights.T, (cov * weights.T)))
    return (np.multiply(weights.T, (cov * weights.T))) / (np.sqrt((weights * cov * weights.T))[0, 0])

def RBO(weights, args): #Risk budget objective
    weights = np.matrix(weights)
    cov = args[0]
    assets_risk_budget = args[1]
    assets_risk_cons = ARC(weights, cov)
    return sum(np.square(assets_risk_cons - (np.asmatrix(np.multiply((np.sqrt((weights * cov * weights.T))[0, 0]), assets_risk_budget))).T))[0, 0]

def optimizer(cov, assets_risk_budget, start_weights):
    cons = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}, {'type': 'ineq', 'fun': lambda x: x}) #constraints
    optimize_result = minimize(RBO, x0=start_weights, args=[cov, assets_risk_budget], method='SLSQP', constraints=cons, options={'disp':False})
    return optimize_result.x

def get_weights(tickers, start_date):
    end_date=datetime.datetime.today()
    prices = pd.DataFrame([get_data.DataReader(i, 'yahoo', start_date, end_date).loc[:, 'Adj Close'] for i in tickers], index=tickers).T
    #cov = np.log(prices).diff().cov().values
    #cov = 252 * prices.asfreq('B').pct_change().iloc[1:, :].cov().values
    returns = np.log(prices / prices.shift(1))
    cov = returns.cov() * 252 #covariance matrix
    cov = cov.to_numpy()
    #print(type(cov))
    assets_risk_budget = [1.0 / prices.shape[1]] * prices.shape[1]
    #seaborn heatmap
    sb.set()
    cor_map = sb.heatmap(returns.corr(), vmin=0, vmax=1)#, cmap='YlGnBu') #pretty color
    plt.show()
    #plt.clf()
    #assets_risk_cons = ARC(weights, cov)
    #risk_budget_objective = RBO(weights, cov)
    start_weights = [1.0 / prices.shape[1]] * prices.shape[1]
    weights = optimizer(cov, assets_risk_budget, start_weights)
    weights = pd.Series(weights, index=prices.columns, name='weight')
    return weights

# begins
sb.color_palette("Spectral", as_cmap=True)
#^ seaborn colors
start_date = datetime.datetime(2022,1,1) #year, month, day
#tickers = ['AAPL', 'AMD', 'JPM'] #random 3 decent stocks
tickers = ['TSLA', 'KO', 'AAPL', 'AXP', 'RACE', 'AMD', 'JPM', 'UNH', 'PLD', 'MRK', 'BHP', 'WMT', 'APD', 'T', 'XOM'] #algory previous portfolio
#tickers = ['OXY', 'CEG', 'HES', 'CTRA', 'DVN', 'MPC', 'ENPH', 'XOM', 'VLO', 'MRO'] #insane sharpe + L + ratio
#tickers = ['LAD', 'TNL', 'MLI', 'FBP', 'HRI', 'DVN', 'MRO', 'QCOM', 'BRK-A', 'MU'] #good outlook
#tickers = ['TRMD', 'AMR', 'VERU', 'PBF', 'NEX', 'TMDX', 'LNTH', 'CEIX', 'STNG', 'TH']
weights = get_weights(tickers, start_date)
print(weights)
#analisis:
print("Optimized vs Equal")
weights = weights.tolist()
prices = get_data.get_data_yahoo(tickers, start_date)
prices = prices['Adj Close']
#log_returns = np.sum(np.log(prices / prices.shift()) * weights, axis = 1)
log_returns = np.sum(prices.pct_change()[1:] * weights, axis = 1)
sharpe_ratio = log_returns.mean() / log_returns.std()
sharpe_ratio = sharpe_ratio*252**0.5
weights_e = [1.0 / prices.shape[1]] * prices.shape[1]
#log_returns_e = np.sum(np.log(prices / prices.shift()) * weights_e, axis = 1)
log_returns_e = np.sum(prices.pct_change()[1:] * weights_e, axis = 1)
sharpe_ratio_e = log_returns_e.mean() / log_returns_e.std()
sharpe_ratio_e = sharpe_ratio_e*252**0.5
print('Sharpe ratio [optimized] =', sharpe_ratio, 'vs Sharpe ratio [equal alocation] =', sharpe_ratio_e)
#plot
ret_data = prices.pct_change()[1:]
weighted_returns = (weights * ret_data)
#print(weighted_returns.head())
port_ret = weighted_returns.sum(axis=1)
cumulative_ret = (port_ret + 1).cumprod()
cumulative_ret = 100 * cumulative_ret
#we save out graph**
saved_graph = cumulative_ret
#saving done
fig = plt.figure()
ax1 = fig.add_axes([0.1,0.1,0.8,0.8])
ax1.plot(cumulative_ret)
ax1.set_xlabel('Date')
ax1.set_ylabel("Cumulative Returns %")
ax1.set_title("Portfolio optimized Cumulative Returns vs equal weights")

weighted_returns = (weights_e * ret_data)
#print(weighted_returns.head())
port_ret = weighted_returns.sum(axis=1)
cumulative_ret = (port_ret + 1).cumprod()
cumulative_ret = 100 * cumulative_ret
cumulative_ret.plot(fig=fig)
plt.legend(['Portfolio returns optimized', 'equal weights'])
plt.show();

#print(sum(weights))

#our vs spy
print("Optimized vs SPY")
plt.clf()
ticker = 'SPY'
prices_spy = get_data.get_data_yahoo(ticker, start_date)
prices_spy = prices_spy['Adj Close']
sharpe_ratio_spy = ((sum(prices_spy) / len(prices_spy)) / (((sum([x - (sum(prices_spy) / len(prices_spy)) ** 2 for x in prices_spy])) / (len(prices_spy)-1)**(1/2))))
sharpe_ratio_spy = sharpe_ratio_spy * 252 ** 0.5
#our port
fig = plt.figure()
ax1 = fig.add_axes([0.1,0.1,0.8,0.8])
ax1.plot(saved_graph)
ax1.set_xlabel('Date')
ax1.set_ylabel("Cumulative Returns %")
ax1.set_title("Portfolio optimized Cumulative Returns vs SPY")
#port ends
ret_data = prices_spy.pct_change()[1:]
ret_data = ret_data.to_frame()
port_ret = ret_data.sum(axis=1)
cumulative_ret = 100 * (port_ret + 1).cumprod()
cumulative_ret.plot(fig=fig)
plt.legend(['Portfolio returns optimized', 'SPY'])
plt.show();
print('Sharpe ratio [optimized] =', sharpe_ratio, 'vs Sharpe ratio [SPY] =', sharpe_ratio_spy)
