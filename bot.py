import logging
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

TOKEN = "7729207035:AAEW8jA8MqQtGpMzuYGzYrvP_EuPvAgiW3I"
GROUP_ID = -5143299793
MANAGER_ID = 1753344846

# ================= CHECKLIST ================= #

checklists = {
    "12": ["POS cihazları şarja takıldı mı","Kasa açıldı mı","Faturalar sisteme işlendi mi","Temizlik kontrolü yapıldı mı"],
    "14": ["Eksikler sipariş edildi mi","Rezervasyonlar kontrol edildi mi","Faturalar sisteme işlendi mi","Eksikler tamamlandı mı"],
    "17": ["Servis öncesi son kontrol yapıldı mı","Personel işe vaktinde geldi mi","Kasa aktif mi","Giderler yazıldı mı","Şirket telefonu mesajları cevaplandı mı"],
    "20": ["Problem olduysa üst yetkiliye bildirildi mi","Paket sistemleri aktif mi","İşleyiş problemsiz mi","Kasa kontrol yapıldı mı"],
    "23": ["Paketler sisteme girildi mi","Z raporları alındı mı","Kasa gelir gider yazıldı mı","POS cihazları şarja takıldı mı","Kasa düzenli mi","Gün sonu tablosu işlendi mi","Kasa kapatıldı mı","Alarm kuruldu mu","Camlar kapalı mı","Işıklar kapalı mı","Masalar düzenli mi"],
    "kolaci": ["Kola stoğu kontrol edildi mi","Eksik ürünler yazıldı mı","Sipariş verildi mi","Fatura kontrol edildi mi"],
    "biraci": ["Bira stoğu kontrol edildi mi","Soğuk dolap kontrol edildi mi","Sipariş verildi mi","İrsaliye alındı mı"],
    "rakici": ["Rakı stoğu kontrol edildi mi","Eksikler not edildi mi","Sipariş verildi mi","Fatura kontrol edildi mi"]
}

daily_status = {}

# ================= PANEL ================= #

async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "private":
        return

    text = """
📊 RESTORAN ERP PRO PANEL

/start - Botu başlat
/panel - Komutları göster
/odeme - Ödeme hatırlatıcı kur
/reset - Günlük checklist sıfırla (Müdür)

Otomatik Sistemler:
• Saatlik checklist
• Sipariş günü kontrol
• Ödeme hatırlatma
• Müdüre otomatik uyarı
"""
    await update.message.reply_text(text)

# ================= START ================= #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 ERP PRO BOT AKTİF\n\nKomutlar için /panel")

# ================= RESET ================= #

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != MANAGER_ID:
        return

    daily_status.clear()
    await update.message.reply_text("🔄 Checklistler sıfırlandı.")

# ================= CHECKLIST ================= #

async def checklist_gonder(context: ContextTypes.DEFAULT_TYPE, key: str):
    items = checklists[key]

    daily_status[key] = {"completed": {}, "total": len(items)}

    baslik = f"🕛 {key}:00 Checklist" if key.isdigit() else f"📦 {key.upper()} Sipariş"

    keyboard = [[InlineKeyboardButton("✔ İşaretle", callback_data=f"{key}_{i}")]
                for i in range(len(items))]

    await context.bot.send_message(
        chat_id=GROUP_ID,
        text=f"{baslik}\n\nTamamlanma: %0",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    # sipariş kontrolü (2 saat sonra)
    if key in ["kolaci","biraci","rakici"]:
        context.job_queue.run_once(siparis_kontrol, 7200, data=key)

async def siparis_kontrol(context: ContextTypes.DEFAULT_TYPE):
    key = context.job.data
    status = daily_status.get(key)
    if not status:
        return

    if 2 not in status["completed"]:
        await context.bot.send_message(
            chat_id=MANAGER_ID,
            text=f"🚨 {key.upper()} siparişi yapılmadı!"
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

    text_output = f"{'🕛 '+key+':00' if key.isdigit() else '📦 '+key.upper()} Checklist\n\n"

    keyboard = []

    for i, item in enumerate(checklists[key]):
        if i in status["completed"]:
            yapan = status["completed"][i]
            text_output += f"✅ {item} – {yapan}\n"
        else:
            text_output += f"⬜ {item}\n"

        keyboard.append([InlineKeyboardButton("✔ İşaretle", callback_data=f"{key}_{i}")])

    text_output += f"\nTamamlanma: %{percent}"

    await query.edit_message_text(text_output, reply_markup=InlineKeyboardMarkup(keyboard))

# ================= ÖDEME ================= #

async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    mesaj = context.job.data
    await context.bot.send_message(chat_id=GROUP_ID, text=f"🔔 ÖDEME ZAMANI\n\n💳 {mesaj}")

async def odeme(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    delay = (zaman - datetime.now()).total_seconds()
    if delay <= 0:
        await update.message.reply_text("Geçmiş tarih girdin.")
        return

    context.job_queue.run_once(send_reminder, delay, data=mesaj)

    await context.bot.send_message(
        chat_id=GROUP_ID,
        text=f"📝 YENİ ÖDEME PLANLANDI\n\n📅 {tarih}\n🕒 {saat_str}\n💳 {mesaj}"
    )

    await update.message.reply_text("⏰ Kuruldu!")

# ================= MAIN ================= #

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", panel))
    app.add_handler(CommandHandler("odeme", odeme))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CallbackQueryHandler(button))

    tz = ZoneInfo("Europe/Istanbul")

    for key in ["12","14","17","20","23"]:
        app.job_queue.run_daily(
            lambda c, k=key: c.application.create_task(checklist_gonder(c,k)),
            time(int(key),0,tzinfo=tz)
        )

    # Sipariş günleri
    app.job_queue.run_daily(lambda c: c.application.create_task(checklist_gonder(c,"kolaci")),
                            time(11,0,tzinfo=tz), days=(6,))
    app.job_queue.run_daily(lambda c: c.application.create_task(checklist_gonder(c,"biraci")),
                            time(11,0,tzinfo=tz), days=(0,))
    app.job_queue.run_daily(lambda c: c.application.create_task(checklist_gonder(c,"rakici")),
                            time(11,0,tzinfo=tz), days=(2,))

    logging.info("ERP PRO BOT AKTİF 🚀")
    app.run_polling()

if __name__ == "__main__":
    main()
