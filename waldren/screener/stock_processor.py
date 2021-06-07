import pandas as pd
import os
import pickle
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from datetime import timedelta

class BaseProcessor():
    def __init__(self, symbol='___', date='dt', open='open', high='high', low='low', close='close', volume='volume'):
        self.symbol = symbol
        self.date = date
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume

class SqueezeProcessor(BaseProcessor):
    def __init__(self, data_folder='./data', indices=['spy', 'nasdaq'], drop_nan=True,
                squeeze_threshold=0.025, breakout_duration=5, breakout_threshold=0.05, hx_length=40, future_length=5,
                moav_period=20, moav_long=100, moav_short=10, keltner_multiplier=1.5, **kwargs):
        if (not os.path.exists(data_folder)):
            os.mkdir(data_folder)
        self.data_folder = data_folder
        self.indices = indices
        self.drop_nan = drop_nan
        self.moav_period = moav_period
        self.keltner_multiplier = keltner_multiplier
        self.ma_name = "{}sma".format(self.moav_period)
        self.max_name = "{}max".format(self.moav_period)
        self.lo_name = "{}low".format(self.moav_period)
        self.moav_short = moav_short
        self.moav_long  = moav_long
        self.ma_s_name = "{}sma".format(self.moav_short)
        self.ma_l_name = "{}sma".format(self.moav_long)

        self.squeeze_threshold = 1 - squeeze_threshold
        self.breakout_duration = breakout_duration
        self.breakout_threshold = breakout_threshold
        self.bar_duration = timedelta(days=1)
        self.hx_length = hx_length
        self.future_length = future_length

        super().__init__(**kwargs)

    def in_squeeze_bands(self, df):
        return df['lower_band'] > df['lower_keltner'] and df['upper_band'] < df['upper_keltner']

    def is_breaking_out(df, percentage=2.5):
        last_close = df[-1:][self.close].values[0]

        if is_consolidating(df[:-1], percentage=percentage):
            recent_closes = df[-16:-1]

            if last_close > recent_closes[self.close].max():
                return True

        return False

    def donchian(self, df):
        return (df[self.max_name] + df[self.lo_name]) / 2
    def mom_hist(self, df):
        return df[self.close] - ((df['donchian']+ df[self.ma_name])/2)
    def over_ma(self, df):
        return (df[self.close] > df[self.ma_s_name] and df[self.close] > df[self.ma_l_name])

    def process(self, df, symbol):
        self.symbol=symbol
        if df is None:
            return None
        if df.empty:
            return None
        
        df[self.ma_name] = df[self.close].rolling(window=self.moav_period).mean()
        df['stddev'] = df[self.close].rolling(window=self.moav_period).std()
        df[self.max_name] = df[self.close].rolling(window=self.moav_period).max()
        df[self.lo_name] = df[self.close].rolling(window=self.moav_period).min()
        
        df[self.ma_s_name] = df[self.close].rolling(window=self.moav_short).mean()
        df[self.ma_l_name] = df[self.close].rolling(window=self.moav_long).mean()
        
        
        df['donchian'] =  df.apply(self.donchian, axis=1)
        df['mom_hist'] = df.apply(self.mom_hist, axis=1)
        df['lower_band'] = df[self.ma_name] - (2 * df['stddev'])
        df['upper_band'] = df[self.ma_name] + (2 * df['stddev'])

        df['TR'] = abs(df[self.high] - df[self.low])
        df['ATR'] = df['TR'].rolling(window=self.moav_period).mean()

        df['lower_keltner'] = df[self.ma_name] - (df['ATR'] * self.keltner_multiplier)
        df['upper_keltner'] = df[self.ma_name] + (df['ATR'] * self.keltner_multiplier)

        df['close_pct_change'] = df[self.close].pct_change(fill_method='ffill')
        df['growth'] = df['close_pct_change'].cumsum()
        
        df['has_momentum'] = df.apply(self.over_ma, axis=1)
        # df['TTM_squeeze'] = df.apply(self.in_squeeze, axis=1)

        df['TTM_squeeze'] = df[self.close].rolling(window=5).min() > (df[self.close].rolling(window=5).max() * self.squeeze_threshold)

        # Add Stock Index metrics
        for c in self.indices:
            df["{}_10ma".format(c)] = df[c].rolling(window=10).mean()
        
        if self.drop_nan:
            df = df.dropna(axis=0)
        return df 

    def create_squeeze_samples(self, df, hx_length=22, future_length=5):
        sq_idx = df.index[(df['TTM_squeeze'].shift(-1)== True) & (df['TTM_squeeze'] == False)]
        for idx in sq_idx:
            fut_idx = df.index.get_loc(idx)+1
            df_hx = df.loc[:idx].tail(self.hx_length)
            df_future = df.iloc[fut_idx:].head(self.future_length)
            self.save_sample(idx, df_hx, df_future)
    
    def save_sample(self, idx, df_hx, df_future):
        # check for a future breakout        
        f_growth = df_future['close_pct_change'].head(self.breakout_duration).sum()
        # Label the sample
        label = 'no_growth'
        if f_growth > self.breakout_threshold:
            print("{} with breakout at {} of {}".format(self.symbol,idx,f_growth))
            label = 'breakout'
        elif f_growth < -self.breakout_threshold:
            print("{} with breakdown at {} of {}".format(self.symbol,idx,f_growth))
            label = 'breakdown'
        elif f_growth > 0:
            label = 'up'
        elif f_growth < 0:
            label = 'down'

        sample_dict = {'symbol':self.symbol, 'history':df_hx, "future":df_future, "label":label}
        self.write_to_folder(idx, sample_dict, label)
    
    def write_to_folder(self, idx, sample_dict, label):
        # path /data_folder/label/symbol_idx.pickle
        label_dir = os.path.join(self.data_folder, label)
        if not os.path.exists(label_dir):
            os.mkdir(label_dir)
        idx_frmtd = idx.strftime("%Y%m%dT%H%M%S")
        filename = f"{self.symbol}_{idx_frmtd}.pickle"
        out_file_path = os.path.join(label_dir, filename)
        with open (out_file_path, 'wb') as handle:
            pickle.dump(sample_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def chart(self,df, symbol):
        print(self.date)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02)

        fig.add_trace( go.Candlestick(x=df[self.date], open=df[self.open], high=df[self.high], low=df[self.low], close=df[self.close]), row=1, col=1)
        fig.add_trace( go.Scatter(
            x=df[self.date], y=df['upper_band'], name='Upper Bollinger Band', line={'color': 'red'}
            ), row=1, col=1)
        fig.add_trace( go.Scatter(x=df[self.date], y=df['lower_band'], name='Lower Bollinger Band', line={'color': 'red'}), row=1, col=1)

        fig.add_trace( go.Scatter(x=df[self.date], y=df['upper_keltner'], name='Upper Keltner Channel', line={'color': 'blue'}), row=1, col=1)
        fig.add_trace( go.Scatter(x=df[self.date], y=df['lower_keltner'], name='Lower Keltner Channel', line={'color': 'blue'}), row=1, col=1)

        fig.add_trace( go.Bar(name='Momentum', x=df[self.date], y=df['mom_hist'] ), row=2, col=1)

        fig.layout.xaxis.type = 'category'
        fig.layout.xaxis.rangeslider.visible = False
        fig.update_layout(height=600, width=800, title_text="Squeeze Scan for {}".format(symbol))
        fig.show()
