# Autoregressive distributed lag model
# Took a portion of my implementation from here: https://github.com/jkclem/ECM-in-python/blob/master/ECMs.ipynb

# Y_t=a_0+a_1 Y_(t−1)+γ_0 X_t+γ_1 X_(t−1)+u_t

import pandas as pd
import statsmodels.api as sm
import warnings
from data_download import get_spy_data
warnings.filterwarnings('ignore')
import os
from math import log
import numpy as np

if not os.path.exists("spy.csv"):
    get_spy_data()

spy = pd.read_csv("spy.csv")
predictors = ["X","const",'disequilibrium']
gammas = set()
alphas = set()
data_train = pd.DataFrame()
data = pd.DataFrame()

class Pair:
    def __init__(self,t1,t2,m=3,n=3,train_length = 50):
        self.train_length = train_length

        self.stock1 = t1 #independent, X
        self.stock2 = t2 #dependent, Y
        self.m = m
        self.n = n

        self.predictors = ["X","const",'disequilbrium']
        self.gammas = set()
        self.alphas = set()
        self.data_train = pd.DataFrame()
        self.data = pd.DataFrame()
        self.close = pd.Series()

        self.history = pd.DataFrame()
        self.diff_history = pd.DataFrame()
        self.diff_train= pd.DataFrame()
        self.diff_test = pd.DataFrame()

        self.instructions = []
        self.z_scores = []
        self.spreads = []

        self.get_data(t1,t2,5,5)
        
    def get_data(self,t1,t2,m,n):
        series_X = spy[t1]
        series_X.name = "X"

        close = spy[t2] #series_Y
        close.name = "close"

        self.data[series_X.name] = series_X

        for lag_order in range(1,m+1):
            new_col= 'gamma_' + str(lag_order)
            self.data[new_col] = close.shift(lag_order)
            self.predictors.append(new_col)
            self.gammas.add(new_col)
        
        for lag_order in range(1,n+1):
            new_col= 'a_' + str(lag_order)
            self.data[new_col] = close.shift(lag_order)
            self.predictors.append(new_col)
            self.alphas.add(new_col)

        #print(data)
        

        self.data[close.name] = close
        self.data.dropna(inplace=True)

        self.data['disequilibrium'] = self.get_disequilibrium()
        self.data_train = self.data[:-self.train_length].reset_index(drop=True)
        self.data_test = self.data[-self.train_length:].reset_index(drop=True)

        print(self.data)
        print(self.data_train)
        print(len(self.data_test))

        # diff everything
        self.diff_data = self.data.diff().dropna().reset_index(drop=True)
        self.close = self.close.diff().dropna().reset_index(drop=True)

        self.diff_train = self.diff_data[:-self.train_length].reset_index(drop=True)
        print(self.diff_train,self.diff_data)
        self.diff_test = self.data[-self.train_length:].reset_index(drop=True) #all(1) for columns

        #close = close.reset_index(drop=True)


    def get_disequilibrium(self):
        self.data = sm.add_constant(self.data)
        # linear regression on closing share price on the lagged closing market level
        # this is for short-term correction term e^_t-1

        lr_model = sm.OLS(self.data['close'], self.data[['const','X']]) # X_(t-1)
        lr_model_fit = lr_model.fit(cov_type='HC0') # hetroskedasticity-robust standard errors. Assumes errors are not constant.

        print(lr_model_fit.summary())
        
        print(lr_model_fit.params.keys())
        #const (beta_0), X (beta_1)
        self.data['disequilibrium'] = lr_model_fit.resid
        print(self.data['disequilibrium'])
        return lr_model_fit.resid #error term

    def get_error_correction_coefficient(self,params): #pi
        # 1-sum(i for i in a[i])
        self.err_cor_coeff = 1 - sum(params[i] for i in alphas)
        return -self.err_cor_coeff

    def create_ecm(self):
        #self.get_data(spy.columns[1],spy.columns[2],3,3)

        #run training data

        self.data_train = sm.add_constant(self.data_train)

        self.data_train = self.data_train.reset_index(drop=True)

        print(self.data_train,self.data_train.head(0),predictors)
        
        model = sm.OLS(self.data_train["close"],self.data_train[predictors]).fit()

        print(model.summary())

        print(model.params)
        return

        #err_cor_coeff = get_error_correction_coefficient(model.param())


        # add all of terms for sigma by using list comprehension + append
        #fitted model.predict()

    def roll_forecast_ecm(self,lr_train,lr_test,diff_train,diff_test,y_var='close',X_vars=predictors,lr_X_vars=['close','const'],data_train=data_train,):
        #y_var,X_vars,lr_train,lr_test,diff_train,diff_test

        lr_train.dropna(inplace=True)
        #dataframes that track past history
        self.history = lr_train
        self.diff_history = diff_train.dropna()
        print(self.diff_history)

        # linear model to predict long-run relationship
        print(self.history)
        lr_model_train = sm.OLS(self.history[[y_var]],self.history[lr_X_vars])
        # fits lr model
        lr_model_train_fit = lr_model_train.fit(cov_type='HC0')
        # add disequilibrium column for training period
        self.diff_train['disequilibrium'] = lr_model_train_fit.resid.shift(1)

        # creates an empty list that will hold the residuals for the next period
        self.disequilibrium = []

        # loops through the indexes of the set being forecasted
        print(len(lr_test))
        for i in range(len(lr_test)):
            
            # estimates a linear model to predict the longrun relationship
            print(self.history)
            lr_model = sm.OLS(self.history[[y_var]], self.history[lr_X_vars])
            # fits the lr model
            lr_model_fit = lr_model.fit(cov_type='HC0')
            # forecasts the disequilibrium in the next period and appends it to the list by predicting 
            # the closing price using the 1st lagged value of the independent variable at t+1, which makes it
            # at time t, and subtracting the closing price at time t, giving the residual for time t, which is 
            # t - 1 for the future value we want to predict
            disequilibrium_hat = (float(lr_model_fit.predict(self.history[-1:][lr_X_vars]))
                                - float(self.history[-1:].close.values))
            self.disequilibrium.append(disequilibrium_hat)
            # grabs the observation at the ith index
            obs = lr_test[i : i + 1]
            # appends the observation to the estimation data set
            print("Hello",self.history,obs,len(obs))
            #self.history = self.history.append(obs)
            self.history = pd.concat([self.history,obs])
            
        # creates a column of the lagged disequilibrium values 
        print(len(self.diff_test),len(self.disequilibrium))
        print(self.disequilibrium)
        self.diff_test['disequilibrium'] = self.disequilibrium
        print(self.diff_history)
        
        
        # this chunk of code does the 1-step ahead ECM estimation and prediction
        
        predictions = []
        
        # this list will store the error_correction coefficients  
        error_correction_coefficients = []
        # this list stores the standard error of the EC coefficients
        error_correction_coef_stderr = []
        print("Iterating diff_test")

        # loops through the indexes of the set being forecasted
        for i in range(len(diff_test)):
            print(self.diff_history)
            # estimates an ECM to predict future values
            ecm_model = sm.OLS(self.diff_history[[y_var]], self.diff_history[X_vars])
            # fits the ECM
            ecm_model_fit = ecm_model.fit(cov_type='HC0')
            # predicts the future closing price change and appends it to the list of predictions
            delta_y_hat = float(ecm_model_fit.predict(diff_test[i : i + 1][X_vars]))
            predictions.append(delta_y_hat)
            # grabs the observation at the ith index
            obs = diff_test[i : i + 1]
            # appends the observation to the estimation data set
            #diff_history = diff_history.append(obs)
            self.diff_history = pd.concat([self.diff_history,obs])
            
            # appends the error_correction coefficient to the list  
            error_correction_coefficients.append(ecm_model_fit.params.disequilibrium)
            error_correction_coef_stderr.append(ecm_model_fit.HC0_se.disequilibrium)
        
        # adds columns for our lists
        diff_test['delta_y_hat'] = predictions     
        diff_test['ec_coef'] = error_correction_coefficients
        diff_test['ec_stderr'] = error_correction_coef_stderr
        
        # returns predictions
        return(diff_test, ecm_model_fit) 

    def calculate_instructions(self, enter_position_z = 3, exit_position_z = 1):
        z_score = self.z_scores[-1]
        instruction = [None,self.stock2,10] #buy/sell, ticker, quantity

        if z_score < 0 or z_score >>31 -(-z_score>>31)== -1:
            if abs(z_score) > enter_position_z:
                instruction[0] = "Buy"
            elif abs(z_score) <= exit_position_z:
                instruction[0] = "Sell"
        else:
            pass
        
        self.instructions.append(instruction)


        ''' try:
            if z_score >= 0:
                if z_score > enter_position_z:
                    #short
                    instruction[0] = "Short"
                    raise("Next")
                if z_score > exit_position_z:
                    #sell
                    instruction[1] = "Sell"
                    raise("Next")
            else:
                if z_score < enter_position_z:
                    #buy
                    instruction[1] = "Buy"
                    raise("Next")
                if z_score < exit_position_z:
                    #exit short
                    instruction[0] = "Exercise"

        except Exception("Next"):
            pass
        '''

    def calculate_z_score(self,priceX,priceY):
        spread = abs(log(priceX)-log(priceY))
        self.spreads.append(spread)

        stddev = np.std(self.spreads)
        mean = np.mean(np.mean(self.spreads)) #this mean is not rolling. Don't know if this is an issue

        z_score = (spread-mean)/stddev

        self.z_scores.append(z_score)

        self.calculate_instructions() #based on calculated z_score

    def outer_test_stddev(self,priceX,priceY,std=3): #enter a position
        spread = abs(log(priceX)-log(priceY))

    def inner_test_stddev(self,priceX,priceY,std=1): # exit a position
        spread = abs(log(priceX)-log(priceY))

    def generate_instruction(self,data,model,*args):
        pass

    def plot_ecm(*func):
        def wrapper():
            pass

        return wrapper

if __name__ == "__main__":
    stock_pair = Pair(spy.columns[1],spy.columns[2])
    stock_pair.create_ecm()

    y_var,X_vars,lr_X_vars,lr_train,lr_test,diff_train,diff_test = 'close',stock_pair.predictors,['close_market','const'],stock_pair.data_train.dropna(),stock_pair.data_test,stock_pair.diff_train,stock_pair.diff_test
    stock_pair.diff_history,ecm_results = stock_pair.roll_forecast_ecm(lr_train,lr_test,diff_train,diff_test)

    print("done")