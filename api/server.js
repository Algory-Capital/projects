const mongoose = require("mongoose");
const express = require("express");
const bodyParser = require("body-parser");
const _ = require("lodash");
const yfin = require("yahoo-finance");
const cors = require("cors");
const fetch = require("node-fetch");
// const yfin2 = require("yahoo-finance2");
require("dotenv").config();

const { restClient } = require("@polygon.io/client-js");
// const { start } = require("repl");

var path = require("path");

const app = express();
app.use(cors());

app.engine("pug", require("pug").__express);

app.set("views", path.join(__dirname, "/dashboard/assets/"));
app.set("view engine", "pug");

app.use(bodyParser.urlencoded({ extended: true }));
app.use("/assets", express.static(__dirname + "/dashboard/assets/"));

mongoose.connect(
  "mongodb+srv://admin:admin123@cluster0.ftlnrsd.mongodb.net/algoryPortDB"
);

const divSchema = {
  lastUpdate: String,
  payoutRatio: Number,
  payout: Number,
  frequency: Number,
};

const equitiesSchema = {
  ticker: String,
  startDate: String,
  entryPrice: Number,
  shares: Number,
  divInfo: divSchema,
  assetClass: String,
  data: [Number],
  dates: [String],
};

const Equity = mongoose.model("Equity", equitiesSchema);

const aumDataSchema = {
  cash: Number,
  data: [Number],
  dates: [String],
};

const AUMData = mongoose.model("AUMData", aumDataSchema);

const apikey = process.env.POLY_API_KEY;
const fetchURL =
  "https://api.polygon.io/v3/reference/dividends?apiKey=" + apikey + "&ticker=";

const rest = restClient(process.env.POLY_API_KEY);

function unix_to_date(unix_ts) {
  // convert unix to our date format
  // Polygon provides timestamp in unix
  var date = new Date(unix_ts);

  // Create our formatted string
  var year = date.getUTCFullYear();
  var month = (date.getUTCMonth() + 1).toString().padStart(2, "0");
  var day = date.getDate().toString().padStart(2, "0");

  // Build string: YYYY-MM-DD
  return year + "-" + month + "-" + day;
}

async function polygon_historical(tickers, start_date, end_date) {
  console.log("POLYGON HISTORICAL CALLED");

  return new Promise((resolve, reject) => {
    let res = {};
    const promises = []; // Array to store promises from API calls

    for (const ticker of tickers) {
      console.log("TICKER: " + ticker);
      try {
        console.log("Dates: " + start_date + " : " + end_date);

        const promise = rest.stocks
          .aggregates(ticker.toUpperCase(), 1, "day", start_date, end_date)
          .then((data) => {
            res[ticker] = [];

            data.results.forEach((arg) => {
              let ts = unix_to_date(arg.t);

              let tkrData = {
                adjClose: arg.c,
                date: ts,
              };

              res[ticker].push(tkrData);
            });
          });
        promises.push(promise);
      } catch (error) {
        console.error("ERROR OCCURRED IN POLYGON_HISTORICAL: " + error);
        reject(error);
      }
    }

    Promise.all(promises)
      .then(() => {
        console.log("RETURNING:", res);
        resolve(JSON.stringify(res));
      })
      .catch((error) => {
        throw error;
      });
  });
}

// USELESS? We just need a getter + json parsing for polygon data
// async function updatePolygonPosData() {
//   /*
//    * Updates Polygon Position Data via Polygon API
//    * To be called when SPY.dates.at(-1) is not latest date (needs updating)
//    */
//   let tickers = [];
//   js = {};
//   // iterate documents
//   for await (const doc of Equity.find({}, (err, equities) => {
//     if (err) console.error("Error occurred in getPolygonPosData", err);
//   })) {
//     equities.map((equity) => {
//       tickers.push(equity.ticker);
//       js[equity.ticker] = equity;
//     });
//   }

//   return { tickers, js };
// }

