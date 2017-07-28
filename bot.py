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

import cherrypy
import requests
import telebot

from telebot import types

import config
import nextstream
import picturedetect
import ru_strings

bot = telebot.TeleBot(config.token)

cherrypy.config.update({'log.screen': False,
                        'log.access_file': '',
                        'log.error_file': ''})


logger = logging.getLogger('alphabot')


class WebhookServer(object):
    @cherrypy.expose
    def index(self):
        if 'content-length' in cherrypy.request.headers and \
                        'content-type' in cherrypy.request.headers and \
                        cherrypy.request.headers['content-type'] == 'application/json':
            length = int(cherrypy.request.headers['content-length'])
            json_string = cherrypy.request.body.read(length).decode("utf-8")
            # print(json_string)
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
            if msg.new_chat_member is not None:
                if msg.new_chat_member.id == config.bot_id:
                    bot.send_message(msg.chat.id, ru_strings.BOT_HI_MESSAGE["strings"][0])
                    bot.send_sticker(msg.chat.id, ru_strings.BOT_HI_MESSAGE['stickers'][0])
                else:
                    logger.info("New chat member, username: @{:s}".format(msg.from_user.username))
                    random_message(msg, ru_strings.HELLO_MESSAGE, SEND_MESSAGE)
            else:
                if msg.text is not None:
                    logger.info("{}: {}".format(msg.from_user.first_name, msg.text))
    except Exception as e:
        logger.error("(Update listener) unexpected error: {}".format(e))


@bot.message_handler(content_types=['sticker'])
def sticker_message(msg):
    logger.info("{:s}: [STICKER] {:s}".format(msg.from_user.first_name, msg.sticker.file_id))


@bot.message_handler(content_types=['left_chat_member'])
def left_chat_message(msg):
    logger.info("Left chat member, username: @{:s}".format(msg.from_user.username))
    bot.send_message(msg.chat.id, ru_strings.GOODBYE_MESSAGE['strings'][0], parse_mode='Markdown')
    bot.send_sticker(msg.chat.id, ru_strings.GOODBYE_MESSAGE['stickers'][0])


def file_download(file_id, patch):
    file_info = bot.get_file(file_id)
    _, file_extension = os.path.splitext(file_info.file_path)
    filename = file_id
    attempts = 5

    for i in range(attempts):
        file = requests.get('https://api.telegram.org/file/bot{}/{}'.format(config.token, file_info.file_path),
                            stream=True)
        if file.status_code == 200:
            file_patch = "".join([patch, filename, file_extension])
            try:
                with open(file_patch, 'wb') as f:
                    file.raw.decode_content = True
                    shutil.copyfileobj(file.raw, f)
            except Exception as e:
                logger.error("(Write to file) Unexpected error: {}".format(e))
                return None

            return file_patch
        else:
            logger.error("(Attempt #{}) File download error! Status Code: {}".format(i, file.status_code))
            sleep(3)

    return None


@bot.message_handler(commands=['start'])
def start_command(message):
    logger.info("/start command by {:s}, Username {:d}"
                .format(message.from_user.first_name, (message.from_user.username or "NONE")))
    if message.chat.id > 0:
        bot.send_message(message.chat.id, ru_strings.START_MESSAGE['strings'][0].format(message.chat.first_name))


@bot.message_handler(commands=['nextstream'])
def next_stream_command(message):
    logger.info("/nextstream command by {:s}, Username @{:s}"
                .format(message.from_user.first_name, (message.from_user.username or "NONE")))
    bot.send_message(message.chat.id, nextstream.get_next_stream_msg(nextstream.STREAM), parse_mode='Markdown')


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
    if any(message.from_user.id == user for user in config.allowed_users):
        logger.info("The owner detected!")
        bot.send_message(message.chat.id, ru_strings.SEND_MSG_MESSAGE['strings'][0], parse_mode='Markdown')
        bot.register_next_step_handler(message, send_message)
    else:
        logger.info("This isn't the owner!")


def send_message(message):
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
    if any(message.from_user.id == user for user in config.allowed_users):
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
    logger.info("/getuserid command by {:s}, Username @{:s}"
                .format(message.from_user.first_name, (message.from_user.username or "NONE")))
    bot.reply_to(message, ru_strings.GET_ID_MESSAGE['strings'][0].format(message.from_user.id), parse_mode='Markdown')


@bot.message_handler(commands=['donate'])
def get_user_id_message(message):
    logger.info("/donate command by {:s}, Username @{:s}"
                .format(message.from_user.first_name, (message.from_user.username or "NONE")))
    print(message)
    keyboard = types.InlineKeyboardMarkup()
    url_button = types.InlineKeyboardButton(
        text="Пожертвовать", url="https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=P9NSFS4W7PYZC")
    keyboard.add(url_button)
    bot.send_message(message.chat.id,
                     'Граждане трудящиеся, попрошу внести по рублю в кассу на развитие отечественного персика!',
                     reply_markup=keyboard)


@bot.message_handler(content_types=["photo"])
def photo_receive(message):
    file_id = message.photo[len(message.photo) - 1].file_id

    if message.caption and message.forward_from is None:
        if re.match('(?i)(\W|^).*?!п[еэ]рс[ие].*?(\W|$)', message.caption):
            bot.reply_to(message, picturedetect.reply_get_concept_msg(file_id), parse_mode='Markdown')

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

    logger.info("Start analysing | ID {:s}".format(file_id))

    concepts = picturedetect.analise_photo(file_patch)
    if picturedetect.check_blacklist(concepts, picturedetect.BLACKLIST, logger) is True:
        random_message(message, ru_strings.SPACE_DETECT_MESSAGE, REPLY_MESSAGE)

        bot.send_chat_action(message.chat.id, 'typing')

        sleep(8)

        gotospace_command(message)
        logger.info("SPACE FOUND! | ID {:s}".format(file_id))
    else:
        logger.info("SPACE NOT FOUND! | ID {:s}".format(file_id))


