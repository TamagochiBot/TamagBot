import os

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, ReplyKeyboardRemove

from src.db.db_queries import DataBase

db = DataBase('testDB.db')

from src.app.player import Player

player_info = Player()


bot = telebot.TeleBot(os.environ['TOKEN'])


# Регистрация в БД
def registration(message: Message):
    db.create_player(id=message.from_user.id, pet_name=message.text, user_name=message.from_user.username)
    player_info.setId(message.from_user.id)
    bot.reply_to(message, "Вы успешно зарегестрированы!")


# Создание inline кнопок
def gen_markup() -> telebot.types.InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("Yes", callback_data="cb_yes"),
               InlineKeyboardButton("No", callback_data="cb_no"))
    return markup

#Создание KeyBoard кнопок
def MarkupFromList(listOfButtons):
    markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for buttonName in listOfButtons:
        btn=telebot.types.KeyboardButton(buttonName)
        markup.add(btn)
    return markup


@bot.message_handler(commands=['start'])
def start_message(message: Message):
    if db.exists(table='player', id=message.from_user.id):
        bot.send_message(message.chat.id, '''Ты уже зарегестрирован в боте.''')
    else:
        bot.send_message(message.chat.id, """Похоже, ты ещё не зарегестрирован, минуту...""")
        bot.send_message(message.chat.id, """Как будут звать твоего питомца?""")
        bot.register_next_step_handler(message, registration)

@bot.message_handler(commands=['cancel'])
def cancel(message: Message):
    if message.from_user.id in states:
        del states[message.from_user.id]
    db.save()
    bot.send_message(message.chat.id, 'Отмена', reply_markup=ReplyKeyboardRemove())


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


@bot.message_handler(commands=['debug'])
def debug(message: Message):
    db.update(table='player', id=message.from_user.id, column='pet_name', data='Edic')
    db.save()


@bot.message_handler(commands=['create_event'])
def event_creator(message: Message):
    if db.exists(table='event', id=message.from_user.id, column='user_id'):
        bot.send_message(message.chat.id, text='Вы не можете иметь более одного ивента')
    else:
        db.create_event(id=message.from_user.id)
        bot.send_message(message.chat.id, 'Напиши имя ивента')
        states[message.from_user.id] = 'event_name'


@bot.message_handler(commands=['event_delete'])
def event_deleter(message: Message):
    if db.exists(table='event', id=message.from_user.id, column='user_id'):
        db.delete_event(message.from_user.id)
        bot.send_message(message.chat.id, 'Ваш ивент удален')
    else:
        bot.send_message(message.chat.id, 'У вас не было ивентов')

@bot.message_handler(commands=['event_edit'])
def event_edit(message: Message):
    if db.exists(table='event',id=message.from_user.id, column='user_id'):
        i = message.from_user.id
        bot.send_message(message.chat.id, text=f'\nИвент: {db.fetchone(table="event", id=i, column="event_name")}\n'
                                               f'Описание: {db.fetchone(table="event", id=i, column="description")}\n'
                                               f'Опыт: {db.fetchone(table="event", id=i, column="experience")}\n'
                                               f'Дедлайн: {db.fetchone(table="event", id=i, column="deadline")}\n\n')
        bot.send_message(message.chat.id, 'Что ты хочешь поменять?', reply_markup=MarkupFromList(['Название',
                                                                                                  'Описание',
                                                                                                  'Количество опыта',
                                                                                                  'Дедалйн']))
        states[message.from_user.id] = 'edit_smth'
    else:
        bot.send_message(message.chat.id, 'У вас нет ивентов, которые можно редактировать')



@bot.message_handler(func=lambda message: message.from_user.id in states and
                                          states[message.from_user.id] in ['edit_smth',
                                                                           'edit_name',
                                                                           'edit_description',
                                                                           'edit_exp',
                                                                           'edit_deadline'
                                                                           ])
