# -*- coding: utf-8 -*-
from io import StringIO
import sys
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
import urllib.request, json
from uuid import uuid4
import threading

import cherrypy
import requests
import telebot

from telebot import types

import config
import nextstream
import picturedetect
import ru_strings
import payments
from utils import logger

from wit import Wit
import subprocess
import tempfile

from gtts import gTTS

client = Wit('VUSXEG457XQEH57D5YAD3KFX76YAIODS')

bot = telebot.TeleBot(config.token)
payments.bot = bot

cherrypy.config.update({'log.screen': False,
                        'log.access_file': '',
                        'log.error_file': ''})


class WebhookServer(object):
    @cherrypy.expose
    def index(self):
        if 'content-length' in cherrypy.request.headers and \
                        'content-type' in cherrypy.request.headers and \
                        cherrypy.request.headers['content-type'] == 'application/json':
            length = int(cherrypy.request.headers['content-length'])
            json_string = cherrypy.request.body.read(length).decode("utf-8")
            #print(json_string)
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return ''
        else:
            raise cherrypy.HTTPError(403)


SEND_MESSAGE, REPLY_MESSAGE = range(2)


def random_message(message, string_list, mode):
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
            #print(msg)
            if msg.new_chat_member is not None:
                if msg.new_chat_member.id == config.bot_id:
                    bot.send_message(msg.chat.id, ru_strings.BOT_HI_MESSAGE["strings"][0])
                    bot.send_sticker(msg.chat.id, ru_strings.BOT_HI_MESSAGE['stickers'][0])
                else:
                    logger.info("New chat member, username: @{:s}".format(msg.from_user.username or "NONE"))
                    keyboard = types.InlineKeyboardMarkup()
                    url_button = types.InlineKeyboardButton(
                        text="И Правила Прочти", url="http://telegram.me/alphaofftopbot")
                    keyboard.add(url_button)
                    random_number = randrange(0, len(ru_strings.HELLO_MESSAGE["strings"]), 1)
                    bot.reply_to(msg, ru_strings.HELLO_MESSAGE["strings"][random_number] + '\n*Оставь пердак свой всяк сюда входящий, ибо сгорит!*', reply_markup=keyboard, parse_mode='Markdown')
            else:
                antispam(msg)
                if msg.text is not None:
                    logger.info("[CHAT] {}: {}".format(msg.from_user.first_name, msg.text))
    except Exception as e:
        logger.error("[Update listener] unexpected error: {}".format(e))

time_window = 1
messages_list = []
def antispam(message):
    if(len(messages_list) > 1):
        while (messages_list[-1].date - messages_list[0].date) > time_window:
            messages_list.pop(0)
        
    messages_list.append(message)

    messages_count = dict()
    for msg in messages_list:
        if msg.content_type is not 'photo':
            if messages_count.get(msg.from_user.id) is None:
                messages_count.setdefault(msg.from_user.id, 1)
            else:
                messages_count[msg.from_user.id] += 1

    for user, count in messages_count.items():
        freq = count
        #print("{{\"{}\": {}}}".format(user, freq))
        if freq > 3:
            for msg in messages_list:
                if msg.from_user.id == user:
                    bot.delete_message(message.chat.id, msg.message_id)

            d = datetime.utcnow()
            d = d + timedelta(0, 200)
            timestamp = calendar.timegm(d.utctimetuple())
            messages_list.clear()
            bot.restrict_chat_member(message.chat.id, user, timestamp, False, False, False, False)
            bot.send_message(message.chat.id, "*{} уходит в бан! Причина: СПАМ*"
                                 .format(message.from_user.first_name), parse_mode='Markdown')


@bot.message_handler(commands=['rate'])
def rate_command(message):
    if "alphaofftopbot" not in message.text:
        return

    resp = requests.get("https://min-api.cryptocompare.com/data/price?fsym=BTC&tsyms=USD&e=Bitfinex&extraParams=Persik")
    if resp.status_code == 200:
        json_obj = json.loads(resp.content.decode("utf-8"))
        print(json_obj)
        bot.send_message(message.chat.id,"1 btc = {} usd".format(json_obj['USD']), parse_mode='Markdown')
    resp = requests.get("https://min-api.cryptocompare.com/data/price?fsym=ETH&tsyms=USD&e=Bitfinex&extraParams=Persik")
    if resp.status_code == 200:
        json_obj = json.loads(resp.content.decode("utf-8"))
        print(json_obj)
        bot.send_message(message.chat.id,"1 eth = {} usd".format(json_obj['USD']), parse_mode='Markdown')
    resp = requests.get("https://min-api.cryptocompare.com/data/price?fsym=ZEC&tsyms=USD&e=Bitfinex&extraParams=Persik")
    if resp.status_code == 200:
        json_obj = json.loads(resp.content.decode("utf-8"))
        print(json_obj)
        bot.send_message(message.chat.id,"1 zec = {} usd".format(json_obj['USD']), parse_mode='Markdown')

        
