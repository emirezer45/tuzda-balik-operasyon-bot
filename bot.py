import pytz
from datetime import time
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

TOKEN = "7729207035:AAEW8jA8MqQtGpMzuYGzYrvP_EuPvAgiW3I"  
GROUP_ID = -51432299793
MUDUR_ID = 1753344846

TZ = pytz.timezone("Europe/Istanbul")

# =========================
# CHECKLISTLER
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

# =========================
# GÖNDERME FONKSİYONU
# =========================

async def checklist_gonder(context: ContextTypes.DEFAULT_TYPE):
    key = context.job.data
    await context.bot.send_message(chat_id=GROUP_ID, text=checklists[key])

# =========================
# SİPARİŞ GÜNLERİ
# =========================

async def siparis_gonder(context: ContextTypes.DEFAULT_TYPE):
    mesaj = context.job.data
    await context.bot.send_message(chat_id=GROUP_ID, text=mesaj)

# =========================
# ÖDEME HATIRLATMA
# =========================

async def odeme_hatirlat(context: ContextTypes.DEFAULT_TYPE):
    mesaj = context.job.data
    await context.bot.send_message(chat_id=GROUP_ID, text=f"💰 ÖDEME HATIRLATMA\n\n{mesaj}")

# =========================
# PANEL KOMUTU
# =========================

async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
📌 BOT KOMUTLARI

/odeme → Ödeme hatırlatma kur
/panel → Komutları göster
""")

# =========================
# ÖDEME KOMUTU
# =========================

async def odeme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Kullanım: /odeme 25 Kredi Kartı")
        return

    gun = int(context.args[0])
    aciklama = " ".join(context.args[1:])

    context.job_queue.run_monthly(
        odeme_hatirlat,
        when=time(10, 0, tzinfo=TZ),
        day=gun,
        data=aciklama,
        name=f"odeme_{gun}"
    )

    await update.message.reply_text("✅ Ödeme hatırlatma kuruldu.")

# =========================
# BOT BAŞLAT
# =========================

def main():
    app = Application.builder().token(TOKEN).build()

    job_queue = app.job_queue

    # Günlük checklist saatleri (Türkiye saati)
    job_queue.run_daily(checklist_gonder, time(12, 0, tzinfo=TZ), data="12")
    job_queue.run_daily(checklist_gonder, time(14, 0, tzinfo=TZ), data="14")
    job_queue.run_daily(checklist_gonder, time(17, 0, tzinfo=TZ), data="17")
    job_queue.run_daily(checklist_gonder, time(20, 0, tzinfo=TZ), data="20")
    job_queue.run_daily(checklist_gonder, time(23, 0, tzinfo=TZ), data="23")

    # Sipariş Günleri (Türkiye saati)
    job_queue.run_daily(siparis_gonder, time(11, 0, tzinfo=TZ), days=(6,), data="🥤 Pazar - Kolacı Siparişi")
    job_queue.run_daily(siparis_gonder, time(11, 0, tzinfo=TZ), days=(0,), data="🍺 Pazartesi - Biracı Siparişi")
    job_queue.run_daily(siparis_gonder, time(11, 0, tzinfo=TZ), days=(2,), data="🥃 Çarşamba - Rakıcı Siparişi")

    app.add_handler(CommandHandler("panel", panel))
    app.add_handler(CommandHandler("odeme", odeme))

    print("Bot Türkiye saatine göre çalışıyor 🇹🇷")
    app.run_polling()

if __name__ == "__main__":
    main()
