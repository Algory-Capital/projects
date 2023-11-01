from datetime import datetime,timedelta
import pandas as pd
import pandas_market_calendars as mcal
import pytz

def get_market_start_date(days_ago = 50,end_date = datetime.now(),return_type="str"):
    #assumes that each stock is listed on either NYSE or Nasdaq, which follow the same schedule
    nyse = mcal.get_calendar('NYSE')
    date = pd.to_datetime(end_date.strftime('%m/%d/%Y')) - pd.tseries.offsets.CustomBusinessDay(days_ago, holidays = nyse.holidays().holidays)
    if return_type == "str":
        date = date.strftime('%Y-%m-%d')
        #"2002-01-01"
        # Format: year-month-day
    return date

def get_market_valid_times(length = 50,end_date = datetime.now()):
    start = get_market_start_date(length,end_date)
    dates = []
    nyse = mcal.get_calendar('NYSE')
    for _ in range(length):
        date = date + pd.tseries.offsets.CustomBusinessDay(1, holidays = nyse.holidays().holidays)
        date = date.strftime('%Y-%m-%d')
        dates.append(date)
    
    return dates

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