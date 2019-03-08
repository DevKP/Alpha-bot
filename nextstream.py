# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import json
import requests

# Launch Status
l_status = ["", "Launch is GO", "Launch is NO-GO",
            "Launch was a success", "Launch failed"]

# Message Template
l_template = '''<b>Следующий пуск через {delta_ua}</b>
<b>По Киеву</b><a href="{pic}">:</a> {time_ua}
<b>По МСК</b>: {time_msk}

<b>Ракета-носитель:</b> {rocket}(<a href="{r_wiki}">wiki</a>)
<b>Место пуска:</b> {place}(<a href="{p_wiki}">wiki</a>) <a href="{p_map}">🗺</a>
<b>Полезная нагрузка:</b> {payload}

<b>Миссия:</b> {mission}

<b>СТАТУС:</b> {status}
<b>Watch:</b> {watch}

{hold}
<b>Внимание! Учтите, что трансляция начинается за 20-30 минут до пуска!</b>
'''


holdreason = 'IN HOLD! Hold Reason: {}\n'  # Message if launch in hold state
watch_link = None  # AC channel stream link


def get_next_stream_msg():
    ''' Gets info about the next launch from launchlibrary.net

    Returns
    -------
    string
        Formatted message string with information about the next launch.

    Raises
    ------
    Exception
        If response status code isn't 200
    '''

    resp = requests.get('https://launchlibrary.net/1.3/launch/next/1')
    if resp.status_code == 200:
        json_obj = json.loads(resp.content.decode("utf-8"))
        launch = json_obj['launches'][0]

        time_ua = datetime.fromtimestamp(launch['netstamp'])
        ua_delta_ua = time_ua - datetime.now()
        delta_ua = str(
            timedelta(seconds=ua_delta_ua.seconds, days=ua_delta_ua.days))

        time_msk = time_ua
        delta_msk = delta_ua

        rocket = launch['rocket']['name']
        r_wiki = launch['rocket']['wikiURL']
        place = launch['location']['pads'][0]['name']
        p_wiki = launch['location']['pads'][0]['wikiURL']
        status = l_status[launch['status']]
        pic = (watch_link or launch['rocket']['imageURL'])
        payload = launch['missions'][0]['name']
        mission = launch['missions'][0]['description']
        p_map = 'https://www.google.com/maps/?q={},{}'.format(
                                    launch['location']['pads'][0]['latitude'],
                                    launch['location']['pads'][0]['longitude'])

        if launch['inhold'] == True:
            hold = holdreason.format(launch['holdreason'])
        else:
            hold = ''

        return l_template.format(time_ua=time_ua.strftime("%d.%m %H:%M:%S"),
            delta_ua=delta_ua, time_msk=time_msk.strftime("%d.%m %H:%M:%S"),
            delta_msk=delta_msk, rocket=rocket, r_wiki=r_wiki, place=place,
            p_wiki=p_wiki, status=status, pic=pic, p_map=p_map, hold=hold,
            payload=payload, mission=mission, watch=(watch_link or ' ... '))

    else:
        print("error ", resp.status_code)
        raise Exception("Response: {}".format(resp.status_code))
