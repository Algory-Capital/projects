## Using the api

To add a position, go to www.algoryapi.herokuapp.com/addPos

ASSET_CLASS is either E for equity or FI for fixed income

If entered correctly, the new position will be added to our database. To see the raw json data, go to https://algoryapi.herokuapp.com/getData to access the historical daily data on our current portfolio.

To delete a position, go to www.algoryapi.herokuapp.com/delete/TICKER

Check out live dashboard at https://algorycapital.com/performance

[Polygon Library](https://www.npmjs.com/package/@polygon.io/client-js?ref=polygon.io)

[Ticker Historical API Call](https://polygon.io/docs/stocks/get_v2_aggs_ticker__stocksticker__range__multiplier___timespan___from___to)

### JSON formatting

- Ticker
  - Array with JSON (keys: date, adjClose)

> [!WARNING]
> DO <strong>NOT</strong> USE REST CLIENT ["@polygon.io/client-js"](https://github.com/polygon-io/client-js)
