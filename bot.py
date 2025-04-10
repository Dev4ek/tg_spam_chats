import asyncio
import os
import subprocess
import time
import aiosqlite
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from telethon import TelegramClient
import requests
from telethon.errors import SessionPasswordNeededError
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.sessions import StringSession
import aiosqlite
from qrcode import QRCode
from aiogram.types import InputFile, ReplyKeyboardMarkup, KeyboardButton, FSInputFile, ReplyKeyboardRemove
from telethon.extensions import markdown
from telethon import types
import re


qr = QRCode()

# API_TOKEN = ''
API_TOKEN = ''


client_session = None

storage = MemoryStorage()
dp = Dispatcher(storage=storage)


class CustomMarkdown:
    @staticmethod
    def parse(text):
        text, entities = markdown.parse(text)
        for i, e in enumerate(entities):
            if isinstance(e, types.MessageEntityTextUrl):
                if e.url == 'spoiler':
                    entities[i] = types.MessageEntitySpoiler(e.offset, e.length)
                elif e.url.startswith('emoji/'):
                    entities[i] = types.MessageEntityCustomEmoji(e.offset, e.length, int(e.url.split('/')[1]))
        return text, entities
    @staticmethod
    def unparse(text, entities):
        for i, e in enumerate(entities or []):
            if isinstance(e, types.MessageEntityCustomEmoji):
                entities[i] = types.MessageEntityTextUrl(e.offset, e.length, f'emoji/{e.document_id}')
            if isinstance(e, types.MessageEntitySpoiler):
                entities[i] = types.MessageEntityTextUrl(e.offset, e.length, 'spoiler')
        return markdown.unparse(text, entities)


bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class Form(StatesGroup):
    api_id = State()
    api_hash = State()
    phone = State()
    chat_ids = State()
    awaiting_code = State()
    awaiting_password = State()
    code = State()
    send_messages = State()
    count_cercle_sendal = State()
    min_resend_time = State()


@dp.message(Command('start'))
async def cmd_start(message: types.Message, state: FSMContext):
    async with aiosqlite.connect('users.db') as db:
        user = await db.execute('select * FROM users WHERE telegram_id =?', (message.from_user.id,))
        user = await user.fetchone()
    

    print(user)
    if not user:
        await message.answer("Привет! Введите ваш api_id:")
        await state.set_state(Form.api_id)
    else:
        kb = ReplyKeyboardBuilder()
        kb.row(KeyboardButton(text='Выбрать чаты ✅'), KeyboardButton(text='Начать спам ▶️'))
        kb.row(KeyboardButton(text='Чаты 💬'), KeyboardButton(text='Войти 🙎🏼‍♂'))
        await message.answer(" Выберите действие:", reply_markup=kb.as_markup(resize_keyboard=True))


@dp.message(Form.api_id)
async def process_api_id(message: types.Message, state: FSMContext):
    await state.update_data(api_id=message.text)
    await message.answer("Теперь введите api_hash:")
    await state.set_state(Form.api_hash)

@dp.message(Form.api_hash)
async def process_api_hash(message: types.Message, state: FSMContext):
    await state.update_data(api_hash=message.text)
    await message.answer("Теперь введите ваш телефонный номер (с кодом страны):")
    await state.set_state(Form.phone)

@dp.message(Form.phone)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    user_data = await state.get_data()
    telegram_id = message.from_user.id
    
    async with aiosqlite.connect('users.db') as db:
        await db.execute('INSERT OR REPLACE INTO users (telegram_id, api_id, api_hash, phone) VALUES (?, ?, ?, ?)',
                         (telegram_id, user_data['api_id'], user_data['api_hash'], user_data['phone']))
        await db.commit()

    kb = ReplyKeyboardBuilder()
    kb.row(KeyboardButton(text='Выбрать чаты ✅'), KeyboardButton(text='Начать спам ▶️'))
    kb.row(KeyboardButton(text='Чаты 💬'), KeyboardButton(text='Войти 🙎🏼‍♂'))
    await message.answer("Ваши данные сохранены. Выберите действие:", reply_markup=kb.as_markup(resize_keyboard=True))
    await state.clear()

@dp.message(lambda message: message.text == 'Выбрать чаты ✅')
async def cmd_select_chats(message: types.Message, state: FSMContext):
    kb = ReplyKeyboardBuilder()
    kb.row(KeyboardButton(text='/start'))

    await message.answer("Введите ссылки чатов через запятую:", reply_markup=kb.as_markup(resize_keyboard=True))
    await state.set_state(Form.chat_ids)



