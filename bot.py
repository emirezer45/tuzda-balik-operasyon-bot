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

def is_private(update: Update) -> bool:
    return bool(update.effective_chat and update.effective_chat.type == "private")

# ---- Güvenli gönderim: hata olursa özelden yaz ----
async def grupid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Grup ID: {update.effective_chat.id}")
async def safe_send_to_group(context: ContextTypes.DEFAULT_TYPE, user_chat_id: int, text: str):
    try:
        await context.bot.send_message(chat_id=GROUP_ID, text=text)
        return True, None
    except Exception as e:
        # hatayı kullanıcıya dm at
        try:
            await context.bot.send_message(chat_id=user_chat_id, text=f"❌ Gruba gönderemedim.\nHata: {e}")
        except:
            pass
        return False, str(e)

# =========================
# JOB FONKSİYONLARI
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
        "/id → ID'leri göster\n"
        "/testgrup → Gruba mesaj testi\n\n"
        "MANUEL CHECKLIST:\n"
        "/c12 /c14 /c17 /c20 /c23\n\n"
        "MANUEL SİPARİŞ:\n"
        "/kolaci /biraci /rakici\n\n"
        "ÖDEME:\n"
        "/odeme 25 Kredi Kartı\n\n"
        "YÖNETİCİ:\n"
        "/reset (Sadece Müdür)"
    )

async def id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_private(update):
        return
    await update.message.reply_text(
        f"🆔 ID Bilgileri\n\n"
        f"👤 User ID: {update.effective_user.id}\n"
        f"💬 Bu chat ID: {update.effective_chat.id}\n"
        f"👥 Grup ID (ayar): {GROUP_ID}\n"
    )

# >>> TEŞHİS KOMUTU
async def testgrup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_private(update):
        return
    ok, err = await safe_send_to_group(
        context,
        user_chat_id=update.effective_chat.id,
        text="✅ Test: Bot gruba mesaj atabiliyor."
    )
    if ok:
        await update.message.reply_text("✅ Test başarılı: Mesaj gruba gitti.")
    else:
        await update.message.reply_text("❌ Test başarısız. Hata mesajını yukarıda attım.")

async def manual_checklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_private(update):
        return

    cmd = update.message.text.lstrip("/").split("@")[0].lower()
    mapping = {"c12": "12", "c14": "14", "c17": "17", "c20": "20", "c23": "23"}
    key = mapping.get(cmd)
    if not key:
        await update.message.reply_text("Geçersiz komut.")
        return

    ok, _ = await safe_send_to_group(context, update.effective_chat.id, checklists[key])
    if ok:
        await update.message.reply_text(f"✅ {key}:00 checklist gruba gönderildi.")

async def manual_siparis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_private(update):
        return

    cmd = update.message.text.lstrip("/").split("@")[0].lower()
    if cmd not in SIPARIS_MESAJ:
        await update.message.reply_text("Geçersiz sipariş komutu.")
        return

    ok, _ = await safe_send_to_group(context, update.effective_chat.id, SIPARIS_MESAJ[cmd])
    if ok:
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
        await update.message.reply_text("Gün 1 ile 28 arasında olmalı.")
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
        when=time(10, 0, tzinfo=TZ),
        day=gun,
        data=aciklama,
        name=job_name
    )

    await safe_send_to_group(
        context,
        update.effective_chat.id,
        f"📝 YENİ ÖDEME PLANLANDI\n\n📅 Her ayın {gun}. günü\n🕒 10:00 (TR)\n💳 {aciklama}"
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

def main():
    job_queue = app.job_queue

    # Otomatik günlük checklistler
    job_queue.run_daily(checklist_job, time(12, 0, tzinfo=TZ), data="12", name="chk_12")
    job_queue.run_daily(checklist_job, time(14, 0, tzinfo=TZ), data="14", name="chk_14")
    job_queue.run_daily(checklist_job, time(17, 0, tzinfo=TZ), data="17", name="chk_17")
    job_queue.run_daily(checklist_job, time(20, 0, tzinfo=TZ), data="20", name="chk_20")
    job_queue.run_daily(checklist_job, time(23, 0, tzinfo=TZ), data="23", name="chk_23")

    # Otomatik sipariş günleri
    job_queue.run_daily(siparis_job, time(11, 0, tzinfo=TZ), days=(6,), data="🥤 Pazar - Kolacı Siparişi", name="sip_kolaci")
    job_queue.run_daily(siparis_job, time(11, 0, tzinfo=TZ), days=(0,), data="🍺 Pazartesi - Biracı Siparişi", name="sip_biraci")
    job_queue.run_daily(siparis_job, time(11, 0, tzinfo=TZ), days=(2,), data="🥃 Çarşamba - Rakıcı Siparişi", name="sip_rakici")

    # Komutlar
   app.add_handler(CommandHandler("grupid", grupid))
 app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", panel))
    app.add_handler(CommandHandler("id", id))
    app.add_handler(CommandHandler("testgrup", testgrup))
    app.add_handler(CommandHandler("odeme", odeme))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler(["c12", "c14", "c17", "c20", "c23"], manual_checklist))
    app.add_handler(CommandHandler(["kolaci", "biraci", "rakici"], manual_siparis))

    app.run_polling()

if __name__ == "__main__":
    main()