def event_redactor(message: Message):
    current_state = str(states[message.from_user.id])
    empty_markup = telebot.types.ReplyKeyboardRemove()
    match current_state:
        case 'edit_smth':
            match message.text:
                case 'Название':
                    states[message.from_user.id] = 'edit_name'
                    bot.send_message(message.chat.id, 'Я вас слушаю...', reply_markup=empty_markup)
                case 'Описание':
                    states[message.from_user.id] = 'edit_description'
                    bot.send_message(message.chat.id, 'Я вас слушаю...', reply_markup=empty_markup)
                case 'Колчиество опыта':
                    states[message.from_user.id] = 'edit_exp'
                    bot.send_message(message.chat.id, 'Я вас слушаю...', reply_markup=empty_markup)
                case 'Дедалйн':
                    states[message.from_user.id] = 'edit_deadline'
                    bot.send_message(message.chat.id, 'Я вас слушаю...', reply_markup=empty_markup)
                case _ :
                    bot.send_message(message.chat.id, 'Попробуй еще раз')
        case 'edit_name':
            db.update(table='event',id=message.from_user.id, column='event_name',data=message.text)
            bot.send_message(message.chat.id, 'Готово!', reply_markup=empty_markup)
            db.save()
            del states[message.from_user.id]
        case 'edit_description':
            db.update(table='event', id=message.from_user.id, column='description', data=message.text)
            bot.send_message(message.chat.id, 'Готово!', reply_markup=empty_markup)
            db.save()
            del states[message.from_user.id]
        case 'edit_exp':
            db.update(table='event', id=message.from_user.id, column='experience', data=int(message.text))
            bot.send_message(message.chat.id, 'Готово!', reply_markup=empty_markup)
            db.save()
            del states[message.from_user.id]
        case 'edit_deadline':
            db.update(table='event', id=message.from_user.id, column='deadline', data=message.text)
            bot.send_message(message.chat.id, 'Готово!', reply_markup=empty_markup)
            db.save()
            del states[message.from_user.id]
        case _:
            bot.send_message(message.chat.id, 'Что то пошло не так')


@bot.message_handler(commands=['events'])
def events(message: Message):
    lst_of_events = db.fetchall("event")
    text = 'Списко ивентов\n'
    for event in lst_of_events:
        text += f'''\nИвент: {event[1]}\nОписание: {event[3]} \nОпыт: {event[4]} \nДедлайн: {event[5]}\n\n'''
    bot.send_message(message.chat.id, text=str(text))

@bot.message_handler(
    func=lambda message: message.from_user.id in states and states[message.from_user.id] in ['name_event',
                                                                                             'event_description',
                                                                                             'event_exp',
                                                                                             'event_deadline',
                                                                                             'event_name'
                                                                                             ])
def event_creator(message: Message):
    current_state = str(states[message.from_user.id])
    match current_state:
        case 'event_name':
            db.update(table='event', column='event_name', id=message.from_user.id, data=message.text)
            bot.send_message(message.chat.id, 'Напишите описание ивента')
            states[message.from_user.id] = 'event_description'
        case 'event_description':
            db.update(table='event', column='description', id=message.from_user.id, data=message.text)
            bot.send_message(message.chat.id, 'Выберите количество опыта за выполнение')
            states[message.from_user.id] = 'event_exp'
        case 'event_exp':
            if str.isdigit(message.text):
                db.update(table='event', column='experience', id=message.from_user.id, data=int(message.text))
                bot.send_message(message.chat.id, 'Укажите дедлайн')
                states[message.from_user.id] = 'event_deadline'
            else:
                bot.send_message(message.chat.id, 'Введите число')
                states[message.from_user.id] = 'event_exp'
        case 'event_deadline':
            db.update(table='event', column='deadline', id=message.from_user.id, data=message.text)
            db.save()
            bot.send_message(message.chat.id, text='Ивент успешно создан')
            del states[message.from_user.id]
        case _:
            bot.send_message(message.chat.id, 'LOL')

def run_polling():
    print("Bot has been started...")
    bot.polling(skip_pending=True)
