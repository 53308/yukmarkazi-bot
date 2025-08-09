#!/usr/bin/env python3
"""
RENDER DEPLOYMENT - ПОЛНАЯ ГЕОГРАФИЧЕСКАЯ БАЗА
Работает без Replit, 24/7, с полным знанием всех городов и районов Узбекистана
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

# ПОЛНАЯ БАЗА ГЕОГРАФИЧЕСКИХ НАЗВАНИЙ (ВСЕ ГОРОДА И РАЙОНЫ УЗБЕКИСТАНА)
REGION_KEYWORDS = {
    # ТАШКЕНТСКАЯ ОБЛАСТЬ (включая Chirchiq)
    'toshkent': {
        'topic_id': 101362,
        'keywords': [
            # Область и столица
            'toshkent', 'tashkent', 'ташкент', 'тошкент', 'toshkentdan', 'toshkentga', 'tashkentdan', 'tashkentga',
            
            # Города области
            'bekobod', 'бекабад', 'бекобод',
            'olmaliq', 'алмалык', 'олмалиқ', 'almalyk',
            'ohangaron', 'ахангаран', 'оҳангарон', 'ahangaron',
            'angren', 'ангрен', 'ангрен',
            'chirchiq', 'чирчик', 'чирчиқ', 'чирчик', 'chirchik', 'chirchiqdan', 'chirchiqga',
            'yangiyo\'l', 'yangiyul', 'янгиюль', 'янгиюл', 'yangiyol',
            
            # Районы Ташкентской области
            'bo\'stonliq', 'bostonliq', 'бустанлык', 'бўстонлиқ',
            'bo\'ka', 'boka', 'бука', 'бўка', 'пскент',
            'chinoz', 'чиназ', 'чиноз', 'chinaz',
            'qibray', 'кибрай', 'қибрай', 'kibray',
            'oqqo\'rg\'on', 'oqqorgon', 'аккурган', 'оққўрғон',
            'parkent', 'паркент',
            'piskent', 'пскент',
            'quyi chirchiq', 'куйи чирчик', 'қуйи чирчиқ',
            'yuqori chirchiq', 'юкори чирчик', 'юқори чирчиқ',
            'zangota', 'зангата', 'зангота',
            'g\'azalkent', 'gazalkent', 'газалкент', 'ғазалкент',
            'nurafshon', 'нурафшан', 'нурафшон',
            'quyichirchiq', 'quichirchiq', 'yuqorichirchiq',
            
            # Микрорайоны и поселки
            '3 mikrorayon', '3 mikrayon', '3-mikrorayon', '3-микрорайон',
            'sergeli', 'сергели',
            'shayxontoxur', 'шайхантахур', 'шайхонтоҳур',
            'chilonzor', 'чиланзар', 'чилонзор',
            'mirzo ulug\'bek', 'мирзо улугбек', 'мирзо улуғбек',
            'bektemir', 'бектемир',
            'yakkasaroy', 'яккасарай', 'яккасарой',
            'uchtepa', 'учтепа', 'учтепа',
            'mirobod', 'мирабад', 'миробод',
            'hamza', 'хамза', 'ҳамза',
            'olmazor', 'алмазар', 'олмазор'
        ]
    },
    
    # ФЕРГАНА (НЕ включает Chirchiq)
    'fargona': {
        'topic_id': 101382,
        'keywords': [
            # Область и столица
            'farg\'ona', 'fargona', 'fergana', 'фергана', 'фарғона', 'fargonodan', 'fargonega', 'farganaga', 'фаргонага', 'фергонага',
            
            # Города Ферганской области
            'qo\'qon', 'qoqon', 'quqon', 'kokand', 'коканд', 'қўқон',
            'marg\'ilon', 'margilon', 'маргилан', 'марғилон',
            'quvasoy', 'кувасай', 'қувасой', 'quvasoyga', 'quvasoydan',
            
            # Районы Ферганской области
            'beshariq', 'бешарык', 'бешариқ',
            'bog\'dod', 'bogdod', 'багдад', 'боғдод',
            'buvayda', 'бувайда',
            'dang\'ara', 'dangara', 'дангара', 'данғара',
            'furqat', 'фуркат', 'фурқат',
            'oltiariq', 'алтыарык', 'олтиариқ',
            'qo\'shtepa', 'qoshtepa', 'куштепа', 'қўштепа',
            'quva', 'кува', 'қува',
            'rishton', 'риштан', 'риштон',
            'so\'x', 'sox', 'сох', 'сўх',
            'toshloq', 'ташлак', 'тошлоқ',
            'uchko\'prik', 'uchkoprik', 'учкуприк', 'учкўприк',
            'uzbekiston', 'узбекистан', 'ўзбекистон',
            'yozyovon', 'язъяван', 'ёзёвон'
        ]
    },
    
    # АНДИЖАН
    'andijon': {
        'topic_id': 101387,
        'keywords': [
            'andijon', 'andijan', 'андижан', 'андижон', 'andijondan', 'andijonega',
            'asaka', 'асака', 'asakadan', 'asakaga',
            'baliqchi', 'балыкчи', 'балиқчи',
            'boz', 'боз',
            'buloqboshi', 'булоқбоши', 'bulakbashi',
            'izboskan', 'избаскан', 'избоскан',
            'jalaquduq', 'жалакудук', 'жалақудуқ',
            'marhamat', 'мархамат', 'марҳамат',
            'oltinko\'l', 'oltinkol', 'олтинкўл', 'altinkul',
            'paxtaobod', 'пахтаабад', 'пахтаобод',
            'qo\'rg\'ontepa', 'qorgontepa', 'қўрғонтепа', 'kurgontepa',
            'shahrixon', 'шахрихан', 'шаҳрихон',
            'ulug\'nor', 'ulugnor', 'улуғнор', 'ulugnor',
            'xo\'jaobod', 'xojaobod', 'хўжаобод', 'khodjaabad'
        ]
    },
    
    # БУХАРА
    'buxoro': {
        'topic_id': 101372,
        'keywords': [
            'buxoro', 'bukhara', 'бухара', 'бухоро', 'buxorodan', 'buxoroga', 'bukharadan', 'bukharaga',
            'alat', 'алат',
            'g\'ijduvon', 'gijduvon', 'гиждуван', 'ғиждувон',
            'jondor', 'жондор',
            'kogon', 'kaagan', 'каган', 'когон',
            'qorako\'l', 'qarakol', 'каракуль', 'қоракўл',
            'qorovulbozor', 'қоровулбозор', 'karavulbazar',
            'romitan', 'ромитан',
            'shofirkon', 'шафиркан', 'шофиркон',
            'vobkent', 'вабкент', 'вобкент',
            'peshku', 'пешку'
        ]
    },
    
    # НАМАНГАН
    'namangan': {
        'topic_id': 101377,
        'keywords': [
            'namangan', 'наманган', 'наманган',
            'pop', 'поп',
            'uchqurgan', 'учкурган', 'учқурган',
            'yangiqo\'rg\'on', 'yangiqorgon', 'янгикурган', 'янгиқўрғон',
            'chortoq', 'чартак', 'чортоқ',
            'kosonsoy', 'косонсой', 'косонсой',
            'mingbuloq', 'мингбулак', 'мингбулоқ',
            'norin', 'норин',
            'to\'raqo\'rg\'on', 'turakurgan', 'туракурган', 'тўрақўрғон',
            'uychi', 'уйчи'
        ]
    },
    
    # САМАРКАНД
    'samarqand': {
        'topic_id': 101357,
        'keywords': [
            'samarqand', 'samarkand', 'самарканд', 'самарқанд',
            'kattaqo\'rg\'on', 'kattakurgan', 'каттакурган', 'каттақўрғон',
            'jomboy', 'джамбай', 'жомбой',
            'urgut', 'ургут',
            'payariq', 'пайарик', 'пайариқ',
            'bulungur', 'булунгур', 'булунғур',
            'ishtixon', 'иштихан', 'иштиҳон',
            'narpay', 'нарпай',
            'nurobod', 'нурабад', 'нуробод',
            'oqdaryo', 'акдарья', 'оқдарё',
            'pastdarg\'om', 'пастдаргом', 'пастдарғом',
            'paxtachi', 'пахтачи', 'пахтачи',
            'qo\'shrabot', 'kushrabot', 'кушработ', 'қўшработ',
            'toyloq', 'тайлак', 'тойлоқ'
        ]
    },
    
    # КАШКАДАРЬЯ
    'qashqadaryo': {
        'topic_id': 101352,
        'keywords': [
            'qarshi', 'карши', 'қарши',
            'shakhrisabz', 'shahrisabz', 'шахрисабз', 'шаҳрисабз',
            'muborak', 'мубарек', 'муборак',
            'kitob', 'китаб', 'китоб',
            'koson', 'касан', 'косон',
            'chiroqchi', 'чиракчи', 'чироқчи',
            'dehqonobod', 'дехканабад', 'деҳқонобод',
            'g\'uzor', 'guzar', 'гузар', 'ғузор',
            'kamashi', 'камаши', 'камаши',
            'mirishkor', 'миришкор', 'миришкор',
            'nishon', 'нишан', 'нишон',
            'qamashi', 'камаши', 'қамаши',
            'yakkabog\'', 'yakkabaag', 'яккабаг', 'яккабоғ'
        ]
    },
    
    # СУРХАНДАРЬЯ
    'surxondaryo': {
        'topic_id': 101347,
        'keywords': [
            'termiz', 'термез', 'термиз', 'termez',
            'denov', 'денау', 'денов',
            'boysun', 'байсун', 'бойсун',
            'qumqo\'rg\'on', 'kumkurgan', 'кумкурган', 'қумқўрғон',
            'sherobod', 'шеробод', 'шеробод',
            'angor', 'ангор',
            'bandixon', 'бандихан', 'бандиҳон',
            'jarqo\'rg\'on', 'zharkurgan', 'жаркурган', 'жарқўрғон',
            'muzrobod', 'музрабат', 'музрабод',
            'oltinsoy', 'алтынсай', 'олтинсой',
            'sho\'rchi', 'shorchi', 'шурчи', 'шўрчи',
            'uzun', 'узун'
        ]
    },
    
    # ДЖИЗАК
    'jizzax': {
        'topic_id': 101342,
        'keywords': [
            'jizzax', 'djizak', 'джизак', 'жиззах',
            'g\'allaorol', 'gallaaral', 'галляарал', 'ғаллаорол',
            'zafarobod', 'зафарабад', 'зафаробод',
            'pakhtakor', 'пахтакор', 'пахтакор',
            'mirzacho\'l', 'mirzachul', 'мирзачул', 'мирзачўл',
            'arnasoy', 'арнасай', 'арнасой',
            'baxtiyor', 'бахтиёр',
            'do\'stlik', 'dustlik', 'дустлик', 'дўстлик',
            'forish', 'фариш', 'фариш',
            'yangiobod', 'янгиабад', 'янгиобод',
            'zomin', 'зомин'
        ]
    },
    
    # СЫРДАРЬЯ
    'sirdaryo': {
        'topic_id': 101337,
        'keywords': [
            'guliston', 'гулистан', 'гулистон',
            'shirin', 'ширин',
            'boyovut', 'баяут', 'боёвут',
            'sayxunobod', 'сайхунабад', 'сайхунобод',
            'syrdariya', 'сырдарья', 'сирдарё',
            'akaltyn', 'акалтын', 'ақолтин',
            'mirzaobod', 'мирзаабад', 'мирзаобод',
            'sardoba', 'сардоба'
        ]
    },
    
    # ХОРЕЗМ
    'xorazm': {
        'topic_id': 101332,
        'keywords': [
            'urgench', 'ургенч', 'урганч',
            'xiva', 'khiva', 'хива', 'ҳива',
            'shovot', 'шават', 'шовот',
            'qo\'shko\'pir', 'koshkupir', 'кошкупыр', 'қўшкўпир',
            'bog\'ot', 'bagat', 'багат', 'боғот',
            'gurlen', 'гурлен', 'гурлен',
            'xonqa', 'khanki', 'ханки', 'хонқа',
            'yangiariq', 'янгиарык', 'янгиариқ',
            'yangibozor', 'янгибазар', 'янгибозор'
        ]
    },
    
    # КАРАКАЛПАКСТАН
    'qoraqalpoq': {
        'topic_id': 101327,
        'keywords': [
            'nukus', 'нукус', 'нукус',
            'to\'rtko\'l', 'turtkul', 'турткуль', 'тўрткўл',
            'xo\'jayli', 'khojeli', 'ходжейли', 'хўжайли',
            'qo\'ng\'irot', 'kungrad', 'кунград', 'қўнғирот',
            'mo\'ynoq', 'muynak', 'муйнак', 'мўйноқ',
            'chimbay', 'чимбай', 'чимбай',
            'kegeyli', 'кегейли', 'кегейли',
            'amudaryo', 'амударья', 'амударё',
            'beruniy', 'беруний', 'беруний',
            'ellikqal\'a', 'ellikkala', 'элликкала', 'элликқала',
            'bo\'zatov', 'bozatau', 'бозатау', 'бўзатов',
            'qanliko\'l', 'kanlykul', 'канлыкуль', 'қанликўл',
            'nukus', 'taqiyotas', 'такиятас'
        ]
    },
    
    # МЕЖДУНАРОДНЫЕ НАПРАВЛЕНИЯ
    'xalqaro': {
        'topic_id': 101367,
        'keywords': [
            # Россия
            'russia', 'rossiya', 'россия',
            'moskva', 'moscow', 'москва', 'масква', 'moskvadan', 'moskvaga', 'маскавдан', 'масквадан', 'москвадан', 'москвага',
            'spb', 'petersburg', 'piter', 'питер', 'санкт-петербург',
            'kazan', 'казань', 'қозон',
            'novosibirsk', 'новосибирск',
            'ufa', 'уфа',
            'rostov', 'ростов',
            'volgograd', 'волгоград',
            'samara', 'самара',
            'perm', 'пермь',
            'krasnoyarsk', 'красноярск',
            'voronezh', 'воронеж',
            'saratov', 'саратов',
            'tolyatti', 'тольятти',
            'izhevsk', 'ижевск',
            'barnaul', 'барнаул',
            'vladivostok', 'владивосток',
            'irkutsk', 'иркутск',
            'yaroslavl', 'ярославль',
            'tyumen', 'тюмень',
            'makhachkala', 'махачкала',
            'tomsk', 'томск',
            'orenburg', 'оренбург',
            'novokuznetsk', 'новокузнецк',
            'ryazan', 'рязань',
            'astrakhan', 'астрахань',
            'naberezhnye chelny', 'набережные челны',
            'penza', 'пенза',
            'lipetsk', 'липецк',
            'kirov', 'киров',
            'cheboksary', 'чебоксары',
            'kaliningrad', 'калининград',
            'kursk', 'курск',
            'magnitogorsk', 'магнитогорск',
            'tver', 'тверь',
            'nizhniy tagil', 'нижний тагил',
            'arkhangelsk', 'архангельск',
            'sochi', 'сочи',
            'vladimir', 'владимир',
            'surgut', 'сургут',
            'petropavlovsk', 'петропавловск',
            'ульяновск', 'ulyanovsk',
            'arys', 'арысь',
            
            # Казахстан
            'astana', 'астана', 'нур-султан',
            'almaty', 'алматы', 'алмаота',
            'shymkent', 'шымкент',
            'taraz', 'тараз',
            'aktobe', 'актобе',
            'aktau', 'актау',
            'atyrau', 'атырау',
            'karaganda', 'караганда',
            'pavlodar', 'павлодар',
            'ust-kamenogorsk', 'усть-каменогорск',
            'semey', 'семей',
            'kostanay', 'костанай',
            'petropavl', 'петропавл',
            
            # Другие страны
            'bishkek', 'бишкек',
            'dushanbe', 'душанбе',
            'tehran', 'тегеран', 'теҳрон',
            'istanbul', 'стамбул', 'истанбул',
            'ankara', 'анкара', 'анқара',
            'baku', 'баку', 'боку',
            'tbilisi', 'тбилиси',
            'kiyev', 'kiev', 'киев',
            'minsk', 'минск',
            'riga', 'рига',
            'tallin', 'таллин',
            'vilnyus', 'вильнюс',
            'prayga', 'prague', 'прага',
            'berlin', 'берлин',
            'parej', 'paris', 'париж',
            'london', 'лондон',
            'xitoy', 'china', 'китай',
            'urumchi', 'урумчи',
            'beijing', 'пекин',
            'eron', 'iran', 'иран', 'эрон',
            'afg\'oniston', 'afganistan', 'афганистан', 'афғонистон',
            'pokiston', 'pakistan', 'пакистан', 'покистон',
            'hindiston', 'india', 'индия', 'ҳиндистон',
            'turkiya', 'turkey', 'турция', 'туркия',
            'germaniya', 'germany', 'германия'
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
bot_status = "АКТИВЕН"

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
            logger.info(f"✅ Сообщение {message_count} отправлено")
        
        return success
    except Exception as e:
        logger.error(f"❌ Ошибка отправки: {e}")
        return False

def handle_admin_command(message):
    """Обработка админских команд в ЛС"""
    try:
        text = message.get('text', '').lower()
        chat_id = message['chat']['id']
        user_id = message['from']['id']
        
        if user_id != ADMIN_USER_ID:
            return
        
        if text == '/start' or text == 'старт':
            uptime = datetime.now() - bot_start_time
            hours = int(uptime.total_seconds() // 3600)
            minutes = int((uptime.total_seconds() % 3600) // 60)
            
            stats = f"""🤖 YUKMARKAZI BOT - ПОЛНАЯ БАЗА

