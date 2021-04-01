import scipy.signal as sig 
import numpy as np
import pandas as pd

class Kristjan_Breakout():

    def __init__(self, date_col='dt', open_col='open', high_col='high', low_col='low', close_col='close', volume_col='volume'):
        # Parameters
        self.prv_brkout_thr = 2 #percent  1 = 100%
        self.pullback_pct   = -0.2

        # Variables to manage different colument names for OHLCV
        self.date_col = date_col
        self.open_col = open_col
        self.high_col = high_col
        self.low_col = low_col
        self.close_col = close_col
        self.volume_col = volume_col
        # Call the percent change column using the same OHLCV naming
        self.close_pct_chg_col = "{}_pct_chg".format(self.close_col)
        self.open_pct_chg_col = "{}_pct_chg".format(self.open_col)
        self.low_pct_chg_col = "{}_pct_chg".format(self.low_col)
        self.high_pct_chg_col = "{}_pct_chg".format(self.high_col)
 
    def dollar_value(self, df):
        return (df[self.high_col]+df[self.low_col])/2 * df[self.volume_col]

    def mark_bigmoves(self, df):
        if df['peaks'] == 1 and df['growth']>= self.prv_brkout_thr:
            return 1
        elif df['troughs'] == 1 and abs(df['growth']) >= self.prv_brkout_thr:
            return -1
        else:
            return 0

    def apply_moavs(self, df):
        if df is None:
            print("apply_moavs: df is None")
            return df 
        # Create the rolling averages 
        df['10sma'] = df[self.close_col].rolling(window=10).mean()
        df['20sma'] = df[self.close_col].rolling(window=20).mean()
        df['50sma'] = df[self.close_col].rolling(window=50).mean()
        df['100sma'] = df[self.close_col].rolling(window=100).mean()
        df['200sma'] = df[self.close_col].rolling(window=200).mean() 
        # Find the highest of the moving averages to help determine if price is above all   
        df['max_mav'] = df[["10sma", "20sma", "50sma", "100sma"]].max(axis=1)
        df['above_20sma'] = df[self.close_col] > df['20sma']
        df['20sma_above_50sma'] = df['20sma'] > df['50sma']
        
        return df
    
    def find_extrema(self, df):
        if df is None:
            print("apply_extrema: df is None")
            return df 
        close = df[self.close_col]
        df = self._find_peaks(close, 'peaks', df)
        close = close.mul(-1)
        df = self._find_peaks(close, 'troughs', df)
        return df

    def _find_peaks(self, close, col_name, df):
        peaks, dic = sig.find_peaks(close)
        v = np.zeros(df.shape[0])
        h = np.zeros(df.shape[0])
        j = 0
        for i in peaks:
            v[i] = 1
        df[col_name] = v
        
        return df


    def apply_growth_indicators(self, df):
        if df is None:
            print("apply_growth_indicators: df is None")
            return df 
        # Calculate the percent change from the last day
        df[self.close_pct_chg_col] = df[self.close_col].pct_change(fill_method='ffill')
        df[self.open_pct_chg_col] = df[self.open_col].pct_change(fill_method='ffill')
        df[self.high_pct_chg_col] = df[self.high_col].pct_change(fill_method='ffill')
        df[self.low_pct_chg_col] = df[self.low_col].pct_change(fill_method='ffill')

        df['growth'] = df[self.close_pct_chg_col].cumsum()

        return df

    def apply_volume_indicators(self, df):
        # Calculate the Average Volume for last 20 days
        df['vol_avg'] = df[self.volume_col].rolling(window=20).mean()
        # Calculate the Dollar Value at the day
        df['dol_val'] = df.apply(self.dollar_value, axis=1)
        return df
    
    def apply_range_indicators(self, df):
        # Calculate the Average Daily Range (%) of the last 20 days
        df['adr_pct'] = 100*(((df[self.high_col]/df[self.low_col]).rolling(window=20).mean())-1)
        return df

    def scan(self, df):
        # TODO Add check to see if these have already been run on df
        # Apply indicators if they havne not already been applied
        if '10sma' not in df.columns:
            df = self.apply_moavs(df)
        if self.close_pct_chg_col not in df.columns:
            df = self.apply_growth_indicators(df)
        if 'peaks' not in df.columns: 
            df = self.find_extrema(df)
        if 'vol_avg' not in df.columns: 
            df = self.apply_volume_indicators(df)
        if 'adr_pct' not in df.columns: 
            df = self.apply_range_indicators(df)
        # Mark Breakouts
        df['big_move'] = df.apply(self.mark_bigmoves, axis=1)
        return df
    
    def pre_scan(self, df):
        if df is None:
            print("pre_scan: df is None")
            return df 
        print("pre_scan NOT YET IMPLEMENTED")
        return df

    def _find_orderly_pullback(self, df):
        bm = df.iloc[(df['big_move']==1 | df['troughs']==1 )]


    
