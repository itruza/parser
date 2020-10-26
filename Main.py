# -*- coding: utf-8 -*-
from loguru import logger
import importlib
import os
import argparse
import cmd
import sys
import configparser


config = configparser.ConfigParser()


def start_script():
    mainlib = importlib.import_module(name)
    while True:
        command = mainlib.main()
        if command == 'exit':
            break
        logger.info('Перезапуск скрипта...')
        mainlib = importlib.reload(mainlib)


@logger.catch
def loadconfig():
    global config
    platform = sys.platform
    if platform == 'linux' or platform == 'linux2':
        config.read('settings/lin.ini')
    else:
        config.read('settings/win.ini')


class Cli(cmd.Cmd):

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = "Parser> "
        self.intro  = "Добро пожаловать\nДля справки наберите 'help'"
        self.doc_header ="Доступные команды (для справки по конкретной команде наберите 'help _команда_')"


    def do_hello(self, args):
        """hello - выводит 'hello world' на экран"""
        print("hello world")

    def do_check(self, args):
        """Проверка доступности системы SKIOG"""
        print('Successfully!')

    def do_install(self, args):
        """Выполнение установки скрипта и первоначальной настройки"""
        print(args)
        print('Install!')

    def do_run(self, args):
        """Запуск парсера"""
        start_script()

    def do_view(self, args):
        """Просмотр параметров конфига """
        global config
        if not args:
            for i in config:
                print(i)
                for j in config[i]:
                    print(f'---{j} = {config[i][j]}')
        else:
            pass
        print('Чтобы изменить небходимо ввести данную команду с аргументом')

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
    loadconfig()
    if args.s == 0:
        start_script()
    else:
        cli = Cli()
        try:
            cli.cmdloop()
        except KeyboardInterrupt:
            print("\nЗавершение сеанса...")
