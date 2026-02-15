import os
import logging
from zoneinfo import ZoneInfo
from datetime import time

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

logging.basicConfig(level=logging.INFO)

TOKEN = ("7729207035:AAEW8jA8MqQtGpMzuYGzYrvP_EuPvAgiW3I")
GROUP_ID = -5143299793  # Grup ID

if not TOKEN:
    raise ValueError("BOT_TOKEN bulunamadı!")

# ---------------- CHECKLIST TANIMLARI ---------------- #

checklists = {
    "12": [
        "POS cihazları şarja takıldı mı",
        "Kasa açıldı mı",
        "Faturalar sisteme işlendi mi",
        "Temizlik kontrolü yapıldı mı"
    ],
    "14": [
        "Eksikler sipariş edildi mi",
        "Rezervasyonlar kontrol edildi mi",
        "Faturalar sisteme işlendi mi",
        "Eksikler tamamlandı mı"
    ],
    "17": [
        "Servis öncesi son kontrol yapıldı mı",
        "Personel işe vaktinde geldi mi",
        "Kasa aktif mi",
        "Giderler yazıldı mı",
        "Şirket telefonu mesajları cevaplandı mı"
    ],
    "20": [
        "Problem olduysa üst yetkiliye bildirildi mi",
        "Paket sistemleri aktif mi",
        "İşleyiş problemsiz mi",
        "Kasa kontrol yapıldı mı"
    ],
    "23": [
        "Paketler sisteme girildi mi",
        "Z raporları alındı mı",
        "Kasa gelir gider yazıldı mı",
        "POS cihazları şarja takıldı mı",
        "Kasa düzenli mi",
        "Gün sonu tablosu işlendi mi",
        "Kasa kapatıldı mı",
        "Alarm kuruldu mu",
        "Camlar kapalı mı",
        "Işıklar kapalı mı",
        "Masalar düzenli mi"
    ]
}

daily_status = {}

# ---------------- CHECKLIST GÖNDER ---------------- #

async def checklist_gonder(context: ContextTypes.DEFAULT_TYPE, saat: str):
    items = checklists[saat]

    daily_status[saat] = {
        "completed": {},  # index: user
        "total": len(items)
    }

    keyboard = [
        [InlineKeyboardButton(f"✔ Madde {i+1}", callback_data=f"{saat}_{i}")]
        for i in range(len(items))
    ]

    await context.bot.send_message(
        chat_id=GROUP_ID,
        text=f"🕛 {saat}:00 Checklist\n\nTamamlanma: %0",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------- BUTON ---------------- #

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    saat, index = query.data.split("_")
    index = int(index)

    user = query.from_user.first_name

    status = daily_status.get(saat)
    if not status:
        return

    if index not in status["completed"]:
        status["completed"][index] = user

    percent = int(len(status["completed"]) / status["total"] * 100)

    text_output = f"🕛 {saat}:00 Checklist\n\n"

    keyboard = []

    for i, item in enumerate(checklists[saat]):
        if i in status["completed"]:
            yapan = status["completed"][i]
            text_output += f"✅ {item} – {yapan}\n"
        else:
            text_output += f"⬜ {item}\n"

        keyboard.append([
            InlineKeyboardButton("✔ İşaretle", callback_data=f"{saat}_{i}")
        ])

    text_output += f"\nTamamlanma: %{percent}"

    await query.edit_message_text(
        text_output,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------- KOMUTLAR ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        return

    await update.message.reply_text(
        "👋 Restoran Checklist Bot\n\n"
        "Komutlar:\n"
        "/gonder 12\n"
        "/gonder 14\n"
        "/gonder 17\n"
        "/gonder 20\n"
        "/gonder 23\n"
        "/rapor\n"
        "/reset"
    )

async def rapor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        return

    if not daily_status:
        await update.message.reply_text("Henüz checklist başlatılmadı.")
        return

    mesaj = "📊 ANLIK DURUM\n\n"

    for saat, status in daily_status.items():
        percent = int(len(status["completed"]) / status["total"] * 100)
        mesaj += f"{saat}:00 → %{percent}\n"

    await update.message.reply_text(mesaj)

async def gonder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        return

    if not context.args:
        await update.message.reply_text("Örnek: /gonder 12")
        return

    saat = context.args[0]

    if saat not in checklists:
        await update.message.reply_text("Geçersiz saat.")
        return

    await checklist_gonder(context, saat)
    await update.message.reply_text(f"{saat}:00 checklist gönderildi ✅")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        return

    daily_status.clear()
    await update.message.reply_text("🔄 Günlük checklist sıfırlandı.")

# ---------------- MAIN ---------------- #

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("rapor", rapor))
    app.add_handler(CommandHandler("gonder", gonder))
    app.add_handler(CommandHandler("reset", reset))

    tz = ZoneInfo("Europe/Istanbul")

    app.job_queue.run_daily(
        lambda c: c.application.create_task(checklist_gonder(c, "12")),
        time(12, 0, tzinfo=tz)
    )
    app.job_queue.run_daily(
        lambda c: c.application.create_task(checklist_gonder(c, "14")),
        time(14, 0, tzinfo=tz)
    )
    app.job_queue.run_daily(
        lambda c: c.application.create_task(checklist_gonder(c, "17")),
        time(17, 0, tzinfo=tz)
    )
    app.job_queue.run_daily(
        lambda c: c.application.create_task(checklist_gonder(c, "20")),
        time(20, 0, tzinfo=tz)
    )
    app.job_queue.run_daily(
        lambda c: c.application.create_task(checklist_gonder(c, "23")),
        time(23, 0, tzinfo=tz)
    )

    logging.info("CHECKLIST BOT AKTİF")
    app.run_polling()

if __name__ == "__main__":
    main()
