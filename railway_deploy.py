#!/usr/bin/env python3
"""
RENDER DEPLOYMENT - ПОЛНАЯ НЕЗАВИСИМОСТЬ
Работает без Replit, 24/7, полностью бесплатно
ОБНОВЛЕННАЯ ЛОГИКА ОБРАБОТКИ МАРШРУТОВ
"""
import os
import sys
import time
import signal
import logging
import threading
import re
from datetime import datetime
from flask import Flask
import requests
import schedule

# Настройки
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
MAIN_GROUP_ID = -1002259378109
ADMIN_USER_ID = 8101326669
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# РАСШИРЕННАЯ БАЗА ГЕОГРАФИЧЕСКИХ НАЗВАНИЙ (трилингвальная)
REGION_KEYWORDS = {
    # АНДИЖАН
    'andijon': {
        'topic_id': 101387,
        'keywords': [
            # Латиница
            'andijon', 'andijan', 'andijondan', 'andijonega', 'asaka', 'asakadan', 'asakaga', 'baliqchi', 'boz', 'buloqboshi', 'izboskan', 
            'jalaquduq', 'marhamat', 'oltinko\'l', 'oltinkol', 'paxtaobod', 'qo\'rg\'ontepa',
            'qorgontepa', 'shahrixon', 'ulug\'nor', 'ulugnor', 'xo\'jaobod', 'xojaobod',
            # Кирилица узбекская
            'андижон', 'асака', 'балиқчи', 'боз', 'булоқбоши', 'избоскан', 'жалақудуқ',
            'марҳамат', 'олтинкўл', 'пахтаобод', 'қўрғонтепа', 'шаҳрихон', 'улуғнор', 'хўжаобод',
            # Русский
            'андижан', 'асака', 'балыкчи', 'избаскан', 'мархамат', 'пахтаабад', 'шахрихан'
        ]
    },
    
    # БУХАРА
    'buxoro': {
        'topic_id': 101372,
        'keywords': [
            # Латиница
            'buxoro', 'bukhara', 'buxorodan', 'buxoroga', 'bukharadan', 'bukharaga', 'alat', 'g\'ijduvon', 'gijduvon', 'jondor', 'kogon', 'qorako\'l',
            'qarakol', 'qorovulbozor', 'romitan', 'shofirkon', 'vobkent', 'peshku',
            # Кирилица узбекская  
            'бухоро', 'алат', 'ғиждувон', 'жондор', 'когон', 'қоракўл', 'қоровулбозор',
            'ромитан', 'шофиркон', 'вобкент', 'пешку',
            # Русский
            'бухара', 'алат', 'гиждуван', 'каган', 'каракуль', 'ромитан', 'шафиркан', 'вабкент'
        ]
    },
    
    # ФЕРГАНА
    'fargona': {
        'topic_id': 101382,
        'keywords': [
            # Латиница
            'farg\'ona', 'fargona', 'fergana', 'fargonodan', 'fargonega', 'farganaga', 'фаргонага', 'фергонага', 'beshariq', 'bog\'dod', 'bogdod', 'buvayda',
            'dang\'ara', 'dangara', 'farg\'ona', 'furqat', 'oltiariq', 'qo\'shtepa', 'qoshtepa',
            'quva', 'rishton', 'so\'x', 'sox', 'toshloq', 'uchko\'prik', 'uchkoprik', 'uzbekiston',
            'yozyovon', 'qo\'qon', 'qoqon', 'quqon', 'kokand',
            # Кирилица узбекская
            'фарғона', 'бешариқ', 'боғдод', 'бувайда', 'данғара', 'фурқат', 'олтиариқ',
            'қўштепа', 'қува', 'риштон', 'сўх', 'тошлоқ', 'учкўприк', 'ўзбекистон', 'ёзёвон',
            'қўқон',
            # Русский
            'фергана', 'бешарык', 'богдад', 'бувайда', 'дангара', 'фуркат', 'алтиарык',
            'кувасай', 'риштан', 'сох', 'ташлак', 'учкуприк', 'язъяван', 'коканд', 'кокан'
        ]
    },
    
    # ДЖИЗАК
    'jizzax': {
        'topic_id': 101377,
        'keywords': [
            # Латиница
            'jizzax', 'jizak', 'arnasoy', 'baxmal', 'do\'stlik', 'dostlik', 'forish', 'g\'allaorol',
            'gallaorol', 'mirzacho\'l', 'mirzachol', 'paxtakor', 'yangiobod', 'zafarobod', 'zarbdor',
            'zomin',
            # Кирилица узбекская
            'жиззах', 'арнасой', 'бахмал', 'дўстлик', 'фориш', 'ғаллаорол', 'мирзачўл',
            'пахтакор', 'янгиобод', 'зафаробод', 'зарбдор', 'зомин',
            # Русский
            'джизак', 'арнасай', 'бахмал', 'дустлик', 'фариш', 'галляарал', 'мирзачуль',
            'пахтакор', 'янгиабад', 'зафарабад', 'зарбдар', 'зомин'
        ]
    },
    
    # КАШКАДАРЬЯ
    'qashqadaryo': {
        'topic_id': 101380,
        'keywords': [
            # Латиница
            'qashqadaryo', 'qarshi', 'karshi', 'chiroqchi', 'dehqonobod', 'g\'uzor', 'guzor',
            'kasbi', 'kitob', 'koson', 'mirishkor', 'muborak', 'nishon', 'qamashi', 'shahrisabz',
            'yakkabog\'', 'yakkabog', 'shakhrisabz',
            # Кирилица узбекская
            'қашқадарё', 'қарши', 'чироқчи', 'деҳқонобод', 'ғузор', 'касби', 'китоб', 'косон',
            'миришкор', 'муборак', 'нишон', 'қамаши', 'шаҳрисабз', 'яккабоғ',
            # Русский
            'кашкадарья', 'карши', 'чиракчи', 'дехканабад', 'гузар', 'касби', 'китаб', 'косон',
            'миришкор', 'мубарек', 'нишан', 'камаши', 'шахрисабз', 'яккабаг'
        ]
    },
    
    # НАМАНГАН
    'namangan': {
        'topic_id': 101383,
        'keywords': [
            # Латиница
            'namangan', 'chortoq', 'chust', 'kosonsoy', 'mingbuloq', 'norin', 'pop', 'to\'raqo\'rg\'on',
            'toraqorgon', 'uchqo\'rg\'on', 'uchqorgon', 'uychi', 'yangiqo\'rg\'on', 'yangiqorgon',
            # Кирилица узбекская
            'наманган', 'чортоқ', 'чуст', 'косонсой', 'мингбулоқ', 'норин', 'поп', 'тўрақўрғон',
            'учқўрғон', 'уйчи', 'янгиқўрғон',
            # Русский
            'наманган', 'чартак', 'чуст', 'косонсай', 'мингбулак', 'норин', 'поп', 'туракурган',
            'учкурган', 'уйчи', 'янгикурган'
        ]
    },
    
    # НАВОИ
    'navoiy': {
        'topic_id': 101379,
        'keywords': [
            # Латиница
            'navoiy', 'karmana', 'konimex', 'navbahor', 'nurota', 'qiziltepa', 'tomdi', 'uchquduq',
            'xatirchi', 'zarafshon',
            # Кирилица узбекская
            'навоий', 'кармана', 'конимех', 'навбаҳор', 'нурота', 'қизилтепа', 'томди', 'учқудуқ',
            'хатирчи', 'зарафшон',
            # Русский
            'навои', 'кармана', 'конимех', 'навбахар', 'нурата', 'кызылтепа', 'томды', 'учкудук',
            'хатырчи', 'зарафшан'
        ]
    },
    
    # КАРАКАЛПАКСТАН
    'qoraqalpogiston': {
        'topic_id': 101381,
        'keywords': [
            # Латиница
            'qoraqalpog\'iston', 'qoraqalpogiston', 'nukus', 'amudaryo', 'beruniy', 'bo\'zatov',
            'bozatov', 'ellikqala', 'kegeyli', 'qonliko\'l', 'qanlykol', 'qo\'ng\'irot', 'qongirot',
            'mo\'ynoq', 'moynoq', 'shumanay', 'taxtako\'pir', 'taxtakopir', 'to\'rtko\'l', 'tortkol',
            'xo\'jayli', 'xojayli', 'chimboy',
            # Кирилица узбекская
            'қорақалпоғистон', 'нукус', 'амударё', 'беруний', 'бўзатов', 'елликқала', 'кегейли',
            'қонликўл', 'қўнғирот', 'мўйноқ', 'шуманай', 'тахтакўпир', 'тўрткўл', 'хўжайли', 'чимбой',
            # Русский
            'каракалпакстан', 'нукус', 'амударья', 'беруни', 'бузатау', 'елликкала', 'кегейли',
            'канлыкуль', 'кунград', 'муйнак', 'шуманай', 'тахтакупыр', 'турткуль', 'ходжейли', 'чимбай'
        ]
    },
    
    # САМАРКАНД
    'samarqand': {
        'topic_id': 101369,
        'keywords': [
            # Латиница
            'samarqand', 'samarkand', 'bulungur', 'ishtixon', 'jomboy', 'kattaqo\'rg\'on', 'kattaqorgon',
            'narpay', 'nurobod', 'oqdaryo', 'payariq', 'pastdarg\'om', 'pastdargom', 'paxtachi',
            'qo\'shrabot', 'qoshrabot', 'samarqand', 'toyloq', 'urgut',
            # Кирилица узбекская
            'самарқанд', 'булунғур', 'иштихон', 'жомбой', 'каттақўрғон', 'нарпай', 'нуробод',
            'оқдарё', 'паяриқ', 'пастдарғом', 'пахтачи', 'қўшработ', 'тойлоқ', 'урғут',
            # Русский
            'самарканд', 'булунгур', 'иштыхан', 'джамбай', 'каттакурган', 'нарпай', 'нурабад',
            'акдарья', 'пайарык', 'пастдаргом', 'пахтачи', 'кошрабат', 'тайляк', 'ургут'
        ]
    },
    
    # СИРДАРЬЯ
    'sirdaryo': {
        'topic_id': 101378,
        'keywords': [
            # Латиница
            'sirdaryo', 'guliston', 'boyovut', 'mirzaobod', 'oqoltin', 'sardoba', 'sayxunobod',
            'sirdaryo', 'xavos',
            # Кирилица узбекская
            'сирдарё', 'гулистон', 'боёвут', 'мирзаобод', 'оқолтин', 'сардоба', 'сайхунобод',
            'хавос',
            # Русский
            'сырдарья', 'гулистан', 'баяут', 'мирзаабад', 'акалтын', 'сардоба', 'сайхунабад',
            'хавас'
        ]
    },
    
    # СУРХАНДАРЬЯ
    'surxondaryo': {
        'topic_id': 101363,
        'keywords': [
            # Латиница
            'surxondaryo', 'termiz', 'termez', 'angor', 'bandixon', 'boysun', 'denov', 'jarqo\'rg\'on',
            'jarqorgon', 'qiziriq', 'qo\'mqo\'rg\'on', 'qomqorgon', 'sario\'siya', 'sarioosiya',
            'sherobod', 'sho\'rchi', 'shorchi', 'uzun',
            # Кирилица узбекская
            'сурхондарё', 'термиз', 'ангор', 'бандихон', 'бойсун', 'денов', 'жарқўрғон',
            'қизириқ', 'қўмқўрғон', 'сариосия', 'шеробод', 'шўрчи', 'узун',
            # Русский
            'сурхандарья', 'термез', 'ангор', 'бандыхан', 'байсун', 'денау', 'джаркурган',
            'кызырык', 'кумкурган', 'сариасия', 'шерабад', 'шурчи', 'узун'
        ]
    },
    
    # ТАШКЕНТ
    'toshkent': {
        'topic_id': 101362,
        'keywords': [
            # Латиница
            'toshkent', 'tashkent', 'toshkentdan', 'toshkentga', 'tashkentdan', 'tashkentga', 'bekobod', 'bo\'stonliq', 'bostonliq', 'bo\'ka', 'boka',
            'chinoz', 'qibray', 'oqqo\'rg\'on', 'oqqorgon', 'olmaliq', 'ohangaron', 'parkent',
            'piskent', 'quyi chirchiq', 'yuqori chirchiq', 'yangiyul', 'yangiyo\'l', 'zangota',
            'g\'azalkent', 'gazalkent',
            # Кирилица узбекская
            'тошкент', 'бекобод', 'бўстонлиқ', 'бўка', 'чиноз', 'қибрай', 'оққўрғон',
            'олмалиқ', 'охангарон', 'паркент', 'пискент', 'қуйи чирчиқ', 'юқори чирчиқ',
            'янгиюл', 'зангота', 'ғазалкент',
            # Русский
            'ташкент', 'бекабад', 'бустанлык', 'бука', 'чиназ', 'кибрай', 'аккурган',
            'алмалык', 'ахангаран', 'паркент', 'пскент', 'куйи чирчик', 'юкори чирчик',
            'янгиюль', 'зангата', 'газалкент'
        ]
    },
    
    # ХОРЕЗМ
    'xorazm': {
        'topic_id': 101660,
        'keywords': [
            # Латиница
            'xorazm', 'urganch', 'bog\'ot', 'bogot', 'gurlan', 'xonqa', 'xiva', 'yangiariq',
            'yangibozor', 'shovot', 'qo\'shko\'pir', 'qoshkopir', 'tuproqqala', 'hazarasp',
            # Кирилица узбекская
            'хоразм', 'урганч', 'боғот', 'гурлан', 'хонқа', 'хива', 'янгиариқ',
            'янгибозор', 'шовот', 'қўшкўпир', 'тупроққала', 'хазарасп',
            # Русский
            'хорезм', 'ургенч', 'багат', 'гурлен', 'ханка', 'хива', 'янгиарык',
            'янгибазар', 'шават', 'кошкупыр', 'туπроккала', 'хазарасп'
        ]
    },
    
    # МЕЖДУНАРОДНЫЕ НАПРАВЛЕНИЯ
    'xalqaro': {
        'topic_id': 101367,
        'keywords': [
            # Латиница
            'russia', 'rossiya', 'moskva', 'moskvadan', 'moskvaga', 'spb', 'piter', 'kazan', 'novosibirsk', 'ufa', 'astana',
            'almaty', 'bishkek', 'dushanbe', 'tehran', 'istanbul', 'ankara', 'baku', 'tbilisi',
            'kiyev', 'minsk', 'riga', 'tallin', 'vilnyus', 'prayga', 'berlin', 'parej', 'london',
            'xitoy', 'china', 'urumchi', 'beijing', 'eron', 'iran', 'afg\'oniston', 'afganistan',
            'pokiston', 'pakistan', 'hindiston', 'india', 'turkiya', 'turkey', 'germaniya', 'germany',
            # Кирилица узбекская
            'россия', 'москва', 'қозон', 'новосибирск', 'уфа', 'астана', 'алмаота', 'бишкек',
            'душанбе', 'теҳрон', 'истанбул', 'анқара', 'боку', 'тбилиси', 'киев', 'минск',
            'хитой', 'урумчи', 'пекин', 'эрон', 'афғонистон', 'покистон', 'ҳиндистон', 'туркия',
            'германия',
            # Русский
            'россия', 'москва', 'масква', 'маскавдан', 'масквадан', 'москвадан', 'москвага', 'спб', 'питер', 'казань', 'новосибирск', 'уфа', 'астана',
            'алматы', 'бишкек', 'душанбе', 'тегеран', 'стамбул', 'анкара', 'баку', 'тбилиси',
            'киев', 'минск', 'рига', 'таллин', 'вильнюс', 'прага', 'берлин', 'париж', 'лондон',
            'китай', 'урумчи', 'пекин', 'иран', 'афганистан', 'пакистан', 'индия', 'турция', 'германия',
            'петропавловск', 'ульяновск', 'арысь'
        ]
    }
}

