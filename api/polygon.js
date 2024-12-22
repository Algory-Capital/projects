// begin migration of polygon helper funcs for modularity but low prio

const { restClient } = require("@polygon.io/client-js");

// CHECK IF API KEY IS PROPERLY LOADED FROM YOUR ENV
const apikey = process.env.POLY_API_KEY;
const fetchURL =
  "https://api.polygon.io/v3/reference/dividends?apiKey=" + apikey + "&ticker=";

const rest = restClient(apikey);

// slight redundancy: exists in both polygon and server.js and polygon.js
// TODO: migrate to utils.js
function compareTimes(t1, t2) {
  /*
   * -1: t1 < t2
   *  0: t1 = t2
   *  1: t1 > t2
   */
  if (t1 == t2) {
    return 0;
  }

  return t1 < t2 ? -1 : 1;
}

function unix_to_date(unix_ts) {
    // convert unix to our date format
    // Polygon provides timestamp in unix, UTC/GMT TIME
    var date = new Date(unix_ts);
  
    // Create our formatted string
    var year = date.getUTCFullYear();
    var month = (date.getUTCMonth() + 1).toString().padStart(2, "0");
    var day = date.getUTCDate().toString().padStart(2, "0");
  
    // Build string: YYYY-MM-DD
    return year + "-" + month + "-" + day;
  }
  
  function build_polygon_URL(ticker, start_date, end_date) {
    // GET request to Polygon Stocks Aggregate Bars
    // date format: YYYY-MM-DD
    let tkr = ticker.toUpperCase().replace("-", ".");
    return `https://api.polygon.io/v2/aggs/ticker/${tkr}/range/1/day/${start_date}/${end_date}?adjusted=true&sort=asc&apiKey=${POLY_API_KEY}`;
  }
  
  async function polygon_historical(tickers, start_date, end_date) {
  
    return new Promise((resolve, reject) => {
      let res = {};
      const promises = []; // Array to store promises from API calls
      console.log("TICKERS: ", tickers)
  
      try {
        tickers.forEach((ticker, idx) => {
          try {
            // replace for BRK-B edge case
            const promise = rest.stocks
              .aggregates(
                ticker.toUpperCase().replace("-", "."),
                1,
                "day",
                start_date,
                end_date
              )
              .then((data) => {
                res[ticker] = [];
    
                if (data.results == undefined) {
                  return;
                }
    
                data.results.forEach((arg) => {
                  let ts = unix_to_date(arg.t);
                  
                  // issue here
                  if (compareTimes(ts, startDates[idx]) <= 0) {
                    res[ticker].push({ adjClose: null, date: null });
                  } else {
                    let tkrData = {
                      adjClose: arg.c,
                      date: ts,
                    };
    
                    res[ticker].push(tkrData);
                  }
                });
              });
            promises.push(promise);
          } catch (error) {
            console.error("ERROR OCCURRED IN POLYGON_HISTORICAL: " + error);
            //reject(error);
          }
        });
      } catch (error) {
        console.error("INVALID ERROR WITH FOREACH IN POLYGON_HISTORICAL: ", tickers)
      }
      
  
      Promise.all(promises)
        .then(() => {
          resolve(JSON.stringify(res));
        })
        .catch((error) => {
          throw error;
        });
    });
  }

  
// DIVIDEND IMPLEMENTATION FROM POLYGON. Limited 5 queries per minute
// TODO: rewrite?
async function getDivUpdate(ticker, value, spy) {
  // target ex_dividend_date
  var addToAUM = 0;
  fetch(fetchURL + ticker)
    .then((result) => result.json())
    .then(async (output) => {
      if (output.results != undefined && output.results.length > 0) {
        for (const divEntry of output.results) {
          if (divEntry.ex_dividend_date > spy.dates.at(-1)) {
            continue;
          } else if (divEntry.ex_dividend_date == value.divInfo.lastUpdate) {
            break;
          } else if (value.divInfo.lastUpdate < divEntry.ex_dividend_date) {
            // calculate div payout
            addToAUM += divEntry.cash_amount * value.shares;
            // set divInfo to this ex_dividend_date
            const doc = await Equity.findOneAndUpdate(
              { ticker: ticker },
              {
                divInfo: {
                  lastUpdate: divEntry.ex_dividend_date,
                  payoutRatio: divEntry.cash_amount,
                  payout: addToAUM,
                  frequency: divEntry.frequency,
                },
              }
            );

            break;
          }
        }
      }
      return addToAUM;
    });
  }
  
  // module.exports = {
  //   build_polygon_URL,
  //   polygon_historical
  // }