
import pandas as pd
import os
import pickle
from plotly.subplots import make_subplots
import plotly.graph_objects as go

def chart(sample_dict):
    #  {'symbol':symbol, 'history':df_hx, "future":df_future, "label":label}
    break_date = sample_dict['future'].index[0]
    df = pd.concat([sample_dict['history'], sample_dict['future']])
    _chart(df, sample_dict['symbol'], break_date)

def _chart(df,symbol, break_date):
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02)

        fig.add_trace( go.Candlestick(x=df.index, name=symbol, open=df['open'], high=df['high'], low=df['low'], close=df['close']), row=1, col=1)
        fig.add_trace( go.Scatter(
            x=df.index, y=df['upper_band'], name='Upper Bollinger Band', line={'color': 'red'}
            ), row=1, col=1)
        fig.add_trace( go.Scatter(x=df.index, y=df['lower_band'], name='Lower Bollinger Band', line={'color': 'red'}), row=1, col=1)

        fig.add_trace( go.Scatter(x=df.index, y=df['upper_keltner'], name='Upper Keltner Channel', line={'color': 'blue'}), row=1, col=1)
        fig.add_trace( go.Scatter(x=df.index, y=df['lower_keltner'], name='Lower Keltner Channel', line={'color': 'blue'}), row=1, col=1)

        fig.add_trace( go.Bar(name='Momentum', x=df.index, y=df['mom_hist'] ), row=2, col=1)

        fig.layout.xaxis.type = 'category'
        fig.layout.xaxis.rangeslider.visible = False
        fig.update_layout(height=600, width=800, title_text="Breakout at {}".format(break_date))
        fig.show()

if __name__ == "__main__":
    filename = './data/breakout/TSLA_20110324T050000.pickle'
    with open(filename, 'rb') as handle:
        s_dict = pickle.load(handle)
    chart(s_dict)
