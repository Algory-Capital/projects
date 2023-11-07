import time
import yfinance as yf
import csv
import datetime
from data_download import get_spy_data
import strategy as strategy
import adf
import pandas as pd
import os
from ecm import Pair
import matplotlib.pyplot as plt
from helper import series_index_to_dates, process_pair
import numpy as np
from tqdm import tqdm

# from helper import get_market_start_date

if not os.path.exists("spy.csv"):
    get_spy_data

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


def pair_to_orders(pair: Pair):
    """
    Gets pair instructions and merges them with database by index
    @pair: Pair object
    """

    """for i in range(len(pair.instructions)):
        instruction = pair.instructions[i]  #buy/sell, ticker, quantity
        #position,ticker,quantity = instruction

        #trade_instruction = Trade("",ticker,quantity,None,None,None)
        database.iloc[len(database.index)] = instruction"""
    global orders

    instructions = pd.Series(pair.instructions, name=pair.name)
    print(pair.start_date, pair.end_date)
    instructions = series_index_to_dates(instructions, pair.start_date, pair.end_date)

    orders = orders.merge(instructions, how="outer", left_index=True, right_index=True)
    print(orders)
    print(orders.index, type(orders.index[0]))


def calculate_commission(trade):
    if settings.get("C_TYPE") == "PERCENT":
        return trade.price * trade.quantity * settings["C_PERCENT"]
    elif settings.get("C_TYPE") == "FLAT":
        return settings["C_FLAT"]
    elif settings.get("C_TYPE") == "NONE":
        return 0
    else:
        raise TypeError("No valid commision")


# calculates value for positions TO NOW
def portfolio_value():
    total_value = current_capital
    for symbol, position in positions.items():
        stock = yf.Ticker(symbol)
        current_price = stock.history(period="1d")["Close"].iloc[-1]

        # Calculate the current value of the position
        position_value = position["quantity"] * current_price
        total_value += position_value
    return total_value


def buy_stock(symbol, quantity, price, timestamp):
    global current_capital  # Declare global to update the outer variable
    new_trade = Trade(
        len(trades_made),
        symbol=symbol,
        quantity=quantity,
        price=price,
        timestamp=timestamp,
        type="buy",
    )
    if current_capital >= (quantity * price + calculate_commission(new_trade)):
        trades_made.append(new_trade)

        # Calculate the total cost of the purchase, including commission
        total_cost = (quantity * price) + calculate_commission(new_trade)

        if symbol in positions:
            positions[symbol]["quantity"] += quantity
            positions[symbol]["avg_price"] = (
                positions[symbol]["avg_price"] * positions[symbol]["quantity"]
                + quantity * price
            ) / (positions[symbol]["quantity"] + quantity)
        else:
            positions[symbol] = {"quantity": quantity, "avg_price": price}

        current_capital -= total_cost
    else:
        print("Not enough capital to buy", quantity, "shares of", symbol)


def sell_stock(symbol, quantity, price, timestamp):
    new_trade = Trade(
        len(trades_made),
        symbol=symbol,
        quantity=quantity,
        price=price,
        timestamp=timestamp,
        type="sell",
    )
    global current_capital  # Declare global to update the outer variable

    if (
        new_trade.symbol in positions
        and positions[new_trade.symbol]["quantity"] >= quantity
    ):
        # Calculate the total revenue from the sale, after deducting commission
        total_revenue = (quantity * new_trade.price) - calculate_commission(new_trade)

        # Update position
        positions[new_trade.symbol]["quantity"] -= quantity

        # Check if all shares are sold for this position
        if positions[new_trade.symbol]["quantity"] == 0:
            del positions[new_trade.symbol]

        # Update current capital
        current_capital += total_revenue

    else:
        print("Not enough shares to sell or invalid trade.", new_trade)


# STRUCTURE SHOULD BE [[BUY, symbol, quantity], [SELL, symbol, quantity]]


