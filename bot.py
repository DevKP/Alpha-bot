# -*- coding: utf-8 -*-
import logging
import os
import re
import shutil
from pathlib import Path
from random import randrange
from time import sleep
import calendar
from datetime import timedelta
from datetime import datetime
import json
import threading
from PIL import Image, ImageFont, ImageDraw, ImageFilter
import xml.etree.ElementTree as etree
import cherrypy
import requests

import telebot
from telebot import types
from telethon import TelegramClient

import config
import nextstream
import picturedetect
import ru_strings
import birthdays
import utils
from utils import logger
from utils import bot

from wit import Wit
from gtts import gTTS


client = Wit(config.WIT_token)

chatusers = 0
with TelegramClient("Session", config.api_id, config.api_hash) as Tclient:
    chatusers = Tclient.get_participants(config.send_chat_id)

allow_processing = False


def onStartProcessing():
    global allow_processing
    allow_processing = True
    logger.info("Alpha-Bot started!")


# class WebhookServer(object):
#     @cherrypy.expose
#     def index(self):
#         if 'content-length' in cherrypy.request.headers and \
#                         'content-type' in cherrypy.request.headers and \
#                         cherrypy.request.headers['content-type'] == 'application/json':
#             length = int(cherrypy.request.headers['content-length'])
#             json_string = cherrypy.request.body.read(length).decode("utf-8")
#
#             # print(json_string)
#
#             update = telebot.types.Update.de_json(json_string)
#             if allow_processing is True:
#                 bot.process_new_updates([update])
#             return ''
#         else:
#             raise cherrypy.HTTPError(403)


SEND_MESSAGE, REPLY_MESSAGE = range(2)


def random_message(message, string_list, mode):
    '''
    Sands random massage and sticker

    Parameters
        ----------
        message : str
            message from  chat
        string_list : str
            Json list with texts
        mode : type
            SEND_MESSAGE, REPLY_MESSAGE
    '''

    strings_num = len(string_list['strings'])
    r_number = randrange(0, strings_num, 1)

    if string_list['strings'] and string_list['strings'][r_number]:
        if mode is SEND_MESSAGE:
            bot.send_message(message.chat.id, string_list['strings'][r_number], parse_mode='Markdown')
        elif mode is REPLY_MESSAGE:
            bot.reply_to(message, string_list['strings'][r_number], parse_mode='Markdown')
    if string_list['stickers'] and string_list['stickers'][r_number]:
        bot.send_sticker(message.chat.id, string_list['stickers'][r_number])


# Еще один костыль
def listener(messages):
    try:
        for msg in messages:
            if msg.text is not None:
                logger.info("[CHAT] {} ({}): {}".format(
                        msg.from_user.first_name, msg.from_user.id, msg.text))
    except Exception as e:
        logger.error("[Update listener] unexpected error: {}".format(e))


@bot.message_handler(commands=['rate'])
def rate_command(message):
    if "@" in message.text:
        if "alphaofftopbot" not in message.text:
            return

    msg_to_update = bot.send_message(message.chat.id, "*loading..*", parse_mode='Markdown')
    update_crypto_rate(msg_to_update)


@bot.message_handler(func=lambda m: True, content_types=['new_chat_members'])
def on_user_joins(message):
    logger.info("New chat member, username: @{:s}".format(
                                             message.from_user.username or "NONE"))
    print(message)
    if re.search(r"\b[bб6][оo][т7t]\b", message.from_user.first_name, re.IGNORECASE | re.UNICODE) or \
        re.search(r"\b[bб6][оo][т7t]\b", message.from_user.last_name, re.IGNORECASE | re.UNICODE):
        if message.from_user.username is not None:
            username_str = '@{}'.format(message.from_user.username)
        else:
            username_str = message.from_user.first_name or 'Ноунейм'
        message_str = "Возможно [{}] - это бот!\n@via_tcp\n@content_of_brain\n@lopotyana".format(username_str)
        bot.send_message(message.chat.id, message_str)
        bot.restrict_chat_member(message.chat.id, message.from_user.id, 0, False, False, False, False)
        return

    # Use firstname if username is NONE
    if message.from_user.username is not None:
        username_str = '@{}'.format(message.from_user.username)
    else:
        username_str = message.from_user.first_name or 'Ноунейм'
    message_str = "{} готов(а) сжигать пукан свой в пепел вместе с нами!!🔥\nВстречайте героя!👻".format(
        username_str)
    bot.send_message(message.chat.id, message_str)


# @bot.message_handler(func=lambda m: True, content_types=['new_chat_members'])
# def on_user_joins(message):
#     logger.info("New chat member, username: @{:s}".format(
#                                        message.from_user.username or "NONE"))
#
#    keyboard = types.InlineKeyboardMarkup()
#
#     choice1 = types.InlineKeyboardButton(
#        "Суицид!", callback_data='choice1$' + str(message.from_user.id))
#
#     choice2 = types.InlineKeyboardButton(
#        "Вперед!", callback_data='choice2$' + str(message.from_user.id))
#
#    keyboard.row(choice1, choice2)
#
#     # Use firstname if username is NONE
#     if message.from_user.username is not None:
#         username_str = '@{}'.format(message.from_user.username)
#     else:
#        username_str = message.from_user.first_name or 'Ноунейм'
#
#     message_str = '{}! Готов(а) ли ты сжигать пукан свой в пепел вместе с нами?🔥'.format(
#        username_str)
#
#     # Temporary restrict user
#    bot.send_message(message.chat.id, message_str, reply_markup=keyboard)
#
#     # Catch "can't demote chat creator" Exception
#     try:
#         bot.restrict_chat_member(
#             message.chat.id, message.from_user.id, 1, False, False, False, False)
#     except Exception:
#         logger.info("[EXCEPTION] Bad Request: can't demote chat creator!")


