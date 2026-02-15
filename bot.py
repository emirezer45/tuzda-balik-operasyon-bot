import os
import logging
import json
from zoneinfo import ZoneInfo
from datetime import time, datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

logging.basicConfig(level=logging.INFO)

TOKEN = ("7729207035:AAEW8jA8MqQtGpMzuYGzYrvP_EuPvAgiW3I")
GROUP_ID = -5143299793
MANAGER_ID = 1753344846  # 🔐 Müdür ID

if not TOKEN:
    raise ValueError("BOT_TOKEN bulunamadı!")

# ================= CHECKLIST TANIMLARI ================= #

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
    ],
    "kolaci": [
        "Kola stoğu kontrol edildi mi",
        "Eksik ürünler yazıldı mı",
        "Sipariş verildi mi",
        "Fatura kontrol edildi mi"
    ],
    "biraci": [
        "Bira stoğu kontrol edildi mi",
        "Soğuk dolap kontrol edildi mi",
        "Sipariş verildi mi",
        "İrsaliye alındı mı"
    ],
    "rakici": [
        "Rakı stoğu kontrol edildi mi",
        "Eksikler not edildi mi",
        "Sipariş verildi mi",
        "Fatura kontrol edildi mi"
    ]
}

daily_status = {}

# ================= HATIRLATMA ================= #

REMINDER_FILE = "reminders.json"
reminders = {}
reminder_counter = 1


def save_reminders():
    with open(REMINDER_FILE, "w") as f:
        json.dump(reminders, f)


def load_reminders():
    global reminders, reminder_counter
    try:
        with open(REMINDER_FILE, "r") as f:
            reminders = json.load(f)
            if reminders:
                reminder_counter = max(map(int, reminders.keys())) + 1
    except:
        reminders = {}


async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    reminder_id = context.job.data
    reminder = reminders.get(str(reminder_id))
    if not reminder:
        return

    await context.bot.send_message(
        chat_id=GROUP_ID,
        text=f"🔔 ÖDEME ZAMANI\n\n💳 {reminder['text']}"
    )

    reminders.pop(str(reminder_id), None)
    save_reminders()

# ================= SİPARİŞ KONTROL ================= #

async def siparis_kontrol(context: ContextTypes.DEFAULT_TYPE):
    key = context.job.data
    status = daily_status.get(key)

    if not status:
        return

    siparis_index = 2  # "Sipariş verildi mi" maddesi

    if siparis_index not in status["completed"]:
        await context.bot.send_message(
            chat_id=MANAGER_ID,
            text=f"🚨 UYARI\n\n{key.upper()} siparişi henüz girilmedi!"
        )

# ================= CHECKLIST ================= #

async def checklist_gonder(context: ContextTypes.DEFAULT_TYPE, key: str):
    items = checklists[key]

    daily_status[key] = {
        "completed": {},
        "total": len(items)
    }

    if key.isdigit():
        baslik = f"🕛 {key}:00 Checklist"
    else:
        baslik = f"📦 {key.upper()} Checklist"

    keyboard = [
        [InlineKeyboardButton("✔ İşaretle", callback_data=f"{key}_{i}")]
        for i in range(len(items))
    ]

    await context.bot.send_message(
        chat_id=GROUP_ID,
        text=f"{baslik}\n\nTamamlanma: %0",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    # 🔥 Eğer toptancı ise 2 saat sonra kontrol et
    if key in ["kolaci", "biraci", "rakici"]:
        context.job_queue.run_once(
            siparis_kontrol,
            when=7200,  # 2 saat
            data=key
        )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    key, index = query.data.split("_")
    index = int(index)

    user = query.from_user.first_name
    status = daily_status.get(key)
    if not status:
        return

    if index not in status["completed"]:
        status["completed"][index] = user

    percent = int(len(status["completed"]) / status["total"] * 100)

    if key.isdigit():
        baslik = f"🕛 {key}:00 Checklist\n\n"
    else:
        baslik = f"📦 {key.upper()} Checklist\n\n"

    text_output = baslik
    keyboard = []

    for i, item in enumerate(checklists[key]):
        if i in status["completed"]:
            yapan = status["completed"][i]
            text_output += f"✅ {item} – {yapan}\n"
        else:
            text_output += f"⬜ {item}\n"

        keyboard.append([
            InlineKeyboardButton("✔ İşaretle", callback_data=f"{key}_{i}")
        ])

    text_output += f"\nTamamlanma: %{percent}"

    await query.edit_message_text(
        text_output,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= KOMUTLAR ================= #

async def odeme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global reminder_counter

    if update.message.chat.type != "private":
        return

    if len(context.args) < 3:
        await update.message.reply_text("Örnek:\n/odeme 25.02.2026 14:30 Kredi Kartı")
        return

    tarih = context.args[0]
    saat_str = context.args[1]
    mesaj = " ".join(context.args[2:])

    try:
        zaman = datetime.strptime(f"{tarih} {saat_str}", "%d.%m.%Y %H:%M")
    except:
        await update.message.reply_text("Format yanlış.")
        return

    reminder_id = reminder_counter
    reminder_counter += 1

    reminders[str(reminder_id)] = {
        "type": "once",
        "text": mesaj
    }

    context.job_queue.run_once(send_reminder, zaman, data=reminder_id)
    save_reminders()

    # ✅ Anında gruba bilgi mesajı
    await context.bot.send_message(
        chat_id=GROUP_ID,
        text=f"📝 YENİ ÖDEME PLANLANDI\n\n📅 {tarih}\n🕒 {saat_str}\n💳 {mesaj}"
    )

    await update.message.reply_text(f"⏰ Kuruldu (ID: {reminder_id})")

# ================= MAIN ================= #

def main():
    load_reminders()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(CommandHandler("odeme", odeme))

    tz = ZoneInfo("Europe/Istanbul")

    for key in ["12", "14", "17", "20", "23"]:
        app.job_queue.run_daily(
            lambda c, k=key: c.application.create_task(checklist_gonder(c, k)),
            time(int(key), 0, tzinfo=tz)
        )

    app.job_queue.run_daily(
        lambda c: c.application.create_task(checklist_gonder(c, "kolaci")),
        time(11, 0, tzinfo=tz),
        days=(6,)
    )

    app.job_queue.run_daily(
        lambda c: c.application.create_task(checklist_gonder(c, "biraci")),
        time(11, 0, tzinfo=tz),
        days=(0,)
    )

    app.job_queue.run_daily(
        lambda c: c.application.create_task(checklist_gonder(c, "rakici")),
        time(11, 0, tzinfo=tz),
        days=(2,)
    )

    logging.info("RESTORAN ERP BOT AKTİF 🚀")
    app.run_polling()


if __name__ == "__main__":
    main()
