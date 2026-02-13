import os
import telebot
from datetime import datetime

TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

ADMIN_ID = 1753344846

print("Operasyon botu aktif ✅")


def yetkili_kontrol(message):
    return message.from_user.id == ADMIN_ID


def komut_sil(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass


@bot.message_handler(commands=['duyuru'])
def duyuru(message):
    if not yetkili_kontrol(message):
        return
    komut_sil(message)

    metin = message.text.replace("/duyuru", "").strip()

    bot.send_message(
        message.chat.id,
        f"📢 *DUYURU*\n\n{metin}",
        parse_mode="Markdown"
    )


@bot.message_handler(commands=['hatirlat'])
def hatirlat(message):
    if not yetkili_kontrol(message):
        return
    komut_sil(message)

    metin = message.text.replace("/hatirlat", "").strip()

    bot.send_message(
        message.chat.id,
        f"⏰ *HATIRLATMA*\n\n{metin}",
        parse_mode="Markdown"
    )


@bot.message_handler(commands=['odeme'])
def odeme(message):
    if not yetkili_kontrol(message):
        return
    komut_sil(message)

    metin = message.text.replace("/odeme", "").strip()

    bot.send_message(
        message.chat.id,
        f"💳 *ÖDEME BİLGİSİ*\n\n{metin}",
        parse_mode="Markdown"
    )


@bot.message_handler(commands=['rezervasyon'])
def rezervasyon(message):
    if not yetkili_kontrol(message):
        return
    komut_sil(message)

    metin = message.text.replace("/rezervasyon", "").strip()

    bot.send_message(
        message.chat.id,
        f"📅 *REZERVASYON*\n\n{metin}",
        parse_mode="Markdown"
    )


bot.infinity_polling()