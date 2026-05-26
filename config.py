import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Считываем всё из окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
MANAGER_ID = int(os.getenv("MANAGER_ID", 0))
MANAGER_PHONE = os.getenv("MANAGER_PHONE")
MANAGER_USERNAME = os.getenv("MANAGER_USERNAME")
SHEET_NAME = os.getenv("SHEET_NAME")