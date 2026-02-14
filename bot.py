import logging
from datetime import time
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

TOKEN = "7729207035:AAHXP6Nb6PLOhnnQQfKqc7VS0z1g6_zwPM4"
CHAT_ID = -5143299793

CHECK_ITEMS = [
    "Personel hazır mı?",
    "Alan düzenli mi?",
    "Eksik var mı?",
    "Kasa kontrol edildi mi?",
    "Temizlik tamam mı?"
]

logging.basicConfig(level=logging.INFO)

# ==============================
# CHECKLIST GÖNDER
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

# ==============================
# BUTON SİSTEMİ
# ==============================

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if not data.startswith("check_"):
        return

    index = int(data.split("_")[1])
    user = query.from_user.first_name

    state = context.bot_data.get("checklist_state", {})

    # Eğer zaten işaretlendiyse tekrar işlem yapma
    if state.get(index) is not None:
        return

    state[index] = user

    # Yeni klavye oluştur
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
# START
# ==============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 PROFESYONEL BOT AKTİF 🇹🇷")

# ==============================
# TEST JOB
# ==============================

async def kimim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"İsim: {user.first_name}\nID: {user.id}"
    )
async def test_job(context: ContextTypes.DEFAULT_TYPE):
    await send_checklist(context, "TEST CHECK")

# ==============================
# MAIN
# ==============================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    job_queue = app.job_queue

    job_queue.run_once(test_job, 10)

    tz = ZoneInfo("Europe/Istanbul")

    job_queue.run_daily(
        lambda c: send_checklist(c, "12:00 Açılış Checklist"),
        time(12, 0, tzinfo=tz),
    )

    job_queue.run_daily(
        lambda c: send_checklist(c, "14:00 Kasa Checklist"),
        time(14, 0, tzinfo=tz),
    )

    job_queue.run_daily(
        lambda c: send_checklist(c, "15:00 Temizlik Checklist"),
        time(15, 0, tzinfo=tz),
    )

    job_queue.run_daily(
        lambda c: send_checklist(c, "19:00 Servis Kontrol Checklist"),
        time(19, 0, tzinfo=tz),
    )

    job_queue.run_daily(
        lambda c: send_checklist(c, "23:00 Kasa Kontrol Checklist"),
        time(23, 0, tzinfo=tz),
    )

    print("🚀 PROFESYONEL RESTORAN BOT BAŞLATILDI 🇹🇷")

    app.run_polling()

if __name__ == "__main__":
    main()