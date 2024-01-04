import numpy as np

settings = {
    'T': 2 / 52,        # time to maturity in years
    'r': 0.0446,        # risk-free interest rate
    'sigma': 0.2,       # volatility of stock
    'N': 5              # number of nodes in tree
}

def binomial_tree_and_option_price(initial_price, strike_price, option_type='put'):
    T, r, sigma, N = settings.values()
    dt = T / N  # length of each period
    u = np.exp(sigma * np.sqrt(dt))
    d = np.exp(-sigma * np.sqrt(dt))
    p = (np.exp(r * dt) - d) / (u - d)  # risk-neutral probability of up move

    # Create the binomial tree for the stock price
    S = np.zeros((N + 1, N + 1))
    S[0, 0] = initial_price

    option_values = np.zeros((N + 1, N + 1))

    for i in range(1, N + 1):
        for j in range(i + 1):
            S[j, i] = S[0, 0] * (u ** (i - j)) * (d ** j)  # calculate the stock price at each node

    # Calculate option values at maturity
    for j in range(N + 1):
        if option_type == 'put':
            option_values[j, N] = max(0, strike_price - S[j, N])
        elif option_type == 'call':
            option_values[j, N] = max(0, S[j, N] - strike_price)

    # Backward induction to calculate option values at previous nodes
    # I'm ngl I used ChatGPT for this since it had to be dynamic programming for efficiency
    for i in range(N - 1, -1, -1):
        for j in range(i + 1):
            intrinsic_value = max(0, strike_price - S[j, i]) if option_type == 'put' else max(0, S[j, i] - strike_price)
            continuation_value = np.exp(-r * dt) * (
                    p * option_values[j, i + 1] + (1 - p) * option_values[j + 1, i + 1])
            option_values[j, i] = max(intrinsic_value, continuation_value)

    return option_values[0, 0]

#This implementation 
# 1. defaults to puts (get_option_price)
# 2. assumes strike_price = stock_price (get_option_price)
# 3. assumes 2 week maturity date (settings)
# 4. assumes neutral risk stock movement (by nature of the model)


def get_option_price(stock_price, option_type='put'):
    strike_price = stock_price
    result = binomial_tree_and_option_price(stock_price, strike_price, option_type)
    return result

