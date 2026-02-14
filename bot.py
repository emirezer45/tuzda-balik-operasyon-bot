import os
import logging
from zoneinfo import ZoneInfo
from datetime import time

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    ContextTypes,
)

logging.basicConfig(level=logging.INFO)

TOKEN = ("7729207035:AAEW8jA8MqQtGpMzuYGzYrvP_EuPvAgiW3I")
GROUP_ID = -5143299793

if not TOKEN:
    raise ValueError("BOT_TOKEN bulunamadı!")

# Günlük durum kaydı
daily_status = {
    "12": None,
    "14": None,
    "15": None,
    "19": None,
    "23": None,
}

# ---------------- CHECKLIST GÖNDER ---------------- #

async def checklist_gonder(context: ContextTypes.DEFAULT_TYPE, saat):

    daily_status[saat] = None

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Tamamlandı", callback_data=f"done_{saat}")]
    ])

    await context.bot.send_message(
        chat_id=GROUP_ID,
        text=f"🕛 {saat}:00 Checklist\n\nButona basarak tamamlayın.",
        reply_markup=keyboard
    )

# ---------------- BUTON ---------------- #

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("done_"):
        saat = data.split("_")[1]
        user = query.from_user.first_name

        if daily_status[saat] is None:
            daily_status[saat] = user

            await query.edit_message_text(
                f"🕛 {saat}:00 Checklist\n\n"
                f"✅ Tamamlandı - {user}"
            )
        else:
            await query.answer("Zaten tamamlandı.", show_alert=True)

# ---------------- GÜN SONU RAPOR ---------------- #

async def gun_sonu_rapor(context: ContextTypes.DEFAULT_TYPE):

    mesaj = "📊 GÜN SONU RAPORU\n\n"

    for saat, user in daily_status.items():
        if user:
            mesaj += f"✔ {saat}:00 - {user}\n"
        else:
            mesaj += f"❌ {saat}:00 Yapılmadı\n"

    await context.bot.send_message(chat_id=GROUP_ID, text=mesaj)

# ---------------- MAIN ---------------- #

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CallbackQueryHandler(button))

    tz = ZoneInfo("Europe/Istanbul")
    job_queue = app.job_queue

    job_queue.run_daily(lambda c: checklist_gonder(c, "12"),
                        time(12, 0, tzinfo=tz))
    job_queue.run_daily(lambda c: checklist_gonder(c, "14"),
                        time(14, 0, tzinfo=tz))
    job_queue.run_daily(lambda c: checklist_gonder(c, "15"),
                        time(15, 0, tzinfo=tz))
    job_queue.run_daily(lambda c: checklist_gonder(c, "19"),
                        time(19, 0, tzinfo=tz))
    job_queue.run_daily(lambda c: checklist_gonder(c, "23"),
                        time(23, 0, tzinfo=tz))

    job_queue.run_daily(gun_sonu_rapor,
                        time(23, 30, tzinfo=tz))

    logging.info("BUTONLU CHECKLIST + RAPOR AKTİF")
    app.run_polling()

if __name__ == "__main__":
    main()