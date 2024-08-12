import yfinance as yf
from datetime import datetime
from dateutil.parser import parse
from dateutil.rrule import rrule, DAILY, MO, TU, WE, TH, FR

# utilize spaghetti to generate stock market dates
class StockDates:
    def __init__(self, start_date = "2022-08-01", fmt = "%Y/%m/%d"):
        dates = yf.download("SPY", start_date).index
        #self.dates = StockDates.get_weekday_range(start_date = start_date)

        self.dates = list(dates.map(lambda x : datetime.strftime(x,fmt)).values)
        self.length = len(self.dates)

        print(self.dates)
        pass
    
    @staticmethod
    def get_weekday_range(start_date = '2022-08-01', end_date = datetime.now().strftime('%Y-%m-%d'), fmt = "%Y/%m/%d"):

        # generate iterable of datetime timestamps
        res = rrule(
        DAILY,
        byweekday=(MO,TU,WE,TH,FR),
        dtstart=parse(start_date),
        until=parse(end_date)
        )
        
        #res = list(res).map().values
        res = map(lambda x : datetime.strftime(x,fmt), res)
        return list(res)
