import telebot
from telebot import types
from dotenv import load_dotenv
import os
import sqlite3
import random
import string

# загружаем TOKEN из виртуального окружения
load_dotenv()
TOKEN = os.getenv('TOKEN')

ACTIVE_CLASS = ''
SHEDULE_ID = 0

# инициализируем класс TeleBot
bot = telebot.TeleBot(TOKEN)


class SQLighter:
    def __init__(self, user_id):
        self.database = 'db.db'
        self.con = sqlite3.connect(self.database)
        self.cursor = self.con.cursor()
        self.user_id = user_id

    def add_class(self, key, name):
        result_of_execute = self.cursor.execute(f'SELECT * FROM classes WHERE key = {key}').fetchall()
        if result_of_execute:
            return False
        sqlite_insert_query = f"""INSERT INTO classes (key, name)  VALUES  ({key}, '{name}')"""
        self.cursor.execute(sqlite_insert_query)
        self.con.commit()

    def add_admin(self, key):
        result_of_execute = self.cursor.execute(f'SELECT id FROM classes WHERE key'
                                                f' = {key}').fetchall()
        if not result_of_execute:
            return False
        sqlite_insert_query = f"""INSERT INTO admins (class_id, admin)  VALUES
          ({result_of_execute[0][0]}, {self.user_id})"""
        self.cursor.execute(sqlite_insert_query)
        self.con.commit()

    def add_user_to_class(self, key):
        class_id = self.cursor.execute(f'SELECT id FROM classes WHERE key'
                                       f' = {key}').fetchall()
        if_user_in_class = self.cursor.execute(f'SELECT * FROM users_in_classes WHERE user_id'
                                               f' = {self.user_id} AND class_id = {class_id[0][0]}').fetchall()
        if not class_id or if_user_in_class:
            return
        else:
            sqlite_insert_query = f"""INSERT INTO users_in_classes (user_id, class_id)  VALUES
                      ({self.user_id}, {class_id[0][0]})"""
            self.cursor.execute(sqlite_insert_query)
            self.con.commit()

    def search_class(self, key):
        result_of_execute = self.cursor.execute(f'SELECT name FROM classes WHERE key'
                                                f' = {key}').fetchall()
        if not result_of_execute:
            return False
        else:
            return result_of_execute[0][0]

    def search_user_classes(self):
        result_of_execute = self.cursor.execute(f'SELECT name FROM classes INNER JOIN users_in_classes'
                                                f' ON id = class_id WHERE user_id = {self.user_id}').fetchall()
        if not result_of_execute:
            return False
        else:
            return result_of_execute

    def search_users_in_class(self, key):
        global ACTIVE_CLASS
        class_id_from_active = self.cursor.execute(f'SELECT id FROM classes WHERE key = {ACTIVE_CLASS}').fetchone()
        result_of_execute = self.cursor.execute(
            f'SELECT user_id FROM users_in_classes WHERE class_id = {class_id_from_active[0]}').fetchone()
        if not result_of_execute:
            return False
        else:
            return result_of_execute

    def create_new_admin(self, new_admins):
        global ACTIVE_CLASS
        result_of_execute = self.cursor.execute(f'SELECT id FROM classes WHERE key = {ACTIVE_CLASS}').fetchone()
        # class_id_from_active = self.cursor.execute(f"""INSERT INTO admins (class_id, admin)  VALUES
        #                          ({result_of_execute[0]}, {new_admins})""")  # operation must be str ( fix - later )
        # self.cursor.execute(class_id_from_active)
        # self.con.commit()

        if not result_of_execute:
            return False
        else:
            return result_of_execute

    def search_shedule(self, key):
        result_of_execute = self.cursor.execute(f'SELECT * FROM shedule'
                                                f' WHERE id = (SELECT shedule_id FROM'
                                                f' classes_info WHERE class_id = {key})').fetchall()
        if not result_of_execute:
            return False
        else:
            return result_of_execute

    def search_shedule_for_day(self, shedule_id, day):
        result_of_execute = self.cursor.execute(f'SELECT {day} FROM shedule WHERE '
                                                f'id = {shedule_id}').fetchall()
        if not result_of_execute:
            return False
        else:
            return result_of_execute