def run_daily_instructions(current_day: str, instructions=list[list]):
    print(instructions, type(instructions))
    # Name: 2018-06-20, dtype: object [list([None, 'ADI', 10]) list([None, 'AJG', 10])] <class 'numpy.ndarray'> Index(['A ADI', 'A AJG'], dtype='object') <class 'str'> A AJG

    # [list([None, 'ADI', 10]) list([None, 'AJG', 10])] <class 'numpy.ndarray'>
    for instruction in instructions:
        for order in instruction:
            order_type = order[0]
            symbol = order[1]
            quantity = order[2]

            print("CURRENT DATE", current_day, type(current_day))

            # current_date_str = current_day.strftime("%Y-%m-%d %H:%M:%S")

            print(database.loc[current_day][symbol])
            price = float(database.loc[current_day][symbol])

            if order_type == "BUY":
                buy_stock(symbol, quantity, price, current_day)
            elif order_type == "SELL":
                sell_stock(symbol, quantity, price, current_day)
            else:
                print(f"Invalid order{order}")
                return

            print(order_type, symbol, current_day, price)

            print(f"{order_type: <4} {symbol: <4} on {current_day}: {float(price):.2f}")


def run_timeline(orders: pd.DataFrame, start_date, end_date):
    """
    Runs all instructions from a dataframe
    """
    format = "%Y-%m-%d"
    start_date = datetime.datetime.strptime(start_date, format)
    end_date = datetime.datetime.strptime(end_date, format)

    # Set the 'Date' column as the index
    # database.set_index("Date", inplace=True)
    # database.sort_index(inplace=True)

    for current_date in orders.index:  # fix
        # Check if the date exists in the index
        # try:
        data_rows = orders.loc[current_date]
        instructions = data_rows
        print(
            instructions,
            instructions.values,
            type(instructions.values),
            instructions.index,
            type(instructions.index[0]),
            instructions.index[-1],
        )

        run_daily_instructions(current_date, instructions.values)
        print(current_date)
        """except Exception as e:
            print(f"No data available for {current_date}, Error: {e}")
            print(current_date, current_date, orders.loc[current_date])
            input()"""

    return None


def plot_all(df: pd.DataFrame):
    fig = plt.figure()
    ax = fig.gca()
    df.index = df.index.map(lambda time: time.strftime("%Y-%m-%d"))
    pass


# does not account for stock splits
# database currently contains stocks from current s&p 500, if stocks leave/rejoin it gets weird
if __name__ == "__main__":
    start_date = "2018-06-12"
    end_date = "2022-01-01"
    """
    # database_csv = data_download.download_stock_data(start_date= start_date, end_date= end_date)
    database_csv = f"s&p500 {start_date} to {end_date}.csv"

    database = pd.read_csv(database_csv)
    database['Date'] = pd.to_datetime(database['Date'])


    run_timeline(database, start_date, end_date)"""

    root = "StatArb"
    csv_path = "spy.csv"
    database = pd.read_csv(os.path.join(root, csv_path))
    database_index = list(map(lambda x: x.split(" ")[0], database["Date"].tolist()))
    database["Date"] = database_index
    database.set_index("Date", inplace=True)

    print(database, database.index, type(database.index[0]))
    # database.sort_index(inplace=True)

    orders = pd.DataFrame()
    root = "StatArb/ADF_Cointegrated"

    print(root)

    if not os.path.exists(os.path.join(root, "coint.csv")):
        print("Coint csv not found, calling adf main. Input to continue")
        input()
        adf.main(50)
        time.sleep(5)
        assert os.path.exists(os.path.join(root, "coint.csv"))

    # Read to csv and convert to list. Iterating through DataFrame rows is considered an anti-pattern
    coint_pairs = pd.read_csv(os.path.join(root, "coint.csv")).values.tolist()

    pairs = []  # contains the Pair objects

    for pair_set in tqdm(coint_pairs):
        pairs.append(process_pair(pair_set, start_date, end_date))

    for pair in tqdm(pairs):
        instructions = pair_to_orders(pair)  # populate orders dataframe

    orders.sort_index(inplace=True)
    print(orders)
    orders.to_csv("orders.csv", index=True)
    database.to_csv("database.csv", index=True)
    orders_index = orders.index
    print(orders_index[-1], type(orders_index[-1]))
    run_timeline(orders, orders_index[0], orders_index[-1])

    print(f"Current Capital: {float(current_capital):.2f}")
    print(f"Current Portfolio Value: {float(portfolio_value()):.2f}")
    print("Positions:", positions)
