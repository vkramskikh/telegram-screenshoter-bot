#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import urllib
import subprocess
from time import sleep
from selenium import webdriver
from telegram import ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.error import BadRequest
from StringIO import StringIO
import logging

logging.basicConfig(
    filename='bot.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


token = os.environ.get('TELEGRAM_TOKEN')
allowed_chats = map(int, os.environ.get('ALLOWED_CHATS', '').split(','))
allowed_users = os.environ.get('ALLOWED_USERS', '').split(',')
superusers = os.environ.get('SUPERUSERS', '').split(',')
pgm_url = os.environ.get('PGM_URL', 'http://127.0.0.1:5000')


known_allowed_users = {}


keyboard_markup = ReplyKeyboardMarkup(
    keyboard=[[
        KeyboardButton('/screenshot')
    ]],
    resize_keyboard=True,
    selective=True
)


def allowed_only(handler):
    def wrapper(bot, update):
        if (
            update.message.chat_id in allowed_chats or
            update.message.from_user.username in allowed_users or
            update.message.from_user.id in known_allowed_users
        ):
            return handler(bot, update)
        for chat_id in allowed_chats:
            try:
                cm = bot.getChatMember(chat_id, update.message.from_user.id)
                if cm.status not in ('left', 'kicked'):
                    logger.info(
                        'Adding %s to known users',
                        update.message.from_user.username,
                    )
                    known_allowed_users[update.message.from_user.id] = True
                    break
            except BadRequest:
                pass
        else:
            logger.warn(
                '%s attempted to use bot',
                update.message.from_user.username,
            )
            bot.sendMessage(
                update.message.chat_id,
                text="""Бот доступен только для Saratov Mystic"""
            )
            return
        return handler(bot, update)
    return wrapper


def superusers_only(handler):
    def wrapper(bot, update):
        if update.message.from_user.username in superusers:
            return handler(bot, update)
        else:
            logger.warn(
                '%s attempted to use superuser command',
                update.message.from_user.username,
            )
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
@allowed_only
def help(bot, update):
    bot.sendMessage(
        update.message.chat_id,
        text="""Команды: /screenshot""",
        reply_markup=keyboard_markup
    )


@log_update
@allowed_only
def screenshot(bot, update):
    screenshot = take_screenshot(pgm_url)
    bot.sendPhoto(
        update.message.chat_id,
        photo=StringIO(screenshot),
        reply_markup=keyboard_markup
    )


@log_update
@allowed_only
def set_location(bot, update):
    message = update.message
    try:
        lat = message.location.latitude
        lon = message.location.longitude
        urllib.urlopen(
            pgm_url + '/next_loc?lat=%s&lon=%s' % (lat, lon), ''
        ).read()
        bot.sendMessage(
            message.chat_id,
            text="""Локация обновлена!""",
            reply_markup=keyboard_markup
        )
    except:
        bot.sendMessage(
            message.chat_id,
            text="""Ошибка обновления локации!""",
            reply_markup=keyboard_markup
        )


@log_update
@superusers_only
def ifconfig(bot, update):
    bot.sendMessage(
        update.message.chat_id,
        subprocess.check_output('ifconfig')
    )


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
    dp.add_handler(CommandHandler('ifconfig', ifconfig))
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
