

import pandas_datareader.data as web
import pandas as pd
import yfinance as yfin
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sklearn as sklearn
import scipy.cluster.hierarchy as sch
import datetime
import seaborn as sb
import operator
from collections import defaultdict
import random
# from Hierarchical_risk_parity import compute_HRP_weights

yfin.pdr_override()

# Data Collection - INCLUDE BONDS ETFS
tickers = ['AAPL', 'MSFT', 'NVDA', 'V', 'MA', 'ADBE', 'AVGO', 'CSCO', # tech
           'UNH', 'JNJ', 'PFE', 'ABBV', 'LLY', 'MRK', 'TMO', 'ABT', # healthcare
           'JPM', 'AXP', 'BAC', 'CVBF', 'MS', 'COOP', 'FITB', 'XLE','COKE','F','GOLD']
# tickers = random.sample(tickers, len(tickers))
tickers = ['AAPL','NVDA','UNH','JPM','XLE','COKE','NCLH','ADBE','F','GOLD']
tickers = ['BRK-B','AAPL','RITM','JPM','MSFT','GT']

start_date = datetime.datetime(2022, 4, 1)
end = datetime.datetime(2023, 8, 1)

data = web.get_data_yahoo(tickers, start_date, end)
# data = web.DataReader('GE', 'yahoo', start='2019-09-10', end='2020-10-09')
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

covariances = cov
res_order = range(len(tickers))

# weights = compute_HRP_weights(covariances, tickers)
# print(weights)
print(list(std.index))

X = []
for i in range(len(mean)):
    X.append([std[i], mean[i]])
X = np.array(X)
link = sch.linkage(X, method='ward')
dendrogram = sch.dendrogram(link, labels=data.columns)
plt.title('Dendrogram')
plt.show()

print(link)
tickers_ = list(std.index)
for row in link:
    cItems0 = tickers_[int(row[0])]
    cItems1 = tickers_[int(row[1])]
    # if (True in [isinstance(cItems0[i], list) for i in range(len(cItems0))]):
    #     flatten = lambda y:[x for a in y for x in flatten(a)] if type(y) is list else [y]
    #     cItems0 = flatten(cItems0)
    # if (True in [isinstance(cItems1[i], list) for i in range(len(cItems1))]):
    #     flatten = lambda y:[x for a in y for x in flatten(a)] if type(y) is list else [y]
    #     cItems1 = flatten(cItems1)

    tickers_.append([cItems0, cItems1])

print(tickers_)


from sklearn.cluster import AgglomerativeClustering
hc = AgglomerativeClustering(n_clusters=3, linkage= 'ward')
y_hc = hc.fit_predict(X)

def get_cluster_classes(den, label='ivl'):
    cluster_idxs = defaultdict(list)
    for c, pi in zip(den['color_list'], den['icoord']):
        for leg in pi[1:3]:
            i = (leg - 5.0) / 10.0
            if abs(i - int(i)) < 1e-5:
                cluster_idxs[c].append(int(i))

    cluster_classes = {}
    for c, l in cluster_idxs.items():
        i_l = [den[label][i] for i in l]
        cluster_classes[c] = i_l

    return cluster_classes

order = {}
for i in range(len(y_hc)):
    order[tickers[i]] = [y_hc[i], i]


clusters = {}
for i, merge in enumerate(link):
        if merge[0] <= len(link):
            # if it is an original point read it from the centers array
            a = tickers[int(merge[0]) - 1]
        else:
            # otherwise read the cluster that has been created
            a = clusters[int(merge[0])]

        if merge[1] <= len(link):
            b = tickers[int(merge[1]) - 1]
        else:
            b = clusters[int(merge[1])]
        # the clusters are 1-indexed by scipy
        clusters[1 + i + len(link)] = {
            'children' : [a, b]
        }
print(clusters)




ordersorted = sorted_x = sorted(order.items(), key=operator.itemgetter(1))
print(ordersorted)

res_order = []
for key, pair in order.items():
    print(pair)


colors = ['red', 'blue', 'green', 'cyan', 'magenta']
for i in range(max(y_hc) + 1):
    plt.scatter(X[y_hc == i, 0], X[y_hc == i, 1], s= 100, c= colors[i], label='Cluster {}'.format(i + 1))

for i in range(len(tickers)):
    plt.annotate(list(std.index)[i], (X[i, 0], X[i, 1]))


# Plotting
# plt.scatter(std, mean)
# for i, label in enumerate(tickers):
#     plt.annotate(label, (std[i], mean[i]))
plt.title('Hierarchical Clusters')
plt.xlabel('Volatility')
plt.ylabel('Returns')
plt.show()
