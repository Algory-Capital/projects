import requests
import csv

URL = "https://algoryapi.herokuapp.com/getData"


def fetch_and_calculate_portfolio_data(include_aum=False, include_cloa=False):
    try:
        response = requests.get(URL)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            response_json = response.json()

            # Specify tickers to check
            tickers_to_check = []
            for ticker in response_json:
                tickers_to_check.append(ticker)
            tickers_to_check.remove('SPY')
            tickers_to_check.remove('AUM')
            tickers_to_check.remove('CLOA')
            
            if include_aum:
                tickers_to_check.append('AUM')
            if include_cloa:
                tickers_to_check.append('CLOA')      

            current_values, total_portfolio_value = calculate_portfolio_data(response_json, tickers_to_check)

            # Save current values and percentages to CSV
            save_to_csv(current_values, total_portfolio_value)

            print("Current values and percentages saved to current_values.csv")
            return current_values, total_portfolio_value
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"An error occurred: {e}")

def calculate_portfolio_data(api_data, tickers):
    current_values = {}
    total_portfolio_value = 0

    for ticker in tickers:

        if ticker in api_data:
            if ticker == "AUM":
                
                current_value = api_data[ticker]["cash"]
                print(current_value)
                total_portfolio_value += current_value
                continue

            data = api_data[ticker]["data"]
            shares = api_data[ticker]["shares"]

            # Get the closing price on the latest date
            latest_closing_price = data[-1]

            # Calculate the current value
            current_value = shares * latest_closing_price
            current_values[ticker] = current_value

            # Update total portfolio value
            total_portfolio_value += current_value

    print(total_portfolio_value)
    return current_values, total_portfolio_value

def save_to_csv(current_values, total_portfolio_value):
    with open('current_values.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Ticker", "Current Value", "Percentage of Portfolio"])

        for ticker, value in current_values.items():
            percentage = (value / total_portfolio_value) * 100 if total_portfolio_value != 0 else 0
            writer.writerow([ticker, f"${value:.2f}", f"{percentage:.2f}%"])

def get_tickers(include_SPY=False, include_AUM=False, include_CLOA=False):
    try:
        response = requests.get(URL)

        if response.status_code == 200:
            response_json = response.json()

            tickers_to_check = []

            for ticker in response_json:
                if not include_SPY and ticker == 'SPY':
                    continue
                if not include_AUM and ticker == 'AUM':
                    continue
                if not include_CLOA and ticker == 'CLOA':
                    continue
                tickers_to_check.append(ticker)

            return tickers_to_check

        else:
            print(f"Error: {response.status_code}")
            return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
# fetch_and_calculate_portfolio_data()