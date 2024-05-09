# https://stackoverflow.com/questions/9876290/how-do-i-compute-derivative-using-numpy
# https://www.statisticshowto.com/what-is-the-ornstein-uhlenbeck-process/
# https://gist.github.com/jimfleming/9a62b2f7ed047ff78e95b5398e955b9e
# https://stackoverflow.com/questions/34095946/python-3-5-numpy-how-to-avoid-deprecated-technique
# https://hudsonthames.org/optimal-stopping-in-pairs-trading-ornstein-uhlenbeck-model/
# https://www.youtube.com/watch?v=UrE-ckatris
# https://pypi.org/project/ouparams/
# https://github.com/cantaro86/Financial-Models-Numerical-Methods/blob/master/6.1%20Ornstein-Uhlenbeck%20process%20and%20applications.ipynb
# https://arxiv.org/pdf/2003.10502.pdf
# https://www.youtube.com/watch?v=UrE-ckatris
# Optimal Exit: https://arxiv.org/pdf/1906.01255.pdf

# https://colab.research.google.com/drive/1dphtsPZSQxwe9YuadyKWv5BTuQYW36w7#scrollTo=IEMIdRR-1EIc
import numpy as np
import statsmodels.api as sm
import numpy as np
from scipy.stats import norm
from scipy.optimize import minimize
import matplotlib.pyplot as plt
from adf import regress_two
import pandas as pd
import os

"""
dx_t= -theta * (mu - x_t) * dt+ sigma * dW_t

x_t: spread at time t
theta: mean-reversion constant
mu: mean (particle)position
sigma: volatility, coefficient of Wiener process
Wt: Wiener process
    - dWt represents white noise (brownian motion)

"""

###
# Parameters
n_obs = 100
mu = 0.05  # Drift
sigma = 0.2  # Volatility
theta = 0.1  # True mean-reverting parameter
dt = 0.1

# Initial guess for our parameters
p0 = [1, 1, 1]
###

root = "StatArb/"
spy_path = "spy.csv"

spy = pd.read_csv(os.path.join(root, spy_path))


def apply_ou(prices):
    """
    Return holding period
    """
    """ou_process = sm.tsa.OrnsteinUhlenbeckProcess(theta_true)
    ou_prices = ou_process.simulate(n_obs, initial_value=prices[0])

    model = sm.tsa.OrnsteinUhlenbeck(prices)
    results = model.fit()

    theta_estimate = results.params["theta"]

    print(results.params)

    print(f"\n\nTrue Theta: {theta_true}")
    print(f"Estimated Theta: {theta_estimate}")"""

    processes = 1
    samples = 1000

    X = np.zeros(shape=(samples, processes))
    print(type(X))
    X = prices
    print(type(X))
    for t in range(1, samples - 1):
        dw = norm.rvs(
            scale=dt, size=processes
        )  # W: Wierner process, dw: brownian velocity
        dx = theta * (mu - X[t]) * dt + sigma * dw
        X[t + 1] = X[t] + dx


returns = np.random.normal(mu, sigma, n_obs)
prices = np.cumsum(returns)
print(type(prices))

apply_ou(prices)

## GET PARAMETERS SIGMA, THETA, MU


# Code distribution function
def OU(x1, x2, dt, theta, mu, sigma):
    sigma0 = sigma**2 * (1 - np.exp(-2 * mu * dt)) / (2 * mu)  # sigma tilde squared
    sigma0 = np.sqrt(sigma0)

    prefactor = 1 / np.sqrt(2 * np.pi * sigma0**2)  # square root term before Exp

    f = prefactor * np.exp(
        -((x2 - x1 * np.exp(-mu * dt) - theta * (1 - np.exp(-mu * dt))) ** 2)
        / (2 * sigma0**2)
    )

    return f


# calculate negaitve of log likelihood
def log_likelihood_OU(p, X, dt):
    """
    p: parameters
    X: data
    dt: timestep
    """
    theta = p[0]
    mu = p[1]
    sigma = p[2]

    N = X.size
    f = np.zeros((N - 1,))  # N-1 because differencing N terms once

    for i in range(1, N):
        x2 = X[i]
        x1 = X[i - 1]

        f[i - 1] = OU(x1, x2, dt, theta, mu, sigma)

    # hacky
    ind = np.where(f == 0)
    ind = ind[0]
    if ind.size > 0:
        f[ind] = 10**-8

    f = np.log(f)
    f = np.sum(f)

    return -f  # return negative because we are trying to maximize


def constraint1(p):
    return p[1]


def constraint2(p):
    return p[2]


def get_process_data(t1, t2, day_number=None):  # We need to snip off dates
    beta = regress_two(t1, t2)
    df1 = spy[t1]  # returns series, not dataframe
    df2 = spy[t2]

    combined = pd.merge(df1, df2, how="inner", left_index=True, right_index=True)

    beta = regress_two(t1, t2)  # regress t1 on t2

    combined[t2].apply(lambda x: x * beta)  # create linear combination
    combined = combined[t1] - combined[t2]  # get residuals

    return combined


cons = ({"type": "ineq", "fun": constraint1}, {"type": "ineq", "fun": constraint2})

X = get_process_data("A", "AAPL")

minimize(log_likelihood_OU, p0, args=(X, dt), constraints=cons)
