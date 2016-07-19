#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from time import sleep
from selenium import webdriver
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from StringIO import StringIO
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


token = os.environ.get('TELEGRAM_TOKEN')
allowed_ids = map(int, os.environ.get('ALLOWED_IDS', '').split(','))
allowed_usernames = os.environ.get('ALLOWED_USERNAMES', '').split(',')
screenshot_url = os.environ.get('SCREENSHOT_URL', 'http://127.0.0.1:5000/')


def filter_replies(handler):
    def wrapper(bot, update):
        if (
            update.message.chat_id in allowed_ids or
            update.message.from_user.username in allowed_usernames
        ):
            return handler(bot, update)
    return wrapper


@filter_replies
def help(bot, update):
    bot.sendMessage(update.message.chat_id, text="""Commands: /screenshot""")


@filter_replies
def screenshot(bot, update):
    screenshot = take_screenshot(screenshot_url)
    bot.sendPhoto(update.message.chat_id, photo=StringIO(screenshot))


def message(bot, update):
    logger.info(
        '%s - %s - %s',
        update.message.chat_id,
        update.message.from_user.username,
        update.message.text
    )


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


def main():
    updater = Updater(token)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', help))
    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(CommandHandler('screenshot', screenshot))
    dp.add_handler(MessageHandler([Filters.text], message))
    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()


def take_screenshot(url):
    driver = webdriver.Chrome('./chromedriver')
    driver.get(url)
    sleep(3)
    screenshot = driver.get_screenshot_as_png()
    driver.close()
    return screenshot

if __name__ == '__main__':
    main()
