#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import urllib
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
pgm_url = os.environ.get('PGM_URL', 'http://127.0.0.1:5000')


def filter_replies(handler):
    def wrapper(bot, update):
        if (
            update.message.chat_id in allowed_ids or
            update.message.from_user.username in allowed_usernames
        ):
            return handler(bot, update)
    return wrapper


def log_update(handler):
    def wrapper(bot, update):
        logger.info(
            '%s - %s - %s',
            update.message.chat_id,
            update.message.from_user.username,
            update.message.text or update.message.location
        )
        return handler(bot, update)
    return wrapper


@log_update
@filter_replies
def help(bot, update):
    bot.sendMessage(update.message.chat_id, text="""Commands: /screenshot""")


@log_update
@filter_replies
def screenshot(bot, update):
    screenshot = take_screenshot(pgm_url)
    bot.sendPhoto(update.message.chat_id, photo=StringIO(screenshot))


@log_update
@filter_replies
def set_location(bot, update):
    message = update.message
    try:
        lat = message.location.latitude
        lon = message.location.longitude
        urllib.urlopen(
            pgm_url + '/next_loc?lat=%s&lon=%s' % (lat, lon)
        ).read()
        bot.sendMessage(message.chat_id, text="""Location updated!""")
    except:
        bot.sendMessage(message.chat_id, text="""Failed to update location!""")


def noop(*args, **kwargs):
    pass


def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


def main():
    updater = Updater(token)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', help))
    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(CommandHandler('screenshot', screenshot))
    dp.add_handler(MessageHandler([Filters.text], log_update(noop)))
    dp.add_handler(MessageHandler([Filters.location], set_location))
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
