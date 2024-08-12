import bisect
from typing import List
from dates import StockDates

# where to put this search

sd = StockDates()

def index (x: str | float, a: List[str | float] = sd.dates) -> int:
    # input string from excel: MM/DD/YYYY
    # reformat to YYYY/MM/DD

    s = x.split("/") #split values
    x = f'{s[2]}/{s[0]}/{s[1]}'

    i = bisect.bisect_left(a, x)

    if i != len(a) and a[i] == x:
        return i

    print("WARNING: cannot find date: ", x)
    print(f"Cannot locate date: {x}. Last date in array: {a[-1]}. Length: {len(a)}. i: {i}.")
    return i + 1
    
    raise ValueError(f"Cannot Find date: {x}")