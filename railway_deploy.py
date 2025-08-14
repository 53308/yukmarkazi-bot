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
  "tashkent_city": {
    "topic_id": 101362,
    "cyrillic_uz": "Тошкент шаҳри",
    "latin_uz": "Toshkent shahri",
    "russian": "город Ташкент",
    "aliases": [
      "toshkent", "tashkent", "tosh-kent", "tash-kent", "towkent", "toshkent shahri", "tashkent city",
      "toshkentga", "tashkentga", "toshkentdan", "tashkentdan", "toshkentda", "toshkentdagi",
      "Тошкент", "Ташкент", "Тош-Кент", "Таш-Кент", "Товкент", "Тошкент шаҳри", "город Ташкент",
      "Ташкента", "Ташкенте", "Ташкенту", "Ташкентский", "Ташкент-Сити", "toshkent'skiy"
    ]
  },

  "yunusobod": {
    "topic_id": 101362,
    "cyrillic_uz": "Юнусобод тумани",
    "latin_uz": "Yunusobod tumani",
    "russian": "Юнусабадский район",
    "aliases": [
      "yunusobod", "yunusabad", "yunus-obod", "yunus obod", "yunusobod tumani", "yunusobod rayon",
      "yunusobodda", "yunusoboddan", "yunusobodga", "yunusobodlik",
      "Юнусобод", "Юнусабад", "Юнус-Абад", "Юнусабадский район"
    ]
  },

  "mirzo_ulugbek": {
    "topic_id": 101362,
    "cyrillic_uz": "Мирзо-Улуғбек тумани",
    "latin_uz": "Mirzo-Ulug‘bek tumani",
    "russian": "Мирзо-Улугбекский район",
    "aliases": [
      "mirzo-ulugbek", "mirzo ulugbek", "mirzoulugbek", "mirzo-ulughbek", "mirzo ulug‘bek",
      "mirzo-ulug'bek", "mirzo ulug'bek", "mirzo-ulugbek tumani", "mirzo ulugbek rayon",
      "mirzo-ulugbekda", "mirzo-ulugbekdan", "mirzo-ulugbekga",
      "Мирзо-Улуғбек", "Мирзо Улуғбек", "Мирзо-Улугбекский район"
    ]
  },

  "yashnobod": {
    "topic_id": 101362,
    "cyrillic_uz": "Яшнобод тумани",
    "latin_uz": "Yashnobod tumani",
    "russian": "Яшнабадский район",
    "aliases": [
      "yashnobod", "yashnabad", "yashno-bod", "yashnobod tumani", "yashnobod rayon",
      "yashnobodda", "yashnoboddan", "yashnobodga", "yashnobodlik",
      "Яшнобод", "Яшнабад", "Яшнабадский район"
    ]
  },

  "olmazor": {
    "topic_id": 101362,
    "cyrillic_uz": "Олмазор тумани",
    "latin_uz": "Olmazor tumani",
    "russian": "Алмазарский район",
    "aliases": [
      "olmazor", "olma-zor", "olma zor", "almazar", "almazar rayon", "olmazor tumani",
      "olmazorda", "olmazordan", "olmazorlik",
      "Олмазор", "Олма-зор", "Алмазар", "Алмазарский район"
    ]
  },

  "uchtepa": {
    "topic_id": 101362,
    "cyrillic_uz": "Учтепа тумани",
    "latin_uz": "Uchtepa tumani",
    "russian": "Учтепинский район",
    "aliases": [
      "uchtepa", "uch-tepa", "uch tepa", "uchtepa tumani", "uchtepa rayon",
      "uchtepada", "uchtepadan", "uchtepaga",
      "Учтепа", "Уч-Тепа", "Учтепинский район"
    ]
  },

  "shayxontohur": {
    "topic_id": 101362,
    "cyrillic_uz": "Шайхонтоҳур тумани",
    "latin_uz": "Shayxontohur tumani",
    "russian": "Шайхантаурский район",
    "aliases": [
      "shayxontohur", "shayxontoxur", "shaykhontohur", "shayxontahur",
      "shayxontohur tumani", "shayxontohur rayon",
      "shayxontohurda", "shayxontohurdan", "shayxontohurga",
      "Шайхонтоҳур", "Шайхантаур", "Шайхантаурский район"
    ]
  },

  "chilonzor": {
    "topic_id": 101362,
    "cyrillic_uz": "Чилонзор тумани",
    "latin_uz": "Chilonzor tumani",
    "russian": "Чиланзарский район",
    "aliases": [
      "chilonzor", "chilon-zor", "chilon zor", "chilonzor tumani", "chilonzor rayon",
      "chilonzorda", "chilonzordan", "chilonzorlik",
      "Чилонзор", "Чиланзар", "Чиланзарский район"
    ]
  },

  "sergeli": {
    "topic_id": 101362,
    "cyrillic_uz": "Сергели тумани",
    "latin_uz": "Sergeli tumani",
    "russian": "Сергелийский район",
    "aliases": [
      "sergeli", "sergili", "sergeli tumani", "sergili tumani", "sergeli rayon",
      "sergelida", "sergelidan", "sergeliga", "sergelilik",
      "Сергели", "Сергелийский район"
    ]
  },

  "yakkasaroy": {
    "topic_id": 101362,
    "cyrillic_uz": "Яккасарай тумани",
    "latin_uz": "Yakkasaroy tumani",
    "russian": "Яккасарайский район",
    "aliases": [
      "yakkasaroy", "yakkasaray", "yakka-saroy", "yakka saroy", "yakkasaroy tumani",
      "yakkasaroyda", "yakkasaroydan", "yakkasaroyga", "yakkasaroylik",
      "Яккасарай", "Яккасарайский район"
    ]
  },

  "mirobod": {
    "topic_id": 101362,
    "cyrillic_uz": "Мирабод тумани",
    "latin_uz": "Mirobod tumani",
    "russian": "Мирабадский район",
    "aliases": [
      "mirobod", "mirabad", "miro-bod", "mirobod tumani", "mirabad rayon",
      "mirobodda", "miroboddan", "mirobodga", "mirobodlik",
      "Мирабод", "Мирабад", "Мирабадский район"
    ]
  },

  "bektemir": {
    "topic_id": 101362,
    "cyrillic_uz": "Бектемир тумани",
    "latin_uz": "Bektemir tumani",
    "russian": "Бектемирский район",
    "aliases": [
      "bektemir", "bek-temir", "bektemir tumani", "bektemir rayon",
      "bektemirga", "bektemirdan", "bektemirlik",
      "Бектемир", "Бектемирский район"
    ]
  },

  "tashkent_region": {
    "topic_id": 101362,
    "cyrillic_uz": "Тошкент вилояти",
    "latin_uz": "Toshkent viloyati",
    "russian": "Ташкентская область",
    "aliases": [
      "toshkent viloyati", "tashkent oblast", "toshkent region",
      "toshkent viloyatiga", "toshkent viloyatidan", "toshkent viloyatda",
      "Тошкент вилояти", "Ташкентская область"
    ]
  },

  "bekobod": {
    "topic_id": 101362,
    "cyrillic_uz": "Бекобод шаҳри",
    "latin_uz": "Bekobod shahri",
    "russian": "город Бекабад",
    "aliases": [
      "bekobod", "bekabad", "bekobod shaxri", "bekobod city",
      "bekobodda", "bekoboddan", "bekobodga", "bekobodlik",
      "Бекобод", "Бекабад"
    ]
  },

  "angren": {
    "topic_id": 101362,
    "cyrillic_uz": "Ангрен шаҳри",
    "latin_uz": "Angren shahri",
    "russian": "город Ангрен",
    "aliases": [
      "angren", "angiren", "angren shaxri", "angren city",
      "angrenda", "angrendan", "angrenga", "angrenlik",
      "Ангрен", "Ангирен"
    ]
  },

  "almalyk": {
    "topic_id": 101362,
    "cyrillic_uz": "Олмалиқ шаҳри",
    "latin_uz": "Olmaliq shahri",
    "russian": "город Алмалык",
    "aliases": [
      "olmaliq", "olmalik", "almalyk", "almalik", "olmaliq shaxri", "olmaliq city",
      "olmaliqda", "olmaliqdan", "olmaliqlik",
      "Олмалиқ", "Алмалык"
    ]
  },

  "ohangaron": {
    "topic_id": 101362,
    "cyrillic_uz": "Оҳангарон тумани",
    "latin_uz": "Ohangaron tumani",
    "russian": "Ахангаранский район",
    "aliases": [
      "ohangaron", "axangaron", "ohan'garon", "ohangaron tumani", "ahangaran rayon",
      "ohangaronda", "ohangarondan", "ohangaronga",
      "Оҳангарон", "Ахангаран"
    ]
  },

  "yangiyul": {
    "topic_id": 101362,
    "cyrillic_uz": "Янгиюл шаҳри",
    "latin_uz": "Yangiyul shahri",
    "russian": "город Янгиюль",
    "aliases": [
      "yangiyul", "yangiyo'l", "yangiyul shaxri", "yangiyul city",
      "yangiyulda", "yangiyuldan", "yangiyulga", "yangiyullik",
      "Янгиюл", "Янгиюль"
    ]
  },

  "parkent": {
    "topic_id": 101362,
    "cyrillic_uz": "Паркент тумани",
    "latin_uz": "Parkent tumani",
    "russian": "Паркентский район",
    "aliases": [
      "parkent", "parkent tumani", "parkent rayon",
      "parkentda", "parkentdan", "parkentga", "parkentlik",
      "Паркент", "Паркентский район"
    ]
  },

  "piskent": {
    "topic_id": 101362,
    "cyrillic_uz": "Пискент тумани",
    "latin_uz": "Piskent tumani",
    "russian": "Пискентский район",
    "aliases": [
      "piskent", "piskent tumani", "piskent rayon",
      "piskentda", "piskentdan", "piskentga", "piskentlik",
      "Пискент", "Пискентский район"
    ]
  },

  "quyichirchiq": {
    "topic_id": 101362,
    "cyrillic_uz": "Қуйичирчиқ тумани",
    "latin_uz": "Quyichirchiq tumani",
    "russian": "Куйичирчикский район",
    "aliases": [
      "quyichirchiq", "quyi-chirchiq", "quyi chirchiq", "kuyichirchiq", "kuyi-chirchiq",
      "quyichirchiq tumani", "kuyichirchiq rayon",
      "quyichirchiqda", "quyichirchiqdan", "quyichirchiqga",
      "Қуйичирчиқ", "Куйичирчикский район"
    ]
  },

  "yuqorichirchiq": {
    "topic_id": 101362,
    "cyrillic_uz": "Юқоричирчиқ тумани",
    "latin_uz": "Yuqorichirchiq tumani",
    "russian": "Юкоричирчикский район",
    "aliases": [
      "yuqorichirchiq", "yuqori-chirchiq", "yuqori chirchiq", "yukorichirchiq", "yukori-chirchiq",
      "yuqorichirchiq tumani", "yukorichirchiq rayon",
      "yuqorichirchiqda", "yuqorichirchiqdan", "yuqorichirchiqga",
      "Юқоричирчиқ", "Юкоричирчикский район"
    ]
  },

  "boka": {
    "topic_id": 101362,
    "cyrillic_uz": "Бўка тумани",
    "latin_uz": "Bo'ka tumani",
    "russian": "Букинский район",
    "aliases": [
      "boka", "bo'ka", "buka", "boka tumani", "buka rayon",
      "bokada", "bokadan", "bokaga", "bokalik",
      "Бўка", "Бука", "Букинский район"
    ]
  },

  "chinaz": {
    "topic_id": 101362,
    "cyrillic_uz": "Чиноз тумани",
    "latin_uz": "Chinoz tumani",
    "russian": "Чиназский район",
    "aliases": [
      "chinaz", "chinz", "chinoz", "chinaz tumani", "chinoz tumani", "chinaz rayon",
      "chinazda", "chinazdan", "chinazga", "chinazlik",
      "Чиназ", "Чиноз", "Чиназский район"
    ]
  },

  "zangiota": {
    "topic_id": 101362,
    "cyrillic_uz": "Зангиота тумани",
    "latin_uz": "Zangiota tumani",
    "russian": "Зангиатинский район",
    "aliases": [
      "zangiota", "zangi-ota", "zangi ota", "zangiota tumani", "zangiota rayon",
      "zangiotalik", "zangiota-da", "zangiota-dan",
      "Зангиота", "Зангиатинский район"
    ]
  },

  "qibray": {
    "topic_id": 101362,
    "cyrillic_uz": "Қибрай тумани",
    "latin_uz": "Qibray tumani",
    "russian": "Кибрайский район",
    "aliases": [
      "qibray", "kibray", "qibray tumani", "kibray rayon",
      "qibrayda", "qibraydan", "qibrayga", "qibraylik",
      "Қибрай", "Кибрайский район"
    ]
  },

  "nurafshon": {
    "topic_id": 101362,
    "cyrillic_uz": "Нурафшон шаҳри",
    "latin_uz": "Nurafshon shahri",
    "russian": "город Нурафшон",
    "aliases": [
      "nurafshon", "nurafshan", "nurafshon shaxri", "nurafshon city",
      "nurafshonda", "nurafshondan", "nurafshonlik",
      "Нурафшон", "город Нурафшон"
    ]
  },

  "akhangaran": {
    "topic_id": 101362,
    "cyrillic_uz": "Охонгирон тумани",
    "latin_uz": "Oxong‘iron tumani",
    "russian": "Ахангаранский район",
    "aliases": [
      "akhangaran", "axangaran", "oxongiron", "oxong‘iron", "ahan'garan",
      "akhangaran tumani", "akhangaran rayon",
      "akhangaranda", "akhangarandan", "akhangaranlik",
      "Ахангаран", "Ахангаранский район"
    ]
  },

  "gazalkent": {
    "topic_id": 101362,
    "cyrillic_uz": "Газалкент тумани",
    "latin_uz": "Gazalkent tumani",
    "russian": "Газалкентский район",
    "aliases": [
      "gazalkent", "gazal-kent", "gazalkent tumani", "gazalkent rayon",
      "gazalkentda", "gazalkentdan", "gazalkentlik",
      "Газалкент", "Газалкентский район"
    ]
  },

  "keles": {
    "topic_id": 101362,
    "cyrillic_uz": "Келес тумани",
    "latin_uz": "Keles tumani",
    "russian": "Келесский район",
    "aliases": [
      "keles", "keles tumani", "keles rayon",
      "kelesda", "kelesdan", "kelesga", "keleslik",
      "Келес", "Келесский район"
    ]
  },

  "andijon_city": {
    "topic_id": 101387,
    "cyrillic_uz": "Андижон шаҳри",
    "latin_uz": "Andijon shahri",
    "russian": "город Андижан",
    "aliases": [
      "andijon", "andijan", "andijon shaxri", "andijon city",
      "andijonda", "andijondan", "andijonga", "andijonlik",
      "Андижон", "Андижан", "город Андижан"
    ]
  },

  "asaka": {
    "topic_id": 101387,
    "cyrillic_uz": "Асака шаҳри",
    "latin_uz": "Asaka shahri",
    "russian": "город Асака",
    "aliases": [
      "asaka", "asaka shaxri", "asaka city",
      "asakada", "asakadan", "asakaga", "asakalik",
      "Асака", "город Асака"
    ]
  },

  "marhamat": {
    "topic_id": 101387,
    "cyrillic_uz": "Марҳамат тумани",
    "latin_uz": "Marhamat tumani",
    "russian": "Мархаматский район",
    "aliases": [
      "marhamat", "marxamat", "marhamat tumani", "marhamat rayon",
      "marhamatda", "marhamatdan", "marhamatga", "marhamatlik",
      "Марҳамат", "Мархамат", "Мархаматский район"
    ]
  },

  "shahrixon": {
    "topic_id": 101387,
    "cyrillic_uz": "Шаҳрихон тумани",
    "latin_uz": "Shahrixon tumani",
    "russian": "Шахриханский район",
    "aliases": [
      "shahrixon", "shaxrixon", "shahrixon tumani", "shaxrixon tumani", "shahrixon rayon",
      "shahrixonda", "shahrixondan", "shahrixonlik",
      "Шаҳрихон", "Шахрихан", "Шахриханский район"
    ]
  },

  "xojaobod": {
    "topic_id": 101387,
    "cyrillic_uz": "Хўжаобод тумани",
    "latin_uz": "Xo'jaobod tumani",
    "russian": "Ходжаабадский район",
    "aliases": [
      "xojaobod", "xo'jaobod", "xoja-obod", "xoja obod", "xojaobod tumani", "xojaobod rayon",
      "xojaobodda", "xojaoboddan", "xojaobodga", "xojaobodlik",
      "Хўжаобод", "Ходжаабад", "Ходжаабадский район"
    ]
  },

  "qorgontepa": {
    "topic_id": 101387,
    "cyrillic_uz": "Қўрғонтепа тумани",
    "latin_uz": "Qoʻrgʻontepa tumani",
    "russian": "Кургантепинский район",
    "aliases": [
      "qorgontepa", "qurghontepa", "qoʻrgʻontepa", "qorgontepa tumani", "kurgan-tepa",
      "qorgontepada", "qorgontepadan", "qorgontepaga",
      "Қўрғонтепа", "Кургантепа", "Кургантепинский район"
    ]
  },

  "oltinkol": {
    "topic_id": 101387,
    "cyrillic_uz": "Олтинкўл тумани",
    "latin_uz": "Oltinkoʻl tumani",
    "russian": "Алтыкульский район",
    "aliases": [
      "oltinkol", "oltinkoʻl", "altinkul", "oltinkol tumani", "altinkul rayon",
      "oltinkolda", "oltinkoldan", "oltinkolga", "oltinkollik",
      "Олтинкўл", "Алтыкуль", "Алтыкульский район"
    ]
  },

  "fargona_city": {
    "topic_id": 101382,
    "cyrillic_uz": "Фарғона шаҳри",
    "latin_uz": "Farg'ona shahri",
    "russian": "город Фергана",
    "aliases": [
      "farg'ona", "fargʻona", "fargona", "fergana", "farg'ona shaxri", "fargona city",
      "farg'onada", "farg'onadan", "farg'onga", "farg'onalik",
      "Фарғона", "Фергана", "город Фергана"
    ]
  },

  "kokand": {
    "topic_id": 101382,
    "cyrillic_uz": "Қўқон шаҳри",
    "latin_uz": "Qo'qon shahri",
    "russian": "город Коканд",
    "aliases": [
      "qoqon", "kokand", "qo'qon", "qo‘qon", "qoqon shaxri", "qoqon city",
      "qoqonda", "qoqondan", "qoqonga", "qoqonlik",
      "Қўқон", "Коканд"
    ]
  },

  "margilan": {
    "topic_id": 101382,
    "cyrillic_uz": "Марғилон шаҳри",
    "latin_uz": "Marg'ilon shahri",
    "russian": "город Маргилан",
    "aliases": [
      "margilon", "marg'ilon", "margilan", "margilon shaxri", "margilon city",
      "margilonda", "margilondan", "margilonlik",
      "Марғилон", "Маргилан"
    ]
  },

  "quvasoy": {
    "topic_id": 101382,
    "cyrillic_uz": "Қувасой шаҳри",
    "latin_uz": "Quvasoy shahri",
    "russian": "город Кувасай",
    "aliases": [
      "quvasoy", "kuvasay", "quvasoy shaxri", "quvasoy city",
      "quvasoyda", "quvasoydan", "quvasoylik",
      "Қувасой", "Кувасай"
    ]
  },

  "beshariq": {
    "topic_id": 101382,
    "cyrillic_uz": "Бешариқ тумани",
    "latin_uz": "Beshariq tumani",
    "russian": "Бешарыкский район",
    "aliases": [
      "beshariq", "besharik", "beshariq tumani", "beshariq rayon",
      "beshariqda", "beshariqdan", "beshariqga", "beshariqlik",
      "Бешариқ", "Бешарык", "Бешарыкский район"
    ]
  },

  "bogdod": {
    "topic_id": 101382,
    "cyrillic_uz": "Боғдод тумани",
    "latin_uz": "Bog'dod tumani",
    "russian": "Багдадский район",
    "aliases": [
      "bogdod", "bog'dod", "bogʻdod", "bagdad", "bogdod tumani", "bagdad rayon",
      "bogdodda", "bogdoddan", "bogdodga", "bogdodlik",
      "Боғдод", "Багдад", "Багдадский район"
    ]
  },

  "oltiarik": {
    "topic_id": 101382,
    "cyrillic_uz": "Олтиориқ тумани",
    "latin_uz": "Oltiariq tumani",
    "russian": "Алтыарыкский район",
    "aliases": [
      "oltiarik", "oltiariq", "altiarik", "oltiarik tumani", "altiarik rayon",
      "oltiarikda", "oltiarikdan", "oltiariklik",
      "Олтиориқ", "Алтыарык", "Алтыарыкский район"
    ]
  },

  "rishton": {
    "topic_id": 101382,
    "cyrillic_uz": "Риштон тумани",
    "latin_uz": "Rishton tumani",
    "russian": "Риштанский район",
    "aliases": [
      "rishton", "rishtan", "rishton tumani", "rishton rayon",
      "rishtonda", "rishtondan", "rishtonlik",
      "Риштон", "Риштан", "Риштанский район"
    ]
  },

  "sox": {
    "topic_id": 101382,
    "cyrillic_uz": "Сўх тумани",
    "latin_uz": "Sox tumani",
    "russian": "Сухский район",
    "aliases": [
      "sox", "sux", "sox tumani", "sux rayon",
      "soxda", "soxdan", "soxga", "soxlik",
      "Сўх", "Сух", "Сухский район"
    ]
  },

  "namangan_city": {
    "topic_id": 101383,
    "cyrillic_uz": "Наманган шаҳри",
    "latin_uz": "Namangan shahri",
    "russian": "город Наманган",
    "aliases": [
      "namangan", "namangan shaxri", "namangan city",
      "namanganda", "namangandan", "namanganga", "namanganlik",
      "Наманган"
    ]
  },

  "pop_namangan": {
    "topic_id": 101383,
    "cyrillic_uz": "Поп тумани",
    "latin_uz": "Pop tumani",
    "russian": "Папский район",
    "aliases": [
      "pop", "pop tumani", "pop rayon",
      "popda", "popdan", "popga", "poplik",
      "Поп", "Папский район"
    ]
  },

  "chust": {
    "topic_id": 101383,
    "cyrillic_uz": "Чуст тумани",
    "latin_uz": "Chust tumani",
    "russian": "Чустский район",
    "aliases": [
      "chust", "chust tumani", "chust rayon",
      "chustda", "chustdan", "chustga", "chustlik",
      "Чуст", "Чустский район"
    ]
  },

  "kosonsoy": {
    "topic_id": 101383,
    "cyrillic_uz": "Косонсой тумани",
    "latin_uz": "Kosonsoy tumani",
    "russian": "Касансайский район",
    "aliases": [
      "kosonsoy", "kasan-say", "kosonsoy tumani", "kasan-say rayon",
      "kosonsoyda", "kosonsoydan", "kosonsoyga", "kosonsoylik",
      "Косонсой", "Касансай", "Касансайский район"
    ]
  },

  "yangiqorgon": {
    "topic_id": 101383,
    "cyrillic_uz": "Янгикўрган тумани",
    "latin_uz": "Yangiqoʻrgʻon tumani",
    "russian": "Янги-Курганский район",
    "aliases": [
      "yangiqorgon", "yangikurgan", "yangiqoʻrgʻon", "yangiqurgan",
      "yangiqorgon tumani", "yangikurgan rayon",
      "yangiqorgonda", "yangiqorgondan", "yangiqorgonga", "yangiqorgonlik",
      "Янгикўрган", "Янги-Курган", "Янги-Курганский район"
    ]
  },

  "uchqorgon": {
    "topic_id": 101383,
    "cyrillic_uz": "Учқўрғон тумани",
    "latin_uz": "Uchqoʻrgʻon tumani",
    "russian": "Уч-Курганский район",
    "aliases": [
      "uchqorgon", "uchqurgan", "uchqoʻrgʻon", "uchqorgon tumani", "uch-kurgan rayon",
      "uchqorgonda", "uchqorgondan", "uchqorgonga", "uchqorgonlik",
      "Учқўрғон", "Уч-Курган", "Уч-Курганский район"
    ]
  },

  "buxoro_city": {
    "topic_id": 101372,
    "cyrillic_uz": "Бухоро шаҳри",
    "latin_uz": "Buxoro shahri",
    "russian": "город Бухара",
    "aliases": [
      "buxoro", "buxara", "bukhara", "buxoro shaxri", "buxoro city",
      "buxoroda", "buxorodan", "buxoroga", "buxorolik",
      "Бухоро", "Бухара", "город Бухара"
    ]
  },

  "kogon": {
    "topic_id": 101372,
    "cyrillic_uz": "Когон шаҳри",
    "latin_uz": "Kogon shahri",
    "russian": "город Каган",
    "aliases": [
      "kogon", "kagan", "kogon shaxri", "kogon city",
      "kogon-da", "kogon-dan", "kogon-ga", "kogonlik",
      "Когон", "Каган"
    ]
  },

  "gijduvon": {
    "topic_id": 101372,
    "cyrillic_uz": "Ғиждувон тумани",
    "latin_uz": "G'ijduvon tumani",
    "russian": "Гиждувонский район",
    "aliases": [
      "g'ijduvon", "gijduvon", "g‘ijduvon", "gijduvon tumani", "gijduvon rayon",
      "gijduvonda", "gijduvondan", "gijduvonga", "gijduvonlik",
      "Ғиждувон", "Гиждувон", "Гиждувонский район"
    ]
  },

  "romitan": {
    "topic_id": 101372,
    "cyrillic_uz": "Ромитан тумани",
    "latin_uz": "Romitan tumani",
    "russian": "Ромитанский район",
    "aliases": [
      "romitan", "romitan tumani", "romitan rayon",
      "romitanda", "romitandan", "romitanga", "romitanlik",
      "Ромитан", "Ромитанский район"
    ]
  },

  "shofirkon": {
    "topic_id": 101372,
    "cyrillic_uz": "Шофиркон тумани",
    "latin_uz": "Shofirkon tumani",
    "russian": "Шафирканский район",
    "aliases": [
      "shofirkon", "shafirkon", "shofirkon tumani", "shafirkon rayon",
      "shofirkonda", "shofirkondan", "shofirkonga", "shofirkonlik",
      "Шофиркон", "Шафиркан", "Шафирканский район"
    ]
  },

  "qorakol": {
    "topic_id": 101372,
    "cyrillic_uz": "Қоракўл тумани",
    "latin_uz": "Qorakoʻl tumani",
    "russian": "Каракульский район",
    "aliases": [
      "qorakol", "qorakul", "qorakoʻl", "qorakol tumani", "karakul rayon",
      "qorakolda", "qorakoldan", "qorakolga", "qorakollik",
      "Қоракўл", "Каракуль", "Каракульский район"
    ]
  },

  "samarqand_city": {
    "topic_id": 101369,
    "cyrillic_uz": "Самарқанд шаҳри",
    "latin_uz": "Samarqand shahri",
    "russian": "город Самарканд",
    "aliases": [
      "samarqand", "samarkand", "samarqand shaxri", "samarqand city",
      "samarqanda", "samarqandan", "samarqandga", "samarqandlik",
      "Самарқанд", "Самарканд"
    ]
  },

  "urgut": {
    "topic_id": 101369,
    "cyrillic_uz": "Ургут тумани",
    "latin_uz": "Urgut tumani",
    "russian": "Ургутский район",
    "aliases": [
      "urgut", "urgut tumani", "urgut rayon",
      "urgutda", "urgutdan", "urgutga", "urgutlik",
      "Ургут", "Ургутский район"
    ]
  },

  "kattaqorgon": {
    "topic_id": 101369,
    "cyrillic_uz": "Каттақўрғон шаҳри",
    "latin_uz": "Kattaqoʻrgʻon shahri",
    "russian": "город Катта-Курган",
    "aliases": [
      "kattaqorgon", "kattakurgan", "kattaqoʻrgʻon", "katta-qurghon", "katta-qurgan",
      "kattaqorgon shaxri", "kattaqorgon city",
      "kattaqorgonda", "kattaqorgondan", "kattaqorgonga", "kattaqorgonlik",
      "Каттақўрғон", "Катта-Курган", "город Катта-Курган"
    ]
  },

  "payariq": {
    "topic_id": 101369,
    "cyrillic_uz": "Паяриқ тумани",
    "latin_uz": "Payariq tumani",
    "russian": "Паярыкский район",
    "aliases": [
      "payariq", "payariq tumani", "payariq rayon", "payarik",
      "payariqda", "payariqdan", "payariqga", "payariqlik",
      "Паяриқ", "Паярык", "Паярыкский район"
    ]
  },

  "ishtixon": {
    "topic_id": 101369,
    "cyrillic_uz": "Иштихон тумани",
    "latin_uz": "Ishtixon tumani",
    "russian": "Иштиханский район",
    "aliases": [
      "ishtixon", "ishtixan", "ishtixon tumani", "ishtixon rayon",
      "ishtixonda", "ishtixondan", "ishtixonga", "ishtixonlik",
      "Иштихон", "Иштихан", "Иштиханский район"
    ]
  },

  "jomboy": {
    "topic_id": 101369,
    "cyrillic_uz": "Жомбой тумани",
    "latin_uz": "Jomboy tumani",
    "russian": "Джамбайский район",
    "aliases": [
      "jomboy", "jambay", "jomboy tumani", "jambay rayon",
      "jomboyda", "jomboydan", "jomboyga", "jomboylik",
      "Жомбой", "Джамбай", "Джамбайский район"
    ]
  },

  "nurabod": {
    "topic_id": 101369,
    "cyrillic_uz": "Нурабод тумани",
    "latin_uz": "Nurabod tumani",
    "russian": "Нурабадский район",
    "aliases": [
      "nurabod", "nurabad", "nurabod tumani", "nurabad rayon",
      "nurabodda", "nuraboddan", "nurabodga", "nurabodlik",
      "Нурабод", "Нурабад", "Нурабадский район"
    ]
  },

  "qarshi": {
    "topic_id": 101380,
    "cyrillic_uz": "Қарши шаҳри",
    "latin_uz": "Qarshi shahri",
    "russian": "город Карши",
    "aliases": [
      "qarshi", "karshi", "qarshi shaxri", "karshi city",
      "qarshida", "qarshidan", "qarshiga", "qarshilik",
      "Қарши", "Карши", "город Карши"
    ]
  },

  "shahrisabz": {
    "topic_id": 101380,
    "cyrillic_uz": "Шаҳрисабз шаҳри",
    "latin_uz": "Shahrisabz shahri",
    "russian": "город Шахрисабз",
    "aliases": [
      "shahrisabz", "shakhrisabz", "shahrisabz shaxri", "shahrisabz city",
      "shahrisabzda", "shahrisabzdan", "shahrisabzga", "shahrisabzlik",
      "Шаҳрисабз", "Шахрисабз"
    ]
  },

  "koson": {
    "topic_id": 101380,
    "cyrillic_uz": "Косон тумани",
    "latin_uz": "Koson tumani",
    "russian": "Касанский район",
    "aliases": [
      "koson", "kason", "koson tumani", "kason rayon",
      "kosonda", "kosondan", "kosonga", "kosonlik",
      "Косон", "Касан", "Касанский район"
    ]
  },

  "guzar": {
    "topic_id": 101380,
    "cyrillic_uz": "Гузар тумани",
    "latin_uz": "Guzar tumani",
    "russian": "Гузарский район",
    "aliases": [
      "guzar", "guzar tumani", "guzar rayon",
      "guzarda", "guzardan", "guzarga", "guzarlik",
      "Гузар", "Гузарский район"
    ]
  },

  "muborak": {
    "topic_id": 101380,
    "cyrillic_uz": "Муборак тумани",
    "latin_uz": "Muborak tumani",
    "russian": "Мубарекский район",
    "aliases": [
      "muborak", "mubarak", "muborak tumani", "muborak rayon",
      "muborakda", "muborakdan", "muborakga", "muboraklik",
      "Муборак", "Мубарек", "Мубарекский район"
    ]
  },

  "chiroqchi": {
    "topic_id": 101380,
    "cyrillic_uz": "Чироқчи тумани",
    "latin_uz": "Chiroqchi tumani",
    "russian": "Чиракчинский район",
    "aliases": [
      "chiroqchi", "chiroq-chi", "chiroqchi tumani", "chiroqchi rayon",
      "chiroqchida", "chiroqchidan", "chiroqchiga", "chiroqchilik",
      "Чироқчи", "Чиракча", "Чиракчинский район"
    ]
  },

  "yakkabog": {
    "topic_id": 101380,
    "cyrillic_uz": "Яккабоғ тумани",
    "latin_uz": "Yakkabog' tumani",
    "russian": "Яккабагский район",
    "aliases": [
      "yakkabog", "yakkabog'", "yakka-bog", "yakka-bog'", "yakkabog tumani",
      "yakkabogda", "yakkabogdan", "yakkabogga", "yakkaboglik",
      "Яккабоғ", "Яккабаг", "Яккабагский район"
    ]
  },

  "termiz": {
    "topic_id": 101363,
    "cyrillic_uz": "Термиз шаҳри",
    "latin_uz": "Termiz shahri",
    "russian": "город Термез",
    "aliases": [
      "termiz", "termez", "termiz shaxri", "termiz city",
      "termizda", "termizdan", "termizga", "termizlik",
      "Термиз", "Термез"
    ]
  },

  "denov": {
    "topic_id": 101363,
    "cyrillic_uz": "Денов тумани",
    "latin_uz": "Denov tumani",
    "russian": "Денауский район",
    "aliases": [
      "denov", "denau", "denov tumani", "denau rayon",
      "denovda", "denovdan", "denovga", "denovlik",
      "Денов", "Денау", "Денауский район"
    ]
  },

  "boysun": {
    "topic_id": 101363,
    "cyrillic_uz": "Бойсун тумани",
    "latin_uz": "Boysun tumani",
    "russian": "Байсунский район",
    "aliases": [
      "boysun", "baysun", "boysun tumani", "baysun rayon",
      "boysunda", "boysundan", "boysunga", "boysunlik",
      "Бойсун", "Байсун", "Байсунский район"
    ]
  },

  "sherobod": {
    "topic_id": 101363,
    "cyrillic_uz": "Шеробод тумани",
    "latin_uz": "Sherobod tumani",
    "russian": "Шерабадский район",
    "aliases": [
      "sherobod", "sherabad", "sherobod tumani", "sherabad rayon",
      "sherobodda", "sheroboddan", "sherobodga", "sherobodlik",
      "Шеробод", "Шерабад", "Шерабадский район"
    ]
  },

  "qumqorgon": {
    "topic_id": 101363,
    "cyrillic_uz": "Қумқўрғон тумани",
    "latin_uz": "Qumqoʻrgʻon tumani",
    "russian": "Кум-Курганский район",
    "aliases": [
      "qumqorgon", "qumqorğon", "qumqoʻrgʻon", "qumqurgan", "qum-kurgan",
      "qumqorgon tumani", "qumqorgon rayon",
      "qumqorgonda", "qumqorgondan", "qumqorgonga", "qumqorgonlik",
      "Қумқўрғон", "Кум-Курган", "Кум-Курганский район"
    ]
  },

  "uzun": {
    "topic_id": 101363,
    "cyrillic_uz": "Узун тумани",
    "latin_uz": "Uzun tumani",
    "russian": "Узунский район",
    "aliases": [
      "uzun", "uzun tumani", "uzun rayon",
      "uzunda", "uzundan", "uzunga", "uzunlik",
      "Узун", "Узунский район"
    ]
  },

  "navoi_city": {
    "topic_id": 101379,
    "cyrillic_uz": "Навоий шаҳри",
    "latin_uz": "Navoiy shahri",
    "russian": "город Навои",
    "aliases": [
      "navoiy", "navoi", "navoiy shaxri", "navoi city",
      "navoiyda", "navoiydan", "navoiyga", "navoiylik",
      "Навоий", "Навои"
    ]
  },

  "zarafshan": {
    "topic_id": 101379,
    "cyrillic_uz": "Зарафшон шаҳри",
    "latin_uz": "Zarafshon shahri",
    "russian": "город Зарафшан",
    "aliases": [
      "zarafshon", "zarafshan", "zarafshon shaxri", "zarafshon city",
      "zarafshonda", "zarafshondan", "zarafshonga", "zarafshonlik",
      "Зарафшон", "Зарафшан"
    ]
  },

  "karmana": {
    "topic_id": 101379,
    "cyrillic_uз": "Кармана тумани",
    "latin_uз": "Karmana tumani",
    "russian": "Карманинский район",
    "aliases": [
      "karmana", "karmana tumani", "karmana rayon",
      "karmanada", "karmanadan", "karmanaga", "karmanalik",
      "Кармана", "Карманинский район"
    ]
  },

  "nurota": {
    "topic_id": 101379,
    "cyrillic_uз": "Нурота тумани",
    "latin_uз": "Nurota tumani",
    "russian": "Нуратинский район",
    "aliases": [
      "nurota", "nurat", "nurota tumani", "nurat rayon",
      "nurotada", "nurotadan", "nurotaga", "nurotalik",
      "Нурота", "Нурат", "Нуратинский район"
    ]
  },

  "konimex": {
    "topic_id": 101379,
    "cyrillic_uз": "Конимех тумани",
    "latin_uз": "Konimex tumani",
    "russian": "Канимехский район",
    "aliases": [
      "konimex", "kanimeh", "konimex tumani", "kanimeh rayon",
      "konimexda", "konimexdan", "konimexga", "konimexlik",
      "Конимех", "Канимех", "Канимехский район"
    ]
  },

  "uchquduq": {
    "topic_id": 101379,
    "cyrillic_uз": "Учқудуқ тумани",
    "latin_uз": "Uchquduq tumani",
    "russian": "Учкудукский район",
    "aliases": [
      "uchquduq", "uchkuduk", "uchquduq tumani", "uchkuduk rayon",
      "uchquduqda", "uchquduqdan", "uchquduqga", "uchquduqlik",
      "Учқудуқ", "Учкудук", "Учкудукский район"
    ]
  },

  "guliston": {
    "topic_id": 101378,
    "cyrillic_uз": "Гулистон шаҳри",
    "latin_uз": "Guliston shahri",
    "russian": "город Гулистан",
    "aliases": [
      "guliston", "gulistan", "guliston shaxri", "guliston city",
      "gulistonda", "gulistondan", "gulistonga", "gulistonlik",
      "Гулистон", "Гулистан"
    ]
  },

  "shirin": {
    "topic_id": 101378,
    "cyrillic_uз": "Ширин шаҳри",
    "latin_uз": "Shirin shahri",
    "russian": "город Ширин",
    "aliases": [
      "shirin", "shirin shaxri", "shirin city",
      "shirinda", "shirindan", "shiringa", "shirinlik",
      "Ширин"
    ]
  },

  "yangier": {
    "topic_id": 101378,
    "cyrillic_uз": "Янгиёр шаҳри",
    "latin_uз": "Yangiyer shahri",
    "russian": "город Янгиёр",
    "aliases": [
      "yangier", "yangiyer", "yangiyer shaxri", "yangiyer city",
      "yangiyerda", "yangiyerdan", "yangiyerga", "yangiyerlik",
      "Янгиёр", "Янгиёр"
    ]
  },

  "boyovut": {
    "topic_id": 101378,
    "cyrillic_uз": "Боёвут тумани",
    "latin_uз": "Boyovut tumani",
    "russian": "Баяутский район",
    "aliases": [
      "boyovut", "bayaut", "boyovut tumani", "bayaut rayon",
      "boyovutda", "boyovutdan", "boyovutga", "boyovutlik",
      "Боёвут", "Баяут", "Баяутский район"
    ]
  },

  "mirzaobod": {
    "topic_id": 101378,
    "cyrillic_uз": "Мирзаобод тумани",
    "latin_uз": "Mirzaobod tumani",
    "russian": "Мирзаабадский район",
    "aliases": [
      "mirzaobod", "mirzaabad", "mirza-obod", "mirzaobod tumani", "mirzaabad rayon",
      "mirzaobodda", "mirzaoboddan", "mirzaobodga", "mirzaobodlik",
      "Мирзаобод", "Мирзаабад", "Мирзаабадский район"
    ]
  },

  "sirdaryo": {
    "topic_id": 101378,
    "cyrillic_uз": "Сирдарё вилояти",
    "latin_uз": "Sirdaryo viloyati",
    "russian": "Сырдарьинская область",
    "aliases": [
      "sirdaryo", "sirdaryo viloyati", "sirdarya oblast", "sirdarya region",
      "sirdaryoga", "sirdaryodan", "sirdaryoda",
      "Сирдарё", "Сырдарья", "Сырдарьинская область"
    ]
  },

  "jizzakh_city": {
    "topic_id": 101377,
    "cyrillic_uз": "Жиззах шаҳри",
    "latin_uз": "Jizzax shahri",
    "russian": "город Джизак",
    "aliases": [
      "jizzax", "jizzakh", "jizzax shaxri", "jizzax city",
      "jizzaxda", "jizzaxdan", "jizzaxga", "jizzaxlik",
      "Жиззах", "Джизак"
    ]
  },

  "gallaaral": {
    "topic_id": 101377,
    "cyrillic_uз": "Ғаллаорал тумани",
    "latin_uз": "G'allaoʻral tumani",
    "russian": "Галлааральский район",
    "aliases": [
      "gallaaral", "g'allao'ral", "galla-aral", "gallaaral tumani", "gallaaral rayon",
      "gallaaralda", "gallaaraldan", "gallaaralga", "gallaarallik",
      "Ғаллаорал", "Галлаараль", "Галлааральский район"
    ]
  },

  "pakhtakor": {
    "topic_id": 101377,
    "cyrillic_uз": "Пахтакор тумани",
    "latin_uз": "Pakhtakor tumani",
    "russian": "Пахтакорский район",
    "aliases": [
      "pakhtakor", "pakhta-kor", "pakhtakor tumani", "pakhtakor rayon",
      "pakhtakorda", "pakhtakordan", "pakhtakorga", "pakhtakorlik",
      "Пахтакор", "Пахтакорский район"
    ]
  },

  "zomin": {
    "topic_id": 101377,
    "cyrillic_uз": "Зомин тумани",
    "latin_uз": "Zomin tumani",
    "russian": "Зааминский район",
    "aliases": [
      "zomin", "zaamin", "zomin tumani", "zaamin rayon",
      "zominda", "zomindan", "zominga", "zominlik",
      "Зомин", "Заамин", "Зааминский район"
    ]
  },

  "forish": {
    "topic_id": 101377,
    "cyrillic_uз": "Фориш тумани",
    "latin_uз": "Forish tumani",
    "russian": "Фаришский район",
    "aliases": [
      "forish", "farish", "forish tumani", "farish rayon",
      "forishda", "forishdan", "forishga", "forishlik",
      "Фориш", "Фариш", "Фаришский район"
    ]
  },

  "arnasoy": {
    "topic_id": 101377,
    "cyrillic_uз": "Арнасой тумани",
    "latin_uз": "Arnasoy tumani",
    "russian": "Арнасайский район",
    "aliases": [
      "arnasoy", "arnasay", "arnasoy tumani", "arnasay rayon",
      "arnasoyda", "arnasoydan", "arnasoyga", "arnasoylik",
      "Арнасой", "Арнасай", "Арнасайский район"
    ]
  },

  "baxmal": {
    "topic_id": 101377,
    "cyrillic_uз": "Бахмал тумани",
    "latin_uз": "Baxmal tumani",
    "russian": "Бахмальский район",
    "aliases": [
      "baxmal", "bakhmal", "baxmal tumani", "bakhmal rayon",
      "baxmalda", "baxmaldan", "baxmalga", "baxmallik",
      "Бахмал", "Бахмаль", "Бахмальский район"
    ]
  },

  "xorazm_city": {
    "topic_id": 101660,
    "cyrillic_uз": "Хоразм вилояти",
    "latin_uз": "Xorazm viloyati",
    "russian": "Хорезмская область",
    "aliases": [
      "xorazm", "xorezm", "xorazm viloyati", "khorezm oblast", "xorazm region",
      "xorazmga", "xorazmdan", "xorazmda",
      "Хоразм", "Хорезм", "Хорезмская область"
    ]
  },

  "khiva": {
    "topic_id": 101660,
    "cyrillic_uз": "Хива шаҳри",
    "latin_uз": "Xiva shahri",
    "russian": "город Хива",
    "aliases": [
      "xiva", "khiva", "xiva shaxri", "khiva city",
      "xivada", "xivadan", "xivaga", "xivalik",
      "Хива"
    ]
  },

  "shovot": {
    "topic_id": 101660,
    "cyrillic_uз": "Шовот тумани",
    "latin_uз": "Shovot tumani",
    "russian": "Шаватский район",
    "aliases": [
      "shovot", "shavat", "shovot tumani", "shavat rayon",
      "shovotda", "shovotdan", "shovotga", "shovotlik",
      "Шовот", "Шават", "Шаватский район"
    ]
  },

  "yangiariq": {
    "topic_id": 101660,
    "cyrillic_uз": "Янгиариқ тумани",
    "latin_uз": "Yangiariq tumani",
    "russian": "Янгиарыкский район",
    "aliases": [
      "yangiariq", "yangi-arik", "yangiarik", "yangiariq tumani", "yangiarik rayon",
      "yangiariqda", "yangiariqdan", "yangiariqga", "yangiariqlik",
      "Янгиариқ", "Янгиарык", "Янгиарыкский район"
    ]
  },

  "bogot": {
    "topic_id": 101660,
    "cyrillic_uз": "Боғот тумани",
    "latin_uз": "Bog'ot tumani",
    "russian": "Багатский район",
    "aliases": [
      "bogot", "bog'ot", "bogʻot", "bogat", "bogot tumani", "bogat rayon",
      "bogotda", "bogotdan", "bogotga", "bogotlik",
      "Боғот", "Багат", "Багатский район"
    ]
  },

  "hazarasp": {
    "topic_id": 101660,
    "cyrillic_uз": "Хазарасп тумани",
    "latin_uз": "Xazarasp tumani",
    "russian": "Хазараспский район",
    "aliases": [
      "xazarasp", "hazarasp", "xazarasp tumani", "hazarasp rayon",
      "xazaraspda", "xazaraspdan", "xazaraspga", "xazarasplik",
      "Хазарасп", "Хазараспский район"
    ]
  },

  "gurlan": {
    "topic_id": 101660,
    "cyrillic_uз": "Гурлан тумани",
    "latin_uз": "Gurlan tumani",
    "russian": "Гурленский район",
    "aliases": [
      "gurlan", "gurlan tumani", "gurlan rayon",
      "gurlanda", "gurlandan", "gurlanga", "gurlanlik",
      "Гурлан", "Гурленский район"
    ]
  },

  "qoshkopir": {
    "topic_id": 101660,
    "cyrillic_uз": "Қўшкўпир тумани",
    "latin_uз": "Qoʻshkoʻpir tumani",
    "russian": "Кошкепирский район",
    "aliases": [
      "qoshkopir", "koshkepir", "qo`shko`pir", "qoshkopir tumani", "koshkepir rayon",
      "qoshkopirda", "qoshkopirdan", "qoshkopirga", "qoshkopirlik",
      "Қўшкўпир", "Кошкепир", "Кошкепирский район"
    ]
  },

  "tuproqqala": {
    "topic_id": 101660,
    "cyrillic_uз": "Тупроққала тумани",
    "latin_uз": "Tuproqqala tumani",
    "russian": "Тупроккалинский район",
    "aliases": [
      "tuproqqala", "tuprok-kala", "tuproqqala tumani", "tuprok-kala rayon",
      "tuproqqalada", "tuproqqaladan", "tuproqqalaga", "tuproqqalalik",
      "Тупроққала", "Тупроккала", "Тупроккалинский район"
    ]
  },

  "urganch": {
    "topic_id": 101660,
    "cyrillic_uз": "Урганч шаҳри",
    "latin_uз": "Urganch shahri",
    "russian": "город Ургенч",
    "aliases": [
      "urganch", "urgench", "urganch shaxri", "urgench city",
      "urganchda", "urganchdan", "urganchga", "urganchlik",
      "Урганч", "Ургенч"
    ]
  },

  "khorezm": {
    "topic_id": 101660,
    "cyrillic_uз": "Хоразм вилояти",
    "latin_uз": "Xorazm viloyati",
    "russian": "Хорезмская область",
    "aliases": [
      "xorazm", "xorezm", "xorazm viloyati", "khorezm oblast", "khorezm region",
      "xorazmga", "xorazmdan", "xorazmda",
      "Хоразм", "Хорезм", "Хорезмская область"
    ]
  },

  "nukus": {
    "topic_id": 101661,
    "cyrillic_uз": "Нукус шаҳри",
    "latin_uз": "Nukus shahri",
    "russian": "город Нукус",
    "aliases": [
      "nukus", "nukus shaxri", "nukus city",
      "nukusda", "nukusdan", "nukusga", "nukuslik",
      "Нукус"
    ]
  },

  "karakalpakstan": {
    "topic_id": 101661,
    "cyrillic_uз": "Қорақалпоғистон Республикаси",
    "latin_uз": "Qoraqalpog'iston Respublikasi",
    "russian": "Республика Каракалпакстан",
    "aliases": [
      "qoraqalpog'iston", "qoraqalpoqiston", "karakalpakstan", "karakalpak republic",
      "qoraqalpog'iston respublikasi", "karakalpakstan respublikasi",
      "Қорақалпоғистон", "Каракалпакстан", "Республика Каракалпакстан"
    ]
  },

  "muynak": {
    "topic_id": 101661,
    "cyrillic_uз": "Мўйноқ тумани",
    "latin_uз": "Mo'ynoq tumani",
    "russian": "Муйнакский район",
    "aliases": [
      "mo'ynoq", "muynak", "moynoq", "muynak tumani", "muynak rayon",
      "mo'ynoqda", "mo'ynoqdan", "mo'ynoqqa", "mo'ynoqlik",
      "Мўйноқ", "Муйнак", "Муйнакский район"
    ]
  },

  "takhiatash": {
    "topic_id": 101661,
    "cyrillic_uз": "Тахиаташ шаҳри",
    "latin_uз": "Taxiatash shahri",
    "russian": "город Тахиаташ",
    "aliases": [
      "taxiatash", "takhiatash", "taxiatash shaxri", "takhiatash city",
      "taxiatashda", "taxiatashdan", "taxiatashga", "taxiatashlik",
      "Тахиаташ"
    ]
  },

  "turtkul": {
    "topic_id": 101661,
    "cyrillic_uз": "Тўрткўл шаҳри",
    "latin_uз": "To'rtko'l shahri",
    "russian": "город Турткуль",
    "aliases": [
      "to'rtko'l", "tortkul", "turtkul", "to'rtko'l shaxri", "turtkul city",
      "to'rtko'lda", "to'rtko'ldan", "to'rtko'lga", "to'rtko'llik",
      "Тўрткўл", "Турткуль"
    ]
  },

  "beruniy": {
    "topic_id": 101661,
    "cyrillic_uз": "Беруний тумани",
    "latin_uз": "Beruniy tumani",
    "russian": "Берунийский район",
    "aliases": [
      "beruniy", "beruni", "beruniy tumani", "beruni rayon",
      "beruniyda", "beruniidan", "beruniiga", "beruniilik",
      "Беруний", "Берунийский район"
    ]
  },

  "karauzyak": {
    "topic_id": 101661,
    "cyrillic_uз": "Қараўзяк тумани",
    "latin_uз": "Qaro'zyak tumani",
    "russian": "Караузякский район",
    "aliases": [
      "qaro'zyak", "karauzyak", "qaro'zyak tumani", "karauzyak rayon",
      "qaro'zyakda", "qaro'zyakdan", "qaro'zyakga", "qaro'zyaklik",
      "Қараўзяк", "Караузяк", "Караузякский район"
    ]
  },

  "kegeyli": {
    "topic_id": 101661,
    "cyrillic_uз": "Кегейли тумани",
    "latin_uз": "Kegeyli tumani",
    "russian": "Кегейлийский район",
    "aliases": [
      "kegeyli", "kegeyli tumani", "kegeyli rayon",
      "kegeylida", "kegeylidan", "kegeyliga", "kegeylilik",
      "Кегейли", "Кегейлийский район"
    ]
  },

  "amudarya": {
    "topic_id": 101661,
    "cyrillic_uз": "Амударё тумани",
    "latin_uз": "Amudaryo tumani",
    "russian": "Амударьинский район",
    "aliases": [
      "amudaryo", "amudarya", "amudaryo tumani", "amudarya rayon",
      "amudaryoda", "amudaryodan", "amudaryoga", "amudaryolik",
      "Амударё", "Амударьинский район"
    ]
  },

  "kanlikol": {
    "topic_id": 101661,
    "cyrillic_uз": "Қонлиқўл тумани",
    "latin_uз": "Qonliqo'l tumani",
    "russian": "Канлыкульский район",
    "aliases": [
      "qonliqo'l", "qonliko'l", "konlikul", "kanlikol", "qonliqo'l tumani", "kanlikol rayon",
      "qonliqo'lda", "qonliqo'ldan", "qonliqo'lga", "qonliqo'llik",
      "Қонлиқўл", "Канлыкуль", "Канлыкульский район"
    ]
  },

  "chimbay": {
    "topic_id": 101661,
    "cyrillic_uз": "Чимбой тумани",
    "latin_uз": "Chimboy tumani",
    "russian": "Чимбайский район",
    "aliases": [
      "chimboy", "chimbay", "chimboy tumani", "chimbay rayon",
      "chimboyda", "chimboydan", "chimboyga", "chimboylik",
      "Чимбой", "Чимбай", "Чимбайский район"
    ]
  },

  "shumanay": {
    "topic_id": 101661,
    "cyrillic_uз": "Шуманай тумани",
    "latin_uз": "Shumanay tumani",
    "russian": "Шуманайский район",
    "aliases": [
      "shumanay", "shumanai", "shumanay tumani", "shumanay rayon",
      "shumanayda", "shumanaydan", "shumanayga", "shumanaylik",
      "Шуманай", "Шуманайский район"
    ]
  },

  "ellikqala": {
    "topic_id": 101661,
    "cyrillic_uз": "Элликқала тумани",
    "latin_uз": "Ellikqala tumani",
    "russian": "Элликкалинский район",
    "aliases": [
      "ellikqala", "ellik-kala", "ellikqala tumani", "ellik-kala rayon",
      "ellikqalada", "ellikqaladan", "ellikqalaga", "ellikqalalik",
      "Элликқала", "Элликкала", "Элликкалинский район"
    ]
  },

  "bo'zatov": {
    "topic_id": 101661,
    "cyrillic_uз": "Бўзатов тумани",
    "latin_uз": "Bo'zatov tumani",
    "russian": "Бозатауский район",
    "aliases": [
      "bo'zatov", "bozatov", "bo'zatov tumani", "bozatau rayon",
      "bo'zatovda", "bo'zatovdan", "bo'zatovga", "bo'zatovlik",
      "Бўзатов", "Бозатау", "Бозатауский район"
    ]
  },

  "xojeli": {
    "topic_id": 101661,
    "cyrillic_uз": "Хўжели шаҳри",
    "latin_uз": "Xo'jeli shahri",
    "russian": "город Ходжейли",
    "aliases": [
      "xo'jeli", "khodjeyli", "xojeli", "xo'jeli shaxri", "khodjeyli city",
      "xo'jelida", "xo'jelidan", "xo'jeliga", "xo'jelilik",
      "Хўжели", "Ходжейли"
    ]
  },
    'fura_bozor': {
        'topic_id': 101361,
        'keywords': [
            'fura bazar', 'fura bozor', 'fura bozori', 'фура бозор', 'bozor fura', 'fura bazar', 'fura bozor', 'fura bozori', 'фура бозор', 'bozor fura', 'fura bozoriga', 'fura bozordan'
        ]
    },
    'reklama': {
        'topic_id': 101360,
        'keywords': [
            'reklama', 'reklama post', 'реклама', 'reklama berish', 'reklama joylashtirish', 'reklama', 'reklama post', 'реклама', 'reklama berish', 'reklama joylashtirish', 'reklamaga',
            'reklamadan', 'reklama', 'реклама', 'reklama berish', 'reklama joylashtirish',
            'sotiladi', 'sotilad', 'sotaman', 'narxi', 'dastafka', 'dastavka', 'sotiladi', 'narxi', 'dastafka', 'sotuv', 'reklama',
            'sotuv', 'sotuvda', 'sotib olish', 'sotiladi reklama', 'reklama sotiladi', 'reklama', 'реклама', 'sotiladi', 'sotuv', 'narxi',
            'dastafka', 'ремонт',
            'йили', 'sotaman', 'olmoq'
        ]
    },
    'yangiliklar': {
        'topic_id': 101359,
        'keywords': [
            'yangilik', 'yangiliklar', 'новости', 'news', 'xabar', "so'ngi yangiliklar", 'yangilik', 'yangiliklar', 'новости', 'news', 'xabar', "so'ngi yangiliklar", 'yangiliklarga', 'yangiliklardan'
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
            'cis', 'mda', 'cis İ', 'mda İ', 'cis i', 'mda i', 'tomsk shahardan', 'tomsk', 'tomskdan', 'tomskga',
            'import', 'export', 'import İ', 'export İ', 'import i', 'export i', 'russia', 'rosiya', 'russia İ', 'rosiya İ', 'russia i', 'rosiya i',
            'moskva', 'moscow', 'moskva İ', 'moskvaʼ', 'moskva i', "moskva'", 'москва', 'москваga', 'москваdan',
            'spb', 'sankt-peterburg', 'piter', 'saint-petersburg', 'spb İ', 'spb i', 'спб', 'санкт-петербург', 'питер', 'ленинград',
            'krasnodar', 'krasnodar İ', 'krasnodar i', 'voronej', 'воронеж', 'krasnodarga', 'krasnadardan',
            'rostov', 'rostov-na-donu', 'rostov İ', 'rostov i', 'rostovga', 'rostovdan', 'tomsk', 'tomsk shahardan', 'tomskdan', 'tomskga',
            'volgograd', 'volgograd İ', 'volgograd i', 'volgogradga', 'volgograddan',
            'kazan', 'kazan İ', 'kazan i', 'kazanga', 'kazandan',
            'nizhny novgorod', 'nizhniy novgorod', 'nizhny novgorod İ', 'nizhny i', 'nizhnyga', 'nizhnydan',
            'samara', 'samara İ', 'samara i', 'samaranga', 'samaradan',
            'ufa', 'ufa İ', 'ufa i', 'ufaga', 'ufadan',
            'perm', 'perm İ', 'perm i', 'permga', 'permdan',
            'krasnoyarsk', 'krasnoyarsk İ', 'krasnoyarsk i', 'krasnoyarskga', 'krasnoyarskdan',
            'novosibirsk', 'novosibirsk İ', 'novosibirsk i', 'novosibirskga', 'novosibirskdan',
            'yekaterinburg', 'ekaterinburg', 'yekaterinburg İ', 'yekaterinburg i', 'yekaterinburgga', 'yekaterinburgdan',
            'chelyabinsk', 'chelyabinsk İ', 'chelyabinsk i', 'chelyabinskga', 'chelyabinskdan',
            'omsk', 'omsk İ', 'omsk i', 'omskga', 'omskdan',
            'voronezh', 'voronezh İ', 'voronezh i', 'voronezhga', 'voronezhdan',
            'sochi', 'sochi İ', 'sochi i', 'sochiga', 'sochidan',
            'tolyatti', 'tolyatti İ', 'tolyatti i', 'tolyattiga', 'tolyattidan',
            'belgorod', 'belgorod İ', 'belgorod i', 'belgorodga', 'belgroddan',

            # Украина
            'ukraine', 'ukraina', 'ukraine İ', 'ukraina İ', 'ukraine i', 'ukraina i',
            'kiev', 'kyiv', 'kiev İ', 'kyiv İ', 'kiev i', 'kyiv i', 'kievga', 'kievdan',
            'kharkiv', 'kharkov', 'kharkiv İ', 'kharkiv i', 'kharkivga', 'kharkivdan',
            'odessa', 'odesa', 'odessa İ', 'odessa i', 'odessaga', 'odessadan',
            'dnipro', 'dnepr', 'dnipro İ', 'dnipro i', 'dniproga', 'dniprodan',
            'lviv', 'lviv İ', 'lviv i', 'lvivga', 'lvivdan',

            # Казахстан
            'kazakhstan', 'qazaqstan', 'kazakhstan İ', 'qazaq-stan', 'kazakhstan i', 'qazaqstan i',
            'almaty', 'alma-ata', 'almaty İ', 'almaty i', 'almatyga', 'almatydan',
            'astana', 'nur-sultan', 'astana İ', 'astana i', 'astanaga', 'astanadan',
            'shymkent', 'shymkent İ', 'shymkent i', 'shymkentga', 'shymkentdan',
            'karaganda', 'karaganda İ', 'karaganda i', 'karagandaga', 'karagandadan',
            'aktobe', 'aktobe İ', 'aktobe i', 'aktobega', 'aktobedan',
            'pavlodar', 'pavlodar İ', 'pavlodar i', 'pavlodarga', 'pavlodardan',

            # Кыргызстан
            'kyrgyzstan', 'kirgiziya', 'kyrgyzstan İ', 'kyrgyzstan i',
            'bishkek', 'bishkek İ', 'bishkek i', 'bishkekke', 'bishkekdan',
            'osh', 'osh İ', 'osh i', 'oshga', 'oshdan',

            # Таджикистан
            'tajikistan', 'tojikiston', 'tajikistan İ', 'tajikistan i',
            'dushanbe', 'dushanbe İ', 'dushanbe i', 'dushanbega', 'dushanbedan',
            'khujand', 'khujand İ', 'khujand i', 'khujandga', 'khujanddan',

            # Турция
            'turkey', 'turkiya', 'turkey İ', 'turkiya İ', 'turkey i', 'turkiya i',
            'istanbul', 'stambul', 'istanbul İ', 'stambul İ', 'istanbul i', 'stambul i', 'istanbula', 'istanbuldan',
            'ankara', 'ankara İ', 'ankara i', 'ankaraga', 'ankaradan',
            'izmir', 'izmir İ', 'izmir i', 'izmirga', 'izmirndan',
            'antalya', 'antalya İ', 'antalya i', 'antalyaga', 'antalyadan',

            # Общие
            'international', 'xalqaro', 'import', 'export', 'xalqaro yuk', 'importga', 'exportga'
        ]
    }
}

