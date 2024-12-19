const sheetID = "1JOmzegYf0kGxDcjej0Fx_RCuFVoaOxobEnDsptjTJA8"
const sheetName = encodeURIComponent("Fund Dashboard")

/*
Fair warning
- this is very sensitive to human error, I will add better error handling/flow later but low priority
*/


// https://github.com/theotrain/load-google-sheet-data-using-sql/blob/main/getSheetData.js
const getSheetData = async ({ sheetID, sheetName, query, callback, first_cell = null, last_cell = null }) => {
    const base = `https://docs.google.com/spreadsheets/d/${sheetID}/gviz/tq?`;
    const url = `${base}&sheet=${encodeURIComponent(sheetName)}&tq=${encodeURIComponent(query)}`;
  
    await fetch(url)
      .then((res) => res.text())
      .then((response) => {
        // return value post-callback
        return callback(responseToObjects(response));
      });
  
    function responseToObjects(res) {
      const jsData = JSON.parse(res.substring(47).slice(0, -2));
      const data = [];
      const columns = jsData.table.cols;
      const rows = jsData.table.rows;
  
      // Create bounds
      const colMax = last_cell === null ? columns.length : Number(last_cell.substring(1)) + 1;
      const rowMax = last_cell === null ? rows.length : Number(last_cell.substring(0, 1).charCodeAt(0) - 65) + 1;
  
      const colStart = first_cell === null ? 0 : Number(first_cell.substring(1));
      const rowStart = first_cell === null ? 0 : Number(first_cell.substring(0, 1).charCodeAt(0) - 65);
  
      for (let r = rowStart; r < Math.min(rowMax, rows.length); r++) {
        const rowObject = {};
        for (let c = colStart; c < Math.min(colMax, columns.length); c++) {
          const cellData = rows[r]?.c[c];
          const propName = columns[c]?.label || `Column ${c}`;
          if (cellData === null) {
            rowObject[propName] = "";
          } else if (typeof cellData.v === "string" && cellData.v.startsWith("Date")) {
            rowObject[propName] = new Date(cellData.f);
          } else {
            rowObject[propName] = cellData.v;
          }
        }
        data.push(rowObject);
      }
      return data;
    }
  };
  // end helper function "getSheetData"

  // begin main functions

  async function getHoldingsSheets()
  {
    // get holdings
    // callback
    const equityDataHandler = (sheetData) => {   
        console.log("sheet data (passed to equityDataHandler): ", sheetData);
        //Reformat objects to push to mongodb

        var output = []
        
        for (let i = 0; i < sheetData.length; i++)
        {
            let obj = sheetData[i];

            let obj_reformat = {
                "ticker": sheetData["$Ticker "].toUpperCase(),
                "startDate": stringBeforeChar(sheetData["Entry Date"], "T"), // alt hardcode idx but this is cleaner
                "entryPrice": sheetData["Avg Cost"],
                "shares": sheetData["# of Shares"],
                "assetClass": "E",
                // data:,
                // dates:,
            }

            output.push(obj_reformat);
        }

        console.log("Equity Data Handler Output: ", output);
        
        return output;
      };
    
      getSheetData({
        // sheetID you can find in the URL of your spreadsheet after "spreadsheet/d/"
        sheetID: sheetID,
        // sheetName is the name of the TAB in your spreadsheet (default is "Sheet1")
        sheetName: sheetName,
        query: "SELECT E,F,G,H,I,J,K,L",
        callback: equityDataHandler,
      //   first_cell: "E2",
      //   last_cell: "L20"
      });

  }

  function getSummarySheets()
  {
    
  }

  function getCashSheets()
  {

  }

  async function getAUMFromSheets()
  {

    const aumDataHandler = (sheetData) => {   
        console.log("sheet data (passed to aumDataHandler): ", sheetData);
        //Reformat objects to push to mongodb
        try {
            // This may a risky point code may break
            // But it seems sheets query doesn't allow SELECT AS
            const output = sheetData[0]["Column 0"]

            return output
        } catch (error) {
            console.error("FAILED AUM SHEETS FETCH. DATA MAY HAVE BEEN MOVED OR IS INVALID", error)
        }

        return null;
      };
    
    getSheetData({
        // sheetID you can find in the URL of your spreadsheet after "spreadsheet/d/"
        sheetID: sheetID,
        // sheetName is the name of the TAB in your spreadsheet (default is "Sheet1")
        sheetName: sheetName,
        query: "SELECT C WHERE B = 'AUM'",
        callback: sheetDataHandler,
      //   first_cell: "E2",
      //   last_cell: "L20"
      });
  }

  // general util
  function stringBeforeChar(str, char)
  {
    const index = str.indexOf(char);
    
    if (index !== -1) {
        const substring = str.substring(0, index);
        return substring;
    }

    console.error("stringBeforeChar failed: ", str, char);
    return str;
  }

  module.exports = {
    getHoldingsSheets,
  };