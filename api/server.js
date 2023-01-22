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

// console.log(aumDates);
// console.log(aum);
// const nov = [100865.52, 100313.09, 99671.21, 99804.43, 99971.61, 100115.46, 99644.79, 101062.00, 101525.29, 101416.57, 101588.03, 101460.39, 101548.17, 101727.74, 101323];
// for (var i = 0; i < nov.length; i++) {
//   aum.push(nov[i]);
// }



app.get("/getData", function(req, res) {

  const aumDates = ["2022-06-30","2022-07-05","2022-07-06","2022-07-07","2022-07-08","2022-07-11","2022-07-12","2022-07-13","2022-07-14","2022-07-15","2022-07-18","2022-07-19","2022-07-20","2022-07-21","2022-07-22","2022-07-25","2022-07-26","2022-07-27","2022-07-28","2022-07-29","2022-08-01","2022-08-02","2022-08-03","2022-08-04","2022-08-05","2022-08-08","2022-08-09","2022-08-10","2022-08-11","2022-08-12","2022-08-15","2022-08-16","2022-08-17","2022-08-18","2022-08-19","2022-08-22","2022-08-23","2022-08-24","2022-08-25","2022-08-26","2022-08-29","2022-08-30","2022-08-31","2022-09-01","2022-09-02","2022-09-06","2022-09-07","2022-09-08","2022-09-09","2022-09-12","2022-09-13","2022-09-14","2022-09-15","2022-09-16","2022-09-19","2022-09-20","2022-09-21","2022-09-22","2022-09-23","2022-09-26","2022-09-27","2022-09-28","2022-09-29","2022-09-30","2022-10-03","2022-10-04","2022-10-05"];


  const aum = [100059.06];

  for (var i = 0; i < 19; i++) {
    aum.push(Number.parseFloat((aum[aum.length - 1] * 1.000058847).toFixed(2)));
  }
  for (var i = 0; i < 23; i++) {
    aum.push(Number.parseFloat((aum[aum.length - 1] * 1.00006631).toFixed(2)));
  }
  for (var i = 0; i < 24; i++) {
    aum.push(Number.parseFloat((aum[aum.length - 1] * 1.000088122).toFixed(2)));
  }

  Equity.find({}, function(err, results) {
    if (err) {
      console.log(err);
      res.send(err);
    } else {
      var js = {};
      var tickers = [];
      var startDates = [];
      var shares = [];
      var entryPrice = [];
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
                // console.log(`${ticker}: ${addToAUM}`);
              }
            }
            addToAUM += (aum[aum.length - 1] - addToAUM) * 0.000058847;
          }
          // console.log(aum[aum.length - 1] + addToAUM);
          aum.push(Number.parseFloat((aum[aum.length - 1] + addToAUM).toFixed(2)));
          aumDates.push(js[oldestTicker].dates[i])
        }
        console.log(aum);
        console.log(aumDates);

        // for (let ticker in js) {
        //   if (ticker != "SPY") {
        //     let data = js[ticker].data;
        //     let dates = js[ticker].dates;
        //     for (let i = 0; i < data.length; i++) {
        //       if (data[i] != null) {
        //         console.log(data[i]);
        //       }
        //     }
        //   }
        // }

        js["AUM"] = {
          dates: aumDates,
          aum: aum
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
