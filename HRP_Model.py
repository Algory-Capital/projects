import pandas_datareader as get_data
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sklearn as sklearn
from scipy.cluster.hierarchy import linkage
import datetime


# Data Collection
tickers = ['AAPL','NVDA','UNH','JPM','XLE','COKE','NCLH','ADBE','F','GOLD'] #random 3 decent stocks

start_date = datetime.datetime(2022, 1, 1)
end = 'today'

results = get_data.get_data_yahoo(tickers, start_date)
results = results['Adj Close']

# Data Manipulation
returns = np.average(np.log(results))
volatility = np.std(returns)

df = pd.DataFrame({})
for asset in tickers:
    df[asset] = results[asset].pct_change()[1:]

mean = df.mean()
std = df.std()
print(std)

# Plotting
plt.scatter(std, mean)
for i, label in enumerate(tickers):
    plt.annotate(label, (std[i], mean[i]))
plt.title('Hierarchical Clusters')
plt.xlabel('Volatility')
plt.ylabel('Returns')
plt.show()