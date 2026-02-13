import os
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
print("TOKEN:", os.getenv("TOKEN"))
TOKEN = os.getenv("TOKEN")
OWNER_ID = 1753344846

GROUP_ID = None
reminders = {}
reminder_counter = 1


def is_owner(update: Update):
    return update.effective_user.id == OWNER_ID


async def delete_command(update: Update):
    try:
        # SADECE GRUPTA SİL
        if update.effective_chat.type in ["group", "supergroup"]:
            await update.message.delete()
    except:
        pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global GROUP_ID

    if not is_owner(update):
        return

    GROUP_ID = update.effective_chat.id
    await delete_command(update)


async def ekle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global reminder_counter

    if not is_owner(update):
        return

    await delete_command(update)

    if GROUP_ID is None:
        return

    try:
        time_text = context.args[0]
        message_text = " ".join(context.args[1:])
        hour, minute = map(int, time_text.split(":"))
    except:
        return

    now = datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if target < now:
        target += timedelta(days=1)

    reminder_id = reminder_counter
    reminder_counter += 1

    async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=f"📢 HATIRLATMA\n\n{message_text}",
        )

    context.job_queue.run_once(
        send_reminder,
        when=(target - now).total_seconds(),
    )

    reminders[reminder_id] = f"{time_text} → {message_text}"


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ekle", ekle))

    print("Bot çalışıyor...")
    app.run_polling()


if __name__ == "__main__":
    main()