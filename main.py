import os
if not os.path.exists("config.py"):
    API_TOKEN = input("Введите API токен вашего бота: ")
    MONGO_URL = input("Введите URL для подключения к MongoDB: ")
    DB_NAME = input("Введите имя базы данных: ")
    COLLECTION_NAME = input("Введите имя коллекции: ")
    with open("config.py", "w") as config_file:
        config_file.write(f'API_TOKEN = "{API_TOKEN}"\n')
        config_file.write(f'MONGO_URL = "{MONGO_URL}"\n')
        config_file.write(f'DB_NAME = "{DB_NAME}"\n')
        config_file.write(f'COLLECTION_NAME = "{COLLECTION_NAME}"\n')
                          
import json
from aiogram import Bot, Dispatcher, types
import pymongo
from datetime import datetime, timedelta
from bson import json_util
from config import API_TOKEN, MONGO_URL, DB_NAME, COLLECTION_NAME

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

client = pymongo.MongoClient(MONGO_URL)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

async def aggregate_salary_data(dt_from, dt_upto, group_type):
    dataset = []
    labels = []
    if group_type == "hour":
        delta = timedelta(hours=1)
    elif group_type == "day":
        delta = timedelta(days=1)
    elif group_type == "month":
        delta = timedelta(days=30)

    current_time = dt_from
    while current_time <= dt_upto:
        salary = 0
        for record in collection.find({"dt": {"$gte": current_time, "$lt": current_time + delta}}):
            salary += record["value"]
        dataset.append(salary)
        labels.append(current_time.isoformat())
        current_time += delta
    result = {"dataset": dataset, "labels": labels}
    return result

@dp.message_handler(lambda message: True)
async def handle_message(message: types.Message):
    try:
        message_text = message.text
        data = json.loads(message_text, object_hook=json_util.object_hook)
        if "dt_from" in data and "dt_upto" in data and "group_type" in data:
            dt_from = datetime.fromisoformat(data["dt_from"])
            dt_upto = datetime.fromisoformat(data["dt_upto"])
            group_type = data["group_type"]
            result = await aggregate_salary_data(dt_from, dt_upto, group_type)
            await message.answer(json.dumps(result, default=json_util.default, indent=4))
        else:
            await message.answer("Недостаточно данных для агрегации.")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {str(e)}")

@dp.message_handler(commands=['start'])
async def start_message(message: types.Message):
    await message.answer("Привет! Отправь JSON с данными для агрегации зарплат.")

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
