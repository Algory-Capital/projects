
import pandas as pd

#STRUCTURE SHOULD BE [[BUY, symbol, quantity, timestamp], [SELL, symbol, quantity, timestamp]]
#timestamp currently in Y-M-D 00:00:00 time system


def calculate_daily_instructions(data: pd.DataFrame):

     
    instructions = [['BUY', 'AAPL', 20], ['BUY', 'ABT', 10], ['SELL', 'AAPL', 20], ['SELL', 'ABT', 10]]
    return instructions

def stock_info_to_instructions(data: pd.DataFrame):
    return calculate_daily_instructions(data)


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