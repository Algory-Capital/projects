import time
import yfinance as yf

settings = {
    "C_FLAT": 20,
    "C_PERCENT": 0.1,
    "C_TYPE": "FLAT",
    # "C_TYPE": "PERCENT",
    # "C_TYPE": "NONE",
    "INITIAL_CAPITAL": 100000
}

# Linear list of trades made
trades_made = []

# Current positions organized by ticker
positions = {}

current_capital = settings["INITIAL_CAPITAL"]

class Trade:
    def __init__(self, trade_id, symbol, quantity, price, timestamp, type):
        self.trade_id = trade_id
        self.symbol = symbol
        self.quantity = quantity
        self.price = price
        self.timestamp = timestamp
        self.type = type

def calculate_commission(trade):
    if settings.get("C_TYPE") == "PERCENT":
        return trade.price * trade.quantity * settings["C_PERCENT"]
    elif settings.get("C_TYPE") == "FLAT":
        return settings["C_FLAT"]
    elif settings.get("C_TYPE") == "NONE":
        return 0
    else:
        raise TypeError("No valid commision")
    
def portfolio_value():
    total_value = current_capital
    for symbol, position in positions.items():
        stock = yf.Ticker(symbol)
        current_price = stock.history(period="1d")["Close"].iloc[-1]
        
        # Calculate the current value of the position
        position_value = position['quantity'] * current_price
        total_value += position_value
    return total_value


def buy_stock(symbol, quantity, price, timestamp):
    global current_capital  # Declare global to update the outer variable
    new_trade = Trade(len(trades_made), symbol=symbol, quantity=quantity, price=price, timestamp=timestamp, type="buy")
    if current_capital >= (quantity * price + calculate_commission(new_trade)):
        trades_made.append(new_trade)

        # Calculate the total cost of the purchase, including commission
        total_cost = (quantity * price) + calculate_commission(new_trade)
        
        if symbol in positions:
            positions[symbol]['quantity'] += quantity
            positions[symbol]['avg_price'] = (positions[symbol]['avg_price'] * positions[symbol]['quantity'] + quantity * price) / (positions[symbol]['quantity'] + quantity)
        else:
            positions[symbol] = {'quantity': quantity, 'avg_price': price}
        
        # Update current capital
        current_capital -= total_cost

    else:
        print("Not enough capital to buy", quantity, "shares of", symbol)
    print("BUY:  %d %s AT %d" % (quantity, symbol, price))

def sell_stock(symbol, quantity, price, timestamp):
    new_trade = Trade(len(trades_made), symbol=symbol, quantity=quantity, price=price, timestamp=timestamp, type="sell")
    global current_capital  # Declare global to update the outer variable

    if new_trade.symbol in positions and positions[new_trade.symbol]['quantity'] >= quantity:
        
        # Calculate the total revenue from the sale, after deducting commission
        total_revenue = (quantity * new_trade.price) - calculate_commission(new_trade)
        
        # Update position
        positions[new_trade.symbol]['quantity'] -= quantity
        
        # Check if all shares are sold for this position
        if positions[new_trade.symbol]['quantity'] == 0:
            del positions[new_trade.symbol]
        
        # Update current capital
        current_capital += total_revenue
 
    else:
        print("Not enough shares to sell or invalid trade.", new_trade)
    print("SELL: %d %s AT %d" % (quantity, new_trade.symbol, new_trade.price))



# Example usage
if __name__ == '__main__':
    buy_stock('AAPL', 10, 150, time.time())
    buy_stock('MSFT', 10, 300, time.time())
    sell_stock('AAPL', 5, 150, time.time())
    print("Current Capital:", current_capital)
    print("Current Portfolio Value:", portfolio_value())
    print("Positions:", positions)
