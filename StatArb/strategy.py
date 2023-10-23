from ecm import Pair
import pandas as pd

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