@bot.callback_query_handler(func=lambda call: 'choice' in call.data)
def chair_bonjour(call):
    new_user_id = call.data[len('choice1$'):]  # substring ID from callback data
    if new_user_id != str(call.from_user.id):  # Ignore existing chat memders
        return

    # Delete our message
    bot.delete_message(call.message.chat.id, call.message.message_id)
    if 'choice1' in call.data:  # First button or second button(choice1 or choice2)

        logger.info("[Bonjour]: @{:s} pressed FIRST button!".format(
            call.from_user.username or "NONE"))

        # Getting current timestamp
        d = datetime.utcnow()
        d = d + timedelta(0, 30)
        timestamp = calendar.timegm(d.utctimetuple())

        # Catch "user is an administrator of the chat" Exception
        try:
            # Ban user from chat for 30 seconds
            bot.kick_chat_member(call.message.chat.id, new_user_id, until_date=timestamp)
        except Exception:
            logger.info("[EXCEPTION] Bad Request: User is an administrator of the chat!")
    else:
        logger.info("[Bonjour]: @{:s} pressed SECOND button!".format(
            call.from_user.username or "NONE"))

        # Use firstname if username is NONE
        if call.from_user.username is not None:
            username_str = '@{}'.format(call.from_user.username)
        else:
            username_str = call.from_user.first_name or 'Ноунейм'

        bot.send_message(call.message.chat.id, username_str
                         + ' решил(а) остатся!☝️ \nВстречайте героя!👻')

        # Catch "can't demote chat creator" Exception
        try:
            # Unrestrict user
            bot.restrict_chat_member(
                call.message.chat.id, call.from_user.id, 1, True, True, True, True)
        except Exception:
            logger.info("[EXCEPTION] Bad Request: can't demote chat creator!")


def update_crypto_rate(message):
    text = ''
    resp = requests.get("https://min-api.cryptocompare.com/data/generateAvg?fsym=BTC&tsym=USD&e=Poloniex,Kraken,Coinbase,Bitfinex&extraParams=Persik")
    if resp.status_code == 200:
        json_obj = json.loads(resp.content.decode("utf-8"))
        text += "1 btc = {}$ ({:.2f}% / 24h)".format(json_obj['RAW']['PRICE'], json_obj['RAW']['CHANGEPCT24HOUR'])
        if json_obj['RAW']['CHANGEPCT24HOUR'] > 0:
            text += "💹\n"
        else:
            text += "🔻\n"
    resp = requests.get("https://min-api.cryptocompare.com/data/generateAvg?fsym=ETH&tsym=USD&e=Poloniex,Kraken,Coinbase,Bitfinex&extraParams=Persik")
    if resp.status_code == 200:
        json_obj = json.loads(resp.content.decode("utf-8"))
        text += "1 eth = {}$ ({:.2f}% / 24h)".format(json_obj['RAW']['PRICE'], json_obj['RAW']['CHANGEPCT24HOUR'])
        if json_obj['RAW']['CHANGEPCT24HOUR'] > 0:
            text += "💹\n"
        else:
            text += "🔻\n"
    resp = requests.get("https://min-api.cryptocompare.com/data/generateAvg?fsym=ETC&tsym=USD&e=Poloniex,Kraken,Bitfinex&extraParams=Persik")
    if resp.status_code == 200:
        json_obj = json.loads(resp.content.decode("utf-8"))
        text += "1 etc = {}$ ({:.2f}% / 24h)".format(json_obj['RAW']['PRICE'], json_obj['RAW']['CHANGEPCT24HOUR'])
        if json_obj['RAW']['CHANGEPCT24HOUR'] > 0:
            text += "💹\n"
        else:
            text += "🔻\n"
    resp = requests.get("https://min-api.cryptocompare.com/data/generateAvg?fsym=ZEC&tsym=USD&e=Poloniex,Kraken,Bitfinex&extraParams=Persik")
    if resp.status_code == 200:
        json_obj = json.loads(resp.content.decode("utf-8"))
        text += "1 zec = {}$ ({:.2f}% / 24h)".format(json_obj['RAW']['PRICE'], json_obj['RAW']['CHANGEPCT24HOUR'])
        if json_obj['RAW']['CHANGEPCT24HOUR'] > 0:
            text += "💹\n"
        else:
            text += "🔻\n"
    resp = requests.get("https://min-api.cryptocompare.com/data/generateAvg?fsym=LTC&tsym=USD&e=Poloniex,Kraken,Coinbase,Bitfinex&extraParams=Persik")
    if resp.status_code == 200:
        json_obj = json.loads(resp.content.decode("utf-8"))
        text += "1 ltc = {}$ ({:.2f}% / 24h)".format(json_obj['RAW']['PRICE'], json_obj['RAW']['CHANGEPCT24HOUR'])
        if json_obj['RAW']['CHANGEPCT24HOUR'] > 0:
            text += "💹\n"
        else:
            text += "🔻\n"
    resp = requests.get("https://min-api.cryptocompare.com/data/generateAvg?fsym=BCH&tsym=USD&e=Exmo&extraParams=Persik")
    if resp.status_code == 200:
        json_obj = json.loads(resp.content.decode("utf-8"))
        text += "1 bch = {}$ ({:.2f}% / 24h)".format(json_obj['RAW']['PRICE'], json_obj['RAW']['CHANGEPCT24HOUR'])
        if json_obj['RAW']['CHANGEPCT24HOUR'] > 0:
            text += "💹\n\n"
        else:
            text += "🔻\n\n"

    text += datetime.strftime(datetime.now(), "%d.%m.%Y %H:%M")

    keyboard = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton("Update", callback_data='update')
    keyboard.add(button)

    bot.edit_message_text(text, message.chat.id, message.message_id, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data == 'update')
def update_btn(call):
    bot.edit_message_text("*Updating...*", call.message.chat.id,
                          call.message.message_id, parse_mode='Markdown')
    update_crypto_rate(call.message)


