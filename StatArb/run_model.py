import os
import adf
import time
from ecm import Pair, get_stop_loss_thresholds, get_model_settings
import ecm as ecm
from data_download import get_spy_data
import pandas as pd
import strategy
from collections import defaultdict
import csv
import random

# https://scikit-optimize.github.io/stable/auto_examples/sklearn-gridsearchcv-replacement.html#minimal-example
# https://www.freecodecamp.org/news/hyperparameter-optimization-techniques-machine-learning/
# from market_tester_copy import run_timeline,run_daily_instructions
import pandas_market_calendars as mcal
from datetime import datetime
from market_tester import (
    pair_to_orders,
    run_timeline,
    portfolio_value,
    plot_all,
    positions,
    current_capital,
    orders_index,
)
import market_tester as market_tester
from helper import (
    process_pair,
    slice_database_by_dates,
    get_market_valid_times,
    get_market_end_date,
)
from data_download import get_spy_data
from tqdm import tqdm

root = "StatArb"
csv_path = "backtest_history.csv"


def write_to_backtest_csv(config, result):
    config["RETURN"] = result

    with open(os.path.join(root, csv_path), "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=config.keys())
        writer.writerow(config)


def remove_duplicates_from_csv():
    df = pd.read_csv(os.path.join(root, csv_path))
    df.drop_duplicates(inplace=True)
    df.to_csv(os.path.join(root, csv_path), index=False)


# Optimization imports
from skopt import BayesSearchCV
from sklearn.base import BaseEstimator
from sklearn.metrics import make_scorer

# https://github.com/scikit-optimize/scikit-optimize/issues/1171

model_settings = {
    "HOLDING_PERIOD": 9,
    "PCT_SL_THRESHOLD": 44,  # percent stop loss threshold
    "PORTION_SIZE": 1455,  # dollar allocation to each trade
    "ENTER_Z": 6,
    "EXIT_Z": 2,
}


class Estimator(BaseEstimator):
    def __init__(self, config=model_settings):
        self.config = config

    def fit(self):
        return run_model(self.config)


param_space = {
    "HOLDING_PERIOD": (1, 30),
    "PCT_SL_THRESHOLD": (30, 100),  # percent stop loss threshold
    "PORTION_SIZE": (700, 1500),  # dollar allocation to each trade
    "ENTER_Z": (3, 10),
    "EXIT_Z": (1, 3),
}

training_parameters = []


def generate_training_parameters(num_iterations):
    parameter_bounds = list(param_space.values())
    for _ in tqdm(range(num_iterations)):
        current = []
        for bottom, high in parameter_bounds:
            current.append(random.randrange(bottom, high))
        training_parameters.append(current)


def maximize_returns(config):
    return run_model(config)


scorer = make_scorer(score_func=maximize_returns, greater_is_better=True)


def optimize_model_parameters():
    opt = BayesSearchCV(Estimator(), param_space, scoring=scorer, n_iter=50, n_jobs=1)
    opt.fit(X=[15, 100, 200, 5, 1], Y=110000)

    best_params = opt.best_params_
    ecm.model_settings.update(best_params)

    print("Best Parameters:", best_params)


def get_database(start_date, end_date, download=False):
    if download:
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
        market_tester.database, start_date=start_date, end_date=end_date
    )


def run_model(config=model_settings):
    settings = strategy.get_settings()
    ecm.model_settings = config
    print(ecm.model_settings)

    # Linear list of trades made
    trades_made = []

    # Current positions organized by ticker
    positions = {}

    # Tracks days held, updates based on sales, and auto sells at certain date
    daytracker = defaultdict(list)

    current_capital = settings["INITIAL_CAPITAL"]

    day_number = 0

    start_time = time.time()

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
    # print(market_tester.portfolio_history)

    print(f"Current Capital: {float(market_tester.current_capital):.2f}")
    print(f"Current Portfolio Value: {float(portfolio_value()):.2f}")
    print("Positions:", market_tester.positions)
    print(config)
    # print(f"Day tracker: ", daytracker)

    time_diff = time.time() - start_time

    print(
        f"Done. Took {time_diff:.2f} seconds. Average {time_diff/len(pairs):.2f} seconds per pair."
    )

    plot_all(market_tester.portfolio_history, start_date, end_date)
    score = portfolio_value()

    # Write to backtest CSV. This helps create training data for hyperparameter and review prior backtests
    write_to_backtest_csv(config, score)

    return portfolio_value()


def reset_market_tester_data():
    # Linear list of trades made
    market_tester.trades_made = []

    # Current positions organized by ticker
    market_tester.positions = {}

    # Tracks days held, updates based on sales, and auto sells at certain date
    market_tester.daytracker = defaultdict(list)

    market_tester.current_capital = market_tester.settings["INITIAL_CAPITAL"]

    market_tester.day_number = 0

    market_tester.orders_index = []
    market_tester.orders = pd.DataFrame()

    market_tester.portfolio_history = pd.Series()


if __name__ == "__main__":
    print("Starting")
    start_time = time.time()
    # optimize_model_parameters()
    start_date = "2018-06-12"
    end_date = "2022-01-03"
    get_database(start_date=start_date, end_date=end_date)

    # generate_training_parameters(15)

    if training_parameters:
        for i in tqdm(range(len(training_parameters))):
            for key, value in zip(model_settings.keys(), training_parameters[i]):
                model_settings[key] = value

            print(model_settings)
            run_model()
            reset_market_tester_data()
    else:
        run_model()

    remove_duplicates_from_csv()

    print(f"Done. Finished in {time.time()-start_time} seconds.")
