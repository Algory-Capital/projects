%pip install pandas 
*pip install pandas_datareader
*pip install numpy 
*pip install matplotlib.pyplot 
*pip install seaborn
*pip install sklearn 
*pip install datetime 
*pip install seaborn

import pandas_datareader as get_data
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sklearn as sklearn
import scipy.cluster.hierarchy as sch
import datetime
import seaborn as sb


# Data Collection - INCLUDE BONDS ETFS
tickers = ['AAPL', 'MSFT', 'NVDA', 'V', 'MA', 'ADBE', 'AVGO', 'CSCO', # tech
           'UNH', 'JNJ', 'PFE', 'ABBV', 'LLY', 'MRK', 'TMO', 'ABT', # healthcare
           'JPM', 'AXP', 'BAC', 'CVBF', 'MS', 'COOP', 'FITB', 'XLE','COKE','NCLH','F','GOLD']
# tickers = ['AAPL','NVDA','UNH','JPM','XLE','COKE','NCLH','ADBE','F','GOLD']

start_date = datetime.datetime(2020, 4, 1)
end = 'today'

data = get_data.get_data_yahoo(tickers, start_date)
data = data['Adj Close']
df = data.pct_change()[1:]

# Data Manipulation
mean = df.mean()
std = df.std()
cov = df.corr()

# sb.set()
# sb.color_palette("Spectral", as_cmap=True)
# sb.heatmap(cov, vmin=0, vmax=1)

mean = (1 + mean) ** 12 - 1
std = std * 12

X = []
for i in range(len(mean)):
    X.append([std[i], mean[i]])
X = np.array(X)

dendrogram = sch.dendrogram(sch.linkage(X, method='ward'))
plt.title('Dendrogram')
plt.xlabel('Volatility')
plt.ylabel('Returns')
plt.show()
#
from sklearn.cluster import AgglomerativeClustering
hc = AgglomerativeClustering(n_clusters=4, affinity= 'euclidean', linkage= 'ward')
y_hc = hc.fit_predict(X)
print(y_hc)

order = {}
for i in range(len(y_hc)):
    order[tickers[i]] = y_hc[i]


print(order)
#
# colors = ['red', 'blue', 'green', 'cyan', 'magenta']
# for i in range(max(y_hc) + 1):
#     plt.scatter(X[y_hc == i, 0], X[y_hc == i, 1], s= 100, c= colors[i], label='Cluster {}'.format(i + 1))
#
#
# # Plotting
# plt.scatter(std, mean)
# for i, label in enumerate(tickers):
#     plt.annotate(label, (std[i], mean[i]))
# plt.title('Hierarchical Clusters')
# plt.xlabel('Volatility')
# plt.ylabel('Returns')
# plt.show()