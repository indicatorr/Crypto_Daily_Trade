import requests, time, talib, csv
from playsound import playsound
from numpy import genfromtxt as gft
from coinex.coinex import CoinEx
from telegram.ext import Updater, CallbackContext, CommandHandler
from telegram import Update

CryptoToTrade = 'BTC'
timeFrame = '15min'  #1min, 1hour, 1day, 1week
howMuchShouldIBuy = 30  # $
timePeriodForBB = 20
nbDev = .5
twoMinute = 2 * 60
saveProfit = 1.5
whenStopLoss = -.5
leastProfit = .1

telegram_token = '5002478776:AAFcuoK0Qomb57vAJ6SctNrdTW9w-SRvFQE'
updater = Updater(telegram_token, use_context=True)
dispatcher = updater.dispatcher

access_id = '9AB450BFC9574FF2A081D257A691D556'
secret_key = '1343602FFD3EA564E432286088A534EAEC29F8145D1078EC'
coinex = CoinEx(access_id, secret_key)
dataOfChart = 'Data/DataForIndicator_BTC.csv'
saveDataHere = 'Trade_Information/orderHistory_BTC.csv'
buyPrice = 0
sellPrice = 0
currentCandle = -2
orderCounter = 0
totalProfits = 0
totalOrders = []

def listenToTelegram():
    start_handler = CommandHandler('start', start, run_async=True)
    dispatcher.add_handler(start_handler)

    totalOrders_handler = CommandHandler('total_orders', returnTotalOrders, run_async=True)
    dispatcher.add_handler(totalOrders_handler)

    totalProfit_handler = CommandHandler('total_profits', returnTotalProfits, run_async=True)
    dispatcher.add_handler(totalProfit_handler)

    updater.start_polling()

def returnTotalOrders(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'Total Orders:{orderCounter} \n{totalOrders}')

def returnTotalProfits(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'Total Profits:\n{totalProfits}%')

def start(update: Update, context: CallbackContext):
    print(f'Analyze At: {time.ctime(time.time())}')
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'Analyze At: {time.ctime(time.time())} | {CryptoToTrade}')

    while True:
        try:
            getDataForAnalyse()
            checkListForMakingOrder(update, context)
        except Exception as e:
            print('Error...', e)
            print(time.ctime(time.time()))
            context.bot.send_message(chat_id=update.effective_chat.id, text=f'Error!!!! # | time: {time.ctime(time.time())} | cause: {e}')
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

def checkListForMakingOrder(update, context):
    splittedCandle = gft(dataOfChart, delimiter=',')
    candlesClose = splittedCandle[:,2]
    candlesVolume = splittedCandle[:,5]

    MOM_Ready = MOM(candlesClose)
    BBPerB_Ready = BBPerB(candlesClose)
    SMA_Fast_Ready = SMA_Fast(candlesClose)
    OBV_Ready = OBV(candlesClose, candlesVolume)
    
    # print(f'MOM:{MOM_Ready} | BB:{BBPerB_Ready} | SMA-F:{SMA_Fast_Ready}')
    print(f'{MOM_Ready} | {BBPerB_Ready} | {SMA_Fast_Ready} | {OBV_Ready}')

    if MOM_Ready and BBPerB_Ready and SMA_Fast_Ready and OBV_Ready:
        global buyPrice
        buyPrice = candlesClose[currentCandle]
        createOrder(update, context)
    else:
        wait(twoMinute)

def OBV(candlesClose, candlesVolume):
    OBVs = talib.OBV(candlesClose, candlesVolume)
    
    if OBVs[currentCandle - 1] < OBVs[currentCandle]:
        return True
    else:
        return False

def SMA_Fast(candlesClose):
    SMAs5 = talib.SMA(candlesClose, timeperiod=5)
    SMAs21 = talib.SMA(candlesClose, timeperiod=21)
            
    currentSMA5 = SMAs5[currentCandle]
    currentSMA21 = SMAs21[currentCandle]

    if currentSMA5 > currentSMA21:
        return True
    else:
        return False

def BBPerB(candlesClose):
    upper, middle, lower = talib.BBANDS(candlesClose, matype=0)
    BBperB = middle[currentCandle] + (upper[currentCandle] - middle[currentCandle]) / 2

    if candlesClose[currentCandle] > BBperB:
        return True
    else:
        return False

def MOM(candlesClose):
    MOMs = talib.MOM(candlesClose, timeperiod=5)
    currentMOM = MOMs[currentCandle]

    if currentMOM > 0:
        return True
    else:
        return False

def createOrder(update, context):
    global orderCounter
    # print(coinex.order_market(CryptoToTrade + 'USDT', 'buy', howMuchShouldIBuy))
    # print('new order. #', orderCounter)
    orderCounter += 1

    context.bot.send_message(chat_id=update.effective_chat.id, text=f'new order | #{orderCounter} | Time: {time.ctime(time.time())}')

    waitForSellPosition(update, context)

def wait(second):
    while second:
        mins, secs = divmod(second, 60) 
        timer = 'Time Left: {:02d}:{:02d}'.format(mins, secs) 
        second -= 1
        time.sleep(1) 
        print(timer, end="\r") 

def waitForSellPosition(update, context):
    while True:
        checkListForStopOrder(update, context)
        wait(twoMinute)

def checkListForStopOrder(update, context):
    getDataForAnalyse()
    splittedCandle = gft(dataOfChart, delimiter=',')
    candlesClose = splittedCandle[:,2]
    candlesHighest = splittedCandle[:,3]
    upperBB, middleBB, lowerBB = talib.BBANDS(candlesClose, timeperiod=timePeriodForBB, nbdevup=nbDev, nbdevdn=nbDev, matype=0)
    profit = checkProfit(candlesClose[currentCandle])

    if candlesHighest[currentCandle] > upperBB[currentCandle] \
        and profit >= leastProfit \
        or profit <= whenStopLoss \
        or profit >= saveProfit:
            closeOrder(update, context)

def checkProfit(sellPrice):
    profit = float(sellPrice / buyPrice)*100 - 100
    return profit

def closeOrder(update, context):
    # wallet = coinex.balance_info()
    # assest = (wallet[CryptoToTrade])['available']
    getDataForAnalyse()
    splittedCandle = gft(dataOfChart, delimiter=',')
    candleClose = splittedCandle[:,2][currentCandle]
    global sellPrice
    sellPrice = candleClose
    profit = float(sellPrice / buyPrice)*100 - 100

    # print(coinex.order_limit(CryptoToTrade + 'USDT', 'sell', assest, sellPrice[currentCandle]))
    # print(f'Profit: {profit}')
    # print('=======================================')
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'order {orderCounter} closed | profit: {profit}')

    saveData(profit)
    start(update, context)  # Start New Run

def saveData(tradeData):
    tradeDataCSV = open(saveDataHere, 'a', newline='')
    writer = csv.writer(tradeDataCSV)
    date = {time.ctime(time.time())}
    detailOfTrade = (str(tradeData)[:6]), (CryptoToTrade), (date)
    writer.writerow(detailOfTrade)
    tradeDataCSV.close()

    totalOrders.append([str(tradeData)[:6], CryptoToTrade, date])

    global totalProfits
    totalProfits += float(str(tradeData)[:6])

listenToTelegram()