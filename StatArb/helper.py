from datetime import datetime, timedelta
import pandas as pd
import pandas_market_calendars as mcal
import pytz
from ecm import Pair
from collections import defaultdict

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
    for _ in range(length):
        date = date + pd.tseries.offsets.CustomBusinessDay(
            1, holidays=nyse.holidays().holidays
        )
        new_date = date.strftime("%Y-%m-%d")
        dates.append(new_date)

    return dates


def series_index_to_dates(series: pd.Series, start_date: str, end_date) -> pd.Series:
    """
    Sets index for series to dates to prepare mergin

    @series: pd.Series
    @ start_date: '%Y-%m-%d'
    """
    # format = '%Y-%m-%d'
    # start_datetime = datetime.strptime(start_date,format)

    print(len(series), start_date)

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
    For quantity,day_bought in zip(day_tracker[stock]):
        if day_bought-delta >= MAXPERIOD:
            sell

Selling from z-score

For stock in position:
    keep subtracting quantity and popleft until quantity = 0,
"""


def check_hold(day_tracker: defaultdict(list), positions: dict, cur_day:int, MAXHOLD:int):
    # We use day number rather than time.strptime datetime object because strptime and timedelta is slower
    for stock in positions.keys():
        slice_idx = 0
        for quantity, day_bought in day_tracker[stock]:
            if cur_day - day_bought > MAXHOLD:
                break  # exit for-loop, slice list, then go to next stock

            slice_idx += 1

        if slice_idx >= len(day_tracker[stock]):
            del day_tracker[stock]

        else:
            day_tracker[stock] = day_tracker[stock][slice_idx:]


def add_to_daytracker(daytracker: defaultdict(list), quantity: int, ticker: str, cur_day:int):
    daytracker[ticker].append([quantity, cur_day])


def remove_from_daytracker(stock: str, quantity:int, day_tracker: defaultdict(list)):
    # updates when stock is sold
    slice_idx = 0
    while quantity > 0:
        # decrease quantity as we take off stocks
        # stocks should already be in descending order in # days held
        for qty, day_bought in zip(day_tracker[stock]):
            if qty <= quantity:
                quantity -= qty
                slice_idx += 1
            else:
                day_tracker[stock] = [[qty - quantity][day_bought]].extend(day_tracker[slice_idx+1:])

def get_buy_size(dollars,price,partial = False):
    if partial:
        return price/dollars
    else:
        return price//dollars

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
