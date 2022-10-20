# import the modules
import pandas_datareader.data as web
import pandas as pd
import numpy as np
import math
import plotly.graph_objects as go

# choose a portfolio of 3 tickers
tickers = ['AAPL', 'BRK-B', 'XLE']

# choose a start date
start = '2013-01-01'

# get the monthly returns
data = web.get_data_yahoo(tickers, start)
data = data['Adj Close']

# change into percent change
df = pd.DataFrame()
for asset in tickers:
    df[asset] = data[asset].pct_change()[1:]


#-- Get annualised mean returns
mus = (1+df.mean())**252 - 1

#-- Get covariances and variances
#- Variance along diagonal of covariance matrix
#- Multiply by 252 to annualise it
#- https://quant.stackexchange.com/questions/4753/annualized-covariance
cov = df.cov()*252

# - How many assests to include in each portfolio
n_assets = 3
# -- How many portfolios to generate
n_portfolios = 1000

# -- Initialize empty list to store mean-variance pairs for plotting
mean_variance_pairs = []

np.random.seed()
# -- Loop through and generate lots of random portfolios
for i in range(n_portfolios):
    # - Choose assets randomly without replacement
    assets = np.random.choice(list(df.columns), n_assets, replace=False)
    # - Choose weights randomly
    weights = np.random.rand(n_assets)
    # - Ensure weights sum to 1
    weights = weights / sum(weights)

    # -- Loop over asset pairs and compute portfolio return and variance
    # - https://quant.stackexchange.com/questions/43442/portfolio-variance-explanation-for-equation-investments-by-zvi-bodie
    portfolio_E_Variance = 0
    portfolio_E_Return = 0
    for i in range(len(assets)):
        portfolio_E_Return += weights[i] * mus.loc[assets[i]]
        for j in range(len(assets)):
            # -- Add variance/covariance for each asset pair
            # - Note that when i==j this adds the variance
            portfolio_E_Variance += weights[i] * weights[j] * cov.loc[assets[i], assets[j]]

    # -- Add the mean/variance pairs to a list for plotting
    mean_variance_pairs.append([portfolio_E_Return, portfolio_E_Variance])

mean_variance_pairs = np.array(mean_variance_pairs)
risk_free_rate=0 #-- Include risk free rate here for sharpe ratio


#-- Create Plot
fig = go.Figure()
fig.add_trace(go.Scatter(x=mean_variance_pairs[:,1]**0.5,
                         y=mean_variance_pairs[:,0],
                      #- Add color scale for sharpe ratio
                      marker=dict(color=(mean_variance_pairs[:,0]-risk_free_rate)/(mean_variance_pairs[:,1]**0.5),
                                  showscale=True,
                                  size=7,
                                  line=dict(width=1),
                                  colorscale="RdBu",
                                  colorbar=dict(title="Sharpe<br>Ratio")
                                 ),
                      mode='markers'))
#- Add title/labels
fig.update_layout(template='plotly_white',
                  xaxis=dict(title='Annualised Risk (Volatility)'),
                  yaxis=dict(title='Annualised Return'),
                  title='Sample of Random Portfolios',
                  coloraxis_colorbar=dict(title="Sharpe Ratio"))

fig.show()