# -*- coding: utf-8 -*-
import telebot
import cherrypy
import logging
import re
import requests
import shutil
import pymorphy2

from random import randint
from pathlib import Path
from time import sleep

import config
import nextstream
import picturedetect
import ru_strings

bot = telebot.TeleBot(config.token)
morph = pymorphy2.MorphAnalyzer()

cherrypy.config.update({'log.screen': False,
                       'log.access_file': '',
                       'log.error_file': ''})

#loggerr = telebot.logger
#telebot.logger.setLevel(logging.DEBUG)

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
            #print(json_string)
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return ''
        else:
            raise cherrypy.HTTPError(403)

reply_toOwner = {'ownerid': None, 'reply': False}

#Еще один костыль
def listener(messages):
    for msg in messages:
        if reply_toOwner['reply'] is True and reply_toOwner['ownerid'] is not None:
            print(msg)
            if msg.chat.id == config.send_chat_id:
                bot.forward_message(reply_toOwner['ownerid'], config.send_chat_id, msg.message_id)

        if msg.text is not None:
            logger.info("{:s}: {:s}".format(msg.from_user.first_name, msg.text))
        try:
            if msg.new_chat_member is not None:
                if msg.new_chat_member.id == config.bot_id:
                    bot.send_message(msg.chat.id, ru_strings.bothi_message["strings"][0])
                    bot.send_sticker(msg.chat.id, ru_strings.bothi_message['stickers'][0])
                else:
                    logger.info("New chat member, username: @{:s}".format(msg.from_user.username))
                    r_number = randint(0, 5)
                    bot.send_message(msg.chat.id, ru_strings.hello_message['strings'][r_number])
        except:
            print("Some error O_o")



@bot.message_handler(content_types=['sticker'])
def sticker_message(msg):
    logger.info("{:s}: [STICKER] {:s}".format(msg.from_user.first_name, msg.sticker.file_id))

@bot.message_handler(content_types=['left_chat_member'])
def left_chat_message(msg):
    logger.info("Left chat member, username: @{:s}".format(msg.from_user.username))
    bot.send_message(msg.chat.id, ru_strings.goodbye_message['strings'][0], parse_mode='Markdown')
    bot.send_sticker(msg.chat.id, ru_strings.goodbye_message['stickers'][0])

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


def replygetconcept_msg(photoID):
    filepatch = './photos/{:s}.jpg'.format(photoID)
    _file = Path(filepatch)
    if _file.is_file() is not True:
        fileinfo = bot.get_file(photoID)
        file = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(config.token, fileinfo.file_path), stream=True)
        filepatch = './photos/{:s}.jpg'.format(fileinfo.file_id)
        if file.status_code == 200:
            with open(filepatch, 'wb') as f:
                file.raw.decode_content = True
                shutil.copyfileobj(file.raw, f)
                f.close()


    concepts = picturedetect.analizephoto(filepatch)
    name1 = concepts[0]['name']
    name2 = concepts[1]['name']
    name3 = concepts[2]['name']

    #Костыль костылевский
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

    logger.info("[WHATISTHIS] Photo ID {0} - [{1}|{2}|{3}]".format(photoID, name1, name2, name3))
    return "*{}!*".format(answers[0][0])

@bot.message_handler(commands=['start'])
def start_message(message):
    logger.info("/start command by {:s}, Username {:d}".format(message.from_user.first_name, message.from_user.username))
    if(message.chat.id > 0 ):
        bot.send_message(message.chat.id, ru_strings.start_message['strings'][0].format(message.chat.first_name))

@bot.message_handler(commands=['nextstream'])
def _nextstream(message):
    logger.info("/nextstream command by {:s}, Username @{:s}".format(message.from_user.first_name, message.from_user.username))
    bot.send_message(message.chat.id, nextstream.getnextstreammsg(), parse_mode='Markdown')

@bot.message_handler(commands=['gotospace'])
def _gotospace(message):
    logger.info("/gotospace command by {:s}, Username @{:s}".format(message.from_user.first_name, message.from_user.username))
    bot.send_message(message.chat.id, ru_strings.offtop_command_message, parse_mode='Markdown')
    
@bot.message_handler(commands=['info'])
def start_message(message):
    print(message)
    logger.info("/info command by {:s}, Username @{:s}".format(message.from_user.first_name, message.from_user.username))
    bot.send_message(message.chat.id, ru_strings.info_command_message, parse_mode='Markdown')

@bot.message_handler(commands=['msg'])
def start_message(message):
    logger.info("/msg command by {:s}, Username @{:s}".format(message.from_user.first_name,message.from_user.username))
    if message.from_user.id == config.ownerid:
        logger.info("Owner detected!")
        bot.send_message(message.chat.id, ru_strings.sendmsg_message['strings'][0], parse_mode='Markdown')
        reply_toOwner['ownerid'] = message.from_user.id
        reply_toOwner['reply'] = True
        bot.register_next_step_handler(message, send_message)

def send_message(message):
    if message.text.find('/cancel') != -1:
        bot.send_message(message.chat.id, ru_strings.cancel_message['strings'][0], parse_mode='Markdown')
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
        bot.send_message(message.chat.id, ru_strings.sendsticker_message['stickers'][0], parse_mode='Markdown')
        bot.register_next_step_handler(message, send_sticker)

def send_sticker(message):
    if message.content_type is not 'sticker':
        if message.text is not None:
            if message.text.find('/cancel') != -1:
                bot.send_message(message.chat.id, ru_strings.cancel_message['strings'][0], parse_mode='Markdown')
            else:
                bot.send_message(message.chat.id, ru_strings.sendsticker_message['stickers'][1], parse_mode='Markdown')
                bot.register_next_step_handler(message, send_sticker)
    else:
        bot.send_sticker(config.send_chat_id, message.sticker.file_id)
        logger.info("Sending sticker {:s} to chat {:d}".format(message.sticker.file_id, config.send_chat_id))

