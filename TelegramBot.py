from telegram.ext import Updater, CallbackContext, CommandHandler
from telegram import Update
import os

import ETH as crypto

telegram_token = os.getenv('TELEGRAM_KEY_ETH')
updater = Updater(telegram_token, use_context=True)
dispatcher = updater.dispatcher

def listenToTelegram():
    start_handler = CommandHandler('start', start, run_async=True)
    dispatcher.add_handler(start_handler)

    totalOrders_handler = CommandHandler('total_orders', returnTotalOrders, run_async=True)
    dispatcher.add_handler(totalOrders_handler)

    totalProfit_handler = CommandHandler('total_profits', returnTotalProfits, run_async=True)
    dispatcher.add_handler(totalProfit_handler)

    status_handler = CommandHandler('status', status, run_async=True)
    dispatcher.add_handler(status_handler)

    stopNew_handler = CommandHandler('stop_new', stopNew, run_async=True)
    dispatcher.add_handler(stopNew_handler)

    startNew_handler = CommandHandler('start_new', stopNew, run_async=True)
    dispatcher.add_handler(startNew_handler)

    areYouOk_handler = CommandHandler('are_you_ok', iAmOk, run_async=True)
    dispatcher.add_handler(areYouOk_handler)

    updater.start_polling()

def returnTotalOrders(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'Total Orders:{crypto.orderCounter} \n{crypto.totalOrders}')

def returnTotalProfits(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'Total Profits:\n{str(crypto.totalProfits)[:4]}%')

def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text=f'---------------------------------------------------------')
    print('---------------------------------------------------------')
    crypto.run(update, context)

def stopNew(update: Update, context: CallbackContext):
    crypto.startNew = False

def startNew(update: Update, context: CallbackContext):
    crypto.startNew = True

def iAmOk(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text='I Am Ok Alexander, Thanks For Asking. 💚💻')

def status(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text=crypto.startNew)