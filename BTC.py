import requests, time, talib, csv
from playsound import playsound
from numpy import genfromtxt as gft
from coinex.coinex import CoinEx

CryptoToTrade = 'BTC'
timeFrame = '5min'  #1min, 1hour, 1day, 1week
howMuchShouldIBuy = 30  # $

access_id = '9AB450BFC9574FF2A081D257A691D556'
secret_key = '1343602FFD3EA564E432286088A534EAEC29F8145D1078EC'
coinex = CoinEx(access_id, secret_key)
dataOfChart = 'Data/DataForIndicator_BTC.csv'
saveDataHere = 'Trade_Information/orderHistory_BTC.csv'
fiveMin = 5 * 60
timePeriodForBB = 20
nbDev = .5
RSILevelToBuy = 30
RSILessThan = 80
saveProfit = 1
trendTimeFrame = 600  # Minute
whenStopLoss = -1
buyPrice = 0
sellPrice = 0
orderCounter = 1

def start():
    print(time.ctime(time.time()))
    while True:
        try:
            getDataForAnalyse()
            BB()
        except Exception as e:
            print('Error...', e)
            print(time.ctime(time.time()))
            playsound('Alarms/Rocket.wav')
            continue
        
def getDataForAnalyse():
    request = requests.get(f"https://api.coinex.com/v1/market/kline?market={CryptoToTrade+'USDT'}&type={timeFrame}&limit=150")
    response = (request.json())['data']

    csvFile = open("Data/DataForIndicator_BTC.csv", 'w', newline='')
    candleStickWriter = csv.writer(csvFile, delimiter = ',')
    #date, open, close, high, low, volume, amount | 5m-16h | 30m-336

    for candles in response:
        candleStickWriter.writerow(candles)
    csvFile.close()

def RSI():
    splittedCandle = gft(dataOfChart, delimiter=',')
    candlesClose = splittedCandle[:,2]
    RSIs = talib.RSI(candlesClose, timeperiod=14)
    currentRSI = RSIs[-2]

    if RSILessThan >= currentRSI >= RSILevelToBuy:
        return True
    else:
        return False

def SMA():
    splittedCandle = gft(dataOfChart, delimiter=',')
    candlesClose = splittedCandle[:,2]

    SMAs5 = talib.SMA(candlesClose, timeperiod=5)
    SMAs8 = talib.SMA(candlesClose, timeperiod=8)
    SMAs13 = talib.SMA(candlesClose, timeperiod=13)

    currentSMA5 = SMAs5[-2]
    previousSMA5 = SMAs5[-3]

    currentSMA8 = SMAs8[-2]
    previousSMA8 = SMAs8[-3]

    currentSMA13 = SMAs13[-2]
    previousSMA13 = SMAs13[-3]

    if currentSMA5 > previousSMA5 and \
       currentSMA8 > previousSMA8 and \
       currentSMA13 > previousSMA13:
        return True
    else:
        return False

def checkListForMakingOrder():
    RSI_Ready = RSI()
    SMA_Ready = SMA()

    # BB RSI UpTrend
    print(f'{RSI_Ready} | {SMA_Ready}')
    if SMA_Ready and RSI_Ready:
            createOrder()
    else:
        wait(fiveMin)

def createOrder():
    # print(coinex.order_market(CryptoToTrade + 'USDT', 'buy', howMuchShouldIBuy))
    global orderCounter
    print('new order. #', orderCounter)
    print(time.ctime(time.time()))
    orderCounter += 1

    waitForSellPosition()

def checkTheTrend():
    splittedCandle = gft(dataOfChart, delimiter=',')
    candlesClose = splittedCandle[:,2]
    if candlesClose[-2] >= (candlesClose[int(-2 - (trendTimeFrame / 5))] ):
        return 'upTrend'

def wait(second):
    while second:
        mins, secs = divmod(second, 60) 
        timer = 'Time Left: {:02d}:{:02d}'.format(mins, secs) 
        print(timer, end="\r") 
        time.sleep(1) 
        second -= 1

def waitForSellPosition():
    while True:
        checkListForStopOrder()
        wait(fiveMin)

def checkListForStopOrder():
    getDataForAnalyse()
    splittedCandle = gft(dataOfChart, delimiter=',')
    candlesClose = splittedCandle[:,2]
    upperBB, middleBB, lowerBB = talib.BBANDS(candlesClose, timeperiod=timePeriodForBB, nbdevup=nbDev, nbdevdn=nbDev, matype=0)
    profit = checkProfit(candlesClose[-2])

    if candlesClose[-2] > upperBB[-2] \
        or profit <= whenStopLoss \
        or profit >= saveProfit:
            closeOrder()

def checkProfit(sellPrice):
    profit = float(sellPrice / buyPrice)*100 - 100
    return profit

def closeOrder():
    # wallet = coinex.balance_info()
    # assest = (wallet[CryptoToTrade])['available']
    getDataForAnalyse()
    splittedCandle = gft(dataOfChart, delimiter=',')
    candleClose = splittedCandle[:,2][-2]
    global sellPrice
    sellPrice = candleClose
    profit = float(sellPrice / buyPrice)*100 - 100

    # print(coinex.order_limit(CryptoToTrade + 'USDT', 'sell', assest, sellPrice[-2]))
    print(f'Profit: {profit}')
    print('=======================================')

    saveData(profit)
    start()  # Start New Run

def saveData(tradeData):
    tradeDataCSV = open(saveDataHere, 'a', newline='')
    writer = csv.writer(tradeDataCSV)
    date = {time.ctime(time.time())}
    detailOfTrade = (str(tradeData)[:6]), (CryptoToTrade), (date)
    writer.writerow(detailOfTrade)
    tradeDataCSV.close()

print('Turn on the openVPN')
start()