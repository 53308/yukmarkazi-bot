# ... (всё до REGION_KEYWORDS без изменений)

# === ДОБАВЛЕНО: функция для нормализации текста ===
import unicodedata

def normalize_text(text):
    text = unicodedata.normalize('NFKD', text)  # Разложение символов
    text = text.replace('İ', 'I').replace('ı', 'i')  # Турецкие буквы → обычные
    return text.lower().strip()

# ... (всё до process_message без изменений)

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
            
        # Поиск региона по ключевым словам
        def find_region_by_text(text):
            text_lower = normalize_text(text)  # ← заменили на нормализованный текст
            words = re.findall(r'\b\w+\b', text_lower)
            
            # Сначала ищем точное совпадение по словам
            for region_key, region_data in REGION_KEYWORDS.items():
                for keyword in region_data['keywords']:
                    keyword_lower = normalize_text(keyword)  # ← тоже нормализуем ключ
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
            # Уведомление админу об успешной обработке Xorazm
            if topic_keyword == 'xorazm':
                send_message(ADMIN_USER_ID, f"✅ XORAZM РАБОТАЕТ!\n{from_city} → {to_city} → XORAZM (101660)")
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки: {e}")

# ... (всё остальное без изменений)
