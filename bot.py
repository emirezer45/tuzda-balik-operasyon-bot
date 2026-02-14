import logging
from datetime import time
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "BURAYA_TOKEN"
GROUP_ID = -5143299793

logging.basicConfig(level=logging.INFO)

# CHECKLISTLER

async def checklist_12(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(GROUP_ID, "🕛 12:00 Açılış Checklist")

async def checklist_14(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(GROUP_ID, "🕑 14:00 Kasa Checklist")

async def checklist_15(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(GROUP_ID, "🧹 15:00 Temizlik Checklist")

async def checklist_19(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(GROUP_ID, "🍽 19:00 Servis Checklist")

async def checklist_23(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(GROUP_ID, "🔒 23:00 Kasa Kontrol Checklist")

async def start(update, context):
    await update.message.reply_text("Bot Aktif ✅")

async def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.job_queue.run_daily(checklist_12, time=time(12, 0))
    app.job_queue.run_daily(checklist_14, time=time(14, 0))
    app.job_queue.run_daily(checklist_15, time=time(15, 0))
    app.job_queue.run_daily(checklist_19, time=time(19, 0))
    app.job_queue.run_daily(checklist_23, time=time(23, 0))

    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())