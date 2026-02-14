import logging
import os
from datetime import time, datetime, timedelta
from zoneinfo import ZoneInfo

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ==============================
# AYARLAR
# ==============================

TOKEN = os.getenv("7729207035:AAGQLgaJA-nC5yL7E529lEEcX8d2fVR_6hc")  # Railway ENV'den alır
CHAT_ID = -5143299793
OWNER_ID = 1753344846

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

async def send_checklist(context: ContextTypes.DEFAULT_TYPE):
    context.bot_data["checklist_state"] = {i: None for i in range(len(CHECK_ITEMS))}

    keyboard = [
        [InlineKeyboardButton(f"⬜ {item}", callback_data=f"check_{i}")]
        for i, item in enumerate(CHECK_ITEMS)
    ]

    await context.bot.send_message(
        chat_id=CHAT_ID,
        text="📋 Günlük Checklist\n\nİlerleme: 0%",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    index = int(query.data.split("_")[1])
    user = query.from_user.first_name
    state = context.bot_data.get("checklist_state", {})

    if state.get(index) is not None:
        return

    state[index] = user

    keyboard = []
    completed = 0

    for i, item in enumerate(CHECK_ITEMS):
        if state[i]:
            keyboard.append([
                InlineKeyboardButton(f"✅ {item} - {state[i]}", callback_data="done")
            ])
            completed += 1
        else:
            keyboard.append([
                InlineKeyboardButton(f"⬜ {item}", callback_data=f"check_{i}")
            ])

    percent = int((completed / len(CHECK_ITEMS)) * 100)

    await query.edit_message_text(
        text=f"📋 Günlük Checklist\n\nİlerleme: {percent}%",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ==============================
# HATIRLATMA
# ==============================

async def hatirlat(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=f"⏰ {context.job.data}"
    )

def zaman_hesapla(saat_str):
    now = datetime.now()
    hedef = datetime.strptime(saat_str, "%H:%M").replace(
        year=now.year, month=now.month, day=now.day
    )
    if hedef < now:
        hedef += timedelta(days=1)
    return (hedef - now).total_seconds()

def yetki(update: Update):
    return update.effective_user.id == OWNER_ID and update.effective_chat.type == "private"

async def alarm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not yetki(update):
        return
    try:
        saat = context.args[0]
        mesaj = " ".join(context.args[1:])
        context.job_queue.run_once(
            hatirlat,
            zaman_hesapla(saat),
            data=f"Alarm: {mesaj}"
        )
        await update.message.reply_text("✅ Alarm kuruldu.")
    except:
        await update.message.reply_text("❌ Format: /alarm 15:30 Mesaj")

# ==============================
# MAIN
# ==============================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(CommandHandler("alarm", alarm))

    tz = ZoneInfo("Europe/Istanbul")
    app.job_queue.run_daily(
        send_checklist,
        time(12, 0, tzinfo=tz),
    )

    print("🚀 BOT ÇALIŞIYOR")

    app.run_polling()

if __name__ == "__main__":
    main()