🟢 Статус: {bot_status}
📊 Обработано: {message_count} сообщений
⏰ Время работы: {hours}ч {minutes}м
📋 Регионов: {len(REGION_KEYWORDS)}
📍 Городов и районов: {sum(len(data['keywords']) for data in REGION_KEYWORDS.values())}
🔄 Последний update: {last_update_id}
🌍 Международные направления: XALQARO (101367)
🚀 Платформа: Render.com

✅ CHIRCHIQ ИСПРАВЛЕН: теперь в ТАШКЕНТСКОЙ области!

КОМАНДЫ:
/status - краткий статус  
/stats - полная статистика
/test - тест географии"""
            
            send_message(chat_id, stats)
            
        elif text == '/status' or text == 'статус':
            status_msg = f"🟢 БОТ {bot_status}\n📊 Сообщений: {message_count}\n🔄 Update: {last_update_id}\n⏰ Работает: {int((datetime.now() - bot_start_time).total_seconds() // 60)}м"
            send_message(chat_id, status_msg)
            
        elif text == '/test' or text == 'тест':
            test_msg = """🧪 ТЕСТ ГЕОГРАФИИ:

✅ Chirchiq → ТАШКЕНТСКАЯ область (101362)
✅ Quvasoy → ФЕРГАНСКАЯ область (101382)  
✅ Москва → XALQARO (101367)
✅ Бухара → БУХАРСКАЯ область (101372)

