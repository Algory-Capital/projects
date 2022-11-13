const mongoose = require("mongoose");
const express = require("express");
const bodyParser = require("body-parser");
const _ = require("lodash");
const yfin = require("yahoo-finance");
const axios = require('axios');

const app = express();

app.set('view engine', 'ejs');

app.use(bodyParser.urlencoded({extended: true}));
app.use(express.static("public"));

mongoose.connect("mongodb+srv://admin:admin123@cluster0.ftlnrsd.mongodb.net/algoryPortDB");

const equitiesSchema = {
  ticker: String,
  startDate: String,
  entryPrice: Number
};

const Equity = mongoose.model("Equity", equitiesSchema);

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
      var js = [];
      var tickers = [];
      var startDates = [];
      results.forEach(function(result) {
        tickers.push(result.ticker);
        startDates.push(result.startDate);
      });

      oldestDate = startDates.sort((a, b) => {
        return Date.parse(a) > Date.parse(b);
      })[0];

      getData(tickers, oldestDate).then((data) => {
        for (let ticker in data) {
            var adjClose = [];
            var dates = [];
            var idx = tickers.indexOf(ticker)
            for (var i = data[ticker].length - 1; i >= 0; i--) {
              adjClose.push(data[ticker][i].adjClose);
              dates.push(JSON.stringify(data[ticker][i].date).slice(1, 11));
            }

            var start = dates.indexOf(startDates[idx])
            adjClose = adjClose.slice(start);
            dates = dates.slice(start);

            js.push({
              ticker: ticker,
              data: adjClose,
              dates: dates
            });
        }
        res.send(js);
      }).catch((err) => {
        console.log(err);
      });
    }
  });
});

app.get('/:ticker&:startDate&:startPrice', function(req, res) {
  const ticker = req.params.ticker.toUpperCase();
  const startDate = req.params.startDate;
  const startPrice = req.params.startPrice;
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
        entryPrice: startPrice
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
