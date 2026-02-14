import logging
from datetime import time, datetime, timedelta
from zoneinfo import ZoneInfo

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ==============================
# AYARLAR
# ==============================

import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

TOKEN = os.getenv("7729207035:AAHbjzutiw3hiNRbWKlZghg9Ta57Xpw0rzM")

app = Application.builder().token(TOKEN).build()

CHAT_ID = -5143299793
OWNER_ID = 1753344846  # BURAYA KENDİ ID'ni YAZ

CHECK_ITEMS = [
    "Personel hazır mı?",
    "Alan düzenli mi?",
    "Eksik var mı?",
    "Kasa kontrol edildi mi?",
    "Temizlik tamam mı?"
]

logging.basicConfig(level=logging.INFO)

# ==============================
# CHECKLIST
# ==============================

async def send_checklist(context: ContextTypes.DEFAULT_TYPE, title: str):

    context.bot_data["checklist_state"] = {
        i: None for i in range(len(CHECK_ITEMS))
    }

    keyboard = [
        [InlineKeyboardButton(f"⬜ {item}", callback_data=f"check_{i}")]
        for i, item in enumerate(CHECK_ITEMS)
    ]

    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=f"📋 {title}\n\nİlerleme: 0%",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data.startswith("check_"):
        return

    index = int(data.split("_")[1])
    user = query.from_user.first_name

    state = context.bot_data.get("checklist_state", {})

    if state.get(index) is not None:
        return

    state[index] = user

    keyboard = []
    completed = 0

    for i, item in enumerate(CHECK_ITEMS):
        if state[i] is not None:
            keyboard.append([
                InlineKeyboardButton(
                    f"✅ {item} - {state[i]}",
                    callback_data="done"
                )
            ])
            completed += 1
        else:
            keyboard.append([
                InlineKeyboardButton(
                    f"⬜ {item}",
                    callback_data=f"check_{i}"
                )
            ])

    percent = int((completed / len(CHECK_ITEMS)) * 100)

    status = ""
    if percent == 100:
        status = "\n\n🎉 TÜM CHECKLIST TAMAMLANDI!"

    await query.edit_message_text(
        text=f"📋 Günlük Checklist\n\nİlerleme: {percent}%{status}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ==============================
# HATIRLATMA SİSTEMİ
# ==============================

async def hatirlat(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=f"⏰ HATIRLATMA\n\n{job.data}"
    )

def zaman_hesapla(saat_str):
    now = datetime.now()
    hedef = datetime.strptime(saat_str, "%H:%M").replace(
        year=now.year,
        month=now.month,
        day=now.day
    )
    if hedef < now:
        hedef += timedelta(days=1)
    return (hedef - now).total_seconds()

# ==============================
# SADECE OWNER KOMUTLAR
# ==============================

def yetki_kontrol(update: Update):
    return (
        update.effective_user.id == OWNER_ID
        and update.effective_chat.type == "private"
    )

async def alarm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not yetki_kontrol(update):
        return
    try:
        saat = context.args[0]
        mesaj = " ".join(context.args[1:])
        context.job_queue.run_once(
            hatirlat,
            zaman_hesapla(saat),
            data=f"🔔 Alarm: {mesaj}"
        )
        await update.message.reply_text("✅ Alarm kuruldu.")
    except:
        await update.message.reply_text("❌ Format: /alarm 15:30 Mesaj")

async def odeme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not yetki_kontrol(update):
        return
    try:
        saat = context.args[0]
        mesaj = " ".join(context.args[1:])
        context.job_queue.run_once(
            hatirlat,
            zaman_hesapla(saat),
            data=f"🏦 Banka Ödemesi: {mesaj}"
        )
        await update.message.reply_text("✅ Ödeme hatırlatması kuruldu.")
    except:
        await update.message.reply_text("❌ Format: /odeme 18:00 Açıklama")

async def fatura(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not yetki_kontrol(update):
        return
    try:
        saat = context.args[0]
        mesaj = " ".join(context.args[1:])
        context.job_queue.run_once(
            hatirlat,
            zaman_hesapla(saat),
            data=f"🧾 Fatura: {mesaj}"
        )
        await update.message.reply_text("✅ Fatura hatırlatması kuruldu.")
    except:
        await update.message.reply_text("❌ Format: /fatura 20:00 Açıklama")

async def rezervasyon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not yetki_kontrol(update):
        return
    try:
        saat = context.args[0]
        mesaj = " ".join(context.args[1:])
        context.job_queue.run_once(
            hatirlat,
            zaman_hesapla(saat),
            data=f"🍽 Rezervasyon: {mesaj}"
        )
        await update.message.reply_text("✅ Rezervasyon kuruldu.")
    except:
        await update.message.reply_text("❌ Format: /rez 19:30 Açıklama")

# ==============================
# MAIN
# ==============================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CallbackQueryHandler(button))

    app.add_handler(CommandHandler("alarm", alarm))
    app.add_handler(CommandHandler("odeme", odeme))
    app.add_handler(CommandHandler("fatura", fatura))
    app.add_handler(CommandHandler("rez", rezervasyon))

    tz = ZoneInfo("Europe/Istanbul")
    job_queue = app.job_queue

    job_queue.run_daily(
        lambda c: send_checklist(c, "12:00 Açılış Checklist"),
        time(12, 0, tzinfo=tz),
    )

    print("🚀 YÖNETİCİ KİLİTLİ BOT BAŞLATILDI 🇹🇷")

    app.run_polling()

if __name__ == "__main__":
    main()