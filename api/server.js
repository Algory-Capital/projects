const mongoose = require("mongoose");
const express = require("express");
const bodyParser = require("body-parser");
const _ = require("lodash");
const cors = require("cors");
const fetch = require("node-fetch");
// const yfin2 = require("yahoo-finance2");
require("dotenv").config();

const { restClient } = require("@polygon.io/client-js");

var path = require("path");
const { start } = require("repl");

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

// if debugMode = true, do not push to db
const debugMode = false;

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

// CHECK IF API KEY IS PROPERLY LOADED FROM YOUR ENV
const apikey = process.env.POLY_API_KEY;
const fetchURL =
  "https://api.polygon.io/v3/reference/dividends?apiKey=" + apikey + "&ticker=";

const rest = restClient(apikey);

var startDates = [];

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
async function updateAUM2(excludeStartDate = true) {
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
    compareTimes(aumResults.dates.at(-1), posBenchmark.dates[i]) <= 0;
    i--
  ) {
    var newdate = posBenchmark.dates[i];
    newDates.unshift(newdate);
    addToAUM.unshift(cash);

    let price, shares;

    for (var [ticker, data] of Object.entries(js)) {
      //reverse this
      var idx = data.dates.indexOf(newdate);
      price = data.data[idx] || 0;
      shares = data.shares || 0;

      addToAUM[0] += Number.parseFloat(price * shares);
      addToAUM[0] = Math.round((addToAUM[0] + Number.EPSILON) * 100) / 100;
    }
  }
  // issue: not casting properly to Number for addToAUM
  addToAUM.map((arg) => {
    return Number(arg);
  });

  if (excludeStartDate) {
    if (
      addToAUM === undefined ||
      addToAUM.length == 0 ||
      newDates === undefined ||
      newDates.length == 0
    ) {
      console.error("Detected empty addToAUM or newDates in updateAUM2.");
      return aumResults;
    }
    addToAUM.shift();
    newDates.shift();
  }

  if (debugMode === true) {
    // var res = { addtoAUM: addToAUM, newDates: newDates };
    // return res;
    const newData = await AUMData.find({});
    console.log(newData);
    return newData[0];
  }

  // await AUMData.findOneAndUpdate(
  //   { _id: aumResults._doc._id.toHexString() },
  //   {
  //     $push: {
  //       data: { $each: addToAUM },
  //       dates: { $each: newDates },
  //     },
  //   },
  //   { new: true }
  // );

  const newData = await AUMData.find({});

  return newData[0];
}

async function resetAUM() {
  // writing this function bc I screwed up the db
  // can be used to replace updateAUM2 when retroactively place orders

  cash = 100000;
  startDate = "2022-10-05";

  var { tickers, js } = getPosData();

  for (var [ticker, data] of Object.entries(js)) {
  }
}

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

  const processTickerData = async (ticker, excludeStartDate = true) => {
    if (ticker !== "SPY") {
      var tickData = data[ticker];
      adjClose = Array(tickData.length).fill(-1);
      dates = Array(tickData.length).fill(-1);
      let tickDate;

      for (var i = tickData.length - 1; i >= 0; i--) {
        if (tickData[i].date != null && tickData[i].adjClose != null) {
          tickDate = JSON.stringify(tickData[i].date).slice(1, 11);

          if (tickDate >= js[ticker]._doc.startDate) {
            adjClose[i] = tickData[i].adjClose;
            dates[i] = tickDate;
          } else {
            adjClose[i] = null;
            dates[i] = null;
          }
        } else {
          adjClose[i] = null;
          dates[i] = null;
        }

        // console.log(
        //   tickData[i].date,
        //   dates[i],
        //   tickData[i].date == dates[i]
        // );
      }

      // adjClose.reverse();
      // dates.reverse();
      if (excludeStartDate) {
        if (
          adjClose === undefined ||
          adjClose.length == 0 ||
          dates === undefined ||
          dates.length == 0
        ) {
          console.error(
            "Detected empty adjClose or dates in processTickerData."
          );
          return;
        }
        adjClose.shift();
        dates.shift();
      }

      //if (debugMode === true) return;

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

      console.log("PUSHING DATA")
    }
  }; // end processTickerData function

  for (const ticker of tickers) {
    if (ticker != "SPY") {
      await processTickerData(ticker);
    }
  }

  console.log(`UPDATEPOS: START DATE ${startDate}, END DATE: ${endDate}`);

  var { tickers, js } = await getPosData();
  return js;
}

