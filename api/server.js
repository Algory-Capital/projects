const mongoose = require("mongoose");
const express = require("express");
const bodyParser = require("body-parser");
const _ = require("lodash");
const yfin = require("yahoo-finance");
const axios = require('axios');
const cors = require("cors");
const e = require("express");

const app = express();
app.use(cors());

app.set('view engine', 'ejs');

app.use(bodyParser.urlencoded({extended: true}));
app.use(express.static("public"));

mongoose.connect("mongodb+srv://admin:admin123@cluster0.ftlnrsd.mongodb.net/algoryPortDB");

const equitiesSchema = {
  ticker: String,
  startDate: String,
  entryPrice: Number,
  shares: Number
};

const Equity = mongoose.model("Equity", equitiesSchema);

function findEarliestDate(dates){
    if(dates.length == 0) return null;
    var earliestDate = dates[0];
    for(var i = 1; i < dates.length ; i++){
        var currentDate = dates[i];
        if(currentDate < earliestDate){
            earliestDate = currentDate;
        }
    }
    return earliestDate;
}

async function getData(tickers, startDate) {
  const today = new Date().toJSON().slice(0, 10);

  const myData = yfin.historical({
    symbols: tickers,
    from: startDate,
    to: today,
    period: 'd'
  }).catch((err) => {
    console.log(err);
  })
  return myData;
}



app.get("/getData", function(req, res) {
  Equity.find({}, function(err, results) {
    if (err) {
      console.log(err);
      res.send(err);
    } else {
      var js = {};
      var tickers = [];
      var startDates = [];
      const aum = [100536.24];
      var aumDates = [];
      var shares = [];
      var entryPrice = [];
      var aumPercentage = [];
      var spyPercentage = [0.00];
      results.forEach(function(result) {
        tickers.push(result.ticker);
        startDates.push(result.startDate);
        shares.push(result.shares);
        entryPrice.push(result.entryPrice);
      });
      tickers.push('SPY');

      var oldestDate = findEarliestDate(startDates);
      startDates.push(oldestDate);

      var oldestTicker = tickers[startDates.indexOf(oldestDate)];

      getData(tickers, oldestDate).then((data) => {
        for (let ticker in data) {
            var adjClose = [];
            var dates = [];
            var idx = tickers.indexOf(ticker)
            for (var i = data[ticker].length - 1; i >= 0; i--) {
              adjClose.push(data[ticker][i].adjClose);
              dates.push(JSON.stringify(data[ticker][i].date).slice(1, 11));
            }

            var start = dates.indexOf(startDates[idx]);
            adjClose = adjClose.slice(start);

            js[ticker] = {
              shares: shares[idx],
              entryPrice: entryPrice[idx],
              entryDate: startDates[idx],
              data: adjClose,
              dates: dates
            };
        }

        for (var [ticker, value] of Object.entries(js)) {
          if (ticker != oldestTicker) {
            for (var i = value.data.length; i < js[oldestTicker].data.length; i++) {
              value.data.unshift(null);
            }
          }
        }

        // Update AUM
        for (let i = 0; i < js[oldestTicker].data.length; i++) {
          let addToAUM = 0;
          for (let [ticker, value] of Object.entries(js).slice(0, -1)) {
            let data = value.data;
            if (i == 0 && data[i] != null) {
              addToAUM += ((data[i] - value.entryPrice) * js[ticker].shares);
            } else {
              if (data[i] != null && data[i-1] != null) {
                addToAUM += ((data[i] - data[i-1]) * js[ticker].shares);
              }
            }
            addToAUM += (aum[aum.length - 1] - addToAUM) * 0.000038847;
          }
          aum.push(Number.parseFloat((aum[aum.length - 1] + addToAUM).toFixed(2)));
          aumDates.push(js[oldestTicker].dates[i]);
          if (i == 0) {aum.shift();}
        }

        // AUM percentage
        for (let i = 0; i < aum.length; i++) {
          aumPercentage.push(Number(((aum[i] - 100536.24) / 100536.24 * 100).toFixed(3)));
        }

        // SPY percentage
        for (let i = 1; i < js["SPY"].data.length; i++) {
          spyPercentage.push(Number(((js["SPY"].data[i] - js["SPY"].data[0]) / js["SPY"].data[0] * 100).toFixed(3)));
        }

        js["SPY"].spyPercentage = spyPercentage;

        js["AUM"] = {
          dates: aumDates,
          aum: aum,
          aumPercentage: aumPercentage
        }

        res.send(js);
      }).catch((err) => {
        res.send(err);
        console.log(err);
      });
    }
  });
});

app.get('/:ticker&:startDate&:startPrice&:shares', function(req, res) {
  const ticker = req.params.ticker.toUpperCase();
  const startDate = req.params.startDate;
  const startPrice = req.params.startPrice;
  const shares = req.params.shares;
  const today = new Date().toJSON().slice(0, 10);

  Equity.findOne({ticker: ticker}, function(err, foundList) {
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
        shares: shares
      });

      newPosition.save();

      res.send(`Successfully added ${ticker} to portfolio`);
    }
  });
});

app.get('/delete/:ticker', function(req, res) {
  const ticker = req.params.ticker.toUpperCase();
  Equity.deleteMany({ticker: ticker}, (err) => {
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

app.listen(port, function() {
  console.log(`Server started on port ${port}`);
});
