import os
import random

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, ReplyKeyboardRemove, CallbackQuery
from telebot import custom_filters

from src.db.db_queries import DataBase

db = DataBase('testDB.db')

from app.player import Player

player_info = Player()

bot = telebot.TeleBot(os.environ["TOKEN"])

states = {}
types = {}
last_regular_event = db.count_rows("regular_event")

id_for_edit = int()
table_for_edit = str()

# Регистрация в БД
def registration(message: Message):
    db.create_player(id=message.from_user.id, pet_name=message.text, user_name=message.from_user.first_name)
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
    bot.send_message(message.chat.id, 'Привет, я ПопугБот!')
    bot.send_message(message.chat.id, 'Давай ка посмотрим, есть ли у тебя попуг 🦜')
    if db.exists(table='player', id=message.from_user.id):
        bot.send_message(message.chat.id, '''У тебя ''')
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



@bot.message_handler(commands=['attack'])
def message_handler(message):
    bot.send_message(message.chat.id, "Yes/no?", reply_markup=gen_markup())

@bot.message_handler(commands=['debug'])
def debug(message: Message):
    db.update(table='player', id=message.from_user.id, column='is_admin', data=True)
    db.save()

@bot.message_handler(commands=['create_event'])
def create_event(message: Message):
    if db.exists(table='event', id=message.from_user.id, column='user_id'):
        if db.is_admin(message.from_user.id):
            bot.send_message(message.chat.id, text='Сейчас вы можете создать лишь регулярный ивент')
        else:
            bot.send_message(message.chat.id, text='Вы не можете иметь более одного ивента')
    else:
        db.create_event(id=message.from_user.id)
        bot.send_message(message.chat.id, 'Напиши имя ивента')
        states[message.from_user.id] = 'event_name'
        types[message.from_user.id] = 'unregular'

@bot.message_handler(commands=['create_regular'])
def create_regular(message: Message):
    global last_regular_event
    if db.is_admin(message.from_user.id):
        db.create_regular_event(id=message.from_user.id)
        bot.send_message(message.chat.id, 'Напиши имя ивента')
        states[message.from_user.id] = 'event_name'
        types[message.from_user.id] = 'regular'
        last_regular_event += 1
    else:
        bot.send_message(message.chat.id, "У вас нет доступа")

@bot.message_handler(commands=['delete_event'])
def delete_event(message: Message):
    if db.exists(table='event', id=message.from_user.id, column='user_id'):
        db.delete_event(message.from_user.id)
        bot.send_message(message.chat.id, 'Ваш ивент удален')
    else:
        bot.send_message(message.chat.id, 'У вас не было ивентов')

@bot.message_handler(commands=["delete_regular"])
def delete_regular(message: Message):
    lst = get_list_of_regular()
    if len(lst) != 0:
        bot.send_message(message.chat.id, "Введите айди ивента, который хотите удалить")
        bot.send_message(message.chat.id, get_list_of_regular())
        states[message.from_user.id] = "delete_regular"
    else:
        bot.send_message(message.chat.id, "Нет регулярных событий")

@bot.message_handler(func=lambda message: message.from_user.id in states and
                                          states[message.from_user.id] == "delete_regular")
def delete_regular(message: Message):
    try:
        id = int(message.text)

        if not db.exists(table="regular_event", id = id):
            raise "doesn't exist"
        
        db.delete_regular(id)
        bot.send_message(message.chat.id, "Готово")
        del states[message.from_user.id]
    except:
            bot.send_message(message.chat.id, "Не подходящий айди. Попробуй еще раз")

def describe_event(id:int,table:str)->None:
    bot.send_message(id, text=f'\nИвент: {db.fetchone(table=table, id=id, column="event_name")}\n'
                                               f'Описание: {db.fetchone(table=table, id=id, column="description")}\n'
                                               f'Опыт: {db.fetchone(table=table, id=id, column="experience")}\n'
                                               f'Дедлайн: {db.fetchone(table=table, id=id, column="deadline")}\n\n')

@bot.message_handler(commands=['edit_event'])
def edit_event(message: Message):
    global id_for_edit
    global table_for_edit

    if db.is_admin(message.from_user.id):
        bot.send_message(message.chat.id, 'Что ты хочешь поменять?', reply_markup=MarkupFromList(['Регулярное событие',
                                                                                                  'Нерегулярное событие'
                                                                                                  ]))
        states[message.from_user.id] = 'choose_type'
        #print(states[message.from_user.id], ' ', db.is_admin(message.from_user.id))
    else:
        if db.exists(table='event',id=message.from_user.id, column='user_id'):
            id = message.from_user.id
            describe_event(id, "event")
            bot.send_message(message.chat.id, 'Что ты хочешь поменять?', reply_markup=MarkupFromList(['Название',
                                                                                                    'Описание',
                                                                                                    'Количество опыта',
                                                                                                    'Дедалйн']))
            states[message.from_user.id] = 'edit_smth'
            types[message.from_user.id] = "unregular"
            id_for_edit = message.from_user.id
            table_for_edit = "event"
        else:
            bot.send_message(message.chat.id, 'У вас нет ивентов, которые можно редактировать')

