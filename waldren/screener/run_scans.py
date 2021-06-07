import psycopg2
import pandas as pd
from stock_scanners import SqueezeScanner
from setup_finder import Kristjan_Breakout

import sys
sys.path.append('/app/waldren/base')
from plotter import CandleStickPlotter
import td_db_client

def getDataBaseConnection():
        connection = psycopg2.connect(
            host='timescale',
            database='tradekit',
            user='tradekit',
            password='yourpassword',
        )
        return connection 


def testSqueeze():
    df = pd.read_pickle('/app/data/aapl_squeezescan.pickle')

    sq = SqueezeScanner()

    df = sq.scan(df)

    print(df.tail())

    # df.to_pickle('/app/data/aapl_squeezescan.pickle')

    sq.chart(df, 'AAPL')

def handle_result(df, stock):
    if  df['TTM_squeeze'].iloc[-1]:
        print(stock[1])
        print("---------")
        print(df.iloc[-1])
        print("***********************")
    
    # print ("{} - SQUEEZE: {}".format(stock[1], df['TTM_squeeze'].iloc[-1]) )

def pull_daily_and_scan(symbols):
    tdc = td_db_client.Client()
    sq = SqueezeScanner(date="datetime")

    period = tdc.get_year_period(1)
    i = 0 
    for s in symbols:
        if i > 1:
            break
        df = tdc.get_price_daily_history(s[1], period=period)
        df = sq.scan(df)
        if df is not None:
            handle_result(df, s)

def look_for_setup(df, s):
    bm = df.loc[(df['big_move']==1) | ((df['troughs']==1) & (df['growth'] < -0.001))]
    print(bm[['close','close_pct_chg', 'growth', 'peaks', 'troughs']])
    csp = CandleStickPlotter()
    csp.plot_basic(bm, 'XXII')

def search_daily_setup(symbols):
    tdc = td_db_client.Client()
    print("Using Kristjan Breakout Definition")
    kb = Kristjan_Breakout(date_col="datetime")
    period = tdc.get_year_period(1)
    i = 0  # debug
    for s in symbols:
        if i > 1:   # debug
            break
        df = tdc.get_price_daily_history(s[1], period=period)
        df = kb.scan(df)
        if df is not None:
            print("Looking for setups...")
            look_for_setup(df, s)
        i += 1  # debug

def get_symbols():
    query = "SELECT id, symbol FROM stock WHERE symbol NOT SIMILAR TO %s AND exchange = %s AND sector = %s"  
    param = ('%(\^|/)%','NYSE','Health Care',)
    tdc = td_db_client.Client()
    return tdc.run_select_query_with_param(query, param)

def main():
    # symbols = get_symbols()
    symbols = [(1, 'XXII')]
    print("{} symbols to be processes.".format(len(symbols)))
    # testSqueeze()
    # pull_daily_and_scan(symbols)
    search_daily_setup(symbols)

if __name__ == "__main__":
    main()



# with con.cursor(name='custom_cursor') as cursor:
#      cursor.itersize = 1000 # chunk size
#      query = 'SELECT * FROM mytbale;'
#      cursor.execute(query)
#      for row in cursor:
#          print(row)