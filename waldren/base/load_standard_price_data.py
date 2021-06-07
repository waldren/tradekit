from td_db_client import Client
import pandas as pd
import datetime
import time


tdc = Client()
symbol = 'AAPL'

query_stocks = "SELECT stock.id, stock.symbol FROM stock WHERE stock.sector IN ('Technology', 'Health Care') AND stock.id NOT IN (SELECT DISTINCT stock_id FROM ohlc_data) AND symbol NOT SIMILAR TO %s"

# Get the list of stocks
stocks = tdc.run_select_query_with_param(query_stocks, '%(\^|/)%')
sdt = datetime.datetime(year=2020, month=12, day=1)
i = 1
for s in stocks:
    print ("Saving price history for {}".format(s[1]))
    tdc.save_price_history(s[0], sdt, s[1])
    i += 1