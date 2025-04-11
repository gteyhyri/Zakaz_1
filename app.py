import os
from flask import Flask, request, jsonify, render_template
import psycopg2
from psycopg2.extras import DictCursor
import logging
from logging.handlers import RotatingFileHandler
from flask_cors import CORS
from datetime import datetime, timedelta
import sqlite3
import json
from tasks_config import get_task_by_id, get_all_tasks, TASKS
import random
import telebot

app = Flask(__name__, static_folder='static')
CORS(app)

# Инициализация бота Telegram
bot = telebot.TeleBot('7615667336:AAGtPhj_aZdkptoXnOpF5DNvZBus9lIQCSk')

# Функция для проверки подписки пользователя на канал
def check_subscription(user_id, chat_id):
    try:
        status = bot.get_chat_member(chat_id, user_id).status
        return status in ["creator", "administrator", "member"]
    except Exception as e:
        app.logger.error(f"Error checking subscription: {str(e)}")
        return False

# Конфигурация PostgreSQL
DATABASE_URL = "postgresql://zakazbd_user:hk99lR7fL5jYIdjpGauwzsWA4COo00pm@dpg-cvmoh6ngi27c73cv25dg-a.oregon-postgres.render.com/zakazbd"

# Настройка логирования
def setup_logging():
    os.makedirs('logs', exist_ok=True)
    handler = RotatingFileHandler('logs/app.log', maxBytes=10000, backupCount=3)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

setup_logging()

def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        return conn
    except Exception as e:
        app.logger.error(f"Database connection error: {str(e)}")
        raise

