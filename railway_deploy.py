#!/usr/bin/env python3
"""
RAILWAY DEPLOYMENT - ПОЛНАЯ НЕЗАВИСИМОСТЬ
Работает без Replit, 24/7, первые $5 бесплатно
"""
import os
import sys
import time
import signal
import logging
import threading
from datetime import datetime
from flask import Flask
import requests

# Настройки
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
MAIN_GROUP_ID = -1002259378109
ADMIN_USER_ID = 8101326669
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# 18 ТОПИКОВ
TOPICS = {
    'buxoro': 101372, 'toshkent': 101362, 'andijon': 101387,
    'namangan': 101383, 'fargona': 101382, 'qoqon': 101382,
    'nukus': 101381, 'qarshi': 101380, 'navoiy': 101379,
    'sirdaryo': 101378, 'jizzax': 101377, 'nukus2': 101376,
    'urganch': 101375, 'samarqand': 101369, 'xalqaro': 101367,
    'russia': 101367, 'surxondaryo': 101363, 'xorazm': 101660
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

def process_message(message):
    """Обработка сообщения"""
    try:
        if not message.get('text'):
            return
            
        text = message['text'].lower()
        chat_id = message['chat']['id']
        
        if chat_id != MAIN_GROUP_ID:
            return
            
        # Поиск ключевого слова
        found_keyword = None
        for keyword in TOPICS:
            if keyword in text:
                found_keyword = keyword
                break
                
        if not found_keyword:
            return
            
        # Форматирование на узбекском латинице
        sender = message.get('from', {}).get('first_name', 'Anonim')
        region = found_keyword.capitalize()
        
        formatted_text = f"""🚛 {region}
{message['text']}

☎️ Ko'rsatilmagan
👤 {sender}
#{region.lower()}
➖➖➖
Boshqa yuklar: @logistika_marka"""

        # Отправка в топик
        topic_id = TOPICS[found_keyword]
        success = send_message(MAIN_GROUP_ID, formatted_text, topic_id)
        
        if success:
            logger.info(f"🎯 {found_keyword} -> {topic_id}: {message['text'][:50]}...")
        
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
            
            status = f"""🟢 RAILWAY BOT АКТИВЕН
📊 Обработано: {message_count} сообщений
⏰ Время работы: {hours}ч {minutes}м
📋 Топиков: {len(set(TOPICS.values()))}
🔄 Update: {last_update_id}
🚀 Платформа: Railway (НЕ Replit!)
💰 Стоимость: $0 (первые $5 бесплатно)"""
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

def bot_main_loop():
    """Основной цикл бота"""
    global last_update_id
    
    logger.info("🚀 RAILWAY BOT ЗАПУЩЕН")
    
    # Уведомление админу
    send_message(ADMIN_USER_ID, "🚀 RAILWAY BOT ЗАПУЩЕН - ПОЛНАЯ НЕЗАВИСИМОСТЬ ОТ REPLIT!")
    
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

# Flask приложение для Railway
app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health():
    uptime = datetime.now() - bot_start_time
    return {
        'status': 'running',
        'platform': 'Railway',
        'uptime_seconds': int(uptime.total_seconds()),
        'messages_processed': message_count,
        'last_update_id': last_update_id,
        'time': datetime.now().isoformat()
    }

@app.route('/ping')
def ping():
    return 'pong'

def run_web_server():
    """Веб-сервер для Railway health checks"""
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == "__main__":
    # Запуск веб-сервера в отдельном потоке
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # Основной цикл бота
    bot_main_loop()