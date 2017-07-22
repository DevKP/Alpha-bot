# -*- coding: utf-8 -*-
from datetime import datetime

STREAM = {
    'datetime': datetime(2017, 7, 28, 18, 41, 0),
    # dtime = datetime(2017, 7, 21, 15, 13, 0),
    'time_str': '18:41',
    'rocket': 'Союз-ФГ',
    'place': 'Байконур, Казахстан',
    'stream_link': ''
}


def get_next_stream_msg(stream):
    delta = stream['datetime'] - datetime.now()

    if delta.total_seconds() < 0:
        hours, remainder = divmod(delta.total_seconds() * -1, 3600)
        minutes, seconds = divmod(remainder, 60)
        time = 'Пуск должен был состоятся %dч. %dмин. назад*' % (hours, minutes)
    else:
        days, remainder = divmod(delta.total_seconds(), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes = round(remainder/60)
        time = 'Следующий пуск состоится *через %dд. %dч. %dмин.*' % (days, hours, minutes)

    info_text = '{0} ({1} по Киеву/МСК).\n' \
                'Ракета-носитель: {2}.\n' \
                'Место пуска: {3}\n\n' \
                '[Ссылка на трансляцию]({4})\n\n'.format(time, stream['time_str'], stream['rocket'], stream['place'],
                                                         stream['stream_link'])
    caution_text = '*Внимание! Учтите, что трансляция начинается за 20-30 минут до пуска!*'

    return "".join([info_text, caution_text, '\n//\n\n//'])
