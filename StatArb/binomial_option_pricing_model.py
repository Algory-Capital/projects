import numpy as np

# ASSUMPTIONS OF THIS MODEL
# 1 Risk-Neutral Probability of stock moving: Price can move in any direction
# 2 Put can be exercised at any point - American
# 3 For our model, Strike Price = initial stock price

def build_tree(initial_price, r, sigma, T, N):
    dt = T / N  # length of each period

    u = np.exp(sigma * np.sqrt(dt))
    d = np.exp(-sigma * np.sqrt(dt))
    p = (np.exp(r * dt) - d) / (u - d)  # risk-neutral probability of up move

    # Create the binomial tree for the stock price
    S = np.zeros((N + 1, N + 1))  # initialize the stock price matrix
    S[0, 0] = initial_price  # set the initial stock price

    for i in range(1, N + 1):  # loop over the periods
        for j in range(i + 1):  # loop over the nodes
            S[j, i] = S[0, 0] * (u ** (i - j)) * (d ** j)  # calculate the stock price at each node

    return S

def put_option_price(stock_price, strike_price, r, T, N, sigma):
    dt = T / N  # length of each period

    option_values = np.zeros((N + 1, N + 1))

    # Calculate option values at maturity
    for j in range(N + 1):
        option_values[j, N] = max(0, strike_price - stock_price[j, N])

    # Backward induction to calculate option values at previous nodes
    for i in range(N - 1, -1, -1):
        for j in range(i + 1):
            intrinsic_value = max(0, strike_price - stock_price[j, i])
            continuation_value = np.exp(-r * dt) * (
                    p * option_values[j, i + 1] + (1 - p) * option_values[j + 1, i + 1])
            option_values[j, i] = max(intrinsic_value, continuation_value)

    return option_values[0, 0]

def get_option_price(stock_price):


    #modifyable settings
    stock_price = 370.2
    strike_price = stock_price
    T = 1  # time to maturity in years
    r = 0.0446  # risk-free interest rate - manually gotten
    sigma = 0.2  # volatility of the stock
    N = 10
    stock_price_tree = build_tree(strike_price, r, sigma, T, N)

    result = put_option_price(stock_price_tree, strike_price, r, T, N, sigma)
    print(f"Put Option Price: {result:.2f}")

    return result


