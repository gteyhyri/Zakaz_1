# Конфигурация заданий
TASKS = {
    '1': {
        'id': '1',
        'title': 'ДЕНЬГИ В TONE',
        'channel_id': '-1002435743499',
        'channel_link': 'https://t.me/moneyiston',
        'reward': 500
    }
}

# Функция для получения задания по ID
def get_task_by_id(task_id):
    return TASKS.get(str(task_id))

# Функция для получения всех заданий
def get_all_tasks():
    return list(TASKS.values()) 