# Служебные топики
SERVICE_TOPICS = {
    'fura': 101361,      # Fura bozor
    'reklama': 101360,   # REKLAMA  
    'yangiliklar': 101359 # Yangiliklar
}

# Логирование
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)

# Глобальные переменные
message_count = 0
last_update_id = 0
bot_start_time = datetime.now()

def send_message(chat_id, text, message_thread_id=None):
    """Отправка сообщения"""
    global message_count
    try:
        data = {'chat_id': chat_id, 'text': text}
        if message_thread_id:
            data['message_thread_id'] = message_thread_id
            
        response = requests.post(f"{API_URL}/sendMessage", json=data, timeout=10)
        success = response.json().get('ok', False)
        
        if success:
            message_count += 1
            logger.info(f"✅ Сообщение {message_count} отправлено в топик {message_thread_id}")
        
        return success
    except Exception as e:
        logger.error(f"❌ Ошибка отправки: {e}")
        return False

def extract_phone_number(text):
    """Извлечение номера телефона из текста"""
    phone_patterns = [
        r'\b(\+?998)?[-\s]?(\d{2})[-\s]?(\d{3})[-\s]?(\d{2})[-\s]?(\d{2})\b',
        r'\b(\d{9})\b',
        r'\b(\d{2}[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2})\b'
    ]
    
    for pattern in phone_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return "Ko'rsatilmagan"

