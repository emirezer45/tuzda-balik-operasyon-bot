import telebot
import os
import time

TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

print("Bot başlatılıyor...")

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Bot aktif ✅")

while True:
    try:
        print("Polling başlıyor...")
        bot.polling(none_stop=True, timeout=60)
    except Exception as e:
        print("Hata:", e)
        time.sleep(5)
@bot.message_handler(func=lambda message: True)
def grup_id_goster(message):
    print("CHAT ID:", message.chat.id)