def check_and_update_schema():
    """Проверяет и обновляет схему базы данных, если необходимо."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Проверяем наличие столбца username в таблице users
        cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'username'
        )
        """)
        
        if not cur.fetchone()[0]:
            app.logger.info("Adding username column to users table")
            cur.execute("ALTER TABLE users ADD COLUMN username VARCHAR(255)")
        
        # Проверяем наличие столбца last_claim_time в таблице users
        cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'last_claim_time'
        )
        """)
        
        if not cur.fetchone()[0]:
            app.logger.info("Adding last_claim_time column to users table")
            cur.execute("ALTER TABLE users ADD COLUMN last_claim_time TIMESTAMP")
        
        # Проверяем наличие столбца earnings в таблице referrals
        cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_name = 'referrals' AND column_name = 'earnings'
        )
        """)
        
        if not cur.fetchone()[0]:
            app.logger.info("Adding earnings column to referrals table")
            cur.execute("ALTER TABLE referrals ADD COLUMN earnings INTEGER DEFAULT 0")
        
        # Проверяем наличие столбцов для уровней улучшений
        for column in ['click_upgrade_level', 'storage_upgrade_level', 'speed_upgrade_level']:
            cur.execute(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = '{column}'
            )
            """)
            
            if not cur.fetchone()[0]:
                app.logger.info(f"Adding {column} column to users table")
                cur.execute(f"ALTER TABLE users ADD COLUMN {column} INTEGER DEFAULT 0")
        
        conn.commit()
        app.logger.info("Database schema updated successfully")
    except Exception as e:
        app.logger.error(f"Error updating database schema: {str(e)}")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

# Вызываем инициализацию и обновление схемы базы данных
try:
    app.logger.info("Checking and updating database schema...")
    check_and_update_schema()
    app.logger.info("Schema update completed")
except Exception as e:
    app.logger.error(f"Error during schema update: {str(e)}")

def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Основная таблица пользователей
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username VARCHAR(255) DEFAULT 'user',
            total_clicks INTEGER DEFAULT 0,
            available_clicks NUMERIC DEFAULT 100,
            click_power INTEGER DEFAULT 1,
            max_clicks INTEGER DEFAULT 100,
            regen_rate NUMERIC DEFAULT 1,
            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_claim_time TIMESTAMP NULL,
            click_upgrade_level INTEGER DEFAULT 0,
            storage_upgrade_level INTEGER DEFAULT 0,
            speed_upgrade_level INTEGER DEFAULT 0
        )
        """)
        
        # Таблица для учета рефералов
        cur.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id SERIAL PRIMARY KEY,
            referrer_id BIGINT NOT NULL,
            referred_id BIGINT NOT NULL,
            earnings INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(referrer_id, referred_id),
            FOREIGN KEY (referrer_id) REFERENCES users(user_id),
            FOREIGN KEY (referred_id) REFERENCES users(user_id)
        )
        """)
        
        # Создаем таблицу выполненных заданий
        cur.execute('''CREATE TABLE IF NOT EXISTS completed_tasks
                     (user_id INTEGER,
                      task_id INTEGER,
                      completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      PRIMARY KEY (user_id, task_id))''')
        
        conn.commit()
        app.logger.info("Database initialized successfully")
        
    except Exception as e:
        app.logger.error(f"Error initializing database: {str(e)}")
        raise
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/user', methods=['POST'])
def get_user():
    try:
        data = request.get_json()
        user_id = data.get('userId')
        username = data.get('username', 'user')
        
        if not user_id:
            app.logger.error("No user ID provided")
            return jsonify({'error': 'User ID is required'}), 400
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                # Сначала проверяем существование пользователя
                cur.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
                user_exists = cur.fetchone()
                
                if not user_exists:
                    # Если пользователя нет, создаем нового
                    try:
                        cur.execute("""
                        INSERT INTO users (user_id, username, total_clicks, available_clicks, 
                                        click_power, max_clicks, regen_rate, last_update, created_at,
                                        click_upgrade_level, storage_upgrade_level, speed_upgrade_level)
                        VALUES (%s, %s, 0, 100, 1, 100, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0, 0, 0)
                        RETURNING *
                        """, (user_id, username))
                    except psycopg2.Error as e:
                        # Если ошибка связана с отсутствием колонок улучшений, используем базовый запрос
                        if "column" in str(e) and any(col in str(e) for col in ["click_upgrade_level", "storage_upgrade_level", "speed_upgrade_level"]):
                            app.logger.warning("Using basic INSERT query due to missing upgrade columns")
                            cur.execute("""
                            INSERT INTO users (user_id, username, total_clicks, available_clicks, 
                                            click_power, max_clicks, regen_rate, last_update, created_at)
                            VALUES (%s, %s, 0, 100, 1, 100, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                            RETURNING *
                            """, (user_id, username))
                        else:
                            raise
                    
                    user_data = cur.fetchone()
                else:
                    # Если пользователь существует, обновляем его данные
                    cur.execute("""
                    UPDATE users 
                    SET 
                        available_clicks = LEAST(
                            max_clicks,
                            available_clicks + EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - last_update)) * 0.1 * regen_rate
                        ),
                        last_update = CURRENT_TIMESTAMP,
                        username = CASE WHEN %s != 'user' AND %s IS NOT NULL THEN %s ELSE username END
                    WHERE user_id = %s
                    RETURNING *
                    """, (username, username, username, user_id))
                    user_data = cur.fetchone()
                
                if not user_data:
                    app.logger.error("Failed to get or create user data")
                    return jsonify({'error': 'Failed to get user data'}), 500
                
                conn.commit()
                
                # Проверяем наличие полей улучшений у пользователя
                upgrade_levels = {}
                
                # Получаем все уровни улучшений, с учетом того, что колонки могут отсутствовать
                try:
                    click_level = user_data.get('click_upgrade_level', 0) or 0
                    storage_level = user_data.get('storage_upgrade_level', 0) or 0
                    speed_level = user_data.get('speed_upgrade_level', 0) or 0
                    
                    upgrade_levels = {
                        'click': {
                            'level': click_level,
                            'cost': 200 * (2 ** click_level) if click_level < 12 else None,
                            'maxLevel': 12
                        },
                        'storage': {
                            'level': storage_level,
                            'cost': 200 * (2 ** storage_level) if storage_level < 12 else None,
                            'maxLevel': 12
                        },
                        'speed': {
                            'level': speed_level,
                            'cost': 2000 * (2 ** speed_level) if speed_level < 12 else None,
                            'maxLevel': 12
                        }
                    }
                except Exception as e:
                    app.logger.warning(f"Error preparing upgrade levels: {str(e)}")
                    upgrade_levels = {
                        'click': {'level': 0, 'cost': 200, 'maxLevel': 12},
                        'storage': {'level': 0, 'cost': 200, 'maxLevel': 12},
                        'speed': {'level': 0, 'cost': 2000, 'maxLevel': 12}
                    }
                
                return jsonify({
                    'totalClicks': user_data['total_clicks'],
                    'availableClicks': float(user_data['available_clicks']),
                    'clickPower': user_data['click_power'],
                    'maxClicks': user_data['max_clicks'],
                    'regenRate': float(user_data['regen_rate']),
                    'upgradeLevels': upgrade_levels
                })
                
    except Exception as e:
        app.logger.error(f"Error in get_user: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/user/click', methods=['POST'])
def handle_click():
    try:
        data = request.get_json()
        user_id = data.get('userId')
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                # Пытаемся обновить клики пользователя
                cur.execute("""
                UPDATE users 
                SET 
                    total_clicks = total_clicks + click_power,
                    available_clicks = GREATEST(0, available_clicks - 1),
                    last_update = CURRENT_TIMESTAMP
                WHERE user_id = %s AND available_clicks >= 1
                RETURNING *
                """, (user_id,))
                
                result = cur.fetchone()
                
                if not result:
                    # Если не удалось обновить (нет доступных кликов)
                    cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                    result = cur.fetchone()
                    if not result:
                        return jsonify({'error': 'User not found'}), 404
                    return jsonify({'error': 'No clicks available'}), 400
                
                conn.commit()
                
                return jsonify({
                    'totalClicks': result['total_clicks'],
                    'availableClicks': float(result['available_clicks'])
                })
                
    except Exception as e:
        app.logger.error(f"Error in handle_click: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/user/upgrade', methods=['POST'])
def handle_upgrade():
    try:
        data = request.get_json()
        user_id = data.get('userId')
        upgrade_type = data.get('upgradeType')
        
        if not user_id or not upgrade_type:
            return jsonify({'error': 'Missing parameters'}), 400
        
        valid_upgrades = ['click', 'storage', 'speed']
        if upgrade_type not in valid_upgrades:
            return jsonify({'error': 'Invalid upgrade type'}), 400
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                # Проверяем, существуют ли колонки для улучшений, и добавляем их при необходимости
                for column in ['click_upgrade_level', 'storage_upgrade_level', 'speed_upgrade_level']:
                    try:
                        # Пробуем выбрать данные с этой колонкой
                        cur.execute(f"SELECT {column} FROM users WHERE user_id = %s", (user_id,))
                    except psycopg2.Error as e:
                        if "column" in str(e) and column in str(e):
                            # Если колонка не существует, добавляем ее
                            app.logger.info(f"Adding {column} column to users table")
                            cur.execute(f"ALTER TABLE users ADD COLUMN {column} INTEGER DEFAULT 0")
                            conn.commit()
                
                # Получаем текущие данные пользователя
                try:
                    cur.execute("""
                    SELECT total_clicks, click_upgrade_level, storage_upgrade_level, speed_upgrade_level
                    FROM users
                    WHERE user_id = %s
                    """, (user_id,))
                except psycopg2.Error:
                    # Если не удалось выбрать все колонки вместе, используем более простой запрос
                    cur.execute("SELECT total_clicks FROM users WHERE user_id = %s", (user_id,))
                
                user_data = cur.fetchone()
                if not user_data:
                    return jsonify({'error': 'User not found'}), 404
                
                # Получаем текущие уровни улучшений, используя значения по умолчанию, если колонки нет
                click_level = user_data.get('click_upgrade_level', 0) or 0
                storage_level = user_data.get('storage_upgrade_level', 0) or 0
                speed_level = user_data.get('speed_upgrade_level', 0) or 0
                
                # Рассчитываем стоимость и значение улучшения в зависимости от типа
                if upgrade_type == 'click':
                    next_level = click_level + 1
                    
                    # Максимальный уровень улучшения
                    if next_level > 12:
                        return jsonify({'error': 'Maximum upgrade level reached'}), 400
                    
                    # Стоимость улучшения (200 * 2^level)
                    cost = 200 * (2 ** click_level)
                    
                    # Проверка, достаточно ли денег у пользователя
                    if user_data['total_clicks'] < cost:
                        return jsonify({'error': 'Not enough clicks'}), 400
                    
                    # Определение бонуса за клик в зависимости от уровня
                    click_bonus = 0
                    if next_level == 1:
                        click_bonus = 2
                    elif next_level == 2:
                        click_bonus = 3.5
                    elif next_level == 3:
                        click_bonus = 1.5
                    elif next_level == 4:
                        click_bonus = 4
                    else:
                        click_bonus = 1 + (next_level - 4)
                    
                    # Обновляем данные пользователя
                    try:
                        cur.execute("""
                        UPDATE users 
                        SET 
                            total_clicks = total_clicks - %s,
                            click_power = click_power + %s,
                            click_upgrade_level = %s,
                            last_update = CURRENT_TIMESTAMP
                        WHERE user_id = %s
                        RETURNING *
                        """, (cost, click_bonus, next_level, user_id))
                    except psycopg2.Error as e:
                        if "column" in str(e) and "click_upgrade_level" in str(e):
                            # Если колонки нет, обновляем только основные данные
                            cur.execute("""
                            UPDATE users 
                            SET 
                                total_clicks = total_clicks - %s,
                                click_power = click_power + %s,
                                last_update = CURRENT_TIMESTAMP
                            WHERE user_id = %s
                            RETURNING *
                            """, (cost, click_bonus, user_id))
                        else:
                            raise
                
                elif upgrade_type == 'storage':
                    next_level = storage_level + 1
                    
                    # Максимальный уровень улучшения
                    if next_level > 12:
                        return jsonify({'error': 'Maximum upgrade level reached'}), 400
                    
                    # Стоимость улучшения (200 * 2^level)
                    cost = 200 * (2 ** storage_level)
                    
                    # Проверка, достаточно ли денег у пользователя
                    if user_data['total_clicks'] < cost:
                        return jsonify({'error': 'Not enough clicks'}), 400
                    
                    # Определение бонуса к хранилищу в зависимости от уровня
                    storage_bonus = 0
                    if next_level == 1:
                        storage_bonus = 20
                    elif next_level == 2:
                        storage_bonus = 25
                    elif next_level == 3:
                        storage_bonus = 30
                    else:
                        storage_bonus = 20
                    
                    # Обновляем данные пользователя
                    try:
                        cur.execute("""
                        UPDATE users 
                        SET 
                            total_clicks = total_clicks - %s,
                            max_clicks = max_clicks + %s,
                            available_clicks = available_clicks + %s,
                            storage_upgrade_level = %s,
                            last_update = CURRENT_TIMESTAMP
                        WHERE user_id = %s
                        RETURNING *
                        """, (cost, storage_bonus, storage_bonus, next_level, user_id))
                    except psycopg2.Error as e:
                        if "column" in str(e) and "storage_upgrade_level" in str(e):
                            # Если колонки нет, обновляем только основные данные
                            cur.execute("""
                            UPDATE users 
                            SET 
                                total_clicks = total_clicks - %s,
                                max_clicks = max_clicks + %s,
                                available_clicks = available_clicks + %s,
                                last_update = CURRENT_TIMESTAMP
                            WHERE user_id = %s
                            RETURNING *
                            """, (cost, storage_bonus, storage_bonus, user_id))
                        else:
                            raise
                
                elif upgrade_type == 'speed':
                    next_level = speed_level + 1
                    
                    # Максимальный уровень улучшения
                    if next_level > 12:
                        return jsonify({'error': 'Maximum upgrade level reached'}), 400
                    
                    # Стоимость улучшения (2000 * 2^level)
                    cost = 2000 * (2 ** speed_level)
                    
                    # Проверка, достаточно ли денег у пользователя
                    if user_data['total_clicks'] < cost:
                        return jsonify({'error': 'Not enough clicks'}), 400
                    
                    # Увеличение скорости восстановления (скорость регенерации + 0.05)
                    speed_bonus = 0.05
                    
                    # Обновляем данные пользователя
                    try:
                        cur.execute("""
                        UPDATE users 
                        SET 
                            total_clicks = total_clicks - %s,
                            regen_rate = regen_rate + %s,
                            speed_upgrade_level = %s,
                            last_update = CURRENT_TIMESTAMP
                        WHERE user_id = %s
                        RETURNING *
                        """, (cost, speed_bonus, next_level, user_id))
                    except psycopg2.Error as e:
                        if "column" in str(e) and "speed_upgrade_level" in str(e):
                            # Если колонки нет, обновляем только основные данные
                            cur.execute("""
                            UPDATE users 
                            SET 
                                total_clicks = total_clicks - %s,
                                regen_rate = regen_rate + %s,
                                last_update = CURRENT_TIMESTAMP
                            WHERE user_id = %s
                            RETURNING *
                            """, (cost, speed_bonus, user_id))
                        else:
                            raise
                
                updated_data = cur.fetchone()
                conn.commit()
                
                # Обновляем уровни улучшений на основе переданных данных
                if upgrade_type == 'click':
                    click_level = next_level
                elif upgrade_type == 'storage':
                    storage_level = next_level
                elif upgrade_type == 'speed':
                    speed_level = next_level
                
                # Подготовка данных для ответа, включая информацию о стоимости следующего улучшения
                next_level_data = {
                    'click': {
                        'level': click_level,
                        'cost': 200 * (2 ** click_level) if click_level < 12 else None,
                        'maxLevel': 12
                    },
                    'storage': {
                        'level': storage_level,
                        'cost': 200 * (2 ** storage_level) if storage_level < 12 else None,
                        'maxLevel': 12
                    },
                    'speed': {
                        'level': speed_level,
                        'cost': 2000 * (2 ** speed_level) if speed_level < 12 else None,
                        'maxLevel': 12
                    }
                }
                
                return jsonify({
                    'totalClicks': updated_data['total_clicks'],
                    'clickPower': updated_data['click_power'],
                    'regenRate': float(updated_data['regen_rate']),
                    'maxClicks': updated_data['max_clicks'],
                    'availableClicks': float(updated_data['available_clicks']),
                    'upgradeLevels': next_level_data
                })
                
    except Exception as e:
        app.logger.error(f"Error in handle_upgrade: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/user/referrals', methods=['POST'])
def get_referrals():
    try:
        data = request.get_json()
        user_id = data.get('userId')
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                # Получаем количество рефералов пользователя
                cur.execute("""
                SELECT COUNT(*) as referral_count 
                FROM referrals 
                WHERE referrer_id = %s
                """, (user_id,))
                
                result = cur.fetchone()
                referral_count = result['referral_count'] if result else 0
                
                # Пытаемся получить список рефералов с именами и заработком
                referrals = []
                total_earnings = 0
                
                # Версия запроса будет зависеть от наличия столбцов
                try:
                    cur.execute("""
                    SELECT r.referred_id, r.earnings, u.username
                    FROM referrals r
                    JOIN users u ON r.referred_id = u.user_id
                    WHERE r.referrer_id = %s
                    ORDER BY r.earnings DESC, r.created_at DESC
                    """, (user_id,))
                    
                    referrals_data = cur.fetchall()
                    for ref in referrals_data:
                        username = ref['username']
                        if not username or username == 'user':
                            username = f"User{ref['referred_id'] % 1000}"
                            
                        referrals.append({
                            'id': ref['referred_id'],
                            'username': username,
                            'earnings': ref['earnings'] or 0
                        })
                        total_earnings += ref['earnings'] or 0
                        
                except psycopg2.Error as e:
                    if any(col in str(e) for col in ['earnings', 'username']):
                        app.logger.warning("Using simplified referrals query due to missing columns")
                        
                        # Запрос без username и earnings
                        cur.execute("""
                        SELECT r.referred_id, r.created_at 
                        FROM referrals r
                        WHERE r.referrer_id = %s
                        ORDER BY r.created_at DESC
                        """, (user_id,))
                        
                        referrals_data = cur.fetchall()
                        for ref in referrals_data:
                            referrals.append({
                                'id': ref['referred_id'],
                                'username': f"User{ref['referred_id'] % 1000}",
                                'earnings': 0
                            })
                    else:
                        raise
                
                # Получаем время последнего сбора дохода
                last_claim_time = None
                try:
                    cur.execute("""
                    SELECT last_claim_time
                    FROM users
                    WHERE user_id = %s
                    """, (user_id,))
                    
                    user_data = cur.fetchone()
                    if user_data and 'last_claim_time' in user_data and user_data['last_claim_time']:
                        last_claim_time = user_data['last_claim_time']
                except psycopg2.Error as e:
                    if "column" in str(e) and "last_claim_time" in str(e):
                        app.logger.warning("last_claim_time column not found")
                    else:
                        raise
                
                return jsonify({
                    'referralCount': referral_count,
                    'referrals': referrals,
                    'claimableAmount': int(total_earnings),
                    'lastClaimTime': last_claim_time.isoformat() if last_claim_time else None
                })
                
    except Exception as e:
        app.logger.error(f"Error in get_referrals: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/user/claim-referrals', methods=['POST'])
def claim_referrals():
    try:
        data = request.get_json()
        user_id = data.get('userId')
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                # Подсчитываем сумму для сбора, с учетом того, что столбец earnings может отсутствовать
                try:
                    cur.execute("""
                    SELECT SUM(earnings) as total_earnings
                    FROM referrals 
                    WHERE referrer_id = %s
                    """, (user_id,))
                    
                    earnings_data = cur.fetchone()
                    claimable_amount = int(earnings_data['total_earnings']) if earnings_data and earnings_data['total_earnings'] else 0
                except psycopg2.Error as e:
                    if "column" in str(e) and "earnings" in str(e):
                        app.logger.warning("Earnings column not found, using default claimable amount")
                        # Если столбца earnings нет, даем фиксированную сумму за каждого реферала
                        cur.execute("""
                        SELECT COUNT(*) as referral_count 
                        FROM referrals 
                        WHERE referrer_id = %s
                        """, (user_id,))
                        result = cur.fetchone()
                        claimable_amount = result['referral_count'] * 100 if result else 0
                    else:
                        raise
                
                if claimable_amount <= 0:
                    return jsonify({'error': 'No earnings to claim'}), 400
                
                # Проверяем, прошло ли 8 часов с последнего сбора
                try:
                    cur.execute("""
                    SELECT last_claim_time
                    FROM users
                    WHERE user_id = %s
                    """, (user_id,))
                    
                    user_data = cur.fetchone()
                    
                    if user_data and 'last_claim_time' in user_data and user_data['last_claim_time']:
                        # Проверяем, прошло ли 8 часов с последнего сбора
                        last_claim = user_data['last_claim_time']
                        min_next_claim = last_claim + timedelta(hours=8)
                        
                        if datetime.now() < min_next_claim:
                            return jsonify({
                                'error': 'You can claim earnings only once every 8 hours',
                                'nextClaimTime': min_next_claim.isoformat()
                            }), 400
                except psycopg2.Error as e:
                    if "column" in str(e) and "last_claim_time" in str(e):
                        app.logger.warning("last_claim_time column not found, skipping cooldown check")
                    else:
                        raise
                
                # Обновляем баланс пользователя и сбрасываем заработок рефералов
                try:
                    cur.execute("""
                    UPDATE users
                    SET 
                        total_clicks = total_clicks + %s,
                        last_claim_time = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                    RETURNING total_clicks
                    """, (claimable_amount, user_id))
                except psycopg2.Error as e:
                    if "column" in str(e) and "last_claim_time" in str(e):
                        app.logger.warning("last_claim_time column not found, updating without it")
                        cur.execute("""
                        UPDATE users
                        SET total_clicks = total_clicks + %s
                        WHERE user_id = %s
                        RETURNING total_clicks
                        """, (claimable_amount, user_id))
                    else:
                        raise
                
                updated_user = cur.fetchone()
                
                # Обнуляем заработок рефералов до следующего сбора
                try:
                    cur.execute("""
                    UPDATE referrals
                    SET earnings = 0
                    WHERE referrer_id = %s
                    """, (user_id,))
                except psycopg2.Error as e:
                    if "column" in str(e) and "earnings" in str(e):
                        app.logger.warning("Earnings column not found, skipping earnings reset")
                    else:
                        raise
                
                conn.commit()
                
                return jsonify({
                    'success': True,
                    'claimedAmount': claimable_amount,
                    'newBalance': updated_user['total_clicks']
                })
                
    except Exception as e:
        app.logger.error(f"Error in claim_referrals: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/user/referral-register', methods=['POST'])
def register_referral():
    try:
        data = request.get_json()
        user_id = data.get('userId')
        referrer_id = data.get('referrerId')
        
        if not user_id or not referrer_id:
            return jsonify({'error': 'User ID and Referrer ID are required'}), 400
        
        # Проверяем, что пользователь не пытается стать своим собственным рефералом
        if user_id == referrer_id:
            return jsonify({'error': 'Cannot refer yourself'}), 400
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                # Проверяем существование реферрера
                cur.execute("SELECT user_id FROM users WHERE user_id = %s", (referrer_id,))
                if not cur.fetchone():
                    return jsonify({'error': 'Referrer not found'}), 404
                
                # Проверяем, новый ли это пользователь (для предотвращения повторных регистраций)
                cur.execute("SELECT created_at FROM users WHERE user_id = %s", (user_id,))
                user_data = cur.fetchone()
                
                # Добавляем связь реферала, только если еще нет такой записи
                cur.execute("""
                INSERT INTO referrals (referrer_id, referred_id)
                VALUES (%s, %s)
                ON CONFLICT (referrer_id, referred_id) DO NOTHING
                RETURNING id
                """, (referrer_id, user_id))
                
                new_referral = cur.fetchone()
                
                # Если создана новая запись реферала, даем бонус реферреру
                if new_referral:
                    # Бонус 10,000 кликов реферреру
                    cur.execute("""
                    UPDATE users 
                    SET total_clicks = total_clicks + 10000
                    WHERE user_id = %s
                    RETURNING total_clicks
                    """, (referrer_id,))
                    
                    referrer_updated = cur.fetchone()
                    
                    conn.commit()
                    
                    return jsonify({
                        'success': True,
                        'message': 'Referral successfully registered',
                        'referrerNewBalance': referrer_updated['total_clicks'] if referrer_updated else None
                    })
                else:
                    conn.commit()
                    return jsonify({
                        'success': False,
                        'message': 'Referral already exists or could not be created'
                    })
                
    except Exception as e:
        app.logger.error(f"Error in register_referral: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/ranking', methods=['POST'])
def get_ranking():
    try:
        data = request.get_json()
        user_id = data.get('userId')
        username = data.get('username')
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        # Обновляем имя пользователя, если оно передано
        if username and username != 'user':
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                        UPDATE users SET username = %s WHERE user_id = %s
                        """, (username, user_id))
                        conn.commit()
            except Exception as e:
                app.logger.error(f"Error updating username: {str(e)}")
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                # Получаем топ-20 игроков по балансу
                cur.execute("""
                SELECT user_id, username, total_clicks as balance
                FROM users
                ORDER BY total_clicks DESC
                LIMIT 20
                """)
                
                top_players = []
                for row in cur.fetchall():
                    # Если имя пользователя отсутствует или установлено в default 'user'
                    display_username = row['username']
                    if not display_username or display_username == 'user':
                        display_username = f"User{row['user_id'] % 1000}"
                    
                    top_players.append({
                        'userId': row['user_id'],
                        'username': display_username,
                        'balance': row['balance']
                    })
                
                # Определяем ранг текущего пользователя
                cur.execute("""
                SELECT count(*) as total_users FROM users
                """)
                total_users = cur.fetchone()['total_users']
                
                cur.execute("""
                SELECT count(*) as better_users
                FROM users
                WHERE total_clicks > (SELECT total_clicks FROM users WHERE user_id = %s)
                """, (user_id,))
                better_users = cur.fetchone()['better_users']
                
                user_rank = better_users + 1  # Ранг = количество пользователей с большим балансом + 1
                
                return jsonify({
                    'topPlayers': top_players,
                    'userRank': {
                        'rank': user_rank,
                        'totalUsers': total_users
                    }
                })
                
    except Exception as e:
        app.logger.error(f"Error in get_ranking: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/ranking/referrals', methods=['POST'])
def get_referral_ranking():
    try:
        data = request.get_json()
        user_id = data.get('userId')
        username = data.get('username')
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        # Обновляем имя пользователя, если оно передано
        if username and username != 'user':
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                        UPDATE users SET username = %s WHERE user_id = %s
                        """, (username, user_id))
                        conn.commit()
            except Exception as e:
                app.logger.error(f"Error updating username: {str(e)}")
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                # Получаем топ-20 игроков по количеству рефералов
                cur.execute("""
                SELECT u.user_id, u.username, COUNT(r.id) as referral_count
                FROM users u
                LEFT JOIN referrals r ON u.user_id = r.referrer_id
                GROUP BY u.user_id
                ORDER BY referral_count DESC
                LIMIT 20
                """)
                
                top_players = []
                for row in cur.fetchall():
                    # Если имя пользователя отсутствует или установлено в default 'user'
                    display_username = row['username']
                    if not display_username or display_username == 'user':
                        display_username = f"User{row['user_id'] % 1000}"
                    
                    top_players.append({
                        'userId': row['user_id'],
                        'username': display_username,
                        'referralCount': row['referral_count'] or 0
                    })
                
                # Определяем ранг текущего пользователя по количеству рефералов
                cur.execute("""
                SELECT count(*) as total_users FROM users
                """)
                total_users = cur.fetchone()['total_users']
                
                cur.execute("""
                SELECT count(*) as better_users
                FROM (
                    SELECT u.user_id, COUNT(r.id) as referral_count
                    FROM users u
                    LEFT JOIN referrals r ON u.user_id = r.referrer_id
                    GROUP BY u.user_id
                ) t
                WHERE t.referral_count > (
                    SELECT COUNT(r.id) 
                    FROM referrals r 
                    WHERE r.referrer_id = %s
                )
                """, (user_id,))
                
                better_users = cur.fetchone()['better_users']
                user_rank = better_users + 1  # Ранг = количество пользователей с большим числом рефералов + 1
                
                return jsonify({
                    'topPlayers': top_players,
                    'userRank': {
                        'rank': user_rank,
                        'totalUsers': total_users
                    }
                })
                
    except Exception as e:
        app.logger.error(f"Error in get_referral_ranking: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/health')
def health_check():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        return jsonify({'status': 'ok', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'error', 'database': str(e)}), 500

@app.route('/api/user/check-subscription', methods=['POST'])
def check_user_subscription():
    try:
        data = request.get_json()
        user_id = data.get('userId')
        channel_id = data.get('channelId')
        
        if not user_id or not channel_id:
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Получаем информацию о задании
        task = get_task_by_id(int(channel_id))
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Проверяем, не выполнено ли задание уже
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT * FROM completed_tasks WHERE user_id = ? AND task_id = ?',
                 (user_id, task['id']))
        if c.fetchone():
            return jsonify({'error': 'Task already completed'}), 400
        
        # Проверяем подписку
        is_subscribed = check_subscription(user_id, channel_id)
        
        if is_subscribed:
            # Добавляем запись о выполнении задания
            c.execute('INSERT INTO completed_tasks (user_id, task_id) VALUES (?, ?)',
                     (user_id, task['id']))
            
            # Начисляем награду
            c.execute('UPDATE users SET total_clicks = total_clicks + ? WHERE user_id = ?',
                     (task['reward'], user_id))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'isSubscribed': True,
                'reward': task['reward']
            })
        else:
            conn.close()
            return jsonify({
                'isSubscribed': False
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/tasks', methods=['POST'])
def get_user_tasks():
    try:
        data = request.get_json()
        user_id = data.get('userId')
        
        if not user_id:
            return jsonify({'error': 'Missing user ID'}), 400
        
        # Получаем все задания
        tasks = get_all_tasks()
        
        # Получаем выполненные задания пользователя
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT task_id FROM completed_tasks WHERE user_id = ?', (user_id,))
        completed_tasks = {row[0] for row in c.fetchall()}
        conn.close()
        
        # Формируем ответ с информацией о выполнении
        tasks_info = []
        for task in tasks:
            tasks_info.append({
                'id': task['id'],
                'title': task['title'],
                'reward': task['reward'],
                'channel_id': task['channel_id'],
                'channel_link': task['channel_link'],
                'completed': task['id'] in completed_tasks
            })
        
        return jsonify({'tasks': tasks_info})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    try:
        # Получаем список заданий из конфигурации
        tasks = get_all_tasks()
        return jsonify(tasks)
    except Exception as e:
        app.logger.error(f"Error getting tasks: {str(e)}")
        return jsonify({'error': 'Failed to load tasks'}), 500

@app.route('/api/tasks/check-subscription', methods=['POST'])
def check_task_subscription():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        channel_id = data.get('channel_id')
        
        if not user_id or not channel_id:
            return jsonify({
                'success': False,
                'error': 'Missing required parameters'
            }), 400
            
        # Используем функцию проверки подписки через Telegram API
        is_subscribed = check_subscription(user_id, channel_id)
        
        # Находим задание по ID канала
        task = None
        for t in get_all_tasks():
            if t['channel_id'] == channel_id:
                task = t
                break
        
        if not task:
            return jsonify({
                'success': False,
                'error': 'Task not found'
            }), 404
        
        # Получаем награду за задание
        task_reward = task['reward']
        
        if is_subscribed:
            try:
                # Проверяем, выполнено ли уже задание
                with get_db_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            "SELECT 1 FROM completed_tasks WHERE user_id = %s AND task_id = %s",
                            (user_id, task['id'])
                        )
                        already_completed = cursor.fetchone() is not None
                        
                if already_completed:
                    return jsonify({
                        'success': True,
                        'is_subscribed': True,
                        'already_completed': True
                    })
                
                # Обновляем баланс пользователя и добавляем запись о выполнении задания
                with get_db_connection() as conn:
                    with conn.cursor() as cursor:
                        # Добавляем запись о выполнении задания
                        cursor.execute(
                            "INSERT INTO completed_tasks (user_id, task_id) VALUES (%s, %s)",
                            (user_id, task['id'])
                        )
                        
                        # Обновляем баланс пользователя (считаем clicks как валюту)
                        cursor.execute(
                            "UPDATE users SET total_clicks = total_clicks + %s WHERE user_id = %s",
                            (task_reward, user_id)
                        )
                        
                        conn.commit()
                
                return jsonify({
                    'success': True,
                    'is_subscribed': True,
                    'reward': task_reward
                })
            except Exception as e:
                app.logger.error(f"Database error in check_task_subscription: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': 'Database error'
                }), 500
        else:
            return jsonify({
                'success': True,
                'is_subscribed': False
            })
            
    except Exception as e:
        app.logger.error(f"Error checking subscription: {str(e)}")
        return jsonify({'error': 'Failed to check subscription'}), 500

# Инициализация базы данных при запуске
init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
