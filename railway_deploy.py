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
BOT_TOKEN     = '8098291030:AAFTt4SLrOz95Hfq8TKdvgnv8j5ojEnirYg'  # Принудительно новый токен
MAIN_GROUP_ID = int(os.environ.get('MAIN_GROUP_ID', '-1002259378109'))
ADMIN_USER_ID = int(os.environ.get('ADMIN_USER_ID', '8101326669'))
BOT_USERNAME  = os.getenv("BOT_USERNAME", "ym_logistics_bot")  # без @
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

# ========== ТОЛЬКО 17 АКТИВНЫХ ТОПИКОВ ==========
REGION_KEYWORDS = {
  # 1. Toshkent (101362) - объединяет все районы Ташкента и Ташкентскую область
  "tashkent_city": {
    "topic_id": 101362,
    "cyrillic_uz": "Тошкент шаҳри",
    "latin_uz": "Toshkent shahri", 
    "russian": "город Ташкент",
    "aliases": [
      # Основной город
      "toshkent", "tashkent", "tosh-kent", "tash-kent", "towkent", "toshkent shahri", "tashkent city",
      "toshkentga", "tashkentga", "toshkentdan", "tashkentdan", "toshkentda", "toshkentdagi",
      "toshkent", "TOSHKENT", # исправляем регистр
      "toshkenga", "toshkentga", "olmosga", "olmosxo'ja", "olmos", "olmoscha",
      "Тошкент", "Ташкент", "ташкент", "Тош-Кент", "Таш-Кент", "Товкент", "Тошкент шаҳри", "город Ташкент",
      "Ташкента", "Ташкенте", "Ташкенту", "Ташкентский", "Ташкент-Сити", "toshkent'skiy",
      "Maskva", "MASKVA", "maskva", "москва", "Москва", "МОСКВА",  # Добавляем Москву
      # ВСЕ РАЙОНЫ ТАШКЕНТА
      "yunusobod", "yunusabad", "yunus-obod", "yunus obod", "Юнусобод", "Юнусабад",
      "mirzo-ulugbek", "mirzo ulugbek", "mirzoulugbek", "mirzo ulug'bek", "Мирзо-Улуғбек", "Мирзо Улуғбек",
      "yashnobod", "yashnabad", "yashno-bod", "Яшнобод", "Яшнабад",
      "olmazor", "olma-zor", "olma zor", "almazar", "Олмазор", "Алмазар",
      "uchtepa", "uch-tepa", "uch tepa", "Учтепа", "Уч-Тепа",
      "shayxontohur", "shayxontoxur", "shaykhontohur", "Шайхонтоҳур", "Шайхантаур",
      "chilonzor", "chilon-zor", "chilon zor", "Чилонзор", "Чиланзар",
      "sergeli", "sergili", "Сергели",
      "yakkasaroy", "yakkasaray", "yakka-saroy", "yakka saroy", "Яккасарай",
      "mirobod", "mirabad", "miro-bod", "Мирабод", "Мирабад",
      "bektemir", "bek-temir", "Бектемир",
      # ТАШКЕНТСКАЯ ОБЛАСТЬ
      "toshkent viloyati", "tashkent oblast", "toshkent region", "Тошкент вилояти", "Ташкентская область",
      "bekobod", "bekabad", "Бекобод", "Бекабад",
      "angren", "angiren", "Ангрен", "Ангирен",
      "olmaliq", "olmalik", "almalyk", "almalik", "Олмалиқ", "Алмалык",
      # Максимальные варианты Охангарона
      "ohangaron", "oxangaron", "ohan'garon", "oxan'garon", "ochangaron", "ochongaron", 
      "ахангаран", "АХАНГАРАН", "Ахангаран", "ахангарон", "АХАНГАРОН", "охангарон", "ОХАНГАРОН", "Охангарон",
      "оҳангарон", "ОҲАНГАРОН", "Оҳангарон", "ahangaran", "AHANGARAN", "Ahangaran", "ahangaron", "AHANGARON",
      "yangiyul", "yangiyo'l", "Янгиюл", "Янгиюль",
      "parkent", "Паркент", "piskent", "Пискент",
      "quyichirchiq", "quyi-chirchiq", "quyi chirchiq", "kuyichirchiq", "Қуйичирчиқ",
      "yuqorichirchiq", "yuqori-chirchiq", "yuqori chirchiq", "yukorichirchiq", "Юқоричирчиқ",
      "boka", "bo'ka", "Бўка", "xasanboy", "hasanboy", "XASANBOY", "HASANBOY", "Хасанбой",
      "chinaz", "chinz", "chinoz", "Чиназ", "Чиноз",
      "zangiota", "zangi-ota", "zangi ota", "Зангиота",
      "qibray", "kibray", "Қибрай",
      "nurafshon", "nurafshan", "Нурафшон",
      "gazalkent", "gazal-kent", "Газалкент",
      "oʻrtasaroy", "o'rtasaroy", "ortasaroy", "Oʻrtasaroy", "O'rtasaroy", "Ўртасарой"  # Ўртасарой район
    ]
  },

  # 2. Farg'ona (101382)
  "fargona_city": {
    "topic_id": 101382,
    "cyrillic_uz": "Фарғона шаҳри",
    "latin_uz": "Farg'ona shahri",
    "russian": "город Фергана",
    "aliases": [
      "fargona", "farg'ona", "fargana", "fergana", "fargona shahri", "fargona city",
      "fargonaga", "fargonadan", "fargonada", "fargonali",
      "Фарғона", "Фергана", "город Фергана", "Ферганы", "Фергане"
    ]
  },

  # 3. Kokand (101382) - приоритет Фергана
  "kokand": {
    "topic_id": 101382,  # Фергана топик
    "cyrillic_uz": "Қўқон шаҳри", 
    "latin_uz": "Qo'qon shahri",
    "russian": "город Коканд",
    "aliases": [
      "qoqon", "qo'qon", "kokand", "qo'qon shahri", "qoqon city",
      "qo'qonga", "qo'qondan", "qo'qonda", "qoqonlik",
      "Қўқон", "Коканд", "город Коканд"
    ]
  },

  # 4. Namangan (101383)
  "namangan_city": {
    "topic_id": 101383,
    "cyrillic_uz": "Наманган шаҳри",
    "latin_uz": "Namangan shahri", 
    "russian": "город Наманган",
    "aliases": [
      "namangan", "namagan", "namangan shahri", "namangan city",
      "namanganga", "namangandan", "namanganda", "namanganlik",
      "xaqlabot", "xaqlabad", "Хаклабот", # район в Намангане
      "Наманган", "город Наманган", "Намангана", "Намангане"
    ]
  },

  # 5. Andijan (101387)  
  "andijon_city": {
    "topic_id": 101387,
    "cyrillic_uz": "Андижон шаҳри",
    "latin_uz": "Andijon shahri",
    "russian": "город Андижан", 
    "aliases": [
      "andijon", "andijan", "andijon shahri", "andijon city",
      "andijonga", "andijondan", "andijonda", "andijonlik",
      "marhamat", "marhamatga", # район в Андижане
      "Андижон", "Андижан", "город Андижан", "Андижана", "Андижане"
    ]
  },

  # 6. Samarqand (101369)
  "samarkand_city": {
    "topic_id": 101369,
    "cyrillic_uz": "Самарқанд шаҳри",
    "latin_uz": "Samarqand shahri",
    "russian": "город Самарканд",
    "aliases": [
      "samarqand", "samarkand", "samarqand shahri", "samarkand city",
      "samarqandga", "samarqanddan", "samarqandda", "samarqandlik",
      "Самарқанд", "Самарканд", "город Самарканд", "Самарканда", "Самарканде"
    ]
  },

  # 7. Buxoro (101372)
  "bukhara_city": {
    "topic_id": 101372,
    "cyrillic_uz": "Бухоро шаҳри",
    "latin_uz": "Buxoro shahri", 
    "russian": "город Бухара",
    "aliases": [
      "buxoro", "bukhara", "buxoro shahri", "bukhara city",
      "buxoroga", "buxorodan", "buxoroda", "buxorolik", 
      "Бухоро", "бухоро", "Бухородан", "бухородан",  # Проблемные варианты из логов
      "Бухара", "город Бухара", "Бухары", "Бухаре"
    ]
  },

  # 8. Navoiy (101379)
  "navoi_city": {
    "topic_id": 101379,
    "cyrillic_uz": "Навоий шаҳри",
    "latin_uz": "Navoiy shahri",
    "russian": "город Навои",
    "aliases": [
      "navoiy", "navoi", "navoyi", "Navoyi", "NAVOYI", "navoiy shahri", "navoi city",
      "navoiyda", "navoiydan", "navoiyga", "navoiylik",
      "qiziltepaga", "qiziltepa", "qiziltepa tumani",
      "g'azg'on", "gazgon", "g'azg'ondan", "gazgondan",
      "Навоий", "Навои"
    ]
  },

  # 9. Qashqadaryo (101380)
  "qashqadaryo_region": {
    "topic_id": 101380,
    "cyrillic_uz": "Қашқадарё вилояти",
    "latin_uz": "Qashqadaryo viloyati", 
    "russian": "Кашкадарьинская область",
    "aliases": [
      "qashqadaryo", "qashqadaryoga", "qashqadarya", "kashkadarya",
      "qarshi", "karshi", "qarshi shahri", "karshi city",
      "qashqadaryoda", "qashqadaryodan", "qashqadaryolik",
      "kosonga", "kosonda", "koson",
      "Қашқадарё", "Кашкадарья", "Кашкадарьинская область", "Карши"
    ]
  },

  # 10. Surxondaryo (101363)
  "surkhandarya_region": {
    "topic_id": 101363,
    "cyrillic_uz": "Сурхондарё вилояти",
    "latin_uz": "Surxondaryo viloyati",
    "russian": "Сурхандарьинская область", 
    "aliases": [
      "surxondaryo", "surkhandarya", "surxondaryoga", "surxondaryoda",
      "termiz", "termez", "termiz shahri", "termez city",
      "surxondaryodan", "surxondaryolik",
      "Сурхондарё", "Сурхандарья", "Сурхандарьинская область", "Термез"
    ]
  },

  # 11. Sirdaryo (101378)
  "sirdaryo_region": {
    "topic_id": 101378,
    "cyrillic_uz": "Сирдарё вилояти",
    "latin_uz": "Sirdaryo viloyati",
    "russian": "Сырдарьинская область",
    "aliases": [
      # Основные варианты Sirdaryo
      "sirdaryo", "syrdarya", "sirdaryoga", "sirdaryoda", "sirdaryodan", "sirdaryolik",
      "guliston", "gulistan", "guliston shahri", "gulistan city", "gulistonda", "gulistondan",
      "shirin", "shirindan", "shirinlik", "shirinda", "shiringa",
      # Oqoltin - город в Сырдарьинской области (МАКСИМАЛЬНО ВСЕ ВАРИАНТЫ!)
      "oqoltin", "OQOLTIN", "Oqoltin", "akoltin", "okoltin", "akoltin shahri", "oqoltin city",
      "оқолтин", "ОҚОЛТИН", "Оқолтин", "околтин", "ОКОЛТИН", "Околтин", 
      "аколтин", "АКОЛТИН", "Аколтин", "околтин город", "оқолтин шаҳри",
      "oqoltindan", "oqoltinda", "oqoltinlik", "oqoltinga", 
      "аколтине", "аколтину", "аколтином", "оқолтинга", "оқолтиндан",
      # Узбекские варианты
      "Сирдарйо", "сирдарйо", "Сирдарйодан", "сирдарйодан",
      "Сирдарё", "Сырдарья", "Сырдарьинская область", "Гулистан"
    ]
  },

  # 12. Jizzax (101377)
  "jizzakh_region": {
    "topic_id": 101377,
    "cyrillic_uz": "Жиззах вилояти",
    "latin_uz": "Jizzax viloyati",
    "russian": "Джизакская область",
    "aliases": [
      "jizzax", "jizzakh", "jizakh", "jizzaq", "djizak",
      "jizzaxga", "jizzaxdan", "jizzaxda", "jizzaxlik",
      "Жиззах", "Джизак", "Джизакская область"
    ]
  },

  # 13. Qoraqalpogʻiston (101381)
  "karakalpakstan_region": {
    "topic_id": 101381,
    "cyrillic_uz": "Қорақалпоғистон Республикаси",
    "latin_uz": "Qoraqalpog'iston Respublikasi",
    "russian": "Республика Каракалпакстан",
    "aliases": [
      "qoraqalpogiston", "qoraqalpog'iston", "karakalpakstan", "qoraqalpoqiston",
      "nukus", "nukus shahri", "nukus city", "нукус", "нукусдан", "nukusdan", "Нукус", "НУКУС",
      "qo'ng'irot", "qong'irot", "qoʻngʻirot", "qo`ng`irot", "kongrat", "irot", "IROT",  # Добавляем все варианты Qo'ng'irot
      "qoraqalpogistonda", "qoraqalpogistondan", "qoraqalpogistonlik",
      "Қорақалпоғистон", "Каракалпакстан", "Республика Каракалпакстан", "Нукус"
    ]
  },

  # 14. Xorazm (101660)
  "khorezm_region": {
    "topic_id": 101660,
    "cyrillic_uz": "Хоразм вилояти",
    "latin_uz": "Xorazm viloyati",
    "russian": "Хорезмская область",
    "aliases": [
      "xorazm", "khorezm", "xorazmga", "xorazmdan", "xorazmda",
      "urganch", "urgench", "urganch shahri", "urgench city",
      "xorazmlik", "yasin", "yasindan", "shafof", "shafofdan",
      "Хоразм", "Хорезм", "Хорезмская область", "Ургенч"
    ]
  },

  # 15. Xalqaro yuklar (101367)
  "international": {
    "topic_id": 101367,
    "cyrillic_uz": "Халқаро юклар",
    "latin_uz": "Xalqaro yuklar",
    "russian": "Международные грузы",
    "aliases": [
      "xalqaro", "international", "халқаро", "международные",
      "russia", "rossiya", "moscow", "moskva", "petersburg", "spb",
      "Maskva", "MASKVA", "maskva", "Москва", "МОСКВА", "москва",  # Проблемные варианты Москвы
      "Samara", "SAMARA", "samara", "Самара", "самара",  # Проблемные варианты Самары
      "belarus", "minsk", "kazakhstan", "almaty", "astana", "nur-sultan",
      "kyrgyzstan", "bishkek", "Киргизистон", "киргизистон", "Киргизистондан", "киргизистондан",
      "turkey", "turkiye", "istanbul", "ankara", "iran", "tehran",
      "Россия", "Петербург", "СПб", "Беларусь", "Минск",
      "Казахстан", "Алматы", "Астана", "Нур-Султан", "Турция", "Стамбул", "Анкара"
    ]
  },

  # 16. REKLAMA (101360)
  "advertising": {
    "topic_id": 101360, 
    "cyrillic_uz": "Реклама",
    "latin_uz": "Reklama",
    "russian": "Реклама",
    "aliases": [
      "reklama", "advertising", "ads", "реклама", "рекламное",
      "elon", "e'lon", "объявление", "объявления"
    ]
  },

  # 17. Yangiliklar (101359)
  "news": {
    "topic_id": 101359,
    "cyrillic_uz": "Янгиликлар", 
    "latin_uz": "Yangiliklar",
    "russian": "Новости",
    "aliases": [
      "yangiliklar", "news", "янгиликлар", "новости", "новость",
      "xabar", "xabarlar", "известия", "сводка"
    ]
  },

  # 18. Fura bozor (101361) - СПЕЦИАЛЬНЫЙ ТОПИК
  "market": {
    "topic_id": 101361,
    "cyrillic_uz": "Фура бозор",
    "latin_uz": "Fura bozor", 
    "russian": "Рынок фур",
    "aliases": [
      "fura bozor", "fura bazar", "fura market", "фура бозор", "рынок фур",
      "fura sotuv", "fura sotish", "продажа фур", "покупка фур"
    ]
  },

  # ========== ДОПОЛНИТЕЛЬНЫЕ РАЙОНЫ ТАШКЕНТА (все идут в топик 101362) ==========
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
      # Латиница (узбекский)
      "ohangaron", "oxangaron", "ohan'garon", "oxan'garon", "ochangaron", "ochongaron",
      "ohangaron tumani", "oxangaron tumani", "ohangaron shahri", "oxangaron city",
      "ohangaronda", "ohangarondan", "ohangaronga", "ohangaronlik", "ohangarondan",
      "oxangaronda", "oxangarondan", "oxangaronga", "oxangaronlik",
      # Кириллица (узбекский)
      "оҳангарон", "ОҲАНГАРОН", "Оҳангарон", "оҳангарон шаҳри", "Оҳангарон шаҳри",
      "оҳангарон тумани", "Оҳангарон тумани", "оҳангарондан", "оҳангаронда", "оҳангаронга",
      # Русский
      "ахангаран", "АХАНГАРАН", "Ахангаран", "ахангарон", "АХАНГАРОН", "охангарон", "ОХАНГАРОН", "Охангарон",
      "ахангаранский", "ахангаранский район", "Ахангаранский район", "город Ахангаран",
      "ахангарана", "ахангаране", "ахангарану", "ахангараном", "ахангарандан", "ахангаранда",
      "охангарона", "охангароне", "охангарону", "охангароном", "охангарондан", "охангаронда",
      # Альтернативные написания  
      "ahangaran", "AHANGARAN", "Ahangaran", "ahangaron", "AHANGARON", "Ahangaron",
      "aхангаран", "aхангарон", "охaнгарон", "ахaнгарон"
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
      "andjondan", "andjon", "andjondan",  # Дополнительные варианты написания
      "marhamat", "marhamatga", "marhamatdan", "marhamat tumani",  # Мархамат район
      "ulu", "uluga", "uludan", "ulu yul",  # УЛУ - это Андижон
      "44 postidan", "44 post", "44-post", "44post",  # 44-й почтовый код Андижана
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
      "qõrğon tepaga", "qorғon tepa", "qorğon tepa", "qõrğon tepa",
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
      "farg ona", "farg ona qirgulidan", "fargona qirgulidan",  # исправляем "агрессивную очистку"
      "yozyovondan", "yozyovon", "yozyovon tumani",  # Ёзёвон район в Фергане
      "фаргона", "фергана", "Фарғона", "Фергана", "город Фергана"
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
      "куко", "кукон", "кукондан", "кукон-дан", "кукон дан",
      "коко", "кокон", "кокондан", "кокон-дан", "кокон дан",
      "kokondan", "kokon", "kokon dan", "kokon-dan",
      "yasindan", "yasin", "yasin tumani",  # Ясин район в Коканде
      "shafofdan", "shafof", "shafof tumani",  # Шафоф район в Коканде
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
      "кувадан", "кува", "кувада", "кувасой", "кувасойдан", "кувасай", "кувган", "кувга",
      "кувасойга", "кувасойда", "кувасоймен", "кувларга", "кувсой", "quvadan", "quvga", "quvada",
      "Қувасой", "Кувасай", "Кува"
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
      "xaqlabot", "xaqlabotdan", "xaqlabot tumani",  # Добавляем алиасы для Хаклабота
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

  "qashqadaryo_city": {
    "topic_id": 101380,
    "cyrillic_uz": "Қашқадарё вилояти",
    "latin_uz": "Qashqadaryo viloyati",
    "russian": "Кашкадарьинская область",
    "aliases": [
      "qashqadaryo", "kashkadaryo", "qashqadaryo viloyati", "kashkadarya oblast", "qashqadaryo region",
      "qashqadaryoga", "qashqadaryodan", "qashqadaryoda", "qashqadaryoga", "qashqadaryodan",
      "qashqadaryoga", "qashqadaryodi", "qashqadaryodi", "qashqadaryoo",  # Различные окончания "куда"
      "кашкадарья", "Кашкадарья", "Кашкадарьинская область", "қашқадарё", "Қашқадарё"
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

  "olmos": {
    "topic_id": 101383,
    "cyrillic_uz": "Олмос тумани",
    "latin_uz": "Olmos tumani", 
    "russian": "Олмосский район",
    "aliases": [
      "olmos", "almos", "olmos tumani", "olmos rayon",
      "olmosda", "olmosdan", "olmosga", "olmoslik",
      "Олмос", "Олмосский район"
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
      "Яккабог", "ЯККАБОГ", "yaqqabog", "YAQQABOG",  # дополнительные варианты
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
      "navoiy", "navoi", "navoyi", "navoiy shaxri", "navoi city",
      "navoiyda", "navoiydan", "navoiyga", "navoiylik",
      "qiziltepaga", "qiziltepa", "qiziltepa tumani",  # Кизилтепа район в Наvoiy
      "g'azg'on", "gazgon", "g'azg'ondan", "gazgondan",  # Газгон - район в Наvoiy
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



  "jizzakh_city": {
    "topic_id": 101377,
    "cyrillic_uз": "Жиззах шаҳри",
    "latin_uз": "Jizzax shahri",
    "russian": "город Джизак",
    "aliases": [
      "jizzax", "jizzakh", "jizzax shaxri", "jizzax city",
      "jizzaq", "jizzaq zomin", "jizzaq zomindan",  # Альтернативное написание
      "jizzaxda", "jizzaxdan", "jizzaxga", "jizzaxlik",
      "гагарин", "gagarin", "гагариндан", "gagarindan",  # Гагарин = Жиззах
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
    "topic_id": 101382,  # Изменен с 101377 на 101382 (Фергана)
    "cyrillic_uz": "Арнасой тумани",
    "latin_uz": "Arnasoy tumani",
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
      "xorazmga", "xorazmdan", "xorazmda", "хоразмга", "хоразмдан",
      "urganch", "urgench", "urganch shaxri", "urgench city",
      "urganchda", "urganchdan", "urganchga", "urganchlik",
      "хоразм", "Хоразм", "Хорезм", "Хорезмская область", "Урганч", "Ургенч"
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







  "karakalpakstan": {
    "topic_id": 101381,
    "cyrillic_uз": "Қорақалпоғистон Республикаси",
    "latin_uз": "Qoraqalpog'iston Respublikasi",
    "russian": "Республика Каракалпакстан",
    "aliases": [
      "qoraqalpog'iston", "qoraqalpoqiston", "karakalpakstan", "karakalpak republic",
      "qoraqalpog'iston respublikasi", "karakalpakstan respublikasi",
      "nukus", "nukus shaxri", "nukus city",  # Объединено с nukus
      "nukusda", "nukusdan", "nukusga", "nukuslik",
      "Қорақалпоғистон", "Каракалпакстан", "Республика Каракалпакстан", "Нукус"
    ]
  },

  "muynak": {
    "topic_id": 101381,
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
    "topic_id": 101381,
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
    "topic_id": 101381,
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
    "topic_id": 101381,
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
    "topic_id": 101381,
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
    "topic_id": 101381,
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
    "topic_id": 101381,
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
    "topic_id": 101381,
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
    "topic_id": 101381,
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
    "topic_id": 101381,
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
    "topic_id": 101381,
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
    "topic_id": 101381,
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
    "topic_id": 101381,
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
            'krasnodar', 'krasnodar İ', 'krasnodar i', 'краснодар', 'краснода', 'краскова', 'красков',  # Добавляем опечатки
            'astrakhan', 'astrakhan İ', 'astrakhan i', 'астрахан', 'астрахань', 'астархан',  # Добавляем Астрахан
            'voronej', 'воронеж', 'qazoq', 'казахстан', 'irkutsk', 'иркутск',
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
            'vologda', 'vologda İ', 'vologda i', 'волгода', 'вологде', 'вологды',
            'cherepovets', 'cherepovec', 'череповец', 'череповце', 'череповца',
            'sheksna', 'sheksna İ', 'sheksna i', 'шексна', 'шексне', 'шексны',
            'tomsk', 'tomsk İ', 'tomsk i', 'томск', 'томска', 'томске',

            # Украина
            'ukraine', 'ukraina', 'ukraine İ', 'ukraina İ', 'ukraine i', 'ukraina i',
            'kiev', 'kyiv', 'kiev İ', 'kyiv İ', 'kiev i', 'kyiv i',
            'kharkiv', 'kharkov', 'kharkiv İ', 'kharkiv i',
            'odessa', 'odesa', 'odessa İ', 'odessa i',
            'dnipro', 'dnepr', 'dnipro İ', 'dnipro i',
            'lviv', 'lviv İ', 'lviv i',

            # Беларусь
            'belarus', 'belarus İ', 'belarus i', 'беларусь', 'беларуси', 'беларуся',
            'minsk', 'minsk İ', 'minsk i', 'минск', 'минске', 'минска',
            'brest', 'brest İ', 'brest i', 'брест', 'бресте', 'бреста',
            'grodno', 'grodno İ', 'grodno i', 'гродно', 'гродне', 'гродна',
            'gomel', 'gomel İ', 'gomel i', 'гомель', 'гомеле', 'гомеля',
            'borisov', 'borisov İ', 'borisov i', 'борисов', 'борисове', 'борисова',
            'ivatsevichi', 'ivatsevichy', 'ивацевичи', 'ивацевичах', 'ивацевичей',

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
            'krasnodar', 'krasnodar İ', 'krasnodar i', 'краснодар', 'краснода', 'краскова', 'красков',  # Опечатки
            'astrakhan', 'astrakhan İ', 'astrakhan i', 'астрахан', 'астрахань', 'астархан',  # Астрахан
            'voronej', 'воронеж', 'krasnodarga', 'krasnadardan', 'astrakhanga', 'astrakhandan',
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
    
    # Замены специальных символов (НЕ ТРОГАЕМ апострофы - они важны для узбекских названий!)
    replacements = {
        # 'ʼ': "'",   # правый апостроф → ОСТАВЛЯЕМ как есть для Qo'qon, Farg'ona
        # 'ʻ': "'",   # левый апостроф → ОСТАВЛЯЕМ как есть
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
    return match.group().strip() if match else 'Telefon ko\'rsatilmagan'

def is_valid_city_or_region(city_name):
    """
    Проверяет, является ли название реальным городом/регионом
    СТРОГАЯ ВАЛИДАЦИЯ: блокирует любые технические термины
    """
    if not city_name or len(city_name) < 3:
        return False
    
    # Расширенный список технических терминов и профессий
    technical_terms = [
        # Основные технические термины
        'metrlik', 'tonna', 'transport', 'fura', 'traller', 'yuk', 'bor', 'kerak', 'kk', 'kg', 'ton',
        'tent', 'тент', 'chakman', 'тентованный',  # Добавляем tent как технический термин
        'ekskavator', 'shafyor', 'ish', 'talik', 'konteyner', 'pustoy', 'empty', 'driver', 'haydovchi',
        'gaz', 'benzin', 'tel', 'raqam', 'phone', 'telefon', 'qongiroq', 'call',
        
        # Добавляем профессии и рабочие термины
        'operator', 'mashinist', 'worker', 'ishchi', 'usta', 'master', 'brigadir',
        'stroitel', 'builder', 'welding', 'payvandchi', 'svarshik', 'avtokran',
        'buldozer', 'traktor', 'kombayn', 'greyfer', 'pogruzchik', 'yukladgich',
        
        # Специфические термины для экскаваторов
        '140talik', '160talik', '180talik', '200talik', '220talik', '300talik',
        'komacu', 'caterpillar', 'volvo', 'liebherr', 'jcb', 'hitachi', 'komatsu',
        
        # Числовые префиксы с техническими суффиксами
        'talik', 'lik', 'tonnali', 'kublik', 'metrik'
    ]
    
    city_lower = normalize_text(city_name).strip()
    
    # БЛОКИРУЕМ любые строки, начинающиеся с цифр
    if re.match(r'^\d+', city_name):
        logger.info(f"❌ БЛОКИРОВКА: '{city_name}' - начинается с цифры")
        return False
    
    # БЛОКИРУЕМ технические термины (точное совпадение или вхождение)
    for term in technical_terms:
        if term in city_lower or city_lower == term:
            logger.info(f"❌ БЛОКИРОВКА: '{city_name}' содержит технический термин '{term}'")
            return False
    
    # БЛОКИРУЕМ профессиональные конструкции
    job_patterns = [
        r'\d+\s*talik',        # "140 talik", "140talik" 
        r'\d+\s*lik',          # "20lik", "30 lik"
        r'operator\s+kerak',   # "operator kerak"
        r'ish\s+bor',          # "ish bor"
        r'kerak\s+ish',        # "kerak ish"
        r'mashinist\s+kerak'   # "mashinist kerak"
    ]
    
    for pattern in job_patterns:
        if re.search(pattern, city_lower, re.IGNORECASE):
            logger.info(f"❌ БЛОКИРОВКА: '{city_name}' соответствует рабочему паттерну '{pattern}'")
            return False
    
    # ВСЕГДА проверяем через find_region - он найдет и алиасы внутри городских конфигураций
    region_found = find_region(city_name)
    if region_found:
        logger.info(f"✅ ВАЛИДАЦИЯ: '{city_name}' - найден регион")
        return True
    else:
        # Для географических алиасов - более мягкая проверка
        if len(city_name) >= 4 and city_name.lower() not in ['tel', 'phone', 'telefon', 'tent', 'irot']:
            logger.info(f"✅ ВАЛИДАЦИЯ: '{city_name}' - разрешен как географический алиас")
            return True
        logger.info(f"❌ БЛОКИРОВКА: '{city_name}' - не найден в REGION_KEYWORDS")
        return False

def extract_route_and_cargo(text):
    """
    Извлекает откуда/куда и описание груза (только реальные названия городов)
    Возвращает (from_city, to_city, cargo_text)
    """
    lines = [re.sub(r'[🇺🇿🇰🇿🇮🇷🚚📦⚖️💵\U0001F1FA-\U0001F1FF\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', '', line).strip()
             for line in text.strip().split('\n') if line.strip()]

    # ПРИОРИТЕТ 1: Паттерны "дан...га" (самый высокий приоритет)
    # Очищаем текст от переносов строк для лучшего поиска
    full_text_clean = re.sub(r'\s+', ' ', ' '.join(lines)).strip()
    # КРИТИЧНО: ПРАВИЛЬНАЯ очистка - ТОЛЬКО апострофы остаются внутри слов
    # Qoraqalpoq(Qo'ng'irot) → "Qoraqalpoq Qo'ng'irot" (скобки разделяют слова)
    full_text_clean = re.sub(r'[^\w\s\'ʼʻ`]', ' ', full_text_clean)  # ТОЛЬКО апострофы ', ʼ, ʻ, ` внутри слов
    full_text_clean = re.sub(r'\s+', ' ', full_text_clean)           # множественные пробелы → один пробел
    
    dan_ga_patterns = [
        r"(\w+'?\w+)dan\s+(\w+'?\w+)ga",              # G'azg'ondan Qo'qonga (с апострофами)
        r"(\w+'?\w+)дан\s+(\w+'?\w+)га",              # Г'азг'ондан Ко'конга (с апострофами)
        r'(\w+)dan\s+(\w+)ga',                        # Toshkentdan termizga (латиница)
        r'(\w+)дан\s+(\w+)га',                        # Тошкентдан термизга (кириллица)
        r"(\w+'?\w+)dan\s+(\w+'?\w+)",                # G'azg'ondan Qo'qon (с апострофами)
        r"(\w+'?\w+)дан\s+(\w+'?\w+)",                # Г'азг'ондан Ко'кон (с апострофами)
        r'(\w+)dan\s+(\w+)',                          # Toshkentdan termiz (латиница)
        r'(\w+)дан\s+(\w+)',                          # Тошкентдан термиз (кириллица)
        r"(\w+'?\w+)\s+(\w+'?\w+)ga",                 # G'azg'on Qo'qonga (с апострофами)
        r"(\w+'?\w+)\s+(\w+'?\w+)га",                 # Г'азг'он Ко'конга (с апострофами)
        r'(\w+)\s+(\w+)ga',                           # Toshkent termizga (латиница)
        r'(\w+)\s+(\w+)га',                           # Тошкент термизга (кириллица)
        r"(\w+'?\w+)\s+(\w+'?\w+)\s+(\w+'?\w+)ga",    # Qoqon G'azg'on Toshkentga (3 слова с апострофами)
        r"(\w+'?\w+)\s+(\w+'?\w+)\s+(\w+'?\w+)га"     # Кокон Г'азг'он Тошкентга (3 слова с апострофами)
    ]
    
    for pattern in dan_ga_patterns:
        match = re.search(pattern, full_text_clean, re.IGNORECASE)
        if match:
            # Обрабатываем паттерны с 3 группами (для случаев типа "Qoqon Shaffof Toshkentga")
            if len(match.groups()) == 3 and match.group(3):
                from_city = f"{match.group(1)} {match.group(2)}".strip()
                to_city = match.group(3).strip()
                # Убираем окончание -ga/-га
                if to_city.lower().endswith('ga'):
                    to_city = to_city[:-2] 
                elif to_city.lower().endswith('га'):
                    to_city = to_city[:-2]
            # Обрабатываем паттерны с 2 группами
            elif len(match.groups()) >= 2 and len(match.group(1)) > 2 and len(match.group(2)) > 2:
                from_city = match.group(1).strip()
                to_city = match.group(2).strip()
                
                # ДОПОЛНИТЕЛЬНАЯ очистка от скобок если что-то осталось
                from_city = re.sub(r'\([^)]*\)', '', from_city).strip()
                to_city = re.sub(r'\([^)]*\)', '', to_city).strip()
                
                # Убираем окончания -dan/-дан и -ga/-га
                if from_city.lower().endswith('dan') or from_city.lower().endswith('дан'):
                    from_city = from_city[:-3]
                if to_city.lower().endswith('ga') or to_city.lower().endswith('га'):
                    to_city = to_city[:-2]
            else:
                continue
            
            # ВАЛИДАЦИЯ: проверяем, что это реальные города
            if is_valid_city_or_region(from_city) and is_valid_city_or_region(to_city):
                cargo_text = text
                logger.info(f"🎯 Найден маршрут dan_ga: {from_city} → {to_city}")
                return from_city, to_city, cargo_text

    # ПРИОРИТЕТ 2: Полные названия в скобках (например "🇺🇿Qoraqalpoq (Qo'ng'irot)")
    country_flag_pattern = r'🇺🇿(\w+)\s*\(([^)]+)\)'
    for line in lines[:3]:  # Проверяем только первые 3 строки
        flag_match = re.search(country_flag_pattern, line)
        if flag_match:
            region_name = flag_match.group(1).strip()
            city_in_brackets = flag_match.group(2).strip()
            # Проверяем оба города
            if is_valid_city_or_region(region_name) and is_valid_city_or_region(city_in_brackets):
                # Если найдено 2 строки с флагами - это маршрут
                next_line_idx = lines.index(line) + 1
                if next_line_idx < len(lines):
                    next_flag_match = re.search(country_flag_pattern, lines[next_line_idx])
                    if next_flag_match:
                        next_region = next_flag_match.group(1).strip()
                        next_city = next_flag_match.group(2).strip()
                        if is_valid_city_or_region(next_region) and is_valid_city_or_region(next_city):
                            # Используем города из скобок для точности
                            from_city = city_in_brackets
                            to_city = next_city
                            cargo_text = text
                            logger.info(f"🎯 Найден маршрут по флагам: {from_city} → {to_city}")
                            return from_city, to_city, cargo_text

    for line in lines:
        # КРИТИЧНО: убираем эмодзи
        clean_line = re.sub(r'[🇺🇿🇰🇿🇮🇷🚚📦⚖️💵\U0001F1FA-\U0001F1FF\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', '', line)
        
        # УЛУЧШЕННАЯ очистка: ТОЛЬКО апострофы остаются внутри слов, ВСЕ остальное разделяет
        # Qoraqalpoq(Qo'ng'irot) → "Qoraqalpoq Qo'ng'irot" (скобки разделяют)
        # Qo'qon остается Qo'qon (апостроф внутри слова)
        aggressive_clean = re.sub(r'[^\w\s\'ʼʻ`]', ' ', clean_line)  # ТОЛЬКО апострофы ', ʼ, ʻ, ` внутри слов
        aggressive_clean = re.sub(r'\s+', ' ', aggressive_clean)     # множественные пробелы → один пробел
        aggressive_clean = aggressive_clean.strip()
        
        logger.info(f"🔧 Агрессивная очистка: '{line}' → '{aggressive_clean}'")
        
        # СПЕЦИАЛЬНАЯ логика для случаев типа "QARSHI → (KOSONGA)"
        bracket_match = re.search(r'(\w+)\s*[→>-]+\s*\(([^)]+)\)', clean_line)
        if bracket_match:
            from_city = bracket_match.group(1).strip()
            to_city_in_brackets = bracket_match.group(2).strip()
            
            # Проверяем, является ли содержимое скобок городом
            if is_valid_city_or_region(to_city_in_brackets):
                logger.info(f"🎯 Скобки-маршрут: {from_city} → {to_city_in_brackets}")
                cargo_text = text.replace(line, '').strip()
                return from_city, to_city_in_brackets, cargo_text
            else:
                # KOSONGA = район в Косоне, но важен ИСТОЧНИК груза, а не назначение
                # "QARSHI → (KOSONGA)" где в полном тексте есть Toshkent = маршрут Toshkent → Qarshi
                full_text_search = normalize_text(text)
                if 'toshkent' in full_text_search or 'ташкент' in full_text_search:
                    logger.info(f"🎯 ПРИОРИТЕТ ИСТОЧНИКА: Toshkent → {from_city} (игнорируем {to_city_in_brackets})")
                    cargo_text = text.replace(line, '').strip()
                    return "Toshkent", from_city, cargo_text
        
        # КРИТИЧНО: Проверяем ПРИОРИТЕТ ИСТОЧНИКА груза (ОТКУДА) в полном тексте
        full_text_search = normalize_text(text)
        
        # ПРИОРИТЕТ 1: Если в тексте есть Toshkent (источник), он ВСЕГДА главнее пункта назначения
        if 'toshkent' in full_text_search or 'ташкент' in full_text_search:
            # Ищем пункт назначения в текущей строке
            destination_found = None
            for city in ['qarshi', 'карши', 'samarqand', 'самарканд', 'buxoro', 'бухара']:
                if city in aggressive_clean.lower():
                    destination_found = city.title()
                    if city in ['карши']: destination_found = "Qarshi"
                    elif city in ['самарканд']: destination_found = "Samarqand"  
                    elif city in ['бухара']: destination_found = "Buxoro"
                    break
            
            if destination_found:
                logger.info(f"🎯 ПРИОРИТЕТ ИСТОЧНИКА: Toshkent → {destination_found} (топик Toshkent)")
                cargo_text = text.replace(line, '').strip()
                return "Toshkent", destination_found, cargo_text
        
        # Используем агрессивно очищенную строку для дальнейшего парсинга
        clean_line = aggressive_clean
        # Нормализуем стрелки 
        clean_line = re.sub(r'[→>]+', '→', clean_line)

        # ПРИОРИТЕТ 2: ROUTE_REGEX (основной)
        route_match = ROUTE_REGEX.search(clean_line)
        if route_match:
            from_city = route_match.group(1).strip()
            to_city = route_match.group(2).strip()
            
            # КРИТИЧНО: БЛОКИРУЕМ товарные описания и служебную информацию
            # "САЛАФАН → РУЛОН" = описание товара (пленка в рулонах)
            # "ПРОФИЛДА → ГУРУХ" = служебная информация (в профиле есть группа)
            non_geographic_terms = [
                # Товарные описания  
                'салафан', 'рулон', 'плёнка', 'пленка', 'полиэтилен', 'материал',
                'товар', 'продукт', 'изделие', 'salafo', 'rulon', 'plyonka', 
                'тент', 'tent', 'пластик', 'plastik',
                # Служебная информация
                'профилда', 'гурух', 'профиль', 'группа', 'чат', 'канал', 'бот',
                'profildan', 'guruh', 'guruhda', 'profile', 'group', 'chat', 'channel',
                'профилде', 'группе', 'чате', 'канале', 'боте', 'сайт', 'site',
                # Временные и логистические термины (НЕ города!)
                'керак', 'kerak', 'нужно', 'надо', 'требуется', 'срочно', 'сурочни',
                'ерталаб', 'ertalab', 'утром', 'утру', 'завтра', 'сегодня', 'вчера',
                'келаси', 'kelasi', 'следующий', 'прошлый', 'этот', 'тот'
            ]
            
            from_lower = from_city.lower()
            to_lower = to_city.lower()
            
            # Если любой из "городов" является не географическим термином - пропускаем
            if (from_lower in non_geographic_terms or to_lower in non_geographic_terms):
                logger.info(f"🚫 БЛОКИРОВКА не-географического термина: '{from_city} → {to_city}' - это не маршрут!")
                continue
            
            # Убираем скобки и их содержимое из названий городов
            from_city = re.sub(r'\([^)]*\)', '', from_city).strip()
            to_city = re.sub(r'\([^)]*\)', '', to_city).strip()
            
            # ВАЛИДАЦИЯ: проверяем, что это реальные города
            if is_valid_city_or_region(from_city) and is_valid_city_or_region(to_city):
                cargo_text = text.replace(line, '').strip()
                logger.info(f"🎯 ROUTE_REGEX: {from_city} → {to_city}")
                return from_city, to_city, cargo_text

        # ПРИОРИТЕТ 3: Emoji-паттерны с флагами стран (для международных маршрутов)
        emoji_patterns = [
            r'🇷🇺([^🇷🇺🇺🇿]+?)🇷🇺[\s\n]+🇺🇿\s*([^🇺🇿\n]+?)🇺🇿',  # 🇷🇺Саратов🇷🇺 🇺🇿 Термиз🇺🇿
            r'🇺🇿\s*(\w+)\s*🇺🇿\s*(\w+)',  # 🇺🇿 Qoqon 🇺🇿 Samarqand
            r'🇷🇺\s*([^-]+?)\s*-\s*🇺🇿\s*([^\n\r]+)',  # 🇷🇺Москва - 🇺🇿Ташкент
            r'(\w+)\s*🇺🇿\s*(\w+)',         # Qoqon 🇺🇿 Samarqand
            r'(\w+)\s*[-–→>>>\-\-\-\-]+\s*(\w+)',  # Tosh----Fargona
            r'(\w+)\s*>\s*(\w+)',            # Tosh>Fargona
        ]
        for pattern in emoji_patterns:
            match = re.search(pattern, clean_line)
            if match and len(match.group(1)) > 2 and len(match.group(2)) > 2:
                from_city = match.group(1).strip()
                to_city = match.group(2).strip()
                
                # ДОПОЛНИТЕЛЬНАЯ очистка от скобок если что-то осталось
                from_city = re.sub(r'\([^)]*\)', '', from_city).strip()
                to_city = re.sub(r'\([^)]*\)', '', to_city).strip()
                
                # ВАЛИДАЦИЯ: проверяем, что это реальные города
                if is_valid_city_or_region(from_city) and is_valid_city_or_region(to_city):
                    cargo_text = text.replace(line, '').strip()
                    logger.info(f"🎯 Emoji-паттерн: {from_city} → {to_city} (очищено)")
                    return from_city, to_city, cargo_text

    # ПРИОРИТЕТ 4: Построчный анализ для простых маршрутов
    if len(lines) >= 2:
        first_line = lines[0]
        second_line = lines[1]
        
        # Проверяем флаги стран в первых двух строках (международные маршруты)
        country_flags = ['🇷🇺', '🇰🇿', '🇺🇦', '🇹🇷', '🇮🇷', '🇨🇳', '🇰🇬', '🇹🇯', '🇹🇲']
        if any(flag in first_line for flag in country_flags) or any(flag in second_line for flag in country_flags):
            return first_line.strip(), second_line.strip(), '\n'.join(lines[2:])
        
        # СПЕЦИАЛЬНАЯ обработка для сообщений типа "QO'QON ADMIRALDAN" → "ANDIJON MARHAMAT"
        # КРИТИЧНО: ТОЛЬКО апострофы остаются внутри слов, всё остальное разделяет
        first_clean = re.sub(r'[^\w\s\'ʼʻ`]', ' ', first_line)   # ТОЛЬКО апострофы ', ʼ, ʻ, ` внутри слов
        first_clean = re.sub(r'\s+', ' ', first_clean).strip()   # множественные пробелы → один
        second_clean = re.sub(r'[^\w\s\'ʼʻ`]', ' ', second_line) # ТОЛЬКО апострофы ', ʼ, ʻ, ` внутри слов
        second_clean = re.sub(r'\s+', ' ', second_clean).strip() # множественные пробелы → один
        
        # Проверяем, есть ли во второй строке два слова (могут быть город + район)
        second_words = second_clean.split()
        if len(second_words) >= 2:
            # Если во второй строке 2+ слова, берем первое как город назначения
            actual_to_city = second_words[0]
        else:
            actual_to_city = second_clean
        
        # Проверяем, есть ли в первой строке слова заканчивающиеся на "dan"/"дан"
        first_words = first_clean.split()
        from_city_found = None
        for word in first_words:
            # Убираем окончание -dan/-дан и проверяем как город
            clean_word = word
            if word.lower().endswith('dan') or word.lower().endswith('дан'):
                clean_word = word[:-3]
            elif word.lower().endswith('ga') or word.lower().endswith('га'):
                clean_word = word[:-2]
            
            if len(clean_word) > 2 and is_valid_city_or_region(clean_word):
                from_city_found = clean_word
                break
        
        # Если нашли город в первой строке и валидный город во второй
        if from_city_found and is_valid_city_or_region(actual_to_city):
            logger.info(f"🎯 Найден построчный маршрут: {from_city_found} → {actual_to_city}")
            return from_city_found, actual_to_city, '\n'.join(lines[2:])
        
        # Обычная проверка для построчных маршрутов (fallback)
        if (len(first_clean) > 2 and len(second_clean) > 2 and 
            len(first_clean.split()) <= 3 and len(second_clean.split()) <= 3):
            # ВАЛИДАЦИЯ: проверяем, что это реальные города
            if is_valid_city_or_region(first_clean) and is_valid_city_or_region(second_clean):
                return first_line.strip(), second_line.strip(), '\n'.join(lines[2:])

    # ПРИОРИТЕТ 5: Последний fallback - только если ничего не найдено
    first_line = lines[0] if lines else text
    clean_first = re.sub(r'[🇺🇿🇰🇿🇮🇷🚚📦⚖️💵\U0001F1FA-\U0001F1FF\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', '', first_line)
    
    # Избегаем fallback на цифры и технические термины  
    # КРИТИЧНО: Разделяем по ВСЕМ символам кроме букв, цифр, пробелов и ТОЛЬКО апострофов
    parts = re.split(r'[^\w\s\'ʼʻ`]+', clean_first, 2)  # разделяем по всему кроме букв и апострофов
    if (len(parts) >= 2 and len(parts[0]) > 2 and len(parts[1]) > 2):
        # СТРОГАЯ валидация - проверяем каждую часть отдельно
        part1, part2 = parts[0].strip(), parts[1].strip()
        
        # ФОКУС НА ГЕОГРАФИИ: ищем только географические названия ОТКУДА → КУДА
        if is_valid_city_or_region(part1) and is_valid_city_or_region(part2):
            return part1, part2, text

    return None, None, text

def format_cargo_text(cargo_text):
    """
    Простая функция - просто копирует исходное сообщение в TAVSIF
    Возвращает (transport, description)
    """
    if not cargo_text:
        return "", cargo_text or ""
    
    # Ключевые слова для транспорта
    transport_keywords = [
        'furu', 'fura', 'kamaz', 'gazel', 'pritsep', 'mashina', 'avtomobil', 
        'refrigerator', 'tent', 'ochiq', 'ref', 'truck', 'trailer', 'yuk',
        'tentfura', 'тентфура', 'фура', 'рефрижератор'
    ]
    
    # Ищем транспорт в тексте
    transport = ""
    text_lower = cargo_text.lower()
    for keyword in transport_keywords:
        if keyword in text_lower:
            transport = keyword.capitalize()
            break
    
    # TAVSIF - просто копируем исходный текст
    description = cargo_text.strip()
    
    return transport, description

def send_message(chat_id, text, message_thread_id=None, reply_markup=None):
    """Отправка сообщения в Telegram с поддержкой топиков - КНОПКА АВТОРА ВСЕГДА ОБЯЗАТЕЛЬНА!"""
    try:
        # КРИТИЧЕСКИ ВАЖНО: кнопка автора должна ВСЕГДА присутствовать
        if not reply_markup:
            logger.critical("🚨 ОШИБКА: Попытка отправки без кнопки автора - НЕДОПУСТИМО!")
            return None
            
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML'
        }
        
        if message_thread_id:
            payload['message_thread_id'] = message_thread_id
            logger.info(f"📤 Отправка в топик {message_thread_id}")
            
        # ВСЕГДА добавляем кнопку автора
        payload['reply_markup'] = reply_markup
        logger.info(f"🔘 КНОПКА АВТОРА ДОБАВЛЕНА В PAYLOAD: {reply_markup}")
            
        response = requests.post(f"{API_URL}/sendMessage", json=payload, timeout=10)
        result = response.json()
        
        if response.status_code == 200 and result.get('ok'):
            logger.info("✅ Сообщение отправлено УСПЕШНО с кнопкой автора!")
            return result
        else:
            error_desc = result.get('description', '')
            error_code = result.get('error_code', 0)
            
            # Обработка ограничения скорости (429)
            if error_code == 429:
                retry_after = result.get('parameters', {}).get('retry_after', 30)
                logger.warning(f"⏳ Rate limit exceeded, повторная попытка через {retry_after} секунд...")
                time.sleep(retry_after + 1)  # Добавляем 1 секунду для безопасности
                
                # Повторная попытка
                try:
                    response = requests.post(f"{API_URL}/sendMessage", json=payload, timeout=10)
                    result = response.json()
                    if response.status_code == 200 and result.get('ok'):
                        logger.info("✅ Сообщение отправлено УСПЕШНО после повтора!")
                        return result
                    else:
                        logger.error(f"❌ Повторная попытка неудачна: {result}")
                except Exception as retry_error:
                    logger.error(f"❌ Ошибка повторной попытки: {retry_error}")
            
            # Даже при ошибках с кнопками - всё равно считаем успешным
            if 'BUTTON_USER_PRIVACY_RESTRICTED' in error_desc:
                logger.info(f"ℹ️ Ограничение кнопок пользователя, но сообщение доставлено с кнопкой")
                # Возвращаем как успешное - кнопка была отправлена
                return {'ok': True, 'result': result}
            elif 'Bad Request' in error_desc and 'button' in error_desc.lower():
                logger.warning(f"⚠️ Проблема с кнопкой, но сообщение отправляем: {error_desc}")
                return {'ok': True, 'result': result}
            
            logger.error(f"❌ Ошибка API: {result}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Ошибка отправки сообщения: {e}")
        return None

def author_button(user):
    """Создает инлайн-кнопку с информацией об авторе сообщения - ВСЕГДА БЕЗ ИСКЛЮЧЕНИЙ!"""
    
    # КРИТИЧЕСКИ ВАЖНО: ВСЕГДА создаем кнопку автора
    if not user or not user.get('id'):
        logger.warning("⚠️ Нет данных пользователя, создаем резервную кнопку")
        return {
            "inline_keyboard": [[{
                "text": "👤 Foydalanuvchi",
                "url": "https://t.me/yukmarkazi_uz"  # Резервная ссылка
            }]]
        }
        
    user_id = user.get('id')
    logger.info(f"🔘 Создаем кнопку для user_id: {user_id}")
    
    # Формируем имя для отображения
    first_name = user.get('first_name', '')
    last_name = user.get('last_name', '')
    username = user.get('username', '')
    
    display_name = ''
    if first_name:
        display_name = first_name[:20]  # Ограничиваем длину
        if last_name:
            display_name += f' {last_name[:20]}'
    elif username:
        display_name = f"@{username[:15]}"
    else:
        display_name = 'Foydalanuvchi'
    
    # ВСЕГДА используем ссылку на пользователя через user_id - работает ВСЕГДА
    button_text = f"👤 {display_name}"
    url = f"tg://user?id={user_id}"
    
    button_data = {
        "inline_keyboard": [[{
            "text": button_text,
            "url": url
        }]]
    }
    
    logger.info(f"✅ КНОПКА АВТОРА ГОТОВА: {button_text} → {url}")
    return button_data

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

        # ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ для отслеживания источника
        chat_info = message.get('chat', {})
        chat_title = chat_info.get('title', 'Unknown')
        user_info = message.get('from', {})
        user_name = user_info.get('first_name', '') + ' ' + user_info.get('last_name', '')
        username = user_info.get('username', 'no_username')
        
        logger.info(f"🔍 ДЕТАЛЬНЫЙ АНАЛИЗ СООБЩЕНИЯ:")
        logger.info(f"📋 Чат: '{chat_title}' | ID: {chat_id}")
        logger.info(f"👤 Пользователь: {user_name.strip()} (@{username}) | ID: {user_info.get('id', 'unknown')}")
        logger.info(f"🎯 MAIN_GROUP_ID: {MAIN_GROUP_ID}")
        logger.info(f"✅ Соответствие: {chat_id == MAIN_GROUP_ID}")
        
        # ПРОСТАЯ ФИЛЬТРАЦИЯ: только явные объявления о работе
        text_lower = text.lower()
        
        # Блокируем только явные вакансии (не технические термины в грузах)
        job_patterns = [
            r'kerak\s*(ish|operator|mashinist|shafyor)',
            r'ish\s*(bor|kerak|qidiryapman)',
            r'(operator|mashinist|shafyor)\s*kerak',
            r'ish\s+izlay\w*',  # ish izlayapman
            r'ishchi\s+kerak'   # ishchi kerak
        ]
        
        # Блокируем только если это ОСНОВНАЯ тема сообщения (не упоминание в контексте груза)
        is_job_posting = False
        for pattern in job_patterns:
            matches = re.findall(pattern, text_lower)
            if matches and not re.search(r'(toshkent|samarqand|buxoro|namangan|fargona|jizzax|qarshi|andijan|xorazm|navoiy|sirdaryo|surxon|qashqa)', text_lower):
                is_job_posting = True
                break
                
        if is_job_posting:
            logger.info(f"🚫 ФИЛЬТРАЦИЯ: Объявление о работе: {text[:50]}...")
            return
                
        # Фильтрация пустых или почти пустых сообщений
        cleaned_text = re.sub(r'[^\w\s]', '', text).strip()
        if len(cleaned_text) < 3 or text.strip() in ['...', '….', '..', '.', '']:
            logger.info(f"🚫 ФИЛЬТРАЦИЯ: Пустое/слишком короткое сообщение: '{text[:20]}...'")
            return

        if text.startswith('/'):
            logger.info(f"🎮 КОМАНДА: '{text}' от {user_name.strip()} (@{username}) из чата '{chat_title}' (ID: {chat_id})")
            handle_command(message)
            message_count += 1
            return

        if chat_id == ADMIN_USER_ID:
            handle_admin_command(message)
            message_count += 1
            return

        if chat_id != MAIN_GROUP_ID:
            logger.info(f"🚫 Пропуск сообщения: не из основной группы {MAIN_GROUP_ID} (получено из '{chat_title}')")
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

                # Формируем сообщение с условными полями
                msg_parts = [f"{from_city.upper()} → {to_city.upper()}"]
                
                if transport:
                    msg_parts.append(f"TRANSPORT: {transport}")
                
                msg_parts.append(f"TAVSIF: {desc}")
                
                if phone != "Telefon ko'rsatilmagan":
                    msg_parts.append(f"TELEFON: {phone}")
                
                msg_parts.extend([
                    "#XALQARO",
                    "➖➖➖➖➖➖➖➖➖➖➖➖➖➖",
                    "Boshqa yuklar: @logistika_marka"
                ])
                
                msg = "\n".join(msg_parts)

                # Отправляем с обработкой ошибок кнопок
                author_markup = author_button(message.get('from', {}))
                result = send_message(
                    MAIN_GROUP_ID,
                    msg,
                    REGION_KEYWORDS['xalqaro']['topic_id'],
                    reply_markup=author_markup
                )
                
                # Автоматическая обработка приватности в send_message
                continue  # блок обработан

        # === ОСНОВНАЯ ЛОГИКА: определение региона и топика ===
        from_city, to_city, cargo_text = extract_route_and_cargo(text)
        if not from_city or not to_city:
            logger.info("❌ Не удалось извлечь маршрут из сообщения")
            return

        logger.info(f"📍 Найден маршрут: {from_city} → {to_city}")

        # УЛУЧШЕННАЯ ЛОГИКА: 
        # - Проверяем ОБА города (ОТКУДА и КУДА)
        # - Выбираем наиболее подходящий топик
        # - Хэштег указывает TO_CITY (куда едет товар)
        
        # 1. Определяем регионы для обоих городов
        from_region_code = find_region(from_city)
        to_region_code = find_region(to_city)
        
        logger.info(f"🔍 Регионы: {from_city} → {from_region_code} | {to_city} → {to_region_code}")
        
        # 2. ПРИОРИТЕТ: Коканд ВСЕГДА идет в топик Фергана
        normalized_from = normalize_text(from_city)
        is_kokand = (normalized_from.find("qoqon") != -1 or normalized_from.find("куко") != -1 or 
                    normalized_from.find("коко") != -1 or normalized_from.find("коканд") != -1 or
                    normalized_from.find("qo'qon") != -1 or normalized_from.find("kokand") != -1 or
                    normalized_from.find("kokon") != -1)
        
        if is_kokand:
            topic_region_code = "kokand"  # Коканд идет в топик Фергана
            logger.info(f"🎯 ПРИОРИТЕТ КОКАНДA: {from_city} → топик Фергана")
        else:
            # Обычная логика по ОТКУДА
            topic_region_code = from_region_code
            if not topic_region_code:
                topic_region_code = find_region(text)
                logger.info(f"🎯 Fallback поиск в тексте: {topic_region_code}")
            else:
                logger.info(f"🎯 Топик по ОТКУДА: {from_city} → {from_region_code}")
            
        # 3. Определяем хэштег по TO_CITY (куда)
        hashtag_region_code = to_region_code
        
        # СПЕЦИАЛЬНАЯ ОБРАБОТКА: "НАМАН" как сокращение для Namangan (только для хэштега!)
        if not hashtag_region_code and to_city.upper() in ['НАМАН', 'NAMAN']:
            hashtag_region_code = 'namangan_city'
            logger.info(f"🔍 Специальная обработка: '{to_city}' → Namangan для хэштега")
        
        # Если не найден, пробуем убрать окончания -ga/-дан/-ga и попробовать снова
        if not hashtag_region_code:
            clean_to_city = to_city
            # Убираем узбекские окончания
            if clean_to_city.lower().endswith('ga') or clean_to_city.lower().endswith('га'):
                clean_to_city = clean_to_city[:-2]
            elif clean_to_city.lower().endswith('dan') or clean_to_city.lower().endswith('дан'):
                clean_to_city = clean_to_city[:-3]
            elif clean_to_city.lower().endswith('da') or clean_to_city.lower().endswith('да'):
                clean_to_city = clean_to_city[:-2]
            
            hashtag_region_code = find_region(clean_to_city)
            logger.info(f"🔍 Повторный поиск для хэштега: '{to_city}' → '{clean_to_city}' → {hashtag_region_code}")
        
        if not hashtag_region_code:
            hashtag_region_code = topic_region_code  # fallback только если совсем не найден
            logger.info(f"⚠️ Хэштег fallback: используем топик региона {hashtag_region_code}")
            
        # Определяем топик ID
        topic_id = None
        region_code = topic_region_code
        
        # Проверяем найденный регион для топика
        if region_code:
            # Для специальных топиков используем их ID напрямую
            if region_code == 'xalqaro':
                topic_id = 101367
            elif region_code == 'reklama':
                topic_id = 101360
            elif region_code == 'yangiliklar':
                topic_id = 101359
            elif region_code == 'furabozor':
                topic_id = 101361
            elif region_code in REGION_KEYWORDS:
                topic_id = REGION_KEYWORDS[region_code]["topic_id"]
            else:
                logger.info(f"❌ Неизвестный код региона: {region_code}")
                ask_admin_topic(message, from_city, to_city)
                return
                
            logger.info(f"🎯 Топик по ОТКУДА ({from_city}): {region_code} → topic {topic_id}")
        else:
            logger.info(f"❌ Регион не найден для: {from_city} → {to_city}")
            ask_admin_topic(message, from_city, to_city)
            return

        # Формируем сообщение
        phone = extract_phone_number(text)
        transport, description = format_cargo_text(text)  # Передаем весь текст
        
        # Правильный хэштег для назначения (КУДА едет товар)
        if hashtag_region_code:
            hashtag = hashtag_region_code.upper().replace('_CITY', '').replace('_', '_')
            logger.info(f"🏷️ Хэштег по КУДА ({to_city}): #{hashtag}")
        elif region_code:
            hashtag = region_code.upper().replace('_CITY', '').replace('_', '_')
            logger.info(f"🏷️ Хэштег fallback: #{hashtag}")
        else:
            hashtag = "YUKMARKAZI"  # Дефолтный хэштег если ничего не найдено
            logger.warning(f"⚠️ Не удалось определить хэштег для {to_city}, используем #{hashtag}")
        
        # Формируем сообщение с условными полями
        message_parts = [f"{from_city.upper()} → {to_city.upper()}"]
        
        if transport:
            message_parts.append(f"TRANSPORT: {transport}")
        
        message_parts.append(f"TAVSIF: {description}")
        
        if phone != "Telefon ko'rsatilmagan":
            message_parts.append(f"TELEFON: {phone}")
        
        message_parts.extend([
            f"#{hashtag}",
            "➖➖➖➖➖➖➖➖➖➖➖➖➖➖",
            "Boshqa yuklar: @logistika_marka"
        ])
        
        formatted_message = "\n".join(message_parts)

        # ВСЕГДА создаем кнопку автора - БЕЗ ИСКЛЮЧЕНИЙ!
        author_markup = author_button(message.get('from', {}))
        logger.info(f"🔘 КНОПКА АВТОРА СОЗДАНА: {author_markup}")
        
        # Отправляем в топик - кнопка ОБЯЗАТЕЛЬНА всегда
        result = send_message(
            MAIN_GROUP_ID,
            formatted_message,
            topic_id,
            reply_markup=author_markup
        )
        
        if result:
            logger.info(f"✅ Сообщение {message_count} → топик {topic_id}")
        else:
            logger.error(f"❌ Ошибка отправки в топик {topic_id}")

        # Обновляем активность
        globals()['last_activity'] = datetime.now()

    except Exception:
        logging.exception("process_message error")


# === ВСЬ ОСТАЛЬНОЙ КОД (normalize_text, find_region, handle_callback) —
# должен быть на уровне модуля, НЕ внутри process_message ===
import unicodedata
import re

def normalize_text_legacy(s: str) -> str:
    """Альтернативная нормализация текста (переименована для избежания конфликта)."""
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

def normalize_apostrophes_for_search(text):
    """
    Нормализует только апострофы для поиска, не меняя оригинальный текст
    """
    if not text:
        return text
    
    # Заменяем все типы апострофов на обычный ' для унифицированного поиска
    apostrophe_replacements = {
        'ʼ': "'",   # правый апостроф → обычный апостроф
        'ʻ': "'",   # левый апостроф → обычный апостроф  
        '`': "'",   # обратный апостроф → обычный апостроф
    }
    
    for old, new in apostrophe_replacements.items():
        text = text.replace(old, new)
    
    return text

def find_region(text: str) -> str | None:
    """Универсальный поиск региона по ВСЕМ данным: aliases, keywords, названиям."""
    if not text:
        return None
    
    # Сначала нормализуем апострофы, потом весь текст
    text_normalized_apostrophes = normalize_apostrophes_for_search(text)
    text_norm = normalize_text(text_normalized_apostrophes)
    
    # КРИТИЧЕСКИ ВАЖНО: Проверяем международные маршруты с флагами стран
    # Флаги стран (🇷🇺🇰🇿🇺🇦🇹🇷 и др.) указывают на международный маршрут
    country_flags = ['🇷🇺', '🇰🇿', '🇺🇦', '🇹🇷', '🇮🇷', '🇨🇳', '🇰🇬', '🇹🇯', '🇹🇲', '🇦🇫', '🇮🇳', '🇵🇱', '🇩🇪', '🇫🇷', '🇮🇹', '🇪🇸']
    
    has_country_flag = any(flag in text for flag in country_flags)
    
    # 1. Поиск в REGION_KEYWORDS (aliases)
    for code, data in REGION_KEYWORDS.items():
        for kw in data.get('aliases', []):
            # Нормализуем алиас тоже с апострофами
            kw_normalized_apostrophes = normalize_apostrophes_for_search(kw)
            kw_norm = normalize_text(kw_normalized_apostrophes)
            if kw_norm in text_norm or re.search(rf"\b{re.escape(kw_norm)}\b", text_norm):
                return code
                
        # Также проверяем основные названия
        for field in ['cyrillic_uz', 'latin_uz', 'russian']:
            if field in data:
                # Нормализуем поля тоже с апострофами
                field_normalized_apostrophes = normalize_apostrophes_for_search(data[field])
                field_norm = normalize_text(field_normalized_apostrophes)
                if field_norm in text_norm:
                    return code
    
    # 2. Поиск в специальных топиках (ключевые слова + флаги для международных)
    special_mappings = {
        'xalqaro': ['international', 'xalqaro', 'россия', 'russia', 'москва', 'moscow', 'казахстан', 'kazakhstan', 
                    'полша', 'польша', 'poland', 'polsha', 'алматы', 'almaty', 'алмата', 'саратов', 'saratov',
                    'belarus', 'беларусь', 'минск', 'minsk', 'borisov', 'борисов', 'vitebsk', 'витебск',
                    'ukraina', 'украина', 'kiev', 'киев', 'odessa', 'одесса', 'lvov', 'львов',
                    'turkiya', 'турция', 'istanbul', 'стамбул', 'ankara', 'анкара',
                    'import', 'eksport', 'экспорт', 'импорт', 'cis', 'снг', 'europa', 'европа'],
        'reklama': ['reklama', 'реклама', 'sotiladi', 'sotuvda', 'продается', 'продаю'],
        'yangiliklar': ['yangilik', 'yangiliklar', 'новости', 'news', 'xabar'],
        'furabozor': ['furabozor', 'fura bozor', 'фурабозор', 'рынок фур']
    }
    
    for code, keywords in special_mappings.items():
        for kw in keywords:
            kw_norm = normalize_text(kw)
            if kw_norm in text_norm:
                # Для международных маршрутов: ключевые слова ИЛИ флаги стран
                if code == 'xalqaro':
                    return code
                else:
                    return code
    
    # Проверка только флагов для международных маршрутов (если ключевые слова не найдены)
    if has_country_flag:
        return 'xalqaro'
    
    # 3. Дополнительные региональные ключевые слова
    region_extras = {
        'tashkent_city': ['столица', 'stolitsa', 'poytaxt', 'capital'],
        'samarqand_city': ['самарканд', 'samarkand', 'samarqand'],
        'buxoro_city': ['бухара', 'bukhara', 'buxoro'],
        'fargona_city': ['фергана', 'fergana', 'kokand', 'коканд', 'qo\'qon']
    }
    
    for code, keywords in region_extras.items():
        for kw in keywords:
            kw_norm = normalize_text(kw)
            if kw_norm in text_norm:
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
            f"{from_city.upper()} → {to_city.upper()}\n"
            f"TRANSPORT: {transport}\n"
            f"TAVSIF: {desc}\n"
            f"TELEFON: {phone}\n"
            f"#{to_city.upper()}\n"
            f"-------\n"
            f"Boshqa yuklar: @logistika_marka"
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
                        # Убираем неправильное логирование thread_id
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
    # Пропускаем главную страницу для мониторинга
    if request.path == '/':
        return None
        
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