@bot.message_handler(regexp='(?i)(\W|^).*?!п[еэ]рс[ие].*?(\W|$)')
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

            bot.reply_to(message, msg, parse_mode='Markdown')
            return

        if len(message.text) < 9:
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


def true_ban_user(message):
    bot.send_sticker(message.chat.id, 'CAADAgADJwMAApFfCAABfVrdPYRn8x4C')
    sleep(4)
    ban_user(message, message.from_user.id, 120)
    bot.send_message(message.chat.id, ru_strings.BAN_MESSAGE['strings'][0]
                     .format(message.from_user.first_name, 120), parse_mode='Markdown')
    bot.send_sticker(message.chat.id, 'CAADAgADPQMAApFfCAABt8Meib23A_QC')


def false_ban_user(message):
    time_str = re.search('[0-9]{1,5}', message.text)
    if time_str is not None:
        time_ = int(time_str.group(0))
    else:
        time_ = 30
    bot.send_message(message.chat.id, ru_strings.BAN_MESSAGE['strings'][0]
                     .format(message.reply_to_message.from_user.first_name, time_), parse_mode='Markdown')


def ban_user_command(message):
    if any(message.from_user.id == user for user in config.allowed_users):
        if message.reply_to_message:
            time_str = re.search('[0-9]{1,5}', message.text)
            if time_str is not None:
                time_ = int(time_str.group(0))
            else:
                time_ = 30

            ban_user(message.reply_to_message, message.reply_to_message.from_user.id, time_)
            if time_ < 30:
                bot.send_message(message.chat.id, ru_strings.BAN_MESSAGE['strings'][1]
                                 .format(message.reply_to_message.from_user.first_name), parse_mode='Markdown')
            else:
                bot.send_message(message.chat.id, ru_strings.BAN_MESSAGE['strings'][0]
                                 .format(message.reply_to_message.from_user.first_name, time_), parse_mode='Markdown')

            logger.info("User {:s}, Username @{:s} - banned!"
                        .format(message.from_user.first_name, (message.from_user.username or "NONE")))


def roulette_game(message):
    r_number = randrange(0, 6)

    if r_number == 3:
        ban_user(message, message.from_user.id, 1200)
        bot.send_message(message.chat.id,
                         ru_strings.ROULETTE_MESSAGE['strings'][0].format(message.from_user.first_name),
                         parse_mode='Markdown')
    else:
        bot.send_message(message.chat.id,
                         ru_strings.ROULETTE_MESSAGE['strings'][1].format(message.from_user.first_name),
                         parse_mode='Markdown')


def ban_user(message, user_id, time):
    d = datetime.utcnow()
    d = d + timedelta(0, time)
    timestamp = calendar.timegm(d.utctimetuple())

    bot.restrict_chat_member(message.chat.id, user_id, timestamp, False, False, False, False)


def drink_question(message):
    logger.info("[Drink] command by {:s}, Username @{:s} | '{:s}'"
                .format(message.from_user.first_name, (message.from_user.username or "NONE"), message.text))
    random_message(message, ru_strings.DRINK_QUESTION_MESSAGE, REPLY_MESSAGE)


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

MESSAGE_TEMPLATES = [
    ['(?i)(\W|^).*?(дур[ао]к|пид[аоэ]?р|говно|д[еыи]бил|г[оа]ндон|лох).*?(\W|$)', true_ban_user],
    ['(?i)(\W|^).*?(плохой|туп|гад|бяка).*?(\W|$)', badboy],
    ['(?i)(\W|^).*?((за)?бaн(ь)?).*?(\W|$)', false_ban_user],
    ['(?i)(\W|^).*?((за)?бан(ь)?|заблокируй|накажи|фас).*?(\W|$)', ban_user_command],
    ['(?i)(\W|^).*?((когда.*?стрим|трансляция|(зап|п)уск)|((стрим|трансляция|(зап|п)уск).*?когда)).*?(\W|$)',
     answer_stream],
    ['(?i)(\W|^).*?(иди сюда|ты где|ты тут|привет|кыс).*?(\W|$)', come_here_message],
    ['(?i)(\W|^).*?(тут зануда|космос|выгони).*?(\W|$)', answer_goto_space],
    ['(?i)(\W|^).*?(мозг|живой|красав|молодец|хорош).*?(\W|$)', goodboy],
    ['(?i)(\W|^).*?(.*?пить.*?или.*?не).*?(\W|$)', drink_question],
    ['(?i)(\W|^).*?(улитка|барабан).*?(\W|$)', roulette_game]
]


@bot.message_handler(regexp='(?i)(\W|^)Привет Т[её]ма(\W|$)')
def secret_message(message):
    bot.send_message(message.chat.id, 'Ы', parse_mode='Markdown')


@bot.message_handler(regexp='(?i)(\W|^)Альфа Центавра(\W|$)')
def secret_message(message):
    bot.reply_to(message, '*Понад усе!*', parse_mode='Markdown')


@bot.message_handler(regexp='(?i)(\W|^)кто захватит мир(\W|$)')
def secret_message(message):
    bot.reply_to(message, '*Команда Alpha Centauri!*', parse_mode='Markdown')


@bot.message_handler(regexp='(?i)(\W|^)слава украине(\W|$)')
def secret_message(message):
    bot.reply_to(message, '*Героям слава!*', parse_mode='Markdown')


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
