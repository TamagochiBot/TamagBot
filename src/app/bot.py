import json

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from db.db_queries import DataBase
db = DataBase('testDB.db')

from app.player import Player
player_info = Player()

with open('configs/configs.json') as file:
      CONFIG = json.load(file)

BOT_TOKEN = CONFIG['BOT_TOKEN']
bot = telebot.TeleBot(BOT_TOKEN)

# Регистрация в БД
def registration(message):
    db.insert(message.from_user.id, message.text)
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
def start_message(message):
    if not db.exists(message.from_user.id):
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

def run_polling():
    print("Bot has been started...")
    bot.polling()