# https://stackoverflow.com/questions/9876290/how-do-i-compute-derivative-using-numpy
# https://www.statisticshowto.com/what-is-the-ornstein-uhlenbeck-process/
# https://gist.github.com/jimfleming/9a62b2f7ed047ff78e95b5398e955b9e
# https://stackoverflow.com/questions/34095946/python-3-5-numpy-how-to-avoid-deprecated-technique
# https://hudsonthames.org/optimal-stopping-in-pairs-trading-ornstein-uhlenbeck-model/
# https://www.youtube.com/watch?v=UrE-ckatris
# https://pypi.org/project/ouparams/
# https://github.com/cantaro86/Financial-Models-Numerical-Methods/blob/master/6.1%20Ornstein-Uhlenbeck%20process%20and%20applications.ipynb
# https://arxiv.org/pdf/2003.10502.pdf

import numpy as np
import statsmodels.api as sm
import numpy as np
from scipy.stats import norm
import matplotlib.pyplot as plt

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
###


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

# Set up a class object

# example = omr.OrnsteinUhlenbeck()

#
