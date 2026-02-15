import os
import logging
from zoneinfo import ZoneInfo
from datetime import time

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    ContextTypes,
)

logging.basicConfig(level=logging.INFO)

TOKEN = osgetenv("7729207035:AAEW8jA8MqQtGpMzuYGzYrvP_EuPvAgiW3I")
GROUP_ID = -5143299793

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
        "Herhangi bir problem olduysa üst yetkiliye bildirildi mi",
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

async def checklist_gonder(context: ContextTypes.DEFAULT_TYPE):
    saat = context.job.data
    items = checklists[saat]

    daily_status[saat] = {
        "completed": [],
        "total": len(items)
    }

    keyboard = []

    for i, item in enumerate(items):
        keyboard.append([
            InlineKeyboardButton(
                f"⬜ {item}",
                callback_data=f"{saat}_{i}"
            )
        ])

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

    status = daily_status.get(saat)

    if not status:
        return

    if index not in status["completed"]:
        status["completed"].append(index)

    percent = int(len(status["completed"]) / status["total"] * 100)

    keyboard = []

    for i, item in enumerate(checklists[saat]):
        if i in status["completed"]:
            text = f"✅ {item}"
        else:
            text = f"⬜ {item}"

        keyboard.append([
            InlineKeyboardButton(
                text,
                callback_data=f"{saat}_{i}"
            )
        ])

    await query.edit_message_text(
        f"🕛 {saat}:00 Checklist\n\nTamamlanma: %{percent}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------------- GÜN SONU RAPOR ---------------- #

async def gun_sonu_rapor(context: ContextTypes.DEFAULT_TYPE):
    mesaj = "📊 GÜN SONU RAPORU\n\n"

    for saat, status in daily_status.items():
        percent = int(len(status["completed"]) / status["total"] * 100)
        mesaj += f"{saat}:00 → %{percent}\n"

    await context.bot.send_message(chat_id=GROUP_ID, text=mesaj)

# ---------------- MAIN ---------------- #

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CallbackQueryHandler(button))

    tz = ZoneInfo("Europe/Istanbul")

    app.job_queue.run_daily(checklist_gonder, time(12, 0, tzinfo=tz), data="12")
    app.job_queue.run_daily(checklist_gonder, time(14, 0, tzinfo=tz), data="14")
    app.job_queue.run_daily(checklist_gonder, time(17, 0, tzinfo=tz), data="17")
    app.job_queue.run_daily(checklist_gonder, time(20, 0, tzinfo=tz), data="20")
    app.job_queue.run_daily(checklist_gonder, time(23, 0, tzinfo=tz), data="23")

    app.job_queue.run_daily(gun_sonu_rapor, time(23, 30, tzinfo=tz))

    logging.info("FULL RESTORAN CHECKLIST BOT AKTİF")
    app.run_polling()

if __name__ == "__main__":
    main()
