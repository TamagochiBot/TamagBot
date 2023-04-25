import math
import os
import random
from datetime import datetime

import schedule
from threading import Thread
import time as tm

from PIL import Image
from PIL import ImageOps

import telebot
from telebot import custom_filters
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, ReplyKeyboardRemove, CallbackQuery

from src.db.db_queries import DataBase

db = DataBase('testDB.db')

from src.app.player import Player

player_info = Player()

bot = telebot.TeleBot(os.environ["TOKEN"])

states = {}
type_of_event = {}
state_of_regular = {}
participants_of_regular = {}
for_edit = {}
last_regular_event = db.get_last_regular()

id_for_edit = int()
table_for_edit = str()


# Создание inline кнопок
def gen_markup() -> telebot.types.InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("Yes", callback_data="cb_yes"),
               InlineKeyboardButton("No", callback_data="cb_no"))
    return markup


# Создание InlineKeyboard кнопок
def InlineMarkupFromLists(listOfButtons, listOfCalls):
    markup = telebot.types.InlineKeyboardMarkup()
    for i in range(len(listOfCalls)):
        btn = telebot.types.InlineKeyboardButton(text=listOfButtons[i], callback_data=listOfCalls[i])
        markup.add(btn)
    return markup


# Создание KeyBoard кнопок
def MarkupFromList(listOfButtons):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for buttonName in listOfButtons:
        btn = telebot.types.KeyboardButton(buttonName)
        markup.add(btn)
    return markup


def run_threaded(message: Message, id: int, table: str, event_data: list):
    Thread(target=notification_event,
           kwargs={"message": message, "id": id, "table": table, "event_data": event_data}).start()
    if table == "event":
        return schedule.CancelJob
    elif state_of_regular[id] == "close":
        del participants_of_regular[id]
        del state_of_regular[id]
        return schedule.CancelJob


def notification_event(message: Message, id: int, table: str, event_data: list):
    if table == "event":
        bot.send_message(message.chat.id, text=f'Ваш ивент:\n'
                                               f'{event_data[0]}\n'
                                               f'Описание: {event_data[1]}\n'
                                               f'Опыт: {event_data[2]}\n'
                                               f'Закончился!')
        db.delete_event(id)
    elif state_of_regular[id] == "run":
        bot.send_message(message.from_user.id, text=f'Ваш ивент:\n'
                                                    f'{event_data[0]}\n'
                                                    f'Описание: {event_data[1]}\n'
                                                    f'Опыт: {event_data[2]}\n'
                                                    f'Участники: {participants_of_regular[id]}')
    # return schedule.CancelJob


@bot.message_handler(commands=['help'])
def helper(message: Message):
    photo = open('app/Images/popug.jpg', 'rb')
    text = 'Привет, я ПопугБот 🦜\n\n' \
           'Что я могу?\n' \
           'Ты можешь создавать ивенты - регуляраные и нереулярные. ' \
           'Регулярные повотряются заданное тобой время и их могут создавть/редактировать только админы. ' \
           'Нерегулярные выполняются один раз и их может создвавать любой попуг, ты можешь иметь не более одного ивента\n' \
           'Просто введи /create_event для нерегулярного и /create_regular для регулярного.\n' \
           'Также есть несколько интересных фич)\n' \
           'Отправь "ПопугБот, кто [твое утверждение]"\n' \
           'Или можешь начать подозревать кого нибудь, просто отправь "Подозревать"'
    bot.send_photo(message.chat.id, photo=photo, caption=text)


@bot.message_handler(commands=['start'])
def start_message(message: Message):
    bot.send_message(message.chat.id, 'Привет, я ПопугБот!')
    bot.send_message(message.chat.id, 'Давай ка посмотрим, есть ли у тебя попуг 🦜')
    if db.exists(table='player', id=message.from_user.id):
        bot.send_message(message.chat.id, '''У тебя уже есть попуг)''')
    else:
        bot.send_message(message.chat.id, """Похоже, ты ещё не зарегестрирован, минуту...""")
        bot.send_message(message.chat.id, """Как будут звать твоего питомца?""")
        states[message.from_user.id] = 'registry'


# Регистрация в БД
@bot.message_handler(func=lambda message: message.from_user.id in states and
                                          states[message.from_user.id] == 'registry')
def registration(message: Message):
    db.create_player(id=message.from_user.id, pet_name=message.text, user_name=message.from_user.username)
    bot.reply_to(message, "Вы успешно зарегестрированы!")
    db.add_body_skin(message.from_user.id, "1")
    db.add_head_skin(message.from_user.id, "1")
    db.add_weapon_skin(message.from_user.id, "0")
    db.set_body_skin(message.from_user.id, "1")
    db.set_head_skin(message.from_user.id, "1")
    db.set_weapon_skin(message.from_user.id, "0")
    db.save()
    del states[message.from_user.id]


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
        type_of_event[message.from_user.id] = 'unregular'


