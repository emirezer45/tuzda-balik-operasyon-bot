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

# ==============================
# AYARLAR
# ==============================

TOKEN = "7729207035:AAHXP6Nb6PLOhnnQQfKqc7VS0z1g6_zwPM4"
CHAT_ID = -5143299793  # GRUP ID (başında -100 olmalı)

CHECK_ITEMS = [
    "Personel hazır mı?",
    "Alan düzenli mi?",
    "Eksik var mı?",
    "Kasa kontrol edildi mi?",
    "Temizlik tamam mı?"
]

logging.basicConfig(level=logging.INFO)

# ==============================
# CHECKLIST MESAJ GÖNDERME
# ==============================

async def send_checklist(context: ContextTypes.DEFAULT_TYPE, title: str):

    keyboard = []
    for i, item in enumerate(CHECK_ITEMS):
        keyboard.append([
            InlineKeyboardButton(
                f"⬜ {item}",
                callback_data=f"check_{i}"
            )
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=f"📋 {title}\n\nİlerleme: 0%",
        reply_markup=reply_markup
    )

# ==============================
# BUTON SİSTEMİ
# ==============================

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user.first_name
    data = query.data

    if not data.startswith("check_"):
        return

    index = int(data.split("_")[1])

    message_text = query.message.text
    completed_count = message_text.count("✅")

    keyboard = []
    new_completed = 0

    for i, item in enumerate(CHECK_ITEMS):

        if i == index:
            keyboard.append([
                InlineKeyboardButton(
                    f"✅ {item} - {user}",
                    callback_data="done"
                )
            ])
            new_completed += 1

        elif f"✅ {item}" in message_text:
            keyboard.append([
                InlineKeyboardButton(
                    f"✅ {item}",
                    callback_data="done"
                )
            ])
            new_completed += 1

        else:
            keyboard.append([
                InlineKeyboardButton(
                    f"⬜ {item}",
                    callback_data=f"check_{i}"
                )
            ])

    percent = int((new_completed / len(CHECK_ITEMS)) * 100)

    if percent == 100:
        status = "\n\n🎉 TÜM CHECKLIST TAMAMLANDI!"
    else:
        status = ""

    await query.edit_message_text(
        text=f"📋 Günlük Checklist\n\nİlerleme: {percent}%{status}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ==============================
# START KOMUTU
# ==============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 FULL PROFESYONEL BOT AKTİF 🇹🇷")

# ==============================
# TEST JOB (10 SANİYE)
# ==============================

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

    # 🔥 10 saniyede test
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

    print("🚀 FULL PROFESYONEL RESTORAN BOT BAŞLATILDI 🇹🇷")

    app.run_polling()

if __name__ == "__main__":
    main()