@bot.message_handler(commands=['exch'])
def exch_command(message):
    resp = requests.get("https://openexchangerates.org/api/latest.json?app_id=d4b0b34863a6422bb5ca14e12c67fdca")
    if resp.status_code == 200:
        json_obj = json.loads(resp.content.decode("utf-8"))
        print(json_obj)
        bot.send_message(message.chat.id,"1 USD = {} RUB".format(json_obj['rates']['RUB']), parse_mode='Markdown')
        bot.send_message(message.chat.id,"1 USD = {} BYN".format(json_obj['rates']['BYN']), parse_mode='Markdown')
        bot.send_message(message.chat.id,"1 USD = {} UAH".format(json_obj['rates']['UAH']), parse_mode='Markdown')


@bot.message_handler(commands=['exec'])#its mistake dont do it
def eval_command(message):
    if all(message.from_user.id != user for user in config.allowed_users):
           return
    with StringIO() as buf:
        sys.stdout = buf
        try:
            res = exec(message.text[6:])
            if res:
                bot.send_message(message.chat.id, res)
        finally:
            sys.stdout = sys.__stdout__
        result = buf.getvalue()
        if result:
            bot.send_message(message.chat.id, result or 'Empty')

@bot.message_handler(commands=['test'])
def test_command(message):
    keyboard = types.InlineKeyboardMarkup()
    url_button = types.InlineKeyboardButton(
        text="Прочесть Правила", url="http://telegram.me/alphaofftopbot")
    keyboard.add(url_button)
    bot.send_message(message.chat.id, ru_strings.HELLO_MESSAGE["strings"][0], reply_markup=keyboard)


@bot.message_handler(commands=['footfetishfreyja'])
def test_command(message):
    bot.delete_message(message.chat.id, message.message_id)


@bot.message_handler(content_types=['sticker'])
def sticker_message(msg):
    logger.info("{:s}: [STICKER] {:s}".format(msg.from_user.first_name, msg.sticker.file_id))


@bot.message_handler(content_types=['document'])
def document_message(msg):
    logger.info("{:s}: [DOCUMENT] {:s}".format(msg.from_user.first_name, msg.document.file_id))
    file_download(msg.document.file_id, './documents/')


def convert_oga_to_mp3(in_filename=None):
    command = [
        r'.\ffmpeg\bin\ffmpeg.exe',
        '-y',
        '-i', in_filename,
        '-acodec', 'libmp3lame',
        '{}.mp3'.format(in_filename)
    ]

    proc = subprocess.Popen(command)
    proc.wait()


@bot.message_handler(content_types=['voice'])
def audio_message(msg):
    logger.info("{:s}: [VOICE] {:s}".format(msg.from_user.first_name, msg.voice.file_id))
    file_download(msg.voice.file_id, './voice/')
    resp = None
    attempts = 5

    convert_oga_to_mp3('./voice/{}'.format(msg.voice.file_id))
    for i in range(attempts):
        logger.info("{:s}: [VOICE Recognition] Sending to server. Attempt: {}".format(msg.from_user.first_name, i+1))

        try:
            with open('./voice/{}.mp3'.format(msg.voice.file_id), 'rb') as f:
                resp = client.speech(f, None, {'Content-Type': 'audio/mpeg3'})
        except Exception as e:
            logger.error("[VOICE Recognition] Unexpected error: {}".format(e))

        if resp is None:
            continue

        bot.reply_to(msg, '<b>voice:</b> {}'.format(resp['_text']), parse_mode='HTML')
        os.remove('./voice/{}'.format(msg.voice.file_id))
        logger.info("{:s}: [VOICE Recognition] DONE! Result: {:s}".format(msg.from_user.first_name, resp['_text']))
        return

    bot.reply_to(msg, '*Не распознается :c*', parse_mode='Markdown')