@bot.message_handler(commands=['exch'])
def exch_command(message):
    resp = requests.get("http://cbr.ru/scripts/XML_daily.asp", stream=True)
    if resp.status_code == 200:
        root = etree.fromstring(resp.content.decode(
             "windows-1251").encode('utf-8').decode('utf-8'))

        exch = ''
        for valute in root.findall('Valute'):
            if valute.get('ID') == 'R01235':
                exch = valute.find('Value').text
                break
        bot.send_message(message.chat.id, "1 USD = {} RUB".format(
            exch), parse_mode='Markdown')

    resp = requests.get("http://www.nbrb.by/API/ExRates/Rates/USD?ParamMode=2")
    if resp.status_code == 200:
        json_obj = json.loads(resp.content.decode("utf-8"))
        bot.send_message(message.chat.id, "1 USD = {} BYN".format(
            json_obj['Cur_OfficialRate']), parse_mode='Markdown')
    resp = requests.get(
        "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json")
    if resp.status_code == 200:
        json_obj = json.loads(resp.content.decode("utf-8"))
        exch = ''
        for curr in json_obj:
            if curr['cc'] == 'USD':
                exch = curr['rate']
                break
        bot.send_message(message.chat.id, "1 USD = {} UAH".format(
            exch), parse_mode='Markdown')


#@bot.message_handler(commands=['test'])
#def test_command(message):

    #markup = types.InlineKeyboardMarkup()
    #itembtn1 = types.InlineKeyboardButton('TEST', callback_data='test')
    #markup.add(itembtn1)
    #bot.send_message(message.chat.id, "Нажми для теста", reply_markup=markup)
    #sleep(2)
    # bot.answer_callback_query('TEST', "СУКА ЧТО ЭТО ЗА ПОЕБЕНЬ?", show_alert=True)


# @bot.callback_query_handler(func=lambda call: call.data == 'test')
# def test_callback_answer(call):
#    bot.answer_callback_query(call.id, "Тест Тест\n\nПеренос строки\nЭмоджики 🤯👍🙄👀👄🖖🏽🖐🦷👄", show_alert=True)


@bot.message_handler(content_types=['sticker'])
def sticker_message(msg):
    if any(msg.sticker.file_id == sticker_ID for sticker_ID in config.stickers_black_list):
        bot.delete_message(msg.chat.id, msg.message_id)
        logger.info("{:s}: [STICKER] {:s} in BLACKLIST! Deleted!".format(
            msg.from_user.first_name, msg.sticker.file_id))

    logger.info("{:s}: [STICKER] {:s}".format(
        msg.from_user.first_name, msg.sticker.file_id))


@bot.message_handler(content_types=['document'])
def document_message(msg):
    logger.info("{:s}: [DOCUMENT] {:s}".format(msg.from_user.first_name,
                                               msg.document.file_id))

    try:
        os.makedirs("./documents")
    except FileExistsError:
        pass

    file_info = bot.get_file(msg.document.file_id)
    utils.file_download(file_info, './documents/')


@bot.message_handler(commands=['everyone'])
def everyone_command(message):
    administrators = bot.get_chat_administrators(config.send_chat_id)
    if any(message.from_user.id == member.user.id for member in administrators):
        logger.info("/everyone command by {:s}, Username @{:s}"
                     .format(message.from_user.first_name, (message.from_user.username or "NONE")))
        message_text = ""
        bot.send_message(message.chat.id, "*@everyone* 😈", parse_mode='Markdown')
        for x in range(0, len(chatusers)):
            message_text += "[.](tg://user?id=" + str(chatusers[x].id) + ") "
            if (x + 1) % 10 == 0:
                bot.send_message(message.chat.id, message_text, parse_mode='Markdown')
                message_text = ""

        if len(message_text) > 1:
            bot.send_message(message.chat.id, message_text, parse_mode='Markdown')


@bot.message_handler(commands=['start'])
def start_command(message):
    logger.info("/start command by {:s}, Username {:s}"
                .format(message.from_user.first_name, (message.from_user.username or "NONE")))

    if message.chat.id > 0:
        bot.send_message(message.chat.id, ru_strings.START_MESSAGE['strings'][0].format(message.chat.first_name))
        sleep(2)
        info_command(message)


@bot.message_handler(commands=['nextstream'])
def next_stream_command(message):
    logger.info("/nextstream command by {:s}, Username @{:s}"
                .format(message.from_user.first_name, (message.from_user.username or "NONE")))
    bot.send_message(message.chat.id, nextstream.get_next_stream_msg(), parse_mode='HTML')


@bot.message_handler(commands=['gotospace'])
def gotospace_command(message):
    logger.info("/gotospace command by {:s}, Username @{:s}"
                .format(message.from_user.first_name, (message.from_user.username or "NONE")))
    bot.send_message(message.chat.id, ru_strings.OFFTOP_COMMAND_MESSAGE, parse_mode='Markdown')


@bot.message_handler(commands=['info'])
def info_command(message):
    logger.info("/info command by {:s}, Username @{:s}"
                .format(message.from_user.first_name, (message.from_user.username or "NONE")))
    bot.send_message(message.chat.id, ru_strings.INFO_COMMAND_MESSAGE, parse_mode='Markdown')

@bot.message_handler(commands=['mc'])
def msg_count_command(message):
    logger.info("/msg_count command by {:s}, Username @{:s}"
                .format(message.from_user.first_name, (message.from_user.username or "NONE")))
    bot.send_message(message.chat.id, "*{} сообщений в чате*".format(message.message_id), parse_mode='Markdown')

@bot.message_handler(commands = ['msg'])
def send_msg_command(message):
    logger.info("/msg command by {:s}, Username @{:s}"
                .format(message.from_user.first_name, (message.from_user.username or "NONE")))

    if message.chat.type != "private":
        return

    administrators = bot.get_chat_administrators(config.send_chat_id)
    if any(message.from_user.id == member.user.id for member in administrators) or message.from_user.id == 204678400:
        logger.info("The owner detected!")
        bot.send_message(message.chat.id, ru_strings.SEND_MSG_MESSAGE['strings'][0], parse_mode='Markdown')
        bot.register_next_step_handler(message, send_message)
    else:
        logger.info("This isn't the owner!")


def send_message(message):
    if message.text:
        if message.text.find('/cancel') != -1:
            bot.send_message(
                message.chat.id, ru_strings.CANCEL_MESSAGE['strings'][0], parse_mode='Markdown')
        else:
            bot.send_message(config.send_chat_id,
                             message.text, parse_mode='Markdown')
            logger.info("Sending message {:s} to chat {:d}".format(
                message.text, config.send_chat_id))
            bot.send_message(
                message.chat.id, ru_strings.SEND_MSG_MESSAGE['strings'][1], parse_mode='Markdown')
    elif message.photo:

        try:
            os.makedirs("./photos")
        except FileExistsError:
            pass

        file_id = message.photo[len(message.photo) - 1].file_id
        file_info = bot.get_file(file_id)
        file_patch = utils.file_download(file_info, './photos/')
        with open(file_patch, 'rb') as photo:
            bot.send_photo(config.send_chat_id, photo)

        logger.info("Sending photo {:s} to chat {:d}".format(
            file_id, config.send_chat_id))
        bot.send_message(
            message.chat.id, ru_strings.SEND_MSG_MESSAGE['strings'][1], parse_mode='Markdown')


