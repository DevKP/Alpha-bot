# -*- coding: utf-8 -*-
import logging
import re
import shutil
import sys
import os
from pathlib import Path
from random import randint
from time import sleep

import cherrypy
import pymorphy2
import requests
import telebot

import config
import nextstream
import picturedetect
import ru_strings

bot = telebot.TeleBot(config.token)
morph = pymorphy2.MorphAnalyzer()

cherrypy.config.update({'log.screen': False,
                        'log.access_file': '',
                        'log.error_file': ''})

# loggerr = telebot.logger
# telebot.logger.setLevel(logging.DEBUG)

logger = logging.getLogger('alphabot')
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


reply_toOwner = {'ownerid': None, 'reply': False}


# Еще один костыль
def listener(messages):
    try:
        for msg in messages:
            if reply_toOwner['reply'] is True and reply_toOwner['ownerid'] is not None:
                print(msg)
                if msg.chat.id == config.send_chat_id:
                    bot.forward_message(reply_toOwner['ownerid'], config.send_chat_id, msg.message_id)

            if msg.text is not None:
                logger.info("{:s}: {:s}".format(msg.from_user.first_name, msg.text))

                if msg.new_chat_member is not None:
                    if msg.new_chat_member.id == config.bot_id:
                        bot.send_message(msg.chat.id, ru_strings.BOT_HI_MESSAGE["strings"][0])
                        bot.send_sticker(msg.chat.id, ru_strings.BOT_HI_MESSAGE['stickers'][0])
                    else:
                        logger.info("New chat member, username: @{:s}".format(msg.from_user.username))
                        r_number = randint(0, 5)
                        bot.send_message(msg.chat.id, ru_strings.HELLO_MESSAGE['strings'][r_number])
    except:
        logger.error("Unexpected error: {}".format(sys.exc_info()[0]))
        bot.reply_to(msg, ru_strings.SOMEERROR_MESSAGE['strings'], parse_mode='Markdown')
        bot.send_sticker(msg.chat.id, ru_strings.SOMEERROR_MESSAGE['stickers'][0])
        raise


bot.set_update_listener(listener)


@bot.message_handler(content_types=['sticker'])
def sticker_message(msg):
    logger.info("{:s}: [STICKER] {:s}".format(msg.from_user.first_name, msg.sticker.file_id))


@bot.message_handler(content_types=['left_chat_member'])
def left_chat_message(msg):
    logger.info("Left chat member, username: @{:s}".format(msg.from_user.username))
    bot.send_message(msg.chat.id, ru_strings.GOODBYE_MESSAGE['strings'][0], parse_mode='Markdown')
    bot.send_sticker(msg.chat.id, ru_strings.GOODBYE_MESSAGE['stickers'][0])


def get_tags(word):
    required_grammemes = set()
    if word.tag.gender:
        required_grammemes.add(word.tag.gender)
    if word.tag.case:
        required_grammemes.add(word.tag.case)
    if word.tag.number:
        required_grammemes.add(word.tag.number)
    return required_grammemes


def get_answer(*names):
    words = [morph.parse(name)[0] for name in names]

    answer_template = "Я думаю, это {}"

    if all([x.tag.POS == "NOUN" for x in words]):
        return answer_template.format(", ".join(names)), len(names) - 1

    required_grammemes = [get_tags(word) for word in words]

    coherence = 0

    answer = answer_template.format(words[0].inflect(required_grammemes[0]).word)

    for i in range(1, len(words)):
        word = words[i].inflect(required_grammemes[i - 1])
        if not word:
            word = words[i].inflect(required_grammemes[i])
            answer += ", "
            coherence += 1
        else:
            answer += " "

        answer += word.word

    return answer, coherence


def file_download(file_id, patch):
    file_info = bot.get_file(file_id)
    filename, file_extension = os.path.splitext(file_info.file_path)
    filename = file_id
    attempts = 5

    for i in range(attempts):
        file = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(config.token, file_info.file_path),
                            stream=True)
        if file.status_code == 200:
            file_patch = "".join([patch, filename, file_extension])
            try:
                with open(file_patch, 'wb') as f:
                    file.raw.decode_content = True
                    shutil.copyfileobj(file.raw, f)
                    f.close()
            except:
                logger.error("Unexpected error: {}".format(sys.exc_info()[0]))
                return None

            return file_patch
        else:
            logger.error("(Attempt #{}) File download error! Status Code: {}".format(i, file.status_code))
            sleep(3)

    return None

