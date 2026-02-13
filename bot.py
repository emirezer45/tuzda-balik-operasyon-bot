import os
import telebot

TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

print("Bot çalışıyor...")

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Bot aktif ve çalışıyor ✅")

@bot.message_handler(func=lambda message: True)
def echo(message):
    bot.reply_to(message, "Mesajını aldım: " + message.text)

bot.infinity_polling()