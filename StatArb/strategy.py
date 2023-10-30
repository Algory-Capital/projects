# Treat strategy as our main file
from ecm import Pair
import pandas as pd
import os
import adf
import time
#from market_tester_copy import run_timeline,run_daily_instructions
import pandas_market_calendars as mcal
from datetime import datetime

root = "StatArb"

def get_settings():
    
    settings = {
    "C_FLAT": 20,
    "C_PERCENT": 0.1,
    # "C_TYPE": "FLAT",
    # "C_TYPE": "PERCENT",
    "C_TYPE": "NONE",
    "INITIAL_CAPITAL": 100000
    }
    return settings

def calculate_daily_instructions(data: pd.DataFrame, pair: Pair):

    instructions = pair.instructions
    return instructions

def stock_info_to_instructions(data: pd.DataFrame):
    return calculate_daily_instructions(data)

def process_pair(pair)->Pair:
    """
    Does all the operations necessary for one pair
    @pair: Pair object
    """
    pair = Pair(pair[0],pair[1])

    pair.pair_main()

    return pair

if __name__ == "__main__":
    start_time = time.time()
    settings = get_settings()

    if not os.path.exists(os.path.join(root,"coint.csv")):
        adf.main(5)

    # Read to csv and convert to list. Iterating through DataFrame rows is considered an anti-pattern
    coint_pairs = pd.read_csv(os.path.join(root,"coint.csv")).to_list() 

    for pair_set in coint_pairs:
        process_pair(pair_set)

    print(f"Complete. Took {time.time()-start_time}")