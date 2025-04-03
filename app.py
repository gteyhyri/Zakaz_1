import os
from flask import Flask, request, jsonify, render_template
import psycopg2
from psycopg2.extras import DictCursor
import logging
from logging.handlers import RotatingFileHandler
from flask_cors import CORS

app = Flask(__name__, static_folder='static')
CORS(app)

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

def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
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
        
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id)
        """)
        
        conn.commit()
        app.logger.info("Database initialized")
    except Exception as e:
        app.logger.error(f"Error initializing database: {str(e)}")
        raise
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/user', methods=['POST'])
def get_user():
    try:
        data = request.get_json()
        user_id = data.get('userId')
        
        if not user_id:
            app.logger.error("No user ID provided")
            return jsonify({'error': 'User ID is required'}), 400
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("SELECT CURRENT_TIMESTAMP AS now")
                server_now = cur.fetchone()['now']
                
                cur.execute("""
                INSERT INTO users (user_id, last_update)
                VALUES (%s, %s)
                ON CONFLICT (user_id) DO UPDATE
                SET 
                    available_clicks = LEAST(
                        users.max_clicks,
                        users.available_clicks + EXTRACT(EPOCH FROM (%s - users.last_update)) * 0.1 * users.regen_rate
                    ),
                    last_update = %s
                RETURNING *
                """, (user_id, server_now, server_now, server_now))
                
                user_data = cur.fetchone()
                conn.commit()
                
                return jsonify({
                    'totalClicks': user_data['total_clicks'],
                    'availableClicks': float(user_data['available_clicks']),
                    'clickPower': user_data['click_power'],
                    'maxClicks': user_data['max_clicks'],
                    'regenRate': user_data['regen_rate']
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
                cur.execute("""
                WITH updated AS (
                    UPDATE users 
                    SET 
                        total_clicks = total_clicks + click_power,
                        available_clicks = GREATEST(0, available_clicks - 1),
                        last_update = CURRENT_TIMESTAMP
                    WHERE user_id = %s AND available_clicks >= 1
                    RETURNING *
                )
                SELECT * FROM updated
                UNION
                SELECT * FROM users WHERE user_id = %s AND NOT EXISTS (SELECT 1 FROM updated)
                """, (user_id, user_id))
                
                result = cur.fetchone()
                conn.commit()
                
                if not result or float(result['available_clicks']) < 0:
                    return jsonify({'error': 'No clicks available'}), 400
                
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
        
        valid_upgrades = ['power', 'regen', 'max']
        if upgrade_type not in valid_upgrades:
            return jsonify({'error': 'Invalid upgrade type'}), 400
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                if upgrade_type == 'max':
                    cur.execute("""
                    UPDATE users 
                    SET 
                        max_clicks = max_clicks + 10,
                        available_clicks = available_clicks + 10,
                        last_update = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                    RETURNING *
                    """, (user_id,))
                elif upgrade_type == 'regen':
                    cur.execute("""
                    UPDATE users 
                    SET 
                        regen_rate = regen_rate + 0.1,
                        last_update = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                    RETURNING *
                    """, (user_id,))
                else:
                    cur.execute("""
                    UPDATE users 
                    SET 
                        click_power = click_power + 1,
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

@app.route('/health')
def health_check():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        return jsonify({'status': 'ok', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'error', 'database': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)