@bot.message_handler(commands=['stk'])
def stk_command(message):
    logger.info("/stk command by {:s}, Username @{:s}"
                .format(message.from_user.first_name, (message.from_user.username or "NONE")))

    if message.chat.type != "private":
        return

    administrators = bot.get_chat_administrators(config.send_chat_id)
    if any(message.from_user.id == member.user.id for member in administrators):
        logger.info("The owner detected!")
        bot.send_message(
            message.chat.id, ru_strings.SEND_STICKER_MESSAGE['strings'][0], parse_mode='Markdown')
        bot.register_next_step_handler(message, send_sticker)
    else:
        logger.info("This isn't the owner!")


def send_sticker(message):
    if message.content_type != 'sticker':
        if message.text is not None:
            if message.text.find('/cancel') != -1:
                bot.send_message(
                    message.chat.id, ru_strings.CANCEL_MESSAGE['strings'][0], parse_mode='Markdown')
            else:
                bot.send_message(
                    message.chat.id, ru_strings.SEND_STICKER_MESSAGE['stickers'][1], parse_mode='Markdown')
                bot.register_next_step_handler(message, send_sticker)
    else:
        bot.send_sticker(config.send_chat_id, message.sticker.file_id)

        logger.info("Sending sticker {:s} to chat {:d}".format(
            message.sticker.file_id, config.send_chat_id))


@bot.message_handler(commands=['getuserid'])
def get_user_id_message(message):
    if message.forward_from:
        return
    logger.info("/getuserid command by {:s}, Username @{:s}"
                .format(message.from_user.first_name, (message.from_user.username or "NONE")))

    bot.reply_to(message, ru_strings.GET_ID_MESSAGE['strings'][0].format(
        message.from_user.id), parse_mode='Markdown')


@bot.message_handler(commands=['getphoto'])
def get_photo_message(message):
    logger.info("/getphoto command by {:s}, Username @{:s}"
                .format(message.from_user.first_name, (message.from_user.username or "NONE")))

    if '/' in message.text[10:] or '\\' in message.text[10:]:
        return

    try:
        os.makedirs("./photos")
    except FileExistsError:
        pass

    _file = Path('./photos/{}.jpg'.format(message.text[10:]))
    if _file.is_file() is not True:
        logger.info("/getphoto command [NOT FOUND]")
        return

    with open('./photos/{}.jpg'.format(message.text[10:]), 'rb') as photo:
        bot.send_photo(message.chat.id, photo, message.message_id)


@bot.message_handler(commands=['getdocument'])
def get_document_message(message):
    logger.info("/getdocument command by {:s}, Username @{:s}"
                .format(message.from_user.first_name, (message.from_user.username or "NONE")))
    print(message.text[13:])
    bot.send_document(message.chat.id, message.text[13:], message.message_id)


def birthday_method():
    '''
    Automatically publishes greetings from the list

    Still in test mode!
    TODO: replace chat_id
    '''

    logger.info('Birthday thread started!')
    chat_id = '-1001464920421'  # Test chat id

    while True:
        todaytime = datetime.today()
        if bot.get_chat(chat_id).pinned_message is not None:
            pinnedmessage = bot.get_chat(chat_id).pinned_message.text
        else:
            pinnedmessage = 'none'

        for birthday in birthdays.BIRTHDAYS_LIST:

            birthdatetime = birthday[birthdays.date]
            delta = birthdatetime - todaytime

            # print(delta.total_seconds())

            if(delta.total_seconds() < 0 and delta.total_seconds() > -86400):
                # 86400 secs = 24 hours
                pinmessage = birthday[birthdays.message]
                if(pinmessage != pinnedmessage):
                    # bot.send_message(message.chat.id, "ЗАМЕНИТЬ ВСЕ НАХРЕН") #DEBUG

                    msg_topin = bot.send_message(chat_id, birthday[birthdays.message])
                    sleep(1)  # Antispam
                    bot.pin_chat_message(chat_id, msg_topin.message_id)
                    # bot.send_message(message.chat.id, "ВСЕ ВЕРНО") #DEBUG
        sleep(30*60)


def extract_revenue(D):
    try:
        return float(D[1]['btc_revenue24'])
    except KeyError:
        return 0


def makeShadow(image, iterations, border, offset, backgroundColour, shadowColour):
    '''
    Shadow rendering algorithm
    '''


    fullWidth = image.size[0] + abs(offset[0]) + 2*border
    fullHeight = image.size[1] + abs(offset[1]) + 2*border

    shadow = Image.new(image.mode, (fullWidth, fullHeight), backgroundColour)

    shadowLeft = border + max(offset[0], 0)
    shadowTop = border + max(offset[1], 0)

    shadow.paste(shadowColour,
                 [shadowLeft, shadowTop,
                  shadowLeft + image.size[0],
                  shadowTop + image.size[1]])

    for i in range(iterations):
        shadow = shadow.filter(ImageFilter.BLUR)

    imgLeft = border - min(offset[0], 0)
    imgTop = border - min(offset[1], 0)
    shadow.paste(image, (imgLeft, imgTop))

    return shadow