@bot.message_handler(content_types=['video'])
def audio_message(msg):
    logger.info("{:s}: [AUDIO] {:s}".format(msg.from_user.first_name, msg.video.file_id))


@bot.message_handler(content_types=['left_chat_member'])
def left_chat_message(msg):
    logger.info("Left chat member, username: @{:s}".format(msg.from_user.username))
    bot.send_message(msg.chat.id, ru_strings.GOODBYE_MESSAGE['strings'][0], parse_mode='Markdown')
    bot.send_sticker(msg.chat.id, ru_strings.GOODBYE_MESSAGE['stickers'][0])


def file_download(file_id, path):
    file_info = bot.get_file(file_id)
    _, file_extension = os.path.splitext(file_info.file_path)
    filename = file_id
    attempts = 5

    for i in range(attempts):
        file = requests.get('https://api.telegram.org/file/bot{}/{}'.format(config.token, file_info.file_path),
                            stream=True)
        if file.status_code == 200:
            file_patch = "".join([path, filename, file_extension])
            try:
                with open(file_patch, 'wb') as f:
                    file.raw.decode_content = True
                    shutil.copyfileobj(file.raw, f)
            except Exception as e:
                logger.error("[Write to file] Unexpected error: {}".format(e))
                return None

            return file_patch
        else:
            logger.error("(Attempt #{}) File download error! Status Code: {}".format(i, file.status_code))
            sleep(3)

    return None


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
    bot.send_message(message.chat.id, nextstream.get_next_stream_msg(nextstream.STREAMS), parse_mode='Markdown')


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


@bot.message_handler(commands=['msg'])
def send_msg_command(message):
    logger.info("/msg command by {:s}, Username @{:s}"
                .format(message.from_user.first_name, (message.from_user.username or "NONE")))
    if any(message.from_user.id == user for user in config.allowed_users) or message.from_user.id == 243956745:
        logger.info("The owner detected!")
        bot.send_message(message.chat.id, ru_strings.SEND_MSG_MESSAGE['strings'][0], parse_mode='Markdown')
        bot.register_next_step_handler(message, send_message)
    else:
        logger.info("This isn't the owner!")


def send_message(message):
    if message.text:
        if message.text.find('/cancel') != -1:
            bot.send_message(message.chat.id, ru_strings.CANCEL_MESSAGE['strings'][0], parse_mode='Markdown')
        else:
            bot.send_message(config.send_chat_id, message.text, parse_mode='Markdown')
            logger.info("Sending message {:s} to chat {:d}".format(message.text, config.send_chat_id))
            bot.send_message(message.chat.id, ru_strings.SEND_MSG_MESSAGE['strings'][1], parse_mode='Markdown')


@bot.message_handler(commands=['stk'])
def stk_command(message):
    logger.info("/stk command by {:s}, Username @{:s}"
                .format(message.from_user.first_name, (message.from_user.username or "NONE")))
    if any(message.from_user.id == user for user in config.allowed_users) or message.from_user.id == 243956745:
        logger.info("The owner detected!")
        bot.send_message(message.chat.id, ru_strings.SEND_STICKER_MESSAGE['strings'][0], parse_mode='Markdown')
        bot.register_next_step_handler(message, send_sticker)
    else:
        logger.info("This isn't the owner!")


def send_sticker(message):
    if message.content_type is not 'sticker':
        if message.text is not None:
            if message.text.find('/cancel') != -1:
                bot.send_message(message.chat.id, ru_strings.CANCEL_MESSAGE['strings'][0], parse_mode='Markdown')
            else:
                bot.send_message(message.chat.id, ru_strings.SEND_STICKER_MESSAGE['stickers'][1], parse_mode='Markdown')
                bot.register_next_step_handler(message, send_sticker)
    else:
        bot.send_sticker(config.send_chat_id, message.sticker.file_id)
        logger.info("Sending sticker {:s} to chat {:d}".format(message.sticker.file_id, config.send_chat_id))


@bot.message_handler(commands=['getuserid'])
def get_user_id_message(message):
    if message.forward_from:
        return
    logger.info("/getuserid command by {:s}, Username @{:s}"
                .format(message.from_user.first_name, (message.from_user.username or "NONE")))
    bot.reply_to(message, ru_strings.GET_ID_MESSAGE['strings'][0].format(message.from_user.id), parse_mode='Markdown')


