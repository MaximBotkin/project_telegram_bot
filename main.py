#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

# постоянная переменная, отвечающая за активный класс
ACTIVE_CLASS = ''
# постоянная переменная, отвечающая за id расписания
SHEDULE_ID = 0

# инициализируем класс TeleBot
bot = telebot.TeleBot(TOKEN)


# глобальный класс с функциями, отвечающими за работу с БД
class SQLighter:
    global ACTIVE_CLASS, SHEDULE_ID

    # подключение к БД
    def __init__(self, user_id):
        self.database = 'db.db'
        self.con = sqlite3.connect(self.database)
        self.cursor = self.con.cursor()
        self.user_id = user_id

    # добавляем класс и его название в БД
    def add_class(self, key, name):
        # проверка на уже существующий класс
        result_of_execute = self.cursor.execute(f'SELECT * FROM classes WHERE key = {key}').fetchall()
        if result_of_execute:
            return False
        # внесение в БД информации о новом классе
        sqlite_insert_query = f"""INSERT INTO classes (key, name)  VALUES  ({key}, '{name}')"""
        self.cursor.execute(sqlite_insert_query)
        self.con.commit()

    # добавляем админа
    def add_admin(self, key):
        # проверка на существование класса
        result_of_execute = self.cursor.execute(f'SELECT id FROM classes WHERE key'
                                                f' = {key}').fetchall()
        if not result_of_execute:
            return False
        # внесение в БД информации о админе
        sqlite_insert_query = f"""INSERT INTO admins (class_id, admin)  VALUES
          ({result_of_execute[0][0]}, {self.user_id})"""
        self.cursor.execute(sqlite_insert_query)
        self.con.commit()

    # добавляем учеников в класс
    def add_user_to_class(self, key):
        # находим нужный id класса
        class_id = self.cursor.execute(f'SELECT id FROM classes WHERE key'
                                       f' = {key}').fetchall()
        # проверка, есть ли ученик в классе
        if_user_in_class = self.cursor.execute(f'SELECT * FROM users_in_classes WHERE user_id'
                                               f' = {self.user_id} AND class_id = {class_id[0][0]}').fetchall()

        if not class_id or if_user_in_class:
            return
        else:
            # внесение в БД информации об ученике
            sqlite_insert_query = f"""INSERT INTO users_in_classes (user_id, class_id)  VALUES
                              ({self.user_id}, {class_id[0][0]})"""
            self.cursor.execute(sqlite_insert_query)
            self.con.commit()

    # поиск класса
    def search_class(self, key):
        # получание из БД названия класса
        result_of_execute = self.cursor.execute(f'SELECT name FROM classes WHERE key'
                                                f' = {key}').fetchall()
        return result_of_execute[0][0] if result_of_execute else False

    # поиск id в классе
    def search_id_class(self, key):
        # получение из БД id
        result_of_execute = self.cursor.execute(f'SELECT id FROM classes WHERE key'
                                                f' = {key}').fetchall()
        return result_of_execute[0][0] if result_of_execute else False

    # поиск учеников в классе
    def search_user_classes(self):
        # получение из БД информации о учениках
        result_of_execute = self.cursor.execute(f'SELECT name, key FROM classes INNER JOIN users_in_classes'
                                                f' ON id = class_id WHERE user_id = {self.user_id}').fetchall()
        return result_of_execute if result_of_execute else False

    # проверка на наличие прав администратора в классе
    def user_is_admin(self, key):
        # сверка информации об админе
        result_of_execute = self.cursor.execute(f'SELECT * FROM admins INNER JOIN classes'
                                                f' ON class_id = id WHERE admin = {self.user_id}'
                                                f' AND key = {key}').fetchall()
        return True if result_of_execute else False

    # поиск пользователей в определенном классе
    def search_users_in_class(self, key):
        # сверка информации об учениках
        result_of_execute = self.cursor.execute(
            f'SELECT user_id FROM users_in_classes WHERE class_id ='
            f' (SELECT id FROM classes WHERE key = {key})').fetchall()
        return result_of_execute if result_of_execute else False

    # добавление нового админа в определенный класс
    def create_new_admin(self, new_admins):
        global ACTIVE_CLASS
        # выбор класса, в который нужно добавить админа
        class_id_from_active = self.cursor.execute(f'SELECT id FROM classes WHERE key = {ACTIVE_CLASS}').fetchone()
        # добавление информации о новом админе в определенный класс
        result_of_execute = f'INSERT INTO admins (class_id, admin)  VALUES({class_id_from_active[0]}, {new_admins});'
        self.cursor.execute(result_of_execute)
        self.con.commit()
        return result_of_execute if result_of_execute else False

    def add_shedule(self, key):
        # добавляем новое расписание
        class_id = self.search_id_class(key)
        sqlite_insert_query = f"""INSERT INTO shedule (class_id) VALUES ({class_id})"""
        self.cursor.execute(sqlite_insert_query)
        self.con.commit()

    def add_shedule_on_day(self, day, text):
        # добавляем расписание на определённый день
        class_id = self.search_id_class(ACTIVE_CLASS)
        sqlite_insert_query = f"""UPDATE shedule SET {day} = '{text}' WHERE class_id = {class_id}"""
        self.cursor.execute(sqlite_insert_query)
        self.con.commit()

    def search_shedule(self, key):
        # ищем расписание класса
        result_of_execute = self.cursor.execute(f'SELECT * FROM shedule'
                                                f' WHERE class_id = (SELECT id FROM'
                                                f' classes WHERE key = {key})').fetchall()
        return result_of_execute if result_of_execute else False

    def search_shedule_for_day(self, shedule_id, day):
        # ищем расписание на определённый день
        result_of_execute = self.cursor.execute(f'SELECT {day} FROM shedule WHERE '
                                                f'id = {shedule_id}').fetchall()
        return result_of_execute if result_of_execute else False

    # добавление домашнего задания для учеников
    def create_new_homework(self, key, date, homeworks):
        class_id = self.search_id_class(ACTIVE_CLASS)
        # внесение информации в БД о классе, домашнем задании и его дате
        sqlite_insert_query = f"""INSERT INTO homework (id, date, homework, class_id) VALUES  ({key}, {date}, '{homeworks}', {class_id})"""
        self.cursor.execute(sqlite_insert_query)
        self.con.commit()


