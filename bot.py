import logging
from datetime import time
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "BURAYA_BOT_TOKENİNİ_YAZ"
GROUP_ID = -5143299793

logging.basicConfig(level=logging.INFO)

# ---------------- CHECKLIST MESAJLARI ---------------- #

async def checklist_12(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=GROUP_ID, text="🕛 12:00 AÇILIŞ CHECKLIST\n- Işıklar açık mı?\n- Sistemler aktif mi?\n- Personel hazır mı?")

async def checklist_14(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=GROUP_ID, text="🕑 14:00 KASA CHECKLIST\n- Nakit kontrol edildi mi?\n- POS çalışıyor mu?")

async def checklist_15(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=GROUP_ID, text="🧹 15:00 TEMİZLİK CHECKLIST\n- Masa düzeni kontrol edildi mi?\n- WC temiz mi?")

async def checklist_19(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=GROUP_ID, text="🍽 19:00 SERVİS CHECKLIST\n- Rezervasyonlar hazır mı?\n- Mutfak hazır mı?")

async def checklist_23(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=GROUP_ID, text="🔒 23:00 KASA KONTROL\n- Gün sonu alındı mı?\n- Kasa kapandı mı?")

# ---------------- KOMUT ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Restoran Yönetim Botu Aktif!")

# ---------------- ZAMANLAYICI ---------------- #

async def setup_jobs(app: Application):

    app.job_queue.run_daily(checklist_12, time=time(hour=12, minute=0))
    app.job_queue.run_daily(checklist_14, time=time(hour=14, minute=0))
    app.job_queue.run_daily(checklist_15, time=time(hour=15, minute=0))
    app.job_queue.run_daily(checklist_19, time=time(hour=19, minute=0))
    app.job_queue.run_daily(checklist_23, time=time(hour=23, minute=0))

# ---------------- MAIN ---------------- #

async def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    await setup_jobs(app)

    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())