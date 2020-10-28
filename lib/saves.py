# -*- coding: utf-8 -*-
from loguru import logger
import requests
import json

# Название плагина
name = 'Сохранение обращений'
names = 'saves'


class Plugins(object):
    """docstring for Plugins."""

    def __init__(self, queueotv, config, event, *args, **kwargs):
        super(Plugins, self).__init__()
        # self.actionlist = {'1': self.action_1}
        self.event = event
        if queueotv:
            self.queueotv = queueotv
        else:
            logger.error('Не произведена передача очереди ответов')
            return [False, 'не произведена передача очереди ответов']
        if config:
            self.config = config
        else:
            logger.error('Не произведена передача конфига')
            return [False, 'не произведена передача конфига']

    def run(self):
        while self.event:
            data = self.queueotv.get()
            retu = self.run_saves(data=data)
            if retu:
                self.queueotv.task_done()
            else:
                logger.error(' Не удалось сохранить.')

    def run_saves(self, data):
        url = self.config['script']['typesite'] + '://' + self.config['script']['ipsite'] + ':' + self.config['script']['portsite'] + '/api/problems/saves/'
        try:
            r = requests.post(url, data=json.dumps(data))
        except Exception as e:
            logger.error(f'Ошибка при отправки сохранения. Ошибка: {e}')
            logger.error(f'Форма запроса: {data}')
            return None
        if r.status_code == 200:
            return True
            logger.debug('Умпешно отправлены данные на сохранение')
        else:
            logger.error(f'Ошибка на сервере. Ошбика №{r.status_code}')
            logger.error(f'Форма запроса: {data}')
            return None
