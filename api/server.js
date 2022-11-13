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

async function getData(ticker, startDate) {
  const today = new Date().toJSON().slice(0, 10);

  const myData = yfin.historical({
    symbol: ticker,
    from: startDate,
    to: today,
    period: 'd'
  }, function (err, quotes) {
    if (err) {
      res.send(err);
    }
  });
  return myData;
}

app.get("/getData", function(req, res) {

  Equity.find({}, function(err, results) {
    if (err) {
      console.log(err);
      res.send(err);
    } else {
      var js = [];
      results.forEach(function(result) {
        getData(result.ticker, result.startDate).then((data) => {
          var adjClose = [];
          var dates = [];
          for (var i = data.length - 1; i >= 0; i--) {
            adjClose.push(data[i].adjClose);
            dates.push(JSON.stringify(data[i].date).slice(1, 11));
          }
          js.push({
            ticker: result.ticker,
            data: adjClose,
            dates: dates
          });
          console.log(js);
        }).catch((err) => {
          console.log(err);
        });
      });
      console.log(js);
      // var ticker = results[0].ticker;
      // var startDate = results[0].startDate;
      // var today = new Date().toJSON().slice(0, 10);
      // yfin.historical({
      //   symbol: ticker,
      //   from: startDate,
      //   to: today,
      //   period: 'd'
      // }, function (err, quotes) {
      //   if (err) {
      //     res.send(err);
      //   } else {
      //     var data = [];
      //     var dates = [];
      //     for (var i = quotes.length - 1; i >= 0; i--) {
      //       data.push(quotes[i].adjClose);
      //       dates.push(JSON.stringify(quotes[i].date).slice(1, 11));
      //     }
      //
      //     res.send({
      //       ticker: ticker,
      //       data: data,
      //       dates: dates
      //     });
      //   }
      // });
      res.send(js);
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

app.post('/delete/:ticker', function(req, res) {
  const ticker = req.body.ticker;


});

app.listen(3000, function() {
  console.log("Server started on port 3000");
});



// async function test() {
//   await axios.get("http://localhost:3000/getData").then((res) => {
//     console.log(res);
//   }).catch((err) => {
//     console.log(err);
//   });
// };
// test();