@bot.message_handler(commands=['whattomine'])
def whattomine_command(m):
    '''
    Draws image
    '''

    image = Image.new("RGBA", (640, 1260), (255, 255, 255, 255))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype('arial', 24)

    pop_curr = {"ZEC", "ETH", "ETC"}

    url = 'http://whattomine.com/coins.json?utf8=%E2%9C%93&adapt_q_280x=0&adapt_q_380=0&adapt_q_fury=0&adapt_q_470=0&adapt_q_480=3&adapt_q_570=0&adapt_q_580=0&adapt_q_750Ti=0&adapt_q_1050Ti=0&adapt_q_10606=1&adapt_q_1070=0&adapt_q_1080=0&adapt_q_1080Ti=0&eth=true&factor%5Beth_hr%5D=23&factor%5Beth_p%5D=90.0&grof=true&factor%5Bgro_hr%5D=20.5&factor%5Bgro_p%5D=90.0&x11gf=true&factor%5Bx11g_hr%5D=7.2&factor%5Bx11g_p%5D=90.0&cn=true&factor%5Bcn_hr%5D=510&factor%5Bcn_p%5D=70.0&eq=true&factor%5Beq_hr%5D=320&factor%5Beq_p%5D=90.0&lre=true&factor%5Blrev2_hr%5D=25000&factor%5Blrev2_p%5D=90.0&ns=true&factor%5Bns_hr%5D=500.0&factor%5Bns_p%5D=90.0&lbry=true&factor%5Blbry_hr%5D=170.0&factor%5Blbry_p%5D=90.0&bk2bf=true&factor%5Bbk2b_hr%5D=990.0&factor%5Bbk2b_p%5D=80.0&bk14=true&factor%5Bbk14_hr%5D=1550.0&factor%5Bbk14_p%5D=90.0&pas=true&factor%5Bpas_hr%5D=580.0&factor%5Bpas_p%5D=90.0&skh=true&factor%5Bskh_hr%5D=18.0&factor%5Bskh_p%5D=90.0&factor%5Bl2z_hr%5D=420.0&factor%5Bl2z_p%5D=300.0&factor%5Bcost%5D=0.0&sort=Profitability24&volume=0&revenue=24h&factor%5Bexchanges%5D%5B%5D=&factor%5Bexchanges%5D%5B%5D=abucoins&factor%5Bexchanges%5D%5B%5D=bitfinex&factor%5Bexchanges%5D%5B%5D=bittrex&factor%5Bexchanges%5D%5B%5D=bleutrade&factor%5Bexchanges%5D%5B%5D=cryptopia&factor%5Bexchanges%5D%5B%5D=hitbtc&factor%5Bexchanges%5D%5B%5D=poloniex&factor%5Bexchanges%5D%5B%5D=yobit'
    resp = requests.get(url)
    if resp.status_code == 200:
        json_obj = json.loads(resp.content.decode("utf-8"))

        json_obj['coins'] = sorted(json_obj['coins'].items(), key=extract_revenue, reverse=True)

        offset = 80

        upper_offset = 14
        centre_offset = 28
        lower_offset = 42

        left_offset = 20
        vert_offset = 60

        btc_price = 0
        btc_resp = requests.get("https://min-api.cryptocompare.com/data/generateAvg?fsym=BTC&tsym=USD&e=Poloniex,Kraken,Coinbase,Bitfinex&extraParams=Persik")
        if btc_resp.status_code == 200:
            btc_obj = json.loads(btc_resp.content.decode("utf-8"))
            btc_price = float(btc_obj['RAW']['PRICE'])

            topcard = Image.new("RGBA", (650, vert_offset),
                                (38, 193, 255, 255))
            topcard = makeShadow(topcard, 10, 14, (0, 1),
                                 (255, 255, 255), (80, 80, 80))

            image.paste(topcard, (-20, -15))
            draw.text((30, 16), "Name(Tag)", font=ImageFont.truetype(
                'arialbd', 24), fill='black')
            draw.text((290, 16), "Rewards 24h", font=ImageFont.truetype(
                'arialbd', 24), fill='black')
            draw.text((492, 16), "Rev. $", font=ImageFont.truetype(
                'arialbd', 24), fill='black')

            for i in range(15):
                vert_y_line = vert_offset + offset * i
                vert_y_text = vert_offset + (offset * i)

                if i != 0:
                    draw.line([(0, vert_y_line), (640, vert_y_line)],
                              fill=(210, 214, 213))

                name = json_obj['coins'][i][0]
                algo = json_obj['coins'][i][1]["algorithm"]

                tag = json_obj['coins'][i][1].get('tag')
                if tag != "NICEHASH":
                    name += "({})".format(tag)

                draw.text((left_offset, vert_y_text + upper_offset),
                          name, font=font, fill='black')
                draw.text((left_offset-1, vert_y_text + lower_offset),
                          algo, font=font, fill=(140, 140, 140))

                intersec = {tag} & pop_curr
                if len(intersec) != 0:
                    draw.rectangle(
                        [(0, vert_y_text+1), (10, vert_y_text + offset - 1)], fill=(39, 186, 77))

                profit = float(json_obj['coins'][i][1]
                               ['btc_revenue24']) * btc_price
                revardcoin = float(json_obj['coins'][i][1]['estimated_rewards24'])

                draw.text((320, vert_y_text + centre_offset),
                          "{rev24:.5f}".format(rev24=revardcoin), font=font, fill='black')
                draw.text((500, vert_y_text + centre_offset),
                          "{rev:.2f}$".format(rev=profit), font=font, fill='black')
        else:
            print("BTC price get error " + str(btc_resp.status_code))

        image.save('./tmp_whattomine.png', 'PNG')
        with open('./tmp_whattomine.png', 'rb') as photo:
            bot.send_photo(m.chat.id, photo)

    else:
        print("WTM coins get error " + str(resp.status_code))


allow_nsfw = False
@bot.message_handler(commands=['togglensfw'])
def togglensfw(message):
    global allow_nsfw

    administrators = bot.get_chat_administrators(config.send_chat_id)
    if any(message.from_user.id == member.user.id for member in administrators):

        allow_nsfw = not allow_nsfw

        if allow_nsfw is True:
            bot.send_message(message.chat.id, ru_strings.NSFW_TOGGLE_MESSAGE['strings'][1], parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, ru_strings.NSFW_TOGGLE_MESSAGE['strings'][0], parse_mode='Markdown')

        logger.info("/togglensfw command by {:s}, Username @{:s}".format(
            message.from_user.first_name, (message.from_user.username or "NONE")))


