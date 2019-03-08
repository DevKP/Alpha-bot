# -*- coding: utf-8 -*-

token = ''  # Bot API token
provider_token = '' 
WIT_token = ''  # WIT token
api_id = 0  # Telegram Client ID
api_hash = ''  # Telegram Client Hash

WEBHOOK_HOST = '0.0.0.0'  # Host IP
WEBHOOK_PORT = 8443  # 443, 80, 88, 8443
WEBHOOK_LISTEN = '0.0.0.0'

WEBHOOK_SSL_CERT = './webhook_cert.pem'  # Certificate path
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'  # Private key path

WEBHOOK_URL_BASE = "https://{0}:{1}".format(WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/{:s}/".format(token)

send_chat_id = -1001125742098
bot_id = 407478787

exec_allowed_users = {
    204678400,
    59415606,
    198813830,
    243956745,
    56653908,
    331016418
}

stickers_black_list = {'CAADAgADCw8AAtEbogwJPT3WA-qidwI'}

CONCEPTS_COUNT = 3  # Number of keywords
