import telebot
import sqlite3

from telebot.types import Message

API_TOKEN = '5932887460:AAEqLOtWTfWZrN8j8JJXiS3joAOXWPFYo5I'

bot = telebot.TeleBot(API_TOKEN, skip_pending=True)

def search_id_tlg(id_tlgrm):
    conn = sqlite3.connect('UserInfo.db')
    cursor = conn.execute("SELECT id FROM pet WHERE id=?", (id_tlgrm,)).fetchone()
    if cursor is None:
        conn.close()
        return True
    else:
        conn.close()
        return False




# bot.send_message(771366061,"Бот работает")

# Handle '/start' and '/help'
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not search_id_tlg(message.from_user.id):
        bot.send_message(message.chat.id, '''Ты уже зарегестрирован в боте.''')
    else:
        bot.send_message(message.chat.id, """Похоже, ты ещё не зарегестрирован, минуту...""")
        bot.send_message(message.chat.id, """Как будут звать твоего питомца?""")
        bot.register_next_step_handler(message, registration)


def registration(message: Message):
    with sqlite3.connect('UserInfo.db') as conn:
        cur = conn.cursor()
        cur.execute('''INSERT INTO pet (id,name) VALUES (?,?);''', (message.from_user.id, str(message.text)))
        conn.commit()
    bot.reply_to(message, "Вы успешно зарегестрированы!")

#     bot.send_message(message.chat.id, """\
# Hi there, I am TestBot.
# I am here to save information about you.
# Write /info for collecting data.\
# """)


def next_step(message):
    if message.from_user.text == "Да":
        bot.send_message(message.chat.id, "Ща")


# @bot.message_handler(commands=['info'])
# def info_message(message):
#     bot.send_message(message.chat.id, 'Getting information...')
#     a = telebot.types.ReplyKeyboardRemove()
#     with sqlite3.connect('UserInfo.db') as conn:
#         _data = (str(message.from_user.id), str(message.from_user.first_name), str(message.from_user.last_name),
#                  str(message.from_user.username), datetime.datetime.now())
#
#         if search_id_tlg(message.from_user.id):
#             cur = conn.cursor()
#             cur.execute('''INSERT INTO users VALUES (?,?,?,?,?);''', _data)
#             conn.commit()
#             bot.send_message(message.chat.id, 'Collected information',reply_markup=a)
#         else:
#             with sqlite3.connect('UserInfo.db') as connect:
#                 cur = connect.cursor()
#                 cur.execute('''UPDATE users SET fname = ?, sname = ?, usrname = ? WHERE userid = ?''', [
#                     message.from_user.first_name, message.from_user.last_name, message.from_user.username,
#                     message.from_user.id])
#                 connect.commit()
#                 bot.send_message(message.chat.id, "Your information has been updated",reply_markup=a)

bot.polling(none_stop=True)
