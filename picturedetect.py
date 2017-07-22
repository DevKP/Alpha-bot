# -*- coding: utf-8 -*-
from clarifai.rest import ClarifaiApp

key = 'c3e552013fa64ff2a3beea5fefbb597e'
app = ClarifaiApp(api_key=key)

blacklist = {'планета','астрономия','вселенная'
            ,'орбита','космическое пространство'
            ,'солнечная система','космический корабль'
            ,'галактика','астрология'
            ,'туманность','созвездие','сверхновая звезда'
            ,'космея','телескоп','внешний','Юпитер'
            ,'Сатурн (планета)','Марс'}

def analizephoto(file):
    model = app.models.get('general-v1.3')
    res = model.predict_by_filename(file)
    outputs = res.get('outputs')
    for output in outputs:
        return output.get('data').get('concepts')


def checkblacklist(concepts, list, logger):
    for concept in concepts:
        for word in list:
            if concept['name'] == word:
                logger.info("Triggered by %s " % word)
                return True