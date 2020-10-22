# -*- coding: utf-8 -*-
from loguru import logger
import pika
import pickle
import traceback

# Название плагина print(f'[{names}]: text')
name = 'Плагин для работы с RabbitMQ'
names = 'rabbit'


class Plugins(object):
    """docstring for Plugins."""

    def __init__(self, queuez, queueotv, config, status, event, *args, **kwargs):
        super(Plugins, self).__init__()
        self.event = event
        self.connection = None
        self.channel = None
        self.daemon = None
        if queuez:
            self.queuez = queuez
        else:
            logger.error('Не произведена передача очереди заданий')
            return [False, 'не произведена передача очереди заданий']
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
        if status:
            self.status = status
        else:
            logger.error('Не произведена передача статуса')
            return [False, 'не произведена передача статуса']
        if 'url' in self.config['rabbit'] or 'login' in self.config['rabbit'] or 'password' in self.config['rabbit'] or 'ip' in self.config['rabbit']:
            url = f"{self.config['rabbit']['url']}{self.config['rabbit']['login']}:{self.config['rabbit']['password']}@{self.config['rabbit']['ip']}"
            self.params = pika.URLParameters(url)
        else:
            logger.critical('Не произведена настройка конфига!')
            return [False, 'не произведена настройка конфига']

    def run(self):
        if not self.connection:
            self.connect()
        self.channel.basic_consume('parsing.tasks', self.read_rabbit)
        self.start_consuming()
        #self.daemon = threading.Thread(target=self.channel.start_consuming(), kwargs={'channel': self.channel}, daemon=True) # BUG: Не создает поток
        # while True:
        #     data = self.queueotv.get()
        #     self.save_rabbit(text=data)
        #     self.queueotv.task_done()

    def inic_rabbit(self):
        if not self.connection and self.channel:
            self.connect()
        self.channel.queue_declare(queue='parsing.tasks', durable=True)
        # self.channel.queue_declare(queue='parsing.saves', durable=True)
        self.channel.exchange_declare(exchange='parsing', exchange_type='fanout', durable=True)
        self.channel.queue_bind(exchange='parsing', queue='parsing.tasks')
        # self.channel.queue_bind(exchange='parsing', queue='parsing.saves')
        logger.debug('Точка обмена и очереди созданы.')

    def connect(self):
        self.connection = pika.BlockingConnection(self.params)
        self.channel = self.connection.channel()

    def start_consuming(self):
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.channel.stop_consuming()
        except Exception:
            self.channel.stop_consuming()
            logger.error('Ошибка при вычитки очереди.')
            print(traceback.format_exc())

    def close_connect(self):
        if self.connection:
            self.connection.close()
        else:
            logger.error('Закрытие не прошло, соединения не существует.')

    def read_rabbit(self, channel, method_frame, header_frame, body):
        task = pickle.loads(body)
        if task['nom'] == 'reload':
            self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)
            self.status.status = False
        else:
            task['type'] = 'rabbit'
            self.queuez.put(task)
            self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    def save_rabbit(self, text):
        bod = pickle.dumps(text)
        print(bod)
        if self.connection and self.channel:
            self.channel.basic_publish(exchange='parsing', routing_key='parsing', body=bod)
            logger.debug('Успешная отправка на сохранение.')
        else:
            logger.error('Не успешная отправка сообщения, соединения отустсвует')
