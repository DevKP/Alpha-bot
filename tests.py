from datetime import datetime, timedelta

from nextstream import get_next_stream_msg
from picturedetect import check_blacklist, BLACKLIST


def test_nextstream_future():
    stream = {
        'datetime': datetime.now() + timedelta(hours=24, minutes=25),
        'time_str': '18:41',
        'rocket': 'Союз-ФГ',
        'place': 'Байконур, Казахстан',
        'stream_link': ''
    }

    message = get_next_stream_msg(stream)
    assert message == 'Следующий пуск состоится *через 1д. 0ч. 25мин.* (18:41 по Киеву/МСК).\n' \
                      'Ракета-носитель: Союз-ФГ.\n' \
                      'Место пуска: Байконур, Казахстан\n\n' \
                      '[Ссылка на трансляцию]()\n\n' \
                      '*Внимание! Учтите, что трансляция начинается за 20-30 минут до пуска!*\n//\n\n//'


def test_nextstream_past():
    stream = {
        'datetime': datetime.now() - timedelta(hours=24, minutes=25),
        'time_str': '18:41',
        'rocket': 'Союз-ФГ',
        'place': 'Байконур, Казахстан',
        'stream_link': ''
    }

    message = get_next_stream_msg(stream)
    assert message == 'Пуск должен был состоятся 24ч. 25мин. назад* (18:41 по Киеву/МСК).\n' \
                      'Ракета-носитель: Союз-ФГ.\n' \
                      'Место пуска: Байконур, Казахстан\n\n' \
                      '[Ссылка на трансляцию]()\n\n' \
                      '*Внимание! Учтите, что трансляция начинается за 20-30 минут до пуска!*\n//\n\n//'


def test_check_in_blacklist():
    concepts = [{
        'name': "black word",
    }]

    blacklist = {
        'black word'
    }
    is_black = check_blacklist(concepts, blacklist)
    assert is_black is True


def test_check_not_in_blacklist():
    concepts = [{
        'name': "black word",
    }]

    blacklist = {
        'white word'
    }
    is_black = check_blacklist(concepts, blacklist)
    assert is_black is False


def test_check_current_blacklist():
    concepts = [
        {
            'name': "космос"
        },
        {
            'name': "Сатурн (планета)"
        }
    ]

    is_black = check_blacklist(concepts, BLACKLIST)
    assert is_black is True