def check_scheduler():
    while True:
        schedule.run_pending()
        tm.sleep(1)


@bot.message_handler(commands=['create_regular'])
def create_regular(message: Message):
    global last_regular_event
    if db.is_admin(message.from_user.id):
        db.create_regular_event(id=message.from_user.id)
        bot.send_message(message.chat.id, 'Напиши имя ивента')
        states[message.from_user.id] = 'event_name'
        type_of_event[message.from_user.id] = 'regular'
        last_regular_event += 1
        state_of_regular[last_regular_event] = "run"
        participants_of_regular[last_regular_event] = ''
    else:
        bot.send_message(message.chat.id, "У вас нет доступа")


@bot.message_handler(
    func=lambda message: message.from_user.id in states and states[message.from_user.id] in [
        'event_description',
        'event_exp',
        'event_deadline',
        'event_name'
    ])
def create_event(message: Message):
    global last_regular_event
    current_state = str(states[message.from_user.id])
    event_type = str(type_of_event[message.from_user.id])

    table = "event" if event_type == "unregular" else "regular_event"
    id = message.from_user.id if table == "event" else last_regular_event

    match current_state:
        case 'event_name':
            db.update(table=table, column='event_name', id=id, data=message.text)
            bot.send_message(message.chat.id, 'Напишите описание ивента')
            states[message.from_user.id] = 'event_description'
        case 'event_description':
            db.update(table=table, column='description', id=id, data=message.text)
            bot.send_message(message.chat.id, 'Выберите количество опыта за выполнение')
            states[message.from_user.id] = 'event_exp'
        case 'event_exp':
            if str.isdigit(message.text):
                db.update(table=table, column='experience', id=id, data=int(message.text))
                bot.send_message(message.chat.id, 'Укажите дедлайн в секундах')
                states[message.from_user.id] = 'event_deadline'
            else:
                bot.send_message(message.chat.id, 'Введите число')
                # states[message.from_user.id] = 'event_exp' нахера это делать?
        case 'event_deadline':
            db.update(table=table, column='deadline', id=id, data=message.text)
            db.save()

            event_data = list()
            event_data.append(db.get_event_name(id))
            event_data.append(db.get_event_description(id))
            event_data.append(db.get_event_experience(id))

            schedule.every(int(message.text)).seconds.do(run_threaded, table=table, id=id, message=message,
                                                         event_data=event_data)  # .tag(message.from_user.id)
            bot.send_message(message.chat.id, text='Ивент успешно создан')
            del states[message.from_user.id]
        case _:
            bot.send_message(message.chat.id, 'LOL')


@bot.message_handler(commands=['delete_event'])
def delete_event(message: Message):
    if db.exists(table='event', id=message.from_user.id, column='user_id'):
        db.delete_event(message.from_user.id)
        bot.send_message(message.chat.id, 'Ваш ивент удален')
        schedule.clear(message.from_user.id)
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

        if not db.exists(table="regular_event", id=id):
            raise "doesn't exist"
        state_of_regular[id] = "close"
        db.delete_regular(id)
        bot.send_message(message.chat.id, "Готово")
        del states[message.from_user.id]
    except:
        bot.send_message(message.chat.id, "Не подходящий айди. Попробуй еще раз")


def describe_event(id: int, table: str) -> None:
    bot.send_message(id, text=f'\nИвент: {db.get_event_name(id)}\n'
                              f'Описание: {db.get_event_description(id)}\n'
                              f'Опыт: {db.get_event_experience(id)}\n'
                              f'Дедлайн: {db.get_event_deadline(id)}\n\n')


