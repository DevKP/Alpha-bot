# -*- coding: utf-8 -*-
from clarifai.rest import ClarifaiApp

KEY = 'c3e552013fa64ff2a3beea5fefbb597e'
app = ClarifaiApp(api_key=KEY)

BLACKLIST = {'планета', 'астрономия', 'вселенная',
             'орбита', 'космическое пространство',
             'солнечная система', 'космический корабль',
             'галактика', 'астрология',
             'туманность', 'созвездие', 'сверхновая звезда',
             'космея', 'телескоп', 'внешний', 'Юпитер',
             'Сатурн (планета)', 'Марс'}


def analise_photo(file):
    model = app.models.get('general-v1.3')
    res = model.predict_by_filename(file)
    outputs = res.get('outputs')
    for output in outputs:
        return output.get('data').get('concepts')


def check_blacklist(concepts, blacklist, logger=None):
    intersection = {concept['name'] for concept in concepts} & blacklist
    if len(intersection) != 0:
        if logger:
            logger.info("Triggered by %s " % intersection)
        return True
    return False
