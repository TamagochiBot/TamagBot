#!/usr/bin/python

# It echoes any incoming text messages.

# This is a simple echo bot using the decorator mechanism.
import telebot
from telebot import types
import sqlite3, datetime
from Game import Player
API_TOKEN = '5932887460:AAEqLOtWTfWZrN8j8JJXiS3joAOXWPFYo5I'

bot = telebot.TeleBot(API_TOKEN, skip_pending=True)

conn = sqlite3.connect('UserInfo.db')
c = conn.cursor()
conn.commit()
c.execute('''CREATE TABLE IF NOT EXISTS users (
        userid INT PRIMARY KEY,
        fname TEXT,
        sname TEXT,
        usrname TEXT,
        join_data TIMESTAMP);    
    ''')

conn.commit()



def search_id_tlg(id_tlgrm):
    conn = sqlite3.connect('UserInfo.db')
    cursor = conn.execute("SELECT userid FROM users WHERE userid=?", (id_tlgrm,)).fetchone()
    if cursor is None:
        conn.close()
        return True
    else:
        conn.close()
        return False




bot.send_message(771366061,"Бот работает")

# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button = types.KeyboardButton('/info')
    markup.add(button)
    bot.send_message(message.chat.id, """\
Hi there, I am TestBot.
I am here to save information about you.
Write /info for collecting data.\
""", reply_markup=markup)


@bot.message_handler(commands=['info'])
def info_message(message):
    bot.send_message(message.chat.id, 'Getting information...')
    a = telebot.types.ReplyKeyboardRemove()
    with sqlite3.connect('UserInfo.db') as conn:
        _data = (str(message.from_user.id), str(message.from_user.first_name), str(message.from_user.last_name),
                 str(message.from_user.username), datetime.datetime.now())

        if search_id_tlg(message.from_user.id):
            cur = conn.cursor()
            cur.execute('''INSERT INTO users VALUES (?,?,?,?,?);''', _data)
            conn.commit()
            bot.send_message(message.chat.id, 'Collected information',reply_markup=a)
        else:
            with sqlite3.connect('UserInfo.db') as connect:
                cur = connect.cursor()
                cur.execute('''UPDATE users SET fname = ?, sname = ?, usrname = ? WHERE userid = ?''', [
                    message.from_user.first_name, message.from_user.last_name, message.from_user.username,
                    message.from_user.id])
                connect.commit()
                bot.send_message(message.chat.id, "Your information has been updated",reply_markup=a)




@bot.message_handler(commands=["button1"])
def bt1(message):
    markup = types.InlineKeyboardMarkup
    button = types.InlineKeyboardButton("foo",None,"FOO")
    markup.add()



bot.polling(none_stop=True)
