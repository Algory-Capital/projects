# https://stackoverflow.com/questions/9876290/how-do-i-compute-derivative-using-numpy
# https://www.statisticshowto.com/what-is-the-ornstein-uhlenbeck-process/
import numpy as np

"""
dx_t= -theta * (mu - x_t) * dt+ sigma * dW_t

x_t: spread at time t
theta: mean-reversion constant
mu: mean (particle)position
sigma: volatility, coefficient of Wiener process
Wt: Wiener process
    - dWt represents white noise (brownian motion)

"""

x = np.linspace(0, 10, 1000)
dx = x[1] - x[0]
y = x**2 + 1
dydx = np.gradient(y, dx)
