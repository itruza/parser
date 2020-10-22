# -*- coding: utf-8 -*-
from loguru import logger
import socket
import sys
import asyncore

# Название плагина
name = 'Сокетное управление парсером'
names = 'socke'

class Plugins(object):
    """docstring for Plugins."""
    thread = None
    socket = None

    @logger.catch
    def __init__(self, config, plugins, event, status, *args, **kwargs):
        super(Plugins, self).__init__()
        self.event = event
        if config:
            self.config = config
        else:
            logger.error('Не произведена передача конфига')
            return [False, 'не произведена передача конфига']
        if plugins:
            self.plugins = plugins
        else:
            logger.error('Не произведена передача списка плагинов')
            return [False, 'не произведена передача списка плагинов']
        if status:
            self.status = status
        else:
            logger.error('Не произведена передача статуса')
            return [False, 'не произведена передача статуса']

    def run(self):  # Запуск плагина
        self.action_server(action='start')
        while self.event:
            c, addr = self.socket.accept()
            logger.info(f'Зафиксировано соединение с: {addr}')
            while self.event:
                data = c.recv(1024)
                print(data)
                self.decryption_commands(data=data, connect=c)

    def decryption_commands(self, data, connect):
        datastr = data.decode("utf-8")
        if datastr[0] == '/':
            com = datastr[1:]
            if com == 'stop':
                connect.send(b'Executing command')
                connect.close()
                self.stop()
            else:
                logger.error('Неправильная комманда.')
                connect.send(f'Error command')
        else:
            logger.error('Неправильная комманда.')
            connect.send(f'Error command')

    def start_server(self):  # Старт сервера
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('', int(self.config['socket']['port'])))
        self.socket.listen(int(self.config['socket']['maxcount']))

    def stop(self):  # Остановка работы скрипта
        logger.info('Остановка скрипта.')
        self.status.command = 'exit'
        self.status.status = False

    def stop_server(self):
        pass

    def send(self, data):  # Отправка сообщения
        pass

    def security(self):  # Проверка соединения
        pass

    def action(self):  # Обработка действий
        pass

    def get_status(self):
        data = {}
        for i in self.plugins:
            data[i] = self.plugins.thread.is_alive()
        self.send(data)


if __name__ == '__main__':
    config = {}
    config['socket'] = {}
    config['socket']['port'] = 8080
    config['socket']['maxcount'] = 5
    a = Plugins(config=config, plugins={'test': 0}, event=True, status={'test': 0})
    a.run()
