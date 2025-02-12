import aiohttp
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states import Form

router = Router()

def setup_handlers(dp):
    dp.include_router(router)

# Команда /start
@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.reply("Привет! Я помогу вам отслеживать воду, калории и тренировки. Используйте /set_profile для настройки профиля.")

# Команда /set_profile
@router.message(Command("set_profile"))
async def set_profile(message: Message, state: FSMContext):
    await message.reply("Введите ваш вес (в кг):")
    await state.set_state(Form.weight)

@router.message(Form.weight)
async def process_weight(message: Message, state: FSMContext):
    await state.update_data(weight=int(message.text))
    await message.reply("Введите ваш рост (в см):")
    await state.set_state(Form.height)

@router.message(Form.height)
async def process_height(message: Message, state: FSMContext):
    await state.update_data(height=int(message.text))
    await message.reply("Введите ваш возраст:")
    await state.set_state(Form.age)

@router.message(Form.age)
async def process_age(message: Message, state: FSMContext):
    await state.update_data(age=int(message.text))
    await message.reply("Сколько минут активности у вас в день?")
    await state.set_state(Form.activity)

@router.message(Form.activity)
async def process_activity(message: Message, state: FSMContext):
    await state.update_data(activity=message.text)
    await message.reply("В каком городе вы находитесь?")
    await state.set_state(Form.city)

@router.message(Form.city)
async def process_city(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    global users

    users[user_id] = {
        "weight": data["weight"],
        "height": data["height"],
        "age": data["age"],
        "activity": data["activity"],
        "city": message.text,
        "water_goal": data["weight"] * 30,
        "calorie_goal": 10 * data["weight"] + 6.25 * data["height"] - 5 * data["age"]
    }

    await message.reply("Профиль сохранен! Теперь вы можете отслеживать воду и калории.")
    await state.clear()

# Команда /log_water
@router.message(Command("log_water"))
async def log_water(message: Message, users: dict):
    user_id = message.from_user.id
    if user_id not in users:
        await message.reply("Сначала настройте профиль с помощью /set_profile")
        return

    try:
        amount = int(message.text.split()[1])
        users[user_id]["logged_water"] = users[user_id].get("logged_water", 0) + amount
        remaining = users[user_id]["water_goal"] - users[user_id]["logged_water"]
        await message.reply(f"Вы выпили {amount} мл воды. Осталось {max(0, remaining)} мл до нормы.")
    except (IndexError, ValueError):
        await message.reply("Используйте команду в формате: /log_water <количество мл>")

# Команда /log_food
@router.message(Command("log_food"))
async def log_food(message: Message, users: dict):
    user_id = message.from_user.id
    if user_id not in users:
        await message.reply("Сначала настройте профиль с помощью /set_profile")
        return

    product = " ".join(message.text.split()[1:])
    if not product:
        await message.reply("Используйте команду в формате: /log_food <название продукта>")
        return

    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://world.openfoodfacts.org/cgi/search.pl?action=process&search_terms={product}&json=true") as response:
            data = await response.json()
            products = data.get('products', [])
            if products:
                first_product = products[0]
                calories = first_product.get('nutriments', {}).get('energy-kcal_100g', 0)
                users[user_id]["logged_calories"] = users[user_id].get("logged_calories", 0) + calories
                await message.reply(f"🍽 {product}: {calories} ккал добавлено.")
            else:
                await message.reply("Не удалось найти информацию о продукте.")

# Команда /check_progress
@router.message(Command("check_progress"))
async def check_progress(message: Message, users: dict):
    user_id = message.from_user.id
    if user_id not in users:
        await message.reply("Сначала настройте профиль с помощью /set_profile")
        return

    progress = (f"📊 Прогресс:\n"
                f"Вода: {users[user_id].get('logged_water', 0)} мл из {users[user_id]['water_goal']} мл\n"
                f"Калории: {users[user_id].get('logged_calories', 0)} ккал из {users[user_id]['calorie_goal']} ккал")
    await message.reply(progress)
