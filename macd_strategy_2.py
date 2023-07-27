#                            "MACD + Price Action"
from binance.client import Client
import csv,os,talib,numpy
from datetime import datetime
import pandas as pd

api_key = os.environ.get("binance_api_key")
api_security = os.environ.get("binance_api_security")
client = Client(api_key,api_security)

with open('input.txt', 'r') as file:
    input_lines = [line.strip() for line in file]

x = []
for i in range(3,12,2):
    x.append(int(input_lines[i]))

start_date =str(input_lines[13])
end_date = str(input_lines[15])
time_frame = x[0]

# getting historical data
data = client.get_historical_klines("BTCUSDT",Client.KLINE_INTERVAL_1MINUTE,start_date,end_date)

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
# print(data)
candle_date_time=pd.to_datetime(candle_date_time)
#print(candle_date_time)

# setting up index to date time because resample work only if index is datetime
data.set_index(candle_date_time,inplace=True)
def candlestick(time,dat):
    x= dat.resample(time).agg({
                        1: 'first',
                        2: 'max',
                        3: 'min',
                        4: 'last',
                       })
    return x

# getting historical data after processing
historical_data = pd.DataFrame(candlestick(str(time_frame)+"T",data),index = None)
historical_data = historical_data.astype(float)


# print(historical_data)
# print(historical_data)
#getting closes
closes = historical_data[4]
# print(closes)
#getting highs of each candle
highs = historical_data[2]
#getting lows
lows = historical_data[3]
# print(len(highs))

#getting excel shit
csv_file = open("result3.csv","w",newline='')
csv_writer = csv.writer(csv_file,delimiter=',')
csv_writer.writerow(["buy price","position","stop_loss","take profit","net %"])


# key level is suppport and resistance ?
is_key_level = False
in_position = False
buy_price = 0
#key level price
key_level_price = 0


fast_length = x[1]
slow_length =x[2]
signal_period =x[3]

MA = x[4]
# finding support and resistance with the help of fractals
# fractal's are formed using 5 candles in which the third candles is chosen support & resistance based on condition
# if 3rd candles low is lower than the second and fourth candle low and if
# second & fourth candle's low are lower than 1st & 5th candle low
# than it is support. similar with resistance

# a function that take position as input at returns True if the price is support
def is_support(i):
    if lows[i] < lows[i - 1] and lows[i] < lows[i + 1] and lows[i - 1] < lows[i - 2] and lows[i + 1] < lows[i + 2]:
        return True
    else:
        return False
# a function that take position as input at returns True if the price is resistance
def is_resistance(i):
    if highs[i] > highs[i - 1] and highs[i] > highs[i + 1] and highs[i - 1] > highs[i - 2] and highs[i + 1] > highs[i + 2]:
        #print(historical_data.iloc[i,:])
        return True
    else:
        return False

lower_tf = candlestick(str(time_frame / 2) + "T", data)
lower_tf = lower_tf.astype(float)
# lower tf closes
closes_ltf = lower_tf[4]
# print(historical_data)
# print(lower_tf)
np_closes = numpy.array(closes)
# a function that takes position/index[eg., 4HR] of support/resistance and returns the index of 2X smaller time frame[eg.,2HR]
def fun(i) :
    # a,b will be the possible value where key level will be
    # print("np closes i :",np_closes[i])
    # print("np _closes _ltf : ",np_closes_ltf[i*2+1])
    a = i*2
    b = i*2+1
    c = i*2-1
    if np_closes_ltf[a] == np_closes[i]:
        return a
    if np_closes_ltf[b] == np_closes[i]:
        return b
    if np_closes_ltf[c] == np_closes[i]:
        return c
#closes of lower time frame candles
np_closes_ltf = numpy.array(closes_ltf)
macd = talib.MACD(np_closes_ltf,fast_length,slow_length,signal_period)
# print(len(np_closes_ltf))
macd_line = macd[0]
# print(len(macd_line))
macd_signal = macd[1]
macd_hist = macd[2]

