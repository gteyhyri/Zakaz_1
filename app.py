import os
from flask import Flask, request, jsonify, render_template
from datetime import datetime
import psycopg2
from psycopg2.extras import DictCursor
import time
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__, static_folder='static')

# Конфигурация PostgreSQL для Render
DATABASE_CONFIG = {
    'host': 'dpg-cvmoh6ngi27c73cv25dg-a.oregon-postgres.render.com',
    'database': 'zakazbd',
    'user': 'zakazbd_user',
    'password': 'hk99lR7fL5jYIdjpGauwzsWA4COo00pm',
    'port': '5432'
}

DATABASE_URL = f"postgresql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}/{DATABASE_CONFIG['database']}"

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
        conn = psycopg2.connect(DATABASE_URL)
        app.logger.info("Successfully connected to database")
        return conn
    except Exception as e:
        app.logger.error(f"Database connection error: {str(e)}")
        raise

def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Проверяем существование таблицы
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            total_clicks INTEGER DEFAULT 0,
            available_clicks NUMERIC DEFAULT 100,
            click_power INTEGER DEFAULT 1,
            max_clicks INTEGER DEFAULT 100,
            regen_rate NUMERIC DEFAULT 1,
            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Создаем индекс для улучшения производительности
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id)
        """)
        
        conn.commit()
        app.logger.info("Database tables initialized successfully")
    except Exception as e:
        app.logger.error(f"Error initializing database: {str(e)}")
        raise
    finally:
        cur.close()
        conn.close()

# Инициализация базы данных при старте
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/user', methods=['POST'])
def get_user():
    conn = None
    cur = None
    try:
        data = request.get_json()
        user_id = data.get('userId')
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=DictCursor)
        
        # Получаем или создаем пользователя
        cur.execute("""
        INSERT INTO users (user_id)
        VALUES (%s)
        ON CONFLICT (user_id) DO UPDATE SET user_id = EXCLUDED.user_id
        RETURNING *
        """, (user_id,))
        
        user_data = cur.fetchone()
        
        # Обновляем доступные клики
        now = datetime.now()
        time_passed = (now - user_data['last_update']).total_seconds()
        regen_amount = time_passed * (0.1 * user_data['regen_rate'])
        new_clicks = min(
            float(user_data['available_clicks']) + regen_amount,
            float(user_data['max_clicks'])
        )
        
        cur.execute("""
        UPDATE users 
        SET available_clicks = %s, last_update = %s
        WHERE user_id = %s
        RETURNING *
        """, (new_clicks, now, user_id))
        
        updated_data = cur.fetchone()
        conn.commit()
        
        return jsonify({
            'totalClicks': updated_data['total_clicks'],
            'availableClicks': updated_data['available_clicks'],
            'clickPower': updated_data['click_power'],
            'maxClicks': updated_data['max_clicks'],
            'regenRate': updated_data['regen_rate']
        })
        
    except Exception as e:
        app.logger.error(f"Error in get_user: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/api/user/click', methods=['POST'])
def handle_click():
    conn = None
    cur = None
    try:
        data = request.get_json()
        user_id = data.get('userId')
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=DictCursor)
        
        # Блокируем строку для обновления
        cur.execute("""
        SELECT available_clicks, click_power 
        FROM users 
        WHERE user_id = %s
        FOR UPDATE
        """, (user_id,))
        
        user = cur.fetchone()
        
        if not user or float(user['available_clicks']) < 1:
            return jsonify({'error': 'No clicks available'}), 400
        
        # Обновляем клики
        cur.execute("""
        UPDATE users 
        SET 
            total_clicks = total_clicks + %s,
            available_clicks = available_clicks - 1,
            last_update = CURRENT_TIMESTAMP
        WHERE user_id = %s
        RETURNING total_clicks, available_clicks
        """, (user['click_power'], user_id))
        
        result = cur.fetchone()
        conn.commit()
        
        return jsonify({
            'totalClicks': result['total_clicks'],
            'availableClicks': float(result['available_clicks'])
        })
        
    except Exception as e:
        app.logger.error(f"Error in handle_click: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/api/user/upgrade', methods=['POST'])
def handle_upgrade():
    conn = None
    cur = None
    try:
        data = request.get_json()
        user_id = data.get('userId')
        upgrade_type = data.get('upgradeType')
        
        if not user_id or not upgrade_type:
            return jsonify({'error': 'Missing parameters'}), 400
        
        valid_upgrades = ['click_power', 'regen_rate', 'max_clicks']
        if upgrade_type not in valid_upgrades:
            return jsonify({'error': 'Invalid upgrade type'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=DictCursor)
        
        # Применяем улучшение
        if upgrade_type == 'max_clicks':
            cur.execute("""
            UPDATE users 
            SET 
                max_clicks = max_clicks + 10,
                available_clicks = available_clicks + 10,
                last_update = CURRENT_TIMESTAMP
            WHERE user_id = %s
            RETURNING *
            """, (user_id,))
        else:
            cur.execute(f"""
            UPDATE users 
            SET 
                {upgrade_type} = {upgrade_type} + 1,
                last_update = CURRENT_TIMESTAMP
            WHERE user_id = %s
            RETURNING *
            """, (user_id,))
        
        updated_data = cur.fetchone()
        conn.commit()
        
        return jsonify({
            'clickPower': updated_data['click_power'],
            'regenRate': updated_data['regen_rate'],
            'maxClicks': updated_data['max_clicks'],
            'availableClicks': float(updated_data['available_clicks'])
        })
        
    except Exception as e:
        app.logger.error(f"Error in handle_upgrade: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/health')
def health_check():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        return jsonify({'status': 'ok', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'error', 'database': str(e)}), 500
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)