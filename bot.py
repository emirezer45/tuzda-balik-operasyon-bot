import os
import telebot
import time

TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

print("Operasyon botu başlatılıyor...")

while True:
    try:
        print("Bot polling başlatıldı ✅")
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print("Hata oldu, yeniden deneniyor:", e)
        time.sleep(5)