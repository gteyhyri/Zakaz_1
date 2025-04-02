from flask import Flask, request, jsonify, render_template
import time
import json
import os
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)

# Конфигурация
CONFIG = {
    'DATA_FILE': 'data/user_data.json',
    'MAX_CLICKS_BASE': 100,
    'REGEN_RATE_BASE': 0.1,  # кликов в секунду
    'LOG_FILE': 'logs/app.log',
    'LOG_LEVEL': logging.INFO
}

# Настройка логирования
def setup_logging():
    os.makedirs('logs', exist_ok=True)
    handler = RotatingFileHandler(
        CONFIG['LOG_FILE'], 
        maxBytes=10000, 
        backupCount=3
    )
    handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    app.logger.addHandler(handler)
    app.logger.setLevel(CONFIG['LOG_LEVEL'])

setup_logging()

# Убедимся, что директории существуют
os.makedirs('data', exist_ok=True)
os.makedirs('logs', exist_ok=True)

def init_user_data(user_id):
    """Инициализация данных нового пользователя"""
    return {
        'clicks': 0,
        'available_clicks': CONFIG['MAX_CLICKS_BASE'],
        'last_update': time.time(),
        'upgrades': {
            'click_power': 1,
            'regen_rate': 1,
            'max_clicks': CONFIG['MAX_CLICKS_BASE']
        },
        'created_at': datetime.now().isoformat(),
        'last_seen': datetime.now().isoformat()
    }

def load_data():
    """Загрузка данных из файла"""
    try:
        if os.path.exists(CONFIG['DATA_FILE']):
            with open(CONFIG['DATA_FILE'], 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        app.logger.error(f"Error loading data: {str(e)}")
        return {}

def save_data(data):
    """Сохранение данных в файл"""
    try:
        with open(CONFIG['DATA_FILE'], 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        app.logger.error(f"Error saving data: {str(e)}")

def update_available_clicks(user_data):
    """Обновление доступных кликов на основе времени"""
    now = time.time()
    time_passed = now - user_data['last_update']
    
    regen_amount = time_passed * (CONFIG['REGEN_RATE_BASE'] * user_data['upgrades']['regen_rate'])
    max_clicks = user_data['upgrades']['max_clicks']
    
    user_data['available_clicks'] = min(
        user_data['available_clicks'] + regen_amount,
        max_clicks
    )
    
    user_data['last_update'] = now
    user_data['last_seen'] = datetime.now().isoformat()
    return user_data

@app.before_request
def log_request():
    """Логирование входящих запросов"""
    if request.path == '/health':
        return
    app.logger.info(f"{request.method} {request.path} - {request.remote_addr}")

@app.route('/health')
def health_check():
    """Эндпоинт для проверки здоровья сервера"""
    return jsonify({'status': 'ok', 'time': datetime.now().isoformat()})

@app.route('/')
def index():
    """Главная страница приложения"""
    init_data = request.args.get('tgWebAppStartParam', '')
    user_id = init_data.split('=')[-1] if 'user_id=' in init_data else 'default_user'
    app.logger.info(f"User {user_id} accessed the app")
    return render_template('index.html', user_id=user_id)

@app.route('/click', methods=['POST'])
def handle_click():
    """Обработка кликов"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User ID missing'}), 400
        
        all_data = load_data()
        user_data = all_data.setdefault(str(user_id), init_user_data(user_id))
        user_data = update_available_clicks(user_data)
        
        if user_data['available_clicks'] >= 1:
            user_data['clicks'] += user_data['upgrades']['click_power']
            user_data['available_clicks'] -= 1
        else:
            return jsonify({'error': 'No clicks available'}), 400
        
        save_data(all_data)
        
        return jsonify({
            'clicks': user_data['clicks'],
            'available_clicks': user_data['available_clicks'],
            'upgrades': user_data['upgrades']
        })
    except Exception as e:
        app.logger.error(f"Error in handle_click: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/upgrade', methods=['POST'])
def handle_upgrade():
    """Обработка улучшений"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        upgrade_type = data.get('upgrade_type')
        
        if not user_id or not upgrade_type or upgrade_type not in ['click_power', 'regen_rate', 'max_clicks']:
            return jsonify({'error': 'Invalid parameters'}), 400
        
        all_data = load_data()
        user_data = all_data.setdefault(str(user_id), init_user_data(user_id))
        user_data = update_available_clicks(user_data)
        
        # В реальном приложении здесь должна быть проверка стоимости улучшения
        user_data['upgrades'][upgrade_type] += 1
        
        if upgrade_type == 'max_clicks':
            user_data['available_clicks'] = user_data['upgrades']['max_clicks']
        
        save_data(all_data)
        
        return jsonify({
            'upgrades': user_data['upgrades'],
            'available_clicks': user_data['available_clicks']
        })
    except Exception as e:
        app.logger.error(f"Error in handle_upgrade: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/get_data', methods=['POST'])
def get_user_data_route():
    """Получение данных пользователя"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User ID missing'}), 400
        
        all_data = load_data()
        user_data = all_data.setdefault(str(user_id), init_user_data(user_id))
        user_data = update_available_clicks(user_data)
        save_data(all_data)
        
        return jsonify({
            'clicks': user_data['clicks'],
            'available_clicks': user_data['available_clicks'],
            'upgrades': user_data['upgrades']
        })
    except Exception as e:
        app.logger.error(f"Error in get_user_data_route: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)