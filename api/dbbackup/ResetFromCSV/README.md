### Hard Reset in Python

aliases.json: hold ticker aliases for Activity Logs

## Relevant Excel

``
=CONCAT(CHAR(34), NAME, CHAR(34), " : ", CHAR(34), TKR, CHAR(34), ",",CHAR(13))
``

``
F9
``

## Handling Excel Spreadsheet Data

> [!NOTE]
> `BLACKROCK TREASURY TRUST INSTL 10` represents cash

> [!WARNING]
> We have never exercised ITM calls/options, so lumping them with Buy/Sell for now

- Transaction Type
    - Buy, Sell, Dividend
- Actual Settle Date
    - When we record transaction
- Units: quantity
- Amount: Total amount
    - Calculate price per unit/share

To Do
- Holdings methods in child classes from masters, calculate AUM
    - We only handle cash for now
- Figure out if possible to get options price daily
- Options
    - AUM calculation?
    - String parsing - replace hardcoded options json with string fmt json (optional)
- PushMongoDB class