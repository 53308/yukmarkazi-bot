#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
railway_deploy.py – улучшенный файл
- инлайн-кнопки админу при неопознанном маршруте
- кнопка «👤 Aloqaga_chiqish» с @username или без
- нормализация: İ→i, ʼ→', регистр не важен
- все районные центры и крупные посёлки (Пишагардан, Чиназ, …)
"""
import os
import sys
import time
import signal
import logging
import threading
import re
import unicodedata
import traceback
from datetime import datetime
from flask import Flask, request, jsonify
import requests

# ========== Настройки ==========
BOT_TOKEN     = os.environ.get('TELEGRAM_BOT_TOKEN')
MAIN_GROUP_ID = int(os.environ.get('MAIN_GROUP_ID', '-1002259378109'))
ADMIN_USER_ID = int(os.environ.get('ADMIN_USER_ID', '8101326669'))
BOT_USERNAME  = os.getenv("BOT_USERNAME", "yukmarkazi_bot")  # без @
API_URL       = f"https://api.telegram.org/bot{BOT_TOKEN}" if BOT_TOKEN else None
# ========== Глобальные переменные ==========
last_update_id = 0
stop_polling = False
bot_status = "АКТИВЕН"
message_count = 0
bot_start_time = datetime.now()
logger = logging.getLogger(__name__)

# ========== Логирование ==========
def init_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        handlers=[
            logging.FileHandler('bot.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

# ========== REGION_KEYWORDS ==========
REGION_KEYWORDS = {
    'toshkent': {
        'topic_id': 101362,
        'keywords': [
            # столица
            'toshkent', 'tashkent', 'toshkent shahri', 'tashkent city',
            'tosh-kent', 'tash-kent', 'toshʼkent', 'tashʼkent',
            'toshkent İ', 'toshkent i', 'TOSHKENT', 'TASHKENT',
            'tosh', 'toshkentga', 'тошкент', 'тошкентга', 'тошкендан', 'ташкент', 'ташкентga',
            # районы города
            'yashnobod', 'yashnobod tumani', 'yunusobod', 'yunusobod tumani',
            'mirzo-ulugbek', 'mirzo ulugbek', 'mirzo-ulugbek tumani',
            'olmazor', 'olmazor tumani', 'uchtepa', 'uchtepa tumani',
            'shayxontoxur', 'shayxontohur', 'shayxontoxur tumani',
            'chilonzor', 'chilon-zor', 'chilonzor tumani',
            'sergeli', 'sergeli tumani', 'sergili', 'сергели', 'сергили',
            'yakkasaroy', 'yakkasaray', 'yakkasaroy tumani',
            'mirobod', 'mirabad', 'mirobod tumani', 'bektemir', 'bektemir tumani',
            # области и районы Ташкентской области
            'bekobod', 'bekabad', 'bekobod tumani', 'bekabad tumani',
            'xasanboy', 'hasanboy', 'xasanboydan', 'хасанбой', 'хасанбойдан',
            'olmaliq', 'alma-lyk', 'olmalik', 'olmaliq tumani', 'olmaliq i',
            'ohangaron', 'axangaron', 'ohanʼgaron', 'ohangaron tumani', 'ohangaron i',
            'angren', 'angren İ', 'angiren', 'angren i',
            'chirchiq', 'chirchik', 'chirchik İ', 'chir-chiq', 'chirchiq i',
            'yangiyul', "yangiyo'l", 'yangiyul tumani', 'yangiyul i', "yangiyo'l tumani",
            'parkent', 'parkent tumani', 'piskent', 'piskent tumani', 'bekobod', 'bekabad', 'бекабад', 'бекобод',
            'quyichirchiq', 'quyichirchiq tumani',
            'boʻka', 'boka', 'boʻka tumani', 'boka tumani', 'chinaz', 'chinazdan', 'chinaz tumani', 'chinoz', 'chinozdan', 'чино', 'чиноз', 'чиноздан',
            'zangiota', 'zangiota tumani',
            'qibray', 'qibray tumani',
            'yuqorichirchiq', 'yuqorichirchiq tumani',
            'nurafshon', 'nurafshon tumani',
            'akhangaran', 'axangaran', 'akhangaran tumani',
            'forish', 'forish tumani', 'ustarkhan', 'ustarkhan tumani',
            'gazalkent', 'gazalkent tumani', 'keles', 'keles tumani',
            'tashkent region', 'toshkent viloyati', 'tashkent oblast'
        ]
    },
    'andijon': {
        'topic_id': 101387,
        'keywords': [
            'andijon', 'andijan', 'andijon İ', 'andijonʼ', 'andijon i', "andijon'",
            'андижон', 'андижонга', 'андижондан', 'андижон', 'андижонга',
            'andijonga', 'andijon-ga', 'andijon ga',
            'asaka', 'asaka İ', 'asakaʼ', 'asaka tumani', 'asaka i', "asaka'",
            'marhamat', 'marxamat', 'marhamat tumani', 'marhamat i',
            'shahrixon', 'shahrixon tumani', 'shaxrixon', 'shahrixon i',
            'xoja-obod', 'xojaobod', 'xojaʼobod', "xoja'obod", "xoja'obod",
            'qorgontepa', 'qurghontepa', 'qurgʻontepa', 'qurghontepa i',
            'oltinkol', 'oltinkoʻl', 'oltinkol tumani', 'oltinkol i'
        ]
    },
    'fargona': {
        'topic_id': 101382,
        'keywords': [
            "farg'ona", "fargʻona", 'fargona', 'fergana', 'farg-on-a',
            'fargona İ', 'fargona i', "farg'ona İ", "fargʻona İ",
            'qoqon', 'kokand', 'quqon', 'qoʼqon', 'qoqon İ', 'qoqon i',
            'коканд', 'кокандga', 'кокандdan',
            'margilon', 'margilan', 'margilon İ', 'margilon i',
            'quvasoy', 'kuvasay', 'quvasoy İ', 'quvasoy i', 'quvasoyʼ', 'quvasoy', 'kuvasay', 'кувасай', 'кувасой', 'quvasoydan', 'кувасойдан',
            'beshariq', 'besharik', 'beshariq İ', 'beshariq i',
            "bog'dod", 'bogdod', "bogʻdod", "bog'dod İ", "bog'dod i",
            "bog'doddan", 'bogdoddan', 'богдод', 'богдодdan',
            'oltiarik', 'oltiarik İ', 'oltiarik i',
            'rishton', 'rishtan', 'rishton İ', 'rishton i',
            'sox', 'sox tumani', 'sox İ', 'sox i'
        ]
    },
    'namangan': {
        'topic_id': 101383,
        'keywords': [
            'namangan', 'namangan İ', 'namanganʼ', 'namangan i', "namangan'",
            'наманган', 'наманганга', 'намангандан', 'наманган',
            'chortoq', 'chartak', 'chortoq İ', 'chortoq i', 'chortoqʼ',
            'yangiqorgon', 'yangikurgan', 'yangi-qorğon', 'yangikurgan i',
            'chust', 'chust tumani', 'chust İ', 'chust i', 'chustʼ', "chust'",
            'чуст', 'чустга', 'чустdан',
            'kosonsoy', 'kosonsoy tumani', 'kosonsoy İ', 'kosonsoy i',
            'mullomirsoy', 'mullomirʼsoy', "mullomir'soy",
            'uchqorgon', 'uch-qorğon', 'uchqoʻrgʻon', 'uchqorgon i',
            'pop', 'pop tumani', 'pop İ', 'pop i'
        ]
    },
    'buxoro': {
        'topic_id': 101372,
        'keywords': [
            'buxoro', 'bukhara', 'buxara', 'buxoro İ', 'buxoroʼ', 'buxoro i', "buxoro'",
            'бухоро', 'бухорога', 'бухородан', 'бухара',
            'alat', 'alat tumani', 'alat İ', 'alat i',
            "g'ijduvon", 'gijduvon', "gʻijduvon", "g'ijduvon İ", "g'ijduvon i",
            'kogon', 'kogon tumani', 'kogon İ', 'kogon i',
            'romitan', 'romitan tumani', 'romitan İ', 'romitan i',
            'shofirkon', 'shofirkon İ', 'shofirkon tumani', 'shofirkon i',
            'qorakoʻl', 'qorakol', 'qorakol İ', 'qorakol i'
        ]
    },
    'samarqand': {
        'topic_id': 101369,
        'keywords': [
            'samarqand', 'samarkand', 'samarqand İ', 'samarqandʼ', 'samarqand i', "samarqand'",
            'самарканд', 'самаркандga', 'самаркандdan',
            'urgut', 'urgut tumani', 'urgut İ', 'urgut i',
            'kattaqorgon', 'kattakurgan', 'katta-qorğon', 'kattaqoʻrgʻon', 'kattaqorgon i',
            "kattaqo'rg'on", "kattaqo'rg'ondan", 'каттакурган',
            'payariq', 'payariq tumani', 'payarik', 'payariq i',
            'ishtixon', 'ishtixon tumani', 'ishtixon İ', 'ishtixon i',
            'jomboy', 'jomboy tumani', 'jomboy İ', 'jomboy i',
            'nurabod', 'nurabod tumani', 'nurabod i'
        ]
    },
    'qashqadaryo': {
        'topic_id': 101380,
        'keywords': [
            'qarshi', 'karshi', 'qarshi İ', 'qarshiʼ', 'qarshi i', "qarshi'",
            'qashqadaryo', 'кашкадарё', 'кашкадарёdан', 'кашкадарьё',
            'shahrisabz', 'shahrisabz İ', 'shakhrisabz', 'shahri-sabz', 'shahrisabz i',
            'koson', 'koson tumani', 'koson İ', 'koson i',
            'guzar', 'guzar tumani', 'guzar İ', 'guzar i',
            'muborak', 'muborak tumani', 'muborak İ', 'muborak i',
            'chiroqchi', 'chiroqchi tumani', 'chiroqchi İ', 'chiroqchi i',
            'yakkabog', 'yakkabogʻ', 'yakkabog İ', 'yakkabog i'
        ]
    },
    'surxondaryo': {
        'topic_id': 101363,
        'keywords': [
            'termiz', 'termez', 'termiz İ', 'termizʼ', 'termiz i', "termiz'",
            'denov', 'denau', 'denov İ', 'denovʼ', 'denov i', "denov'",
            'boysun', 'boysun tumani', 'boysun İ', 'boysun i', 'surxondaryo', 'сурхондарё', 'сурхондарёга', 'сурхондарье',
            'sherobod', 'sherobod tumani', 'sherobod İ', 'sherobod i',
            'qumqorgon', 'qumqorğon', 'qumqoʻrgʻon', 'qumqorgon i',
            'uzun', 'uzun tumani', 'uzun i'
        ]
    },
    'navoiy': {
        'topic_id': 101379,
        'keywords': [
            'navoiy', 'navoi', 'navoiy İ', 'navoi İ', 'navoiy i', 'navoi i',
            'навоий', 'навоийга', 'навоийдан', 'навои',
            'zarafshon', 'zarafshan', 'zarafshon İ', 'zarafshon i',
            'karmana', 'karmana tumani', 'karmana İ', 'karmana i',
            'nurota', 'nurota tumani', 'nurota İ', 'nurota i',
            'konimex', 'konimex tumani', 'konimex İ', 'konimex i',
            'uchquduq', 'uchquduk', 'uch-quduq', 'uchquduq i'
        ]
    },
    'sirdaryo': {
        'topic_id': 101378,
        'keywords': [
            'guliston', 'gulistan', 'guliston İ', 'gulistonʼ', 'guliston i', "guliston'",
            'shirin', 'shirin tumani', 'shirin İ', 'shirin i',
            'boyovut', 'bayaut', 'boyovut tumani', 'boyovut İ', 'boyovut i',
            'sirdaryo', 'sirdaryo İ', 'sirdaryoʼ', 'sirdaryo i', "sirdaryo'",
            'сирдарё', 'сирдарёга', 'сирдарёдан', 'сырдарья',
            'mirzaobod', 'mirzaobod tumani', 'mirzaobod i'
        ]
    },
    'jizzax': {
        'topic_id': 101377,
        'keywords': [
            'jizzax', 'jizzax İ', 'jizzax i', 'jizzakh', 'jiz-zax', 'жиззах', 'джизак',
            'gallaaral', 'gallaaral İ', 'gallaaral i', 'galla-aral', 'gallaaʼral', "galla'aral",
            'pakhtakor', 'pakhtakor İ', 'pakhtakor i', 'pakhtakor tumani',
            'zomin', 'zomin tumani', 'zomin İ', 'zomin i',
            'pishagar', 'pishagaron', 'pishagardan', 'pishagar İ', 'pishagar i', "pishagar'",
            'forish', 'forish tumani', 'forish İ', 'forish i',
            'arnasoy', 'arnasoy tumani', 'arnasoy İ', 'arnasoy i',
            'baxmal', 'baxmal tumani', 'baxmal i',
            'pishagardan', 'пишагардан', 'pishagardan i', 'pishagardan İ'
        ]
    },
    'xorazm': {
        'topic_id': 101660,
        'keywords': [
            'xorazm', 'xorezm', 'xorazm İ', 'xorezm İ', 'xorazm i', 'xorezm i',
            'хоразм', 'хоразмга', 'хоразмдан', 'хорезм',
            'xiva', 'khiva', 'xiva İ', 'xivaʼ', 'xiva i', "xiva'",
            # урганч удален - теперь отдельный регион
            'shovot', 'shavat', 'shovot İ', 'shovot i', "shovot'", 'shovotʼ',
            'yangiariq', 'yangiariq tumani', 'yangiariq İ', 'yangiariq i',
            'bogʻot', 'bogot', 'bogʻot tumani', 'bogʻot İ', 'bogʻot i',
            'xazarasp', 'hazarasp', 'xazarasp tumani', 'xazarasp i',
            'gurlan', 'gurlan tumani', 'gurlan İ', 'gurlan i',
            'qoshkopir', 'koshkupir', 'qoshkopir tumani', 'qoshkopir i',
            'tuproqqala', 'tuprak kala', 'tuproqqala tumani', 'tuproqqala i',
            'pitnak', 'pitnak shaharcha', 'pitnak posyolok',
            'khanka', 'xanka', 'khanka shaharcha',
            'dashoguz', 'dashoguz yuli', 'urganch-dashoguz'
        ]
    },
    'urganch': {
        'topic_id': 101375,
        'keywords': [
            'urganch', 'urgench', 'urganch İ', 'urganchʼ', 'urganch i', "urganch'",
            'ургенч', 'urgench İ', 'urgench i', 'urganchga', 'ургенчга',
            'urgenchdan', 'urganchdan', 'ургенчдан', 'urgench city', 'urganch shahar'
        ]
    },
    'nukus': {
        'topic_id': 101376,
        'keywords': [
            'nukus', 'nukus İ', 'nukusʼ', 'nukus i', "nukus'", 'noʻkis', 'nokis',
            'kegeyli', 'kegeyli tumani', 'kegeyli İ', 'kegeyli i',
            'muynoq', 'muynaq', 'muynoq İ', 'muynoq i',
            'takhiatash', 'takhiatash tumani', 'takhiatash İ', 'takhiatash i'
        ]
    },
    'qoraqalpoq': {
        'topic_id': 101381,
        'keywords': [
            'qoraqalpoq', 'qaraqalpaqstan', 'qoraqalpoq İ', 'qaraqalpaq-stan', 'qoraqalpoq i',
            'qorakalpoq', 'karakalpakstan', 'qorakalpoq İ', 'qorakalpoq i',
            'turtkul', 'turtkul İ', 'turtkulʼ', 'turtkul tumani', 'turtkul i', "turtkul'",
            'khojeli', 'xojeli', 'hodjeyli', 'xojeli İ', 'xojeli i', 'khojeliʼ', "xojeli'",
            'amudarya', 'amudaryo', 'amudarya tumani', 'amudarya İ', 'amudarya i',
            'chimboy', 'chimboy tumani', 'chimboy İ', 'chimboy i'
        ]
    },
    'fura_bozor': {
        'topic_id': 101361,
        'keywords': [
            'fura bazar', 'fura bozor', 'fura bozori', 'фура бозор', 'bozor fura'
        ]
    },
    'reklama': {
        'topic_id': 101360,
        'keywords': [
            'reklama', 'reklama post', 'реклама', 'reklama berish', 'reklama joylashtirish'
        ]
    },
    'yangiliklar': {
        'topic_id': 101359,
        'keywords': [
            'yangilik', 'yangiliklar', 'новости', 'news', 'xabar', "so'ngi yangiliklar"
        ]
    },
    'xalqaro': {
        'topic_id': 101367,
        'keywords': [
            # Россия
            'russia', 'rosiya', 'russia İ', 'rosiya İ', 'russia i', 'rosiya i',
            'moskva', 'moscow', 'moskva İ', 'moskvaʼ', 'moskva i', "moskva'",
            'москва', 'московская', 'москва обл', 'московская область',
            'spb', 'sankt-peterburg', 'piter', 'saint-petersburg', 'spb İ', 'spb i',
            'спб', 'санкт-петербург', 'питер', 'ленинград',
            'krasnodar', 'krasnodar İ', 'krasnodar i', 'voronej', 'воронеж', 'qazoq', 'казахстан', 'irkutsk', 'иркутск',
            'rostov', 'rostov-na-donu', 'rostov İ', 'rostov i',
            'volgograd', 'volgograd İ', 'volgograd i',
            'kazan', 'kazan İ', 'kazan i',
            'nizhny novgorod', 'nizhniy novgorod', 'nizhny novgorod İ', 'nizhny i',
            'samara', 'samara İ', 'samara i',
            'ufa', 'ufa İ', 'ufa i',
            'perm', 'perm İ', 'perm i',
            'krasnoyarsk', 'krasnoyarsk İ', 'krasnoyarsk i',
            'novosibirsk', 'novosibirsk İ', 'novosibirsk i',
            'барнаул', 'barnaul', 'barnaulskaya',
            'yekaterinburg', 'ekaterinburg', 'yekaterinburg İ', 'yekaterinburg i',
            'chelyabinsk', 'chelyabinsk İ', 'chelyabinsk i',
            'omsk', 'omsk İ', 'omsk i',
            'voronezh', 'voronezh İ', 'voronezh i',
            'sochi', 'sochi İ', 'sochi i',
            'tolyatti', 'tolyatti İ', 'tolyatti i',
            'belgorod', 'belgorod İ', 'belgorod i',
            'tula', 'tula İ', 'tula i',
            'yaroslavl', 'yaroslavl İ', 'yaroslavl i',
            'tver', 'tver İ', 'tver i',
            'ivanovo', 'ivanovo İ', 'ivanovo i',
            'vladivostok', 'vladivostok İ', 'vladivostok i',
            'irkutsk', 'irkutsk İ', 'irkutsk i',
            'khabarovsk', 'khabarovsk İ', 'khabarovsk i',

            # Украина
            'ukraine', 'ukraina', 'ukraine İ', 'ukraina İ', 'ukraine i', 'ukraina i',
            'kiev', 'kyiv', 'kiev İ', 'kyiv İ', 'kiev i', 'kyiv i',
            'kharkiv', 'kharkov', 'kharkiv İ', 'kharkiv i',
            'odessa', 'odesa', 'odessa İ', 'odessa i',
            'dnipro', 'dnepr', 'dnipro İ', 'dnipro i',
            'lviv', 'lviv İ', 'lviv i',

            # Беларусь
            'belarus', 'belarus İ', 'belarus i',
            'minsk', 'minsk İ', 'minsk i',
            'brest', 'brest İ', 'brest i',
            'grodno', 'grodno İ', 'grodno i',
            'gomel', 'gomel İ', 'gomel i',

            # Казахстан
            'kazakhstan', 'qazaqstan', 'kazakhstan İ', 'qazaq-stan', 'kazakhstan i',
            'almaty', 'alma-ata', 'almaty İ', 'almaty i',
            'astana', 'nur-sultan', 'astana İ', 'astana i',
            'shymkent', 'shymkent İ', 'shymkent i',
            'karaganda', 'karaganda İ', 'karaganda i',
            'aktobe', 'aktobe İ', 'aktobe i',
            'pavlodar', 'pavlodar İ', 'pavlodar i',

            # Кыргызстан
            'kyrgyzstan', 'kirgiziya', 'kyrgyzstan İ', 'kyrgyzstan i',
            'bishkek', 'bishkek İ', 'bishkek i',
            'osh', 'osh İ', 'osh i',

            # Таджикистан
            'tajikistan', 'tojikiston', 'tajikistan İ', 'tajikistan i',
            'dushanbe', 'dushanbe İ', 'dushanbe i',
            'khujand', 'khujand İ', 'khujand i',

            # Туркменистан
            'turkmenistan', 'turkmenistan İ', 'turkmenistan i',
            'ashgabat', 'ashgabat İ', 'ashgabat i',
            'turkmenbashy', 'turkmenbashy İ', 'turkmenbashy i',

            # Турция
            'turkey', 'turkiya', 'turkey İ', 'turkiya İ', 'turkey i', 'turkiya i',
            'istanbul', 'stambul', 'istanbul İ', 'stambul İ', 'istanbul i', 'stambul i',
            'ankara', 'ankara İ', 'ankara i',
            'izmir', 'izmir İ', 'izmir i',
            'antalya', 'antalya İ', 'antalya i',

            # Другие страны
            'iran', 'iran İ', 'iran i',
            'afganistan', 'afghanistan', 'afghanistan İ', 'afghanistan i',
            'china', 'xitoy', 'china İ', 'xitoy İ', 'china i', 'xitoy i',
            'india', 'xindiston', 'india İ', 'xindiston İ', 'india i', 'xindiston i',
            'poland', 'polsha', 'poland İ', 'polsha İ', 'poland i', 'polsha i',
            'germany', 'germaniya', 'germany İ', 'germaniya İ', 'germany i', 'germaniya i',
            'europe', 'europa', 'europe İ', 'europa İ', 'europe i', 'europa i',

            # Общие ключевые слова для международных маршрутов
            'international', 'xalqaro', 'international İ', 'xalqaro İ', 'international i', 'xalqaro i',
            'cis', 'mda', 'cis İ', 'mda İ', 'cis i', 'mda i',
            'import', 'export', 'import İ', 'export İ', 'import i', 'export i'
        ]
    }
}

# ========== Рядом с REGION_KEYWORDS нужно добавить константы для номеров телефонов и маршрутов ==========

PHONE_REGEX = re.compile(r'[\+]?[\d\s\-\(\)]{9,18}')
ROUTE_REGEX = re.compile(r'(?:^\s*)?(.+?)(?:\s*>\s*|\s*—\s*|\s*-\s*|\s+)(.+?)(?:\s|$)', re.IGNORECASE | re.MULTILINE)

# ========== Функции нормализации ==========

def normalize_text(text):
    """
    Нормализация текста для поиска ключевых слов
    - приводит к нижнему регистру
    - убирает эмодзи
    - заменяет İ→i, ʼ→', ё→e
    """
    if not text:
        return ""
    
    # Убираем эмодзи
    text = re.sub(r'[🇺🇿🇰🇿🇮🇷🚚📦⚖️💵\U0001F1FA-\U0001F1FF\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', '', text)
    
    # Нормализация Unicode (для корректного сравнения)
    text = unicodedata.normalize('NFD', text)
    
    # Приведение к нижнему регистру
    text = text.lower()
    
    # Замены специальных символов
    replacements = {
        'ʼ': "'",   # правый апостроф → обычный апостроф
        'ʻ': "'",   # левый апостроф → обычный апостроф
        'ё': 'e',   # ё → e
        'і': 'i',   # і → i
        'ı': 'i',   # ı → i (турецкий)
        'İ': 'i',   # İ → i (турецкий)
        'ğ': 'g',   # ğ → g
        'ş': 's',   # ş → s
        'ç': 'c',   # ç → c
        'ü': 'u',   # ü → u
        'ö': 'o',   # ö → o
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text

def extract_phone_number(text):
    """Извлекает номер телефона из текста"""
    match = PHONE_REGEX.search(text)
    return match.group().strip() if match else 'Номер не указан'

def extract_route_and_cargo(text):
    """
    Извлекает откуда/куда и описание груза
    Возвращает (from_city, to_city, cargo_text)
    """
    lines = text.strip().split('\n')
    
    for line in lines:
        # Убираем эмодзи из строки для анализа
        clean_line = re.sub(r'[🇺🇿🇰🇿🇮🇷🚚📦⚖️💵\U0001F1FA-\U0001F1FF\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', '', line)
        
        # Ищем паттерны маршрута в очищенной строке
        route_match = ROUTE_REGEX.search(clean_line)
        if route_match:
            from_city = route_match.group(1).strip()
            to_city = route_match.group(2).strip()
            
            # Убираем маршрут из общего текста, оставляем описание груза
            cargo_text = text.replace(line, '').strip()
            
            return from_city, to_city, cargo_text
        
        # Дополнительные паттерны для форматов с эмодзи и разделителями
        emoji_patterns = [
            r'🇺🇿\s*(\w+)\s*🇺🇿\s*(\w+)',  # 🇺🇿 Qoqon 🇺🇿 Samarqand
            r'🇷🇺\s*([^-]+?)\s*-\s*🇺🇿\s*([^\\n\\r]+)',  # 🇷🇺Москва обл. - 🇺🇿Ташкент
            r'(\w+)\s*🇺🇿\s*(\w+)',         # Qoqon 🇺🇿 Samarqand  
            r'(\w+)\s*[-–→>>>\-\-\-\-]+\s*(\w+)',  # Tosh.Xasanboydan----Fargonaga, >>>
            r'(\w+)\s*>\s*(\w+)',            # Кашкадарёдан>> Чуст
            r'(\w+)\s+(\w+)',                # простой формат через пробел
        ]
        
        for pattern in emoji_patterns:
            match = re.search(pattern, clean_line)
            if match and len(match.group(1)) > 2 and len(match.group(2)) > 2:
                from_city = match.group(1).strip()
                to_city = match.group(2).strip()
                cargo_text = text.replace(line, '').strip()
                return from_city, to_city, cargo_text
    
    # Если не найден четкий маршрут, пытаемся извлечь из первой строки
    first_line = lines[0] if lines else text
    clean_first = re.sub(r'[🇺🇿🇰🇿🇮🇷🚚📦⚖️💵\U0001F1FA-\U0001F1FF\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', '', first_line)
    
    # Дополнительные сложные паттерны
    complex_patterns = [
        r'([А-Яа-я\w\.]+)дан[\s\-\-\-\-]+([А-Яа-я\w]+)га',  # Tosh.Xasanboydan----Fargonaga
        r'([А-Яа-я\w\.]+)дан\s+([А-Яа-я\w]+)\s+([А-Яа-я\w]+)',  # Bog'doddan toshkent sergiliga
        r'([А-Яа-я\w\.]+)дан[\s\n]+([А-Яа-я\w]+)га',  # многострочные формы
        r'([А-Яа-я\w\.]+)дан[\s\n]+([А-Яа-я\w]+)',  # простые многострочные
    ]
    
    for pattern in complex_patterns:
        match = re.search(pattern, clean_first, re.IGNORECASE)
        if match:
            from_city = match.group(1).strip()
            to_city = match.group(2).strip()
            return from_city, to_city, text
    
    parts = re.split(r'[\s\-\>\→\—\-\-\-\-]+', clean_first, 2)
    
    if len(parts) >= 2 and len(parts[0]) > 2 and len(parts[1]) > 2:
        return parts[0].strip(), parts[1].strip(), text
    
    return None, None, text

def format_cargo_text(cargo_text):
    """
    Форматирует описание груза, разделяя на транспорт и описание
    Возвращает (transport, description)
    """
    if not cargo_text:
        return "Груз", "Детали не указаны"
    
    # Список ключевых слов для транспорта
    transport_keywords = [
        'фура', 'fura', 'камаз', 'kamaz', 'газель', 'gazel', 'прицеп', 'pritsep',
        'машина', 'mashina', 'автомобиль', 'avtomobil', 'грузовик', 'gruzovik',
        'рефрижератор', 'refrigerator', 'tent', 'тент', 'открытый', 'ochiq'
    ]
    
    cargo_lines = cargo_text.strip().split('\n')
    transport = "Груз"
    description = "Детали не указаны"
    
    for line in cargo_lines:
        line_lower = line.lower()
        
        # Проверяем, содержит ли строка транспорт
        for keyword in transport_keywords:
            if keyword in line_lower:
                transport = line.strip()
                break
        else:
            # Если в строке нет транспорта, считаем её описанием
            if line.strip() and 'номер' not in line_lower and '+' not in line:
                description = line.strip()
    
    return transport, description

def send_message(chat_id, text, message_thread_id=None, reply_markup=None):
    """Отправка сообщения в Telegram"""
    try:
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML'
        }
        
        if message_thread_id:
            payload['message_thread_id'] = message_thread_id
            
        if reply_markup:
            payload['reply_markup'] = reply_markup
            
        response = requests.post(f"{API_URL}/sendMessage", json=payload, timeout=10)
        return response.json()
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")
        return None

def author_button(user):
    """Создает инлайн-кнопку с информацией об авторе"""
    name = user.get('first_name', 'Пользователь')
    username = user.get('username', '')
    
    if username:
        button_text = f"👤 @{username}"
        url = f"https://t.me/{username}"
    else:
        button_text = f"👤 {name}"
        url = f"tg://user?id={user.get('id', '')}"
    
    return {
        "inline_keyboard": [[{
            "text": button_text,
            "url": url
        }]]
    }

def handle_admin_command(message):
    """Обработка команд администратора"""
    text = message.get('text', '').strip()
    
    if text == '/stats':
        stats_text = f"""📊 Статистика бота:
