from tda import auth, client
#from tda.orders import EquityOrderBuilder, Duration, Session
import json
import CONFIG as config
import datetime
from datetime import timedelta
import pandas as pd 
import os
import sys 

class TDClient:
    def __init__(self, config=config):
        self.c = self.authenticate(config)
        self.config = config

    # authenticate
    def authenticate(self, config):
        try:
            return auth.client_from_token_file(config.TOKEN_PATH, config.API_KEY)
        except FileNotFoundError:
            from selenium import webdriver
            with webdriver.Chrome(executable_path=config.CHROME_DRIVER_PATH) as driver:
                return auth.client_from_login_flow(
                    driver, config.API_KEY, config.REDIRECT_URL, config.TOKEN_PATH)

    def convert_symbol_price_hx_todataframe(self, res):
        if res['empty'] == True:
            print("****Empty result****")
            return pd.DataFrame()
        
        rows_list = []
        #df = pd.DataFrame(columns = ['datetime', 'open', 'high', 'low', 'close','volume']) 
        for row in res['candles']:
            rows_list.append(row)
        df = pd.DataFrame(rows_list)[['datetime', 'open', 'high', 'low', 'close','volume']]
        df['openinterest'] = 0
        df['datetime'] = pd.to_datetime(df['datetime'], unit='ms', utc=True)
        df.set_index('datetime', inplace=True, drop=True)
        return df

    '''
    Function to get a standand daily candles for the supplied period. Period type 
    is `YEAR`
    '''
    def get_price_daily_history(self, symbol, period=client.Client.PriceHistory.Period.TWENTY_YEARS, save=False):

        period_type=client.Client.PriceHistory.PeriodType.YEAR
        frequency_type=client.Client.PriceHistory.FrequencyType.DAILY
        frequency=client.Client.PriceHistory.Frequency.DAILY
        if save:
            return self.get_save_price_history(symbol=symbol,period_type=period_type,period=period,frequency_type=frequency_type,frequency=frequency)
        else:
            return self.get_price_history(symbol=symbol,period_type=period_type,period=period,frequency_type=frequency_type,frequency=frequency)


    '''
    Function to get a standand intraday candles for every minute for the supplied period. Period type 
    is `DAY`
    '''
    def get_price_intraday_history(self, symbol, period=client.Client.PriceHistory.Period.THREE_MONTHS):
        
        period_type=client.Client.PriceHistory.PeriodType.DAY
        frequency_type=client.Client.PriceHistory.FrequencyType.MINUTE
        frequency=client.Client.PriceHistory.Frequency.EVERY_MINUTE
        # end_datetime=end_datetime, start_datetime=start_datetime,
        return self.get_save_price_history(symbol=symbol, period_type=period_type, period=period, frequency_type=frequency_type,frequency=frequency)

    def get_price_history(self, **kwargs):
        # call the TD API and grab the json
        r = self.c.get_price_history(**kwargs)
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
    
    def get_save_price_history(self, **kwargs):
        df = self.get_price_history(self, **kwargs)

        ftype = self.get_freq_type_str(kwargs['frequency_type'])
        # create a folder structure so each symbol has its own folder with some foler for each frequency type
        outpath = '{}/{}/{}'.format(config.DATA_PATH, kwargs['symbol'], ftype)
        os.makedirs(outpath, exist_ok=True)
        # this is the date format for the file name (endDate_startDate)
        dtfrmt = "%Y-%m-%dT%H%M%S"
        filename = '{}_daily_{}_{}'.format(kwargs['symbol'], df.index[0].strftime(dtfrmt), df.index[-1].strftime(dtfrmt))
        path = os.path.join(outpath, filename)
        # this is the format for the default datetime in backtrader (time is in UTC)
        zfrmt = "%Y-%m-%d %H:%M:%S"
        df.to_csv(path, date_format=zfrmt)
        r.close()
        return df
    
    def get_fundamentals(self, symbol):
        r = self.c.search_instruments(symbol, client.Client.Instrument.Projection.FUNDAMENTAL)
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

    def get_save_fundamentals(self, symbol):
        fund = self.get_fundamentals(self, symbol)

        #see if a fundamental dataframe exists
        pickle_path = '{0}/{1}/{1}_fundamental.pickle'.format(config.DATA_PATH, symbol)
        if os.path.exists(pickle_path):
            df = pd.read_pickle(pickle_path)
        else:
            df = pd.DataFrame(columns=fund.keys())
            df = df.set_index(['datetime', 'symbol'])
            #make symbol directory if not exists
            os.makedirs('{}/{}'.format(config.DATA_PATH, symbol), exist_ok=True)

        df = df.append(fund, ignore_index=True)
        pd.to_pickle(df, pickle_path)
        return df
       

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

def watchlist():
    tc = TDClient(config)
    print("Saving Watch List: {}".format(config.WATCHLIST))
    for s in config.WATCHLIST:
       save_stock_data(tc, s)

def save_stock_data(tc,s):
    print("Getting daily history for {}".format(s))
    tc.get_price_daily_history(s)
    print("Getting minute history for {}".format(s))
    tc.get_price_intraday_history(s)
    print("Getting fundamentals for {}".format(s))
    tc.get_save_fundamentals(s)

def run():
    tc = TDClient(config)
    s = 'ADV'
    j = tc.get_fundamentals(s)
    print(j)
    
if __name__ == '__main__':
    # watchlist()
    run()