def reply_get_concept_msg(photo_id):
    file_patch = './photos/{:s}.jpg'.format(photo_id)
    _file = Path(file_patch)
    if _file.is_file() is not True:
        file_patch = file_download(photo_id, './photos/')

    concepts = picturedetect.analise_photo(file_patch)
    name1 = concepts[0]['name']
    name2 = concepts[1]['name']
    name3 = concepts[2]['name']

    # Костыль костылевский
    if name1 == 'нет человек':
        name1 = 'безлюдное'
    if name2 == 'нет человек':
        name2 = 'безлюдное'
    if name3 == 'нет человек':
        name3 = 'безлюдное'

    names = list((name1, name2, name3))

    answers = list()

    i = 0

    for j in range(6):
        answer, coherence = get_answer(*names)
        answers.append((answer, coherence))
        names[i], names[i + 1] = names[i + 1], names[i]
        i = (i + 1) if i < len(names) - 2 else 0

    def sort_answers(a):
        return a[1]

    answers.sort(key=sort_answers)

    # answer += "\n*Думаю, это {}, {}, {}!*".format(name1, name2, name3)

    logger.info("[WHATISTHIS] Photo ID {0} - [{1}|{2}|{3}]".format(photo_id, name1, name2, name3))
    return "*{}!*".format(answers[0][0])


@bot.message_handler(commands=['start'])
def start_message(message):
    logger.info(
        "/start command by {:s}, Username {:d}".format(message.from_user.first_name, message.from_user.username))
    if message.chat.id > 0:
        bot.send_message(message.chat.id, ru_strings.START_MESSAGE['strings'][0].format(message.chat.first_name))


@bot.message_handler(commands=['nextstream'])
def _next_stream(message):
    logger.info(
        "/nextstream command by {:s}, Username @{:s}".format(message.from_user.first_name, message.from_user.username))
    bot.send_message(message.chat.id, nextstream.get_next_stream_msg(nextstream.STREAM), parse_mode='Markdown')


@bot.message_handler(commands=['gotospace'])
def _goto_space(message):
    logger.info(
        "/gotospace command by {:s}, Username @{:s}".format(message.from_user.first_name, message.from_user.username))
    bot.send_message(message.chat.id, ru_strings.OFFTOP_COMMAND_MESSAGE, parse_mode='Markdown')


@bot.message_handler(commands=['info'])
def start_message(message):
    print(message)
    logger.info(
        "/info command by {:s}, Username @{:s}".format(message.from_user.first_name, message.from_user.username))
    bot.send_message(message.chat.id, ru_strings.INFO_COMMAND_MESSAGE, parse_mode='Markdown')


@bot.message_handler(commands=['msg'])
def start_message(message):
    logger.info("/msg command by {:s}, Username @{:s}".format(message.from_user.first_name, message.from_user.username))
    if message.from_user.id == config.ownerid:
        logger.info("Owner detected!")
        bot.send_message(message.chat.id, ru_strings.SEND_MSG_MESSAGE['strings'][0], parse_mode='Markdown')
        reply_toOwner['ownerid'] = message.from_user.id
        reply_toOwner['reply'] = True
        bot.register_next_step_handler(message, send_message)


def send_message(message):
    if message.text.find('/cancel') != -1:
        bot.send_message(message.chat.id, ru_strings.CANCEL_MESSAGE['strings'][0], parse_mode='Markdown')
        reply_toOwner['reply'] = False
    else:
        bot.send_message(config.send_chat_id, message.text, parse_mode='Markdown')
        logger.info("Sending message {:s} to chat {:d}".format(message.text, config.send_chat_id))
        bot.register_next_step_handler(message, send_message)


@bot.message_handler(commands=['stk'])
def stk_command(message):
    logger.info("/stk command by {:s}, Username @{:s}".format(message.from_user.first_name, message.from_user.username))
    if message.from_user.id == config.ownerid or message.from_user.id == 42577446:
        logger.info("Owner detected!")
        bot.send_message(message.chat.id, ru_strings.SENDSTICKER_MESSAGE['stickers'][0], parse_mode='Markdown')
        bot.register_next_step_handler(message, send_sticker)


def send_sticker(message):
    if message.content_type is not 'sticker':
        if message.text is not None:
            if message.text.find('/cancel') != -1:
                bot.send_message(message.chat.id, ru_strings.CANCEL_MESSAGE['strings'][0], parse_mode='Markdown')
            else:
                bot.send_message(message.chat.id, ru_strings.SENDSTICKER_MESSAGE['stickers'][1], parse_mode='Markdown')
                bot.register_next_step_handler(message, send_sticker)
    else:
        bot.send_sticker(config.send_chat_id, message.sticker.file_id)
        logger.info("Sending sticker {:s} to chat {:d}".format(message.sticker.file_id, config.send_chat_id))


