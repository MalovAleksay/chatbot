# Подключаем библиотеки
import asyncio
import logging
import requests
from aiogram import Bot, Dispatcher, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton

import config  # тут токен для бота

TOKEN = config.token  # токен берем отсюда
bot_r = Router()  # роутер для команд

# Стейты для анкеты, типа шаги заполнения
class Anketa(StatesGroup):
    name = State()  # для имени
    fam = State()  # фамилия
    phone = State()  # телефончик
    mail = State()  # емаил
    color = State()  # цвет

# Спрашиваем фамилию после имени
@bot_r.message(Anketa.name)
async def ask_name(msg: types.Message, state: FSMContext):
    name = msg.text
    await state.update_data(name=name)  # сохраняем имя

    # Пробуем угадать пол по имени, но не используем эту информацию дальше
    resp = requests.get(f"https://api.genderize.io/?name={name}")
    if resp.status_code == 200:
        gender_data = resp.json()
        gender = gender_data.get("gender", None)
        if gender == "male":
            gender_rus = "мужчина"
        elif gender == "female":
            gender_rus = "женщина"
        else:
            gender_rus = "не ясно"

        await msg.answer(f"Кажется, ты {gender_rus}.")
    else:
        await msg.answer("Пол не угадал, ладно.")

    await state.set_state(Anketa.fam)  # следующий шаг
    await msg.answer("Как тебя по фамилии?")

# Спрашиваем телефон после фамилии
@bot_r.message(Anketa.fam)
async def ask_fam(msg: types.Message, state: FSMContext):
    fam = msg.text  # берем фамилию
    await state.update_data(fam=fam)  # сохраняем фамилию
    await state.set_state(Anketa.phone)  # следующий шаг
    await msg.answer("Какой у тебя телефон?")

# Запрос почты после телефона
@bot_r.message(Anketa.phone)
async def ask_phone(msg: types.Message, state: FSMContext):
    phone = msg.text
    await state.update_data(phone=phone)
    await state.set_state(Anketa.mail)
    await msg.answer("Какой у тебя email?")

# Спрашиваем любимый цвет после почты
@bot_r.message(Anketa.mail)
async def ask_mail(msg: types.Message, state: FSMContext):
    mail = msg.text
    await state.update_data(mail=mail)
    await state.set_state(Anketa.color)

    knopki = [
        [KeyboardButton(text="Красный"), KeyboardButton(text="Синий"), KeyboardButton(text="Зеленый")],
        [KeyboardButton(text="Желтый"), KeyboardButton(text="Черный")]
    ]

    color_keyboard = ReplyKeyboardMarkup(keyboard=knopki, resize_keyboard=True, one_time_keyboard=True)

    await msg.answer("Какой твой любимый цвет?", reply_markup=color_keyboard)

# Итоговое сообщение с данными пользователя
@bot_r.message(Anketa.color)
async def ask_color(msg: types.Message, state: FSMContext):
    color = msg.text
    await state.update_data(color=color)

    user_data = await state.get_data()

    text = f"Все, что я знаю о тебе:\nИмя: {user_data['name']}\nФамилия: {user_data['fam']}\nТелефон: {user_data['phone']}\nEmail: {user_data['mail']}\nЛюбимый цвет: {user_data['color']}"
    await msg.answer(text, reply_markup=ReplyKeyboardRemove())
    await state.clear()

# Стартовая команда
@bot_r.message(CommandStart())
async def start_cmd(msg: types.Message, state: FSMContext):
    await state.set_state(Anketa.name)  # начинаем с имени
    await msg.answer("Приветик! Как твое имя?", reply_markup=ReplyKeyboardRemove())

# Главная функция для запуска бота
async def main():
    bot = Bot(token=TOKEN)  # создаем бота
    dp = Dispatcher()  # диспетчер для обработки команд
    dp.include_router(bot_r)  # добавляем роутер

    await dp.start_polling(bot)  # начинаем слушать команды

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)  # настраиваем логирование
    asyncio.run(main())  # запускаем бота
