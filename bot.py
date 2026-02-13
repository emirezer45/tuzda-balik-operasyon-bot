import os
import asyncio
from datetime import datetime, time
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 1753344846

reminders = {}
reminder_counter = 1


def is_owner(update: Update):
    return update.effective_user.id == OWNER_ID


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return
    await update.message.reply_text("Tuzda Balık Hatırlatıcı Aktif 🚀")


async def ekle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global reminder_counter

    if not is_owner(update):
        return

    try:
        time_text = context.args[0]
        message_text = " ".join(context.args[1:])
        hour, minute = map(int, time_text.split(":"))
    except:
        await update.message.reply_text(
            "Kullanım: /ekle 14:30 Balıkları çevir"
        )
        return

    now = datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0)

    if target < now:
        target = target.replace(day=now.day + 1)

    delay = (target - now).total_seconds()

    reminder_id = reminder_counter
    reminder_counter += 1

    async def send_reminder():
        await asyncio.sleep(delay)
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"⏰ Hatırlatma: {message_text}",
        )

    asyncio.create_task(send_reminder())

    reminders[reminder_id] = f"{time_text} → {message_text}"

    await update.message.reply_text(
        f"✅ Hatırlatma eklendi ({reminder_id})"
    )


async def liste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return

    if not reminders:
        await update.message.reply_text("Aktif hatırlatma yok.")
        return

    text = "📋 Aktif Hatırlatmalar:\n"
    for rid, content in reminders.items():
        text += f"{rid} - {content}\n"

    await update.message.reply_text(text)


async def sil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        return

    try:
        rid = int(context.args[0])
    except:
        await update.message.reply_text("Kullanım: /sil 1")
        return

    if rid in reminders:
        del reminders[rid]
        await update.message.reply_text(f"❌ Silindi ({rid})")
    else:
        await update.message.reply_text("Bulunamadı.")


async def gunluk_mesaj(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=OWNER_ID,
        text="🐟 Günlük balık kontrol zamanı!",
    )


async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ekle", ekle))
    app.add_handler(CommandHandler("liste", liste))
    app.add_handler(CommandHandler("sil", sil))

    job_queue = app.job_queue
    job_queue.run_daily(
        gunluk_mesaj,
        time(hour=9, minute=0),
    )

    await app.run_polling()


if __name__ == "__main__":
    import asyncio
    asyncio.get_event_loop().run_until_complete(main())
    