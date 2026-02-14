import telebot
import os
import time

TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

print("Bot başlatılıyor...")

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Bot aktif ✅")
@bot.message_handler(commands=['id'])
def id_goster(message):
    bot.reply_to(message, f"Chat ID: {message.chat.id}")
while True:
    try:
        print("Polling başlıyor...")
        bot.polling(none_stop=True, timeout=60)
    except Exception as e:
        print("Hata:", e)
        time.sleep(5)
