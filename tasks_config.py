# Конфигурация заданий
TASKS = [

    {
        "id": 1,
        "title": "ДЕНЬГИ В  TONE",
        "channel_id": "-1002435743499",
        "channel_link": "t.me/moneyiston",
        "reward": 500
    }
]

# Функция для получения задания по ID
def get_task_by_id(task_id):
    for task in TASKS:
        if task["id"] == task_id:
            return task
    return None

# Функция для получения всех заданий
def get_all_tasks():
    return TASKS 
