import json
import numpy as np

# handle calls/puts

'''
Examples:

"SPDR S+P 500 393.0 PUT 14APR23"
"SPDR S+P 500 406.0 PUT 28APR23"
"SEPTEMBER 23 CALLS ON VIX 17.000000"

For some reason NEXEN does not have standard formatting
'''

class OptionsException(Exception):
    "OPTIONS EXCEPTION: "

class Options:
    def __init__(self, path = "./Data/aliases.json"):
        self.cfg = json.load(path)['options']

    def handle_options(self, transaction : str, premium: float):
        try:
            if transaction not in self.cfg:
                raise (OptionsException("Failed to locate transaction in aliases.json."))
            data = self.cfg[transaction]

            # could just do data.values() here but I'd rather not
            date, opt_type, asset, strike = data['date'], data['type'], data['asset'], data['strike']

            if opt_type == "PUT":
                self.put(asset, date, premium)
            elif opt_type == "CALL":
                self.call(asset, date, premium)
            else:
                raise (OptionsException("Invalid Option Type: ", opt_type))
        except OptionsException as e:
            print(e)

    def put(self, asset, date, premium):
        cost = 100 * 10
        pass

    def call(self, asset, date, premium):
        pass