async function updateAUMCash() {
  var aumResults = await AUMData.find();
  aumResults = aumResults[0];

  //console.log("AUM RESULTS", aumResults)

  var curCash = aumResults["cash"];
  var lastAUMValue = aumResults["data"].at(-1);
  var nonCashAUM = 0;
  var holdings = await getPosData();
  var newCash;
  var dataArr;

  console.log(holdings)

  for (const [ticker, data] of Object.entries(holdings["js"])) 
  {
    dataArr = data["data"]
    dataArr = Array.from(dataArr)
    
    let curPrice = Number(dataArr.at(-1));
    nonCashAUM += Number((data.shares * curPrice).toFixed(2));

    console.log(`ticker ${ticker}, nonCashAUM: ${nonCashAUM} shares: ${data.shares} Total: ${data.shares * curPrice}`)
  }

  var newCash = (lastAUMValue - nonCashAUM).toFixed(2);

  if (newCash != curCash)
  {
    console.log(`Not same cash. Old cash: ${curCash}. Non-cash: ${nonCashAUM}. new Cash: ${newCash}. Updating AUM`)

    let res = await AUMData.updateOne({}, {cash : newCash});
    
    if (res.modifiedCount == 1)
    {
      console.log("Successfully updated cash.")
    }
  }

  console.log("finished cash update")
  return newCash;
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

function getLaterDate(ts1, ts2) {
  let res = compareTimes(ts1, ts2) < 0 ? ts1 : ts2;
  return res;
}

// VERSION 2 of obtaining data
app.get("/getData", async function (req, res) {
  //GETDATA ROUTE
  var { tickers, js } = await getPosData();
  var aumResults = await AUMData.find({});
  aumResults = aumResults[0];
  
  var date = new Date();
  // NASQAD + NYSE close hour 21 UTC
  // 86400000 = 24 * 60 * 60 * 1000
  // mark last date to yesterday IF AND ONLY IF market's have not closed today.
  // i know this is spaghetti but js is spaghetti anyways. I need to migrate this to typescript
  const today = date.getUTCHours() >= 21 ? date.toJSON().slice(0, 10) : new Date(date.getTime() - 86400000).toJSON().slice(0,10);

  Object.values(js).forEach((val) => {
    startDates.push(val.startDate);
  });

  var oldestDate = findEarliestDate(startDates);

  const spy = await polygon_historical(["spy"], oldestDate, today).then(
    (res) => {
      return JSON.parse(res)["spy"];
    }
  );

  var spyData = [];
  var spyDates = [];
  for (let i = 0; i < spy.length; i++) {
    spyData.push(spy[i].adjClose);
    spyDates.push(JSON.stringify(spy[i].date));
  }

  const recentDate = JSON.stringify(spy.at(-1).date);

  const today_ts = new Date(today).getTime();
  const aum_date_ts = new Date(aumResults.dates.at(-1)).getTime();

  if (today_ts > aum_date_ts) {
    // this logic needs to get refactored to last close
    console.log(
      `Update data. Detected recentDate < today. Today: ${new Date(
        today
      )}. Previous Date: ${new Date(aumResults.dates.at(-1))}`
    );
    // Update data. Detected recentDate < today
    js = await updatePosData(aumResults.dates.at(-1), today);
    aumResults = await updateAUM2();
  }

  js["SPY"] = {
    entryDate: oldestDate,
    data: spyData,
    dates: spyDates,
  };

  updateAUMCash();

  js["AUM"] = {
    cash: aumResults.cash,
    aum: aumResults.data,
    dates: aumResults.dates,
  };

  // console.log(
  //   "GETDATA: DATES: " + recentDate + " : " + aumResults.dates.at(-1)
  // );
  // console.log(oldestDate);
  res.send(js);
});

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

      // const aumResults = await AUMData.find({});
      // let aumDates = aumResults[0].dates;

      // // Update AUM until entry date of new position (edge case)
      // if (aumDates.at(-1) < startDate) {
      //   await updatePosData(aumDates.at(-1), startDate);
      //   await updateAUM2();
      // }
      // for (var i = aumDates.indexOf(dates[0]) - 1; i >= 0; i--) {
      //   dates.unshift(aumDates[i]);
      //   adjClose.unshift(null);
      // }

      // const newCash = (aumResults[0].cash - startPrice * shares).toFixed(2);
      // var newaum = await AUMData.findOneAndUpdate(
      //   { _id: aumResults[0]._doc._id },
      //   {
      //     $set: {
      //       cash: newCash,
      //     },
      //   }
      // );

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

app.get("/sellPos", function (req, res) {
  res.render("sellPos");
});

// Post route to saving the position into the portfolio
app.post("/sellPos", function (req, res) {
  const ticker = req.body.ticker.toUpperCase();
  const startDate = req.body.startdate;
  const sellPrice = req.body.sellprice;
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

      console.log("TICKER DATA IN /SELLPOS: ", {ticker})
      // const data = await yfin.historical({
      //   symbol: ticker,
      //   from: startDate,
      //   to: today,
      //   period: "d",
      // });
      // SEEMS TO BREAK HERE

      // const data = await polygon_historical({ ticker }, startDate, today).then(
      //   (res) => {
      //     return JSON.parse(res);
      //   }
      // );

      // var adjClose = [];
      // var dates = [];

      // for (var i = data.length - 1; i >= 0; i--) {
      //   if (data[i].adjClose != null) {
      //     adjClose.push(data[i].adjClose);
      //     dates.push(JSON.stringify(data[i].date).slice(1, 11));
      //   }
      // }

      // const aumResults = await AUMData.find({});
      // aumDates = aumResults[0].dates;

      // // Update AUM until entry date of new position (edge case)
      // if (aumDates.at(-1) < startDate) {
      //   //await updatePosData(aumDates.at(-1), startDate);
      //   await updateAUM2();
      // }
      // for (var i = aumDates.indexOf(dates[0]) - 1; i >= 0; i--) {
      //   dates.unshift(aumDates[i]);
      //   adjClose.unshift(null);
      // }

      // const newCash = (aumResults[0].cash + sellPrice * shares).toFixed(2);
      // var newaum = await AUMData.findOneAndUpdate(
      //   { _id: aumResults[0]._doc._id },
      //   {
      //     $set: {
      //       cash: newCash,
      //     },
      //   }
      // );
      const jsonFoundList = foundList.toObject();

      var newEquityData = {};
      const newShares = jsonFoundList.shares - shares;

      if (newShares == 0)
      {
        // Call delete
        console.log("SELL ALL OF TICKER:  ", ticker)
        // "/delete/:ticker"

      }
      else if(newShares < 0)
      {
        var card = {
          status: "Something went wrong",
          message: `Not enough shares of ${ticker} to sell. Inputed shares to sell: ${shares}`,
          buttons: [{ text: "Back to Form", link: "/sellPos" }],
        };
        res.render("error", { card });
      }

      // for weighted avg price
      const weightedAvgPrice = ((jsonFoundList.startprice * jsonFoundList.shares - shares * sellPrice) / (newShares)).toFixed(2);

      // var updatedPosition = new Equity({
      //   _id : jsonFoundList.id,
      //   ticker: ticker,
      //   startDate: startDate,
      //   entryPrice: jsonFoundList.price,
      //   shares: shares,
      // });

      const updatedPosition = await Equity.findOneAndUpdate(
        {ticker: ticker}, 
        {$set : { entryPrice : jsonFoundList.price}, $set : {shares : newShares} }
      )
      console.log("UPDATED POSITION FORM SELL: ", updatedPosition)

      //await updatedPosition.save();

      var card = {
        status: "Success!",
        message: `Successfully sold ${ticker} from portfolio`,
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

app.get("/testPolygon", async function (req, res) {
  // test route for ensuring polygon api call is correct
  console.log("GET POLYGON 1");
  let tkrs = ["MSFT"];
  const data = await polygon_historical(tkrs, "2022-12-05", "2024-05-20");
  // .then(
  //   (res) => {
  //     return JSON.parse(res);
  //   }
  // );
  console.log("GET POLYGON");

  res.send(data);
});

app.get("/testAUM2", async function (req, res) {
  aum = await updateAUM2();

  res.send(aum);
});

app.get("/testAUMRESET", async function (req, res) {
  // full AUM reset in case things go wrong
  var { tickers, js } = await getPosData();

  console.log("JKLDF");

  var aumResults = await AUMData.find({});
  aumResults = aumResults[0];

  var cash = aumResults.cash;
  var addToAUM = [];
  let tmpAUM;

  var dates = ["2022-10-05", "2022-10-06"].concat(
    js["AAPL"].dates.filter((arg) => arg != null)
  );

  console.log(dates.length);

  for (let i = 0; i < dates.length; i++) {
    console.log(cash);
    tmpAUM = cash;
    for (const ticker of tickers) {
      if (i > js[ticker].data.length) {
        // address CLOA edge case
        //console.log(ticker);
        continue;
      }

      if (dates.at(-i) == js[ticker]._doc.startDate) {
        //console.log(cash, cash + js[ticker]._doc.entryPrice);
        cash += js[ticker]._doc.entryPrice * js[ticker]._doc.shares;
        tmpAUM += js[ticker]._doc.entryPrice * js[ticker]._doc.shares;
        continue;
      }
      tmpAUM +=
        js[ticker].data.at(-i) != null
          ? js[ticker].data.at(-i) * js[ticker]._doc.shares
          : 0;
    }
    //console.log(tmpAUM - cash);
    console.log(cash);
    addToAUM.push(Math.round((tmpAUM + Number.EPSILON) * 100) / 100);
  }

  addToAUM.reverse();

  let resJSON = { date: dates, data: addToAUM };
  // await AUMData.findOneAndUpdate(
  //   { _id: aumResults._doc._id.toHexString() },
  //   {
  //     $push: {
  //       data: { $each: addToAUM },
  //       dates: { $each: dates },
  //     },
  //   },
  //   { new: true }
  // );

  res.send(resJSON);
});

let port = process.env.PORT;
if (port == null || port == "") {
  port = 3000;
}

app.listen(port, function () {
  console.log(`Server started on port ${port}.`);
});
