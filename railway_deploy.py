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

# ========== REGION_KEYWORDS ==========
REGION_KEYWORDS = {
    'toshkent': {
        'topic_id': 101362,
        'keywords': [
            # столица
            'toshkent', 'tashkent', 'toshkent shahri', 'tashkent city',
            'tosh-kent', 'tash-kent', 'toshʼkent', 'tashʼkent',
            'toshkent İ', 'toshkent i', 'TOSHKENT', 'TASHKENT',
            # области и районы
            'bekobod', 'bekabad', 'bekobod tumani', 'bekabad tumani',
            'olmaliq', 'alma-lyk', 'olmalik', 'olmaliq İ', 'olmaliq i',
            'ohangaron', 'axangaron', 'ohanʼgaron', 'ohangaron İ', 'ohangaron i',
            'angren', 'angren İ', 'angiren', 'angren i',
            'chirchiq', 'chirchik', 'chirchik İ', 'chir-chiq', 'chirchiq i',
            'yangiyul', "yangiyo'l", 'yangiyul İ', 'yangiyul i', "yangiyo'l İ",
            'sergeli', 'chilonzor', 'chilon-zor', 'mirzo-ulugbek',
            'yunus-obod', 'yunusobod', 'yunusʼobod', 'yunus‘obod', 'yunus’obod',
            'm-u-lugbek', 'mirzoulugbek', 'mirzo ulugbek'
        ]
    },
    'andijon': {
        'topic_id': 101387,
        'keywords': [
            'andijon', 'andijan', 'andijon İ', 'andijonʼ', 'andijon i', 'andijon‘',
            'asaka', 'asaka İ', 'asakaʼ', 'asaka tumani', 'asaka i', 'asaka‘',
            'marhamat', 'marxamat', 'marhamat tumani', 'marhamat i',
            'shahrixon', 'shahrixon tumani', 'shaxrixon', 'shahrixon i',
            'xoja-obod', 'xojaobod', 'xojaʼobod', 'xoja‘obod', 'xoja’obod',
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
            'margilon', 'margilan', 'margilon İ', 'margilon i',
            'quvasoy', 'kuvasay', 'quvasoy İ', 'quvasoy i', 'quvasoyʼ',
            'beshariq', 'besharik', 'beshariq İ', 'beshariq i',
            "bog'dod", 'bogdod', "bogʻdod", "bog'dod İ", "bog'dod i",
            'oltiarik', 'oltiarik İ', 'oltiarik i',
            'rishton', 'rishtan', 'rishton İ', 'rishton i',
            'sox', 'sox tumani', 'sox İ', 'sox i'
        ]
    },
    'namangan': {
        'topic_id': 101383,
        'keywords': [
            'namangan', 'namangan İ', 'namanganʼ', 'namangan i', 'namangan‘',
            'chortoq', 'chartak', 'chortoq İ', 'chortoq i', 'chortoqʼ',
            'yangiqorgon', 'yangikurgan', 'yangi-qorğon', 'yangikurgan i',
            'chust', 'chust tumani', 'chust İ', 'chust i', 'chustʼ', 'chust‘',
            'kosonsoy', 'kosonsoy tumani', 'kosonsoy İ', 'kosonsoy i',
            'mullomirsoy', 'mullomirʼsoy', 'mullomir‘soy',
            'uchqorgon', 'uch-qorğon', 'uchqoʻrgʻon', 'uchqorgon i',
            'pop', 'pop tumani', 'pop İ', 'pop i'
        ]
    },
    'buxoro': {
        'topic_id': 101372,
        'keywords': [
            'buxoro', 'bukhara', 'buxara', 'buxoro İ', 'buxoroʼ', 'buxoro i', 'buxoro‘',
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
            'samarqand', 'samarkand', 'samarqand İ', 'samarqandʼ', 'samarqand i', 'samarqand‘',
            'urgut', 'urgut tumani', 'urgut İ', 'urgut i',
            'kattaqorgon', 'kattakurgan', 'katta-qorğon', 'kattaqoʻrgʻon', 'kattaqorgon i',
            'payariq', 'payariq tumani', 'payarik', 'payariq i',
            'ishtixon', 'ishtixon tumani', 'ishtixon İ', 'ishtixon i',
            'jomboy', 'jomboy tumani', 'jomboy İ', 'jomboy i',
            'nurabod', 'nurabod tumani', 'nurabod i'
        ]
    },
    'qashqadaryo': {
        'topic_id': 101380,
        'keywords': [
            'qarshi', 'karshi', 'qarshi İ', 'qarshiʼ', 'qarshi i', 'qarshi‘',
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
            'termiz', 'termez', 'termiz İ', 'termizʼ', 'termiz i', 'termiz‘',
            'denov', 'denau', 'denov İ', 'denovʼ', 'denov i', 'denov‘',
            'boysun', 'boysun tumani', 'boysun İ', 'boysun i',
            'sherobod', 'sherobod tumani', 'sherobod İ', 'sherobod i',
            'qumqorgon', 'qumqorğon', 'qumqoʻrgʻon', 'qumqorgon i',
            'uzun', 'uzun tumani', 'uzun i'
        ]
    },
    'navoiy': {
        'topic_id': 101379,
        'keywords': [
            'navoiy', 'navoi', 'navoiy İ', 'navoi İ', 'navoiy i', 'navoi i',
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
            'guliston', 'gulistan', 'guliston İ', 'gulistonʼ', 'guliston i', 'guliston‘',
            'shirin', 'shirin tumani', 'shirin İ', 'shirin i',
            'boyovut', 'bayaut', 'boyovut tumani', 'boyovut İ', 'boyovut i',
            'sirdaryo', 'sirdaryo İ', 'sirdaryoʼ', 'sirdaryo i', 'sirdaryo‘',
            'mirzaobod', 'mirzaobod tumani', 'mirzaobod i'
        ]
    },
    'jizzax': {
        'topic_id': 101377,
        'keywords': [
            'jizzax', 'jizzax İ', 'jizzax i', 'jizzakh', 'jiz-zax', 'жиззах', 'джизак',
            'gallaaral', 'gallaaral İ', 'gallaaral i', 'galla-aral', 'gallaaʼral', 'galla‘aral',
            'pakhtakor', 'pakhtakor İ', 'pakhtakor i', 'pakhtakor tumani',
            'zomin', 'zomin tumani', 'zomin İ', 'zomin i',
            'pishagar', 'pishagaron', 'pishagardan', 'pishagar İ', 'pishagar i', 'pishagar‘',
            'forish', 'forish tumani', 'forish İ', 'forish i',
            'arnasoy', 'arnasoy tumani', 'arnasoy İ', 'arnasoy i',
            'baxmal', 'baxmal tumani', 'baxmal i',
            # добавляем Пишагардан
            'pishagardan', 'пишагардан', 'pishagardan i', 'pishagardan İ'
        ]
    },
    'xorazm': {
        'topic_id': 101660,
        'keywords': [
            'xorazm', 'xorezm', 'xorazm İ', 'xorezm İ', 'xorazm i', 'xorezm i',
            'xiva', 'khiva', 'xiva İ', 'xivaʼ', 'xiva i', 'xiva‘',
            'urganch', 'urgench', 'urganch İ', 'urganchʼ', 'urganch i', 'urganch‘',
            'shovot', 'shavat', 'shovot İ', 'shovotʼ', 'shovot i', 'shovot‘',
            'yangiariq', 'yangiariq tumani', 'yangiariq İ', 'yangiariq i',
            'bogʻot', 'bogot', 'bogʻot İ', 'bogʻot i'
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
            'yangilik', 'yangiliklar', 'новости', 'news', 'xabar', 'so‘ngi yangiliklar'
        ]
    },
        'urganch': {
        'topic_id': 101375,
        'keywords': [
            # сам город
            'urganch', 'urgench', 'urganch İ', 'urganch i', 'urganch‘', 'urganchʼ',
            # районы Хоразма
            'xiva', 'khiva', 'xiva İ', 'xiva i', 'xiva‘', 'xivaʼ',
            'shovot', 'shavat', 'shovot İ', 'shovot i', 'shovot‘', 'shovotʼ',
            'yangiariq', 'yangiariq tumani', 'yangiariq İ', 'yangiariq i',
            'bogʻot', 'bogot', 'bogʻot tumani', 'bogʻot İ', 'bogʻot i',
            'xazarasp', 'hazarasp', 'xazarasp tumani', 'xazarasp i',
            'gurlan', 'gurlan tumani', 'gurlan İ', 'gurlan i',
            'qoshkopir', 'koshkupir', 'qoshkopir tumani', 'qoshkopir i',
            'tuproqqala', 'tuprak kala', 'tuproqqala tumani', 'tuproqqala i'
        ]
    },
    'nukus': {
        'topic_id': 101376,
        'keywords': [
            'nukus', 'nukus İ', 'nukusʼ', 'nukus i', 'nukus‘', 'noʻkis', 'nokis',
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
            'turtkul', 'turtkul İ', 'turtkulʼ', 'turtkul tumani', 'turtkul i', 'turtkul‘',
            'khojeli', 'xojeli', 'hodjeyli', 'xojeli İ', 'xojeli i', 'khojeliʼ', 'xojeli‘',
            'amudarya', 'amudaryo', 'amudarya tumani', 'amudarya İ', 'amudarya i',
            'chimboy', 'chimboy tumani', 'chimboy İ', 'chimboy i'
        ]
    },
        'xalqaro': {
        'topic_id': 101367,
        'keywords': [
            # Россия
            'russia', 'rosiya', 'russia İ', 'rosiya İ', 'russia i', 'rosiya i',
            'moskva', 'moscow', 'moskva İ', 'moskvaʼ', 'moskva i', 'moskva‘',
            'spb', 'sankt-peterburg', 'piter', 'saint-petersburg', 'spb İ', 'spb i',
            'krasnodar', 'krasnodar İ', 'krasnodar i',
            'rostov', 'rostov-na-donu', 'rostov İ', 'rostov i',
            'volgograd', 'volgograd İ', 'volgograd i',
            'kazan', 'kazan İ', 'kazan i',
            'nizhny novgorod', 'nizhniy novgorod', 'nizhny novgorod İ', 'nizhny i',
            'samara', 'samara İ', 'samara i',
            'ufa', 'ufa İ', 'ufa i',
            'perm', 'perm İ', 'perm i',
            'krasnoyarsk', 'krasnoyarsk İ', 'krasnoyarsk i',
            'novosibirsk', 'novosibirsk İ', 'novosibirsk i',
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

            # ОАЭ
            'dubai', 'dubay', 'dubai İ', 'dubay İ', 'dubai i', 'dubay i',
            'abu dhabi', 'abu-dhabi', 'abu dhabi İ', 'abu dhabi i',

            # Китай
            'china', 'xitoy', 'china İ', 'xitoy İ', 'china i', 'xitoy i',
            'shanghai', 'shanghai İ', 'shanghai i',
            'beijing', 'pekin', 'beijing İ', 'beijing i',
            'guangzhou', 'guangzhou İ', 'guangzhou i',
            'shenzhen', 'shenzhen İ', 'shenzhen i',

            # Корея
            'korea', 'koreya', 'korea İ', 'koreya İ', 'korea i', 'koreya i',
            'seoul', 'seoul İ', 'seoul i',
            'busan', 'busan İ', 'busan i',

            # Европа (общее + крупные города)
            'europe', 'yevropa', 'europe İ', 'yevropa İ', 'europe i', 'yevropa i',
            'germany', 'germaniya', 'germany İ', 'germaniya i',
            'berlin', 'berlin İ', 'berlin i',
            'hamburg', 'hamburg İ', 'hamburg i',
            'munich', 'munich İ', 'munich i',
            'frankfurt', 'frankfurt İ', 'frankfurt i',
            'warsaw', 'warsaw İ', 'warsaw i',
            'prague', 'prague İ', 'prague i',
            'budapest', 'budapest İ', 'budapest i',
            'vienna', 'vienna İ', 'vienna i',
            'rome', 'rome İ', 'rome i',
            'milan', 'milan İ', 'milan i',
            'paris', 'paris İ', 'paris i',
            'madrid', 'madrid İ', 'madrid i',
            'barcelona', 'barcelona İ', 'barcelona i',

            # Другие маршруты
            'uzbekistan-germany', 'germany-uzbekistan', 'uzbekistan-poland', 'poland-uzbekistan'
        ]
    }
}

