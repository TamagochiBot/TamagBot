import os
import random
from datetime import datetime

import schedule
from threading import Thread
import time as tm

import telebot
from telebot import custom_filters
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, ReplyKeyboardRemove, CallbackQuery

from src.db.db_queries import DataBase

db = DataBase('testDB.db')

from src.app.player import Player

player_info = Player()

bot = telebot.TeleBot(os.environ["TOKEN"])

states = {}
types = {}
for_edit = {}
last_regular_event = db.count_rows("regular_event")

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
def InlineMarkupFromLists(listOfButtons,listOfCalls):
    markup = telebot.types.InlineKeyboardMarkup()
    for i in range(len(listOfCalls)):
        btn = telebot.types.InlineKeyboardButton(text=listOfButtons[i],callback_data=listOfCalls[i])
        markup.add(btn)
    return markup

# Создание KeyBoard кнопок
def MarkupFromList(listOfButtons):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for buttonName in listOfButtons:
        btn = telebot.types.KeyboardButton(buttonName)
        markup.add(btn)
    return markup

def notification_event(message: Message):
    table='event'
    id=message.from_user.id
    bot.send_message(message.chat.id,text=f'Ваш ивент:\n'
                                          f'{db.fetchone(table=table, id=id, column="event_name")}\n'
                                          f'Описание: {db.fetchone(table=table, id=id, column="description")}\n'
                                          f'Опыт: {db.fetchone(table=table, id=id, column="experience")}\n\n'
                                          f'Закончился!'
                     )
    db.delete_event(message.from_user.id)
    return schedule.CancelJob



@bot.message_handler(commands=['start'])
def start_message(message: Message):
    bot.send_message(message.chat.id, 'Привет, я ПопугБот!')
    bot.send_message(message.chat.id, 'Давай ка посмотрим, есть ли у тебя попуг 🦜')
    if db.exists(table='player', id=message.from_user.id):
        bot.send_message(message.chat.id, '''У тебя уже есть попуг)''')
    else:
        bot.send_message(message.chat.id, """Похоже, ты ещё не зарегестрирован, минуту...""")
        bot.send_message(message.chat.id, """Как будут звать твоего питомца?""")
        states[message.from_user.id]='registry'


# Регистрация в БД
@bot.message_handler(func=lambda message: message.from_user.id in states and
                                          states[message.from_user.id] =='registry')
def registration(message: Message):
    db.create_player(id=message.from_user.id, pet_name=message.text, user_name=message.from_user.first_name)
    bot.reply_to(message, "Вы успешно зарегестрированы!")
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

        db.delete_regular(id)
        bot.send_message(message.chat.id, "Готово")
        del states[message.from_user.id]
    except:
        bot.send_message(message.chat.id, "Не подходящий айди. Попробуй еще раз")


def describe_event(id: int, table: str) -> None:
    bot.send_message(id, text=f'\nИвент: {db.fetchone(table=table, id=id, column="event_name")}\n'
                              f'Описание: {db.fetchone(table=table, id=id, column="description")}\n'
                              f'Опыт: {db.fetchone(table=table, id=id, column="experience")}\n'
                              f'Дедлайн: {db.fetchone(table=table, id=id, column="deadline")}\n\n')


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
            types[message.from_user.id] = "unregular"
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

                        types[message.from_user.id] = "regular"
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
                        types[message.from_user.id] = "unregular"
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

def check_scheduler():
    while True:
        schedule.run_pending()
        tm.sleep(1)

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
                bot.send_message(message.chat.id, 'Укажите дедлайн в секундах')
                states[message.from_user.id] = 'event_deadline'
            else:
                bot.send_message(message.chat.id, 'Введите число')
                #states[message.from_user.id] = 'event_exp' нахера это делать?
        case 'event_deadline':
            db.update(table=table, column='deadline', id=user_id, data=message.text)
            db.save()
            #event_id = last_regular_event if table == "regular_event" else message.from_user.id
            #time = int(db.fetchone(table=table,id=event_id, column='deadline'))
            schedule.every(int(message.text)).seconds.do(notification_event,message=message).tag(message.from_user.id)
            bot.send_message(message.chat.id, text='Ивент успешно создан')
            del states[message.from_user.id]
        case _:
            bot.send_message(message.chat.id, 'LOL')


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
    my_id = int(message.from_user.id)
    op_id = int(db.get_player_id(message.text.split(" ", 1)[1][1:]))
    op_name = message.text.split(" ", 1)[1][1:]
    bot.send_message(message.chat.id, f'{message.text.split(" ", 1)[1]}, Вас вызвали на бой', reply_markup=kb)
    print(message.chat.id)


class OpFilter(custom_filters.AdvancedCustomFilter):
    key = 'set_op_id'

    def check(self, message, text):
        if isinstance(message, CallbackQuery):
            return message.message.from_user.id in text
        return message.from_user.id in text


