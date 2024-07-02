# Algory Dashboard

Created by Anay Roge, maintained by Alexander Liu.

Currently down. While our dashboard works on localhost and CodePen, it is crashing on Wix due to ApexCharts refresh routines.

## Possible fixes

- Contact Wix
- Vero by Wix?
- Switch libaries
- External website embed

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

## Backups

- [ApexCharts Backup (CodePen)](https://codepen.io/Fobertree/pen/BaegMKY)
