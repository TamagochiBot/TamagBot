import telebot
import json

from db.db_queries import DataBase
db = DataBase('testDB.db')

from app.player import Player
player_info = Player()

with open('configs/configs.json') as file:
      CONFIG = json.load(file)

BOT_TOKEN = CONFIG['BOT_TOKEN']

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start_message(message):
    if not db.exists(message.from_user.id):
        bot.send_message(message.chat.id, '''Ты уже зарегестрирован в боте.''')
    else:
        bot.send_message(message.chat.id, """Похоже, ты ещё не зарегестрирован, минуту...""")
        bot.send_message(message.chat.id, """Как будут звать твоего питомца?""")
        bot.register_next_step_handler(message, registration)

        

def registration(message):
    db.insert(message.from_user.id, message.text)
    player_info.setId(message.from_user.id)
    bot.reply_to(message, "Вы успешно зарегестрированы!")

@bot.message_handler(commands=['balance'])
def get_balance(message):
    bot.send_message(message.chat.id, player_info.getBalance())

def run_polling():
    print("Bot has been started...")
    bot.infinity_polling()