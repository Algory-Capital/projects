# Treat strategy as our main file
from ecm import Pair
import pandas as pd

root = "StatArb"


def get_settings():
    settings = {
        "C_FLAT": 20,
        "C_PERCENT": 0.1,
        # "C_TYPE": "FLAT",
        # "C_TYPE": "PERCENT",
        "C_TYPE": "NONE",
        "INITIAL_CAPITAL": 100000,
    }
    return settings


def get_adjustable_settings():
    settings = {
        "HOLDING_PERIOD": 15,
        "PCT_SL_THRESHOLD": 50,
        "PORTION_SIZE": 300,
        "ENTER_Z": 5,
        "EXIT_Z": 1,
    }
    return settings


def calculate_daily_instructions(data: pd.DataFrame, pair: Pair):
    instructions = pair.instructions
    return instructions


def stock_info_to_instructions(data: pd.DataFrame):
    return calculate_daily_instructions(data)