def extract_route_and_cargo(text):
    """Извлечение маршрута и груза из текста"""
    # Поиск маршрута (ГОРОД - ГОРОД)
    route_pattern = r'([A-Z][A-Za-z]+)\s*[-–]\s*([A-Z][A-Za-z]+)'
    route_match = re.search(route_pattern, text.upper())
    
    if route_match:
        from_city = route_match.group(1).lower()
        to_city = route_match.group(2).lower()
        
        # Остальной текст без маршрута
        cargo_text = text.replace(route_match.group(0), '').strip()
        
        return from_city, to_city, cargo_text
    
    return None, None, text

def format_cargo_text(cargo_text):
    """Форматирование текста груза"""
    # Убираем лишние пробелы и переводы строк
    lines = [line.strip() for line in cargo_text.split('\n') if line.strip()]
    
    # Первая строка - тип транспорта/груза
    transport_type = "Transport"
    cargo_description = ""
    
    if lines:
        first_line = lines[0]
        if any(word in first_line.upper() for word in ['ISUZU', 'KAMAZ', 'GAZEL', 'TRUCK']):
            transport_type = first_line.title()
            cargo_description = ' '.join(lines[1:]) if len(lines) > 1 else ""
        else:
            cargo_description = ' '.join(lines)
    
    return transport_type, cargo_description

