import os
import pandas as pd
from statsmodels.tsa.stattools import adfuller
import matplotlib.pyplot as plt
import time
from tqdm import tqdm
import threading
import concurrent.futures
import statsmodels.api as sm
import pandas as pd

# from HistoricalData import get_spy_data

lock = threading.Lock()

###
# Config

dest_coint = "ADF_Cointegrated"
dest_not_coint = "ADF_Diff"
csv_path = "spy.csv"
max_processes = 24
adf_percentage = "1%"
###

start_time = time.time()
root = "StatArb"

if not os.path.exists("spy.csv"):
    # get_spy_data()
    pass

spy = pd.read_csv(os.path.join(root, csv_path))
spy.dropna(how="any", axis=1)

tickers = [i for i in spy.columns]
tickers.pop(0)  # pop column name for index

# print(tickers)

if not os.path.exists(dest_coint):
    os.mkdir(dest_coint)


def regress_two(t1: str, t2: str):  # regress t1 on t2 to get cointegration vector
    Y = spy[t1]
    X = spy[t2]

    Y.to_list()
    X.to_list()

    X = sm.add_constant(X)
    model = sm.OLS(Y, X)
    results = model.fit()

    # print(results.summary())

    # print(f'Results.params: {results.params.to_list()}')

    return results.params.to_list()[1]


# if not os.path.exists(dest_not_coint):
#    os.mkdir(dest_not_coint)


# Dickey Fuller and ADF can only be done on a snigle time series. It is referred to as a test of stationarity for this reason
# If we merge two time series, then if the test for stationary rejects null hypothesis (residual is stationary), then cointegration is proven
def compare_two(t1: str, t2: str):
    # with lock:
    df1 = spy[t1]  # returns series, not dataframe
    df2 = spy[t2]

    # need to run separate adf tests on each time series
    # need to test first differences being stationary
    # create ECM
    try:
        combined = pd.merge(df1, df2, how="inner", left_index=True, right_index=True)

        beta = regress_two(t1, t2)  # regress t1 on t2

        combined[t2].apply(lambda x: x * beta)  # create linear combination
        combined = combined[t1] - combined[t2]  # get residuals

        # Stationarity: Yt - \beta * Xt = I(0)

        # plt.plot(combined)
        result = adfuller(combined)

        # print(result)
        # input()

        print(f"ADF Statistic: {result[0]:.2f}")
        print(f"p-value: {result[1]:.2f}")
        print("Critical Values:")
        for key, value in result[4].items():
            print(f"\t{key}: {value:.2f}")

        print(f"Tickers {t1}, {t2}")

        # filename = f"ADF_{t1}_{t2}.png"

        # pbar.update()
        if result[0] < result[4][adf_percentage]:
            print("Reject H0 - Time Series is Stationary")
            return f"{t1}, {t2}"
            # plt.savefig(os.path.join(dest_coint,filename))
        else:
            print("Failed to Reject H0 - Time Series is Non-Stationary")
            # plt.savefig(os.path.join(dest_not_coint,filename))
            return "Not cointegrated"

        # plt.clf()
        """
        plt.show()                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
        time.sleep(5)
        plt.close()
        """

    except Exception as e:
        print(e)


# compare_two,tickers[0],tickers[1]


def main(bound=len(tickers)):
    results, coint = [], []
    total_operations = sum(i for i in range(bound))
    print(total_operations)

    pbar_results = tqdm(total=total_operations)

    with concurrent.futures.ProcessPoolExecutor(max_processes) as executor:
        for i in range(bound):
            for j in range(i + 1, bound):
                results.append(executor.submit(compare_two, tickers[i], tickers[j]))

        for f in concurrent.futures.as_completed(results):
            print(f"RESULT: {f.result()}")
            if f.result() != "Not cointegrated":
                coint.append(f.result())
            pbar_results.update()

    data = pd.DataFrame(coint)
    print(data)
    data.dropna(axis=0, inplace=True)
    print(data)
    data.to_csv(os.path.join(root, dest_coint, "coint.csv"), index=False)

    print(f"Completed program. Took {time.time()-start_time} seconds.")


if __name__ == "__main__":
    main()
