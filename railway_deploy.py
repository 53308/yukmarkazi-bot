#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAILWAY_DEPLOY / RENDER ENTRYPOINT
Исправленная версия: нормализация турецких символов (İ, ı и пр.)
Устойчивость при отсутствии TELEGRAM_BOT_TOKEN и улучшенное логирование.
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
from flask import Flask
import requests

# ========== Настройки ==========
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
MAIN_GROUP_ID = int(os.environ.get('MAIN_GROUP_ID', '-1002259378109'))
ADMIN_USER_ID = int(os.environ.get('ADMIN_USER_ID', '8101326669'))
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}" if BOT_TOKEN else None

# ========== TOPICS / КЛЮЧЕВЫЕ СЛОВА (с добавлением borisov в xalqaro) ==========
REGION_KEYWORDS = {
    # ТАШКЕНТ - 101362 ✅
    'toshkent': {
        'topic_id': 101362,
        'keywords': [
            'toshkent', 'tashkent', 'ташкент', 'тошкент', 'toshkentdan', 'toshkentga', 'tashkentdan', 'tashkentga',
            'bekobod', 'бекабад', 'бекобод', 'olmaliq', 'алмалык', 'олмалиқ', 'almalyk',
            'ohangaron', 'ахангаран', 'оҳангарон', 'ahangaron', 'angren', 'ангрен',
            'chirchiq', 'чирчик', 'чирчиқ', 'chirchik', 'chirchiqdan', 'chirchiqga',
            "yangiyo'l", 'yangiyul', 'янгиюль', 'янгиюл', 'yangiyol',
            "bo'stonliq", 'bostonliq', 'бустанлык', 'бўстонлиқ',
            "bo'ka", 'boka', 'бука', 'бўка', 'chinoz', 'чиназ', 'чиноз', 'chinaz',
            'qibray', 'кибрай', 'қибрай', 'kibray',
            "oqqo'rg'on", 'oqqorgon', 'аккурган', 'оққўрғон',
            'parkent', 'паркент', 'piskent', 'пскент',
            'quyi chirchiq', 'куйи чирчик', 'қуйи чирчиқ',
            'yuqori chirchiq', 'юкори чирчик', 'юқори чирчиқ',
            'zangota', 'зангата', "g'azalkent", 'gazalkent', 'газалкент', 'ғазалкент',
            'nurafshon', 'нурафшан', '3 mikrorayon', '3 mikrayon', '3-mikrorayon', '3-микрорайон',
            'sergeli', 'сергели', 'chilonzor', 'чиланзар', 'чилонзор',
            "mirzo ulug'bek", 'мирзо улугбек', 'мирзо улуғбек',
            'bektemir', 'бектемир', 'yakkasaray', 'яккасарай', 'яккасарой',
            'uchtepa', 'учтепа', 'mirobod', 'мирабад', 'миробод',
            'hamza', 'хамза', 'ҳамза', 'olmazor', 'алмазар', 'олмазор'
        ]
    },
    # ФЕРГАНА - 101382 ✅
    'fargona': {
        'topic_id': 101382,
        'keywords': [
            "farg'ona", 'fargona', 'fergana', 'фергана', "фарғона", 'fargonodan', 'fargonega', 'farganaga', 'фаргонага', 'фергонага',
            "qo'qon", 'qoqon', 'quqon', 'kokand', 'коканд', 'қўқон',
            "marg'ilon", 'margilon', 'маргилан', 'марғилон',
            'quvasoy', 'кувасай', 'қувасой', 'quvasoyga', 'quvasoydan',
            'beshariq', 'бешарык', 'бешариқ', "bog'dod", 'bogdod', 'багдад', 'боғдод',
            'buvayda', 'бувайда', "dang'ara", 'dangara', 'дангара', 'данғара',
            'furqat', 'фуркат', 'фурқат', 'oltiariq', 'алтыарык', 'олтиариқ',
            "qo'shtepa", 'qoshtepa', 'куштепа', 'қўштепа', 'quva', 'кува', 'қува',
            'rishton', 'риштан', 'риштон', "so'x", 'sox', 'сох', 'сўх',
            "toshloq", 'ташлак', 'тошлоқ', "uchko'prik", 'uchkoprik', 'учкуприк', 'учкўприк',
            'uzbekiston', 'узбекистан', 'ўзбекистон', 'yozyovon', 'язъяван', 'ёзёвон'
        ]
    },
    # АНДИЖАН - 101387 ✅
    'andijon': {
        'topic_id': 101387,
        'keywords': [
            'andijon', 'andijan', 'андижан', 'андижон', 'andijondan', 'andijonega',
            'asaka', 'асака', 'asakadan', 'asakaga', 'baliqchi', 'балыкчи', 'балиқчи',
            'boz', 'боз', 'buloqboshi', 'булоқбоши', 'bulakbashi',
            'izboskan', 'избаскан', 'избоскан', 'jalaquduq', 'жалакудук', 'жалақудуқ',
            'marhamat', 'мархамат', 'марҳамат', "oltinko'l", 'oltinkol', 'олтинкўл', 'altinkul',
            'paxtaobod', 'пахтаабад', 'пахтаобод', "qo'rg'ontepa", 'qorgontepa', 'қўрғонтепа', 'kurgontepa',
            'shahrixon', 'шахрихан', 'шаҳрихон', 'ulug\'nor', 'ulugnor', 'улуғнор',
            "xo'jaobod", 'xojaobod', 'хўжаобод', 'хива',
            'khodjaabad'
        ]
    },
    # БУХАРА - 101372 ✅
    'buxoro': {
        'topic_id': 101372,
        'keywords': [
            'buxoro', 'bukhara', 'бухара', 'бухоро', 'buxorodan', 'buxoroga', 'bukharadan', 'bukharaga',
            'alat', 'алат', "g'ijduvon", 'gijduvon', 'гиждуван', 'ғиждувон',
            'jondor', 'жондор', 'kogon', 'kaagan', 'каган', 'когон',
            "qorako'l", 'qarakol', 'каракуль', 'қоракўл',
            'qorovulbozor', 'қоровулбозор', 'karavulbazar',
            'romitan', 'ромитан', 'shofirkon', 'шафиркан', 'шофиркон',
            'vobkent', 'вабкент', 'вобкент', 'peshku', 'пешку'
        ]
    },
    # НАМАНГАН - 101383 ✅
    'namangan': {
        'topic_id': 101383,
        'keywords': [
            'namangan', 'наманган', 'pop', 'поп', 'uchqurgan', 'учкурган', 'учқурган',
            "yangiqo'rg'on", 'yangiqorgon', 'янгикурган', 'янгиқўрғон',
            'chortoq', 'чартак', 'чортоқ', 'kosonsoy', 'косонсой',
            'mingbuloq', 'мингбулак', 'мингбулоқ', 'norin', 'норин',
            "to'raqo'rg'on", 'turakurgan', 'туракурган', 'тўрақўрғон', 'uychi', 'уйчи'
        ]
    },
    # САМАРКАНД - 101369 ✅
    'samarqand': {
        'topic_id': 101369,
        'keywords': [
            'samarqand', 'samarkand', 'самарканд', 'самарқанд', 'urgut', 'ургут',
            "kattaqo'rg'on", 'kattakurgan', 'каттакурган', 'каттақўрғон',
            'jomboy', 'джамбай', 'жомбой', 'payariq', 'пайарик', 'пайариқ',
            'bulungur', 'булунгур', 'булунғур', 'ishtixon', 'иштихан', 'иштиҳон',
            'narpay', 'нарпай', 'nurobod', 'нурабад', 'нуробод',
            'oqdaryo', 'акдарья', 'оқдарё', "pastdarg'om", 'пастдаргом', 'пастдарғом',
            'paxtachi', 'пахтачи', "qo'shrabot", 'kushrabot', 'кушработ', 'қўшработ',
            'toyloq', 'тайлак', 'тойлоқ'
        ]
    },
    # КАШКАДАРЬЯ - 101380 ✅
    'qashqadaryo': {
        'topic_id': 101380,
        'keywords': [
            'qarshi', 'карши', 'қарши', 'shakhrisabz', 'shahrisabz', 'шахрисабз', 'шаҳрисабз',
            'muborak', 'мубарек', 'муборак', 'kitob', 'китаб', 'китоб',
            'koson', 'касан', 'косон', 'chiroqchi', 'чиракчи', 'чироқчи',
            'dehqonobod', 'дехканабад', 'деҳқонобод', "g'uzor", 'guzar', 'гузар', 'ғузор',
            'kamashi', 'камаши', 'mirishkor', 'миришкор', 'nishon', 'нишан', 'нишон',
            "qamashi", 'қамаши', "yakkabog'", 'yakkabaag', 'яккабаг', 'яккабоғ'
        ]
    },
    # НАВОИ - 101379 ✅
    'navoiy': {
        'topic_id': 101379,
        'keywords': [
            'navoiy', 'navoi', 'навои', 'навоий', 'zarafshon', 'зарафшан', 'зарафшон',
            'karmana', 'кармана', 'qiziltepa', 'кизилтепе', 'қизилтепа',
            'tomdi', 'томды', 'uchquduq', 'учкудук', 'учқудуқ', 'konimex', 'конимех'
        ]
    },
    # СЫРДАРЬЯ - 101378 ✅
    'sirdaryo': {
        'topic_id': 101378,
        'keywords': [
            'guliston', 'гулистан', 'гулистон', 'shirin', 'ширин',
            'boyovut', 'баяут', 'боёвут', 'sayxunobod', 'сайхунабад', 'сайхунобод',
            'syrdariya', 'сырдарья', 'сирдарё', 'akaltyn', 'акалтын', 'ақолтин',
            'mirzaobod', 'мирзаабад', 'мирзаобод', 'sardoba', 'сардоба'
        ]
    },
    # ДЖИЗАК - 101377 ✅
    'jizzax': {
        'topic_id': 101377,
        'keywords': [
            'jizzax', 'djizak', 'джизак', 'жиззах', "g'allaorol", 'gallaaral', 'галляарал', 'ғаллаорол',
            'zafarobod', 'зафарабад', 'зафаробод', 'pakhtakor', 'пахтакор',
            "mirzacho'l", 'mirzachul', 'мирзачул', 'мирзачўл', 'arnasoy', 'арнасай', 'арнасой',
            'baxtiyor', 'бахтиёр', "do'stlik", 'dustlik', 'дустлик', 'дўстлик',
            'forish', 'фариш', 'yangiobod', 'янгиабад', 'янгиобод', 'zomin', 'зомин'
        ]
    },
    # НУКУС - 101376 ✅
    'nukus': {
        'topic_id': 101376,
        'keywords': [
            'nukus', 'нукус'
        ]
    },
    # УРГЕНЧ - 101375 ✅
    'urganch': {
        'topic_id': 101375,
        'keywords': [
            'urgench', 'urganch', 'ургенч', 'урганч'
        ]
    },
    # ХОРЕЗМ - 101660 ✅
    'xorazm': {
        'topic_id': 101660,
        'keywords': [
            'xorazm', 'xorezm', 'хорезм', 'хоразм', 'хозарасп',
            'xazorasp', 'hazorasp', 'хазарасп', 'xiva', 'khiva', 'хива', 'ҳива',
            'shovot', 'шават', 'шовот', "qo'shko'pir", 'koshkupir', 'кошкупыр', 'қўшкўпир',
            "bog'ot", 'bagat', 'багат', 'боғот', 'gurlen', 'гурлен',
            'xonqa', 'khanki', 'ханки', 'хонқа', 'yangiariq', 'янгиарык', 'янгиариқ',
            'yangibozor', 'янгибазар', 'янгибозор'
        ]
    },
    # КАРАКАЛПАКСТАН - 101381 ✅
    'qoraqalpoq': {
        'topic_id': 101381,
        'keywords': [
            "qoraqalpog'iston", 'qoraqalpoq', 'каракалпакстан', 'қорақалпоғистон',
            "to'rtko'l", 'turtkul', 'турткуль', 'тўрткўл',
            "xo'jayli", 'khojeli', 'ходжейли', 'хўжайли',
            "qo'ng'irot", 'kungrad', 'кунград', 'қўнғирот',
            "mo'ynoq", 'muynak', 'муйнак', 'мўйноқ', 'chimbay', 'чимбай',
            'kegeyli', 'кегейли', 'amudaryo', 'амударья', 'амударё',
            'beruniy', 'беруний', "ellikqal'a", 'ellikkala', 'элликкала', 'элликқала',
            "bo'zatov", 'bozatau', 'бозатау', 'бўзатов',
            "qanliko'l", 'kanlykul', 'канлыкуль', 'қанликўл', 'taqiyotas', 'такиятас'
        ]
    },
    # МЕЖДУНАРОДНЫЕ НАПРАВЛЕНИЯ - 101367 ✅
    'xalqaro': {
        'topic_id': 101367,
        'keywords': [
            # Россия и пр. (оставлены те же ключи)
            'russia', 'rossiya', 'россия',
            'moskva', 'moscow', 'москва', 'масква', 'moskvadan', 'moskvaga', 'маскавдан', 'масквадан', 'москвадан', 'москвага',
            'spb', 'petersburg', 'piter', 'питер', 'санкт-петербург',
            # Добавлены города международные
            'borisov', 'борисов',
            # Можно расширить список международных ключей по необходимости
        ]
    },
    # СУРХАНДАРЬЯ - 101363 ✅
    'surxondaryo': {
        'topic_id': 101363,
        'keywords': [
            'termiz', 'термез', 'термиз', 'termez', 'denov', 'денау', 'денов',
            'boysun', 'байсун', 'бойсун', "qumqo'rg'on", 'kumkurgan', 'кумкурган', 'қумқўрғон',
            'sherobod', 'шеробод', 'angor', 'ангор', 'bandixon', 'бандихан', 'бандиҳон',
            "jarqo'rg'on", 'zharkurgan', 'ж
