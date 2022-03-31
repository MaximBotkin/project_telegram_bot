import telebot
from telebot import types
from dotenv import load_dotenv
import os
import sqlite3

# загружаем TOKEN из виртуального окружения
load_dotenv()
TOKEN = os.getenv('TOKEN')

# инициализируем класс TeleBot
bot = telebot.TeleBot(TOKEN)


class SQLighter:
    def __init__(self, user):
        self.database = 'db.db'
        self.con = sqlite3.connect("data.db")
        self.cursor = self.con.cursor()
        self.users = user


# команда /start
@bot.message_handler(commands=['start'])
def start_message(message):
    # получаем имя user и здороваемся с ним
    user_first_name = str(message.chat.first_name)

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
        search_class(message)
    else:
        bot.send_message(message.chat.id, text='Что-то на человеческом, я вас не понимаю😥')


@bot.message_handler(content_types=['text'])
def search_class(message):
    if str(message.text).isdigit() and len(str(message.text)) == 6:
        bot.send_message(message.chat.id, text=f'Ваш id = {message.text.id}')


# запускаем бота
if __name__ == '__main__':
    bot.infinity_polling()