@bot.message_handler(commands=['getphoto'])
def get_file_message(message):
    logger.info("/getphoto command by {:s}, Username @{:s}"
                .format(message.from_user.first_name, (message.from_user.username or "NONE")))

    if '/' in message.text[10:] or '\\' in message.text[10:]:
        return

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


@bot.message_handler(commands=['donate__'])
def get_user_id_message(message):
    logger.info("/donate command by {:s}, Username @{:s}"
                .format(message.from_user.first_name, (message.from_user.username or "NONE")))
    print(message)
    keyboard = types.InlineKeyboardMarkup()
    url_button = types.InlineKeyboardButton(
        text="Пожертвовать", url="https://igg.me/at/js5j75OG0DQ")
    keyboard.add(url_button)
    bot.send_message(message.chat.id,
                     'Граждане трудящиеся, попрошу внести по рублю в кассу на развитие отечественного персика!',
                     reply_markup=keyboard)


@bot.message_handler(content_types=["photo"])
def photo_receive(message):
    file_id = message.photo[len(message.photo) - 1].file_id

    if message.caption and message.forward_from is None:
        if re.match('(?i)(\W|^).*?!п[eеэ][pр][cс](и|ч[eеи]к).*?(\W|$)', message.caption):
            bot.reply_to(message, "".join([message.from_user.first_name, picturedetect.reply_get_concept_msg(file_id)]),
                        parse_mode='Markdown')

    logger.info("Photo by Username @{:s} | ID {:s}".format((message.from_user.username or "NONE"), file_id))

    file_patch = './photos/{:s}.jpg'.format(file_id)
    _file = Path(file_patch)
    if _file.is_file() is not True:
        file_patch = file_download(file_id, './photos/')

    if file_patch is None:
        logger.error("File download error!'")

        bot.reply_to(message, ru_strings.SOME_ERROR_MESSAGE['strings'], parse_mode='Markdown')
        bot.send_sticker(message.chat.id, ru_strings.SOME_ERROR_MESSAGE['stickers'][0])

        return

    concepts = picturedetect.analise_photo(file_patch)
    if picturedetect.check_blacklist(concepts, picturedetect.BLACKLIST, logger):
        random_message(message, ru_strings.SPACE_DETECT_MESSAGE, REPLY_MESSAGE)

        bot.send_message(message.chat.id, ru_strings.BAN_MESSAGE['strings'][0]
                         .format(message.from_user.first_name, 1, 'мин.'), parse_mode='Markdown')
        ban_user(message.chat.id, message.from_user.id, 60)

        logger.info("SPACE FOUND! | ID {:s}".format(file_id))
    else:
        logger.info("SPACE NOT FOUND! | ID {:s}".format(file_id))

    if picturedetect.nsfw_test(file_patch, 0.8):
        bot.delete_message(message.chat.id, message.message_id)

        bot.send_message(message.chat.id, "*{} уходит в бан на {} {}! Причина: NSFW*"
                         .format(message.from_user.first_name, 5, 'мин.'), parse_mode='Markdown')
        ban_user(message.chat.id, message.from_user.id, 5*60)

@bot.message_handler(regexp='(?i)(\W|^).*?!п[eеэ][pр][cс](и|ч[eеи]к).*?(\W|$)')
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
            if re.match(template[0], message.text):
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
    bot.send_sticker(message.chat.id, 'CAADAgADJwMAApFfCAABfVrdPYRn8x4C')
    if message.chat.type != 'private':
        sleep(4)
        ban_user('-1001125742098', message.from_user.id, 120)
        bot.send_message(message.chat.id, ru_strings.BAN_MESSAGE['strings'][0]
                        .format(message.from_user.first_name, 2, 'мин.'), parse_mode='Markdown')
        bot.send_sticker(message.chat.id, 'CAADAgADPQMAApFfCAABt8Meib23A_QC')


def false_ban(message):
    time = 30
    time_str = re.search('[0-9]{1,5}', message.text)
    if time_str:
        time = int(time_str.group(0))

    time_time = re.search('([0-9]{1,5})\s?(с(ек)?|м(ин)?|ч(ас)?|д(ен|н)?)', message.text)
    if time_time:
        text = re.search('[А-Яа-я]{2}', time_time.group(0))

    time_time = re.search('([0-9]{1,5})\s?(с(ек)?|м(ин)?|ч(ас)?|д(ен|н)?)', message.text)
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

    bot.send_message('-1001125742098', ru_strings.BAN_MESSAGE['strings'][int(time < 30)]
                     .format(message.reply_to_message.from_user.first_name, time, time_text), parse_mode='Markdown')
        

