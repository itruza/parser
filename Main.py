# -*- coding: utf-8 -*-
from loguru import logger
import importlib
import os
import argparse
import cmd


class Cli(cmd.Cmd):

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = "Parser> "
        self.intro  = "Добро пожаловать\nДля справки наберите 'help'"
        self.doc_header ="Доступные команды (для справки по конкретной команде наберите 'help _команда_')"

    def do_hello(self, args):
        """hello - выводит 'hello world' на экран"""
        print("hello world")

    def do_install(self, args):
        """Выполнение установки скрипта и первоначальной настройки"""
        print('Install!')

    def default(self, line):
        print("Несуществующая команда")


# Настройка логгера
logger.add('logs/browser.log', level='DEBUG', rotation="1 week",
            compression="zip", encoding='UTF-8')

parser = argparse.ArgumentParser(description='Парсер для системы SKIOG')
parser.add_argument("--s", default=0, type=int, help="Запуск командной строки приложения")

if __name__ == '__main__':
    args = parser.parse_args()
    name = 'Parser'
    if args.s == 0:
        mainlib = importlib.import_module(name)
        while True:
            command = mainlib.main()
            if command == 'exit':
                break
            logger.info('Перезапуск скрипта...')
            mainlib = importlib.reload(mainlib)
    else:
        cli = Cli()
        try:
            cli.cmdloop()
        except KeyboardInterrupt:
            print("завершение сеанса...")
