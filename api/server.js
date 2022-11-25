const mongoose = require("mongoose");
const express = require("express");
const bodyParser = require("body-parser");
const _ = require("lodash");
const yfin = require("yahoo-finance");
const axios = require('axios');
const cors = require("cors");

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

const aumDates = ["2022-06-30","2022-07-01","2022-07-05","2022-07-06","2022-07-07","2022-07-08","2022-07-11","2022-07-12","2022-07-13","2022-07-14","2022-07-15","2022-07-18","2022-07-19","2022-07-20","2022-07-21","2022-07-22","2022-07-25","2022-07-26","2022-07-27","2022-07-28","2022-07-29","2022-08-01","2022-08-02","2022-08-03","2022-08-04","2022-08-05","2022-08-08","2022-08-09","2022-08-10","2022-08-11","2022-08-12","2022-08-15","2022-08-16","2022-08-17","2022-08-18","2022-08-19","2022-08-22","2022-08-23","2022-08-24","2022-08-25","2022-08-26","2022-08-29","2022-08-30","2022-08-31","2022-09-01","2022-09-02","2022-09-06","2022-09-07","2022-09-08","2022-09-09","2022-09-12","2022-09-13","2022-09-14","2022-09-15","2022-09-16","2022-09-19","2022-09-20","2022-09-21","2022-09-22","2022-09-23","2022-09-26","2022-09-27","2022-09-28","2022-09-29","2022-09-30","2022-10-03","2022-10-04","2022-10-05","2022-10-06","2022-10-07","2022-10-10","2022-10-11","2022-10-12","2022-10-13","2022-10-14","2022-10-17","2022-10-18","2022-10-19","2022-10-20","2022-10-21","2022-10-24","2022-10-25","2022-10-26","2022-10-27","2022-10-28","2022-10-31","2022-11-01","2022-11-02","2022-11-03","2022-11-04","2022-11-07","2022-11-08","2022-11-09","2022-11-10","2022-11-11","2022-11-14","2022-11-15","2022-11-16","2022-11-17", "2022-11-18"];


const aum = [100056.78, 100059.06];

for (var i = 0; i < 19; i++) {
  aum.push(aum[aum.length - 1] * 1.000058847);
}
for (var i = 0; i < 23; i++) {
  aum.push(aum[aum.length - 1] * 1.00006631);
}
for (var i = 0; i < 21; i++) {
  aum.push(aum[aum.length - 1] * 1.000088122);
}
for (var i = 0; i < 21; i++) {
  aum.push(aum[aum.length - 1] * 1.00027649);
}
const nov = [100865.52, 100313.09, 99671.21, 99804.43, 99971.61, 100115.46, 99644.79, 101062.00, 101525.29, 101416.57, 101588.03, 101460.39, 101548.17, 101727.74];
for (var i = 0; i < nov.length; i++) {
  aum.push(nov[i]);
}

console.log(aumDates.length);
console.log(aum.length);



app.get("/getData", function(req, res) {

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

      var oldestDate = findEarliestDate(startDates);

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

        var temp = js[oldestTicker];
        if (aumDates[aumDates.length - 1] != temp.dates[temp.dates.length - 1]) {
          aumDates.push(temp.dates[temp.dates.length - 1])
          var lastAUM = aum[aum.length - 1];
          for (var [ticker, value] of Object.entries(js)) {
            lastAUM += (value.data[value.data.length - 1] - value.data[value.data.length - 2]) * value.shares;
          }
          lastAUM = lastAUM * 1.00007412;
          aum.push(lastAUM);
        }

        js["AUM"] = {
          dates: aumDates,
          aum: aum
        }

        res.send(js);
      }).catch((err) => {
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