def process_message(message):
    """Обработка сообщения"""
    try:
        if not message.get('text'):
            return
            
        text = message['text']
        chat_id = message['chat']['id']
        
        if chat_id != MAIN_GROUP_ID:
            return
        
        # Извлечение маршрута и груза
        from_city, to_city, cargo_text = extract_route_and_cargo(text)
        
        if not from_city or not to_city:
            return
            
        # Поиск региона по ключевым словам
        def find_region_by_text(text):
            text_lower = text.lower()
            # Убираем знаки препинания и разбиваем на слова
            import re
            words = re.findall(r'\b\w+\b', text_lower)
            
            for region_key, region_data in REGION_KEYWORDS.items():
                for keyword in region_data['keywords']:
                    # Проверяем точное совпадение слова или вхождение
                    if keyword.lower() in words or keyword.lower() in text_lower:
                        return region_key
            return None
        
        # ПРИОРИТЕТ: международные направления
        from_city_region = find_region_by_text(from_city)
        to_city_region = find_region_by_text(to_city)
        
        topic_keyword = None
        
        # Если отправление из-за границы или назначение за границу - в xalqaro
        if from_city_region == 'xalqaro' or to_city_region == 'xalqaro':
            topic_keyword = 'xalqaro'
        # Иначе приоритет по отправлению
        elif from_city_region:
            topic_keyword = from_city_region
        # Затем по назначению
        elif to_city_region:
            topic_keyword = to_city_region
        # В крайнем случае по всему тексту
        else:
            topic_keyword = find_region_by_text(text)
                    
        if not topic_keyword:
            return
            
        # Получение информации о пользователе
        sender_name = message.get('from', {}).get('first_name', 'Anonim')
        sender_username = message.get('from', {}).get('username')
        sender_link = f"https://t.me/{sender_username}" if sender_username else sender_name
        
        # Извлечение телефона
        phone = extract_phone_number(text)
        
        # Форматирование груза
        transport_type, cargo_description = format_cargo_text(cargo_text)
        
        # Форматирование сообщения
        formatted_text = f"""{from_city.upper()} - {to_city.upper()}

🚛 {transport_type}

💬 {cargo_description}

☎️ {phone}

👤 {sender_link}

#{to_city.upper()}
➖➖➖➖➖➖➖➖➖➖➖➖➖➖
Boshqa yuklar: @logistika_marka"""

        # Отправка в топик
        topic_id = REGION_KEYWORDS[topic_keyword]['topic_id']
        success = send_message(MAIN_GROUP_ID, formatted_text, topic_id)
        
        if success:
            logger.info(f"🎯 {from_city} -> {to_city} ({topic_keyword}): {transport_type}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки: {e}")

