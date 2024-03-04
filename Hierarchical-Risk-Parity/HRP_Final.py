import matplotlib.pyplot as plt
import scipy.cluster.hierarchy as sch
import random
import numpy as np
import pandas as pd
import pandas_datareader.data as web
import yfinance as yfin
import datetime
import util as util
yfin.pdr_override()

def getIVP(cov):
    # Compute the inverse-variance portfolio
    ivp = 1./np.diag(cov)
    ivp /= ivp.sum()
    return ivp

def getClusterVar(cov, cItems):
    # Compute variance per cluster
    cov_ = cov.loc[cItems, cItems]
    w_ = getIVP(cov_).reshape(-1,1)
    cVar = np.dot(np.dot(w_.T, cov_), w_)[0,0]
    return cVar

def getQuasiDiag(link):
    # Sort clustered items by distance
    link = link.astype(int)
    sortIx = pd.Series([link[-1, 0], link[-1, 1]])
    numItems = link[-1, 3]  # number of original items
    while sortIx.max() >= numItems:
        sortIx.index = range(0, sortIx.shape[0] * 2, 2)  # make space
        df0 = sortIx[sortIx >= numItems]  # find clusters
        i = df0.index
        j = df0.values - numItems
        sortIx[i] = link[j, 0]  # item 1
        df0 = pd.Series(link[j, 1], index=i + 1)
        sortIx = pd.concat([sortIx, df0])  # item 2
        sortIx = sortIx.sort_index()  # re-sort
        sortIx.index = range(sortIx.shape[0])  # re-index
    return sortIx.tolist()

def getRecBipart(cov, sortIx):
    # Compute HRP alloc
    w = pd.Series(1, index= sortIx)
    cItems = [sortIx] # initialize all items in one cluster
    while len(cItems) > 0:
        cItems = [i[int(j) : int(k)] for i in cItems for j, k in ((0, len(i) / 2), (len(i) / 2, len(i))) if len(i) > 1] # bi-section

        for i in range(0, len(cItems), 2): # parse in pairs
            cItems0 = cItems[i] # cluster 1
            cItems1 = cItems[i + 1] # cluster 2

            cVar0 = getClusterVar(cov, cItems0) # risk contributions
            cVar1 = getClusterVar(cov, cItems1)
            alpha = 1 - cVar0 / (cVar0 + cVar1) # cluster weights
            w[cItems0] *= alpha # weight 1
            w[cItems1] *= 1 - alpha # weight 2
    return w

def getHRCBipart(cov, df, sortIx):
    w = pd.Series(1, index=sortIx)
    mean = df.mean()
    std = df.std()

    mean = (1 + mean) ** 12 - 1
    std = std * 12

    X = []
    for i in range(len(mean)): X.append([std[i], mean[i]])
    X = np.array(X)

    tickers_ = list(std.index)
    link = sch.linkage(X, method='ward')
    for row in link:
        cItems0 = tickers_[int(row[0])]
        cItems1 = tickers_[int(row[1])]
        flatten = lambda y: [x for a in y for x in flatten(a)] if type(y) is list else [y]
        if (True in [isinstance(cItems0[i], list) for i in range(len(cItems0))]):
            cItems0 = flatten(cItems0)
        if (True in [isinstance(cItems1[i], list) for i in range(len(cItems1))]):
            cItems1 = flatten(cItems1)
        tickers_.append([cItems0, cItems1])

        if (isinstance(cItems0, str)): cItems0 = [cItems0]
        if (isinstance(cItems1, str)): cItems1 = [cItems1]

        cVar0 = getClusterVar(cov, cItems0)  # risk contributions
        cVar1 = getClusterVar(cov, cItems1)
        alpha = 1 - cVar0 / (cVar0 + cVar1)  # cluster weights
        w[cItems0] *= alpha  # weight 1
        w[cItems1] *= 1 - alpha  # weight 2

    return w

def correlDist(corr):
    # A distance matrix based on correlation, where 0<=d[i,j]<=1
    # This is a proper distance metric
    dist = ((1 - corr) / 2.) ** .5 # distance matrix
    return dist

def plotCorrMatrix(corr, labels= None):
    # Heatmap of the correlation matric
    if labels is None: labels = []
    plt.pcolor(corr)
    plt.colorbar()
    plt.yticks(np.arange(0.5, corr.shape[0] + 0.5), labels)
    plt.xticks(np.arange(0.5, corr.shape[0] + 0.5), labels)
    plt.show()
    plt.clf()
    plt.close()
    return

tickers = util.get_tickers(include_AUM=False, include_SPY=False, include_CLOA=False)

start_date = datetime.datetime(2019, 4, 1)
end = datetime.datetime.today()

data = web.get_data_yahoo(tickers, start_date, end)
data = data['Adj Close']
df = data.pct_change()[1:]

#2) compute and plot correl matrix
cov, corr = df.cov(), df.corr()
plotCorrMatrix(corr,labels= corr.columns)

#3) cluster
dist = correlDist(corr)
link = sch.linkage(dist, method='ward')
sortIx = getQuasiDiag(link)
sortIx = corr.index[sortIx].tolist() # recover labels
df0 = corr.loc[sortIx, sortIx] # reorder
plotCorrMatrix(df0,labels=df0.columns)

#4) Capital allocation
hrp = getRecBipart(cov, sortIx)
hrc = getHRCBipart(cov, df, sortIx)
print('Hierarchical Risk Parity', hrp, sep='\n')
print('Hierarchical Risk Contribution', hrc, sep='\n')



# weighted_returns_hrp = np.sum(df * hrp[df.columns], axis = 1)
# sr_hrp = weighted_returns_hrp.mean() / weighted_returns_hrp.std() * 252 ** 0.5
# print('SHARPE RATIO OF HRP: ', sr_hrp)

# weighted_returns_hrc = np.sum(df * hrc[df.columns], axis = 1)
# sr_hrc = weighted_returns_hrc.mean() / weighted_returns_hrc.std() * 252 ** 0.5
# print('SHARPE RATIO OF HRC: ', sr_hrc)

# herc = pd.Series([0.0625, 0.125, 0.5, 0.125, 0.0625, 0.125], index=list(cov.index))
# weighted_returns_herc = np.sum(df * herc[df.columns], axis= 1)
# sr_herc = weighted_returns_herc.mean() / weighted_returns_herc.std() * 252 ** 0.5
# print('SHARPE RATIO OF HERC: ', sr_herc)

# cur = [0.115, 0.135, 0.042, 0.108, 0.109, 0.048]
# cur = pd.Series([cur[i] / sum(cur) for i in range(len(cur))], index=list(cov.index))
# weighted_returns_cur = np.sum(df * cur[df.columns], axis= 1)
# sr_cur = weighted_returns_cur.mean() / weighted_returns_cur.std() * 252 ** 0.5
# print('SHARPE RATIO OF CURRENT PORT: ', sr_cur)

# plotdf = pd.DataFrame({'hrp' : hrp, 'hrc' : hrc, 'herc' : herc, 'current' : cur}, index=list(df.std().index))
# plotdf.plot.bar(rot=0, color= ['#9FE4FF', '#01A7EA', '#0241CE', '#022E91'], title= 'Weights of Different Algorithms')
# plt.show()