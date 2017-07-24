# -*- coding: utf-8 -*-

START_MESSAGE = {'strings': ['Привет, {:s}! Рад тебя видеть!'],
                 'stickers': None}

HELLO_MESSAGE = {'strings': [
    "Добро пожаловать!",
    "Привет тебе!",
    "Рад вас видеть!",
    "Привет новенький!",
    "Добро пожаловать в оффтоп!",
    "Приветик!"],
    'stickers': None}

GOODBYE_MESSAGE = {'strings': ["*Мне будет тебя нехватать..*"],
                   'stickers': ["CAADAgADHwMAApFfCAABY7_lnPiNJHEC"]}

BOT_HI_MESSAGE = {'strings': ["Всем привет!"],
                  'stickers': ['CAADAgADZQMAApFfCAABq6OimQg-V5EC']}

IM_HERE_MESSAGE = {'strings': [
    '*Я тут!*',
    '*Чем могу служить?*',
    '*Что хотели? :D*',
    '*Говори, только быстро!*',
    'Мяу!',
    '*Привет!*'],
    'stickers': None}

SPACE_DETECT_MESSAGE = {'strings': ['*Какой космос!? Накажу!*',
                                    '*Это похоже на космос!*'],
                        'stickers': ['CAADAgADEQMAApFfCAABY-zGe3B9vwgC',
                                     'CAADAgADJQMAApFfCAABx8uFnPP2m80C']}

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

NA_MESSAGE = {'strings': ['*Не понял вопрос.. D:*',
                          '*Попробуй спросить еще раз.*',
                          '*Хватит над персиком издеватся!((*'],
              'stickers': [None,
                           None,
                           'CAADBAADKgADNDzmB3S04SrrT1xhAg']}

SOME_ERROR_MESSAGE = {'strings': ['*Ой, ошибка какая-то!*'],
                      'stickers': ['CAADBAADKgADNDzmB3S04SrrT1xhAg']}

OFFTOP_COMMAND_MESSAGE = '''*Ой, кажется кто-то здесь начал говорить про космос.*
Друзья, для зануд у нас есть [специальный чат](https://t.me/thealphacentauri). Велкам!'''

INFO_COMMAND_MESSAGE = '''В чате стараемся не оскорблять участников.
Спам смайлами и стикерами наказуемы.
Политота и демагогия *могут* пресекаться.

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
