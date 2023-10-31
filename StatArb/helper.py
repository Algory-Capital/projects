from datetime import datetime
import pandas as pd
import pandas_market_calendars as mcal

def get_market_start_date(days_ago = 50,end_date = datetime.now(),return_type="str"):
    #assumes that each stock is listed on either NYSE or Nasdaq, which follow the same schedule
    nyse = mcal.get_calendar('NYSE')
    date = pd.to_datetime(end_date.strftime('%m/%d/%Y')) - pd.tseries.offsets.CustomBusinessDay(1, holidays = nyse.holidays().holidays)
    if return_type == "str":
        date = date.strftime('%Y-%m-%d')
        #"2002-01-01"
        # Format: year-month-day
    return date
