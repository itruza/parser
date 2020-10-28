# -*- coding: utf-8 -*-
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import xml.etree.ElementTree as xml
import time
from loguru import logger
from tqdm import tqdm

# Название плагина
name = 'Обработчик задач парсера'
names = 'browser'


class Plugins(object):
    """docstring for Plugins."""

    def __init__(self, driver, queuez, queueotv, config, event, *args, **kwargs):
        super(Plugins, self).__init__()
        self.event = event
        self.actionlist = {
            '1': self.action_1,
            '2': self.action_2,
            '3': self.action_3,
            '4': self.action_4,
        }
        if driver:
            self.driver = driver
        else:
            logger.error('Не произведена передача драйвера')
            return [False, 'не произведена передача драйвера']
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
        self.tablelist = {
            'nomdobr': 0,
            'temat': 4,
            'podcat': 5,
            'text': 3,
            'adres': 2,
            'datecre': 8,
            'dateotv': 10,
            'status': 12,
        }
        self.clear_filter()

    def run(self):
        while self.event:
            action = self.queuez.get()
            self.run_action(data=action)
            self.queuez.task_done()

    def run_action(self, data):
        self.clear_filter(load=False)
        if data['nom'] in self.actionlist:
            action = self.actionlist[data['nom']](args=data['args'])
            if not action:
                logger.error(f'Действие №{data["nom"]} выполнено не правильно')
        else:
            logger.error(f'Не правильный номер действия: {data["nom"]}')

    def start_page(self):
        url = self.config['browser']['url']
        self.driver.get(url)
        time.sleep(7)
        self.clear_filter()

    def next_page(self):
        ele = self.driver.find_element_by_class_name('jtable-busy-message')
        while ele.is_displayed():
            time.sleep(3)
        ele = self.driver.find_element_by_class_name('jtable-busy-panel-background')
        while ele.is_displayed():
            time.sleep(3)
        ele = self.driver.find_element_by_class_name('jtable-page-number-next')
        if ele.get_attribute('class') == 'jtable-page-number-next jtable-page-number-disabled':
            return True
        else:
            ele.click()
            return False

    def clear_filter(self, load=True):
        self.driver.find_element_by_tag_name('body').send_keys(Keys.CONTROL + Keys.HOME)
        self.driver.find_element_by_id('datefrom').clear()
        self.driver.find_element_by_id('dateto').clear()
        self.driver.find_element_by_id('deadlineFrom').clear()
        self.driver.find_element_by_id('deadlineTo').clear()
        self.driver.find_element_by_id('id').clear()
        self.driver.find_element_by_xpath('/html/body/div[2]/div[3]/div/div[1]/form/div[5]/div').click()
        ele = self.driver.find_element_by_xpath('/html/body/div[2]/div[3]/div/div[1]/form/div[5]/div/div/p[1]')
        if ele.get_attribute('class') == 'select-all selected':
            ele.click()
        else:
            ele.click()
            ele.click()
        self.driver.find_element_by_id('id').click()
        if load:
            self.driver.find_element_by_id('LoadRecordsButton').click()
            a = Select(self.driver.find_element_by_xpath('/html/body/div[2]/div[3]/div/div[2]/div/div[4]/div[1]/span[3]/select'))
            a.select_by_value('25')
            time.sleep(5)

    def save_obr(self, date, type='table'):  # date - словарь с данными обращений, type - либо table либо card
        data = {'type': type, 'data': date}
        if type == 'table' or type == 'card':
            self.queueotv.put(data)
        else:
            logger.error('Неправильный тип сохранения')

    def pars_table(self):
        ele = self.driver.find_element_by_class_name('jtable-busy-message')
        while ele.is_displayed():
            time.sleep(3)
        ele = self.driver.find_element_by_class_name('jtable-busy-panel-background')
        while ele.is_displayed():
            time.sleep(3)
        bs = BeautifulSoup(self.driver.page_source, 'lxml')
        bs.find()
        table = bs.find_all('tr', class_='jtable-data-row')
        if len(table) > 0:
            all = []
            for i in table:
                temp = i.find_all('td')
                temp2 = []
                iter = 0
                for j in temp:
                    if iter == 3:
                        temp2.append(j.find('a').attrs['data-hint'])
                    else:
                        temp2.append(j.text)
                    iter += 1
                date = temp2[self.tablelist['datecre']].split('.')
                date2 = temp2[self.tablelist['dateotv']].split('.')
                data = {}
                data['nomdobr'] = temp2[self.tablelist['nomdobr']]
                data['temat'] = temp2[self.tablelist['temat']]
                data['podcat'] = temp2[self.tablelist['podcat']]
                data['text'] = temp2[self.tablelist['text']]
                data['adres'] = temp2[self.tablelist['adres']]
                data['datecre'] = f'{date[2]}-{date[1]}-{date[0]}'
                data['dateotv'] = f'{date2[2]}-{date2[1]}-{date2[0]}'
                data['status'] = temp2[self.tablelist['status']]
                all.append(data)
            self.save_obr(all)
            return True
        else:
            return False

    def pars_card(self, nom):
        source = self.driver.page_source
        bs = BeautifulSoup(source, 'lxml')
        prov = bs.find('div', class_='left')
        if len(prov) > 0:
            proverka = prov.text
            if len(proverka.split('№')) == 2:
                if nom == proverka.split('№')[1]:
                    data = {'nomdobr': nom, 'fio': None, 'email': None, 'tel': None}
                    data['fio'] = bs.find('div', class_='t-user-name').text
                    dop = bs.find_all('div', class_='t-user-email')
                    dops = []
                    for j in dop:
                        temp = j.text
                        if temp != '':
                            dops.append(temp)
                    if len(dops) != 0:
                        if len(dops) > 1:
                            data['email'] = dops[0]
                            data['tel'] = dops[1].split(':')[1].replace(' ', '')
                        else:
                            if dops[0].find('@') != -1:
                                data['email'] = dops[0]
                            else:
                                data['tel'] = dops[0].split(':')[1].replace(' ', '')
                    else:
                        data['email'] = None
                        data['tel'] = None
                    self.save_obr(date=data, type='card')
                else:
                    logger.error(f'Не совпадение обращения {nom}.')
            else:
                logger.error('Не найдено id.')
        else:
            logger.error(f'Обращение {nom} на сайте не найдено.')

    def action_1(self, args=None):  # Парсинг определенного обращения
        if args:
            if isinstance(args, list):
                kol = len(args)
                logger.debug(f'Запуск задачи №1 количество обращений - {kol}')
                j = 1
                for i in tqdm(args, ascii=True, desc='Action №1'):
                    #logger.info(f'Обращение {j}/{kol}')
                    self.driver.find_element_by_id('id').send_keys(i['nomdobr'])
                    self.driver.find_element_by_id('LoadRecordsButton').click()
                    status = self.pars_table()
                    j += 1
                    if not status:
                        self.save_obr(date=[{'nomdobr': i['nomdobr'], 'parsing': False}])
                        return True
                    self.driver.find_element_by_id('id').clear()
                logger.info('Задача №1 выполнена.')
                return True
            else:
                self.driver.find_element_by_id('id').send_keys(args)
                self.driver.find_element_by_id('LoadRecordsButton').click()
                status = self.pars_table()
                if not status:
                    self.save_obr(date=[{'nomdobr': args, 'parsing': False}])
                    return True
                return True
        else:
            logger.error('Не правильные аргументы в действии.')
            return None

    def action_2(self, args=None):  # Парсинг фильтрацией по полям "Срок решения"
        if args:
            if ',' in args:
                times = args.split(',')
                self.driver.find_element_by_id('deadlineFrom').send_keys(times[0])
                self.driver.find_element_by_id('deadlineTo').send_keys(times[1])
            else:
                times = args
                self.driver.find_element_by_id('deadlineFrom').send_keys(times)
        else:
            times = args
        self.driver.find_element_by_id('LoadRecordsButton').click()
        while True:
            status = self.pars_table()
            if status:
                next = self.next_page()
                if next:
                    logger.debug('Страницы закончились, задание заверщается.')
                    break
            else:
                logger.debug('Не найдено обращений, заверщение действия.')
        logger.info('Задача №2 выполнена.')
        return True

    def action_3(self, args=None):  # Парсинг фильтрацией по полям "Дата создания"
        if args:
            if ',' in args:
                times = args.split(',')
                self.driver.find_element_by_id('datefrom').send_keys(times[0])
                self.driver.find_element_by_id('dateto').send_keys(times[1])
            else:
                times = args
                self.driver.find_element_by_id('datefrom').send_keys(times)
        else:
            times = args
        self.driver.find_element_by_id('LoadRecordsButton').click()
        while True:
            status = self.pars_table()
            if status:
                next = self.next_page()
                if next:
                    logger.debug('Страницы закончились, задание заверщается.')
                    break
            else:
                logger.debug('Не найдено обращений, заверщение действия.')
        logger.info('Задача №3 выполнена.')
        return True

    def action_4(self, args=None):  # Парсинг авторов в карточках
        if args:
            if isinstance(args, list):
                kol = len(args)
                logger.debug(f'Запуск задачи №4 количество обращений - {kol}')
                url = self.config['browser']['urlcard']
                j = 1
                for i in tqdm(args, ascii=True, desc='Action №4'):
                    logger.info(f'Обращение {j}/{kol}')
                    self.driver.get(f'{url}{i["nomdobr"]}')
                    time.sleep(2)
                    self.pars_card(nom=i["nomdobr"])
                    time.sleep(2)
                    j += 1
                self.start_page()
                logger.info('Задача №4 выполнена.')
                return True
            else:
                url = self.config['browser']['urlcard']
                nom = args
                self.driver.get(f'{url}{nom}')
                time.sleep(2)
                self.pars_card(nom=nom)
                time.sleep(2)
                self.start_page()
                return True
        else:
            logger.error('Не правильные аргументы в действии.')
            return None
