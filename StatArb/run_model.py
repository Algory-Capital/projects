import os
import adf
import time
from ecm import Pair, get_stop_loss_thresholds
from data_download import get_spy_data
import pandas as pd
import strategy
from collections import defaultdict

# from market_tester_copy import run_timeline,run_daily_instructions
import pandas_market_calendars as mcal
from datetime import datetime
import market_tester as market_tester
from market_tester import (
    pair_to_orders,
    run_timeline,
    portfolio_value,
    plot_all,
    positions,
    current_capital,
    orders_index,
)
from helper import (
    process_pair,
    slice_database_by_dates,
    get_market_valid_times,
    get_market_end_date,
)
from data_download import get_spy_data
from tqdm import tqdm


def run_model():
    settings = strategy.get_settings()

    # Linear list of trades made
    trades_made = []

    # Current positions organized by ticker
    positions = {}

    # Tracks days held, updates based on sales, and auto sells at certain date
    daytracker = defaultdict(list)
    HOLDING_PERIOD = settings["HOLDING_PERIOD"]

    current_capital = settings["INITIAL_CAPITAL"]

    day_number = 0

    start_time = time.time()
    start_date = "2018-06-12"
    end_date = "2022-01-03"

    get_spy_data(
        start_date=start_date, end_date=get_market_end_date(end_date=end_date)
    )  # We need to call market_end_date since yfinance doesn't download the last day
    # https://github.com/ranaroussi/yfinance/issues/1445

    root = "StatArb"
    csv_path = "spy.csv"
    market_tester.database = pd.read_csv(os.path.join(root, csv_path))
    market_tester.database_index = list(
        map(lambda x: x.split(" ")[0], market_tester.database["Date"].tolist())
    )
    market_tester.database["Date"] = market_tester.database_index
    market_tester.database.set_index("Date", inplace=True)

    market_tester.database = slice_database_by_dates(
        database=market_tester.database, start_date=start_date, end_date=end_date
    )

    root = "StatArb/ADF_Cointegrated"

    # print(root)

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

    # orders_index = database.index
    market_tester.orders_index = get_market_valid_times(
        len(pairs[0].instructions), start_date, end_date
    )
    print("Converting orders to pairs")
    for pair in tqdm(pairs):
        instructions = pair_to_orders(pair)  # populate orders dataframe

    market_tester.stop_loss_thresholds = get_stop_loss_thresholds()
    # print(stop_loss_thresholds)

    print("Finished converting orders to pairs")
    market_tester.orders.sort_index(inplace=True)
    run_timeline(
        market_tester.orders,
        market_tester.orders_index[0],
        market_tester.orders_index[-1],
    )
    print(market_tester.portfolio_history)

    print(f"Current Capital: {float(market_tester.current_capital):.2f}")
    print(f"Current Portfolio Value: {float(portfolio_value()):.2f}")
    print("Positions:", market_tester.positions)
    # print(f"Day tracker: ", daytracker)

    time_diff = time.time() - start_time

    print(
        f"Done. Took {time_diff:.2f} seconds. Average {time_diff/len(pairs):.2f} seconds per pair."
    )

    plot_all(market_tester.portfolio_history, start_date, end_date)

    return market_tester.current_capital


def optimize_model_parameters():
    pass


if __name__ == "__main__":
    run_model()
