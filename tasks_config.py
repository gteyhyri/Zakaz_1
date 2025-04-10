TASKS = [
    {
        "id": 1,
        "title": "ДЕНЬГИ В TONE ",
        "reward": 500,
        "channel_id": "-1002435743499",
        "channel_link": "t.me/moneyiston"
    },
   # {
   #      "id": 2,
   #     "title": "",
   #     "reward": 500,
   #     "channel_id": "-1002050956587",
   #     "channel_link": "https://t.me/cryptonews"
    #},
    # Добавьте новые задания по аналогии
    # {
    #     "id": 3,
    #     "title": "Название задания",
    #     "reward": 500,
    #     "channel_id": "ID_канала",
    #     "channel_link": "ссылка_на_канал"
    # }
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
