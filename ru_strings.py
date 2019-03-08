# -*- coding: utf-8 -*-

START_MESSAGE = {'strings': ['Привет, {:s}! Рад тебя видеть!'],
                 'stickers': None}

HELLO_MESSAGE = {'strings': [
    "*Добро пожаловать!*",
    "*Привет тебе!*",
    "*Рад вас видеть!*",
    "*Привет, новенький!*",
    "*Добро пожаловать в оффтоп!*",
    "*Приветик!*"],
    'stickers': None}

GOODBYE_MESSAGE = {'strings': ["*Мне будет тебя нехватать..*"],
                   'stickers': ["CAADAgADHwMAApFfCAABY7_lnPiNJHEC"]}

BOT_HI_MESSAGE = {'strings': ["Всем привет!"],
                  'stickers': ['CAADAgADZQMAApFfCAABq6OimQg-V5EC']}

IM_HERE_MESSAGE = {'strings': [
    '*Я!*',
    '*Чем могу служить? 🧐*',
    '*Что? :D*',
    '*Персик говорит - Мяу!*',
    '*Барсик йух*',
    '*о-о*',
    '*🌚*',],
    'stickers': None}

SPACE_DETECT_MESSAGE = {'strings': ['*Обнаружена космическая тематика!*',
                                    '*Это похоже на космос!*'],
                        'stickers': [None,
                                     None]}

DRINK_QUESTION_MESSAGE = {'strings': [
    '*Пить!*',
    '*Однозначно, пить!*',
    '*Не пить!*',
    '*Не пей, подумой!*'],
    'stickers': None}

GOOD_BOY_MESSAGE = {'strings': None,
                    'stickers': ['CAADAgADQQMAApFfCAABzoVI0eydHSgC']}

BAD_BOY_MESSAGE = {'strings': None,
                   'stickers': ['CAADAgADIQMAApFfCAABP2eivT2lvA4C']}

SEND_STICKER_MESSAGE = {'strings': ['Пришли стикер, я отправлю :3! /cancel если передумал.',
                                    '*Это не стикер!*'],
                        'stickers': None}

SEND_MSG_MESSAGE = {'strings': ['Пришли сообщение! /cancel если передумал.',
                                '*Выполнено!*'],
                    'stickers': None}

CANCEL_MESSAGE = {'strings': ['*Окей, не хочешь - как хочешь!*'],
                  'stickers': None}

BAN_MESSAGE = {'strings': ["*{} забанен на {} {}*",
                           "*{} получает перманентный бан!*",
                           "*{} самозабанился на {} {}!*"],
               'stickers': None}

ROULETTE_MESSAGE = {'strings': ["*Пользователь {} застрелился!*",
                                "*Пользователю {} очень повезло!*"],
                    'stickers': None}

GET_ID_MESSAGE = {'strings': ["*Твой уникальный идентификатор: {}*"],
                  'stickers': None}

NA_MESSAGE = {'strings': ['*Не понял вопрос.. D:*',
                          '*Попробуй спросить еще раз.*',
                          '*Хватит над персиком издеваться!((*'],
              'stickers': [None,
                           None,
                           'CAADBAADKgADNDzmB3S04SrrT1xhAg']}

SOME_ERROR_MESSAGE = {'strings': ['*Ой, ошибка какая-то!*'],
                      'stickers': ['CAADBAADKgADNDzmB3S04SrrT1xhAg']}

OFFTOP_COMMAND_MESSAGE = '''*Ой, кажется кто-то здесь начал говорить про космос.*
Друзья, для зануд у нас есть [специальный чат](https://t.me/thealphacentauri). Велкам!'''

INFO_COMMAND_MESSAGE = '''*1.* За систематические оскорбления, переход на личности и неадекватное поведение - *бан*. В особо тяжких случаях и особо тугодумных личностей - *перманетный бан*. 
    *1.1.*  _Если вы считаете, что бан выдан несправедливо, есть возможность оспорить его предоставив пруфы модераторам._
    *1.2.* Чрезмерное употребление мата - *бан*. Тут могут быть дети. Так что, по возможности, соблюдайте данный пункт! Это в ваших интересах и в наших. Мы не стараемся ограничить вас в лексике, мы помогаем вам грамотно обосновать свой ответ оппоненту. Если произошло оскорбление вас, как личности, вас это задело, вы *ВПРАВЕ* рассказать модераторам и ваш вопрос решат.

*2.* Спам смайлами и стикерами наказуемы.
*3.* Политота и демагогия *могут* пресекаться.


*Набор полезных ссылок:*
🚀[Наш канал в Telegram](https://t.me/alphacentaurichannel)
🚀[Мы в тви](https://twitter.com/theACentauri)
🚀[Поддержать нас на Patreon](https://patreon.com/thealphacentauri)
🚀[Стикер-пак Alpha Centauri](https://t.me/addstickers/thealphacentauri)

🚀[Расписание трансляций](https://thealphacentauri.net/schedule)
🚀[Мы ВК](http://vk.com/thealphacentauri)
🚀[Ссылка на канал на YouTube](http://youtube.com/threedaysfaq)

*Команды бота (тоже стараемся не спамить):*
/nextstream@alphaofftopbot – дата, время, ссылка на следующий стрим
/gotospace@alphaofftopbot – вывести ссылку на основной оффтоп чат XD
/info@alphaofftopbot – отображает эту информацию'''

NSFW_TOGGLE_MESSAGE = {'strings': ['*NSFW запрещен.*','*NSFW разрешен.*'],
                        'stickers': None}