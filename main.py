import telebot
from dotenv import load_dotenv
import os


load_dotenv()
TOKEN = os.getenv('TOKEN')

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Привет")


bot.infinity_polling()
