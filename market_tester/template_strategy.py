

#STRUCTURE SHOULD BE [[BUY, symbol, quantity, timestamp], [SELL, symbol, quantity, timestamp]]
#timestamp currently in Y-M-D 00:00:00 time system

def get_instructions():
    
    instructions = [['BUY', 'AAPL', 20, "2002-01-02 00:00:00"], ['BUY', 'ABT', 10, "2002-01-02 00:00:00"], ['SELL', 'AAPL', 20, "2020-01-02 00:00:00"], ['SELL', 'ABT', 10, "2003-01-02 00:00:00"]]


    return instructions



def get_settings():
    
    settings = {
    "C_FLAT": 20,
    "C_PERCENT": 0.1,
    # "C_TYPE": "FLAT",
    # "C_TYPE": "PERCENT",
    "C_TYPE": "NONE",
    "INITIAL_CAPITAL": 100000
    }
    return settings