@bot.message_handler(content_types=["photo"])
def photo_receive(message):
    '''
    Recognizes photos with the comment "персик"
    Ban for NSFW
    '''

    file_id = message.photo[len(message.photo) - 1].file_id

    if message.caption and message.forward_from is None:
        if re.match('(?i)(\W|^).*?!п[eеэ][pр][cс](и|ч[eеи]к).*?(\W|$)', message.caption):
            bot.reply_to(message, "".join([message.from_user.first_name, picturedetect.reply_get_concept_msg(file_id)]),
                        parse_mode='Markdown')

    logger.info("Photo by Username @{:s} | ID {:s}".format((message.from_user.username or "NONE"), file_id))

    try:
        os.makedirs("./photos")
    except FileExistsError:
        pass

    file_patch = './photos/{:s}.jpg'.format(file_id)
    _file = Path(file_patch)
    if _file.is_file() is not True:
        file_info = bot.get_file(file_id)
        file_patch = utils.file_download(file_info, './photos/')

    if file_patch is None:
        logger.error("File download error!'")

        bot.reply_to(message, ru_strings.SOME_ERROR_MESSAGE['strings'], parse_mode='Markdown')
        bot.send_sticker(message.chat.id, ru_strings.SOME_ERROR_MESSAGE['stickers'][0])

        return

    if not allow_nsfw:
        if picturedetect.nsfw_test(file_patch, 0.75):
            bot.delete_message(message.chat.id, message.message_id)

            bot.send_message(message.chat.id, "*{} уходит в бан на {} {}! Причина: NSFW*"
                            .format(message.from_user.first_name, 2, 'мин.'), parse_mode='Markdown')
            ban_user(message.chat.id, message.from_user.id, 2*60)


@bot.message_handler(regexp='.*?((б)?[еeе́ė]+л[оoаaа́â]+[pр][уyу́]+[cсċ]+[uи́иеe]+[я́яию]+).*?')
def byban(message):
    '''
    Restriction for all versions of word Беларуссия
    '''

    bot.send_sticker(message.chat.id, 'CAADAgADGwAD0JwyGF7MX7q4n6d_Ag', reply_to_message_id=message.message_id)

    if message.chat.type == 'private':
        return
    else:
        bot.send_message(message.chat.id, "*{} ушел искать белоруссию на 5 минут!*"
                        .format(message.from_user.first_name), parse_mode='Markdown')
        ban_user(message.chat.id, message.from_user.id, 60*5)


@bot.message_handler(regexp='(?i)(\W|^).*?!п[eеэpр][pрeеэ][cс](и|ч[eеи]к).*?(\W|$)')
def persik_keyword(message):
    if message.forward_from:
        return
    try:
        logger.info("!Persik command by {:s}, Username @{:s}".
                    format(message.from_user.first_name, (message.from_user.username or "NONE")))

        if message.reply_to_message and message.reply_to_message.photo:
            file_info = bot.get_file(
                message.reply_to_message.photo[len(message.reply_to_message.photo) - 1].file_id)
            msg = picturedetect.reply_get_concept_msg(file_info.file_id)
            if msg is None:
                bot.reply_to(message, ru_strings.SOME_ERROR_MESSAGE['strings'], parse_mode='Markdown')
                bot.send_sticker(message.chat.id, ru_strings.SOME_ERROR_MESSAGE['stickers'][0])
                return

            bot.delete_message(message.chat.id, message.message_id)
            bot.reply_to(message.reply_to_message, "".join([message.from_user.first_name, msg]), parse_mode='Markdown')
            return

        if len(message.text) < 10:
            come_here_message(message)
            return

        for template in MESSAGE_TEMPLATES:
            if re.search(template[0], message.text, re.I | re.U):
                template[1](message)
                return

        random_message(message, ru_strings.NA_MESSAGE, REPLY_MESSAGE)

        logger.info("UNKNOWN command by {:s}, Username @{:s}"
                    .format(message.from_user.first_name, (message.from_user.username or "NONE")))
    except Exception as e:
        logger.error("(persik_keyword) Unexpected error: {}".format(e))


penalty_letter_set = set('еауeayЕAУЕАY')


@bot.message_handler(content_types=['text'])
def text_handler(message):
    if penalty_users_id.count(message.from_user.id) > 0:
        if any((c in penalty_letter_set) for c in message.text):
            bot.delete_message(message.chat.id, message.message_id)


@bot.edited_message_handler(content_types=['text'])
def edit_handler(message):
    if penalty_users_id.count(message.from_user.id) > 0:
        if any((c in penalty_letter_set) for c in message.text):
            bot.delete_message(message.chat.id, message.message_id)


def angry_ban(message):
    '''
    Ban with angry stickers
    '''

    bot.send_sticker(message.chat.id, 'CAADAgADJwMAApFfCAABfVrdPYRn8x4C')
    if message.chat.type != 'private':
        sleep(4)
        ban_user(config.send_chat_id, message.from_user.id, 120)
        bot.send_message(message.chat.id, ru_strings.BAN_MESSAGE['strings'][0]
                        .format(message.from_user.first_name, 2, 'мин.'), parse_mode='Markdown')
        bot.send_sticker(message.chat.id, 'CAADAgADPQMAApFfCAABt8Meib23A_QC')


def false_ban(message):
    '''
    Ban prank KEK
    For meanmail exclusive
    '''

    orig_time = time = 40

    if message.chat.type != 'private' and message.reply_to_message is None:
        bot.delete_message(message.chat.id, message.message_id)

    time_str = re.search('[0-9]{1,8}', message.text)
    if time_str:
        orig_time = time = int(time_str.group(0))

    time_time = re.search(
        '([0-9]{1,5})\s?(с(ек)?|м(ин)?|ч(ас)?|д(ен|н)?)', message.text)
    time_text = 'сек.'
    if time_time:
        text = re.search('[А-Яа-я]{1,2}', time_time.group(0))
        if text:
            if text.group(0)[0] == "м":
                time = time * 60
                time_text= "мин."
            elif text.group(0)[0] == "ч":
                time = time * 60 * 60
                time_text= "ч."
            elif text.group(0)[0] == "д":
                time = time * 24 * 60 * 60
                time_text= "д."

    user_to_ban = None
    ban_message_num = int(time < 30)
    if message.chat.type == 'private':
        user_to_ban = message.reply_to_message.forward_from
    elif message.reply_to_message is None:
        user_to_ban = message.from_user
        ban_message_num = 2
    else:
        user_to_ban = message.reply_to_message.from_user
        if message.from_user.id == message.reply_to_message.from_user.id:
            ban_message_num = 2

    try:
        bot.send_message(config.send_chat_id, ru_strings.BAN_MESSAGE['strings'][ban_message_num]
                                .format(user_to_ban.first_name, orig_time, time_text), parse_mode='Markdown')
    except Exception as e:
        logger.error("[ban_command()] Unexpected error: {}".format(e))