@bot.message_handler(func=lambda message: message.from_user.id in states and
                                          states[message.from_user.id] in [
                                                                           'choose_type',
                                                                           'choose_id',
                                                                           'edit_smth',
                                                                           'edit_name',
                                                                           'edit_description',
                                                                           'edit_exp',
                                                                           'edit_deadline'
                                                                           ])
def edit_event(message: Message):
    current_state = str(states[message.from_user.id])
    empty_markup = telebot.types.ReplyKeyboardRemove()
 
    global id_for_edit
    global table_for_edit
    
    match current_state:
        case 'choose_type':
            match message.text:
                case "Регулярное событие":
                    if last_regular_event != 0:
                        bot.send_message(message.chat.id, 'Напиши id ивента, который хочешь поменять?')
                        bot.send_message(message.chat.id, get_list_of_regular())

                        types[message.from_user.id] = "regular"
                        states[message.from_user.id] = "choose_id"
                        table_for_edit = "regular_event"
                    else:
                        bot.send_message(message.chat.id, 'У вас пока нет регулярных ивентов')
                        del states[message.from_user.id]
                case "Нерегулярное событие":
                    if db.exists(table='event',id=message.from_user.id, column='user_id'):
                        describe_event(id=message.from_user.id, table="event")

                        bot.send_message(message.chat.id, 'Что ты хочешь поменять?', reply_markup=MarkupFromList(['Название',
                                                                                                                'Описание',
                                                                                                                'Количество опыта',
                                                                                                                'Дедалйн']))
                        
                        states[message.from_user.id] = 'edit_smth'
                        types[message.from_user.id] = "unregular"
                        id_for_edit = message.chat.id
                        table_for_edit = "event"
                    else:
                        bot.send_message(message.chat.id, 'У вас нет ивентов, которые можно редактировать')
                case _:
                    bot.send_message(message.from_user,"Попробуй еще раз")
        case "choose_id":
            try:
                id_for_edit = int(message.text)
                if not db.exists(table="regular_event", id = id_for_edit):
                    raise "doesn't exist"
                states[message.from_user.id] = "edit_smth"
                bot.send_message(message.chat.id, 'Что ты хочешь поменять?', reply_markup=MarkupFromList(['Название',
                                                                                                                'Описание',
                                                                                                                'Количество опыта',
                                                                                                                'Дедалйн']))
            except:
                bot.send_message(message.chat.id, "Не подходящий айди. Попробуй еще раз")
        case 'edit_smth':
            #table = types[message.from_user.id]
            #print(table_for_edit + "\n\n\n\n\n\n")
            match message.text:
                case 'Название':
                    states[message.from_user.id] = 'edit_name'
                    bot.send_message(message.chat.id, 'Я вас слушаю...', reply_markup=empty_markup)
                case 'Описание':
                    states[message.from_user.id] = 'edit_description'
                    bot.send_message(message.chat.id, 'Я вас слушаю...', reply_markup=empty_markup)
                case 'Количество опыта':
                    states[message.from_user.id] = 'edit_exp'
                    bot.send_message(message.chat.id, 'Я вас слушаю...', reply_markup=empty_markup)
                case 'Дедлайн':
                    states[message.from_user.id] = 'edit_deadline'
                    bot.send_message(message.chat.id, 'Я вас слушаю...', reply_markup=empty_markup)
                case _ :
                    bot.send_message(message.chat.id, 'Попробуй еще раз')
        case 'edit_name':
            db.update(table=table_for_edit,id=id_for_edit, column='event_name',data=message.text)
            bot.send_message(message.chat.id, 'Готово!', reply_markup=empty_markup)
            db.save()
            del states[message.from_user.id]
        case 'edit_description':
            db.update(table = table_for_edit, id=id_for_edit, column='description', data=message.text)
            bot.send_message(message.chat.id, 'Готово!', reply_markup=empty_markup)
            db.save()
            del states[message.from_user.id]
        case 'edit_exp':
            db.update(table=table_for_edit, id=id_for_edit, column='experience', data=int(message.text))
            bot.send_message(message.chat.id, 'Готово!', reply_markup=empty_markup)
            db.save()
            del states[message.from_user.id]
        case 'edit_deadline':
            db.update(table=table_for_edit, id=id_for_edit, column='deadline', data=message.text)
            bot.send_message(message.chat.id, 'Готово!', reply_markup=empty_markup)
            db.save()
            del states[message.from_user.id]
        case _:
            bot.send_message(message.chat.id, 'Что то пошло не так')

