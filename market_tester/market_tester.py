import time
import yfinance as yf
import csv
import datetime
import data_download
import strategy as strategy
import pandas as pd

settings = strategy.get_settings()

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
    
#calculates value for positions TO NOW
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
        
        current_capital -= total_cost

    else:
        print("Not enough capital to buy", quantity, "shares of", symbol)

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

#STRUCTURE SHOULD BE [[BUY, symbol, quantity], [SELL, symbol, quantity]]

def run_daily_instructions(current_day, instructions = list[list]):
    for order in instructions:
        order_type = order[0]
        symbol = order[1]
        quantity = order[2]

        print("CURRENT DATE", current_day)
        
        # current_date_str = current_day.strftime("%Y-%m-%d %H:%M:%S")


        price = float(database.loc[current_day][symbol])

        if order_type == 'BUY':
            buy_stock(symbol, quantity, price, current_day)
        elif order_type == 'SELL':
            sell_stock(symbol, quantity, price, current_day)
        else:
            print(f'Invalid order{order}')

        print(f"{order_type: <4} {symbol: <4} on {current_day}: {float(price):.2f}")


def run_timeline(database, start_date, end_date):
    format = "%Y-%m-%d"
    start_date = datetime.datetime.strptime(start_date, format)
    end_date = datetime.datetime.strptime(end_date, format)

    # Set the 'Date' column as the index
    database.set_index("Date", inplace=True)

    for current_date in pd.date_range(start=start_date, end=end_date):
        # Check if the date exists in the index
        if current_date in database.index:
            data_rows = database.loc[current_date]
            instructions = strategy.stock_info_to_instructions(data_rows)
            run_daily_instructions(current_date, instructions)
            print(current_date)
        else:
            print(f"No data available for {current_date}")

    return None

#does not account for stock splits
#database currently contains stocks from current s&p 500, if stocks leave/rejoin it gets weird
if __name__ == '__main__':
    start_date = "2002-01-01"
    end_date = "2022-01-01"
    # database_csv = data_download.download_stock_data(start_date= start_date, end_date= end_date)
    database_csv = f"s&p500 {start_date} to {end_date}.csv"
    
    database = pd.read_csv(database_csv)
    database['Date'] = pd.to_datetime(database['Date'])


    run_timeline(database, start_date, end_date)
    
    print(f"Current Capital: {float(current_capital):.2f}")
    print(f"Current Portfolio Value: {float(portfolio_value()):.2f}")
    print("Positions:", positions)