def ban_user_command(message):
    '''
    Alot of magic
    '''

    orig_time= 40
    time = 40

    administrators = bot.get_chat_administrators(message.chat.id)
    if message.reply_to_message is not None:
        if all(message.from_user.id != member.user.id for member in administrators) and \
                        message.from_user.id != message.reply_to_message.from_user.id:
            return

    if message.chat.type != 'private' and message.reply_to_message is None:
        bot.delete_message(message.chat.id, message.message_id)

    time_str = re.search('[0-9]{1,8}', message.text)
    if time_str:
        orig_time = time = int(time_str.group(0))

    time_time = re.search('([0-9]{1,8})\s?(с(ек)?|м(ин)?|ч(ас)?|д(ен|н)?)', message.text)
    time_text = 'сек.'
    if time_time:
        text = re.search('[А-Яа-я]{1,2}', time_time.group(0))
        if text:
            if text.group(0)[0] == "м":
                time = time * 60
                time_text = "мин."
            elif text.group(0)[0] == "ч":
                time = time * 60 * 60
                time_text = "ч."
            elif text.group(0)[0] == "д":
                time = time * 24 * 60 * 60
                time_text = "д."

    user_to_ban = None
    ban_message_num = int(time < 30)
    if message.chat.type == 'private':
        if all(message.from_user.id != user for user in config.allowed_users):
            return
        user_to_ban = message.reply_to_message.forward_from
    elif message.reply_to_message is None:
        user_to_ban = message.from_user
        ban_message_num = 2
        if time < 40:
             time = 40
             orig_time = 40
    else:
        user_to_ban = message.reply_to_message.from_user
        if message.from_user.id == message.reply_to_message.from_user.id:
            ban_message_num = 2
            if time < 40:
                time = 40
                orig_time = 40

    try:
        ban_user(config.send_chat_id, user_to_ban.id, time)
        bot.send_message(config.send_chat_id, ru_strings.BAN_MESSAGE['strings'][ban_message_num]
                         .format(user_to_ban.first_name, orig_time, time_text), parse_mode='Markdown')
        logger.info("User {}, Username @{} - banned!"
                    .format(user_to_ban.id, (user_to_ban.username or "NONE")))
    except Exception as e:
        logger.error("[ban_command()] Unexpected error: {}".format(e))


def roulette_game(message):
    if message.chat.type != 'private':  # Only in chat
        r_number = randrange(0, 6)

        if r_number == 3:
            bot.send_message(message.chat.id,
                             ru_strings.ROULETTE_MESSAGE['strings'][0].format(
                                 message.from_user.first_name),
                             parse_mode='Markdown')
            ban_user(config.send_chat_id, message.from_user.id, 1200)
        else:
            msg = bot.send_message(message.chat.id,
                                   ru_strings.ROULETTE_MESSAGE['strings'][1].format(
                                       message.from_user.first_name),
                                   parse_mode='Markdown')
            sleep(10)
            bot.delete_message(message.chat.id, message.message_id)
            bot.delete_message(msg.chat.id, msg.message_id)


def ban_user(chat_id, user_id, time):
    '''
    Restricting chat member

    Parameters
        ----------
        chat_id : str or int
            Chat ID
        user_id : str or int
            User ID
        time : int
            Time in seconds
    '''

    d = datetime.utcnow()
    d = d + timedelta(0, time)
    timestamp = calendar.timegm(d.utctimetuple())

    bot.restrict_chat_member(chat_id, user_id, timestamp, False, False, False, False)


def drink_question(message):
    logger.info("[Drink] command by {:s}, Username @{:s} | '{:s}'"
                .format(message.from_user.first_name, (message.from_user.username or "NONE"), message.text))
    random_message(message, ru_strings.DRINK_QUESTION_MESSAGE, REPLY_MESSAGE)


def smoke_question(message):
    logger.info("[SMOKE] command by {:s}, Username @{:s} | '{:s}'"
                .format(message.from_user.first_name, (message.from_user.username or "NONE"), message.text))
    bot.reply_to(message, "*Однозначно, дуть!*", parse_mode='Markdown')


def come_here_message(message):
    logger.info("[Comehere] command by {:s}, Username @{:s} | '{:s}'"
                .format(message.from_user.first_name, (message.from_user.username or "NONE"), message.text))
    random_message(message, ru_strings.IM_HERE_MESSAGE, REPLY_MESSAGE)


def answer_stream(message):
    logger.info("[Nextstream] command by {:s}, Username @{:s} | '{:s}'"
                .format(message.from_user.first_name, (message.from_user.username or "NONE"), message.text))
    next_stream_command(message)


def answer_goto_space(message):
    logger.info("[Gotospace] command by {:s}, Username @{:s} | '{:s}'"
                .format(message.from_user.first_name, (message.from_user.username or "NONE"), message.text))
    gotospace_command(message)


def goodboy(message):
    logger.info("[Goodboy] command by {:s}, Username @{:s} | '{:s}')"
                .format(message.from_user.first_name, (message.from_user.username or "NONE"), message.text))
    bot.send_sticker(message.chat.id, ru_strings.GOOD_BOY_MESSAGE['stickers'][0])


def badboy(message):
    logger.info("[Badboy] command by {:s}, Username @{:s} | '{:s}')"
                .format(message.from_user.first_name, (message.from_user.username or "NONE"), message.text))
    bot.send_sticker(message.chat.id, ru_strings.BAD_BOY_MESSAGE['stickers'][0])


