from binance.client import Client

import os, csv, talib, numpy

import pandas as pd

from datetime import datetime

api_key = os.environ.get("binance_api_key")
api_security = os.environ.get("binance_api_security")

client = Client(api_key,api_security)
with open('input.txt', 'r') as file:
    input_lines = [line.strip() for line in file]
print("Input Lines : ",input_lines)

x = []
#print(input_lines[11])
for i in range(3,12,2):
    x.append(int(input_lines[i]))
#print(x)
coin_symbol = input_lines[1]

time_frame =str(x[0])+"T"

fast_length = x[1]

slow_length =x[2]

signal_period =x[3]

in_position = False
MA = x[4]
buy_price = 0

# is it buy position or sell position
pos = None

# take profit
tp = 0

#stop loss
sl =  0
# profit or loss
gain_loss = 0
# print(x[5])
# print(x[6])

start_date = str(input_lines[13])
end_date = str(input_lines[15])

# getting historical data
data = client.get_historical_klines(coin_symbol, Client.KLINE_INTERVAL_1MINUTE, start_date, end_date)

# from 1 minute time frame to multiple time frame
closing_time_timestamp = []
for i in data:
    closing_time_timestamp.append(i[6])

candle_date_time  = []
# converting milliosecond data to second
# and then converting into date

for i in closing_time_timestamp:
    n = i/1000
    candle_date_time.append(datetime.fromtimestamp(n))

data = pd.DataFrame(data,index=None)
candle_date_time=pd.to_datetime(candle_date_time)

#print(candle_date_time)

# setting up index to date time because resample work only if index is datetime
data.set_index(candle_date_time,inplace=True)
historical_data= data.resample(time_frame).agg({
                    1: 'first',
                    2: 'max',
                    3: 'min',
                    4: 'last',
                   })
#print(historical_data)
#getting excel shit
csv_file = open("result1.csv","w",newline='')
csv_writer = csv.writer(csv_file,delimiter=',')
csv_writer.writerow(["buy price","position","stop_loss","take profit","net %"])

historical_data = historical_data.astype(float)
closes = historical_data[4]

# a list contains highs of each candles
highs = historical_data[2]
print(closes)

# a list contains low's of each candle
lows = historical_data[3]
np_closes = numpy.array(closes)
#print(np_closes)
macd = talib.MACD(np_closes,fast_length,slow_length,signal_period)
EMA100 = talib.EMA(np_closes,MA)
sum = 0
macd_line = macd[0]
macd_signal = macd[1]
macd_hist = macd[2]


# a function take two arguments price and stop loss and returns tp price and percentage of take profit and stop loss
# because sl is independent variable and tp is dependent variable
def tp_cal(price,s):
    # percentage of sl
    j = (s*100)/price
    y = 100-j
    # profit percentage
    tp_per = y*3
    # calculating price of tp
    take_profit = price+(tp_per/100)*price
    return [take_profit,tp_per,y]



# a function that take position of buy/sell order and returns sl and tp
def fun(n):
    for i in range(n,0,-1):
        if pos == "BUY":
            if lows[i]<lows[i-1]:
                stop_loss = lows[i]
                take_profit = tp_cal(closes[n],stop_loss)
                return take_profit[0], stop_loss

        if pos == "SELL":
            if highs[i]>highs[i-1]:
                stop_loss = highs[i]
                take_profit = tp_cal(closes[n],stop_loss)
                return take_profit[0],stop_loss



sum = 0
#print(EMA100)
buy_price = 0
for i in range(len(closes)):
    # checking if we are still in position and if yes is price has hit TP or SL
    if in_position:
        x = tp_cal(buy_price,sl)
        if pos == "BUY" :
            if closes[i] >= tp or highs[i] >= tp  :
                csv_writer.writerow([buy_price,pos,sl,tp,x[1]])
                sum = sum+x[1]
                print("tp buy order")
                in_position = False
            if closes[i] <= sl or lows[i] <= sl:
                csv_writer.writerow([buy_price,pos, sl, tp, x[2]])
                sum = sum + x[2]
                in_position = False
                print("sl buy order")
        if pos == "SELL":
            if  closes[i]>= sl or highs[i]>=sl:
                csv_writer.writerow([buy_price,pos,sl,tp,x[2]])
                sum = sum + x[2]
                in_position=False
                print("sl sell order")
            if closes[i]<= tp or lows[i] <= tp:
                csv_writer.writerow([buy_price,pos,sl,tp,x[1]])
                print("buy price",buy_price)
                sum = sum + x[1]
                in_position = False
                print("tp sell order")
    #generating buy signal
    if closes[i]>EMA100[i]:
        if macd_line[i]>macd_signal[i]:
            if macd_line[i-1]<= macd_signal[i-1]:
                if in_position:
                    #nothing to do
                    pass
                else:
                    print("Buy at :",closes[i])
                    buy_price = closes[i]
                    #print("buy price",buy_price)
                    pos = "BUY"
                    tp,sl = fun(i)
                    #print(tp,sl)
                    in_position = True




    # generating sell signal
    if closes[i]<EMA100[i]:
        if macd_line[i]<macd_signal[i]:
            if macd_line[i-1]>= macd_signal[i-1]:
                if in_position:
                    #nothing to do
                    pass
                else:
                    print("Sell at",closes[i])
                    pos = "SELL"
                    buy_price = closes[i]
                    tp,sl = fun(i)
                    in_position = True

csv_writer.writerow(["Total "," "," "," ",sum])