@bot.callback_query_handler(func=lambda call: True)
def attack_user(call):

    print(my_id, op_id)
    print(call.message.text)

    if call.data == "accept":

        my_standard_damage = int(db.fetchone(table="player", column="strength", id=my_id))
        op_standard_damage = int(db.fetchone(table="player", column="strength", id=op_id))
        my_first_item_damage = db.get_item_stats(my_id, "item1")
        op_first_item_damage = db.get_item_stats(op_id, "item1")
        my_second_item_damage = db.get_item_stats(my_id, "item2")
        op_second_item_damage = db.get_item_stats(op_id, "item2")
        my_item_ability = db.get_item_mod(my_id, "item1")
        op_item_ability = db.get_item_mod(op_id, "item1")
        my_helmet_hp = db.get_item_stats(my_id, "helmet")
        op_helmet_hp = db.get_item_stats(op_id, "helmet")
        my_helmet_ability = db.get_item_mod(my_id, "helmet")
        op_helmet_ability = db.get_item_mod(op_id, "helmet")
        my_chest_plate_armor = db.get_item_stats(my_id, "chestplate")
        op_chest_plate_armor = db.get_item_stats(op_id, "chestplate")
        my_chest_plate_ability = db.get_item_mod(my_id, "chestplate")
        op_chest_plate_ability = db.get_item_mod(op_id, "chestplate")

        if my_helmet_ability == "Госстандарт":
            my_hp = int(int(db.fetchone(table="player", column="health", id=my_id)) * 1.05) + my_helmet_hp
        else:
            my_hp = int(db.fetchone(table="player", column="health", id=my_id)) + my_helmet_hp
        if op_helmet_ability == "Госстандарт":
            op_hp = int(int(db.fetchone(table="player", column="health", id=op_id)) * 1.05) + op_helmet_hp
        else:
            op_hp = int(db.fetchone(table="player", column="health", id=op_id)) + op_helmet_hp

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

                bot.send_message(my_id, f'Атакует - {db.fetchone("player", my_id, "pet_name")} \n' +
                                        f'Моды, использованные в раунде: {mods_attack_list} \n' +
                                        f'Всего урона с модификаторами: {sum_damage} \n' +
                                        f'Защищается - {db.fetchone("player", op_id, "pet_name")} \n' +
                                        f'Моды, использованные в раунде: {mods_defend_list} \n' +
                                        f'Всего получено урона: {last_hp - op_hp}')

                bot.send_message(op_id, f'Атакует - {db.fetchone("player", my_id, "pet_name")} \n' +
                                        f'Моды, использованные в раунде: {mods_attack_list} \n' +
                                        f'Всего урона с модификаторами: {sum_damage} \n' +
                                        f'Защищается - {db.fetchone("player", op_id, "pet_name")} \n' +
                                        f'Моды, использованные в раунде: {mods_defend_list} \n' +
                                        f'Всего получено урона: {last_hp - op_hp}')
                attacker = "opponent"

            else:
                op_turn += 1
                sum_damage += op_standard_damage

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

                bot.send_message(my_id, f'Атакует - {db.fetchone("player", op_id, "pet_name")} \n' +
                                 f'Моды, использованные в раунде: {mods_attack_list} \n' +
                                 f'Всего урона с модификаторами: {sum_damage} \n' +
                                 f'Защищается - {db.fetchone("player", my_id, "pet_name")} \n' +
                                 f'Моды, использованные в раунде: {mods_defend_list} \n' +
                                 f'Всего получено урона: {last_hp - my_hp}')

                bot.send_message(op_id, f'Атакует - {db.fetchone("player", op_id, "pet_name")} \n' +
                                 f'Моды, использованные в раунде: {mods_attack_list} \n' +
                                 f'Всего урона с модификаторами: {sum_damage} \n' +
                                 f'Защищается - {db.fetchone("player", my_id, "pet_name")} \n' +
                                 f'Моды, использованные в раунде: {mods_defend_list} \n' +
                                 f'Всего получено урона: {last_hp - my_hp}')

                attacker = "me"

        if my_hp <= 0:
            stolen_cookies = int(random.random() * db.fetchone("player", my_id, "balance") / 5)
            bot.send_message(my_id, f'Победитель - {db.fetchone("player", op_id, "pet_name")} \n'
                             f'он крадет у {db.fetchone("player", my_id, "pet_name")} {stolen_cookies} \n')
            bot.send_message(op_id, f'Победитель - {db.fetchone("player", op_id, "pet_name")} \n'
                             f'он крадет у {db.fetchone("player", my_id, "pet_name")} {stolen_cookies} \n')
        else:
            stolen_cookies = int(random.random() * db.fetchone("player", op_id, "balance") / 5)
            bot.send_message(my_id, f'Победитель - {db.fetchone("player", my_id, "pet_name")} \n'
                             f'он крадет у {db.fetchone("player", op_id, "pet_name")} {stolen_cookies} \n')
            bot.send_message(op_id, f'Победитель - {db.fetchone("player", op_id, "pet_name")} \n'
                             f'он крадет у {db.fetchone("player", op_id, "pet_name")} {stolen_cookies} \n')

    elif call.data == "cancel":
        bot.edit_message_text(chat_id=call.message.chat.id,
                              message_id=call.message.message_id, text="Бой отклонен")

# БОИ


def run_polling():
    print("Bot has been started...")
    bot.add_custom_filter(OpFilter())
    Thread(target=check_scheduler).start()
    # try:
    bot.polling(skip_pending=True)

    # except Exception as err:
    #     bot.send_message(771366061, text=f'Время: {datetime.datetime.now()}\n'
    #                                      f'Тип: {err.__class__}\n'
    #                                      f'Ошибка: {err}')