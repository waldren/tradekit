# Hack to be able to import across /app/waldren
import sys
sys.path.append('/app/waldren/base')

import TDClient
from tda import client
import os, pandas
import talib
import psycopg2

def is_consolidating(df, percentage=2):
    recent_candlesticks = df[-15:]
    
    max_close = recent_candlesticks['Close'].max()
    min_close = recent_candlesticks['Close'].min()

    threshold = 1 - (percentage / 100)
    if min_close > (max_close * threshold):
        return True        

    return False

def is_breaking_out(df, percentage=2.5):
    last_close = df[-1:]['Close'].values[0]

    if is_consolidating(df[:-1], percentage=percentage):
        recent_closes = df[-16:-1]

        if last_close > recent_closes['Close'].max():
            return True

    return False

def main():
    connection = psycopg2.connect(
        host="timescale",
        database="tradekit",
        user="tradekit",
        password="yourpassword",
    )

    cursor = connection.cursor()
    cursor.execute ("SELECT symbol, name FROM indicators")
    rows = cursor.fetchall()
    cdl_patterns = []
    for row in rows:
        cdl_patterns.append( (row[0], row[1]) )
    
    tc = TDClient.TDClient()
    df = tc.get_price_daily_history('AAPL', period=client.Client.PriceHistory.Period.TEN_DAYS)
    print(df.head())

    for pat in cdl_patterns:
        pattern_function = getattr(talib, pat[0])

        results = pattern_function(df['open'], df['high'], df['low'], df['close'])
        last = results.tail(1).values[0]

        if last > 0:
            print("{} is bullish".format(pat[1]))
        elif last < 0:
            print("{} is bullish".format(pat[1]))

    cursor.close()
    connection.close()

if __name__ == "__main__":
    main()
    

