import os
from flask import Flask, request, jsonify, render_template
import psycopg2
from psycopg2.extras import DictCursor
import logging
from logging.handlers import RotatingFileHandler
from flask_cors import CORS
from datetime import datetime, timedelta

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
        
        conn.commit()
        app.logger.info("Database schema updated successfully")
    except Exception as e:
        app.logger.error(f"Error updating database schema: {str(e)}")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Основная таблица пользователей
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
        
        # Индекс для быстрого поиска пользователей
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id)
        """)
        
        # Таблица для учета рефералов
        cur.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id SERIAL PRIMARY KEY,
            referrer_id BIGINT NOT NULL,
            referred_id BIGINT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(referrer_id, referred_id),
            FOREIGN KEY (referrer_id) REFERENCES users(user_id),
            FOREIGN KEY (referred_id) REFERENCES users(user_id)
        )
        """)
        
        # Индекс для быстрого поиска рефералов по реферреру
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id)
        """)
        
        conn.commit()
        app.logger.info("Database initialized")
        
        # После создания таблиц, обновляем схему если нужно
        check_and_update_schema()
        
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
        username = data.get('username', 'user')
        
        if not user_id:
            app.logger.error("No user ID provided")
            return jsonify({'error': 'User ID is required'}), 400
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("SELECT CURRENT_TIMESTAMP AS now")
                server_now = cur.fetchone()['now']
                
                # Обновляем/создаем пользователя и сохраняем имя пользователя
                try:
                    cur.execute("""
                    INSERT INTO users (user_id, last_update, username)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE
                    SET 
                        available_clicks = LEAST(
                            users.max_clicks,
                            users.available_clicks + EXTRACT(EPOCH FROM (%s - users.last_update)) * 0.1 * users.regen_rate
                        ),
                        last_update = %s,
                        username = COALESCE(EXCLUDED.username, users.username)
                    RETURNING *
                    """, (user_id, server_now, username, server_now, server_now))
                except psycopg2.Error as e:
                    # Если возникла ошибка с колонкой username, используем запрос без неё
                    if "column" in str(e) and "username" in str(e):
                        app.logger.warning("Username column not found, using legacy query")
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
                    else:
                        raise
                
                user_data = cur.fetchone()
                conn.commit()
                
                # Обновляем заработок для всех рефереров, если пользователь что-то заработал
                if user_data['total_clicks'] > 0:
                    try:
                        cur.execute("""
                        UPDATE referrals
                        SET earnings = %s * 0.1  -- 10% от заработка реферала
                        WHERE referred_id = %s
                        """, (user_data['total_clicks'], user_id))
                        conn.commit()
                    except psycopg2.Error as e:
                        if "column" in str(e) and "earnings" in str(e):
                            app.logger.warning("Earnings column not found, skipping referral earnings update")
                            conn.rollback()
                        else:
                            raise
                
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
                
                if not result:
                    # Если пользователь не найден, это может быть ошибка в базе данных
                    app.logger.error(f"User {user_id} not found in handle_click")
                    return jsonify({'error': 'User not found'}), 404
                
                if float(result['available_clicks']) < 0:
                    return jsonify({'error': 'No clicks available'}), 400
                
                # Обновляем заработок для всех рефереров
                try:
                    cur.execute("""
                    UPDATE referrals
                    SET earnings = %s * 0.1  -- 10% от заработка реферала
                    WHERE referred_id = %s
                    """, (result['total_clicks'], user_id))
                    conn.commit()
                except psycopg2.Error as e:
                    if "column" in str(e) and "earnings" in str(e):
                        app.logger.warning("Earnings column not found, skipping referral earnings update")
                        # Не делаем rollback, т.к. основной апдейт прошел успешно
                    else:
                        raise
                
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
                        referrals.append({
                            'id': ref['referred_id'],
                            'username': ref['username'] or 'user',
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
