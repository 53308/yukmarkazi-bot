#!/usr/bin/env python3
"""
RENDER DEPLOYMENT - ФИНАЛЬНАЯ ВЕРСИЯ
Работает без Replit, 24/7, полностью бесплатно
ОБНОВЛЕННАЯ ЛОГИКА ОБРАБОТКИ МАРШРУТОВ + ПОДДЕРЖКА -DAN/-GA
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

# Настройки
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
MAIN_GROUP_ID = -1002259378109
ADMIN_USER_ID = 8101326669
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# РАСШИРЕННАЯ БАЗА ГЕОГРАФИЧЕСКИХ НАЗВАНИЙ (трилингвальная) с -DAN/-GA
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
            'қўштепа', 'қува', 'риштон', 'сўх', 'тошлоқ', 'учкўприк', 'ёзёвон', 'қўқон',
            # Русский
            'фергана', 'бешарык', 'багдад', 'бувайда', 'дангара', 'фуркат', 'алтыарык',
            'куштепа', 'кува', 'риштан', 'сох', 'ташлак', 'учкуприк', 'язъяван', 'коканд'
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
            'олмалиқ', 'оҳангарон', 'паркент', 'пискент', 'қуйи чирчиқ', 'юқори чирчиқ',
            'янгиюл', 'зангота', 'ғазалкент',
            # Русский
            'ташкент', 'бекабад', 'бустанлык', 'бука', 'чиназ', 'кибрай', 'аккурган',
            'алмалык', 'ахангаран', 'паркент', 'пскент', 'куйи чирчик', 'юкори чирчик',
            'янгиюль', 'зангата', 'газалкент'
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
    """Извлечение номера телефона"""
    phone_pattern = r'[\+]?[0-9]{1,4}[-\s]?[0-9]{2,3}[-\s]?[0-9]{3}[-\s]?[0-9]{2,4}[-\s]?[0-9]{2,4}'
    match = re.search(phone_pattern, text)
    return match.group() if match else "Telefon ko'rsatilmagan"

def extract_route_and_cargo(text):
    """Извлечение маршрута и информации о грузе"""
    # Паттерны для маршрутов
    route_pattern = r'([А-ЯЁа-яё\w\'\-]+)[\s\-→–]+([А-ЯЁа-яё\w\'\-]+)'
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

def bot_main_loop():
    """Основной цикл бота"""
    global last_update_id
    
    logger.info("🚀 RENDER BOT ЗАПУЩЕН С ПОДДЕРЖКОЙ -DAN/-GA")
    
    # Уведомление админу
    send_message(ADMIN_USER_ID, "🚀 RENDER BOT ЗАПУЩЕН - ПОДДЕРЖКА УЗБЕКСКИХ ПРИСТАВОК АКТИВНА!")
    
    while True:
        try:
            updates = get_updates()
            
            for update in updates:
                last_update_id = update['update_id']
                
                if 'message' in update:
                    message = update['message']
                    process_message(message)
                    
        except Exception as e:
            logger.error(f"❌ Ошибка в цикле: {e}")
            time.sleep(5)
            continue
            
        time.sleep(1)

# Flask приложение для Render
app = Flask(__name__)

@app.route('/')
def home():
    uptime = datetime.now() - bot_start_time
    hours = int(uptime.total_seconds() // 3600)
    minutes = int((uptime.total_seconds() % 3600) // 60)
    
    return f"""
    <h1>YukMarkazi Bot - АКТИВЕН</h1>
    <p>Сообщений обработано: {message_count}</p>
    <p>Время работы: {hours}ч {minutes}м</p>
    <p>Регионов: {len(REGION_KEYWORDS)}</p>
    <p>Ключевых слов: {sum(len(data['keywords']) for data in REGION_KEYWORDS.values())}</p>
    <p>Поддержка узбекских приставок: -DAN/-GA</p>
    <p>Последний update: {last_update_id}</p>
    """

@app.route('/health')
def health():
    return {'status': 'ok', 'messages': message_count}

@app.route('/ping')
def ping():
    return 'pong'

def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    logger.info("🛑 Получен сигнал завершения")
    sys.exit(0)

if __name__ == '__main__':
    # Обработка сигналов
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Запуск бота в отдельном потоке
    bot_thread = threading.Thread(target=bot_main_loop, daemon=True)
    bot_thread.start()
    
    # Запуск Flask приложения
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
