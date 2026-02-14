import os
import logging
from zoneinfo import ZoneInfo
from datetime import time

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# ---------------- LOG AYARI ---------------- #

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

TOKEN = os.getenv("7729207035:AAEW8jA8MqQtGpMzuYGzYrvP_EuPvAgiW3I")
GROUP_ID = -5143299793  # Grup ID

if not TOKEN:
    raise ValueError("BOT_TOKEN bulunamadı!")

# ---------------- KOMUTLAR ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("START komutu çalıştı")
    await update.message.reply_text("Bot Aktif ✅")

async def checklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("CHECKLIST komutu çalıştı")
    await update.message.reply_text(
        "📋 Günlük Checklist Saatleri:\n\n"
        "12:00 Açılış\n"
        "14:00 Kasa\n"
        "15:00 Temizlik\n"
        "19:00 Servis Kontör\n"
        "23:00 Kasa Kontrol"
    )

async def durum(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("DURUM komutu çalıştı")
    await update.message.reply_text("Bot aktif ve scheduler çalışıyor ✅")

# ---------------- OTOMATİK MESAJLAR ---------------- #

async def checklist_12(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=GROUP_ID, text="🕛 12:00 Açılış Checklist")

async def checklist_14(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=GROUP_ID, text="🕑 14:00 Kasa Checklist")

async def checklist_15(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=GROUP_ID, text="🕒 15:00 Temizlik Checklist")

async def checklist_19(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=GROUP_ID, text="🕖 19:00 Servis Kontör Checklist")

async def checklist_23(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=GROUP_ID, text="🕚 23:00 Kasa Kontrol Checklist")

# ---------------- MAIN ---------------- #

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Komutlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("checklist", checklist))
    app.add_handler(CommandHandler("durum", durum))

    # Scheduler
    tz = ZoneInfo("Europe/Istanbul")
    job_queue = app.job_queue

    job_queue.run_daily(checklist_12, time(hour=12, minute=0, tzinfo=tz))
    job_queue.run_daily(checklist_14, time(hour=14, minute=0, tzinfo=tz))
    job_queue.run_daily(checklist_15, time(hour=15, minute=0, tzinfo=tz))
    job_queue.run_daily(checklist_19, time(hour=19, minute=0, tzinfo=tz))
    job_queue.run_daily(checklist_23, time(hour=23, minute=0, tzinfo=tz))

    logging.info("BOT BAŞLATILDI")
    app.run_polling()

if __name__ == "__main__":
    main()