📈 Обработано сообщений: {message_count}
⏰ Время работы: {datetime.now() - bot_start_time}
🔄 Статус: {bot_status}
🌐 Последнее обновление: {datetime.now().strftime('%H:%M:%S')}"""
        
        send_message(ADMIN_USER_ID, stats_text)

def ask_admin_topic(message, from_city, to_city):
    """Спрашивает админа, в какой топик отправить неопознанное сообщение"""
    text = message.get('text', '')
    user = message.get('from', {})
    user_data = f"{user.get('id')}:{user.get('first_name', '')}:{user.get('username', '')}"
    
    # Экранируем двоеточия для callback_data
    safe_data = f"{text}|||{user_data}".replace(":", "%3A")
    kb = [
        [{"text": k.upper(), "callback_data": f"route:{k}:{safe_data}"}]
        for k in REGION_KEYWORDS
    ]
    kb.append([{"text": "❌ Отмена", "callback_data": "route:cancel"}])
    requests.post(f"{API_URL}/sendMessage", json={
        "chat_id": ADMIN_USER_ID,
        "text": f"⚠️ Неопознанный маршрут:\n{from_city} → {to_city}",
        "reply_markup": {"inline_keyboard": kb}
    }, timeout=10)

def send_telegram_message(chat_id, text):
    """Отправка сообщения через Telegram API"""
    try:
        requests.post(f"{API_URL}/sendMessage", json={
            "chat_id": chat_id,
            "text": text
        }, timeout=10)
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")

def handle_command(message):
    """Обработка команд бота"""
    text = message.get('text', '').strip()
    chat_id = message['chat']['id']
    user_id = message['from']['id']
    
    if text == '/start':
        response = "🤖 YukMarkazi New Bot активен!\n\n📍 Автоматически пересылаю сообщения о грузах в региональные топики.\n\n🔄 Работаю 24/7 в автономном режиме."
        send_telegram_message(chat_id, response)
        
    elif text == '/status':
        if user_id == ADMIN_USER_ID:
            # Детальная статистика для админа
            response = f"🤖 Статус бота:\n✅ Активен и работает\n📊 Обработано сообщений: {message_count}\n🕐 Время: {datetime.now().strftime('%H:%M:%S')}\n🌐 Сервер: Render\n💚 UptimeRobot мониторинг активен"
        else:
            # Простой статус для всех
            response = f"🤖 Бот активен\n🕐 {datetime.now().strftime('%H:%M:%S')}"
        send_telegram_message(chat_id, response)

def process_message(message):
    global last_update_id, message_count
    try:
        text = message.get('text', '')
        chat_id = message['chat']['id']
        user_id = message['from']['id']
        
        # Логирование для диагностики
        logger.info(f"📥 Получено сообщение из чата {chat_id}: {text[:50]}...")
        
        # Обработка команд
        if text.startswith('/'):
            handle_command(message)
            message_count += 1
            return
            
        if chat_id == ADMIN_USER_ID:
            handle_admin_command(message)
            message_count += 1
            return
            
        # Проверка что сообщение из основной группы
        if chat_id != MAIN_GROUP_ID:
            logger.info(f"🚫 Пропуск сообщения: не из основной группы {MAIN_GROUP_ID}")
            return
            
        logger.info(f"🎯 Обрабатываем сообщение из основной группы")
        message_count += 1
        
        from_city, to_city, cargo_text = extract_route_and_cargo(text)
        if not from_city or not to_city:
            return

        def find_region(txt):
            txt_norm = normalize_text(txt)
            words = re.findall(r"\b\w+\b", txt_norm)
            for key, data in REGION_KEYWORDS.items():
                for kw in data['keywords']:
                    kw_norm = normalize_text(kw)
                    if kw_norm in words or (len(kw_norm) > 4 and kw_norm in txt_norm):
                        return key
            return None

        from_reg = find_region(from_city)
        if from_reg is None:
            ask_admin_topic(message, from_city, to_city)
            return

        # Определяем топик по месту ОТПРАВКИ
        topic_key = 'xalqaro' if 'xalqaro' == from_reg else from_reg
        topic_id = REGION_KEYWORDS[topic_key]['topic_id']

        sender = message.get('from', {})
        phone = extract_phone_number(text)
        transport, desc = format_cargo_text(cargo_text)

        msg = f"""{from_city.upper()} - {to_city.upper()}