def handle_admin_command(message):
    """Обработка команд админа"""
    try:
        if message.get('from', {}).get('id') != ADMIN_USER_ID:
            return
            
        text = message.get('text', '')
        user_id = message['from']['id']
        
        if text == '/status':
            uptime = datetime.now() - bot_start_time
            hours = int(uptime.total_seconds() // 3600)
            minutes = int((uptime.total_seconds() % 3600) // 60)
            
            status = f"""🟢 RENDER BOT АКТИВЕН
📊 Обработано: {message_count} сообщений
⏰ Время работы: {hours}ч {minutes}м
📋 Регионов: {len(REGION_KEYWORDS)} ({sum(len(data['keywords']) for data in REGION_KEYWORDS.values())} ключевых слов)
🔄 Update: {last_update_id}
🚀 Платформа: Render.com (БЕСПЛАТНО!)
💰 Стоимость: $0"""
            send_message(user_id, status)
            
    except Exception as e:
        logger.error(f"❌ Ошибка команды: {e}")

def get_updates():
    """Получение обновлений от Telegram"""
    global last_update_id
    try:
        params = {
            'offset': last_update_id + 1,
            'timeout': 30,
            'allowed_updates': ['message']
        }
        
        response = requests.get(f"{API_URL}/getUpdates", params=params, timeout=35)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                return data.get('result', [])
        return []
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения: {e}")
        return []

def keep_alive_ping():
    """Пинг для поддержания активности"""
    try:
        # Самопинг для предотвращения засыпания
        response = requests.get("https://yukmarkazi-bot.onrender.com/ping", timeout=5)
        logger.info(f"🏓 Keep-alive ping: {response.status_code}")
    except Exception as e:
        logger.info(f"🏓 Keep-alive ping failed: {e}")

def admin_hourly_report():
    """Ежечасный отчет админу"""
    try:
        uptime = datetime.now() - bot_start_time
        hours = int(uptime.total_seconds() // 3600)
        
        report = f"""⏰ HOURLY REPORT
🟢 Render Bot Online
📊 Messages: {message_count}
⏰ Uptime: {hours}h
🌐 Platform: Render.com FREE"""
        
        send_message(ADMIN_USER_ID, report)
    except Exception as e:
        logger.error(f"❌ Ошибка отчета: {e}")

def schedule_tasks():
    """Планировщик задач"""
    # Пинг каждые 10 минут (предотвращает 15-минутное засыпание)
    schedule.every(10).minutes.do(keep_alive_ping)
    
    # Ежечасный отчет админу
    schedule.every().hour.do(admin_hourly_report)

def run_scheduler():
    """Запуск планировщика в отдельном потоке"""
    while True:
        schedule.run_pending()
        time.sleep(60)  # Проверка каждую минуту

def bot_main_loop():
    """Основной цикл бота"""
    global last_update_id
    
    logger.info("🚀 RENDER BOT ЗАПУЩЕН С KEEP-ALIVE")
    
    # Настройка планировщика
    schedule_tasks()
    
    # Запуск планировщика в отдельном потоке
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    # Уведомление админу
    send_message(ADMIN_USER_ID, "🚀 RENDER BOT ЗАПУЩЕН - ANTI-SLEEP СИСТЕМА АКТИВНА!")
    
    # Первый пинг сразу
    keep_alive_ping()
    
    while True:
        try:
            updates = get_updates()
            
            for update in updates:
                last_update_id = update['update_id']
                
                if 'message' in update:
                    message = update['message']
                    
                    # Команды админа
                    if message.get('from', {}).get('id') == ADMIN_USER_ID:
                        handle_admin_command(message)
                    
                    # Обработка сообщений
                    process_message(message)
                    
        except Exception as e:
            logger.error(f"❌ Ошибка в цикле: {e}")
            time.sleep(5)
            continue
            
        time.sleep(1)

# Flask приложение для Render
app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health():
    uptime = datetime.now() - bot_start_time
    return {
        'status': 'running',
        'platform': 'Render.com',
        'uptime_seconds': int(uptime.total_seconds()),
        'messages_processed': message_count,
        'last_update_id': last_update_id,
        'time': datetime.now().isoformat()
    }

@app.route('/ping')
def ping():
    return {
        'status': 'pong',
        'time': datetime.now().isoformat(),
        'uptime': int((datetime.now() - bot_start_time).total_seconds()),
        'messages': message_count
    }

@app.route('/keep-alive')
def keep_alive():
    return {
        'status': 'alive',
        'platform': 'Render.com',
        'anti_sleep': True,
        'time': datetime.now().isoformat()
    }

def run_web_server():
    """Веб-сервер для Render health checks"""
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == "__main__":
    # Запуск веб-сервера в отдельном потоке
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # Основной цикл бота
    bot_main_loop()
