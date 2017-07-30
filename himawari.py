# -*- coding: utf-8 -*-

from datetime import datetime
from datetime import timedelta
from PIL import Image
import requests
import os
from io import BytesIO
import threading
from pathlib import Path

from utils import logger

himawari = {
    'imagePath': './himawaripictures/latestpicture.png',
    'imageUrl': 'http://himawari8-dl.nict.go.jp/himawari8/img/D531106/8d/550'
}

tile_width = 550
tile_height = 550

image_scale = 8
tile_array = [[None] * image_scale] * image_scale


def get_file_path(timeutc, x, y):
    return "%s/%s/%02d/%02d/%02d%02d00_%s_%s.png" \
           % (himawari['imageUrl'], timeutc.year, timeutc.month,
              timeutc.day, timeutc.hour, round(timeutc.minute / 10) * 10, x, y)


def gettime(path):
    return os.path.getctime(''.join(['./himawaripictures/', path]))


def gettimelowres(path):
    return os.path.getctime(''.join(['./himawaripictures_lowres/', path]))


def delete_old_photo(maxnum):
    photos = sorted(os.listdir('./himawaripictures/'), key=gettime)
    lowres_photos = sorted(os.listdir('./himawaripictures_lowres/'), key=gettimelowres)
    if len(photos) > maxnum:
        os.remove(''.join(['./himawaripictures/', photos[0]]))
    if len(lowres_photos) > maxnum:
        os.remove(''.join(['./himawaripictures_lowres/', lowres_photos[0]]))


last_update_time = datetime.now()


def update_image():
    global last_update_time
    threading.Timer(10 * 60, update_image).start()

    png = Image.new('RGB', (tile_width * image_scale, tile_height * image_scale))
    time_now = datetime.utcnow() - timedelta(minutes=60)
    session = requests.Session()

    logger.info("[himawari] Updating image.. Photo {}".format(time_now))

    try:
        for x in range(image_scale):
            for y in range(image_scale):
                file_path = get_file_path(time_now, x, y)
                tile_data = session.get(file_path).content
                tile = Image.open(BytesIO(tile_data))
                png.paste(tile, (tile_width * x, tile_height * y,
                                 tile_width * (x + 1), tile_height * (y + 1)))
                # logger.info("[himawari] Tile {}x{}".format(x,y))

        if Path(himawari['imagePath']).is_file():
            os.rename(himawari['imagePath'],
                      './himawaripictures/{}.png'.format(last_update_time.strftime("%Y%m%d%H%M%S")))
        png.save(himawari['imagePath'], 'PNG')

        if Path('./himawaripictures_lowres/latestpicture.png').is_file():
            os.rename('./himawaripictures_lowres/latestpicture.png', './himawaripictures_lowres/{}.png'
                      .format(last_update_time.strftime("%Y%m%d%H%M%S")))

        png = png.resize((1800, 1800), Image.ANTIALIAS)
        png.save('./himawaripictures_lowres/latestpicture.png', format="PNG", quality=85)
        delete_old_photo(115)
        logger.info("[himawari] Done!")
    except Exception as e:
        logger.info("[himawari] {}".format(e))

    last_update_time = datetime.now()