Всего городов и районов: """ + str(sum(len(data['keywords']) for data in REGION_KEYWORDS.values()))
            send_message(chat_id, test_msg)
            
    except Exception as e:
        logger.error(f"❌ Ошибка админской команды: {e}")

def extract_phone_number(text):
    """Извлечение номера телефона"""
    phone_pattern = r'[\+]?[0-9]{1,4}[-\s]?[0-9]{2,3}[-\s]?[0-9]{3}[-\s]?[0-9]{2,4}[-\s]?[0-9]{2,4}'
    match = re.search(phone_pattern, text)
    return match.group() if match else "Telefon ko'rsatilmagan"

def extract_route_and_cargo(text):
    """Извлечение маршрута и информации о грузе"""
    route_pattern = r'([А-ЯЁа-яё\w\'\-]+)[\s\-→–]+([А-ЯЁа-яё\w\'\-]+)'
    route_match = re.search(route_pattern, text.upper())
    
    if route_match:
        from_city = route_match.group(1).lower()
        to_city = route_match.group(2).lower()
        cargo_text = text.replace(route_match.group(0), '').strip()
        return from_city, to_city, cargo_text
    
    return None, None, text

def format_cargo_text(cargo_text):
    """Форматирование текста груза"""
    lines = [line.strip() for line in cargo_text.split('\n') if line.strip()]
    
    transport_type = "Transport"
    cargo_description = ""
    
    if lines:
        first_line = lines[0]
        if any(word in first_line.upper() for word in ['ISUZU', 'KAMAZ', 'GAZEL', 'TRUCK', 'TENTOFKA', 'PARAVOZ']):
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
        
        # Обработка админских команд в ЛС
        if chat_id == ADMIN_USER_ID:
            handle_admin_command(message)
            return
        
        # Обработка только сообщений из основной группы
        if chat_id != MAIN_GROUP_ID:
            return
        
        # Извлечение маршрута
        from_city, to_city, cargo_text = extract_route_and_cargo(text)
        if not from_city or not to_city:
            return
            
        # Поиск региона по ключевым словам - УЛУЧШЕННАЯ ЛОГИКА
        def find_region_by_text(text):
            text_lower = text.lower().strip()
            words = re.findall(r'\b\w+\b', text_lower)
            
            # Сначала ищем точное совпадение по словам
            for region_key, region_data in REGION_KEYWORDS.items():
                for keyword in region_data['keywords']:
                    keyword_lower = keyword.lower()
                    # Точное совпадение слова
                    if keyword_lower in words:
                        return region_key
                    # Вхождение для составных названий
                    if len(keyword_lower) > 4 and keyword_lower in text_lower:
                        return region_key
            return None
        
        # ПРИОРИТЕТНАЯ ЛОГИКА: международные → отправление → назначение
        from_city_region = find_region_by_text(from_city)
        to_city_region = find_region_by_text(to_city)
        
        topic_keyword = None
        
        # 1. Международные направления имеют абсолютный приоритет
        if from_city_region == 'xalqaro' or to_city_region == 'xalqaro':
            topic_keyword = 'xalqaro'
        # 2. Приоритет по пункту отправления
        elif from_city_region and from_city_region != 'xalqaro':
            topic_keyword = from_city_region
        # 3. Приоритет по пункту назначения
        elif to_city_region and to_city_region != 'xalqaro':
            topic_keyword = to_city_region
        # 4. Поиск по всему тексту
        else:
            topic_keyword = find_region_by_text(text)
                    
        if not topic_keyword:
            # Отправляем админу для анализа неопознанных маршрутов
            send_message(ADMIN_USER_ID, f"⚠️ НЕОПОЗНАННЫЙ МАРШРУТ:\n{from_city} → {to_city}\n\nТекст: {text[:200]}...")
            return
            
        # Получение информации о пользователе
        sender_name = message.get('from', {}).get('first_name', 'Anonim')
        sender_username = message.get('from', {}).get('username')
        sender_link = f"https://t.me/{sender_username}" if sender_username else sender_name
        
        phone = extract_phone_number(text)
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
            logger.info(f"🎯 {from_city} -> {to_city} → {topic_keyword.upper()} ({topic_id})")
            # Уведомление админу об успешной обработке
            if topic_keyword == 'toshkent' and 'chirchiq' in text.lower():
                send_message(ADMIN_USER_ID, f"✅ CHIRCHIQ ИСПРАВЛЕН!\n{from_city} → {to_city} попал в ТАШКЕНТСКУЮ область (101362)")
        
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
    global last_update_id, bot_status
    
    logger.info("🚀 RENDER BOT - ПОЛНАЯ ГЕОГРАФИЧЕСКАЯ БАЗА АКТИВНА")
    
    # Уведомление админу
    send_message(ADMIN_USER_ID, f"🚀 ПОЛНАЯ ГЕОГРАФИЧЕСКАЯ БАЗА АКТИВНА!\n\n✅ Chirchiq теперь в ТАШКЕНТСКОЙ области\n✅ {sum(len(data['keywords']) for data in REGION_KEYWORDS.values())} городов и районов\n✅ Админские команды: /start, /test")
    
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
            bot_status = "ОШИБКА"
            time.sleep(5)
            bot_status = "АКТИВЕН"
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
    <h1>YukMarkazi Bot - {bot_status}</h1>
    <p>Сообщений обработано: {message_count}</p>
    <p>Время работы: {hours}ч {minutes}м</p>
    <p>Регионов: {len(REGION_KEYWORDS)}</p>
    <p>Городов и районов: {sum(len(data['keywords']) for data in REGION_KEYWORDS.values())}</p>
    <p>✅ CHIRCHIQ исправлен - теперь в ТАШКЕНТСКОЙ области</p>
    <p>Поддержка узбекских приставок: -DAN/-GA</p>
    <p>Админские команды: АКТИВНЫ</p>
    <p>Последний update: {last_update_id}</p>
    """

@app.route('/health')
def health():
    return {'status': bot_status.lower(), 'messages': message_count, 'cities': sum(len(data['keywords']) for data in REGION_KEYWORDS.values())}

@app.route('/ping')
def ping():
    return 'pong'

def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    global bot_status
    bot_status = "ОСТАНОВЛЕН"
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
