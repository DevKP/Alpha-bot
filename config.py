# -*- coding: utf-8 -*-

token = 'TOKEN'
provider_token = '361519591:TEST:36f78445e159f9c11e7ff86bb9184e01'

WEBHOOK_HOST = '176.37.39.165'
WEBHOOK_PORT = 8443  # 443, 80, 88, 8443
WEBHOOK_LISTEN = '0.0.0.0'

WEBHOOK_SSL_CERT = './webhook_test_cert.pem'  # Путь к сертификату
WEBHOOK_SSL_PRIV = './webhook_test_pkey.pem'  # Путь к приватному ключу

WEBHOOK_URL_BASE = "https://{0}:{1}".format(WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/{:s}/".format(token)

send_chat_id = -1001125742098
bot_id = 407478787

allowed_users = {
    204678400, 
    59415606,
    243956745
}

exec_allowed_users = {
    204678400, 
    59415606,
    198813830,
    30260375,
	243956745
}

CONCEPTS_COUNT = 3  # Количество ключевых слов

