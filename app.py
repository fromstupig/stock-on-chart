from flask import Flask, request
from finviz.screener import Screener
import pandas as pd
import yfinance as yf
import pandas_ta as ta
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.route("/tickers")
def search_tickers():
    option = request.args.get('o')

    filters = ['exch_nasd', 'sh_avgvol_o1000', 'sh_curvol_o1000']
    stock_list = Screener(filters=filters, table='Overview',
                          order='price')
    lists = list(map(lambda stock: stock['Ticker'], stock_list))
    tickers = " ".join(lists)
    df = yf.download(tickers=tickers, period="1mo", interval="30m", group_by = 'ticker')
    ticker_df_5mins = pd.DataFrame()
    if option == str(2):
        ticker_df_5mins = yf.download(tickers=tickers, period="1mo", interval="5m", group_by='ticker')

    rv = []
    for ticker in lists:
        ticker_df = df[ticker].copy()
        ticker_df.ta.macd(close=ticker_df["Close"], fast=12, slow=26, signal=9, append=True)
        pd.set_option("display.max_columns", None)
        macd_compare = ticker_df['MACDs_12_26_9'] < ticker_df['MACDh_12_26_9']
        macd_compare_value = macd_compare.value_counts().idxmax()

        if option == str(1) and macd_compare_value:
            rv.append(ticker)

        if option == str(2) and not macd_compare_value:
            ticker_df = ticker_df_5mins[ticker].copy()
            ticker_df['EMA_9'] = ta.ema(close=ticker_df["Close"], length=9)
            ticker_df.ta.vwap(high=ticker_df["High"], low=ticker_df['Low'], close=ticker_df["Close"],
                              volume=ticker_df['Volume'], append=True)
            ticker_df['EMA_200'] = ta.ema(close=ticker_df["Close"], length=200)

            ema9_compare_vwap = ticker_df['EMA_9'] > ticker_df['VWAP_D']
            ema9_compare_vwap_value = ema9_compare_vwap.value_counts().idxmax()
            vwap_compare_ema200 = ticker_df['VWAP_D'] > ticker_df['EMA_200']
            vwap_compare_ema200_value = vwap_compare_ema200.value_counts().idxmax()

            if ema9_compare_vwap_value and vwap_compare_ema200_value:
                rv.append(ticker)

    return {
        'data': rv, 'total': len(rv)
    }
