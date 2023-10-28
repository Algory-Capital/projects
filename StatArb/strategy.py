# Treat strategy as our main file
from ecm import Pair
import pandas as pd
import os
import adf
import time

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

def process_pair(pair):
    """
    Does all the operations necessary for one pair
    """
    pair = Pair(pair[0],pair[1])

    pair.pair_main()

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