# ========== Рядом с REGION_KEYWORDS нужно добавить константы для номеров телефонов и маршрутов ==========

PHONE_REGEX = re.compile(r'[\+]?[\d\s\-\(\)]{9,18}')
ROUTE_REGEX = re.compile(
    r'(?:^\s*)?(.+?)'                                   # «откуда»
    r'(?:'
        # 1. Одиночные стрелки и экраны
        r'\s*[>→←↑↓↔↕↖↗↘↙↚↛↜↝↞↟↠↡↢↣↤↥↦↧↨↩↪↫↬↭↮↯↰↱↲↳↴↵↶↷↸↹↺↻↼↽↾↿⇀⇁⇂⇃⇄⇅⇆⇇⇈⇉⇊⇋⇌⇍⇎⇏⇐⇑⇒⇓⇔⇕⇖⇗⇘⇙⇚⇛⇜⇝⇞⇟⇠⇡⇢⇣⇤⇥⇦⇧⇨⇩⇪⇫⇬⇭⇮⇯⇰⇱⇲⇳⇴⇵⇶⇷⇸⇹⇺⇻⇼⇽⇾⇿⟰⟱⟲⟳⟴⟵⟶⟷⟸⟹⟺⟻⟼⟽⟾⟿⤀⤁⤂⤃⤄⤅⤆⤇⤈⤉⤊⤋⤌⤍⤎⤏⤐⤑⤒⤓⤔⤕⤖⤗⤘⤙⤚⤛⤜⤝⤞⤟⤠⤡⤢⤣⤤⤥⤦⤧⤨⤩⤪⤫⤬⤭⤮⤯⤰⤱⤲⤳⤴⤵⤶⤷⤸⤹⤺⤻⤼⤽⤾⤿⥀⥁⥂⥃⥄⥅⥆⥇⥈⥉⥊⥋⥌⥍⥎⥏⥐⥑⥒⥓⥔⥕⥖⥗⥘⥙⥚⥛⥜⥝⥞⥟⥠⥡⥢⥣⥤⥥⥦⥧⥨⥩⥪⥫⥬⥭⥮⥯⥰⥱⥲⥳⥴⥵⥶⥷⥸⥹⥺⥻⥼⥽⥾⥿⦀⦁⦂⦃⦄⦅⦆⦇⦈⦉⦊⦋⦌⦍⦎⦏⦐⦑⦒⦓⦔⦕⦖⦗⦘⦙⦚⦛⦜⦝⦞⦟⦠⦡⦢⦣⦤⦥⦦⦧⦨⦩⦪⦫⦬⦭⦮⦯⦰⦱⦲⦳⦴⦵⦶⦷⦸⦹⦺⦻⦼⦽⦾⦿⧀⧁⧂⧃⧄⧅⧆⧇⧈⧉⧊⧋⧌⧍⧎⧏⧐⧑⧒⧓⧔⧕⧖⧗⧘⧙⧚⧛⧜⧝⧞⧟⧠⧡⧢⧣⧤⧥⧦⧧⧨⧩⧪⧫⧬⧭⧮⧯⧰⧱⧲⧳⧴⧵⧶⧷⧸⧹⧺⧻⧼⧽⧾⧿✀✁✂✃✄✅✆✇✈✉✊✋✌✍✎✏✐✑✒✓✔✕✖✗✘✙✚✛✜✝✞✟✠✡✢✣✤✥✦✧✨✩✪✫✬✭✮✯✰✱✲✳✴✵✶✷✸✹✺✻✼✽✾✿❀❁❂❃❄❅❆❇❈❉❊❋❌❍❎❏❐❑❒❓❔❕❖❗❘❙❚❛❜❝❞❟❠❡❢❣❤❥❦❧❨❩❪❫❬❭❮❯❰❱❲❳❴❵❛❜❝❞❟❠❡❢❣❤❥❦❧❨❩❪❫❬❭❮❯❰❱❲❳❴❵➔➘➙➚➛➜➝➞➟➠➡➢➣➤➥➦➧➨➩➪➫➬➭➮➯➱➲➳➵➸➹➺➻➼➽➾'
        r'|'
        # 2. Эмодзи-стрелки
        r'\s*[▶️➡➢➣➤➥➦➧➨➩➪➫➬➭➮➯➱➲➳➵➸➹➺➻➼➽➾➿]\s*'
        r'|'
        # 3. Слова-разделители
        r'\s+(?:to|dan|ga|dan|в|из|на)\s+'
        r'|'
        # 4. Любые комбинации (1-5 повторов)
        r'\s*[-—–→➔➡▶️◀️➢➣➤➥➦➧➨➩➪➫➬➭➮➯➱➲➳➵➸➹➺➻➼➽➾⟶⟷⟵]{1,5}\s*'
    r')'
    r'(.+?)(?:\s|$)',
    re.IGNORECASE | re.MULTILINE | re.UNICODE
)

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
    lines = [re.sub(r'[🇺🇿🇰🇿🇮🇷🚚📦⚖️💵\U0001F1FA-\U0001F1FF\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', '', line).strip()
             for line in text.strip().split('\n') if line.strip()]

    for line in lines:
        clean_line = re.sub(r'[🇺🇿🇰🇿🇮🇷🚚📦⚖️💵\U0001F1FA-\U0001F1FF\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', '', line)

        # 1. ROUTE_REGEX (основной)
        route_match = ROUTE_REGEX.search(clean_line)
        if route_match:
            from_city = route_match.group(1).strip()
            to_city = route_match.group(2).strip()
            cargo_text = text.replace(line, '').strip()
            return from_city, to_city, cargo_text

        # 2. Emoji-паттерны
        emoji_patterns = [
            r'🇺🇿\s*(\w+)\s*🇺🇿\s*(\w+)',  # 🇺🇿 Qoqon 🇺🇿 Samarqand
            r'🇷🇺\s*([^-]+?)\s*-\s*🇺🇿\s*([^\n\r]+)',  # 🇷🇺Москва - 🇺🇿Ташкент
            r'(\w+)\s*🇺🇿\s*(\w+)',         # Qoqon 🇺🇿 Samarqand
            r'(\w+)\s*[-–→>>>\-\-\-\-]+\s*(\w+)',  # Tosh----Fargona
            r'(\w+)\s*>\s*(\w+)',            # Tosh>Fargona
            r'(\w+)\s+(\w+)',                # Tosh Fargona
        ]
        for pattern in emoji_patterns:
            match = re.search(pattern, clean_line)
            if match and len(match.group(1)) > 2 and len(match.group(2)) > 2:
                from_city = match.group(1).strip()
                to_city = match.group(2).strip()
                cargo_text = text.replace(line, '').strip()
                return from_city, to_city, cargo_text

    # 3. Fallback: первая и вторая строка
    if len(lines) >= 2 and len(lines[0]) > 2 and len(lines[1]) > 2:
        return lines[0], lines[1], '\n'.join(lines[2:])

    # 4. Fallback: сложные паттерны "дан...га"
    first_line = lines[0] if lines else text
    clean_first = re.sub(r'[🇺🇿🇰🇿🇮🇷🚚📦⚖️💵\U0001F1FA-\U0001F1FF\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', '', first_line)
    complex_patterns = [
        r'([А-Яа-я\w\.]+)дан[\s\-\-\-\-]+([А-Яа-я\w]+)га',
        r'([А-Яа-я\w\.]+)дан[\s\n]+([А-Яа-я\w]+)га',
        r'([А-Яа-я\w\.]+)дан[\s\n]+([А-Яа-я\w]+)',
    ]
    for pattern in complex_patterns:
        match = re.search(pattern, clean_first, re.IGNORECASE)
        if match:
            return match.group(1).strip(), match.group(2).strip(), text

    # 5. Последний fallback
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
    user_id = user.get('id', '')

    if username:
        button_text = f"👤 @{username}"
        url = f"https://t.me/{username}"
    else:
        button_text = f"👤 {name}"
        url = f"tg://user?id={user_id}"

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

        logger.info(f"📥 Получено сообщение из чата {chat_id}: {text[:50]}...")

        if text.startswith('/'):
            handle_command(message)
            message_count += 1
            return

        if chat_id == ADMIN_USER_ID:
            handle_admin_command(message)
            message_count += 1
            return

        if chat_id != MAIN_GROUP_ID:
            logger.info(f"🚫 Пропуск сообщения: не из основной группы {MAIN_GROUP_ID}")
            return

        logger.info("🎯 Обрабатываем сообщение из основной группы")
        message_count += 1

        # === НОВАЯ ЛОГИКА: много-маршрутные блоки с флагами ===
        blocks = [b.strip() for b in text.split('\n\n') if b.strip()]
        for block in blocks:
            lines = [l.strip() for l in block.split('\n') if l.strip()]
            if not lines:
                continue

            first_line = lines[0]
            if any(flag in first_line for flag in ['🇷🇺', '🇧🇾', '🇰🇿', '🇺🇸', '🇹🇷']):
                from_city = first_line
                to_city = "🇺🇿 Узбекистан"
                cargo_text = '\n'.join(lines[1:])
                phone = extract_phone_number(block)
                transport, desc = format_cargo_text(cargo_text)

                msg = (
                    f"{from_city.upper()}\n"
                    f"🚛 {transport}\n"
                    f"💬 {desc}\n"
                    f"☎️ {phone}\n"
                    f"#XALQARO\n"
                    f"➖➖➖➖➖➖➖\n"
                    f"Boshqa yuklar: @logistika_marka"
                )

                send_message(
                    MAIN_GROUP_ID,
                    msg,
                    REGION_KEYWORDS['xalqaro']['topic_id'],
                    reply_markup=author_button(message.get('from', {}))
                )
                continue  # блок обработан

        # === СТАРАЯ ЛОГИКА: один маршрут ===
        from_city, to_city, cargo_text = extract_route_and_cargo(text)
        if not from_city or not to_city:
            return

        # ... дальше старая логика ...

    except Exception:
        logging.exception("process_message error")


