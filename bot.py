import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import TOKEN
from handlers import setup_handlers
from middlewares import LoggingMiddleware

# Логирование
logging.basicConfig(level=logging.INFO)

# Словарь для хранения данных пользователей
users = {}

# Создаем экземпляры бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Настраиваем middleware и обработчики
dp.message.middleware(LoggingMiddleware())
setup_handlers(dp)

async def main():
    logging.info("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
