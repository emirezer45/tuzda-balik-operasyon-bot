import logging
import json
import os
from datetime import time
from zoneinfo import ZoneInfo

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler
)

# ================== AYARLAR ==================

TOKEN = "BOT_TOKENİNİ_BURAYA_YAZ"
GROUP_ID = -5143299793
ADMIN_IDS = [1753344846]

DATA_FILE = "data.json"
tz = ZoneInfo("Europe/Istanbul")

# ================== LOG ==================

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ================== DATA ==================

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def reset_daily():
    data = {
        "12": None,
        "14": None,
        "15": None,
        "19": None,
        "23": None
    }
    save_data(data)

# ================== CHECKLIST GÖNDER ==================

async def send_checklist(context: ContextTypes.DEFAULT_TYPE, saat):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Tamamlandı", callback_data=f"done_{saat}")]
    ])

    await context.bot.send_message(
        chat_id=GROUP_ID,
        text=f"⏰ {saat}:00 Checklist\n\nButona basarak tamamlayın.",
        reply_markup=keyboard
    )

# ================== BUTON ==================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    saat = query.data.split("_")[1]

    data = load_data()

    if data.get(saat):
        await query.edit_message_text(f"❗ {saat}:00 zaten {data[saat]} tarafından tamamlandı.")
        return

    data[saat] = user.full_name
    save_data(data)

    await query.edit_message_text(f"✔ {saat}:00 checklist {user.full_name} tarafından tamamlandı.")

# ================== GÜN SONU RAPOR ==================

async def daily_report(context: ContextTypes.DEFAULT_TYPE):
    data = load_data()

    text = "📊 Günlük Rapor\n\n"

    for saat in ["12", "14", "15", "19", "23"]:
        if data.get(saat):
            text += f"✔ {saat}:00 – {data[saat]}\n"
        else:
            text += f"❌ {saat}:00 – Yapılmadı\n"

    await context.bot.send_message(chat_id=GROUP_ID, text=text)

    reset_daily()

# ================== KOMUTLAR ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot Aktif ✅")

async def durum(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot aktif 🇹🇷 Türkiye saati kullanılıyor.\nKayıt sistemi aktif.")

async def duyuru(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return

    mesaj = " ".join(context.args)
    await context.bot.send_message(chat_id=GROUP_ID, text=f"📢 DUYURU:\n\n{mesaj}")

# ================== MAIN ==================

def main():
    if not os.path.exists(DATA_FILE):
        reset_daily()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("durum", durum))
    app.add_handler(CommandHandler("duyuru", duyuru))
    app.add_handler(CallbackQueryHandler(button_handler))

    job_queue = app.job_queue

    job_queue.run_daily(lambda c: send_checklist(c, "12"), time(12, 0, tzinfo=tz))
    job_queue.run_daily(lambda c: send_checklist(c, "14"), time(14, 0, tzinfo=tz))
    job_queue.run_daily(lambda c: send_checklist(c, "15"), time(15, 0, tzinfo=tz))
    job_queue.run_daily(lambda c: send_checklist(c, "19"), time(19, 0, tzinfo=tz))
    job_queue.run_daily(lambda c: send_checklist(c, "23"), time(23, 0, tzinfo=tz))

    job_queue.run_daily(daily_report, time(23, 30, tzinfo=tz))

    logging.info("FULL PROFESYONEL BOT BAŞLATILDI 🇹🇷")

    app.run_polling()

if __name__ == "__main__":
    main()