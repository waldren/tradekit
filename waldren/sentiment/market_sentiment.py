import pandas as pd
import numpy as np 
import collections
import sys
from datetime import datetime, timedelta 
from plotly.subplots import make_subplots
import plotly.graph_objects as go

sys.path.append('/app/waldren/base')
import td_db_client

class SentimentByIndices:
    def __init__(self, client=None):
        if client is None:
            self.client = td_db_client.Client()
        else:
            self.client = client
        self.major_indices = [
            ('Volatility','VIX'),
            # ('Dow Jones Industrial Average','DJIA'),	 
            # ('Dow Jones Transportation Average','DJT'),
            # ('Dow Jones Utility Average Index','DJU'),
            ('NASDAQ 100 Index','NDX'),
            # ('NASDAQ Composite Index','COMP'),
            ('NYSE Composite Index','NYA'),
            ('S&P 500 Index','SPX')
            # ('S&P 400 Mid Cap Index','MID'),
            # ('S&P 100 Index','OEX'),
            # ('Russell 2000 Index','RUT')
        ]
        self.inds = collections.defaultdict(dict)
        self.update_indices()
    '''
    def update_indices(self):
        start_date = datetime.now()- timedelta(days = 5)
        for idx in self.major_indices:
            df = self.client.get_standard_5min_price_history(start_date, idx[1])
            self.inds[idx[1]] = df 
        self.apply_indicators()
    '''

    def update_indices(self):
        for idx in self.major_indices:
            df = self.client.get_price_daily_history(idx[1], period=self.client.get_year_period(1))
            self.inds[idx[1]] = df 
        self.apply_indicators()

    def apply_indicators(self):
        for idx in self.major_indices:
            # Create close change percent
            self.inds[idx[1]]['close_change'] = self.inds[idx[1]]['close'].pct_change(fill_method='ffill')
            # Create the rolling averages
            self.inds[idx[1]]['12sma'] = self.inds[idx[1]]['close_change'].rolling(window=12).mean()
            self.inds[idx[1]]['24sma'] = self.inds[idx[1]]['close_change'].rolling(window=24).mean()
            self.inds[idx[1]]['36sma'] = self.inds[idx[1]]['close_change'].rolling(window=36).mean()
            print(f"{self.inds[idx[1]]['12sma'].shape} is {idx[1]} shape")
        self.create_avg()

    def create_avg(self):
        # iterate through the length of bars
        bar_count = len(self.inds[self.major_indices[0][1]]['close'])

        v_12sma = np.zeros(bar_count)
        v_24sma = np.zeros(bar_count)
        v_36sma = np.zeros(bar_count)
        for i in range(0, bar_count):
            for idx in self.major_indices:
                v_12sma[i] = v_12sma[i] + self.inds[idx[1]]['12sma'].iloc[i]
                v_24sma[i] = v_24sma[i] + self.inds[idx[1]]['24sma'].iloc[i]
                v_36sma[i] = v_36sma[i] + self.inds[idx[1]]['36sma'].iloc[i]
            v_12sma[i] = v_12sma[i] / len(self.major_indices)
            v_24sma[i] = v_24sma[i] / len(self.major_indices)
            v_36sma[i] = v_36sma[i] / len(self.major_indices)
        self.inds['avg']['12sma'] = v_12sma
        self.inds['avg']['24sma'] = v_24sma
        self.inds['avg']['136sma'] = v_36sma

    def get_data(self):
        return self.inds  
        
    def plot(self):
        fig = make_subplots(rows=2, cols=1, row_heights=[0.8, 0.2], shared_xaxes=True, vertical_spacing=0.02)
        fig = self._add_candlestick(df, symbol, fig, row=1, col=1)
        for idx in self.major_indices:
            df = self.ind[idx[1]]
            fig.add_trace( go.Scatter(x=df.index, y=df['12sma'], name='1 hr SMA', line={'color': 'purple'}), row=1, col=1)
        
        fig.layout.xaxis.type = 'category'
        fig.layout.xaxis.rangeslider.visible = False
        fig.update_layout(height=800, width=1280, title_text="Chart for {}".format(symbol))
        fig.show()

        