@bot.message_handler(commands=['edit_event'])
def edit_event(message: Message):
    if db.is_admin(message.from_user.id):
        bot.send_message(message.chat.id, 'Что ты хочешь поменять?', reply_markup=MarkupFromList(['Регулярное событие',
                                                                                                  'Нерегулярное событие'
                                                                                                  ]))
        states[message.from_user.id] = 'choose_type'
    else:
        if db.exists(table='event', id=message.from_user.id, column='user_id'):
            id = message.from_user.id
            describe_event(id, "event")
            bot.send_message(message.chat.id, 'Что ты хочешь поменять?', reply_markup=MarkupFromList(['Название',
                                                                                                      'Описание',
                                                                                                      'Количество опыта',
                                                                                                      'Дедалйн']))
            states[message.from_user.id] = 'edit_smth'
            type_of_event[message.from_user.id] = "unregular"
            id_for_edit = message.from_user.id
            table_for_edit = 'event'
            for_edit[message.from_user.id] = (id_for_edit, table_for_edit)
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
    id_for_edit, table_for_edit = for_edit[message.from_user.id]

    match current_state:
        case 'choose_type':
            match message.text:
                case "Регулярное событие":
                    if last_regular_event != 0:
                        bot.send_message(message.chat.id, 'Напиши id ивента, который хочешь поменять?')
                        bot.send_message(message.chat.id, get_list_of_regular())

                        type_of_event[message.from_user.id] = "regular"
                        states[message.from_user.id] = "choose_id"
                        for_edit[message.from_user.id][1] = "regular_event"
                    else:
                        bot.send_message(message.chat.id, 'У вас пока нет регулярных ивентов')
                        del states[message.from_user.id]
                case "Нерегулярное событие":
                    if db.exists(table='event', id=message.from_user.id, column='user_id'):
                        describe_event(id=message.from_user.id, table="event")

                        bot.send_message(message.chat.id, 'Что ты хочешь поменять?',
                                         reply_markup=MarkupFromList(['Название',
                                                                      'Описание',
                                                                      'Количество опыта',
                                                                      'Дедалйн']))

                        states[message.from_user.id] = 'edit_smth'
                        type_of_event[message.from_user.id] = "unregular"
                        for_edit[message.from_user.id][0] = message.chat.id
                        for_edit[message.from_user.id][1] = "event"
                    else:
                        bot.send_message(message.chat.id, 'У вас нет ивентов, которые можно редактировать')
                case _:
                    bot.send_message(message.chat.id, "Попробуй еще раз")
        case "choose_id":
            try:
                for_edit[message.from_user.id][0] = int(message.text)
                if not db.exists(table="regular_event", id=for_edit[message.from_user.id][0]):
                    raise "doesn't exist"
                states[message.from_user.id] = "edit_smth"
                bot.send_message(message.chat.id, 'Что ты хочешь поменять?', reply_markup=MarkupFromList(['Название',
                                                                                                          'Описание',
                                                                                                          'Количество опыта',
                                                                                                          'Дедалйн']))
            except:
                bot.send_message(message.chat.id, "Не подходящий айди. Попробуй еще раз")
        case 'edit_smth':
            # table = types[message.from_user.id]
            # print(table_for_edit + "\n\n\n\n\n\n")
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
                case _:
                    bot.send_message(message.chat.id, 'Попробуй еще раз')
        case 'edit_name':
            db.update(table=table_for_edit, id=id_for_edit, column='event_name', data=message.text)
            bot.send_message(message.chat.id, 'Готово!', reply_markup=empty_markup)
            db.save()
            del states[message.from_user.id]
        case 'edit_description':
            db.update(table=table_for_edit, id=id_for_edit, column='description', data=message.text)
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


# ВЫПОЛНЕНИЕ ИВЕНТОВ


@bot.message_handler(func=lambda message: message.text == 'my_debug' and not (message.reply_to_message is None))
def debugger(message: Message):
    if db.is_admin(message.from_user.id):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.row_width = 2
        btn1 = InlineKeyboardButton(text='Реуглярный', callback_data='reg')
        btn2 = InlineKeyboardButton(text='Нерегулярный', callback_data='irreg')
        markup.add(btn1, btn2)
        bot.send_message(message.chat.id, text='Какой ивент выполнил попуг?', reply_markup=markup)


# @bot.callback_query_handler(func=lambda call: call.data in ['reg', 'irreg'])
# def admin_access(call: CallbackQuery):
#     match call.data:
#         case 'reg':
#             list = get_list_of_regular()
#             if len(list)


# ВЫПОЛНЕНИЕ ИВЕНТОВ


# FUN


@bot.message_handler(func=lambda message: str(message.text).split()[0] in ['Отмудохать', 'отмудохать'])
def kick_smb(message: Message):
    photo = open('app/Images/fights/popug' + str(random.randint(1, 3)) + '.jpg', 'rb')
    bot.send_photo(message.chat.id, photo=photo,
                   caption=f'{message.from_user.first_name} отмудохал(а) {message.text[11:]}')


@bot.message_handler(
    func=lambda message: str(message.text).split()[0] in ['Попугбот', 'попугбот'] and str(message.text).split()[
        1] == 'кто')
def who_is(message: Message):
    names = db.fetchall_in_one('player', 'user_name')
    bot.send_message(message.chat.id,
                     text=f'Несомненно,{message.text[12:]} - это {names[random.randint(0, len(names) - 1)][0]}')


@bot.message_handler(func=lambda message: message.text == 'Подозревать')
def suspect(message: Message):
    video = open('app/Images/SuspectPopug.mp4', 'rb')
    bot.send_video(message.chat.id, video=video)


# FUN


kb = InlineKeyboardMarkup(row_width=1)
btn_change = InlineKeyboardButton(text='Заменить', callback_data='change')
kb.add(btn_change)
btn_dont_change = InlineKeyboardButton(text='Не менять', callback_data='dont change')
kb.add(btn_dont_change)


@bot.callback_query_handler(func=lambda call: call.data in ['change', 'dont change'])
def switch_item(message: Message, person_id, item_type, item_name, item_stats, item_mod, item_rare):
    db_item_name = ""
    match item_type:
        case 0:
            db_item_name = "helmet"
        case 1:
            db_item_name = "chestplate"
        case 2:
            db_item_name = "item1"
        case 3:
            db_item_name = "item2"
    current_name = ""
    current_stats = db.get_worn_item_stats(person_id, db_item_name)
    current_mod = db.get_worn_item_mod(person_id, db_item_name)
    current_rare = ""
    bot.send_message(message.chat.id, text="")