@bot.message_handler(content_types=["photo"])
def photo_receive(message):
    file_id = message.photo[len(message.photo) - 1].file_id

    logger.info("Photo by Username @{:s} | ID {:s}".format(message.from_user.username, file_id))

    file_patch = './photos/{:s}.jpg'.format(file_id)
    _file = Path(file_patch)
    if _file.is_file() is not True:
        file_patch = file_download(file_id, './photos/')

    if file_patch is None:
        logger.error("File download error!'")

        bot.reply_to(message, ru_strings.SOMEERROR_MESSAGE['strings'], parse_mode='Markdown')
        bot.send_sticker(message.chat.id, ru_strings.SOMEERROR_MESSAGE['stickers'][0])

        return

    logger.info("Start analysing | ID {:s}".format(file_id))

    concepts = picturedetect.analise_photo(file_patch)
    if picturedetect.check_blacklist(concepts, picturedetect.BLACKLIST, logger) is True:
        bot.reply_to(message, ru_strings.SPACE_DETECT_MESSAGE['strings'][0], parse_mode='Markdown')
        bot.send_sticker(message.chat.id, ru_strings.SPACE_DETECT_MESSAGE['stickers'][0])
        bot.send_chat_action(message.chat.id, 'typing')
        sleep(8)
        _goto_space(message)
        logger.info("SPACE FOUND! | ID {:s}".format(file_id))
    else:
        logger.info("SPACE NOT FOUND! | ID {:s}".format(file_id))

    if message.forward_from is None and message.caption is not None:
        if re.match('(?i)(\W|^)(!п[еэ]рс(ичек|ик).*?)(\W|$)', message.caption):
            bot.reply_to(message, reply_get_concept_msg(file_id), parse_mode='Markdown')

@bot.message_handler(regexp='(?i)(\W|^)(!п[еэ]рс(ичек|ик).*?)(\W|$)')
def persik_keyword(message):
    if message.reply_to_message is not None:
        if message.reply_to_message.photo is not None:
            file_info = bot.get_file(message.reply_to_message.photo[len(message.reply_to_message.photo) - 1].file_id)
            msg = reply_get_concept_msg(file_info.file_id)

            if msg is None:
                bot.reply_to(message, ru_strings.SOMEERROR_MESSAGE['strings'], parse_mode='Markdown')
                bot.send_sticker(message.chat.id, ru_strings.SOMEERROR_MESSAGE['stickers'][0])
                return

            bot.reply_to(message, msg, parse_mode='Markdown')
            return
    if len(message.text) < 9:
        come_here_message(message)
        return
    if re.match('(?i)(\W|^).*?(.*?пить.*?или.*?не).*?(\W|$)', message.text):
        drink_question(message)
        return
    if re.match('(?i)(\W|^).*?((иди сюда)|(ты где)|(ты тут)|(привет)|(кыс)).*?(\W|$)', message.text):
        come_here_message(message)
        return
    if re.match('(?i)(\W|^).*?((когда.*?стрим|трансляция|(зап|п)уск)|((стрим|трансляция|(зап|п)уск).*?когда)).*?(\W|$)',
                message.text):
        answer_stream(message)
        return
    if re.match('(?i)(\W|^).*?((зануда*?)|(космос*?)|(выгони*?)).*?(\W|$)', message.text):
        answer_goto_space(message)
        return
    if re.match('(?i)(\W|^).*?((мозг)|(живой)|(красав)|(молодец)|(хорош)).*?(\W|$)', message.text):
        goodboy(message)
        return
    bot.reply_to(message, ru_strings.NA_MESSAGE['strings'][0], parse_mode='Markdown')


def drink_question(message):
    logger.info("[Come here] command by {:s}, Username @{:s} | '{:s}'"
                .format(message.from_user.first_name, message.from_user.username, message.text))
    r_number = randint(0, 3)
    bot.reply_to(message, ru_strings.DRINK_QUESTION_MESSAGE['strings'][r_number], parse_mode='Markdown')


def come_here_message(message):
    logger.info("[Come here] command by {:s}, Username @{:s} | '{:s}'"
                .format(message.from_user.first_name, message.from_user.username, message.text))
    r_number = randint(0, 6)
    bot.reply_to(message, ru_strings.IM_HERE_MESSAGE['strings'][r_number], parse_mode='Markdown')


def answer_stream(message):
    logger.info("[Next stream] command by {:s}, Username @{:s} | '{:s}'"
                .format(message.from_user.first_name, message.from_user.username, message.text))
    _next_stream(message)


def answer_goto_space(message):
    logger.info("[Gotospace] command by {:s}, Username @{:s} | '{:s}'"
                .format(message.from_user.first_name, message.from_user.username, message.text))
    _goto_space(message)


@bot.message_handler(regexp='(?i)(\W|^)((мозг*?)|(живой*?)|(красав*?)|(молодец*?)|(хороший*?))(\W|$)')
def goodboy_message(message):
    if message.reply_to_message is not None:
        if message.reply_to_message.from_user.id == config.bot_id:
            goodboy(message)


def goodboy(message):
    logger.info("[Good boy] command by {:s}, Username @{:s} | '{:s}')"
                .format(message.from_user.first_name, message.from_user.username, message.text))
    bot.send_sticker(message.chat.id, ru_strings.GOODBOY_MESSAGE['stickers'][0])


@bot.message_handler(regexp='(?i)(\W|^)(Привет Т[её]ма)(\W|$)')
def secret_message(message):
    bot.send_message(message.chat.id, 'Ы', parse_mode='Markdown')


if __name__ == "__main__":
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
    logger.info("Alpha-Bot started!")
    cherrypy.quickstart(WebhookServer(), config.WEBHOOK_URL_PATH, {'/': {}})