🚛 {transport}
💬 {desc}
☎️ {phone}
#{to_city.upper()}
➖➖➖➖➖➖➖➖➖➖➖➖➖➖
Другие грузы: @logistika_marka"""

        send_message(MAIN_GROUP_ID, msg, topic_id,
                     reply_markup=author_button(sender))
    except Exception:
        logging.exception("process_message error")

def handle_callback(update):
    try:
        query = update['callback_query']
        data = query['data']
        user_id = query['from']['id']
        if user_id != ADMIN_USER_ID:
            return
        if not data.startswith("route:"):
            return

        parts = data.split(":", 2)
        action = parts[1]
        payload = parts[2].replace("%3A", ":")
        original_text, user_info = payload.split("|||", 1)
        uid, name, username = user_info.split(":", 2)

        if action == "cancel":
            requests.post(f"{API_URL}/answerCallbackQuery", json={
                "callback_query_id": query['id'],
                "text": "❌ Отменено"
            })
            return

        from_city, to_city, cargo_text = extract_route_and_cargo(original_text)
        if not from_city or not to_city:
            requests.post(f"{API_URL}/answerCallbackQuery", json={
                "callback_query_id": query['id'],
                "text": "⚠️ Не удалось распознать маршрут"
            })
            return

        topic_key = action
        topic_id = REGION_KEYWORDS[topic_key]['topic_id']

        phone = extract_phone_number(original_text)
        cargo_clean = re.sub(PHONE_REGEX, '', original_text).strip()
        cargo_clean = re.sub(ROUTE_REGEX, '', cargo_clean).strip()
        transport, desc = format_cargo_text(cargo_clean)

        msg = f"""{from_city.upper()} - {to_city.upper()}
