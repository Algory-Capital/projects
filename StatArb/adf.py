import os
import pandas as pd
from statsmodels.tsa.stattools import adfuller
import matplotlib.pyplot as plt
import time
from tqdm import tqdm
import threading
import concurrent.futures
import statsmodels.api as sm
from data_download import get_spy_data
import sys
import argparse

# Gave up on multiprocessing although it's faster in this case due to pickling serialization error.

lock = threading.Lock()
###
# Config

# Multiprocessing run (failed to properly serialize/save data): 2906 seconds
# Threading run: Took 7359.261744976044 seconds

root = "StatArb"

dest_coint = os.path.join(root,"ADF_Cointegrated")
dest_not_coint = os.path.join(root,"ADF_Diff")
csv_path = os.path.join(root,"spy.csv")
max_processes = 18
adf_percentage = "5%"
###

start_time = time.time()

if not os.path.exists(csv_path):
    get_spy_data()
    pass

spy = pd.read_csv(csv_path)
spy.dropna(how="any",axis=1,inplace=True)

#print(spy)

tickers = [i for i in spy.columns]
tickers.pop(0) #pop column name for index

#print(tickers)

if not os.path.exists(dest_coint):
    os.mkdir(dest_coint)

def regress_two(t1: str,t2: str): # regress t1 on t2 to get cointegration vector
    Y = spy[t1]
    X = spy[t2]

    Y.to_list()
    X.to_list()

    X = sm.add_constant(X)
    model = sm.OLS(Y,X)
    results = model.fit()

    #print(results.summary())

    #print(f'Results.params: {results.params.to_list()}')

    return results.params.to_list()[1]


#if not os.path.exists(dest_not_coint):
#    os.mkdir(dest_not_coint)

# Dickey Fuller and ADF can only be done on a snigle time series. It is referred to as a test of stationarity for this reason
# If we merge two time series, then if the test for stationary rejects null hypothesis (residual is stationary), then cointegration is proven
def compare_two(t1: str,t2: str,pbar):
    with lock:

        df1 = spy[t1] #returns series, not dataframe
        df2 = spy[t2]
        res = []

        # need to run separate adf tests on each time series
        # need to test first differences being stationary
        # create ECM
        try:
            combined = pd.merge(df1,df2,how="inner",left_index=True,right_index=True)

            beta = regress_two(t1,t2) # regress t1 on t2
       
            combined[t2].apply(lambda x:x *beta) #create linear combination
            combined = combined[t1] - combined[t2] #get residuals

            # Stationarity: Yt - \beta * Xt = I(0)

            #plt.plot(combined)
            result = adfuller(combined)

            #print(result)
            #input()
            '''
            print(f'ADF Statistic: {result[0]:.2f}')
            print(f'p-value: {result[1]:.2f}')
            print('Critical Values:')
            '''
            for key,value in result[4].items():
                print(f'\t{key}: {value:.2f}')
       
            print(f'Tickers {t1}, {t2}')

            filename = f"ADF_{t1}_{t2}.png"

            if result[0] < result[4][adf_percentage]:
                print("Reject H0 - Time Series is Stationary")
                res.append([t1,t2])
                #plt.savefig(os.path.join(dest_coint,filename))
            else:
                print("Failed to Reject H0 - Time Series is Non-Stationary")
                #plt.savefig(os.path.join(dest_not_coint,filename))

            pbar.update()
            return res
            #plt.clf()
            '''
            plt.show()                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
            time.sleep(5)
            plt.close()
            '''

        except Exception as e:
            print(e)

    #compare_two,tickers[0],tickers[1]

def main(bound:int = len(tickers)):
    """
    @param bound: Number of stocks to look at
    @type bound: int

    Function brute forces ADF test on stocks from S&P500 for cointegration
    """
    coint = []
    total_operations = sum(i for i in range(len(tickers)))
   
    with concurrent.futures.ThreadPoolExecutor(max_processes) as executor:
        with tqdm(total=total_operations) as pbar:
            futures = []
            for i in range(bound):
                for j in range(i+1,bound):
                    futures.append(executor.submit(compare_two,tickers[i],tickers[j],pbar))
                    #executor.submit is faster than map because it doesn't require processes to be completed in the same order they are sent.
                    #If we want correct order we use map
           
            print(futures)
            for res in concurrent.futures.as_completed(futures):
                #future = futures[res]
                try:
                    data = res.result()
                    print(data)
                    if data != []:
                        coint.append(data)
                except Exception as exc:
                    print(f'Request generated an exception: {exc}')
                   
                    #thread = threading.Thread(target=compare_two, args=(tickers[i],tickers[j]))
                    #thread.start()
                    #compare_two(tickers[i],tickers[j])
                    pbar.update()

    data = pd.DataFrame(coint)
   
    print(data,coint)
    print(f"coint: ", coint,type(coint))
    data.to_csv(os.path.join(dest_coint,"coint.csv"))



    print(f"Completed program. Took {time.time()-start_time} seconds.")

if __name__ == "__main__":
    main()