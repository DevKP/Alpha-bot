# -*- coding: utf-8 -*-
from datetime import datetime

STREAMS = [
    {
    'datetime': datetime(2017, 11, 28, 7, 41, 0),
    'time_str_ua': '7:41',
    'time_str_ru': '8:41',
    'rocket': 'Союз-2',
    'place': 'Космодром «Восточный»',
    'stream_link': None,
    'info_link': None
    }
]


def get_next_stream_msg(streams):
    actual_stream = None

    for stream in streams:
        if (stream['datetime'] - datetime.now()).total_seconds() > 0:
            actual_stream = stream
            break

    delta = actual_stream['datetime'] - datetime.now()

    if delta.total_seconds() < 0:
        hours, remainder = divmod(delta.total_seconds() * -1, 3600)
        minutes, seconds = divmod(remainder, 60)
        time = 'Пуск должен был состояться *%dч. %dмин. назад*' % (hours, minutes)
    else:
        days, remainder = divmod(delta.total_seconds(), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes = round(remainder / 60)

        if days == 0:
            days = ''
        else:
            days = '%dд. ' % days

        if hours == 0:
            hours = ''
        else:
            hours = '%dч. ' % hours
        
        time = 'Следующий пуск состоится *через {}{}{}мин.*'.format(days, hours, minutes)

    info_text = '{0} ({1} по Киеву/{2} МСК).\n' \
                'Ракета-носитель: {3}.\n' \
                'Место пуска: {4}\n\n' \
                '[Ссылка на трансляцию]({5})\n' \
                '[Информация о пуске]({6})\n\n'.format(time, actual_stream['time_str_ua'], actual_stream['time_str_ru'], actual_stream['rocket'], actual_stream['place'],
                                                       actual_stream['stream_link'] or '', actual_stream['info_link'] or '')
    caution_text = '*Внимание! Учтите, что трансляция начинается за 20-30 минут до пуска!*'

    return "".join([info_text, caution_text, ' ' if actual_stream['stream_link'] else '\n//\n\n//'])
