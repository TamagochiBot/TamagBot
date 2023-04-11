import json
import sqlite3

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

from src.db.db_queries import DataBase

db = DataBase('testDB.db')

from src.app.player import Player

player_info = Player()

with open('configs/configs.json') as file:
    CONFIG = json.load(file)

BOT_TOKEN = CONFIG['BOT_TOKEN']
bot = telebot.TeleBot(BOT_TOKEN)


# Регистрация в БД
def registration(message: Message):
    # db.insert(message.from_user.id, message.text)
    db.create_player(id=message.from_user.id, pet_name=message.text, user_name=message.from_user.username)
    player_info.setId(message.from_user.id)
    bot.reply_to(message, "Вы успешно зарегестрированы!")


# Создание inline кнопок
def gen_markup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("Yes", callback_data="cb_yes"),
               InlineKeyboardButton("No", callback_data="cb_no"))
    return markup


@bot.message_handler(commands=['start'])
def start_message(message: Message):
    if db.exists(table='player', id=message.from_user.id):
        bot.send_message(message.chat.id, '''Ты уже зарегестрирован в боте.''')
    else:
        bot.send_message(message.chat.id, """Похоже, ты ещё не зарегестрирован, минуту...""")
        bot.send_message(message.chat.id, """Как будут звать твоего питомца?""")
        bot.register_next_step_handler(message, registration)


@bot.message_handler(commands=['balance'])
def get_balance(message):
    player_info.setId(message.chat.id)
    bot.send_message(message.chat.id, f"Ваш баланс: {player_info.getBalance()}")


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "cb_yes":
        bot.answer_callback_query(call.id, "Answer is Yes")
    elif call.data == "cb_no":
        bot.answer_callback_query(call.id, "Answer is No")


@bot.message_handler(commands=['attack'])
def message_handler(message):
    bot.send_message(message.chat.id, "Yes/no?", reply_markup=gen_markup())


states = {}


@bot.message_handler(commands=['create_event'])
def event_creator(message: Message):
    if db.exists(table='event', id=message.from_user.id):
        bot.send_message(message.chat.id, text='Вы не можете иметь более одного ивента')
    else:
        db.create_event(id=message.from_user.id)
        bot.send_message(message.chat.id, 'Напиши суть ивента')
        states[message.from_user.id] = 'event_description'


@bot.message_handler(
    func=lambda message: message.from_user.id in states and states[message.from_user.id] in ['name_event',
                                                                                             'event_description',
                                                                                             'event_exp',
                                                                                             'event_deadline',
                                                                                             'event_deadline'])
def event_creator(message: Message):
    current_state = str(states[message.from_user.id])
    match current_state:
        case 'event_description':
            db.update(table='event', column='description', id=message.from_user.id, data=message.text)
            bot.send_message(message.chat.id, 'Выберите количество опыта за выполнение')
            states[message.from_user.id] = 'event_exp'
        case 'event_exp':
            db.update(table='event', column='experience', id=message.from_user.id, data=int(message.text))
            bot.send_message(message.chat.id, 'Укажите дедлайн')
            states[message.from_user.id] = 'event_deadline'
        case 'event_deadline':
            db.update(table='event', column='deadline', id=message.from_user.id, data=message.text)
            db.save()
            bot.send_message(message.chat.id, text='Ивент успешно создан')
            del states[message.from_user.id]
        # case 'event_regular':
        #     # update в бд
        #     if message.text == 'Да':
        #         bot.send_message(message.chat.id, 'Когда и во сколько он будет повторяться')
        #         states[message.from_user.id] = 'regular_event_times'
        #     elif message.text == 'Нет':
        #         bot.send_message(message.chat.id, 'Время выполнения')
        #         states[message.from_user.id] = 'irregular_event_times'
        # case 'regular_event_times':
        #     ...
        case _:
            bot.send_message(message.chat.id, 'LOL')


@bot.message_handler(commands=['events'])
def events(message: Message):
    with sqlite3.connect('TestDB.db') as datab:
        # cur = db.cursor()
        # cur.execute('''SELECT Count(*) FROM TABLE event''')
        c = datab.cursor()

        # Выполняем запрос к таблице и получаем список значений столбца
        c.execute("SELECT user_id FROM event")
        result = c.fetchall()
        values = [r[0] for r in result]
        text = ''
        for i in values:
            text += f'''Описание: {db.fetchone(table='event', id=i, column='description')} \nОпыт: {db.fetchone(table='event', id=i, column='experience')} \nДедлайн: {db.fetchone(table='event', id=i, column='deadline')}\n'''
        bot.send_message(message.chat.id, text=str(text))


def run_polling():
    print("Bot has been started...")
    bot.polling(skip_pending=True)
