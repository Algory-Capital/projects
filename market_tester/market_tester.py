settings = {
    "COMMISSION": 20,
    "COMMISSION_percent": 0.1,
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

def buy_stock(symbol, quantity, price, timestamp):
    global current_capital  # Declare global to update the outer variable
    if current_capital >= (quantity * price + settings["COMMISSION"]):
        new_trade = Trade(len(trades_made), symbol=symbol, quantity=quantity, price=price, timestamp=timestamp, type="buy")
        trades_made.append(new_trade)

        # Calculate the total cost of the purchase, including commission
        total_cost = (quantity * price) + settings["COMMISSION"]
        
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

def sell_stock(trade: Trade, quantity):
    global current_capital  # Declare global to update the outer variable
    if trade.symbol in positions and positions[trade.symbol]['quantity'] >= quantity:
        trade.type = "sell"
        trades_made.append(trade)
        
        # Calculate the total revenue from the sale, after deducting commission
        total_revenue = (quantity * trade.price) - settings["COMMISSION"]
        
        # Update position
        positions[trade.symbol]['quantity'] -= quantity
        
        # Check if all shares are sold for this position
        if positions[trade.symbol]['quantity'] == 0:
            del positions[trade.symbol]
        
        # Update current capital
        current_capital += total_revenue
    else:
        print("Not enough shares to sell or invalid trade.", trade)
    print("SOLD: %d %s AT %d" % (quantity, trade.symbol, trade.price))


# Example usage
if __name__ == '__main__':
    buy_stock('AAPL', 10, 150.0, '2023-10-07')
    sell_stock(trades_made[0], 5)
    print("Current Capital:", current_capital)
    print("Positions:", positions)
