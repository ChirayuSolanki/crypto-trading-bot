" crypto trading bot "

#importing the binance client form binance- python API module
import numpy,talib
import pandas as pd
from binance.enums import *
import os,websocket,json
#import pprint
from binance.client import Client

api_key = os.environ.get("binance_api_key")
api_security = os.environ.get("binance_api_security")

FAST_MOVING_MA = 2
SLOW_TERM_MA = 10
MEDIUM_TERM_MA = 5

PAIR = 'FTMUSDT'
QUANTITY = 35
in_position = False
# connecting to binance account
client = Client(api_key,api_security)
current_balance = client.get_asset_balance(asset="FTM")
print(current_balance)

# closing price list
closes = []

def order(side, quantity, symbol):

    try:
        print("sending order")
        order = client.create_order(symbol=symbol, side=side, type= ORDER_TYPE_MARKET, quantity=quantity)
        print(order)

    except Exception as e:
        print("an exception occured - {}".format(e))
        return False

    return True

# connecting through binance socket to fetch data
Socket = "wss://stream.binance.com:9443/ws/ftmusdt@kline_1m"

def on_open(ws):
    print("Connection opened")

def on_close(ws):
    print("Connection Closed")

def on_message(ws,message):

    global closes,LONG_TERM_MA,in_position

    json_message = json.loads(message)
    #pprint.pprint(json_message)

    candle = json_message['k']
    #print(candle)

    is_candle_close = candle['x']

    close = candle['c']

    if is_candle_close:
        print("candle close at {}".format(close))
        closes.append(float(close))
        #print(closes)

        if len(closes) > SLOW_TERM_MA:
            np_closes = numpy.array(closes)
            EMA20 = talib.EMA(np_closes, 20)
            EMA50 = talib.EMA(np_closes, 50)
            EMA200 = talib.EMA(np_closes, 200)

#  "Generating buy signal"
# when the 20period MA crosses above 50 period MA and the both 20 period & 50 period MA are above 200period MA

            if EMA20[-1] and EMA50[-1] > EMA200[-1]:
                if EMA20[-1] >EMA50[-1]:
                    if in_position:
                        #nothing to do
                        print()
                    else:
                        print("buy!!buy!buy")
                        print("time : ", pd.to_datetime(candle["T"],unit='ms'))
                        # closes[-1] because we will buy when candles close
                        print("At price :- ", closes[-1])
                        order_succed = order(SIDE_BUY,QUANTITY,PAIR)
                        if order_succed:
                           in_position = True
                           print("Buy order placed")

#"Generating Sell signal"
# when the fast_MA crosses below medium term or slow term moving average we will sell our position
            if EMA20[-1]<EMA50[-1] or EMA20[-1]<EMA200[-1]:
                if in_position:
                    print("Sell!Sell!Sell!")
                    order_succeded = order(SIDE_SELL,QUANTITY,PAIR)
                    if order_succeded:
                        print("Sell!Sell!Selllll...")
                        print("Sell at price :- ",closes[-1])
                        print("time : ", pd.to_datetime(candle["T"], unit='ms'))
                        in_position = False

                        updated_balance = client.get_asset_balance(asset="USDT")
                        print(updated_balance)
                else:
                    #nothing to do
                    print()


ws = websocket.WebSocketApp(Socket,on_open=on_open,on_close=on_close,on_message=on_message)
ws.run_forever()