def ban_user_command(message):
    orig_time = time = 30

    if message.reply_to_message is not None:
        if all(message.from_user.id != user for user in config.allowed_users) and \
                        message.from_user.id != message.reply_to_message.from_user.id:
            return

    if message.chat.type != 'private' and message.reply_to_message is None:
        bot.delete_message(message.chat.id, message.message_id)

    time_str = re.search('[0-9]{1,5}', message.text)
    if time_str:
         orig_time = time = int(time_str.group(0))

    time_time = re.search('([0-9]{1,5})\s?(с(ек)?|м(ин)?|ч(ас)?|д(ен|н)?)', message.text)
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

    try:
        ban_user('-1001125742098', user_to_ban.id, time)
        bot.send_message('-1001125742098', ru_strings.BAN_MESSAGE['strings'][ban_message_num]
                                .format(user_to_ban.first_name, orig_time, time_text), parse_mode='Markdown')
        logger.info("User {}, Username @{} - banned!"
                    .format(user_to_ban.id,(user_to_ban.username or "NONE")))
    except Exception as e:
        logger.error("[ban_command()] Unexpected error: {}".format(e))


def roulette_game(message):
    if message.chat.type != 'private':
        r_number = randrange(0, 6)

        if r_number == 3:
            bot.send_message(message.chat.id,
                             ru_strings.ROULETTE_MESSAGE['strings'][0].format(message.from_user.first_name),
                             parse_mode='Markdown')
            ban_user('-1001125742098', message.from_user.id, 1200)
        else:
            msg = bot.send_message(message.chat.id,
                                   ru_strings.ROULETTE_MESSAGE['strings'][1].format(message.from_user.first_name),
                                   parse_mode='Markdown')
            sleep(10)
            bot.delete_message(message.chat.id, message.message_id)
            bot.delete_message(msg.chat.id, msg.message_id)


def ban_user(chat_id, user_id, time):
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
    logger.info("[LIFE] command by {:s}, Username @{:s} | '{:s}'"
                .format(message.from_user.first_name, (message.from_user.username or "NONE"), message.text))
    bot.reply_to(message, "*42*", parse_mode='Markdown')


def evaluate_test(message):
    print(message.text[17:])
    print(np.eval(message.text[17:]))
    bot.reply_to(message, "*Будет {}*".format(np.eval(message.text[17:])), parse_mode='Markdown')


def random_joke(message):
    resp = requests.get("http://rzhunemogu.ru/RandJSON.aspx?CType=1")
    if resp.status_code == 200:
        utf8content = resp.content.decode("windows-1251").encode('utf-8').decode('utf-8')
        json_joke = json.loads(utf8content.replace('\r\n', '\\r\\n'))
        bot.send_message(message.chat.id, json_joke['content'])

def fourtytwo(message):
    bot.reply_to(message, "*В чем смысл жизни? 🤔*", parse_mode='Markdown')


penalty_users_id = []


def user_penalty_on(message):
    bot.delete_message(message.chat.id, message.message_id)
    if message.reply_to_message:
        if penalty_users_id.count(message.reply_to_message.from_user.id) == 0:
            penalty_users_id.append(message.reply_to_message.from_user.id)
            bot.send_message(message.chat.id, "*Пользователь {} наказан! Недоступны буквы: a, у, е*"
                             .format(message.reply_to_message.from_user.first_name), parse_mode='Markdown')


def user_penalty_off(message):
    bot.delete_message(message.chat.id, message.message_id)
    if message.reply_to_message:
            if penalty_users_id.count(message.reply_to_message.from_user.id) == 1:
                penalty_users_id.remove(message.reply_to_message.from_user.id)
                bot.send_message(message.chat.id, "*Пользователь {} прощен!*"
                                 .format(message.reply_to_message.from_user.first_name), parse_mode='Markdown')


