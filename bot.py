
import logging
from datetime import time
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

TOKEN = "7729207035:AAHXP6Nb6PLOhnnQQfKqc7VS0z1g6_zwPM4"
CHAT_ID = -100XXXXXXXXXX  # GERÇEK GRUP ID

logging.basicConfig(level=logging.INFO)

# -------- CHECKLIST MESAJ --------
async def send_checklist(context: ContextTypes.DEFAULT_TYPE, title: str):
    message = f"""
📋 {title}

☐ Personel hazır mı?
☐ Alan düzenli mi?
☐ Eksik var mı?
☐ Kasa kontrol edildi mi?
☐ Temizlik tamam mı?
"""
    await context.bot.send_message(chat_id=CHAT_ID, text=message)

# -------- TEST JOB --------
async def test_job(context: ContextTypes.DEFAULT_TYPE):
    await send_checklist(context, "TEST CHECK")

# -------- START KOMUTU --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot aktif 🚀")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    job_queue = app.job_queue

    # 🔥 10 saniyelik test
    job_queue.run_once(test_job, 10)

    # 🇹🇷 Türkiye saati
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

    print("🚀 FULL PROFESYONEL BOT BAŞLATILDI 🇹🇷")

    app.run_polling()

if __name__ == "__main__":
    main()