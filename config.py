# -*- coding: utf-8 -*-

token = '407478787:AAGhAJQXIZuKnSd0AOjDc2xhKiOmrKI9_Rk'

WEBHOOK_HOST = '176.37.39.165'
WEBHOOK_PORT = 8443  # 443, 80, 88 или 8443 (порт должен быть открыт!)
WEBHOOK_LISTEN = '0.0.0.0'  # На некоторых серверах придется указывать такой же IP, что и выше

WEBHOOK_SSL_CERT = './webhook_test_cert.pem'  # Путь к сертификату
WEBHOOK_SSL_PRIV = './webhook_test_pkey.pem'  # Путь к приватному ключу

WEBHOOK_URL_BASE = "https://{0}:{1}".format(WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/{:s}/".format(token)

send_chat_id = -1001149008244
bot_id = 407478787
owner_id = 204678400
exodeon_id = 42577446
