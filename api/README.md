## Using the api
To add a position, go to www.algoryapi.herokuapp.com/TICKER_NAME&START_DATE&ENTRY_PRICE&NUM_SHARES&ASSET_CLASS

ASSET_CLASS is either E for equity or FI for fixed income

If entered correctly, the new position will be added to our database. To see the raw json data, go to https://algoryapi.herokuapp.com/getData to access the historical daily data on our current portfolio. 

To delete a position, enter /delete/TICKER_NAME at the end of the url.

Check out live dashboard at https://algorycapital.com/performance