# ========== Логирование ==========
def init_logging():
    level = logging.DEBUG if os.getenv("DEBUG") else logging.INFO
    logging.basicConfig(level=level, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

message_count = 0
last_update_id = 0
bot_start_time = datetime.now()
bot_status = "АКТИВЕН"
stop_polling = False

def normalize_text(text: str) -> str:
    if not text:
        return ""
    # турецкая İ→I, ı→i
    text = text.replace('\u0130', 'I').replace('\u0131', 'i')
    # NFC → NFKD (декомпозиция)
    text = unicodedata.normalize('NFKD', text)
    # убираем диакритические знаки
    text = ''.join(ch for ch in text if unicodedata.category(ch) != 'Mn')
    # апострофы/дефисы → просто '
    text = re.sub(r"[ʼ‘’–—\-]+", "'", text)
    return text.lower().strip()

def send_message(chat_id, text, message_thread_id=None, reply_markup=None):
    global message_count
    if not BOT_TOKEN:
        return False
    try:
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML'
        }
        if message_thread_id is not None:
            data['message_thread_id'] = int(message_thread_id)
        if reply_markup is not None:
            data['reply_markup'] = reply_markup
        resp = requests.post(f"{API_URL}/sendMessage", json=data, timeout=10)
        if resp.json().get('ok'):
            message_count += 1
            return True
        return False
    except Exception:
        return False

