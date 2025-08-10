#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
railway_deploy.py – полностью готовый, улучшенный файл
- при неопознанном маршруте – инлайн-кнопки админу
- callback-обработка пересылки + кнопка Aloqaga_chiqish
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
BOT_TOKEN   = os.environ.get('TELEGRAM_BOT_TOKEN')
MAIN_GROUP_ID = int(os.environ.get('MAIN_GROUP_ID', '-1002259378109'))
ADMIN_USER_ID = int(os.environ.get('ADMIN_USER_ID', '8101326669'))
BOT_USERNAME  = os.getenv("BOT_USERNAME", "yukmarkazi_bot")  # без @
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}" if BOT_TOKEN else None
# ========== REGION_KEYWORDS (полностью) ==========
REGION_KEYWORDS = {
    'toshkent': {
        'topic_id': 101362,
        'keywords': [
            'toshkent', 'tashkent', 'ташкент', 'тошкент', 'bekobod', 'бекабад', 'бекобод', 'olmaliq', 'алмалык', 'олмалиқ',
            'ohangaron', 'ахангаран', 'оҳангарон', 'angren', 'ангрен', 'chirchiq', 'чирчик', 'чирчиқ',
            "yangiyo'l", 'yangiyul', 'янгиюль', 'янгиюл', 'sergeli', 'сергели', 'chilonzor', 'чиланзар'
        ]
    },
    'fargona': {
        'topic_id': 101382,
        'keywords': [
            "farg'ona", 'fargona', 'фергана', "фарғона", 'qoqon', 'quqon', 'kokand', 'коканд', 'қўқон',
            'margilon', 'маргилан', 'quvasoy', 'кувасай', 'қувасой', 'Quvasoy', 'Қувасой', 'Кувасой',
            'beshariq', 'бешарык', "bog'dod", 'багдад'
        ]
    },
    'andijon': {
        'topic_id': 101387,
        'keywords': ['andijon', 'andijan', 'андижан', 'asaka', 'асака', 'marhamat', 'мархамат']
    },
    'buxoro': {
        'topic_id': 101372,
        'keywords': ['buxoro', 'bukhara', 'бухара', 'alat', 'алат', "g'ijduvon", 'гиждуван', 'kogon', 'когон']
    },
    'namangan': {
        'topic_id': 101383,
        'keywords': ['namangan', 'наманган', 'chortoq', 'чартак', 'yangiqorgon', 'янгикурган']
    },
    'samarqand': {
        'topic_id': 101369,
        'keywords': ['samarqand', 'samarkand', 'самарканд', 'urgut', 'ургут', 'kattaqorgon', 'каттакурган']
    },
    'qashqadaryo': {
        'topic_id': 101380,
        'keywords': ['qarshi', 'карши', 'shahrisabz', 'шахрисабз', 'koson', 'косон', 'guzar', 'гузар']
    },
    'navoiy': {
        'topic_id': 101379,
        'keywords': ['navoiy', 'navoi', 'навои', 'zarafshon', 'зарафшан', 'karmana', 'кармана']
    },
    'sirdaryo': {
        'topic_id': 101378,
        'keywords': ['guliston', 'гулистан', 'shirin', 'ширин', 'boyovut', 'баяут']
    },
    'jizzax': {
        'topic_id': 101377,
        'keywords': ['jizzax', 'джизак', 'gallaaral', 'галляарал', 'pakhtakor', 'пахтакор', 'zomin', 'зомин']
    },
    'nukus': {
        'topic_id': 101376,
        'keywords': ['nukus', 'нукус']
    },
    'urganch': {
        'topic_id': 101375,
        'keywords': ['urganch', 'ургенч']
    },
    'xorazm': {
        'topic_id': 101660,
        'keywords': ['xorazm', 'xorezm', 'хорезм', 'xiva', 'khiva', 'хива', 'shovot', 'шават']
    },
    'qoraqalpoq': {
        'topic_id': 101381,
        'keywords': ['qoraqalpoq', 'каракалпакстан', 'turtkul', 'турткуль', 'khojeli', 'ходжейли']
    },
    'xalqaro': {
        'topic_id': 101367,
        'keywords': [
            'russia', 'россия', 'moskva', 'москва', 'spb', 'питер', 'kazakhstan', 'казахстан',
            'turkey', 'стамбул', 'china', 'китай', 'dubai', 'дубай'
        ]
    },
    'surxondaryo': {
        'topic_id': 101363,
        'keywords': ['termiz', 'термез', 'denov', 'денау', 'boysun', 'байсун']
    }
}

SPECIAL_TOPICS = {
    'fura_bozor': 101361,
    'reklama': 101360,
    'yangiliklar': 101359
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
    text = text.replace('\u0130', 'I').replace('\u0131', 'i')
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(ch for ch in text if unicodedata.category(ch) != 'Mn')
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
    uid   = sender["id"]
    name  = sender.get("first_name", "Аноним")
    un    = sender.get("username")
    text  = "👤 Aloqaga_chiqish"
    if un:
        text += f" @{un}"
    return {
        "inline_keyboard": [[{
            "text": text,
            "url": f"https://t.me/{BOT_USERNAME}?start=user_{uid}"
        }]]
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

PHONE_REGEX = re.compile(r'(?:\+?998[-\s]?)?(?:\d{2}[-\s]?){4}\d{2}')
ROUTE_REGEX = re.compile(r'([A-Za-z\u0130\u0131\'\w\-]+)[\s\-→–_➢]{1,3}([A-Za-z\u0130\u0131\'\w\-]+)', re.IGNORECASE)

def extract_phone_number(text):
    m = PHONE_REGEX.search(text)
    return m.group().strip() if m else "Телефон не указан"

def extract_route_and_cargo(text):
    match = ROUTE_REGEX.search(text)
    if match:
        fr, to = match.group(1).strip(), match.group(2).strip()
        cargo = text.replace(match.group(0), '').strip()
        return fr.lower(), to.lower(), cargo
    return None, None, text

def format_cargo_text(cargo_text):
    lines = [l.strip() for l in cargo_text.splitlines() if l.strip()]
    transport = lines[0].title() if lines and any(w in lines[0].upper() for w in ['FURA','ISUZU','KAMAZ']) else "Транспорт"
    desc = " ".join(lines[1:] if transport != "Транспорт" else lines)
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
            words = re.findall(r'\b\w+\b', txt_norm)
            for key, data in REGION_KEYWORDS.items():
                for kw in data['keywords']:
                    kw_norm = normalize_text(kw)
                    if kw_norm in words or (len(kw_norm) > 4 and kw_norm in txt_norm):
                        return key
            return None

        from_reg = find_region(from_city)
        to_reg = find_region(to_city)

        if from_reg is None:
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
        transport, desc = format_cargo_text(cargo_text)

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
