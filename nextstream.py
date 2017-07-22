# -*- coding: utf-8 -*-
from datetime import datetime

dtime = datetime(2017, 7, 28, 18, 41, 0)
#dtime = datetime(2017, 7, 21, 15, 13, 0)
timestr = '18:41'
rocket = 'Союз-ФГ'
place = 'Байконур, Казахстан'
streamlink = ''

def getnextstreammsg():
    delta = dtime - datetime.now()

    if delta.total_seconds() < 0:
        hours, remainder = divmod(delta.total_seconds() * -1, 3600)
        minutes, seconds = divmod(remainder, 60)
        time = 'Пуск должен был состоятся %dч. %dмин. назад'%(hours, minutes)
    else:
        days, remainder = divmod(delta.total_seconds(), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        time = 'Следующий пуск состоится *через %dд. %dч. %dмин.*'%(days, hours, minutes)

    infotext = '{0} ({1} по Киеву/МСК).\nРакета-носитель: {2}.\nМесто пуска: {3}\n\n[Ссылка на трансляцию]({4})\n\n'.format(time, timestr, rocket, place, streamlink)
    cautiontext = '*Внимание! Учтите, что трансляция начинается за 20-30 минут до пуска!*'

    return "".join([infotext, cautiontext, '\n//\n\n//'])
