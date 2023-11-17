from datetime import datetime, timedelta
import pandas as pd
import pandas_market_calendars as mcal
import pytz
from ecm import Pair
from collections import defaultdict
import numpy as np


def slice_database_by_dates(database, start_date, end_date):
    # print(database.index)
    start_index = np.where(database.index == start_date)[0][0]
    end_index = np.where(database.index == end_date)[0][0]

    database = database.iloc[start_index : end_index + 1]
    return database


def get_market_start_date(days_ago=50, end_date=datetime.now(), return_type="str"):
    # assumes that each stock is listed on either NYSE or Nasdaq, which follow the same schedule
    nyse = mcal.get_calendar("NYSE")
    date = pd.to_datetime(
        end_date.strftime("%Y-%m-%d")
    ) - pd.tseries.offsets.CustomBusinessDay(
        days_ago, holidays=nyse.holidays().holidays
    )
    if return_type == "str":
        date = date.strftime("%Y-%m-%d")
        # "2002-01-01"
        # Format: year-month-day
    return date


def get_market_end_date(end_date: str, change_days=1, return_type="str"):
    # assumes that each stock is listed on either NYSE or Nasdaq, which follow the same schedule
    nyse = mcal.get_calendar("NYSE")
    date = pd.to_datetime(end_date) + pd.tseries.offsets.CustomBusinessDay(
        change_days, holidays=nyse.holidays().holidays
    )
    if return_type == "str":
        date = date.strftime("%Y-%m-%d")
        # "2002-01-01"
        # Format: year-month-day
    return date


def get_market_valid_times(
    length=50, start_date: str = None, end_date=datetime.now()
) -> list[str]:  # start_date is sent as string
    if not start_date:
        date = get_market_start_date(length, end_date)
        print(f"No start date provided. Date set to {date}.")
    else:
        date = start_date

    date = pd.to_datetime(date)
    dates = []

    nyse = mcal.get_calendar("NYSE")
    # replaced this for optimization reasons
    # for _ in range(length):
    #     date = date + pd.tseries.offsets.CustomBusinessDay(
    #         1, holidays=nyse.holidays().holidays
    #     )
    #     new_date = date.strftime("%Y-%m-%d")
    #     dates.append(new_date)

    custom_bday = pd.tseries.offsets.CustomBusinessDay(
        1, holidays=nyse.holidays().holidays
    )
    dates = [
        date.strftime("%Y-%m-%d") for _ in range(length) if (date := date + custom_bday)
    ]

    return dates


def series_index_to_dates(
    series: pd.Series, start_date: str, end_date, index
) -> pd.Series:
    """
    Sets index for series to dates to prepare mergin

    @series: pd.Series
    @ start_date: '%Y-%m-%d'
    """
    # format = '%Y-%m-%d'
    # start_datetime = datetime.strptime(start_date,format)

    # print(len(series), start_date)

    if index:
        dates = index
    else:
        dates = get_market_valid_times(len(series), start_date, end_date)

    series.index = dates

    return series


def generate_instruction_lists(df: pd.DataFrame):
    return df.values.tolist()


def process_pair(pair, start_date, end_date) -> Pair:
    """
    Does all the operations necessary for one pair
    @pair: Pair object
    """
    pair = pair[0].split(", ")

    pair = Pair(pair[0], pair[1])

    pair.pair_main()

    pair.start_date = start_date
    pair.end_date = end_date

    return pair


"""
For stock in position:
    For quantity,day_bought in zip(daytracker[stock]):
        if day_bought-delta >= MAXPERIOD:
            sell

Selling from z-score

For stock in position:
    keep subtracting quantity and popleft until quantity = 0,
"""


def check_hold(
    daytracker: defaultdict(list), positions: dict, cur_day: int, MAXHOLD: int
) -> list[list]:  # we need to actually sell it
    """
    Sells when reaches a holding period MAXHOLD

    To-do: have market_tester act upon to sell
    """
    # We use day number rather than time.strptime datetime object because strptime and timedelta is slower
    # print(daytracker)
    to_sell = []  # stores instructions for stocks to sell
    for stock in positions.keys():
        stock_qty = 0
        for quantity, day_bought, price in daytracker[stock]:
            if cur_day - day_bought < MAXHOLD:
                break  # exit for-loop, generate order, then move to next stock

            stock_qty += quantity

        if stock_qty > 0:
            to_sell.append(["SELL", stock, stock_qty])

    return [to_sell]


