from tda import auth, client
#from tda.orders import EquityOrderBuilder, Duration, Session
import json
import CONFIG as config
import datetime
from datetime import timedelta
import pandas as pd 
import os
import sys 
import psycopg2

class Client:
    def __init__(self, config=config):
        self.config = config
        self.td = self.authenticate_tda()
        self.conn = self.getDataBaseConnection()
        

    # authenticate to TD Ameritrade API
    def authenticate_tda(self):
        try:
            return auth.client_from_token_file(self.config.TOKEN_PATH, self.config.API_KEY)
        except FileNotFoundError:
            from selenium import webdriver
            with webdriver.Chrome(executable_path=self.config.CHROME_DRIVER_PATH) as driver:
                return auth.client_from_login_flow(
                    driver, self.config.API_KEY, self.config.REDIRECT_URL, self.config.TOKEN_PATH)
    
    #Establish DB Connection
    def getDataBaseConnection(self):
        connection = psycopg2.connect(
            host=self.config.DB_HOST,
            database=self.config.DATABASE,
            user=self.config.DB_USER,
            password=self.config.DB_PASSWORD,
        )
        return connection 

    def get_freq_type_str(self, frequency_type):
        if frequency_type == client.Client.PriceHistory.FrequencyType.DAILY:
            return 'daily'
        if frequency_type == client.Client.PriceHistory.FrequencyType.MINUTE:
            return 'minute'
        if frequency_type == client.Client.PriceHistory.FrequencyType.WEEKLY:
            return 'weekly'
        if frequency_type == client.Client.PriceHistory.FrequencyType.MONTHLY:
            return 'monthly'
        return 'other'
    
    def get_year_period(self, years):
        if years == 1:
            return client.Client.PriceHistory.Period.ONE_YEAR
        elif years == 2:
            return client.Client.PriceHistory.Period.TWO_YEARS
        elif years == 3:
            return client.Client.PriceHistory.Period.THREE_YEARS
        elif years == 5:
            return client.Client.PriceHistory.Period.FIFTEEN_YEARS
        elif years == 10:
            return client.Client.PriceHistory.Period.TEN_YEARS
        elif years == 15:
            return client.Client.PriceHistory.Period.FIFTEEN_YEARS
        elif years == 20:
            return client.Client.PriceHistory.Period.TWO_YEARS
        else:
            print("year must be an integer in (1, 2, 3, 5, 10, 15, 20")

    def convert_symbol_price_hx_todataframe(self, res):
        if res['empty'] == True:
            print("****Empty result****")
            return pd.DataFrame()
        
        rows_list = []
        #df = pd.DataFrame(columns = ['datetime', 'open', 'high', 'low', 'close','volume']) 
        for row in res['candles']:
            rows_list.append(row)
        df = pd.DataFrame(rows_list)[['datetime', 'open', 'high', 'low', 'close','volume']]

        df['datetime'] = pd.to_datetime(df['datetime'], unit='ms', utc=True)
        df.set_index('datetime', inplace=True, drop=True)
        return df

    def get_price_history(self, **kwargs):
        # call the TD API and grab the json
        r = self.td.get_price_history(**kwargs)
        j = r.json()

        # Make sure there are candles to know that it is not an error
        if 'candles' not in j:
            print("**** No Candles in Result****")
            print(r.json())
            return pd.DataFrame()
        # If there are candles, make sure the result is not empty
        if j['empty'] == True:
            print("****Empty result****")
            return pd.DataFrame()

        # get the dataframe from the candles and save the dataframe as a CSV file
        df = self.convert_symbol_price_hx_todataframe(j)
        return df 
    
    def get_fundamentals(self, symbol):
        r = self.td.search_instruments(symbol, client.Client.Instrument.Projection.FUNDAMENTAL)
        j = r.json()
        try:
            fund = j[symbol]['fundamental']
            fund['datetime'] = datetime.datetime.now()
        except:
            try:
                # We have have sent too many API calls, stop the program
                if j['error'] == "Individual App\'s transactions per seconds restriction reached. Please contact us with further questions":
                    sys.exit(1)
            except:
                # Must have been another error, print the JSON and then set fund to None
                print("ERROR=============")
                print(j) 
                print("==================")
                fund = None
        return fund

    '''
    Function to get a standand intraday candles for every 5 minutes for the supplied period. Period type 
    is `DAY`
    '''
    def get_price_intraday_history(self, symbol, period=client.Client.PriceHistory.Period.THREE_MONTHS):
        
        period_type=client.Client.PriceHistory.PeriodType.DAY
        frequency_type=client.Client.PriceHistory.FrequencyType.MINUTE
        frequency=client.Client.PriceHistory.Frequency.EVERY_FIVE_MINUTES
        return self.get_price_history(symbol=symbol,period_type=period_type,period=period,frequency_type=frequency_type,frequency=frequency)

    '''
    Function to get a standand daily candles for the supplied period. Period type 
    is `YEAR`
    '''
    def get_price_daily_history(self, symbol, period=client.Client.PriceHistory.Period.TWENTY_YEARS):

        period_type=client.Client.PriceHistory.PeriodType.YEAR
        frequency_type=client.Client.PriceHistory.FrequencyType.DAILY
        frequency=client.Client.PriceHistory.Frequency.DAILY
        return self.get_price_history(symbol=symbol,period_type=period_type,period=period,frequency_type=frequency_type,frequency=frequency)

    def get_standard_5min_price_history(self, start_datetime, symbol):
        frequency_type=client.Client.PriceHistory.FrequencyType.MINUTE
        frequency=client.Client.PriceHistory.Frequency.EVERY_FIVE_MINUTES
        
        end_datetime = datetime.datetime.now()

        return self.get_price_history(symbol=symbol,end_datetime=end_datetime, start_datetime=start_datetime,frequency_type=frequency_type,frequency=frequency)


    '''
    Database Functions
    '''

    ''' 
    Run a select query and get back a rowset
    '''
    def run_select_query(self, query):
        cursor = self.conn.cursor()
        cursor.execute(query)
        row = cursor.fetchall()
        cursor.close()
        return row 
    
    '''
    Run a select query with a parameter and get back a rowset
    '''
    def run_select_query_with_param(self, query, param):
        cursor = self.conn.cursor()
        cursor.execute(query, param)
        row = cursor.fetchall()
        if len(row) == 0:
            print("There are no results for this query")
        cursor.close()
        return row 

    '''
    Returns a list of tuples (stock_id, symbol). If exchance provided, it will limit stocks to only from that exchange.
        When includevariants is False is will exclude stocks symbols for stock variants (ie. AVD^C)
    '''
    def get_stocks_id_symbol(self, exchange=None, includevariants=False):
        cursor = self.conn.cursor()

        if exchange is None:
            if not includevariants:
                cursor.execute("SELECT id, symbol FROM stock WHERE symbol NOT SIMILAR TO %s ", ('%(\^|/)%',))
            else:
                cursor.execute("SELECT id, symbol FROM stock")
        else:
            if not includevariants:
                cursor.execute("SELECT id, symbol FROM stock WHERE symbol NOT SIMILAR TO %s AND exchange = %s", ('%(\^|/)%',exchange,))
            else:
                cursor.execute("SELECT id, symbol FROM stock WHERE exchange = %s", (exchange,))
        stocks = []
        rows = cursor.fetchall()
        for row in rows:
            stocks.append((row[0], row[1]))
        
        cursor.close()
        return stocks
    
    '''
    Save the JSON fundamentals from TD Ameritrade API for a stock. stock_id is the primary key for the stock in the database.
    '''
    def save_fundamentals(self, stock_id, fund):
        if fund is None:
            print("No Fundamentals json provided")
        else:
            cursor = self.conn.cursor()
            query_insert = "INSERT INTO stock_fundamental (dt, stock_id, fundamental_id, val) VALUES (%s,%s,%s,%s)"
            dt = fund['datetime']
            keys = fund.keys()
            for k in keys:
                if k not in ['datetime', 'symbol', 'dividendDate', 'dividendPayDate']:
                    cursor.execute(query_getfund, (k,))
                    r = cursor.fetchone()
                    if r is not None:
                        cursor.execute(query_insert, (dt, stock_id, r[0], fund[k]))
                    else:
                        print("{} symbol not found in fundamental table".format(k))
            self.conn.commit()
            cursor.close()

    def save_price_history(self, stock_id, start_datetime, symbol):
        cursor = self.conn.cursor()
        df = self.get_standard_5min_price_history(start_datetime, symbol)
        query_insert = "INSERT INTO ohlc_data (dt, stock_id, open, high, low, close, volume ) VALUES(%s, %s, %s, %s, %s, %s, %s)"
        for index, r in df.iterrows():
            cursor.execute(query_insert, (r.name, stock_id, r['open'],r['high'],r['low'],r['close'],r['volume'],))
        self.conn.commit()
        cursor.close()
    