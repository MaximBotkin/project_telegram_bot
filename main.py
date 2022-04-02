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

# инициализируем класс TeleBot
bot = telebot.TeleBot(TOKEN)


class SQLighter:
    def __init__(self, user_id):
        self.database = 'db.db'
        self.con = sqlite3.connect(self.database)
        self.cursor = self.con.cursor()
        self.user_id = user_id

    def add_user(self):
        result_of_execute = self.cursor.execute(f'SELECT * FROM users WHERE user_id = {self.user_id}').fetchall()
        if result_of_execute:
            print(result_of_execute)
            return
        sqlite_insert_query = f"""INSERT INTO users (user_id)  VALUES  ({self.user_id})"""
        self.cursor.execute(sqlite_insert_query)
        self.con.commit()

    def add_class(self, key):
        result_of_execute = self.cursor.execute(f'SELECT * FROM classes WHERE key = {key}').fetchall()
        if result_of_execute:
            return False
        sqlite_insert_query = f"""INSERT INTO classes (key)  VALUES  ({key})"""
        self.cursor.execute(sqlite_insert_query)
        self.con.commit()


# команда /start
@bot.message_handler(commands=['start'])
def start_message(message):
    # получаем имя user и здороваемся с ним
    user_first_name = str(message.chat.first_name)
    user_id = message.from_user.id
    sqlither = SQLighter(user_id)
    sqlither.add_user()
    buttons = ['👩‍🏫Создать класс', '👨‍🎓Найти класс', '❓Сообщить об ошибке']
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for button in buttons:
        markup.add(button)
    bot.send_message(message.chat.id, f'Привет, {user_first_name}!\nТебя приветствует SchoolBot,'
                                      f' пользуйся ботом с помощью команд снизу👇', reply_markup=markup)


@bot.message_handler(content_types=['text'])
def buttons(message):
    if message.text == '❓Сообщить об ошибке':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('✅Назад в главную')
        bot.send_message(message.chat.id, text='Если вы столкнулись с ошибкой напишите'
                                               ' админам: @Maxb0ttt или @kirmiq.', reply_markup=markup)
    elif message.text == '✅Назад в главную':
        start_message(message)
    elif message.text == '👨‍🎓Найти класс':
        bot.send_message(message.chat.id, text='Введите id класса(6-значный ключ из цифр):')
    elif message.text == '👩‍🏫Создать класс':
        sent = bot.send_message(message.chat.id, 'Введите название класса:')
        bot.register_next_step_handler(sent, create_class)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ['Расписание', 'ДЗ', 'Настройки']
        markup.add(*buttons)
    else:
        bot.send_message(message.chat.id, text='Что-то на человеческом, я вас не понимаю😥')


def create_class(message):
    try:
        creating_key = True
        while creating_key:
            key = ''.join(random.choice(string.digits) for _ in range(6))
            sqlighter = SQLighter(message.from_user.id)
            if key[0] != '0':
                if not sqlighter.add_class(key):
                    creating_key = False
        bot.send_message(message.chat.id, f'Класс был успешно создан. Ваш ключ:\n`{key}`')
    except Exception:
        bot.send_message(message.chat.id, '❌Ошибка! Не удалось создать класс')


# запускаем бота
if __name__ == '__main__':
    print('Bot is working...')
    bot.infinity_polling()
