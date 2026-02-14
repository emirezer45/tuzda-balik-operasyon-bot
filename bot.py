import logging
from datetime import time
import pytz

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = "7729207035:AAHXP6Nb6PLOhnnQQfKqc7VS0z1g6_zwPM4"
CHAT_ID = -5143299793  # Grup ID

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

tz = pytz.timezone("Europe/Istanbul")


# =========================
# CHECKLIST MESAJI
# =========================
async def send_checklist(context: ContextTypes.DEFAULT_TYPE, title):
    keyboard = [
        [InlineKeyboardButton("✅ Tamamlandı", callback_data=f"done_{title}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=f"📋 {title} Checklist\n\nHazır olduğunda butona basın.",
        reply_markup=reply_markup
    )


# =========================
# BUTON TIKLANINCA
# =========================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user.first_name
    data = query.data.replace("done_", "")

    await query.edit_message_text(
        text=f"✅ {data} tamamlandı.\n👤 {user}"
    )


# =========================
# START KOMUTU
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 FULL PROFESYONEL BOT AKTİF 🇹🇷")


# =========================
# MAIN
# =========================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.bot.delete_webhook(drop_pending_updates=True)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    job_queue = app.job_queue

    # Günlük checklist saatleri
   job_queue.run_once(
    lambda c: send_checklist(c, "TEST CHECK"),
    10
)
 job_queue.run_daily(
        lambda c: send_checklist(c, "12:00 Açılış"),
        time(hour=12, minute=0, tzinfo=tz),
    )

    job_queue.run_daily(
        lambda c: send_checklist(c, "14:00 Kasa"),
        time(hour=14, minute=0, tzinfo=tz),
    )

    job_queue.run_daily(
        lambda c: send_checklist(c, "15:00 Temizlik"),
        time(hour=15, minute=0, tzinfo=tz),
    )

    job_queue.run_daily(
        lambda c: send_checklist(c, "19:00 Servis Kontrol"),
        time(hour=19, minute=0, tzinfo=tz),
    )

    job_queue.run_daily(
        lambda c: send_checklist(c, "23:00 Kasa Kontrol"),
        time(hour=23, minute=0, tzinfo=tz),
    )

    logging.info("FULL PROFESYONEL BOT BAŞLATILDI 🇹🇷")

    app.run_polling()


if __name__ == "__main__":
    main()