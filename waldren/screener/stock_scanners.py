import pandas
from plotly.subplots import make_subplots
import plotly.graph_objects as go

class BaseScanner():
    def __init__(self, date='dt', open='open', high='high', low='low', close='close', volume='volume'):
        self.date = date
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume

class SqueezeScanner(BaseScanner):
    def __init__(self, moav_period=20, moav_long=100, moav_short=10, keltner_multiplier=1.5, **kwargs):
        self.moav_period = moav_period
        self.keltner_multiplier = keltner_multiplier
        self.ma_name = "{}sma".format(self.moav_period)
        self.max_name = "{}max".format(self.moav_period)
        self.lo_name = "{}low".format(self.moav_period)
        self.moav_short = 10
        self.moav_long  = 100
        self.ma_s_name = "{}sma".format(self.moav_short)
        self.ma_l_name = "{}sma".format(self.moav_long)
        super().__init__(**kwargs)

    def in_squeeze(self, df):
        return df['lower_band'] > df['lower_keltner'] and df['upper_band'] < df['upper_keltner']
    def donchian(self, df):
        return (df[self.max_name] + df[self.lo_name]) / 2
    def mom_hist(self, df):
        return df[self.close] - ((df['donchian']+ df[self.ma_name])/2)
    def over_ma(self, df):
        return (df[self.close] > df[self.ma_s_name] and df[self.close] > df[self.ma_l_name])



    def scan(self, df):
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


        
        df['has_momentum'] = df.apply(self.over_ma, axis=1)
        df['TTM_squeeze'] = df.apply(self.in_squeeze, axis=1)
        return df 


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

