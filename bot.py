import os
import telebot
import time

TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

print("Bot başlatılıyor...")

# Webhook varsa temizle
bot.remove_webhook()

time.sleep(2)

print("Polling başlıyor...")

while True:
    try:
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print("Hata:", e)
        time.sleep(5)