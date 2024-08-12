# Hard Reset Data in Python From Excel Transaction Logs

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
> Cash transactions are separated from counterpart changes in equities, cash from dividends, options. We use these to modify holdings or simply for logging
> Drastic bumps in prices come from difference between price order is placed vs order execution
    > We are charged price when order placed

> [!WARNING]
> We have never exercised ITM calls/options, so lumping them with Buy/Sell for now
> Do not have options pricing implemented (which will underestimate AUM)

- Transaction Type
    - Buy, Sell, Dividend
- Actual Settle Date
    - When we record transaction
- Units: quantity
- Amount: Total amount
    - Calculate price per unit/share
- Settlement Policy
    - Actual
        - Sale of Options contracts (QQQ, SPY, VIX)
    - Un-projected Actual
        - Blackrock Treasury (cash)
- Transaction Description
    - Purchase
        - Purchase-Cash Equivalent (STF)
        - Purchase
        - Purchase-Mutual Fund Order
        - Buy of Put/Call
    - Sale
        - Sale
        - Sale-Cash Equivalent(STF)
        - Closing Sale (Write) of Put/Call
        - Sale - Future
        - Sale-Mutual Fund Order
    - Dividend
        - Note: Every dividend is credited towards Blackrock Treasury with equivalent Buy debit for some reason

To Do
- Holdings methods in child classes from masters, calculate AUM
    - We only handle cash for now
- Figure out if possible to get options price daily
- Options
    - AUM calculation?
    - String parsing - replace hardcoded options json with string fmt json (optional)
- Include commission
- PushMongoDB class