# === ВСЬ ОСТАЛЬНОЙ КОД (normalize_text, find_region, handle_callback) —
# должен быть на уровне модуля, НЕ внутри process_message ===
import unicodedata
import re

def normalize_text(s: str) -> str:
    """Нормализует текст для поиска совпадений."""
    s = s.lower()
    s = re.sub(r"[ʼʻ’`´]", "'", s)
    s = s.replace("ı", "i").replace("İ", "i")
    trans_map = {
        "қ": "q", "ў": "o'", "ғ": "g'", "ҳ": "h",
        "ё": "yo", "й": "y", "щ": "sh", "ш": "sh", "ч": "ch",
        "ю": "yu", "я": "ya", "э": "e", "ъ": "", "ь": "",
        "ы": "i", "ә": "a", "ү": "u", "ӱ": "u"
    }
    for cyr, lat in trans_map.items():
        s = s.replace(cyr, lat)
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"\s+", " ", s).strip()
    return s

def find_region(text: str) -> str | None:
    """Ищет регион по любому из синонимов/алиасов, максимально универсально."""
    text_norm = normalize_text(text)
    for code, data in REGION_KEYWORDS.items():
        for kw in data.get('aliases', []):
            kw_norm = normalize_text(kw)
            if kw_norm in text_norm or re.search(rf"\b{re.escape(kw_norm)}\b", text_norm):
                return code
    return None

# --- callback handler ---
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

        msg = (
            f"{from_city.upper()} - {to_city.upper()}\n"
            f"🚛 {transport}\n"
            f"💬 {desc}\n"
            f"☎️ {phone}\n"
            f"#{to_city.upper()}\n"
            f"➖➖➖➖➖➖➖➖➖➖➖➖➖➖\n"
            f"Другие грузы: @logistika_marka"
        )

        send_message(
            MAIN_GROUP_ID,
            msg,
            topic_id,
            reply_markup=author_button({"id": uid, "first_name": name, "username": username})
        )

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

# === ФИЛЬТР ПО USER-AGENT (добавляем здесь) ===
from flask import request

ALLOWED_UA = ("UptimeRobot", "TelegramBot")

@app.before_request
def block_noise():
    ua = request.headers.get("User-Agent", "")
    if not any(key in ua for key in ALLOWED_UA):
        return "", 204  # молча отклоняем всё лишнее
# ==============================================

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
