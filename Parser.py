# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from loguru import logger
import threading
import queue
import time
import sys
import configparser
import importlib

# Объявление глобальных перменных
qs = queue.Queue()
qbr = queue.Queue()
config = configparser.ConfigParser()
command = None
plugins = {}  # Пример {'название': [экзеспляр класса, поток]}
driver = ''


# Объявление основопологающих классов
class Status_object(object):
    status = True
    command = None


class Status_app(object):
    status = True
    name = 'Скрипт запущен'


class Plugin_object(object):
    thread = None
    event = None
    error = None
    module = None
    function = None

    def __init__(self, name, path):
        self.name = name
        self.path_module = path
        self.import_plugin()
        self.event = threading.Event()
        self.function = self.module.Plugins

    @logger.catch
    def import_plugin(self):
        self.module = importlib.import_module(self.path_module)

    def stop_thread(self):
        if self.event:
            self.event.set()
        else:
            logger.critical(f'События не запущены. Плагин {self.name}')


status = Status_object()
status_app = Status_app()


@logger.catch
def loadconfig():
    global config
    platform = sys.platform
    if platform == 'linux' or platform == 'linux2':
        config.read('settings/lin.ini')
    else:
        config.read('settings/win.ini')
    return [True, 'OK']


@logger.catch
def startBrowser():
    global driver
    opts = Options()
    opts.add_argument('--disable-web-security')
    if not 'browser' in config:
        logger.critical('В настройках нет значения для браузера')
        return [False, 'В настройках нет значения для браузера']
    if config['browser']['visible'] != 1:
        opts.add_argument('headless')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    if config['browser']['type'] == 'chrome':
        driver = webdriver.Chrome(config['browser']['driver'], options=opts)
    else:
        driver = webdriver.Firefox(config['browser']['driver'], options=opts)
    return [True, 'OK']


@logger.catch
def loginBrowser():
    global config
    global driver
    driver.get(config['browser']['url'])
    time.sleep(2)
    driver.find_element_by_name('j_username').send_keys(config['browser']['username'])
    driver.find_element_by_name('j_password').send_keys(config['browser']['password'])
    driver.find_element_by_xpath('/html/body/div/div[2]/div/form/div/div[5]').click()
    time.sleep(10)
    return [True, 'OK']



@logger.catch
def inic_plugins(plugin=None):
    global driver
    global config
    global qs
    global qbr
    global status_app
    global plugins
    global status
    deb = config['script']['debug']
    if plugin:
        logger.debug(f'Инициализация плагина "{plugin}"')
        if plugins[plugin].error:
            logger.critical('Повторная инициализация плагина. Завершение работы скрипта')
            exit()
        else:
            plug = Plugin_object(name=plugin, path=config['plugins'][plugin])
            plug.function = plug.module.Plugins(driver=driver, queuez=qbr, queueotv=qs,
                        config=config, status=status, event=plug.event)
            plug.error = True
            plugins[plugin] = plug
            plugins[plugin].thread = threading.Thread(target=plug.function.run, daemon=True)
            plugins[plugin].thread.start()
            if deb == '1':
                logger.debug(f'Плагин "{plug.name}" запущен.')
    else:
        logger.debug('Инициализация плагинов')
        if len(plugins) == 0:
            if len(config['plugins']) == 0:
                logger.error('Плагины не обнаружены (дополните конфиг)')
            else:
                for i in config['plugins']:
                    plug = Plugin_object(name=i, path=config['plugins'][i])
                    plug.function = plug.module.Plugins(driver=driver, queuez=qbr, queueotv=qs,
                                config=config, status=status, event=plug.event)
                    plugins[i] = plug
                    plugins[i].thread = threading.Thread(target=plug.function.run, daemon=True)
                    plugins[i].thread.start()
                    if deb == '1':
                        logger.debug(f'Плагин "{plug.name}" запущен.')
        else:
            logger.error('Плагины уже запущены')


def life_plugins():
    while True:
        for i in plugins:
            if not plugins[i].thread.is_alive():
                logger.error(f'Плагин "{i}" аварийно остановился, перезапуск')
                inic_plugins(plugin=i)
        time.sleep(60)


def console_input():
    global config
    global status
    while status.status:
        if config['script']['console'] == '1':
            a = input('Введите номер действия: ')
            if a == 'exit':
                status.command = 'exit'
                break
            b = input('Введите аргументы: ')
            if b == 'exit':
                status.command = 'exit'
                break
            task = {'type': 'console', 'nom': a, 'args': b}
            qbr.put(task)
        else:
            a = input('Введите действие (!e - выход, !r - рестарт): ')
            if a == '!e':
                status.command = 'exit'
                break
            elif a == '!r':
                status.command = 'restart'
                break
            else:
                logger.error('Такой команды не существует.')


def main():
    global driver
    global config
    global qs
    global qbr
    global status_app
    global plugins
    global status
    status.status = True
    logger.debug('Запуск скрипта')

    temp = loadconfig()
    status_app.status = temp[0]
    status_app.name = temp[1]
    deb = config['script']['debug']
    if deb == '1':
        logger.debug('Конфиг загружен')
        logger.debug('Инициализация окна браузера')
    temp = startBrowser()
    status_app.status = temp[0]
    status_app.name = temp[1]
    if deb == '1':
        logger.debug('Вход в систему')
    temp = loginBrowser()
    status_app.status = temp[0]
    status_app.name = temp[1]
    if deb == '1':
        logger.debug('Поиск плагинов')
    inic_plugins()
    logger.debug('Запуск подсистемы проверки работоспособности плагинов')
    lp = threading.Thread(target=life_plugins, daemon=True)
    lp.start()
    while status.status:
        time.sleep(2)
    if deb == '1':
        logger.debug('Завершение работы скрипта')
    for i in plugins:
        if deb == '1':
            logger.debug(f'Отключение плагина "{plugins[i].name}"')
        plugins[i].stop_thread()
    time.sleep(1)
    # driver.close()
    driver.quit()
    return status.command


if __name__ == '__main__':
    while True:
        try:
            main()
        except KeyboardInterrupt:
            break