@dp.message(lambda message: message.text == 'Чаты 💬')
async def cmd_select_chats(message: types.Message, state: FSMContext):
    async with aiosqlite.connect('users.db') as db:
        chatss = await db.execute_fetchall('SELECT url_chat FROM chats WHERE user_id = ?', (message.from_user.id,))
    chats = chatss

    list_chat = []

    for i in chats:
        list_chat.append(i[0])

    str_list = '\n'.join(list_chat)

    await bot.send_message(message.chat.id, f"Список чатов:\n{str_list}")





@dp.message(lambda message: message.text == 'Войти 🙎🏼‍♂')
async def cmd_select_chats(message: types.Message, state: FSMContext):
    async with aiosqlite.connect('users.db') as db:
        user = await db.execute_fetchall('SELECT api_id, api_hash, phone FROM users WHERE telegram_id = ?', (message.from_user.id,))
    api_id, api_hash, phone = user[0]

    client = TelegramClient(f"{api_id}", api_id, api_hash)

    if(not client.is_connected()):
        await client.connect()


    is_auth = await client.is_user_authorized()
    if is_auth:
        await bot.send_message(message.chat.id, f"Вы уже вошли")

    else:
        qr_login = await client.qr_login()
        qr.clear()
        qr.add_data(qr_login.url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        img.save(f"qr_code_{api_id}.png")
        photo = FSInputFile(f"qr_code_{api_id}.png")


        kb = ReplyKeyboardRemove()

        await message.answer_photo(photo=photo, caption='Отсканируйте qr code, у вас 20 секунд', reply_markup=kb)

        auth_now = False

        for i in range(10):
            await asyncio.sleep(2)
            print('check')
            await client.disconnect()
            await client.connect()
            con_auth = await client.is_user_authorized()
            if con_auth:
                await bot.send_message(message.chat.id, f"Вы вошли в аккаунт! Пропишите /start")
                auth_now = True
                break

        if not auth_now:
            await bot.send_message(message.chat.id, f"Не удалось авторизоваться в телеграмме. пропишите /start и войдите снова")
            await state.clear()
            return

    await state.clear()

    await client.disconnect()



@dp.message(Form.chat_ids)
async def process_chat_ids(message: types.Message, state: FSMContext):
    await message.answer("Идет добавление чатов...")
    chat_urls = message.text.split(', ')
    telegram_id = message.from_user.id

    async with aiosqlite.connect('users.db') as db:
        
        await db.execute(f"DELETE FROM chats WHERE user_id LIKE '{message.from_user.id}'")
        await db.commit()

        for chat_url in chat_urls:
            await asyncio.sleep(1.2)
            teg = chat_url[13:]
            response = requests.get(f"https://api.telegram.org/bot{API_TOKEN}/getChat?chat_id=@{teg}")

            if response.status_code == 200:
                chat_id = response.json()['result']['id']
                async with db.execute('SELECT COUNT(*) FROM chats WHERE url_chat = ?', (chat_url,)) as cursor:
                    count = await cursor.fetchone()
                    if count[0] == 0:
                        await db.execute('INSERT INTO chats (user_id, chat_id, url_chat) VALUES (?, ?, ?)', (telegram_id, int(chat_id), chat_url))
                        await bot.send_message(message.chat.id, f"✅ Ссылка добавлена: {chat_url}", disable_web_page_preview=True)
                    else:
                        await bot.send_message(message.chat.id, f"Ссылка уже существует: {chat_url}")

            else:
                print(response)
                await bot.send_message(message.chat.id, f"Ошибка с получением айди {chat_url}")

        await db.commit()

    await message.answer("Чаты сохранены.")
    await state.clear()
    



@dp.message(lambda message: message.text == 'Начать спам ▶️')
async def cmd_start_spam(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id




    async with aiosqlite.connect('users.db') as db:
        user = await db.execute_fetchall('SELECT api_id, api_hash, phone FROM users WHERE telegram_id = ?', (telegram_id,))
        chat_ids = await db.execute_fetchall('SELECT chat_id FROM chats WHERE user_id = ?', (telegram_id,))

    if user and chat_ids:
        api_id, api_hash, phone = user[0]
        chat_ids = [chat_id[0] for chat_id in chat_ids]

        client = TelegramClient(f'{api_id}', api_id, api_hash)

        if not client.is_connected():
            await client.connect()

        check_auth = await client.is_user_authorized()

        if not check_auth:
            await bot.send_message(message.chat.id, "Необходимо авторизоваться в меню бота, кнопка Войти")
            await client.disconnect()
            return
        

        await client.disconnect() 

        kb = ReplyKeyboardBuilder()
        kb.row(KeyboardButton(text='/start'))

        await message.answer("Введите сколько раз должна пройти рассылка", reply_markup=kb.as_markup(resize_keyboard=True))
        await state.set_state(Form.count_cercle_sendal)
    else:
        await message.answer("Не найдены данные для отправки сообщений.")




@dp.message(Form.count_cercle_sendal)
async def count_cercle_sendal(message: types.Message, state: FSMContext):
    if message.text.isdigit():
        await state.update_data(count_cercle_send=int(message.text))
        await message.answer("Введите через сколько повторить рассылку в секундах")
        await state.set_state(Form.min_resend_time)

    else:
        await bot.send_message(message.chat.id, "Введите число.")    



@dp.message(Form.min_resend_time)
async def minutes_repeat_sendal(message: types.Message, state: FSMContext):
    if message.text.isdigit():
        await state.update_data(minutes_repeat_send=int(message.text))
        await message.answer("Введите текст сообщения:")
        await state.set_state(Form.send_messages)

    else:
        await bot.send_message(message.chat.id, "Введите число.")



@dp.message(Form.send_messages)
async def sending(message: types.Message, state: FSMContext):
    text_message = message.text


    data = await state.get_data()

    count_cercle_send = data.get('count_cercle_send')
    minutes_repeat_send = data.get('minutes_repeat_send')


    telegram_id = message.from_user.id
    id_message = message.message_id

    async with aiosqlite.connect('users.db') as db:
        user = await db.execute_fetchall('SELECT api_id, api_hash, phone FROM users WHERE telegram_id = ?', (telegram_id,))
        chat_ids = await db.execute_fetchall('SELECT url_chat FROM chats WHERE user_id = ?', (telegram_id,))

    list_chat_ids = []

    for chat_id in chat_ids:
        api_id, api_hash, phone = user[0]
        list_chat_ids.append(chat_id[0])

    client = TelegramClient(f'{api_id}', api_id, api_hash)

    if not client.is_connected():
        await client.connect()


    try:

        await bot.send_message(message.chat.id, "Идет отправка сообщений", reply_markup=ReplyKeyboardRemove())

        await state.clear()


        client.parse_mode = CustomMarkdown()
        time_wait = 0


        smile_entitu = message.entities

        def replace_custom_emojis(text, entities):
            pattern = re.compile(r'\{prem\}(.+?)\{prem\}')
            matches = pattern.findall(text)
            if matches:
                for match, entity in zip(matches, entities):
                    emoji_symbol = match
                    emoji_id = entity.custom_emoji_id
                    
                    replacement = f"[{emoji_symbol}](emoji/{emoji_id})"
                    text = text.replace(f"{{prem}}{emoji_symbol}{{prem}}", replacement, 1)
                    
            return text
            
            
        emodji_entit = []
        
        for i in smile_entitu:
            if i.type == "custom_emoji":
                emodji_entit.append(i)
            
        text_ready = replace_custom_emojis(str(text_message), emodji_entit)

        for __time in range(count_cercle_send):
            for chat_id in list_chat_ids:
                username_chat = chat_id.split("/")[-1]
                print(username_chat)

                if time_wait < 10:
                    try:
                        
                        entity = await client.get_entity(username_chat)
                        await client.send_message(entity, text_ready)
                        await bot.send_message(message.chat.id, f"Сообщение было отправленно {chat_id}", disable_web_page_preview=True)
                        time_wait = time_wait + 1
                        
                        
                    except Exception as e:
                        await bot.send_message(message.chat.id, f"Ошибка при отправке сообщения в чат {chat_id}: {str(e)}")
                else:
                    await asyncio.sleep(40)
                    time_wait = 0
                    try:
                        entity = await client.get_entity(username_chat)
                        await client.send_message(entity, text_ready)
                        await bot.send_message(message.chat.id, f"Сообщение было отправленно {chat_id}", disable_web_page_preview=True)
                        time_wait = time_wait + 1
                    except Exception as e:
                        await bot.send_message(message.chat.id, f"Ошибка при отправке сообщения в чат {chat_id}: {str(e)}")


            await asyncio.sleep(minutes_repeat_send)
    except Exception as e:
        print(f"Ошибка при отправке сообщений: ", e)

    await client.disconnect() 
    await bot.send_message(message.chat.id, "Рассылка завершена, пропишите /start")




async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Создание таблицы пользователей
    cursor.execute('''CREATE TABLE IF NOT EXISTS users(
                        id INTEGER PRIMARY KEY,
                        telegram_id INTEGER UNIQUE,
                        api_id INTEGER,
                        api_hash TEXT,
                        phone TEXT
                    )''')

    # Создание таблицы чатов
    cursor.execute('''CREATE TABLE IF NOT EXISTS chats (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER,
                        url_chat TEXT,
                        chat_id INTEGER,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )''')

    conn.commit()
    conn.close()



    print('Bot started...')
    asyncio.run(main())









    