def text_to_speech(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        logger.error("(TTS) Unexpected error: {}".format(e))
    if message.reply_to_message:
        text = message.reply_to_message.text
    else:
        text = message.text[11:]
    speech = gTTS(text, 'ru')

    file_name_len = 10
    if len(text) < 10:
        file_name_len = len(text)

    file_name = './TTS/{}.mp3'.format(text[:file_name_len])

    speech.save(file_name)

    with open(file_name, 'rb') as audio:
        bot.send_voice(message.chat.id, audio)




def donate_generate(message):
    amount_str = re.search('[0-9]{1,15}', message.text)
    if amount_str:
        amount = int(amount_str.group(0))
    else:
        return

    payment_id = uuid4()
    payments.waiting_payments.setdefault(str(payment_id), message.from_user)

    print(payment_id)

    postdata={'WMI_SUCCESS_URL':'https://walletone.com',
              'WMI_FAIL_URL':'https://walletone.com',
              'WMI_MERCHANT_ID':'147906908884',
              'WMI_PAYMENT_AMOUNT': amount,
              'WMI_CURRENCY_ID':'980',
              'WMI_DESCRIPTION':'Кисе на лечение. *-*'}
    resp = requests.post("http://wl.walletone.com/checkout/checkout/Index", data=postdata)

    if "&m=147906908884" not in resp.request.url:
        bot.send_message(message.chat.id, " \nПроизошла ошибка при создании счета! D:\n ", parse_mode='Markdown')
        return

    keyboard = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton("Задонатить 🍩", url=resp.request.url)
    keyboard.add(button)

    bot.send_message(message.chat.id, " \nСчет на сумму *{} UAH* успешно создан :D\n ".format(amount), reply_markup=keyboard, parse_mode='Markdown')


MESSAGE_TEMPLATES = [
    ['(?i)(\W|^).*?(%в).*?(\W|$)', text_to_speech],
    ['(?i)(\W|^).*?(дур[ао]к|пид[аоэ]?р|говно|д[еыи]бил|г[оа]ндон|лох|чмо|скотина).*?(\W|$)', angry_ban],
    ['(?i)(\W|^).*?(плохой|туп|гад|бяка).*?(\W|$)', badboy],
    ['(?i)(\W|^).*?((за)?бaн(ь)?).*?(\W|$)', false_ban],
    ['(?i)(\W|^).*?((за)?бан(ь)?|заблокируй|накажи|фас).*?(\W|$)', ban_user_command],
    ['(?i)(\W|^).*?((когда.*?стрим|трансляция|(зап|п)уск)|((стрим|трансляция|(зап|п)уск).*?когда)).*?(\W|$)',
     answer_stream],
    ['(?i)(\W|^).*?(иди сюда|ты где|ты тут|привет|кыс).*?(\W|$)', come_here_message],
    ['(?i)(\W|^).*?(тут зануда|космос|выгони).*?(\W|$)', answer_goto_space],
    ['(?i)(\W|^).*?(мозг|живой|красав|молодец|хорош|умный|умница).*?(\W|$)', goodboy],
    ['(?i)(\W|^).*?(.*?пить.*?или.*?не).*?(\W|$)', drink_question],
    ['(?i)(\W|^).*?(рулетка|барабан).*?(\W|$)', roulette_game],
    ['(?i)(\W|^).*?(.*?дуть.*?или.*?не).*?(\W|$)', smoke_question],
    ['(?i)(\W|^).*?смысл.*?жизни.*?(\W|$)', life_question],
    ['(?i)(\W|^).*?(шутк|анекдот|шутеечка|(по)?шути|жги).*?(\W|$)', random_joke],
    ['(?i)(\W|^).*?42.*?(\W|$)', fourtytwo],
    ['(?i)(\W|^).*?наказание вкл.*?(\W|$)', user_penalty_on],
    ['(?i)(\W|^).*?наказание выкл.*?(\W|$)', user_penalty_off],
    ['(?i)(\W|^).*?донат.*?(\W|$)', donate_generate],

]


def main():
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

    thread = threading.Thread(target = payments.run)
    thread.daemon = True
    thread.start()

    bot.remove_webhook()
    bot.set_webhook(url=config.WEBHOOK_URL_BASE + config.WEBHOOK_URL_PATH,
                    certificate=open(config.WEBHOOK_SSL_CERT, 'r'))

    cherrypy.config.update({
        'server.socket_host': config.WEBHOOK_LISTEN,
        'server.socket_port': config.WEBHOOK_PORT,
        'server.ssl_module': 'builtin',
        'server.ssl_certificate': config.WEBHOOK_SSL_CERT,
        'server.ssl_private_key': config.WEBHOOK_SSL_PRIV
    })
    bot.set_update_listener(listener)

    

    logger.info("Alpha-Bot started!")
    cherrypy.quickstart(WebhookServer(), config.WEBHOOK_URL_PATH, {'/': {}})


if __name__ == "__main__":
    main()