bronze_case_list = ["Модный кепарик", "Вьетнамский нон", "Рыцарский шлем", "Кибершлем из Найт-сити", "Страдания лиандри"
                    "Футболка фаната AC/DC", "Толстовка \"Люблю Том Ям\"", "Рыцарский доспех из музея Лондона", "Любимая футболка Ви", "Эгида солнечного пламени"
                    "Гитара", "Палочки для риса", "Длинный меч", "Катана Арасаки", "Грань бесконечности"
                    "Водяной пистолет", "Миска рис еда", "Лук империи Майя", "Пистолет Джонни Сильверхенда", "Убийца кракенов"]

silver_case_list = ["Пакет из под чипсов", "Летняя панамка", "Маска Джейсона", "Маска злодея из Скуби-Ду", "Шапка Мономаха"
                    "Плащ разведкорпуса", "Черный плащ", "Костюм на Хэллоуин", "Костюм Человека-паука", "Прикид Майкла Джексона"
                    "Боксерские перчатки Рокки", "Французский багет", "Резиновая утка", "Лестница из фильма про Джеки Чана", "Топор викинга"
                    "Йо-йо", "Руки из Хаги ваги", "Хук Пуджа", "Лассо Индианы Джонса", "Требушет"]

golden_case_list = ["Маска Жнеца", "Шапка хиппи", "Противогаз", "Маска Кайла Крейна", "Любимая кепка босса"
                    "Костюм космонавта", "Халат ученого", "Mark 7", "Куртка ночного бегуна", "Косплей"
                    "Межгалактический звездолет", "Карандаш Джона Уика", "Клинки неразимов", "Дубинка из Харрана", "Лук-порей Хатсуне Мику"
                    "Пулемет Чака Норриса", "Палочка Гарри Поттера", "Винтовка Джима Рейнора", "Крюк-кошка", "Салют-взрыв"]

skin_case_list = []


open_case_list = ["Открыть бронзовый сундук", "Открыть серебряный сундук",
                  "Открыть золотой сундук", "Открыть сундук скинов"]


