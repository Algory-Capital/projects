# Treat strategy as our main file
from ecm import Pair
import pandas as pd
import os
import adf
import time
#from market_tester_copy import run_timeline,run_daily_instructions
import pandas_market_calendars as mcal
from datetime import datetime
"""
from market_tester import pair_to_orders, run_timeline, portfolio_value
from helper import process_pair, slice_database_by_dates,get_market_valid_times
from data_download import get_spy_data
from tqdm import tqdm
from collections import defaultdict
"""

root = "StatArb"

def get_settings():
    
    settings = {
    "C_FLAT": 20,
    "C_PERCENT": 0.1,
    # "C_TYPE": "FLAT",
    # "C_TYPE": "PERCENT",
    "C_TYPE": "NONE",
    "INITIAL_CAPITAL": 100000,
    "HOLDING_PERIOD":15
    }
    return settings

def calculate_daily_instructions(data: pd.DataFrame, pair: Pair):

    instructions = pair.instructions
    return instructions

def stock_info_to_instructions(data: pd.DataFrame):
    return calculate_daily_instructions(data)
"""
if __name__ == "__main__":
    start_time = time.time()
    start_date = "2018-06-12"
    end_date = "2022-01-01"
    settings = get_settings()

    trades_made = []

    # Current positions organized by ticker
    positions = {}

    # Tracks days held, updates based on sales, and auto sells at certain date
    daytracker = defaultdict(list)
    HOLDING_PERIOD = settings["HOLDING_PERIOD"]

    current_capital = settings["INITIAL_CAPITAL"]

    day_number = 0

    get_spy_data(start_date=start_date,end_date=end_date)

    root = "StatArb"
    csv_path = "spy.csv"
    database = pd.read_csv(os.path.join(root, csv_path))
    database_index = list(map(lambda x: x.split(" ")[0], database["Date"].tolist()))
    database["Date"] = database_index
    database.set_index("Date", inplace=True)

    databse = slice_database_by_dates(database=database,start_date=start_date,end_date=end_date)

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

    orders_index = get_market_valid_times(start_date,end_date)
    print("Converting orders to pairs")
    for pair in tqdm(pairs):
        instructions = pair_to_orders(pair)  # populate orders dataframe

    print("Finished converting orders to pairs")
    orders.sort_index(inplace=True)
    print(orders)
    # orders.to_csv("orders.csv", index=True)
    # database.to_csv("database.csv", index=True)
    #orders_index = orders.index
    #print(orders_index[-1], type(orders_index[-1]))
    print(daytracker, type(daytracker))
    run_timeline(orders, orders_index[0], orders_index[-1])

    print(f"Current Capital: {float(current_capital):.2f}")
    print(f"Current Portfolio Value: {float(portfolio_value()):.2f}")
    print("Positions:", positions)
    # print(f"Day tracker: ", daytracker)

    time_diff = time.time() - start_time

    print(
        f"Done. Took {time_diff} seconds. Average {time_diff/len(pairs)} seconds per pair."
    )


    print(f"Complete. Took {time.time()-start_time}")

"""