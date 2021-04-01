import pandas as pd
import time
from stock_processor import SqueezeProcessor

import sys
sys.path.append('/app/waldren/base')
from plotter import CandleStickPlotter
import td_db_client

tc = td_db_client.Client()

df_spy = tc.get_price_daily_history('SPY')
df_nasdaq = tc.get_price_daily_history('QQQ')
df_dji = tc.get_price_daily_history('$DJI')
df_vix = tc.get_price_daily_history('VIX')

def merge_index(df_stock, df_index, suffix):
    return df_stock.merge(df_index, how='left', left_index=True, right_index=True, suffixes=('',suffix) )


sp = SqueezeProcessor(date='datetime', data_folder='./data/training', breakout_threshold=0.20, breakout_duration=10, 
                        keltner_multiplier=2.0, indices=['close_spy','close_qqq','close_dji','close_vix'])

filepath = './data/stocks.txt'
with open(filepath) as fp:
   line = fp.readline()
   cnt = 1
   while line:
        symbol = line.strip()

        df = tc.get_price_daily_history(symbol)
        df = merge_index(df, df_spy['close'], '_spy')
        df = merge_index(df, df_nasdaq['close'], '_qqq')
        df = merge_index(df, df_dji['close'], '_dji')
        df = merge_index(df, df_vix['close'], '_vix')
        sp_df = sp.process(df, symbol=symbol)
        sp.create_squeeze_samples(sp_df)
        if cnt % 100 == 0:
            time.sleep(30)
        line = fp.readline()
        cnt += 1