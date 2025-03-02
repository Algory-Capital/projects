const fetch = require("node-fetch");

const sheetID = "1JOmzegYf0kGxDcjej0Fx_RCuFVoaOxobEnDsptjTJA8"
const sheetName = encodeURIComponent("Fund Dashboard")

/*
Fair warning
- this is very sensitive to human error, I will add better error handling/flow later but low priority
*/

function date_reformat(raw_date) {
  // converts date string from sheets to sheets into YYYY-MM-DD
  // Ex: 'Mon Dec 09 2024 00:00:00 GM'

  function pad_two(data) {
    return data.toString().padStart(2, "0")
  }

  const date = new Date(raw_date)

  console.log(raw_date.toString(), date, stringBeforeChar(raw_date))

  const mm = pad_two(date.getMonth() + 1); // plus 1 bc 0-indexed
  const dd = pad_two(date.getDay());
  const yyyy = pad_two(date.getFullYear());

  const ret = `${yyyy}-${mm}-${dd}`
  console.log("RET: ", ret)
  return ret;
}

// https://github.com/theotrain/load-google-sheet-data-using-sql/blob/main/getSheetData.js
const getSheetData = async ({ sheetID, sheetName, query, callback, first_cell = null, last_cell = null }) => {
    const base = `https://docs.google.com/spreadsheets/d/${sheetID}/gviz/tq?`;
    const url = `${base}&sheet=${encodeURIComponent(sheetName)}&tq=${encodeURIComponent(query)}`;
  
    const ret = await fetch(url)
      .then((res) => res.text())
      .then((response) => {
        // return value post-callback
        const ret = callback(responseToObjects(response));

        console.log("RET: ", ret)
        return ret;
      })
      .catch((err) => {
        console.error("Error fetching sheet data:", err);
        throw err;
      });
    
    return ret; // return post callback

    // helper function below (data parse into array)
  
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
        // console.log("sheet data (passed to equityDataHandler): ", sheetData);
        //Reformat objects to push to mongodb

        var output = []
        
        for (let i = 0; i < sheetData.length; i++)
        {
            let obj = sheetData[i];

            // console.log("sheet data object: ", obj)
            
            // WEAK POINT: cleaned up object (hard-coded so vulnerable)
            let obj_reformat = {
                "ticker": obj["$Ticker "].toUpperCase(),
                "startdate": date_reformat(obj["Entry Date"], "T"), // alt hardcode idx but this is cleaner
                "entryPrice": obj["Avg Cost"],
                "shares": obj["# of Shares"],
                "assetclass": "E",
                // data:,
                // dates:,
            }

            output.push(obj_reformat);
        }

        console.log("Equity Data Handler Output: ", output);
        
        return output;
      };
    
      const ret = await getSheetData({
        // sheetID you can find in the URL of your spreadsheet after "spreadsheet/d/"
        sheetID: sheetID,
        // sheetName is the name of the TAB in your spreadsheet (default is "Sheet1")
        sheetName: sheetName,
        query: "SELECT E,F,G,H,I,J,K,L",
        callback: equityDataHandler,
      //   first_cell: "E2",
      //   last_cell: "L20"
      }).catch((err) => {
        console.error(err)
        return []
      });
      
      console.log("Output from getHoldingsSheets: ", ret)
      return ret
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
    str = str.toString(); // js things
    // console.log("str: ", str);
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