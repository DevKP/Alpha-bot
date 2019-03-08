# -*- coding: utf-8 -*-
import re
from pathlib import Path

import pymorphy2
import itertools
from clarifai.rest import ClarifaiApp

import config
import utils
from utils import logger

KEY = 'c3e552013fa64ff2a3beea5fefbb597e'
ENKEY = 'dbd34c9715484a3abb0bc75a12f1de8f'
app = ClarifaiApp(api_key=KEY)
enapp = ClarifaiApp(api_key=ENKEY)

BLACKLIST = {'Луна', 'планета', 'астрономия', 'вселенная',
             'орбита', 'космическое пространство',
             'солнечная система', 'космический корабль',
             'галактика', 'астрология',
             'туманность', 'созвездие', 'сверхновая звезда',
             'космея', 'телескоп', 'внешний', 'Юпитер',
             'Сатурн (планета)', 'Марс'}

IGNORELIST = {'нет человек'}


def analise_photo(file):
    model = app.models.get('general-v1.3')
    res = model.predict_by_filename(file)
    outputs = res.get('outputs')
    for output in outputs:
        concepts = (concept for concept in output.get('data').get(
            'concepts') if concept['name'] not in IGNORELIST)
        return concepts


def nsfw_test(file, procents):
    model = enapp.models.get('nsfw-v1.0')
    res = model.predict_by_filename(file)

    outputs = res.get('outputs')
    for output in outputs:
        for concept in output.get('data').get('concepts'):
            if concept['name'] == 'nsfw' and concept['value'] > procents:
                return True

    return False


def check_blacklist(concepts, blacklist, logger=None):
    intersection = {concept['name'] for concept in list(concepts)[:3]} & blacklist
    if len(intersection) != 0:
        if logger:
            logger.info("Triggered by %s " % intersection)
        return True
    return False


# To replace words, add a new entry to this dictionary.
REPLACE_MAP = {
    'нет человек': 'безлюдно'
}


def reply_get_concept_msg(photo_id):
    file_patch = './photos/{:s}.jpg'.format(photo_id)
    _file = Path(file_patch)
    if not _file.is_file():
        file_info = utils.bot.get_file(photo_id)
        file_patch = utils.file_download(file_info, './photos/')

    concepts = itertools.islice(analise_photo(file_patch), config.CONCEPTS_COUNT)

    message, word_sets = process_concepts(concepts)

    logger.info("[WHATISTHIS] Photo ID {} - [{}]".format(photo_id, "|".join(word_sets)))
    return message


def process_concepts(concepts):
    words = process_words(concepts)
    word_sets = [" ".join(word_set) for word_set in words]
    return "*, я думаю, это {}!*".format(", ".join(word_sets)), word_sets


def get_tags(word):
    required_grammemes = set()
    if word.tag.gender:
        required_grammemes.add(word.tag.gender)
    if word.tag.case:
        required_grammemes.add(word.tag.case)
    if word.tag.number:
        required_grammemes.add(word.tag.number)
    return required_grammemes


morph = pymorphy2.MorphAnalyzer()


def get_words(*words):
    count = len(words)
    if count == 0:
        return []
    elif count == 1:
        return [words[0].word]

    required_grammemes = [get_tags(word) for word in words]

    answer = [words[count - 1].inflect(required_grammemes[count - 1]).word]

    for i in range(count - 2, -1, -1):
        word = words[i].inflect(required_grammemes[i + 1])
        if not word:
            word = words[i].inflect(required_grammemes[i])

        answer = [word.word] + answer

    return answer


def sort_words(word):
    return word.tag.POS


MAIN_POS = ["NOUN"]

SINGLE_POS = ["ADVB"]


def clean(name):
    name = REPLACE_MAP.get(name, name)
    name = re.sub(r'(.*) \(.*\)', r'\1', name)
    name = re.sub(r'([^\w\s])', r'', name)
    return name


def process_words(concepts):
    """
    1) Sort so that adjectives are before nouns
    2) Divide into phrases so that each phrase is not
    more than one noun or adverb
    3) We agree on each phrase separately

    : param concepts: words to be processed
    : return: words grouped into phrases
    """
    names = [clean(concept['name']) for concept in concepts]

    words = [morph.parse(name)[0] for name in names]

    if all([x.tag.POS in MAIN_POS + SINGLE_POS for x in words]):
        return [[name] for name in names]

    words.sort(key=sort_words)

    word_sets = [[words[0]]]

    index = 0

    for i in range(1, len(words)):
        word = words[i]
        pos = word.tag.POS
        prev_pos = words[i - 1].tag.POS
        if (pos in MAIN_POS and prev_pos in MAIN_POS) or prev_pos in SINGLE_POS or pos in SINGLE_POS:
            word_sets += [[word]]
            index += 1
        else:
            word_sets[index] += [word]

    return [get_words(*word_set) for word_set in word_sets]