@bot.message_handler(content_types=["photo"])
def photorecieve(message):
    fileinfo = bot.get_file(message.photo[len(message.photo) - 1].file_id)
    file = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(config.token, fileinfo.file_path), stream=True)
    filepatch = './photos/{:s}.jpg'.format(fileinfo.file_id)
    if file.status_code == 200:
        with open(filepatch, 'wb') as f:
            file.raw.decode_content = True
            shutil.copyfileobj(file.raw, f)
            f.close()
        logger.info("Photo by Username @{:s} | ID {:s}".format(message.from_user.username, fileinfo.file_id))
        logger.info("Start analizing | ID {:s}".format(fileinfo.file_id))
        concepts = picturedetect.analizephoto(filepatch)
        if picturedetect.checkblacklist(concepts, picturedetect.blacklist, logger) is True:
            bot.reply_to(message, ru_strings.spacedetect_message['strings'][0], parse_mode='Markdown')
            bot.send_sticker(message.chat.id, ru_strings.spacedetect_message['stickers'][0])
            bot.send_chat_action(message.chat.id, 'typing')
            sleep(8)
            _gotospace(message)
            logger.info("SPACE FINDED! | ID {:s}".format(fileinfo.file_id))
        else:
            logger.info("SPACE NOT FINDED! | ID {:s}".format(fileinfo.file_id))
        if message.forward_from is None and message.caption is not None:
            if re.match('(?i)(\W|^)(!п[еэ]рс(ичек|ик).*?)(\W|$)', message.caption):
                bot.reply_to(message, replygetconcept_msg(fileinfo.file_id), parse_mode='Markdown')

@bot.message_handler(regexp='(?i)(\W|^)(!п[еэ]рс(ичек|ик).*?)(\W|$)')
def persik_keyword(message):
    if message.reply_to_message is not None:
        if message.reply_to_message.photo is not None:
            fileinfo = bot.get_file(message.reply_to_message.photo[len(message.reply_to_message.photo) - 1].file_id)
            msg = replygetconcept_msg(fileinfo.file_id)
            bot.reply_to(message, msg, parse_mode='Markdown')
            return
    if len(message.text) < 9:
        comehere_message(message)
        return
    if re.match('(?i)(\W|^).*?(.*?пить.*?или.*?не).*?(\W|$)', message.text):
        drink_question(message)
        return
    if re.match('(?i)(\W|^).*?((иди сюда)|(ты где)|(ты тут)|(привет)|(кыс)).*?(\W|$)', message.text):
        comehere_message(message)
        return
    if re.match('(?i)(\W|^).*?((когда.*?стрим|трансляция|(зап|п)уск)|((стрим|трансляция|(зап|п)уск).*?когда)).*?(\W|$)', message.text):
        answerstream(message)
        return
    if re.match('(?i)(\W|^).*?((зануда*?)|(космос*?)|(выгони*?)).*?(\W|$)', message.text):
        answergotospace(message)
        return
    if re.match('(?i)(\W|^).*?((мозг)|(живой)|(красав)|(молодец)|(хорош)).*?(\W|$)', message.text):
        goodboy(message)
        return
    bot.reply_to(message, ru_strings.na_message['strings'][0], parse_mode='Markdown')

def drink_question(message):
    logger.info("[Come here] command by {:s}, Username @{:s} | '{:s}'"
                .format(message.from_user.first_name, message.from_user.username, message.text))
    r_number = randint(0, 3)
    bot.reply_to(message, ru_strings.drinkquestion_message['strings'][r_number], parse_mode='Markdown')

def comehere_message(message):
    logger.info("[Come here] command by {:s}, Username @{:s} | '{:s}'"
                .format(message.from_user.first_name, message.from_user.username, message.text))
    r_number = randint(0, 6)
    bot.reply_to(message, ru_strings.imhere_message['strings'][r_number], parse_mode='Markdown')

def answerstream(message):
    logger.info("[Next stream] command by {:s}, Username @{:s} | '{:s}'"
                .format(message.from_user.first_name, message.from_user.username, message.text))
    _nextstream(message)

def answergotospace(message):
    logger.info("[Gotospace] command by {:s}, Username @{:s} | '{:s}'"
                .format(message.from_user.first_name, message.from_user.username, message.text))
    _gotospace(message)

@bot.message_handler(regexp='(?i)(\W|^)((мозг*?)|(живой*?)|(красав*?)|(молодец*?)|(хороший*?))(\W|$)')
def goodboy_message(message):
    if message.reply_to_message is not None:
        if message.reply_to_message.from_user.id == config.bot_id:
            goodboy(message)

def goodboy(message):
    logger.info("[Good boy] command by {:s}, Username @{:s} | '{:s}')"
                .format(message.from_user.first_name, message.from_user.username, message.text))
    bot.send_sticker(message.chat.id, ru_strings.goodboy_message['stickers'][0])

@bot.message_handler(regexp='(?i)(\W|^)(Привет Т[её]ма)(\W|$)')
def secret_message(message):
    bot.send_message(message.chat.id, 'Ы', parse_mode='Markdown')

if __name__ == '__main__':
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
    cherrypy.quickstart(WebhookServer(), config.WEBHOOK_URL_PATH, {'/': {}})

    bot.set_update_listener(listener)

    logger.info("Alpha-Bot started!")






