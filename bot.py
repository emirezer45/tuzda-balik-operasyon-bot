from zoneinfo import ZoneInfo
from datetime import time

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

TOKEN = "7729207035:AAHongvrXncUYv5lih9EnUk7URq_UQTle6I"
GROUP_ID = -10051432299793
MUDUR_ID = 1753344846

TZ = ZoneInfo("Europe/Istanbul")

# =========================
# CHECKLISTLER (GRUBA GİDER)
# =========================

checklists = {
    "12": """🕛 12:00 Açılış Kontrolü

▫️ POS cihazları şarja takıldı mı?
▫️ Kasa açıldı mı?
▫️ Faturalar sisteme işlendi mi?
▫️ Temizlik kontrolü yapıldı mı?
""",
    "14": """🕑 14:00 Kontrol

▫️ Eksikler sipariş edildi mi?
▫️ Rezervasyonlar kontrol edildi mi?
▫️ Faturalar sisteme işlendi mi?
▫️ Eksikler tamamlandı mı?
""",
    "17": """🕔 17:00 Servis Öncesi

▫️ Son kontrol yapıldı mı?
▫️ Personel zamanında geldi mi?
▫️ Kasa aktif mi?
▫️ Giderler yazıldı mı?
▫️ Şirket telefonu cevaplandı mı?
""",
    "20": """🕗 20:00 Kontrol

▫️ Problem varsa bildirildi mi?
▫️ Paket sistemleri aktif mi?
▫️ İşleyiş düzgün mü?
▫️ Kasa kontrol edildi mi?
""",
    "23": """🕚 23:00 Gün Sonu

▫️ Paketler sisteme girildi mi?
▫️ Z raporları alındı mı?
▫️ Gelir gider yazıldı mı?
▫️ POS şarja takıldı mı?
▫️ Kasa düzenli mi?
▫️ Alarm kuruldu mu?
▫️ Camlar kapalı mı?
▫️ Işıklar kapalı mı?
▫️ Masalar düzenli mi?
"""
}

SIPARIS_MESAJ = {
    "kolaci": "🥤 Kolacı Siparişi (Manuel)",
    "biraci": "🍺 Biracı Siparişi (Manuel)",
    "rakici": "🥃 Rakıcı Siparişi (Manuel)",
}

# =========================
# YARDIMCI: sadece özelden
# =========================

def is_private(update: Update) -> bool:
    return bool(update.effective_chat and update.effective_chat.type == "private")

# =========================
# OTOMATİK JOB FONKSİYONLARI
# =========================

async def checklist_job(context: ContextTypes.DEFAULT_TYPE):
    key = context.job.data
    await context.bot.send_message(chat_id=GROUP_ID, text=checklists[key])

async def siparis_job(context: ContextTypes.DEFAULT_TYPE):
    mesaj = context.job.data
    await context.bot.send_message(chat_id=GROUP_ID, text=mesaj)

async def odeme_job(context: ContextTypes.DEFAULT_TYPE):
    mesaj = context.job.data
    await context.bot.send_message(chat_id=GROUP_ID, text=f"🔔 ÖDEME ZAMANI\n\n💳 {mesaj}")

# =========================
# KOMUTLAR (SADECE ÖZELDEN)
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_private(update):
        return
    await update.message.reply_text("🤖 Operasyon Bot Aktif ✅\nKomutlar için /panel")

async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_private(update):
        return
    await update.message.reply_text(
        "📌 TÜM KOMUTLAR\n\n"
        "/start → Botu başlat\n"
        "/panel → Komut listesini göster\n"
        "/id → ID'leri göster (chat/user)\n\n"
        "MANUEL CHECKLIST (gruba gönderir):\n"
        "/c12 /c14 /c17 /c20 /c23\n\n"
        "MANUEL SİPARİŞ (gruba gönderir):\n"
        "/kolaci /biraci /rakici\n\n"
        "ÖDEME HATIRLATICI:\n"
        "/odeme 25 Kredi Kartı → Her ayın 25'i 10:00\n\n"
        "YÖNETİCİ:\n"
        "/reset → (Sadece Müdür) ödeme hatırlatmalarını temizler"
    )

async def id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # İstediğin gibi: özelden yazınca tüm ID'leri gösterelim
    if not is_private(update):
        return
    user_id = update.effective_user.id if update.effective_user else None
    chat_id = update.effective_chat.id if update.effective_chat else None

    await update.message.reply_text(
        f"🆔 ID Bilgileri\n\n"
        f"👤 User ID: {user_id}\n"
        f"💬 Bu chat ID: {chat_id}\n"
        f"👥 Grup ID (ayar): {GROUP_ID}\n"
    )