# команда /start
@bot.message_handler(commands=['start', 'help'])
def start_message(message):
    # получаем имя user и здороваемся с ним
    user_first_name = str(message.chat.first_name)
    # создаём список с нужными для нас кнопками
    buttons = ['👩‍🏫Создать класс', '👨‍🎓Найти класс', '❓Сообщить об ошибке', '🎓Ваши классы', '🆔Получить id']
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # добавление кнопок из списка на главный экран
    for button in buttons:
        markup.add(button)
    # отправляем сообщения пользователю, который написал команду /start
    bot.send_message(message.chat.id, f'Привет, {user_first_name}!\nТебя приветствует SchoolBot,'
                                      f' пользуйся ботом с помощью команд снизу👇.', reply_markup=markup)


@bot.message_handler(content_types=['text'])
def buttons(message):
    global ACTIVE_CLASS, SHEDULE_ID
    # подключение к БД
    sqlighter = SQLighter(message.from_user.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # Вызов ответов от бота, на полученные сообщения.
    # Бот либо отправляет соответствующее сообщение методом bot.send_message,
    # Либо перенаправляет нас на другие функции,
    # Либо в случае необходимости вводить данные вручную, в зависимости от функций,
    # бот будет ждать от пользователя ввода конкретных данных от пользователя методом bot.register_next_step_handler
    if message.text == '❓Сообщить об ошибке':
        markup.add('✅Назад в главную')
        bot.send_message(message.chat.id, text='Если вы столкнулись с ошибкой, напишите'
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
    elif message.text == '🎓Ваши классы':
        list_of_classes(message)
    elif message.text == '📝Объявление':
        markup.add('❌Назад')
        sent = bot.send_message(message.chat.id, 'Введите объявление:', reply_markup=markup)
        bot.register_next_step_handler(sent, make_ad)
    elif message.text == '📒ДЗ':
        homework(message)
    elif message.text == '✍Добавить ДЗ':
        sent = bot.send_message(message.chat.id, 'Напишите ДЗ в формате ДД.ММ и домашнее задание.')
        bot.register_next_step_handler(sent, add_homework)
    elif message.text == '📓Расписание':
        shedule(message)
    elif message.text == '🚫Назад':
        search_class(message, ACTIVE_CLASS)
    elif message.text == '❌Назад':
        shedule(message)
    elif message.text == '✅Назад в главную':
        start_message(message)
    elif message.text == '🆔Получить id':
        bot.send_message(message.chat.id, f'Ваш id: {message.chat.id}')
    elif message.text == '⚙Настройки':
        settings(message)
    elif message.text == '👨🏻‍🏫Добавить админа':
        sent = bot.send_message(message.chat.id, 'Введите id пользователя '
                                                 '(человек может получить id по кнопке в главном меню):',
                                reply_markup=markup)
        bot.register_next_step_handler(sent, new_admin)
    elif message.text == '📖Добавить расписание':
        # внутренний цикл, для того, что бы админ смог добавить расписание
        if not sqlighter.search_shedule(ACTIVE_CLASS):
            sqlighter.add_shedule(ACTIVE_CLASS)
            buttons = ['Понедельник', 'Вторник', 'Среда', 'Четверг',
                       'Пятница', 'Суббота', '✅Назад в главную']
            markup.add(*buttons)
            sent = bot.send_message(message.chat.id, 'Выберете день:', reply_markup=markup)
            bot.register_next_step_handler(sent, add_shedule)
        else:
            bot.send_message(message.chat.id, 'Расписание уже добавлено.')
    elif message.text == '✍🏻Изменить расписание':
        shedule(message)
    elif '/' in message.text and len(message.text.split('/')[-1]) == 6:
        key = message.text.split('/')[-1]
        search_class(message, key)
    else:
        bot.send_message(message.chat.id, text='Что-то на человеческом, я вас не понимаю😥.')


# возвращение в меню основных функций админа
def back(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # создание списка необходимых кнопок
    buttons = ['📓Расписание', '📒ДЗ', '⚙Настройки',
               '📝Объявление', '✅Назад в главную']
    # вывод кнопок на экран
    markup.add(*buttons)
    bot.send_message(message.chat.id, text='👀Вы вернулись назад', reply_markup=markup)


# создание класса по вызову от нажатой кнопки
def create_class(message):
    global ACTIVE_CLASS
    try:
        # Выход из функции при необходимости вернуться на главную
        if message.text == '✅Назад в главную':
            return start_message(message)
        # создание уникального ключа
        creating_key = True
        # начальное значение ключа
        key = ''
        # подключение к БД
        sqlighter = SQLighter(message.from_user.id)
        # генерация случайного ключа
        while creating_key:
            # добавление случайных значений в ключ
            key = ''.join(random.choice(string.digits) for _ in range(6))
            # проверка уникальности ключа
            if key[0] != '0':
                if not sqlighter.add_class(key, message.text):
                    creating_key = False
        # присваеваем постоянной переменной ACTIVE_CLASS значение ключа
        ACTIVE_CLASS = key
        # добавление админа в класс по его ключу
        sqlighter.add_admin(key)
        # добавление пользователя в класс по его ключу
        sqlighter.add_user_to_class(key)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        # создание списка необходимых кнопок
        buttons = ['📓Расписание', '📒ДЗ', '⚙Настройки',
                   '📝Объявление', '✅Назад в главную']
        # добавление кнопок на экран
        markup.add(*buttons)
        bot.send_message(message.chat.id, f'Класс был успешно создан. Ваш ключ:\n{key}',
                         reply_markup=markup)
    # вывод сообщения об ошибке в случае некоррекного ввода данных / неверного вызова
    except Exception as e:
        bot.send_message(message.chat.id, '❌Ошибка! Не удалось создать класс.')


# поиск уже существующего класса по вызову функции
def search_class(message, key=None):
    global ACTIVE_CLASS
    # Выход из функции при необходимости вернуться на главную
    if message.text == '✅Назад в главную':
        return start_message(message)
    try:
        # проверка ключа
        if key:
            key = key
        else:
            # присваивание ключую значения введенного пользователем
            key = message.text
        # подключение к БД
        sqlither = SQLighter(message.from_user.id)
        # поиск класса по ключу введенному пользователем
        name = sqlither.search_class(key)
        # в случае, если такого класса не существует вывод Exception
        if not name:
            raise Exception
        # проверка, является ли пользователь админом
        if sqlither.user_is_admin(key):
            # в случае если пользователь админ, предоставление функций администратора
            sqlither.add_user_to_class(key)
            ACTIVE_CLASS = key
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            # создание списка необходимых кнопок
            buttons = ['📓Расписание', '📒ДЗ', '⚙Настройки',
                       '📝Объявление', '✅Назад в главную']
            # вывод кнопок на экран
            markup.add(*buttons)
            bot.send_message(message.chat.id, f'Вы успешно перешли в "{name}"',
                             reply_markup=markup)
        else:
            # если пользователь не является админом, предоставление ему функционала ученика
            sqlither.add_user_to_class(key)
            ACTIVE_CLASS = key
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            # создание списка необходимых кнопок
            buttons = ['📓Расписание', '📒ДЗ', '✅Назад в главную']
            # вывод кнопок на экран
            markup.add(*buttons)
            bot.send_message(message.chat.id, f'Вы успешно перешли в "{name}".',
                             reply_markup=markup)
    # вывод сообщения об ошибке в случае некоррекного ввода данных / неверного вызова
    except Exception as e:
        bot.send_message(message.chat.id, '❌Ошибка! Не удалось найти класс.')


# создание объявления от администратора для учеников
def make_ad(message):
    global ACTIVE_CLASS
    # возвращение к функциям в случае необходимости
    if message.text == '❌Назад':
        return back(message)
    # подключение к БД
    sqlighter = SQLighter(message.from_user.id)
    # получение id пользователей состоящих в классе
    ids = sqlighter.search_users_in_class(ACTIVE_CLASS)
    # рассылка объявлений каждому ученику, состоящему в классе
    for id in ids:
        if id[0] != message.from_user.id:
            bot.send_message(id[0], f'Объявление! {message.text}')
        else:
            bot.send_message(message.chat.id, text='Объявление успешно отправлено.')
            # после выполнения рассылки возвращение на предыдущий экран
            back(message)


# добавление нового администратора в класс
def new_admin(message):
    global ACTIVE_CLASS
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('✅Назад в главную')
    # возвращение к главному меню в случае необходимости
    if message.text == '✅Назад в главную':
        return start_message(message)
    # возвращение к функциям в случае необходимости
    elif message.text == '🚫Назад':
        return search_class(message, ACTIVE_CLASS)
    try:
        # получение id пользователя, которого хотим назначить админом
        new_admins = message.text
        # подключение к БД
        sqlighter = SQLighter(message.from_user.id)
        # создание в БД новго админа согласно внесенным данным пользователя
        sqlighter.create_new_admin(new_admins)
        bot.send_message(message.chat.id, 'Админ успешно добавлен')
    # вывод сообщения об ошибке в случае некоррекного ввода данных / неверного вызова
    except Exception as e:
        bot.send_message(message.chat.id, '❌Ошибка! Не удалось добавить админа.')


# настройки администратора
def settings(message):
    try:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        # возможные настройки администратора
        buttons = ['👨🏻‍🏫Добавить админа', '🚫Назад', '✅Назад в главную']
        # вывод кнопок из списка
        markup.add(*buttons)
        bot.send_message(message.chat.id, 'Вы перешли в настройки.', reply_markup=markup)
    # вывод сообщения об ошибке в случае некоррекного ввода данных / неверного вызова
    except Exception as e:
        bot.send_message(message.chat.id, 'Не удалось перейти в настройки.')


# вывод классов к которых состоит пользователь
def list_of_classes(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    try:
        # подключение к БД
        sqlighter = SQLighter(message.from_user.id)
        # поиск пользователей в классе
        classes = sqlighter.search_user_classes()
        if not classes:
            # вывод сообщения об ошибке в случае некоррекного ввода данных / неверного вызова
            raise Exception
        else:
            # создание списка, в котором будут храниться кнопки классы
            klass = []
            # создание списка, где будут перечислены классы, в которых состоит пользователь
            class_to_send = []
            # перебор каждого класса
            for clas in classes:
                klass.append(f'{clas[0]}/{clas[1]}')
                class_to_send.append(f'{clas[0]}')
            markup.add(*klass)
            markup.add('✅Назад в главную')
            bot.send_message(message.chat.id, f'На данный момент вы состоите в классах: {", ".join(class_to_send)}.',
                             reply_markup=markup)
    # вывод сообщения об ошибке в случае некоррекного ввода данных / неверного вызова
    except Exception as e:
        markup.add('✅Назад в главную')
        bot.send_message(message.chat.id, 'К сожалению, вы не состоите не в одном классе.',
                         reply_markup=markup)


# функция расписания
def shedule(message):
    global ACTIVE_CLASS, SHEDULE_ID
    try:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        sqlighter = SQLighter(message.from_user.id)
        # ищем расписание
        shedule = sqlighter.search_shedule(ACTIVE_CLASS)
        # если есть, добавляем кнопки дней
        if shedule:
            buttons = ['Понедельник', 'Вторник', 'Среда', 'Четверг',
                       'Пятница', 'Суббота', '🚫Назад', '✅Назад в главную']
            if sqlighter.user_is_admin(ACTIVE_CLASS):
                markup.add('✍🏻Изменить расписание')
            markup.add(*buttons)
            # даем выбор дня пользователя
            sent = bot.send_message(message.chat.id, 'Выберете день:', reply_markup=markup)
            SHEDULE_ID = shedule[0][0]
            bot.register_next_step_handler(sent, send_shedule)
        else:
            # иначе предлагаем добавить новое расписание
            buttons1 = ['📖Добавить расписание', '🚫Назад']
            markup.add(*buttons1)
            # и присылаем сообщение
            bot.send_message(message.chat.id, 'На данный момент расписание не добавлено.',
                             reply_markup=markup)
    except Exception as e:
        # в случае ошибки выводим пользователю следующий текст
        bot.send_message(message.chat.id, 'Не удалось найти расписание.')


# функция отправки расписания
def send_shedule(message):
    global ACTIVE_CLASS, SHEDULE_ID
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # если нажата кнопка изменения расписания, предлагаем какой день изменить
    if message.text == '✍🏻Изменить расписание':
        buttons = ['Понедельник', 'Вторник', 'Среда', 'Четверг',
                   'Пятница', 'Суббота', '🚫Назад']
        markup.add(*buttons)
        markup.add('✅Назад в главную')
        sent = bot.send_message(message.chat.id, 'Выберете день:', reply_markup=markup)
        return bot.register_next_step_handler(sent, add_shedule)
    if message.text == '🚫Назад':
        return search_class(message, ACTIVE_CLASS)
    elif message.text == '✅Назад в главную':
        return start_message(message)
    markup.add('❌Назад')
    markup.add('✅Назад в главную')
    sqlighter = SQLighter(message.from_user.id)
    # выводим расписание на разные дни
    if message.text == 'Понедельник':
        day = sqlighter.search_shedule_for_day(SHEDULE_ID, 'monday')
        if day[0][0] is None:
            bot.send_message(message.chat.id, 'На этот день расписание не добавлено.'
                                              ' Добавьте его с помощью кнопки "✍🏻Изменить расписание".',
                             reply_markup=markup)
        else:
            # выводим на новой строке с номером урока в начале
            diary, digit = '', 1
            for subject in day[0][0].split():
                sub = diary
                diary = sub + '\n' + str(digit) + '. ' + subject
                digit += 1
            bot.send_message(message.chat.id, diary, reply_markup=markup)
    elif message.text == 'Вторник':
        day = sqlighter.search_shedule_for_day(SHEDULE_ID, 'tuesday')
        if day[0][0] is None:
            bot.send_message(message.chat.id, 'На этот день расписание не добавлено.'
                                              ' Добавьте его с помощью кнопки "✍🏻Изменить расписание".',
                             reply_markup=markup)
        else:
            diary, digit = '', 1
            for subject in day[0][0].split():
                sub = diary
                diary = sub + '\n' + str(digit) + '. ' + subject
                digit += 1
            bot.send_message(message.chat.id, diary, reply_markup=markup)
    elif message.text == 'Среда':
        day = sqlighter.search_shedule_for_day(SHEDULE_ID, 'wednesday')
        if day[0][0] is None:
            bot.send_message(message.chat.id, 'На этот день расписание не добавлено.'
                                              ' Добавьте его с помощью кнопки "✍🏻Изменить расписание".',
                             reply_markup=markup)
        else:
            diary, digit = '', 1
            for subject in day[0][0].split():
                sub = diary
                diary = sub + '\n' + str(digit) + '. ' + subject
                digit += 1
            bot.send_message(message.chat.id, diary, reply_markup=markup)
    elif message.text == 'Четверг':
        day = sqlighter.search_shedule_for_day(SHEDULE_ID, 'thursday')
        if day[0][0] is None:
            bot.send_message(message.chat.id, 'На этот день расписание не добавлено.'
                                              ' Добавьте его с помощью кнопки "✍🏻Изменить расписание".',
                             reply_markup=markup)
        else:
            diary, digit = '', 1
            for subject in day[0][0].split():
                sub = diary
                diary = sub + '\n' + str(digit) + '. ' + subject
                digit += 1
            bot.send_message(message.chat.id, diary, reply_markup=markup)
    elif message.text == 'Пятница':
        day = sqlighter.search_shedule_for_day(SHEDULE_ID, 'friday')
        if day[0][0] is None:
            bot.send_message(message.chat.id, 'На этот день расписание не добавлено.'
                                              ' Добавьте его с помощью кнопки "✍🏻Изменить расписание".',
                             reply_markup=markup)
        else:
            diary, digit = '', 1
            for subject in day[0][0].split():
                sub = diary
                diary = sub + '\n' + str(digit) + '. ' + subject
                digit += 1
            bot.send_message(message.chat.id, diary, reply_markup=markup)
    elif message.text == 'Суббота':
        day = sqlighter.search_shedule_for_day(SHEDULE_ID, 'saturday')
        if day[0][0] is None:
            bot.send_message(message.chat.id, 'На этот день расписание не добавлено.'
                                              ' Добавьте его с помощью кнопки "✍🏻Изменить расписание".',
                             reply_markup=markup)
        else:
            diary, digit = '', 1
            for subject in day[0][0].split():
                sub = diary
                diary = sub + '\n' + str(digit) + '. ' + subject
                digit += 1
            bot.send_message(message.chat.id, diary, reply_markup=markup)
    else:
        bot.send_message(message.chat.id, 'Такого дня нет в вашем расписании!')


# добавление расписания админом
def add_shedule(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('❌Назад')
    markup.add('✅Назад в главную')
    # в случае необходимости возвращение на главную
    if message.text == '✅Назад в главную':
        start_message(message)
    # в случае небходимости возвращение к функциям админов
    elif message.text == '❌Назад':
        return back(message)
    # в случае необходимости возвращение к расписанию
    elif message.text == '🚫Назад':
        return shedule(message)
    # после того, как мы получаем день, на который нужно составить расписание, вызываем функцию соответствующую
    # каждому учебному дню. Далее пользователь вводит данные о расписании на выбранный день недели
    elif message.text == 'Понедельник':
        sent = bot.send_message(message.chat.id, 'Введите предметы через пробел:', reply_markup=markup)
        bot.register_next_step_handler(sent, add_shedule_on_monday)
    elif message.text == 'Вторник':
        sent = bot.send_message(message.chat.id, 'Введите предметы через пробел:', reply_markup=markup)
        bot.register_next_step_handler(sent, add_shedule_on_tuesday)
    elif message.text == 'Среда':
        sent = bot.send_message(message.chat.id, 'Введите предметы через пробел:', reply_markup=markup)
        bot.register_next_step_handler(sent, add_shedule_on_wednesday)
    elif message.text == 'Четверг':
        sent = bot.send_message(message.chat.id, 'Введите предметы через пробел:', reply_markup=markup)
        bot.register_next_step_handler(sent, add_shedule_on_thursday)
    elif message.text == 'Пятница':
        sent = bot.send_message(message.chat.id, 'Введите предметы через пробел:', reply_markup=markup)
        bot.register_next_step_handler(sent, add_shedule_on_friday)
    elif message.text == 'Суббота':
        sent = bot.send_message(message.chat.id, 'Введите предметы через пробел:', reply_markup=markup)
        bot.register_next_step_handler(sent, add_shedule_on_saturday)
    else:
        bot.send_message(message.chat.id, 'Такого дня нет в вашем расписании!')


# добавление расписания на понедельник
def add_shedule_on_monday(message):
    try:
        # в случае необходимости, возвращение к расписанию
        if message.text == '❌Назад':
            return shedule(message)
        # подключение к БД
        sqlighter = SQLighter(message.from_user.id)
        # добавление расписания в БД на понедельник из сообщения введенного пользователем
        sqlighter.add_shedule_on_day('monday', message.text)
        bot.send_message(message.chat.id, 'Расписание успешно изменено.')
    # вывод сообщения об ошибке в случае некоррекного ввода данных / неверного вызова
    except Exception as e:
        bot.send_message(message.chat.id, 'Не удалось добавить расписание.')


# добавление расписания на вторник
def add_shedule_on_tuesday(message):
    try:
        # в случае необходимости, возвращение к расписанию
        if message.text == '❌Назад':
            return shedule(message)
        # подключение к БД
        sqlighter = SQLighter(message.from_user.id)
        # добавление расписания в БД на вторник из сообщения введенного пользователем
        sqlighter.add_shedule_on_day('tuesday', message.text)
        bot.send_message(message.chat.id, 'Расписание успешно изменено.')
    # вывод сообщения об ошибке в случае некоррекного ввода данных / неверного вызова
    except Exception as e:
        bot.send_message(message.chat.id, 'Не удалось добавить расписание.')


# добавление расписания на среду
def add_shedule_on_wednesday(message):
    try:
        # в случае необходимости, возвращение к расписанию
        if message.text == '❌Назад':
            return shedule(message)
        # подключение к БД
        sqlighter = SQLighter(message.from_user.id)
        # добавление расписания в БД на среду из сообщения введенного пользователем
        sqlighter.add_shedule_on_day('wednesday', message.text)
        bot.send_message(message.chat.id, 'Расписание успешно изменено.')
    # вывод сообщения об ошибке в случае некоррекного ввода данных / неверного вызова
    except Exception as e:
        bot.send_message(message.chat.id, 'Не удалось добавить расписание.')


# добавление расписания на четверг
def add_shedule_on_thursday(message):
    try:
        # в случае необходимости, возвращение к расписанию
        if message.text == '❌Назад':
            return shedule(message)
        # подключение к БД
        sqlighter = SQLighter(message.from_user.id)
        # добавление расписания в БД на четверг из сообщения введенного пользователем
        sqlighter.add_shedule_on_day('thursday', message.text)
        bot.send_message(message.chat.id, 'Расписание успешно изменено.')
    # вывод сообщения об ошибке в случае некоррекного ввода данных / неверного вызова
    except Exception as e:
        bot.send_message(message.chat.id, 'Не удалось добавить расписание.')


# добавление расписания на пятницу
def add_shedule_on_friday(message):
    try:
        # в случае необходимости, возвращение к расписанию
        if message.text == '❌Назад':
            return shedule(message)
        # подключение к БД
        sqlighter = SQLighter(message.from_user.id)
        # добавление расписания в БД на пятницу из сообщения введенного пользователем
        sqlighter.add_shedule_on_day('friday', message.text)
        bot.send_message(message.chat.id, 'Расписание успешно изменено.')
    # вывод сообщения об ошибке в случае некоррекного ввода данных / неверного вызова
    except Exception as e:
        bot.send_message(message.chat.id, 'Не удалось добавить расписание.')


# добавление расписания на субботу
def add_shedule_on_saturday(message):
    try:
        # в случае необходимости, возвращение к расписанию
        if message.text == '❌Назад':
            return shedule(message)
        # подключение к БД
        sqlighter = SQLighter(message.from_user.id)
        # добавление расписания в БД на субботу из сообщения введенного пользователем
        sqlighter.add_shedule_on_day('saturday', message.text)
        bot.send_message(message.chat.id, 'Расписание успешно изменено.')
    # вывод сообщения об ошибке в случае некоррекного ввода данных / неверного вызова
    except Exception as e:
        bot.send_message(message.chat.id, 'Не удалось добавить расписание.')


# работа с домашними заданиями
def homework(message):
    global ACTIVE_CLASS
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # создание списка необходимых кнопок
    buttons = ['✍Добавить ДЗ', '📖Узнать ДЗ', '🚫Назад']
    # вывод кнопок из списка на экран
    markup.add(*buttons)
    bot.send_message(message.chat.id, 'Вы перешли в домашние задания', reply_markup=markup)


def add_homework(message):
    global ACTIVE_CLASS
    try:
        # создание ключа для домашних заданий
        creating_key = True
        # начальное значение ключа
        key = ''
        # подключение к БД
        sqlighter = SQLighter(message.from_user.id)
        # генерация случайного ключа
        while creating_key:
            # добавление случайных значений в ключ
            key = ''.join(random.choice(string.digits) for _ in range(6))
            # проверка уникальности ключа ( нет проверки )
            if key[0] != '0':
                creating_key = False
        # создание спика, в котором будут хранится дата и само домашнее задание
        lst = []
        # сохранение первым элементом даты из полученного сообщения в формате ДД.ММ
        lst.append(message.text[0:5])
        # сохранение вторым элементом всего домашнего задания на введенный день
        lst.append(message.text[6:])
        # присваеваем дату из списка в переменную date
        date = lst[0]
        # присваеваем домашнее задание из списка в переменную homeworks
        homeworks = lst[1]
        # добваляем в БД значения из переменных
        sqlighter.create_new_homework(key, date, homeworks)
    # вывод сообщения об ошибке в случае некоррекного ввода данных / неверного вызова
    except Exception as e:
        bot.send_message(message.chat.id, '❌Ошибка! Добавить домашнее задание')


# запускаем бота
if __name__ == '__main__':
    print('Bot is working...')
    bot.infinity_polling()
