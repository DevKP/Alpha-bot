import logging
import subprocess
import os
import requests
import shutil
from time import sleep
import telebot

import config

logger = logging.getLogger('alphabot')
telebot.logger.setLevel(logging.INFO)
bot = telebot.TeleBot(config.token)


def convert_oga_to_mp3(in_filename=None):
    command = [
        r'.\ffmpeg\bin\ffmpeg.exe',
        '-y',
        '-i', in_filename,
        '-acodec', 'libmp3lame',
        '{}.mp3'.format(in_filename)
    ]

    proc = subprocess.Popen(command)
    proc.wait()


def file_download(file_info, path, attempts=3):
    '''
    Downloads file to path
    Returns : file path

    Parameters
    ----------
    file_id : str
        File ID
    path : str
        Save path
    attempts : int
        Amount of attempts (default 3)
    '''

    _, file_extension = os.path.splitext(file_info.file_path)
    filename = file_info.file_id

    for i in range(attempts):
        file = requests.get('https://api.telegram.org/file/bot{}/{}'.format(
            config.token, file_info.file_path), stream=True)
        if file.status_code == 200:
            file_patch = "".join([path, filename, file_extension])
            try:
                with open(file_patch, 'bw+') as f:
                    file.raw.decode_content = True
                    shutil.copyfileobj(file.raw, f)
            except Exception as e:
                logger.error("[Write to file] Unexpected error: {}".format(e))
                return None

            return file_patch
        else:
            logger.error("(Attempt #{}) File download error! Status Code: {}".format(
                i, file.status_code))

            sleep(3)

    return None
