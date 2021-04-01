# Load the Stock database from TD Ameritrade
import CONFIG as config
import TDClient
import psycopg2
import pandas as pd
import json
from  TDClient import TDClient
import time

def load_stocks(cursor):
    exchanges = {'nasdaq', 'nyse', 'amex'}
    for ex in exchanges:
        df = pd.read_csv('/app/data/{}_stocks.csv'.format(ex))
        load_exchange(ex.upper(), df, cursor)

def load_exchange(exchange, df, cursor):
    query_insert = "INSERT INTO stock (symbol, name, sector, industry, exchange) VALUES(%s, %s, %s, %s, %s)"
    for index, c in df.iterrows():
        cursor.execute(query_insert, (c.Symbol,c.Name,c.Sector,c.Industry, exchange) )
        if index % 100 == 0:
            print("{} loaded so far...".format(index))
    print("{} {} Stocks loaded".format(index, exchange))

def load_fundamental(cursor):
    query_insert = "INSERT INTO fundamental (symbol, name, description, useage) VALUES(%s,%s,%s,%s)"
    with open('/app/data/fundamentals.json') as f:
        fjson = json.load(f)
        for symbol in fjson:
            defin = ""
            use = ""

            if 'def' in fjson[symbol]:
                defin = fjson[symbol]['def']
            if 'use' in fjson[symbol]:
                use = fjson[symbol]['use']

            cursor.execute(query_insert, (symbol, fjson[symbol]['name'], defin, use))

def get_stock_id_symbol(cursor, exchange):
    cursor.execute("SELECT id, symbol FROM stock WHERE symbol  NOT SIMILAR TO %s AND exchange = %s", ('%(\^|/)%',exchange,))
    stocks = []
    rows = cursor.fetchall()
    for row in rows:
        stocks.append((row[0], row[1]))
    return stocks

def get_fundamental_id_symbol(cursor):
    cursor.execute("SELECT id, symbol FROM fundamental")
    funds = []
    rows = cursor.fetchall()
    for row in rows:
        funds.append((row[0], row[1]))
    return funds

def load_latest_fundamentals(cursor, stock_list):
    tc = TDClient()

    query_insert = "INSERT INTO stock_fundamental (dt, stock_id, fundamental_id, val) VALUES (%s,%s,%s,%s)"
    query_getfund = "SELECT id FROM fundamental WHERE symbol=%s"
    i = 0
    for s in stock_list:
        # Skip different stock classes
        if '^' in s[1]:
            continue 
        i += 1
        # throttling
        if i % 220 == 0:
            print ("Sleeping for 30 sec...")
            time.sleep(30)
            print("Loading {}...".format(i))
        elif i % 120 == 0:
            print ("Sleeping for 15 sec...")
            time.sleep(15)
            print("Loading {}...".format(i))
        elif i % 10 == 0:
            print("Loading {}...".format(i))
            # time.sleep(2)
           

        fund = tc.get_fundamentals(s[1])
        if fund is None:
            print("No Fundamentals found for: {}".format(s[1]))
        else:
            dt = fund['datetime']
            keys = fund.keys()
            for k in keys:
                if k not in ['datetime', 'symbol', 'dividendDate', 'dividendPayDate']:
                    cursor.execute(query_getfund, (k,))
                    r = cursor.fetchone()
                    if r is not None:
                        cursor.execute(query_insert, (dt, s[0], r[0], fund[k]))
                    else:
                        print("{} symbol not found in fundamental table".format(k))


def main():
    connection = psycopg2.connect(
        host="timescale",
        database="tradekit",
        user="tradekit",
        password="yourpassword",
    )

    cursor = connection.cursor()
    
    load_stocks(cursor)
    connection.commit()

    # load_fundamental(cursor)
    # connection.commit()
    '''
    exchange = "AMEX"
    stocks = get_stock_id_symbol(cursor, exchange)
    batch_size = 100
    b = 0
    while b < len(stocks)-batch_size:
        print("b: {} batch".format(b))
        load_latest_fundamentals(cursor, stocks[b:b+batch_size+1])
        connection.commit()
        b = batch_size + b 
        print("Sleeping 60 secs....")
        time.sleep(60)
        print("Resuming....")
    print("{} Completed in exchange: {}".format(len(stocks), exchange))
    '''
    
    cursor.close()
    connection.close()

if __name__ == "__main__":
    main()