// DIVIDEND IMPLEMENTATION FROM POLYGON. Limited 5 queries per minute
// TODO: rewrite?
async function getDivUpdate(ticker, value, spy) {
  // console.log(ticker);
  // target ex_dividend_date
  var addToAUM = 0;
  fetch(fetchURL + ticker)
    .then((result) => result.json())
    .then(async (output) => {
      if (output.results != undefined && output.results.length > 0) {
        // console.log(ticker, value)
        for (const divEntry of output.results) {
          // console.log(`${ticker} last update: ${value.divInfo.lastUpdate} ? ${divEntry.ex_dividend_date}`)
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
      console.log(addToAUM);
      return addToAUM;
    });
}

// Simple query to db for stored positions
async function getPosData() {
  let tickers = [];
  js = {};

  const equityResults = await Equity.find({}).catch((err) => {
    console.error(
      "Error occurred in getPosData with fetching Equity Collection: ",
      err
    );
  });
  equityResults.forEach((equity) => {
    tickers.push(equity.ticker);
    js[equity.ticker] = equity;
  });

  return { tickers, js };
}

// VERSION 2 Updates the AUM until the last stored position data
async function updateAUM2() {
  // calculate AUM from current db collection
  var { tickers, js } = await getPosData();

  var aumResults = await AUMData.find({});
  aumResults = aumResults[0];

  var cash = aumResults.cash;
  var addToAUM = [];
  var newDates = [];

  var posBenchmark = Object.values(js)[0];

  for (
    let i = posBenchmark.dates.length - 1;
    aumResults.dates.at(-1) < posBenchmark.dates[i];
    i--
  ) {
    var newdate = posBenchmark.dates[i];
    newDates.unshift(newdate);
    addToAUM.unshift(cash);

    for (var [ticker, data] of Object.entries(js)) {
      var idx = data.dates.indexOf(newdate);
      addToAUM[0] += Number.parseFloat(
        (data.data[idx] * data.shares).toFixed(2)
      );
    }
  }

  await AUMData.findOneAndUpdate(
    { _id: aumResults._doc._id.toHexString() },
    {
      $push: {
        data: { $each: addToAUM },
        dates: { $each: newDates },
      },
    },
    { new: true }
  );

  const newData = await AUMData.find({});

  return newData[0];
}

// Updating the position data and dates within the db
async function updatePosData(startDate, endDate) {
  // TODO: Fix. Replace YFin with Polygon
  var { tickers, js } = await getPosData();
  tickers.push("SPY");

  // CHANGE YFIN.HISTORICAL, AND DATE TARGETING
  // const data = await yfin.historical({
  //   symbols: tickers,
  //   from: startDate,
  //   to: endDate,
  //   period: "d",
  // });

  const data = await polygon_historical(tickers, startDate, endDate).then(
    (res) => {
      return JSON.parse(res);
    }
  );

  for (let ticker of data) {
    if (ticker != "SPY") {
      var adjClose = [];
      var dates = [];
      var tickData = data[ticker];
      for (var i = tickData.length - 1; i >= 0; i--) {
        if (tickData[i].date != null && tickData[i].adjClose != null) {
          // If the date doesn't exist. TODO: Check if dates are handled differently
          if (
            // Custom comparator function
            JSON.stringify(tickData[i].date).slice(1, 11) >
            js[ticker]._doc.dates.at(-1)
          ) {
            adjClose.push(tickData[i].adjClose);
            dates.push(JSON.stringify(tickData[i].date).slice(1, 11));
          }
        } else {
          // Something is wrong with the stock's data for that specific date
          adjClose.push(null);
          dates.push(null);
        }
      }

      var ret = await Equity.findOneAndUpdate(
        { ticker: ticker },
        {
          $push: {
            data: { $each: adjClose },
            dates: { $each: dates },
          },
        },
        { new: true }
      );
    }
  }

  var { tickers, js } = await getPosData();
  return js;
}

// Finds the earliest date given an array of dates
function findEarliestDate(dates) {
  if (dates.length == 0) return null;
  var earliestDate = dates[0];
  for (var i = 1; i < dates.length; i++) {
    var currentDate = dates[i];
    if (currentDate < earliestDate) {
      earliestDate = currentDate;
    }
  }
  return earliestDate;
}

// VERSION 2 of obtaining data
app.get("/getData", async function (req, res) {
  var { tickers, js } = await getPosData();
  var aumResults = await AUMData.find({});
  aumResults = aumResults[0];
  const today = new Date().toJSON().slice(0, 10);

  var startDates = [];
  Object.values(js).forEach((val) => {
    startDates.push(val.startDate);
  });

  var oldestDate = findEarliestDate(startDates);

  // const spy = await yfin.historical({
  //   symbol: "SPY",
  //   from: oldestDate,
  //   to: today,
  //   period: "d",
  // });
  const spy = await polygon_historical(["spy"], oldestDate, today).then(
    (res) => {
      return JSON.parse(res)["spy"];
    }
  );
  //spy = JSON.parse(spy)["spy"];

  console.log("SPY in getData", spy);

  var spyData = [];
  var spyDates = [];
  for (let i = spy.length - 1; i >= 0; i--) {
    spyData.push(spy[i].adjClose);
    spyDates.push(JSON.stringify(spy[i].date));
    //spyDates.push(JSON.stringify(spy[i].date).slice(1, 11));
  }

  const recentDate = JSON.stringify(spy[0].date);
  //const recentDate = JSON.stringify(spy[0].date).slice(1, 11);

  if (recentDate > aumResults.dates.at(-1)) {
    js = await updatePosData(aumResults.dates.at(-1), today);
    aumResults = await updateAUM2();
  }

  js["SPY"] = {
    entryDate: oldestDate,
    data: spyData,
    dates: spyDates,
  };

  js["AUM"] = {
    cash: aumResults.cash,
    aum: aumResults.data,
    dates: aumResults.dates,
  };

  res.send(js);
});

// DEPRECATED v1 of obtaining data (never persisted data in db so i made v2)
app.get("/getDataOld", function (req, res) {
  Equity.find({}).then(function (results, err) {
    if (err) {
      console.log(err);
      res.send(err);
    } else {
      var js = {};
      var tickers = [];
      var startDates = [];
      var aumDates = [];
      var shares = [];
      var entryPrice = [];
      var divInfo = [];
      var assetClass = [];
      results.forEach(function (result) {
        tickers.push(result.ticker);
        startDates.push(result.startDate);
        shares.push(result.shares);
        entryPrice.push(result.entryPrice);
        divInfo.push(result.divInfo);
        assetClass.push(result.assetClass);
      });
      tickers.push("SPY");

      var oldestDate = findEarliestDate(startDates);
      startDates.push(oldestDate);

      var oldestTicker = tickers[startDates.indexOf(oldestDate)];

      getData(tickers, oldestDate)
        .then((data) => {
          for (let ticker in data) {
            var adjClose = [];
            var dates = [];
            var idx = tickers.indexOf(ticker);
            for (var i = data[ticker].length - 1; i >= 0; i--) {
              if (data[ticker][i].adjClose != null) {
                adjClose.push(data[ticker][i].adjClose);
                dates.push(JSON.stringify(data[ticker][i].date).slice(1, 11));
              }
            }

            var start = dates.indexOf(startDates[idx]);
            adjClose = adjClose.slice(start);

            js[ticker] = {
              shares: shares[idx],
              entryPrice: entryPrice[idx],
              entryDate: startDates[idx],
              data: adjClose,
              dates: dates,
              divInfo: divInfo[idx],
              assetClass: assetClass[idx],
            };
          }

          for (var [ticker, value] of Object.entries(js)) {
            if (ticker != oldestTicker) {
              if (value.dates.length == js[oldestTicker].dates.length) {
                for (
                  var i = value.data.length;
                  i < js[oldestTicker].data.length;
                  i++
                ) {
                  value.data.unshift(null);
                }
              } else {
                while (value.data.length != value.dates.length) {
                  value.data.unshift(null);
                }
              }
            }
          }

          //check if aum collection has any documents
          AUMData.find({}).then((aumResults, err) => {
            if (err) {
              console.log(err);
            } else {
              var spy = js["SPY"];
              if (aumResults.length == 0) {
                let cash = 100536.24;
                updateAUM(spy.dates.at(0), spy, js, cash).then((result) => {
                  // drop previously populated AUM collection
                  // AUMData.deleteMany({}, (err, results) => {
                  //   if (err) {
                  //     console.log(err);
                  //   }
                  // });

                  var newAUMData = new AUMData({
                    cash: result.cash,
                    data: result.aum,
                    dates: spy.dates,
                  });
                  newAUMData.save();
                  js["AUM"] = {
                    cash: result.cash,
                    aum: result.aum,
                    dates: spy.dates,
                  };
                  res.send(js);
                });
              } else {
                var aum = aumResults[0];
                if (aum.dates.at(-1) < spy.dates.at(-1)) {
                  let updateStartDate = spy.dates.at(
                    spy.dates.indexOf(aum.dates.at(-1)) + 1
                  );

                  // var assetWorth = [];
                  // for (var [ticker, value] of Object.entries(js)) {
                  //   if (ticker != 'SPY'){
                  //     assetWorth.push(Number.parseFloat(value.shares * value.data.at(-1).toFixed(2)));
                  //   }
                  // }
                  // cash = Number.parseFloat((aum.data.at(-1) - assetWorth.reduce((a,b)=>a+b)).toFixed(2));
                  updateAUM(updateStartDate, spy, js, aum.cash).then(
                    (result) => {
                      let newDates = spy.dates.slice(
                        spy.dates.indexOf(aum.dates.at(-1)) + 1
                      );
                      AUMData.findOneAndUpdate(
                        { _id: aum._id.toHexString() },
                        {
                          $push: {
                            data: result.aum,
                            dates: newDates,
                          },
                          cash: result.cash,
                        },
                        (err, testResult) => {
                          if (err) {
                            console.log(err);
                          }
                          AUMData.findOne(
                            { _id: aum._id.toHexString() },
                            (err, testResult) => {
                              js["AUM"] = {
                                cash: testResult.cash,
                                aum: testResult.data,
                                dates: testResult.dates,
                              };
                              res.send(js);
                            }
                          );
                        }
                      );
                    }
                  );
                } else {
                  js["AUM"] = {
                    cash: aum.cash,
                    aum: aum.data,
                    dates: aum.dates,
                  };
                  res.send(js);
                }
              }
            }
          });

          // Update AUM
          // for (let i = 0; i < js[oldestTicker].data.length; i++) {
          //   let addToAUM = 0;
          //   for (let [ticker, value] of Object.entries(js).slice(0, -1)) {
          //     let data = value.data;
          //     if (i == 0 && data[i] != null) {
          //       addToAUM += ((data[i] - value.entryPrice) * js[ticker].shares);
          //     } else {
          //       if (data[i] != null && data[i-1] != null) {
          //         addToAUM += ((data[i] - data[i-1]) * js[ticker].shares);
          //       }
          //     }
          //     addToAUM += (aum[aum.length - 1] - addToAUM) * 0.000038847;
          //   }
          //   aum.push(Number.parseFloat((aum[aum.length - 1] + addToAUM).toFixed(2)));
          //   aumDates.push(js[oldestTicker].dates[i]);
          //   if (i == 0) {aum.shift();}
          // }

          // js["AUM"] = {
          //   dates: aumDates,
          //   aum: aum,
          // }
        })
        .catch((err) => {
          res.send(err);
          console.log(err);
        });
    }
  });
});

// app.get("/", async function (req, res) {
//   console.log("SDJFKLSD");
//   const oldestDate = new Date().toJSON().slice(0, 10);
//   const today = new Date().toJSON().slice(0, 10);
//   let spy = await polygon_historical(["spy"], "2022-01-01", "2023-08-31").then(
//     () => {
//       console.log("MEOW");
//     }
//   );

//   console.log("SPY", spy);
// });

// Actual interface to adding a position
app.get("/addPos", function (req, res) {
  res.render("addPos");
});

// Post route to saving the position into the portfolio
app.post("/addPos", function (req, res) {
  const ticker = req.body.ticker.toUpperCase();
  const startDate = req.body.startdate;
  const startPrice = req.body.startprice;
  const shares = req.body.shares;
  const assetClass = req.body.assetclass.toUpperCase();
  const today = new Date().toJSON().slice(0, 10);
  var dividend;

  Equity.findOne({ ticker: ticker }).then(async function (foundList, err) {
    if (err) {
      console.log(err);
      res.send(`Error: ${err}`);
    } else if (foundList) {
      // TODO: need to incorporate adding to positions
      var card = {
        status: "Something went wrong",
        message: `${ticker} already exists in the portfolio`,
        buttons: [{ text: "Back to Form", link: "/addPos" }],
      };
      res.render("error", { card });
    } else {
      // const data = await yfin.historical({
      //   symbol: ticker,
      //   from: startDate,
      //   to: today,
      //   period: "d",
      // });

      const data = await polygon_historical([ticker], startDate, today).then(
        (res) => {
          return JSON.parse(res);
        }
      );

      var adjClose = [];
      var dates = [];

      for (var i = data.length - 1; i >= 0; i--) {
        if (data[i].adjClose != null) {
          adjClose.push(data[i].adjClose);
          dates.push(JSON.stringify(data[i].date).slice(1, 11));
        }
      }

      const aumResults = await AUMData.find({});
      let aumDates = aumResults[0].dates;

      // Update AUM until entry date of new position (edge case)
      if (aumDates.at(-1) < startDate) {
        await updatePosData(aumDates.at(-1), startDate);
        await updateAUM2();
      }
      for (var i = aumDates.indexOf(dates[0]) - 1; i >= 0; i--) {
        dates.unshift(aumDates[i]);
        adjClose.unshift(null);
      }

      const newCash = (aumResults[0].cash - startPrice * shares).toFixed(2);
      var newaum = await AUMData.findOneAndUpdate(
        { _id: aumResults[0]._doc._id },
        {
          $set: {
            cash: newCash,
          },
        }
      );

      var newPosition = new Equity({
        ticker: ticker,
        startDate: startDate,
        entryPrice: startPrice,
        shares: shares,
        divInfo: dividend,
        assetClass: assetClass,
        data: adjClose,
        dates: dates,
      });

      await newPosition.save();

      var card = {
        status: "Success!",
        message: `Successfully added ${ticker} to portfolio`,
        buttons: [
          {
            text: "Go to Dashboard",
            link: "https://www.algorycapital.com/performance",
          },
          {
            text: "See Raw Data",
            link: "https://algoryapi.herokuapp.com/getData",
          },
        ],
      };

      res.render("error", { card, title: "Success!" });
    }
  });
});

// DEPRECATED there was no front-end for this and the logic was shit
app.get(
  "/:ticker&:startDate&:startPrice&:shares&:asset",
  async function (req, res) {
    const ticker = req.params.ticker.toUpperCase();
    const startDate = req.params.startDate;
    const startPrice = req.params.startPrice;
    const shares = req.params.shares;
    const assetClass = req.params.asset;
    const today = new Date().toJSON().slice(0, 10);
    var dividend;

    await fetch(fetchURL + ticker)
      .then((result) => result.json())
      .then((output) => {
        for (const divEntry of output.results) {
          if (divEntry.ex_dividend_date > today) {
            continue;
          } else {
            dividend = {
              lastUpdate: divEntry.ex_dividend_date,
              payoutRatio: divEntry.cash_amount,
              payout: null,
              frequency: divEntry.frequency,
            };
            break;
          }
        }
      });

    Equity.findOne({ ticker: ticker }, function (err, foundList) {
      if (err) {
        console.log(err);
        res.send(`Error: ${err}`);
      } else if (foundList) {
        res.send(`${ticker} already exists in the portfolio`);
      } else {
        var newPosition = new Equity({
          ticker: ticker,
          startDate: startDate,
          entryPrice: startPrice,
          shares: shares,
          divInfo: dividend,
          assetClass: assetClass,
        });

        newPosition.save();

        res.send(`Successfully added ${ticker} to portfolio`);
      }
    });
  }
);

// Sell Position.

app.get("sellPos", function (req, res) {
  res.render("sellPos");
});

// Post route to saving the position into the portfolio
app.post("/sellPos", function (req, res) {
  const ticker = req.body.ticker.toUpperCase();
  const startDate = req.body.startdate;
  const startPrice = req.body.sellprice;
  const shares = req.body.shares;
  const assetClass = req.body.assetclass.toUpperCase();
  const today = new Date().toJSON().slice(0, 10);
  var dividend;

  Equity.findOne({ ticker: ticker }).then(async function (foundList, err) {
    if (err) {
      console.log(err);
      res.send(`Error: ${err}`);
    } else if (!foundList) {
      // TODO: need to incorporate adding to positions
      var card = {
        status: "Something went wrong",
        message: `${ticker} does not exist in the portfolio`,
        buttons: [{ text: "Back to Form", link: "/sellPos" }],
      };
      res.render("error", { card });
    } else {
      // const data = await yfin.historical({
      //   symbol: ticker,
      //   from: startDate,
      //   to: today,
      //   period: "d",
      // });

      const data = await polygon_historical({ ticker }, startDate, today).then(
        (res) => {
          return JSON.parse(res);
        }
      );

      var adjClose = [];
      var dates = [];

      for (var i = data.length - 1; i >= 0; i--) {
        if (data[i].adjClose != null) {
          adjClose.push(data[i].adjClose);
          dates.push(JSON.stringify(data[i].date).slice(1, 11));
        }
      }

      const aumResults = await AUMData.find({});
      aumDates = aumResults[0].dates;

      // Update AUM until entry date of new position (edge case)
      if (aumDates.at(-1) < startDate) {
        await updatePosData(aumDates.at(-1), startDate);
        await updateAUM2();
      }
      for (var i = aumDates.indexOf(dates[0]) - 1; i >= 0; i--) {
        dates.unshift(aumDates[i]);
        adjClose.unshift(null);
      }

      const newCash = (aumResults[0].cash + startPrice * shares).toFixed(2);
      var newaum = await AUMData.findOneAndUpdate(
        { _id: aumResults[0]._doc._id },
        {
          $set: {
            cash: newCash,
          },
        }
      );

      var newPosition = new Equity({
        ticker: ticker,
        startDate: startDate,
        entryPrice: startPrice,
        shares: shares,
        divInfo: dividend,
        assetClass: assetClass,
        data: adjClose,
        dates: dates,
      });

      await newPosition.save();

      var card = {
        status: "Success!",
        message: `Successfully added ${ticker} to portfolio`,
        buttons: [
          {
            text: "Go to Dashboard",
            link: "https://www.algorycapital.com/performance",
          },
          {
            text: "See Raw Data",
            link: "https://algoryapi.herokuapp.com/getData",
          },
        ],
      };

      res.render("error", { card, title: "Success!" });
    }
  });
});

app.get("/delete/:ticker", function (req, res) {
  const ticker = req.params.ticker.toUpperCase();
  Equity.deleteMany({ ticker: ticker }, (err) => {
    if (err) {
      console.log(err);
    } else {
      res.send(`Successfully deleted ${ticker} from database`);
    }
  });
});

let port = process.env.PORT;
if (port == null || port == "") {
  port = 3000;
}

app.listen(port, function () {
  console.log(`Server started on port ${port}.`);
});
