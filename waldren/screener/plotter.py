import pandas
from plotly.subplots import make_subplots
import plotly.graph_objects as go

class CandleStickPlotter:
    def __init__(self, date_col='datetime', open_col='open', high_col='high', low_col='low', close_col='close', volume_col='volume'):
        # Parameters

        # Variables to manage different colument names for OHLCV
        self.date_col = date_col
        self.open_col = open_col
        self.high_col = high_col
        self.low_col = low_col
        self.close_col = close_col
        self.volume_col = volume_col

    def plot_basic(self, df, symbol):
        fig = make_subplots(rows=2, cols=1, row_heights=[0.8, 0.2], shared_xaxes=True, vertical_spacing=0.02)
        fig = self._add_candlestick(df, symbol, fig, row=1, col=1)
        fig = self._add_volume(df, fig, row=2, col=1)
        fig = self._add_big_move_mark(df, fig, row=1, col=1)
        
        fig.layout.xaxis.type = 'category'
        fig.layout.xaxis.rangeslider.visible = False
        fig.update_layout(height=800, width=1280, title_text="Chart for {}".format(symbol))
        fig.show()

    def _add_candlestick(self, df, symbol, fig, row=1, col=1):
        fig.add_trace( go.Candlestick(x=df.index, name=symbol, open=df[self.open_col], high=df[self.high_col], low=df[self.low_col], close=df[self.close_col]), row=1, col=1)
        
        fig.add_trace( go.Scatter(x=df.index, y=df['10sma'], name='10 day SMA', line={'color': 'purple'}), row=1, col=1)
        fig.add_trace( go.Scatter(x=df.index, y=df['20sma'], name='20 day SMA', line={'color': 'blue'}), row=1, col=1)
        fig.add_trace( go.Scatter(x=df.index, y=df['50sma'], name='50 day SMA', line={'color': 'yellow'}), row=1, col=1)
        return fig 
    
    def _add_volume(self, df, fig, row=2, col=1):
        fig.add_trace( go.Bar(name='Volume', x=df.index, y=df['volume'] ), row=row, col=col)
        fig.add_trace( go.Scatter(x=df.index, y=df['vol_avg'], name='Average Volume', line={'color': 'black'}), row=2, col=1)
        return fig

    def _add_big_move_mark(self, df, fig, row=1, col=1):
        bm = df.iloc[(df['big_move'] != 0).values ]
        fig.add_trace(go.Scatter(
            x=bm.index,
            y=bm[self.close_col],
            mode='markers',
            marker=dict(
                size=8,
                color='red',
                symbol='cross'
            ),
            name='Big Moves'
        ))
        return fig