# -*- coding: utf-8 -*-

from datetime import datetime
from datetime import timedelta
from PIL import Image
import requests
from io import BytesIO
import threading

himawari = {
    'imagePath': './himawaripictures/lastpicture.png',
    'imageUrl': 'http://himawari8.nict.go.jp/img/D531106/8d/550'
}

tile_width = 550
tile_height = 550

image_scale = 8
tile_array = [[None] * image_scale] * image_scale


def get_file_path(timeutc, x, y):
    return "%s/%s/%02d/%02d/%02d%02d00_%s_%s.png" \
           % (himawari['imageUrl'], timeutc.year, timeutc.month,
              timeutc.day, timeutc.hour, round(timeutc.minute / 10) * 10, x, y)


session = requests.Session()
png = Image.new('RGB', (tile_width * image_scale, tile_height * image_scale))
last_update_time = datetime.now()


def update_image():
    time_now = datetime.utcnow() - timedelta(minutes=40)

    print("Updating image..")
    try:
        for x in range(image_scale):
            for y in range(image_scale):
                file_path = get_file_path(time_now, x, y)
                tile_data = session.get(file_path).content
                tile = Image.open(BytesIO(tile_data))
                png.paste(tile, (tile_width * x, tile_height * y,
                                 tile_width * (x + 1), tile_height * (y + 1)))

        png.save(himawari['imagePath'], 'PNG')

        print("Done!")
    except Exception as e:
        print(e)

    global last_update_time
    last_update_time = datetime.now()
    threading.Timer(10 * 60, update_image).start()