def life_question(message):
    '''
    LOL
    '''

    logger.info("[LIFE] command by {:s}, Username @{:s} | '{:s}'"
                .format(message.from_user.first_name, (message.from_user.username or "NONE"), message.text))
    bot.reply_to(message, "*42*", parse_mode='Markdown')


def random_joke(message):
    '''
    Sending random joke from rzhunemogu.ru in chat
    '''

    resp = requests.get("http://rzhunemogu.ru/RandJSON.aspx?CType=1")
    if resp.status_code == 200:
        utf8content = resp.content.decode("windows-1251").encode('utf-8').decode('utf-8')
        json_joke = json.loads(utf8content.replace('\r\n', '\\r\\n'))

        message.text = "{}\nАХ-ХАХАХАХХАХА! лолол!".format(json_joke)

        if len(json_joke['content']) > 200:
            file = text_to_speech(json_joke['content'])
            with open(file, 'rb') as audio:
                voice_msg = bot.send_voice(message.chat.id, reply_to_message_id=message.message_id,
                                           voice=audio, caption=json_joke['content'][:200])

            bot.send_message(
                message.chat.id, reply_to_message_id=voice_msg.message_id,
                                    text=json_joke['content'][200:])
        else:
            file = text_to_speech(json_joke['content'])
            with open(file, 'rb') as audio:
                bot.send_voice(message.chat.id, voice=audio, caption=json_joke['content'],
                               reply_to_message_id=message.message_id)


def fourtytwo(message):
    '''
    LOL
    '''

    bot.reply_to(message, "*В чем смысл жизни? 🤔*", parse_mode='Markdown')


penalty_users_id = []  # Global variable for user ids with penalty
def user_penalty_on(message):
    '''
    Enables the restriction of users to use certain letters.
    '''

    bot.delete_message(message.chat.id, message.message_id)
    if message.reply_to_message:
        if penalty_users_id.count(message.reply_to_message.from_user.id) == 0:
            penalty_users_id.append(message.reply_to_message.from_user.id)
            bot.send_message(message.chat.id, "*Пользователь {} наказан! Недоступны буквы: a, у, е*"
                             .format(message.reply_to_message.from_user.first_name), parse_mode='Markdown')


def user_penalty_off(message):
    '''
    Disables the restriction of users to use certain letters.
    '''

    bot.delete_message(message.chat.id, message.message_id)
    if message.reply_to_message:
            if penalty_users_id.count(message.reply_to_message.from_user.id) == 1:
                penalty_users_id.remove(message.reply_to_message.from_user.id)
                bot.send_message(message.chat.id, "*Пользователь {} прощен!*"
                                 .format(message.reply_to_message.from_user.first_name), parse_mode='Markdown')


def text_to_speech(text):
    '''
    Translates text to speech, saves mp3 to file
    Returns : file_name : str

    Parameters
    ----------
    text : str
        Text
    '''

    try:
        speech = gTTS(text, 'ru')

        try:
            os.makedirs("./TTS")
        except FileExistsError:
            pass

        file_name_len = 10

        if len(text) < 10:
            file_name_len = len(text)

        file_name = './TTS/{}.mp3'.format(text[:file_name_len])

        speech.save(file_name)

    except Exception as e:
        logger.error("(TTS) Unexpected error: {}".format(e))
        return ""

    return file_name


def text_to_speech_voice(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        logger.error("(TTS) Unexpected error: {}".format(e))

    if message.reply_to_message:
        text = message.reply_to_message.text
    else:
        text = message.text[11:]

    file = text_to_speech(text)

    with open(file, 'rb') as audio:
        bot.send_voice(message.chat.id, voice=audio)


MESSAGE_TEMPLATES = [
    [r'%в', text_to_speech_voice],
    [r'дур[ао]к|пид[аоэ]?р|говно|д[еыи]бил|г[оа]ндон|лох|хуй|чмо|скотина|🖕🏻', angry_ban],
    [r'плохой|туп|гад|бяка', badboy],
    [r'(за)?бaн(ь)?', false_ban],
    [r'(за)?бан(ь)?|заблокируй|накажи|фас', ban_user_command],
    [r'(когда.*?стрим|трансляция|(зап|п)уск)|((стрим|трансляция|(зап|п)уск).*?когда)',
     answer_stream],
    [r'иди сюда|ты где|ты тут|привет|кыс', come_here_message],
    [r'тут зануда|космос|выгони', answer_goto_space],
    [r'мозг|живой|красав|молодец|хорош|умный|умница', goodboy],
    [r'.*?пить.*?или.*?не', drink_question],
    [r'рулетка|барабан', roulette_game],
    [r'.*?дуть.*?или.*?не', smoke_question],
    [r'смысл.*?жизни', life_question],
    [r'шутк|анекдот|шутеечка|(по)?шути|жги', random_joke],
    [r'42', fourtytwo],
    [r'наказание вкл)', user_penalty_on],
    [r'наказание выкл', user_penalty_off]
]


def telegram_polling():
    '''
    Reqursive method for handling polling errors
    '''

    try:
        bot.polling(none_stop=True, timeout=60)  # constantly get messages from Telegram
    except Exception:
        logger.info("Polling error, timeout 10sec")
    bot.stop_polling()
    sleep(10)
    telegram_polling()


def main():

    cherrypy.config.update({'log.screen': True,
                        'log.access_file': '',
                        'log.error_file': ''})

    telebot.logger.setLevel(logging.INFO)
    logger.setLevel(logging.INFO)

    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)

    fh = logging.FileHandler('alphabot.log', encoding='utf-8')
    fh.setLevel(logging.INFO)

    formatter = logging.Formatter(u'[%(asctime)s]: %(message)s')
    sh.setFormatter(formatter)
    fh.setFormatter(formatter)

    logger.addHandler(sh)
    logger.addHandler(fh)

    '''
    Automatic posting of birthday greetings in chat
    '''
    t1 = threading.Thread(target=birthday_method)
    t1.daemon = True
    t1.start()

    bot.set_update_listener(listener)

    # logger.info("Waiting 5 minutes before the start...")
    # print("Start")
    # threading.Timer(5*60, onStartProcessing).start()

    # cherrypy.quickstart(WebhookServer(), config.WEBHOOK_URL_PATH, {'/': {}})
    telegram_polling()

if __name__ == "__main__":
    main()