def get_list_of_regular():
    text = str()
    lst_of_events = db.fetchall("regular_event")
    for event in lst_of_events:
        text += f'''ID:{event[0]}, Ивент: {event[1]}\nОписание: {event[3]} \nОпыт: {event[4]} \nДедлайн: {event[5]}\n\n'''
    return text

def get_list_of_unregular():
    text = str()
    lst_of_events = db.fetchall("event")
    for event in lst_of_events:
        text += f'''Ивент: {event[1]}\nОписание: {event[3]} \nОпыт: {event[4]} \nДедлайн: {event[5]}\n\n'''
    return text

@bot.message_handler(commands=['events'])
def get_events(message: Message):
    text = 'Список ивентов\nРегулярные:\n'
    text += get_list_of_regular()
    text += 'Нерегулярные:\n'
    text += get_list_of_unregular()

    bot.send_message(message.chat.id, text=text)

@bot.message_handler(
    func=lambda message: message.from_user.id in states and states[message.from_user.id] in [#'name_event', че это?
                                                                                             'event_description',
                                                                                             'event_exp',
                                                                                             'event_deadline',
                                                                                             'event_name'
                                                                                             ])
def create_event(message: Message): 
    current_state = str(states[message.from_user.id])
    event_type = str(types[message.from_user.id])

    table = "event" if event_type == "unregular" else "regular_event"
    user_id = message.from_user.id if table == "event" else last_regular_event

    match current_state:
        case 'event_name':
            db.update(table=table, column='event_name', id=user_id, data=message.text)
            bot.send_message(message.chat.id, 'Напишите описание ивента')
            states[message.from_user.id] = 'event_description'
        case 'event_description':
            db.update(table=table, column='description', id=user_id, data=message.text)
            bot.send_message(message.chat.id, 'Выберите количество опыта за выполнение')
            states[message.from_user.id] = 'event_exp'
        case 'event_exp':
            if str.isdigit(message.text):
                db.update(table=table, column='experience', id=user_id, data=int(message.text))
                bot.send_message(message.chat.id, 'Укажите дедлайн')
                states[message.from_user.id] = 'event_deadline'
            else:
                bot.send_message(message.chat.id, 'Введите число')
                states[message.from_user.id] = 'event_exp'
        case 'event_deadline':
            db.update(table=table, column='deadline', id=user_id, data=message.text)
            db.save()
            bot.send_message(message.chat.id, text='Ивент успешно создан')
            del states[message.from_user.id]
        case _:
            bot.send_message(message.chat.id, 'LOL')



@bot.message_handler(func= lambda message: str(message.text).split()[0] in ['Отмудохать','отмудохать'])
def kick_smb(message: Message):
    photo = open('app/Images/fights/popug'+str(random.randint(1,3))+'.jpg','rb')
    bot.send_photo(message.chat.id, photo=photo, caption=f'{message.from_user.first_name} отмудохал(а) {message.text.split(" ", 1)[1]}')

# БОИ

kb = InlineKeyboardMarkup(row_width=1)
btn_accept = InlineKeyboardButton(text='Принять', callback_data='accept')
kb.add(btn_accept)
btn_cancel = InlineKeyboardButton(text='Отказать', callback_data='cancel')
kb.add(btn_cancel)

op_id = 0
my_id = 0
op_name = ""
@bot.message_handler(func= lambda message: str(message.text.lower()).split()[0] in ['бой'])
def attack(message: Message):
    global op_id, my_id, op_name
    my_id = int(message.from_user.id)
    op_id = int(db.get_player_id(message.text.split(" ", 1)[1][1:]))
    op_name = message.text.split(" ", 1)[1][1:]
    bot.send_message(message.chat.id, f'{message.text.split(" ", 1)[1]}, Вас вызвали на бой', reply_markup=kb)
    print(message.chat.id)

class OpFilter(custom_filters.AdvancedCustomFilter):
    key='set_op_id'
    def check(self, message, text):
        if isinstance(message, CallbackQuery):
            return message.message.from_user.id in text
        return message.from_user.id in text
@bot.callback_query_handler(func=lambda call: True)
def attack_user(call):
    choosed_id = random.choice([my_id, op_id])
    print(my_id, op_id)
    print(call.message.text)
    if call.data == "accept":
        db.update(table="player", column="health", id=choosed_id,
                  data=db.fetchone(table="player", column="health", id=choosed_id) - 10)
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id,
                              text=f'у {db.fetchone(table="player", column="user_name", id=choosed_id)} отнялось 10HP. Текущее здоровье - {db.fetchone(table="player", column="health", id=choosed_id)}')
    elif call.data == "cancel":
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id, text="Бой отклонен")


def run_polling():
    print("Bot has been started...")
    bot.add_custom_filter(OpFilter())
    bot.polling(skip_pending=True)