@bot.message_handler(func=lambda message: message.text in open_case_list)
def get_item_from_case(message: Message,  person_id):
    case_type = ""
    if message == open_case_list[0]:
        case_type = "bronze"
    elif message == open_case_list[1]:
        case_type = "silver"
    elif message == open_case_list[2]:
        case_type = "gold"
    elif message == open_case_list[3]:
        case_type = "skin"

    result = int(random.random() * 100)
    type_result = int(random.random() * 4)
    list_navigator = type_result
    number_of_item_in_list = 0

    item_name = ""
    item_type = type_result
    item_stats = 0
    item_mod = "Пусто"
    item_rare = ""

    case_list = []
    match case_type:
        case "bronze":
            case_list = bronze_case_list
        case "silver":
            case_list = silver_case_list
        case "gold":
            case_list = golden_case_list
        case "skin":
            case_list = skin_case_list

    if result < 35:
        item_rare = "обычный"
        number_of_item_in_list = 0

    elif result < 70:
        item_rare = "обычный"
        number_of_item_in_list = 1

    elif result < 84:
        item_rare = "редкий"
        number_of_item_in_list = 2

    elif result < 98:
        item_rare = "редкий"
        number_of_item_in_list = 3

    else:
        item_rare = "эпический"
        number_of_item_in_list = 4

    item_name = case_list[list_navigator * 5 + number_of_item_in_list]

    if case_type != "skin":
        level = int(db.get_level(person_id))
        if item_type == 0:
            item_stats = int(math.sqrt(((number_of_item_in_list + 2) // 2) * level)
                             * 2 * math.sqrt(random.random() * 30 + 15))
            mod_random = random.random() * 100
            if mod_random < 80:
                mod_random = "Госстандарт"
            elif mod_random < 95:
                mod_random = "Только мечом"
            else:
                mod_random = "Мудрость древних ара"
        elif item_type == 1:
            item_stats = int(math.sqrt(((number_of_item_in_list + 2) // 2) * level)
                             * 0.05 * math.sqrt(random.random() * 30 + 15))
            mod_random = random.random() * 100
            if mod_random < 80:
                mod_random = "Пернатая броня"
            elif mod_random < 95:
                mod_random = "Без наворотов"
            else:
                mod_random = "Ядовитые доспехи"
        elif item_type == 2:
            item_stats = int(math.sqrt(((number_of_item_in_list + 2) // 2) * level)
                             * 0.5 * math.sqrt(random.random() * 30 + 15))
            mod_random = random.random() * 100
            if mod_random < 85:
                mod_random = "Снаряжение новичка"
            elif mod_random < 95:
                mod_random = "Критовый попуг"
            else:
                mod_random = "Убийца богов"
        elif item_type == 3:
            item_stats = int(math.sqrt(((number_of_item_in_list + 2) // 2) * level)
                             * 0.8 * math.sqrt(random.random() * 30 + 15))
        switch_item(message, person_id, item_type, item_name, item_stats, item_mod, item_rare)
    else:
        switch_case_item(message, person_id. item_name, item_rare)


def experience_change(person_id, experience):
    lvl_from_table = int(db.get_level(person_id))
    exp_needed = int(math.sqrt(lvl_from_table * 60) * 30)
    exp_got = db.get_experience(person_id) + experience
    while exp_got >= exp_needed:
        exp_got -= exp_needed
        lvl_from_table += 1
        exp_needed = int(math.sqrt(lvl_from_table * 60) * 30)
        factor = lvl_from_table ** (1.2/3.0)
        current_health = int(factor * db.get_health(person_id))
        current_strength = int(factor * db.get_strength(person_id))
        db.set_lvl(person_id, lvl_from_table)
        db.set_health(person_id, current_health)
        db.set_strength(person_id, current_strength)
    db.set_exp(person_id, exp_got)
    db.save()


# БОИ

kb = InlineKeyboardMarkup(row_width=1)
btn_accept = InlineKeyboardButton(text='Принять', callback_data='accept')
kb.add(btn_accept)
btn_cancel = InlineKeyboardButton(text='Отказать', callback_data='cancel')
kb.add(btn_cancel)

op_id = 0
my_id = 0
op_name = ""


@bot.message_handler(func=lambda message: str(message.text.lower()).split()[0] in ['бой'])
def attack(message: Message):
    global op_id, my_id, op_name
    my_id = message.from_user.id
    op_id = db.get_player_id(message.text.split(" ", 1)[1][1:])
    op_name = message.text.split(" ", 1)[1][1:]
    bot.send_message(message.chat.id, f'{message.text.split(" ", 1)[1]}, Вас вызвали на бой', reply_markup=kb)


class OpFilter(custom_filters.AdvancedCustomFilter):
    key = 'set_op_id'

    def check(self, message, text):
        if isinstance(message, CallbackQuery):
            return message.message.from_user.id in text
        return message.from_user.id in text


@bot.callback_query_handler(func=lambda call: call.data in ['accept', 'cancel'])
def attack_user(call: CallbackQuery):
    print(my_id, op_id)
    print(call.message.text)

    if call.data == "accept":
    #     bot.send_photo(call.message.chat.id,photo=photo)
        my_standard_damage = int(db.get_strength(my_id))
        op_standard_damage = int(db.get_strength(op_id))
        my_first_item_damage = db.get_worn_item_stats(my_id, "item1")
        op_first_item_damage = db.get_worn_item_stats(op_id, "item1")
        my_second_item_damage = db.get_worn_item_stats(my_id, "item2")
        op_second_item_damage = db.get_worn_item_stats(op_id, "item2")
        my_item_ability = db.get_worn_item_mod(my_id, "item1")
        op_item_ability = db.get_worn_item_mod(op_id, "item1")
        my_helmet_hp = db.get_worn_item_stats(my_id, "helmet")
        op_helmet_hp = db.get_worn_item_stats(op_id, "helmet")
        my_helmet_ability = db.get_worn_item_mod(my_id, "helmet")
        op_helmet_ability = db.get_worn_item_mod(op_id, "helmet")
        my_chest_plate_armor = db.get_worn_item_stats(my_id, "chestplate")
        op_chest_plate_armor = db.get_worn_item_stats(op_id, "chestplate")
        my_chest_plate_ability = db.get_worn_item_mod(my_id, "chestplate")
        op_chest_plate_ability = db.get_worn_item_mod(op_id, "chestplate")

        if my_helmet_ability == "Госстандарт":
            my_hp = int(int(db.get_health(my_id)) * 1.05) + my_helmet_hp
        else:
            my_hp = int(db.get_health(my_id)) + my_helmet_hp
        if op_helmet_ability == "Госстандарт":
            op_hp = int(int(db.get_health(op_id)) * 1.05) + op_helmet_hp
        else:
            op_hp = int(db.get_health(op_id)) + op_helmet_hp

        my_armor = my_chest_plate_armor
        op_armor = op_chest_plate_armor

        attacker = "me"
        my_turn = 0
        op_turn = 0

        while my_hp > 0 and op_hp > 0:
            sum_damage = 0
            wisdom_of_ara_flag = 0
            only_sword_flag = 0
            poisonous_armor_flag = 0
            no_mods_flag = 0
            gods_killer_flag = 0
            krit_perrot_flag = 0

            if attacker == "me":
                last_hp = op_hp
                my_turn += 1

                sum_damage += my_standard_damage
                if my_turn % 3 == 0:
                    if op_helmet_ability == "Только мечом" and int(random.random() * 100) <= 14:
                        sum_damage += int(my_second_item_damage * 0.8)
                        only_sword_flag = 1
                    else:
                        sum_damage += my_second_item_damage
                    if op_helmet_ability == "Мудрость древних ара" and int(random.random() * 100) <= 9:
                        wisdom_of_ara_flag = 1
                    elif op_chest_plate_ability == "Ядовитые доспехи" and int(random.random() * 100) <= 4:
                        my_hp -= int(sum_damage * (1 - my_armor))
                        poisonous_armor_flag = 1
                    else:
                        op_hp -= int(sum_damage * (1 - op_armor))
                else:
                    sum_damage += my_first_item_damage
                    if op_chest_plate_ability == "Без наворотов" and int(random.random() * 100) <= 14:
                        op_hp -= int(sum_damage * (1 - op_armor))
                        no_mods_flag = 1
                    else:
                        if my_item_ability == "Критовый попуг" and int(random.random() * 100) <= 4:
                            sum_damage = int(sum_damage * 1.4)
                            krit_perrot_flag = 1
                        elif my_item_ability == "Снаряжение новичка":
                            sum_damage += int(my_first_item_damage * 0.01)
                        if op_helmet_ability == "Мудрость древних ара" and int(random.random() * 100) <= 9:
                            wisdom_of_ara_flag = 1
                        elif op_chest_plate_ability == "Ядовитые доспехи" and int(random.random() * 100) <= 4:
                            if my_item_ability == "Убийца богов" and int(random.random() * 100) <= 4:
                                my_hp -= sum_damage
                                gods_killer_flag = 1
                                poisonous_armor_flag = 1
                            else:
                                my_hp -= int(sum_damage * (1 - my_armor))
                                poisonous_armor_flag = 1
                        else:
                            if my_item_ability == "Убийца богов" and int(random.random() * 100) <= 4:
                                op_hp -= sum_damage
                                gods_killer_flag = 1
                            else:
                                op_hp -= int(sum_damage * (1 - op_armor))

                mods_attack_list = []
                mods_defend_list = []

                if wisdom_of_ara_flag == 1:
                    mods_defend_list.append("Мудрость древних ара")
                if only_sword_flag == 1:
                    mods_defend_list.append("Только мечом")
                if poisonous_armor_flag == 1:
                    mods_defend_list.append("Ядовитые доспехи")
                if no_mods_flag == 1:
                    mods_attack_list.append("Без наворотов")
                if gods_killer_flag == 1:
                    mods_attack_list.append("Убийца богов")
                if krit_perrot_flag == 1:
                    mods_attack_list.append("Критовый попуг")

                bot.send_message(my_id, f'Атакует - {db.get_pet_name(my_id)} \n' +
                                 f'Моды, использованные в раунде: {mods_attack_list} \n' +
                                 f'Всего урона с модификаторами: {sum_damage} \n' +
                                 f'Защищается - {db.get_pet_name(op_id)} \n' +
                                 f'Моды, использованные в раунде: {mods_defend_list} \n' +
                                 f'Всего получено урона: {last_hp - op_hp}')

                bot.send_message(op_id, f'Атакует - {db.get_pet_name(my_id)} \n' +
                                 f'Моды, использованные в раунде: {mods_attack_list} \n' +
                                 f'Всего урона с модификаторами: {sum_damage} \n' +
                                 f'Защищается - {db.get_pet_name(op_id)} \n' +
                                 f'Моды, использованные в раунде: {mods_defend_list} \n' +
                                 f'Всего получено урона: {last_hp - op_hp}')
                attacker = "opponent"

            else:
                op_turn += 1
                sum_damage += op_standard_damage
                last_hp = my_hp

                if op_turn % 3 == 0:
                    if my_helmet_ability == "Только мечом" and int(random.random() * 100) <= 14:
                        sum_damage += int(op_second_item_damage * 0.8)
                        only_sword_flag = 1
                    else:
                        sum_damage += op_second_item_damage
                    if my_helmet_ability == "Мудрость древних ара" and int(random.random() * 100) <= 9:
                        wisdom_of_ara_flag = 1
                    elif my_chest_plate_ability == "Ядовитые доспехи" and int(random.random() * 100) <= 4:
                        op_hp -= int(sum_damage * (1 - op_armor))
                        poisonous_armor_flag = 1
                    else:
                        my_hp -= int(sum_damage * (1 - my_armor))
                else:
                    sum_damage += op_first_item_damage
                    if my_chest_plate_ability == "Без наворотов" and int(random.random() * 100) <= 14:
                        my_hp -= int(sum_damage * (1 - my_armor))
                        no_mods_flag = 1
                    else:
                        if op_item_ability == "Критовый попуг" and int(random.random() * 100) <= 4:
                            sum_damage = int(sum_damage * 1.4)
                            krit_perrot_flag = 1
                        elif op_item_ability == "Снаряжение новичка":
                            sum_damage += int(op_first_item_damage * 0.01)
                        if my_helmet_ability == "Мудрость древних ара" and int(random.random() * 100) <= 9:
                            wisdom_of_ara_flag = 1
                        elif my_chest_plate_ability == "Ядовитые доспехи" and int(random.random() * 100) <= 4:
                            if op_item_ability == "Убийца богов" and int(random.random() * 100) <= 4:
                                op_hp -= sum_damage
                                poisonous_armor_flag = 1
                                gods_killer_flag = 1
                            else:
                                op_hp -= int(sum_damage * (1 - op_armor))
                                poisonous_armor_flag = 1
                        else:
                            if op_item_ability == "Убийца богов" and int(random.random() * 100) <= 4:
                                my_hp -= sum_damage
                                gods_killer_flag = 1
                            else:
                                my_hp -= int(sum_damage * (1 - my_armor))

                mods_attack_list = []
                mods_defend_list = []

                if wisdom_of_ara_flag == 1:
                    mods_defend_list.append("Мудрость древних ара")
                if only_sword_flag == 1:
                    mods_defend_list.append("Только мечом")
                if poisonous_armor_flag == 1:
                    mods_defend_list.append("Ядовитые доспехи")
                if no_mods_flag == 1:
                    mods_attack_list.append("Без наворотов")
                if gods_killer_flag == 1:
                    mods_attack_list.append("Убийца богов")
                if krit_perrot_flag == 1:
                    mods_attack_list.append("Критовый попуг")

                bot.send_message(my_id, f'Атакует - {db.get_pet_name(op_id)} \n' +
                                 f'Моды, использованные в раунде: {mods_attack_list} \n' +
                                 f'Всего урона с модификаторами: {sum_damage} \n' +
                                 f'Защищается - {db.get_pet_name(my_id)} \n' +
                                 f'Моды, использованные в раунде: {mods_defend_list} \n' +
                                 f'Всего получено урона: {last_hp - my_hp}')

                bot.send_message(op_id, f'Атакует - {db.get_pet_name(op_id)} \n' +
                                 f'Моды, использованные в раунде: {mods_attack_list} \n' +
                                 f'Всего урона с модификаторами: {sum_damage} \n' +
                                 f'Защищается - {db.get_pet_name(my_id)} \n' +
                                 f'Моды, использованные в раунде: {mods_defend_list} \n' +
                                 f'Всего получено урона: {last_hp - my_hp}')

                attacker = "me"

        if my_hp <= 0:
            stolen_cookies = int(random.random() * db.get_balance(my_id) / 5)
            bot.send_message(my_id, f'Победитель - {db.get_pet_name(op_id)} \n'
                                    f'он крадет у {db.get_pet_name(my_id)} {stolen_cookies} \n')
            bot.send_message(op_id, f'Победитель - {db.get_pet_name(op_id)} \n'
                                    f'он крадет у {db.get_pet_name(my_id)} {stolen_cookies} \n')
        else:
            stolen_cookies = int(random.random() * db.get_balance(op_id) / 5)
            bot.send_message(my_id, f'Победитель - {db.get_pet_name(my_id)} \n'
                                    f'он крадет у {db.get_pet_name(op_id)} {stolen_cookies} \n')
            bot.send_message(op_id, f'Победитель - {db.get_pet_name(op_id)} \n'
                                    f'он крадет у {db.get_pet_name(op_id)} {stolen_cookies} \n')

    elif call.data == "cancel":
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id, text="Бой отклонен")


# БОИ


# CustomizePet

def CreatePetImage(number_of_body, number_of_head, number_of_weapon):
    way_to_body = "app/Images/Body" + number_of_body + ".png"
    way_to_head = "app/Images/Head" + number_of_head + ".png"
    way_to_weapon = "app/Images/Weapon" + number_of_weapon + ".png"
    weapon_image = Image.open(way_to_weapon)
    body_image = Image.open(way_to_body)
    head_image = Image.open(way_to_head)
    body_with_head_image = Image.alpha_composite(body_image, head_image)
    pet_image = Image.alpha_composite(body_with_head_image, weapon_image)
    white_background = Image.new("RGBA", (768, 768), (255, 255, 255))
    pet_image = Image.alpha_composite(white_background, pet_image)
    return pet_image


def CreateVersusImage(first_pet, second_pet):
    versus_image = Image.open("app/Images/Versus.png")
    white_background = Image.new("RGBA", (464, 768), (255, 255, 255))
    versus_image = Image.alpha_composite(white_background, versus_image)
    first_pet = ImageOps.mirror(first_pet)
    new_image = Image.new("RGBA", (2000, 768), (255, 255, 255))
    new_image.paste(first_pet, (0, 0))
    new_image.paste(versus_image, (768, 0))
    new_image.paste(second_pet, (1232, 0))
    return new_image


@bot.message_handler(commands=["customizePet"])
def CustomizePet(message: Message):
    cur_body = db.get_body_skin(message.from_user.id)
    cur_head = db.get_head_skin(message.from_user.id)
    cur_weapon = db.get_weapon_skin(message.from_user.id)

    pet_image = CreatePetImage(cur_body, cur_head, cur_weapon)
    bot.send_message(message.chat.id, "Ваш текущий персонаж:")
    bot.send_photo(message.chat.id, pet_image)
    markup_to_customize = MarkupFromList(["Голову", "Тело", "Оружие", "Отмена"])
    bot.send_message(message.chat.id, "Что вы хотите изменить?", reply_markup=markup_to_customize)
    states[message.from_user.id] = 'choose_part_to_change'


@bot.message_handler(func=lambda message: message.from_user.id in states and
                                          states[message.from_user.id] in [
                                              'choose_part_to_change',
                                              'change_head',
                                              'change_body',
                                              'change_weapon'
                                          ])
def Customizing(message: Message):
    current_state = str(states[message.from_user.id])
    cur_body = db.get_body_skin(message.from_user.id)
    cur_head = db.get_head_skin(message.from_user.id)
    cur_weapon = db.get_weapon_skin(message.from_user.id)
    available_heads = db.get_all_head_skins(message.from_user.id)
    available_bodies = db.get_all_body_skins(message.from_user.id)
    available_weapons = db.get_all_weapon_skins(message.from_user.id)

    match current_state:
        case "choose_part_to_change":
            match message.text:
                case "Голову":
                    markup_to_customize = MarkupFromList(available_heads + ["Отмена"])
                    bot.send_message(message.chat.id, "Текущая: " + cur_head + ". Доступные:",
                                     reply_markup=markup_to_customize)
                    states[message.from_user.id] = 'change_head'

                case "Тело":
                    markup_to_customize = MarkupFromList(available_bodies + ["Отмена"])
                    bot.send_message(message.chat.id, "Текущая: " + cur_body + ". Доступные:",
                                     reply_markup=markup_to_customize)
                    states[message.from_user.id] = 'change_body'

                case "Оружие":
                    markup_to_customize = MarkupFromList(available_weapons + ["Отмена"])
                    bot.send_message(message.chat.id, "Текущее: " + cur_weapon + ". Доступные:",
                                     reply_markup=markup_to_customize)
                    states[message.from_user.id] = 'change_weapon'

                case "Отмена":
                    bot.send_message(message.chat.id, "Хорошо, изменения отменены", reply_markup=ReplyKeyboardRemove())

        case 'change_head':
            cur_head = message.text
            if cur_head in available_heads:
                db.set_head_skin(message.from_user.id, cur_head)
                db.save()
                pet_image = CreatePetImage(cur_body, cur_head, cur_weapon)
                bot.send_message(message.chat.id, "Ваш новый персонаж:", reply_markup=ReplyKeyboardRemove())
                bot.send_photo(message.chat.id, pet_image)
            elif cur_head == "Отмена":
                bot.send_message(message.chat.id, "Хорошо, изменения отменены", reply_markup=ReplyKeyboardRemove())
            else:
                bot.send_message(message.chat.id, "Вам недоступен данный скин", reply_markup=ReplyKeyboardRemove())

        case 'change_body':
            cur_body = message.text
            if cur_body in available_bodies:
                db.set_body_skin(message.from_user.id, cur_body)
                db.save()
                pet_image = CreatePetImage(cur_body, cur_head, cur_weapon)
                bot.send_message(message.chat.id, "Ваш новый персонаж:", reply_markup=ReplyKeyboardRemove())
                bot.send_photo(message.chat.id, pet_image)
            elif cur_body == "Отмена":
                bot.send_message(message.chat.id, "Хорошо, изменения отменены", reply_markup=ReplyKeyboardRemove())
            else:
                bot.send_message(message.chat.id, "Вам недоступен данный скин", reply_markup=ReplyKeyboardRemove())

        case 'change_weapon':
            cur_weapon = message.text
            if cur_weapon in available_weapons:
                db.set_weapon_skin(message.from_user.id, cur_weapon)
                db.save()
                pet_image = CreatePetImage(cur_body, cur_head, cur_weapon)
                bot.send_message(message.chat.id, "Ваш новый персонаж:", reply_markup=ReplyKeyboardRemove())
                bot.send_photo(message.chat.id, pet_image)
            elif cur_weapon == "Отмена":
                bot.send_message(message.chat.id, "Хорошо, изменения отменены", reply_markup=ReplyKeyboardRemove())
            else:
                bot.send_message(message.chat.id, "Вам недоступен данный скин", reply_markup=ReplyKeyboardRemove())


# CustomizePet

def run_polling():
    print("Bot has been started...")
    bot.add_custom_filter(OpFilter())
    Thread(target=check_scheduler).start()
    try:
        bot.polling(skip_pending=True)

    except Exception as err:
        bot.send_message(771366061, text=f'Время: {datetime.now()}\n'
                                         f'Тип: {err.__class__}\n'
                                         f'Ошибка: {err}')