# команда /start
@bot.message_handler(commands=['start', 'help'])
def start_message(message):
    # получаем имя user и здороваемся с ним
    user_first_name = str(message.chat.first_name)
    buttons = ['👩‍🏫Создать класс', '👨‍🎓Найти класс', '❓Сообщить об ошибке', 'Ваши классы', 'Получить id']
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for button in buttons:
        markup.add(button)
    bot.send_message(message.chat.id, f'Привет, {user_first_name}!\nТебя приветствует SchoolBot,'
                                      f' пользуйся ботом с помощью команд снизу👇', reply_markup=markup)


@bot.message_handler(content_types=['text'])
def buttons(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if message.text == '❓Сообщить об ошибке':
        markup.add('✅Назад в главную')
        bot.send_message(message.chat.id, text='Если вы столкнулись с ошибкой напишите'
                                               ' админам: @Maxb0t или @kirmiq.', reply_markup=markup)
    elif message.text == '👨‍🎓Найти класс':
        markup.add('✅Назад в главную')
        sent = bot.send_message(message.chat.id, text='Введите id класса(6-значный ключ из цифр):',
                                reply_markup=markup)
        bot.register_next_step_handler(sent, search_class)
    elif message.text == '👩‍🏫Создать класс':
        markup.add('✅Назад в главную')
        sent = bot.send_message(message.chat.id, 'Введите название класса:', reply_markup=markup)
        bot.register_next_step_handler(sent, create_class)
    elif message.text == 'Ваши классы':
        list_of_classes(message)
    elif message.text == 'Объявление':
        markup.add('✅Назад в главную')
        sent = bot.send_message(message.chat.id, 'Введите объявление:', reply_markup=markup)
        bot.register_next_step_handler(sent, make_ad)
    elif message.text == 'Расписание':
        shedule(message)
    elif message.text == '✅Назад в главную':
        start_message(message)
    elif message.text == 'Получить id':
        bot.send_message(message.chat.id, f'{message.chat.id}')
    elif message.text == 'Настройки':
        settings(message)
    elif message.text == 'Добавить админа':
        sent = bot.send_message(message.chat.id, 'Введите id пользователя:', reply_markup=markup)
        bot.register_next_step_handler(sent, new_admin)
    elif message.text == 'Назад':
        shedule(message)
    else:
        bot.send_message(message.chat.id, text='Что-то на человеческом, я вас не понимаю😥')


def create_class(message):
    global ACTIVE_CLASS
    try:
        if message.text == '✅Назад в главную':
            return start_message(message)
        creating_key = True
        key = ''
        sqlighter = SQLighter(message.from_user.id)
        while creating_key:
            key = ''.join(random.choice(string.digits) for _ in range(6))
            if key[0] != '0':
                if not sqlighter.add_class(key, message.text):
                    creating_key = False
        sqlighter.add_admin(key)
        sqlighter.add_user_to_class(key)
        ACTIVE_CLASS = key
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ['Расписание', 'ДЗ', 'Настройки', 'Объявление', '✅Назад в главную']
        markup.add(*buttons)
        bot.send_message(message.chat.id, f'Класс был успешно создан. Ваш ключ:\n{key}',
                         reply_markup=markup)
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, '❌Ошибка! Не удалось создать класс')


def search_class(message):
    global ACTIVE_CLASS
    try:
        key = message.text
        sqlither = SQLighter(message.from_user.id)
        name = sqlither.search_class(key)
        if not name:
            raise Exception
        sqlither.add_user_to_class(key)
        ACTIVE_CLASS = key
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ['Расписание', 'ДЗ', '✅Назад в главную']
        markup.add(*buttons)
        bot.send_message(message.chat.id, f'Вы успешно перешли в "{name}"',
                         reply_markup=markup)
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, '❌Ошибка! Не удалось найти класс')