def add_to_daytracker(
    daytracker: defaultdict(list), quantity: int, ticker: str, cur_day: int, price: int
):
    # print(daytracker, type(daytracker))
    daytracker[ticker].append([quantity, cur_day, price])
    return daytracker


def remove_from_daytracker(stock: str, quantity: int, daytracker: defaultdict(list)):
    """
    Called when a stock is sold from market_tester. Removes stocks from daytracker based on earliest date bought
    and quantity sold in instructions

    Need a different way to remove when stop-loss
    """
    # print(daytracker)
    # updates when stock is sold
    slice_idx = 0

    # decrease quantity as we take off stocks
    # stocks should already be in descending order in # days held
    for qty, day_bought, price in daytracker[stock]:
        if quantity == 0:
            break
        if qty <= quantity:
            quantity -= qty
            slice_idx += 1
        else:
            daytracker[stock] = [[qty - quantity][day_bought]].extend(
                daytracker[slice_idx + 1 :]
            )

    return daytracker


def remove_stop_loss_from_daytracker(
    stock: str, quantity: int, daytracker: defaultdict(list)
):
    """
    Approach:
    While quantity is > 0, remove items via np.argmax and update quantity.
    Return updated daytracker
    j = [[1,6,2],[1,5,8],[2,7,1]]
    j = np.array(j)[:,-1]
    """
    quantity_array = np.array(daytracker[stock][:, -1])
    while quantity > 0:
        stop_loss_index = np.argmax(quantity_array)
        quantity -= quantity_array[stop_loss_index]
        np.delete(quantity_array, stop_loss_index)
        daytracker[stock] = daytracker[stock].pop(stop_loss_index)
        # np.delete


def check_stop_loss(
    daytracker: defaultdict(list),
    positions: dict,
    database: pd.DataFrame,
    day_number: int,
    stddev,
    z_score=13,
):
    """
    Day_number is int not strftime string
    Be careful about duplicates. For now, am calling run_daily instructions and updating daytracker twice per day
    Daytracker item format: [qty,day_bought,price]

    We need to restructure to get spread (sigma in here). Or, we can store as a separate dataframe
    """
    # np.where?
    to_sell = []  # stores instructions for stocks to sell
    for col_num, stock in enumerate(positions.keys()):
        cur_price = database.iloc[day_number, col_num]
        sell_threshold = cur_price - z_score * stddev
        stock_qty = 0
        for quantity, day_bought, price in daytracker[stock]:
            # exceed = np.where(item[2]<sell_threshold,item)
            if price < sell_threshold:
                stock_qty += quantity
        to_sell.append(["SELL", stock, stock_qty])

    return [to_sell]


"""
def get_valid_times(start_time = datetime.now(),market_exchange='NYSE',length=None):
    
    times = []
    
    exchange = mcal.get_calendar(market_exchange)
    start_time = start_time - timedelta(hours=start_time.hour,minutes=start_time.minute,seconds=start_time.second,microseconds=start_time.microsecond) # round down to day
    if length:
        tmp_time = start_time
        #print(tmp_time)
        ONE_DAY = timedelta(days=1)
        while len(times) < length:
            next_time = tmp_time + ONE_DAY
            #print(type(next_time))
            if valid_market_time(next_time):
                times.append(next_time)
            else:
                next_time += ONE_DAY
        tmp_time = next_time
    return times

def valid_market_time(time:datetime,market_exchange='NYSE'): # helper function for get_valid_times
    tz_naive_to_aware(time)

    return time.weekday() not in [5,6] and 9*60+30 <= time.hour*60+time.minute <= 16*60 # 9:30AM to 4:00PM in NY time, will use pytz to automatically adjust

def tz_naive_to_aware(time, market_exchange = 'NYSE'):
    exchange = mcal.get_calendar(market_exchange)
    tz = pytz.timezone(mcal.get_calendar(market_exchange).tz.zone)
    if time.tzinfo is None or time.tzinfo.utcoffset(time) is None: # Convert tz-naive to tz-aware
        localized_time = pytz.utc.localize(time)
        #print("Localized")
        time = localized_time.astimezone(tz)

    return time
    """