#stop loss
sl = 0
#take profit
tp = 0
# position
pos = None

# a function that takes sl and entry price and returns take profit
def take_profit(price, sl) :
    # percentage of sl
    j = (sl * 100) / price
    y = 100 - j
    # profit percentage
    tp_per = y * 1.5
    # calculating price of tp
    take_profit = price + (tp_per / 100) * price
    return [take_profit, tp_per, y]


key_level_index = 0
sum = 0
key_level = None
print("first : -:",closes[0])
for i in range(2, len(closes)-2):

    if is_resistance(i) :
        print("resistance :-",closes[i])
    if in_position:
        if pos == "BUY":
            if closes[i] >= tp[0] or highs[i] >= tp[0]:
                csv_writer.writerow([buy_price, pos, sl, tp[0], tp[1]])
                sum = sum + tp[1]
                in_position = False
                print("tp buy order")
            if closes[i] <= sl or lows[i] <= sl:
                print("stop looss percentage :-",tp[2])
                csv_writer.writerow([buy_price, pos, sl, tp[0], tp[2]])
                sum = sum + tp[2]
                in_position = False
                print("Sl buy order ")

        if pos == "SELL":
            if closes[i] <= tp[0] or lows[i] <= tp[0]:
                csv_writer.writerow([buy_price, pos, sl, tp[0], tp[1]])
                sum = sum + tp[1]
                in_position = False
                print("tp sell order")
            if closes[i] >= sl or highs[i] >= sl:
                csv_writer.writerow([buy_price, pos, sl, tp[0], tp[2]])
                sum = sum + tp[2]
                in_position = False
                print("Sl sell order")

    if is_key_level:
        if key_level == "SUP" :
            if i == key_level_index+1 or i==key_level_index+2:
                # do nothing
                pass
            else:
                if in_position:
                    # nothing to do
                    pass
                else:
                    if  lows[i] <= key_level_price:
                        # shift to lower time frame
                        # lower tf index of key level
                        # print("high tf i=",i)
                        index_ltf = fun(i)
                        # print("index ltf :-",index_ltf)
                        # generating buy_signal's
                        for j in range(index_ltf, len(np_closes_ltf)):
                            if macd_line[j] > macd_signal[j]:
                                if macd_line[j - 1] <= macd_signal[j - 1]:
                                    if in_position:
                                        # do nothing
                                        pass
                                    else:
                                        buy_price = np_closes_ltf[j]
                                        print("buy_price:",buy_price)
                                        sl = key_level_price
                                        tp = take_profit(buy_price, sl)
                                        pos = "BUY"
                                        is_key_level = False
                                        in_position = True
        if key_level == "RES" :
            # dont look for next and next+1 candle of key level
            if i == key_level_index+1 or i==key_level_index+2:
                # do nothing
                pass
            else:
                if in_position :
                    # nothing to do
                    pass
                else:
                    if highs[i] >= key_level_price :
                        # shifts to lower tf
                        # lower tf index of key level
                        index_ltf = fun(i)
                        #generating sell signals
                        for j in range(index_ltf, len(np_closes_ltf)):
                            if macd_line[j] < macd_signal[j]:
                                if macd_line[j - 1] >= macd_signal[j - 1]:
                                    buy_price = np_closes_ltf[j]
                                    sl = key_level_price
                                    tp = take_profit(buy_price, sl)
                                    pos = "SELL"
                                    in_position = True
                                    is_key_level = False
    else:
        # is candle is support
        if is_support(i):
            key_level_price = np_closes[i]
            print("i = ",i)
            print("key level price :",key_level_price)
            is_key_level = True
            key_level = "SUP"
            key_level_index = i
        # is candle is resistance
        if is_resistance(i):
            is_key_level = True
            key_level = "RES"
            key_level_price = np_closes[i]
            key_level_index = i

# total gain/loss
csv_writer.writerow(["Total "," "," "," ",sum])