def make_ad(message):
    global ACTIVE_CLASS
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('✅Назад в главную')
    try:
        sqlighter = SQLighter(message.from_user.id)
        ids = sqlighter.search_users_in_class(ACTIVE_CLASS)
        bot.send_message(ids[0], message.text)
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, '❌Ошибка! Не удалось сделать объявление')


# need fix
def new_admin(message):
    global ACTIVE_CLASS
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('✅Назад в главную')
    try:
        new_admins = message.from_user.id
        sqlighter = SQLighter(message.from_user.id)
        sqlighter.create_new_admin(ACTIVE_CLASS)
        bot.send_message(message.chat.id, 'Админ успешно не добавлен, нужен фикс')
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, '❌Ошибка! Не удалось добавить админа')


def settings(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ['Добавить админа']
    for button in buttons:
        markup.add(button)
    bot.send_message(message.chat.id, 'Вы перешли в настроки', reply_markup=markup)
    markup.add('✅Назад в главную')


def list_of_classes(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    try:
        sqlighter = SQLighter(message.from_user.id)
        classes = sqlighter.search_user_classes()
        if not classes:
            raise Exception
        else:
            klass = []
            for clas in classes:
                klass.append(f'"{clas[0]}"')
            markup.add(*klass)
            markup.add('✅Назад в главную')
            bot.send_message(message.chat.id, f'На данный момент вы состоите в классах: {", ".join(klass)}.',
                             reply_markup=markup)
    except Exception as e:
        print(e)
        markup.add('✅Назад в главную')
        bot.send_message(message.chat.id, 'К сожалению, вы не состоите не в одном классе',
                         reply_markup=markup)


def shedule(message):
    global SHEDULE_ID
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    try:
        sqlighter = SQLighter(message.from_user.id)
        shedule = sqlighter.search_shedule(ACTIVE_CLASS)
        if shedule:
            buttons = ['Понедельник', 'Вторник', 'Среда', 'Четверг',
                       'Пятница', 'Суббота', 'Изменить расписание']
            markup.add(*buttons)
            markup.add('✅Назад в главную')
            sent = bot.send_message(message.chat.id, 'Выберете день:', reply_markup=markup)
            SHEDULE_ID = shedule[0][0]
            bot.register_next_step_handler(sent, send_shedule)
        else:
            markup.add('Добавить расписание')
            pass
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, 'Расписание не добавлено',
                         reply_markup=markup)


def send_shedule(message):
    global SHEDULE_ID
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('Назад')
    markup.add('✅Назад в главную')
    sqlighter = SQLighter(message.from_user.id)
    if message.text == 'Понедельник':
        day = sqlighter.search_shedule_for_day(SHEDULE_ID, 'monday')
        bot.send_message(message.chat.id, day, reply_markup=markup)
    elif message.text == 'Вторник':
        day = sqlighter.search_shedule_for_day(SHEDULE_ID, 'tuesday')
        bot.send_message(message.chat.id, day, reply_markup=markup)
    elif message.text == 'Среда':
        day = sqlighter.search_shedule_for_day(SHEDULE_ID, 'wednesday')
        bot.send_message(message.chat.id, day, reply_markup=markup)
    elif message.text == 'Четверг':
        day = sqlighter.search_shedule_for_day(SHEDULE_ID, 'thursday')
        bot.send_message(message.chat.id, day, reply_markup=markup)
    elif message.text == 'Пятница':
        day = sqlighter.search_shedule_for_day(SHEDULE_ID, 'friday')
        bot.send_message(message.chat.id, day, reply_markup=markup)
    elif message.text == 'Суббота':
        day = sqlighter.search_shedule_for_day(SHEDULE_ID, 'saturday')
        bot.send_message(message.chat.id, day, reply_markup=markup)
    else:
        bot.send_message(message.chat.id, 'Такого дня нет в вашем расписании!')


# запускаем бота
if __name__ == '__main__':
    print('Bot is working...')
    bot.infinity_polling()
