import telebot
import sqlite3
from db_queries import DataBase

from telebot.types import Message

API_TOKEN = '5932887460:AAGFIyG-f20HF43SyLvQnHgKl6cF2X3xPt4'

bot = telebot.TeleBot(API_TOKEN,skip_pending=True)

db = DataBase("C:\\hackatons\\dasi\\bot1\\TamagBot\\src\\testDB.db")

# Handle '/start' and '/help'
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not db.exists(int(message.from_user.id)):
        bot.send_message(message.chat.id, '''Ты уже зарегестрирован в боте.''')
    else:
        bot.send_message(message.chat.id, """Похоже, ты ещё не зарегестрирован, секунду...""")
        bot.send_message(message.chat.id, """Как будут звать твоего питомца?""")
        bot.register_next_step_handler(message, registration)


def registration(message: Message):
    db.insert(message.from_user.id, str(message.text))
    db.save()
    bot.reply_to(message, "Вы успешно зарегестрированы!")


def next_step(message):
    if message.from_user.text == "Да":
        bot.send_message(message.chat.id, "Ща")


bot.polling(none_stop=True)
