from picturedetect import check_blacklist, BLACKLIST, process_words, process_concepts


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


def test_process_words_three_words():
    concepts = [
        {
            'name': "кот"
        },
        {
            'name': "пушистый"
        },
        {
            'name': "стол"
        }
    ]
    words = process_words(concepts)

    assert words == [["пушистый", "кот"], ["стол"]]


def test_process_words_two_word():
    concepts = [
        {
            'name': "кот"
        },
        {
            'name': "стол"
        }
    ]
    words = process_words(concepts)

    assert words == [["кот"], ["стол"]]


def test_process_words_zero():
    concepts = [
    ]
    words = process_words(concepts)

    assert words == []


def test_process_words_with_replace():
    concepts = [
        {
            'name': "кот"
        },
        {
            'name': "нет человек"
        }
    ]
    words = process_words(concepts)

    assert words == [["кот"], ["безлюдно"]]


def test_process_concepts():
    concepts = [
        {
            'name': "кот"
        },
        {
            'name': "пушистый"
        },
        {
            'name': "стол"
        }
    ]
    message, _ = process_concepts(concepts)

    assert message == "*Я думаю, это пушистый кот, стол!*"
