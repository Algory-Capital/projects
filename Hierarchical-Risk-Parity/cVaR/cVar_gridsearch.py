import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
import datetime as dt
from tqdm import tqdm

class PortfolioSimulator:
    def __init__(self, ticker_file, initial_portfolio=100000, mc_sims=10000, T=365, alpha=5):
        self.ticker_file = ticker_file
        self.initial_portfolio = initial_portfolio
        self.mc_sims = mc_sims
        self.T = T
        self.alpha = alpha

    def getData(self, additional_ticker=None):
        df = pd.read_csv(self.ticker_file)
        stocks = df["Ticker"].tolist()
        if additional_ticker is not None:
            stocks.append(additional_ticker)
        endDate = dt.datetime.now()
        startDate = endDate - dt.timedelta(days=365)
        data = yf.download(stocks, start=startDate, end=endDate)["Close"]
        returns = data.pct_change().dropna()
        meanReturns = returns.mean()
        covMatrix = returns.cov()
        return returns, meanReturns, covMatrix, df

    def portfolioPerformance(self, weights, meanReturns, covMatrix):
        returns = np.sum(meanReturns * weights) * self.T
        std = np.sqrt(np.dot(weights.T, np.dot(covMatrix, weights))) * np.sqrt(self.T)
        return returns, std
    
    def calculateVaRCVaR(self, portfolio_sims):
        portResults = pd.Series(portfolio_sims[-1, :])
        VaR = self.initial_portfolio - np.percentile(portResults, self.alpha)
        CVaR = self.initial_portfolio - self.mcCVaR(portResults)
        print(f"Value at Risk: {VaR}")
        print(f"Conditional Value at Risk: {CVaR}")

    def mcCVaR(self, returns):
        VaR = np.percentile(returns, self.alpha)
        belowVaR = returns <= VaR
        return returns[belowVaR].mean() if belowVaR.any() else np.nan


    def simulate(self):
        returns, meanReturns, covMatrix, df = self.getData()
        weights = df["Percentage of Portfolio"].apply(lambda x: float(x.strip("%")) / 100).values
        weights /= np.sum(weights)
        
        meanM = np.full(shape=(self.T, len(weights)), fill_value=meanReturns).T
        portfolio_sims = np.zeros((self.T, self.mc_sims))
        
        for m in range(self.mc_sims):
            Z = np.random.normal(size=(self.T, len(weights)))
            L = np.linalg.cholesky(covMatrix)
            dailyReturns = meanM + np.inner(L, Z)
            portfolio_sims[:, m] = np.cumprod(np.inner(weights, dailyReturns.T) + 1) * self.initial_portfolio
        
        self.plotMonteCarloSimulation(portfolio_sims)
        self.calculateVaRCVaR(portfolio_sims)

    def plotMonteCarloSimulation(self, portfolio_sims):
        plt.figure(figsize=(10, 6))
        plt.plot(portfolio_sims)
        plt.title('Monte Carlo Simulation of Portfolio Value')
        plt.xlabel('Days')
        plt.ylabel('Portfolio Value')
        plt.grid(True)
        plt.show()

    def simulatePortfolio(self, weights, meanReturns, covMatrix, num_sims=10000, T=365):
        """
        Simulate portfolio performance given weights and returns characteristics.
        Returns an array of ending portfolio values after T days, across all simulations.
        """
        portfolio_sims = np.zeros(num_sims)
        for sim in range(num_sims):
            daily_returns = np.random.multivariate_normal(meanReturns, covMatrix, T)
            cumulative_returns = np.cumprod(1 + np.dot(daily_returns, weights))
            portfolio_sims[sim] = cumulative_returns[-1]
        return portfolio_sims
    
    def calculateCVaR(self, portfolio_sims, alpha=5):
        """
        Calculate the Conditional Value at Risk (CVaR) at the specified alpha percentile.
        """
        VaR = np.percentile(portfolio_sims, alpha)
        CVaR = portfolio_sims[portfolio_sims <= VaR].mean()
        return CVaR

    def gridSearchForNewTicker(self, new_ticker, weight_increment=0.002, target_return=None):
        _, meanReturns, covMatrix, df = self.getData(new_ticker)
        best_CVaR = float('-inf')
        best_weight = 0
        
        print("Starting grid search for optimal weight...")
        original_weights = df["Percentage of Portfolio"].apply(lambda x: float(x.strip("%")) / 100).values
        original_weights /= np.sum(original_weights)  # Normalize before the grid search
        
        for weight in tqdm(np.arange(0, 0.31, weight_increment), desc="Grid Searching Weights"):
            new_weights = np.append(original_weights * (1 - weight), weight)
            new_weights /= np.sum(new_weights)  # Ensure new weights sum to 1 after appending
            
            portfolio_sims = self.simulatePortfolio(new_weights, meanReturns, covMatrix)
            CVaR = self.calculateCVaR(portfolio_sims)
            
            if CVaR > best_CVaR:
                best_CVaR = CVaR
                best_weight = weight

        # Normalize and adjust original weights based on the optimal weight for the new ticker
        adjusted_weights = original_weights * (1 - best_weight)
        final_weights = np.append(adjusted_weights, best_weight)
        final_weights /= np.sum(final_weights)  # Normalize final weights to sum to 1

        # Print out normalized percentages
        print(f"\nOptimal weight for {new_ticker}: {best_weight*100:.2f}% with CVaR: {best_CVaR}")
        print("Normalized percentages of all stock tickers including the new ticker:")
        for i, ticker in enumerate(df['Ticker'].tolist() + [new_ticker]):
            print(f"{ticker}: {final_weights[i]*100:.2f}%")

        return best_weight


# Example usage
simulator = PortfolioSimulator("../current_values.csv")
best_weight = simulator.gridSearchForNewTicker("BLK")