async def manual_checklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_private(update):
        return

    cmd = update.message.text.lstrip("/").split("@")[0].lower()
    mapping = {"c12": "12", "c14": "14", "c17": "17", "c20": "20", "c23": "23"}
    key = mapping.get(cmd)
    if not key:
        await update.message.reply_text("Geçersiz komut.")
        return

    await context.bot.send_message(chat_id=GROUP_ID, text=checklists[key])
    await update.message.reply_text(f"✅ {key}:00 checklist gruba gönderildi.")

async def manual_siparis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_private(update):
        return

    cmd = update.message.text.lstrip("/").split("@")[0].lower()
    if cmd not in SIPARIS_MESAJ:
        await update.message.reply_text("Geçersiz sipariş komutu.")
        return

    await context.bot.send_message(chat_id=GROUP_ID, text=SIPARIS_MESAJ[cmd])
    await update.message.reply_text("✅ Sipariş mesajı gruba gönderildi.")

async def odeme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_private(update):
        return

    if len(context.args) < 2:
        await update.message.reply_text("Kullanım: /odeme 25 Kredi Kartı")
        return

    try:
        gun = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Gün sayısı sayı olmalı. Örn: /odeme 25 Kredi Kartı")
        return

    if not (1 <= gun <= 28):
        await update.message.reply_text("Gün 1 ile 28 arasında olmalı (ay farklarından dolayı).")
        return

    aciklama = " ".join(context.args[1:]).strip()
    if not aciklama:
        await update.message.reply_text("Açıklama yaz. Örn: /odeme 25 Kredi Kartı")
        return

    job_name = f"odeme_{gun}"
    for j in context.job_queue.jobs():
        if j.name == job_name:
            j.schedule_removal()

    context.job_queue.run_monthly(
        odeme_job,
        when=time(10, 0, tzinfo=TZ),  # TR 10:00
        day=gun,
        data=aciklama,
        name=job_name
    )

    await context.bot.send_message(
        chat_id=GROUP_ID,
        text=f"📝 YENİ ÖDEME PLANLANDI\n\n📅 Her ayın {gun}. günü\n🕒 10:00 (TR)\n💳 {aciklama}"
    )

    await update.message.reply_text(f"✅ Ödeme hatırlatma kuruldu. (Her ay {gun} - 10:00 TR)")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_private(update):
        return

    if update.effective_user.id != MUDUR_ID:
        await update.message.reply_text("⛔ Bu komutu sadece müdür kullanabilir.")
        return

    removed = 0
    for j in context.job_queue.jobs():
        if j.name and j.name.startswith("odeme_"):
            j.schedule_removal()
            removed += 1

    await update.message.reply_text(f"🔄 Ödeme hatırlatmalar temizlendi. (Silinen: {removed})")

# =========================
# MAIN
# =========================

def main():
    app = Application.builder().token(TOKEN).build()
    job_queue = app.job_queue

    # Otomatik günlük checklistler (TR saati)
    job_queue.run_daily(checklist_job, time(12, 0, tzinfo=TZ), data="12", name="chk_12")
    job_queue.run_daily(checklist_job, time(14, 0, tzinfo=TZ), data="14", name="chk_14")
    job_queue.run_daily(checklist_job, time(17, 0, tzinfo=TZ), data="17", name="chk_17")
    job_queue.run_daily(checklist_job, time(20, 0, tzinfo=TZ), data="20", name="chk_20")
    job_queue.run_daily(checklist_job, time(23, 0, tzinfo=TZ), data="23", name="chk_23")

    # Otomatik sipariş günleri (TR saati)
    job_queue.run_daily(siparis_job, time(11, 0, tzinfo=TZ), days=(6,), data="🥤 Pazar - Kolacı Siparişi", name="sip_kolaci")
    job_queue.run_daily(siparis_job, time(11, 0, tzinfo=TZ), days=(0,), data="🍺 Pazartesi - Biracı Siparişi", name="sip_biraci")
    job_queue.run_daily(siparis_job, time(11, 0, tzinfo=TZ), days=(2,), data="🥃 Çarşamba - Rakıcı Siparişi", name="sip_rakici")

    # Komutlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", panel))
    app.add_handler(CommandHandler("id", id))
    app.add_handler(CommandHandler("odeme", odeme))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler(["c12", "c14", "c17", "c20", "c23"], manual_checklist))
    app.add_handler(CommandHandler(["kolaci", "biraci", "rakici"], manual_siparis))

    print("Bot Türkiye saatine göre çalışıyor 🇹🇷")
    app.run_polling()

if __name__ == "__main__":
    main()