def author_button(sender: dict) -> dict:
    uid = sender["id"]
    url = f"https://t.me/{BOT_USERNAME}?start=user_{uid}"
    return {
        "inline_keyboard": [[{"text": "👤 Aloqaga_chiqish", "url": url}]]
    }

def handle_admin_command(message):
    text = (message.get('text') or '').lower()
    chat_id = message['chat']['id']
    if message['from']['id'] != ADMIN_USER_ID:
        return
    if text in ('/start', 'старт', '/status', 'статус'):
        uptime = datetime.now() - bot_start_time
        h, m = divmod(int(uptime.total_seconds() // 60), 60)
        send_message(chat_id, f"🤖 Активен. Сообщений: {message_count}. Uptime {h}ч {m}м")

PHONE_REGEX = re.compile(
    r'(?:(?:\+?998|998)?[\s\-]?)?(?:\(?\d{2}\)?[\s\-]?){4}\d{2}'
)
ROUTE_REGEX = re.compile(
    r'(?:🇺🇿\s*([A-Za-z\u0130\u0131\'\w\-]+(?:\s+\([A-Za-z\u0130\u0131\'\w\-]+\))?)\s*\n🇺🇿\s*([A-Za-z\u0130\u0131\'\w\-]+(?:\s+\([A-Za-z\u0130\u0131\'\w\-]+\))?)'
    r'|[Мм]аршрут:\s*([A-Za-z\u0130\u0131\'\w\-]+(?:\s+\([A-Za-z\u0130\u0131\'\w\-]+\))?)\s*[-–—→➯]{1,3}\s*([A-Za-z\u0130\u0131\'\w\-]+(?:\s+\([A-Za-z\u0130\u0131\'\w\-]+\))?)'
    r'|([A-Za-z\u0130\u0131\'\w\-]+(?:\s+\([A-Za-z\u0130\u0131\'\w\-]+\))?)\s*[-–—→➯]{1,3}\s*([A-Za-z\u0130\u0131\'\w\-]+(?:\s+\([A-Za-z\u0130\u0131\'\w\-]+\))?)'
    r'|([A-Za-z\u0130\u0131\'\w\-]+)\s+(NAMANGANGA|TOSHKENT|ANDIJONGA|SURXONDARYOGA|QASHQADARYOGA|SAMARQANDGA|BUXOROGA|FARGʼONAGA|ANDIJONGA|SIRDARYOGA|JIZZAXGA|XORAZMGA|NAVOIYGA|QORAQALPOQSTONGA))',
    re.IGNORECASE
)

def extract_phone_number(text):
    m = PHONE_REGEX.search(text)
    return m.group().strip() if m else "Телефон не указан"

def extract_route_and_cargo(text: str):
    clean = re.sub(r'^[❗️⚠️!#\s]+', '', text, flags=re.MULTILINE)
    matches = ROUTE_REGEX.findall(clean)
    if not matches:
        return None, None, text

    match = matches[0]

    # Проверяем каждую пару групп
    pairs = [
        (match[0], match[1]),
        (match[2], match[3]),
        (match[4], match[5]),
        (match[6], match[7]),
    ]

    fr, to = None, None
    for a, b in pairs:
        if a and b:
            fr, to = a.strip(), b.strip()
            break

    if not fr or not to:
        return None, None, text

    # Удаляем найденные совпадения из текста
    cargo = clean
    for m in matches:
        cargo = cargo.replace(''.join(m), '').strip()

    return fr.lower(), to.lower(), cargo
def format_cargo_text(cargo_text):
    keywords = [
        'фура', 'fura', 'isuzu', 'kamaz', 'man', 'daf', 'scania', 'volvo',
        'тент', 'контейнер', 'реф', 'ref', 'refrigerator', 'chakman', 'чакман'
    ]
    text = cargo_text.lower()
    match = re.search('|'.join(keywords), text)
    transport = match.group(0).title() if match else "Транспорт"
    clean_desc = re.sub('|'.join(keywords), '', text, flags=re.I).strip()
    desc = clean_desc or "—"
    return transport, desc

def ask_admin_topic(message, from_city, to_city):
    text = message.get('text', '')
    user = message.get('from', {})
    user_data = f"{user.get('id')}:{user.get('first_name', '')}:{user.get('username', '')}"
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

def process_message(message):
    global last_update_id
    try:
        text = message.get('text', '')
        chat_id = message['chat']['id']
        user_id = message['from']['id']
        if chat_id == ADMIN_USER_ID:
            handle_admin_command(message)
            return
        if chat_id != MAIN_GROUP_ID:
            return
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
        to_reg = find_region(to_city)
        if from_reg is None or to_reg is None:
            ask_admin_topic(message, from_city, to_city)
            return

        topic_key = 'xalqaro' if 'xalqaro' in {from_reg, to_reg} else from_reg
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
    try:
        params = {'offset': last_update_id + 1, 'timeout': 30,
                  'allowed_updates': ['message', 'callback_query']}
        resp = requests.get(f"{API_URL}/getUpdates", params=params, timeout=35)
        if resp.status_code == 401:
            stop_polling = True
            return []
        data = resp.json()
        return data.get('result', []) if data.get('ok') else []
    except Exception:
        return []

def bot_main_loop():
    global last_update_id
    logger.info("Bot started")
    while True:
        if stop_polling:
            break
        try:
            for upd in get_updates():
                last_update_id = upd['update_id']
                if 'message' in upd:
                    process_message(upd['message'])
                if 'callback_query' in upd:
                    handle_callback(upd)
        except Exception:
            time.sleep(5)
        time.sleep(1)

app = Flask(__name__)

@app.route('/')
def home():
    uptime = datetime.now() - bot_start_time
    h, m = divmod(int(uptime.total_seconds() // 60), 60)
    return f"<h1>YukMarkazi Bot – {bot_status}</h1><p>Сообщений: {message_count}</p><p>Uptime: {h}ч {m}м</p>"

@app.route('/health')
def health():
    return {'status': bot_status.lower(), 'messages': message_count}

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
    signal.signal(signal.SIGTERM, lambda *a: sys.exit(0))
    signal.signal(signal.SIGINT, lambda *a: sys.exit(0))
    threading.Thread(target=bot_main_loop, daemon=True).start()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