🚛 {transport}
💬 {desc}
☎️ {phone}
#{to_city.upper()}
➖➖➖➖➖➖➖➖➖➖➖➖➖➖
Другие грузы: @logistika_marka"""

        send_message(MAIN_GROUP_ID, msg, topic_id,
                     reply_markup=author_button({
                         "id": uid,
                         "first_name": name,
                         "username": username
                     }))

        requests.post(f"{API_URL}/answerCallbackQuery", json={
            "callback_query_id": query['id'],
            "text": f"✅ Отправлено в топик {topic_key}"
        })
    except Exception:
        logging.exception("callback error")

def get_updates():
    global last_update_id, stop_polling
    if not BOT_TOKEN or stop_polling:
        return []
    
    # АВТОНОМНОЕ УЛУЧШЕНИЕ: Retry логика
    for attempt in range(3):
        try:
            params = {'offset': last_update_id + 1, 'timeout': 30,
                      'allowed_updates': ['message', 'callback_query']}
            resp = requests.get(f"{API_URL}/getUpdates", params=params, timeout=35)
            if resp.status_code == 401:
                stop_polling = True
                return []
            data = resp.json()
            return data.get('result', []) if data.get('ok') else []
        except requests.exceptions.Timeout:
            logger.warning(f"⏳ Попытка {attempt + 1}/3: Таймаут getUpdates")
            time.sleep(2)
        except Exception as e:
            logger.error(f"🚨 Попытка {attempt + 1}/3: {e}")
            if attempt == 2:
                return []
            time.sleep(5)
    return []

def bot_main_loop():
    global last_update_id, bot_status, message_count, stop_polling
    logger.info("🤖 Основной цикл бота запущен")
    
    # АВТОНОМНОЕ УЛУЧШЕНИЕ: Heartbeat
    last_heartbeat = time.time()
    max_errors = 5
    consecutive_errors = 0
    restart_count = 0
    
    while not stop_polling:
        try:
            # Heartbeat каждые 60 секунд
            if time.time() - last_heartbeat > 60:
                logger.info("💓 Bot heartbeat - ready for messages")
                last_heartbeat = time.time()
            
            updates = get_updates()
            if not updates:
                time.sleep(1)
                continue
                
            for update in updates:
                try:
                    update_id = update.get('update_id', 0)
                    
                    if 'message' in update:
                        msg = update['message']
                        chat_id = msg.get('chat', {}).get('id')
                        text = msg.get('text', '')
                        thread_id = msg.get('message_thread_id')
                        
                        logger.info(f"🔍 Update {update_id}: чат {chat_id}, текст: {text[:30]}...")
                        
                        process_message(msg)
                        logger.info(f"✅ Сообщение {message_count} → топик {thread_id}")
                        # Обновляем активность
                        globals()['last_activity'] = datetime.now()
                        
                    if 'callback_query' in update:
                        handle_callback(update)
                        
                    last_update_id = max(last_update_id, update_id)
                    consecutive_errors = 0  # Сброс ошибок при успехе
                    
                except Exception as e:
                    logger.error(f"⚠️ Ошибка обработки update: {e}")
                    logger.error(f"Update содержание: {update}")
                    
        except Exception as e:
            consecutive_errors += 1
            logger.error(f"❌ Ошибка цикла #{consecutive_errors}: {e}")
            
            if consecutive_errors >= max_errors:
                logger.critical("🆘 Критические ошибки - автоперезапуск")
                restart_count += 1
                bot_status = "ПЕРЕЗАПУСК"
                
                # Уведомление админу
                try:
                    requests.post(f"{API_URL}/sendMessage", json={
                        "chat_id": ADMIN_USER_ID,
                        "text": f"🔄 Автоперезапуск #{restart_count}\nПричина: {e}"
                    }, timeout=5)
                except:
                    pass
                
                time.sleep(10)
                consecutive_errors = 0
                bot_status = "АКТИВЕН"
            else:
                bot_status = "ОШИБКА"
                time.sleep(5)
                bot_status = "АКТИВЕН"
                
        time.sleep(1)

# Flask приложение для Gunicorn
app = Flask(__name__)

# Инициализация при импорте для Gunicorn
if BOT_TOKEN:
    init_logging()
    logger.info("🚀 Инициализация автономного бота для Gunicorn...")
    
    # Запуск бота в отдельном потоке при старте приложения
    bot_thread = threading.Thread(target=bot_main_loop, daemon=True)
    bot_thread.start()
    logger.info("✅ Бот запущен в фоновом потоке")

@app.route('/')
def home():
    uptime = datetime.now() - bot_start_time
    h, m = divmod(int(uptime.total_seconds() // 60), 60)
    return f"<h1>YukMarkazi Bot – {bot_status}</h1><p>Сообщений: {message_count}</p><p>Uptime: {h}ч {m}м</p>"

@app.route('/health')
def health():
    uptime_seconds = (datetime.now() - bot_start_time).total_seconds()
    last_activity = globals().get('last_activity', bot_start_time)
    last_activity_seconds = (datetime.now() - last_activity).total_seconds()
    
    is_healthy = True
    status_code = 200 if is_healthy else 503
    
    health_data = {
        "status": "healthy" if is_healthy else "unhealthy",
        "bot_status": bot_status,
        "uptime_seconds": int(uptime_seconds),
        "messages_processed": message_count,
        "last_activity_seconds_ago": int(last_activity_seconds),
        "timestamp": datetime.now().isoformat()
    }
    
    return health_data, status_code

@app.route('/ping')
def ping():
    return "pong", 200

@app.route('/telegram', methods=['POST'])
def telegram_webhook():
    try:
        update = request.get_json(force=True)
        if 'message' in update:
            process_message(update['message'])
        if 'callback_query' in update:
            handle_callback(update)
        return jsonify(ok=True), 200
    except Exception:
        logger.exception("Webhook error")
        return jsonify(ok=False), 500

if __name__ == '__main__':
    init_logging()
    
    # Graceful shutdown
    def shutdown_handler(signum, frame):
        global stop_polling, bot_status
        stop_polling = True
        bot_status = "ОСТАНОВЛЕН"
        logger.info("🛑 Graceful shutdown")
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)
    
    # Запуск автономного бота
    threading.Thread(target=bot_main_loop, daemon=True).start()
    
    # Уведомление о запуске
    try:
        requests.post(f"{API_URL}/sendMessage", json={
            "chat_id": ADMIN_USER_ID,
            "text": "🚀 АВТОНОМНЫЙ БОТ v2.0\n\n✅ Полностью независимый\n✅ Автовосстановление\n✅ Heartbeat система\n\nРаботаю 24/7 без Replit Agent!"
        }, timeout=5)
    except:
        pass
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
