import json
import os
from zoneinfo import ZoneInfo
from datetime import time

from telegram import Update
from telegram.constants import ChatType
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

TOKEN = "7729207035:AAHongvrXncUYv5lih9EnUk7URq_UQTle6I"
MUDUR_ID = 1753344846
TZ = ZoneInfo("Europe/Istanbul")

CONFIG_FILE = "group_config.json"


# ----------------- CONFIG -----------------

def load_group_id() -> int | None:
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            gid = data.get("group_id")
            return int(gid) if gid is not None else None
    except Exception:
        return None


def save_group_id(group_id: int) -> None:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"group_id": int(group_id)}, f, ensure_ascii=False, indent=2)


def is_private(update: Update) -> bool:
    return bool(update.effective_chat and update.effective_chat.type == "private")


async def safe_send_to_saved_group(context: ContextTypes.DEFAULT_TYPE, user_chat_id: int, text: str):
    group_id = load_group_id()
    if not group_id:
        await context.bot.send_message(
            chat_id=user_chat_id,
            text="❌ Kayıtlı grup yok.\nBotu gruba ekle veya grupta /setgroup yaz."
        )
        return False

    try:
        await context.bot.send_message(chat_id=group_id, text=text)
        return True
    except Exception as e:
        await context.bot.send_message(chat_id=user_chat_id, text=f"❌ Gruba gönderemedim.\nHata: {e}")
        return False


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

SIPARIS_MESAJ = {
    "kolaci": "🥤 Kolacı Siparişi (Manuel)",
    "biraci": "🍺 Biracı Siparişi (Manuel)",
    "rakici": "🥃 Rakıcı Siparişi (Manuel)",
}


# =========================
# GRUP KAYDETME
# =========================

async def on_any_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Bot gruba eklendiğinde ya da grupta ilk mesajı gördüğünde grup ID'yi kaydeder.
    """
    chat = update.effective_chat
    if not chat:
        return

    if chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        current = load_group_id()
        if current != chat.id:
            save_group_id(chat.id)
            await context.bot.send_message(
                chat_id=chat.id,
                text="✅ Bu grup kaydedildi.\nArtık özelden yazdığın komutların çıktısı buraya düşecek."
            )


async def setgroup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Grupta yazılırsa kesin olarak o grubu kaydeder.
    Sadece müdür kullanabilir (istersen kaldırırım).
    """
    chat = update.effective_chat
    if not chat:
        return

    if update.effective_user.id != MUDUR_ID:
        return

    if chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        await update.message.reply_text("Bu komut grupta kullanılmalı.")
        return

    save_group_id(chat.id)
    await update.message.reply_text("✅ Grup kaydedildi.")


# =========================
# KOMUTLAR
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_private(update):
        return
    await update.message.reply_text("🤖 Operasyon Bot Aktif ✅\nKomutlar için /panel")


async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_private(update):
        return
    gid = load_group_id()
    await update.message.reply_text(
        "📌 TÜM KOMUTLAR\n\n"
        "/start → Botu başlat\n"
        "/panel → Komut listesi\n"
        "/id → ID bilgileri\n"
        "/testgrup → Gruba test mesajı\n\n"
        "MANUEL CHECKLIST:\n"
        "/c12 /c14 /c17 /c20 /c23\n\n"
        "MANUEL SİPARİŞ:\n"
        "/kolaci /biraci /rakici\n\n"
        "ÖDEME:\n"
        "/odeme 25 Kredi Kartı\n\n"
        f"✅ Kayıtlı Grup ID: {gid if gid else 'YOK'}\n"
        "Grup kaydetmek için botu gruba ekle veya grupta /setgroup yaz."
    )


async def id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_private(update):
        return
    await update.message.reply_text(
        f"🆔 ID Bilgileri\n\n"
        f"👤 User ID: {update.effective_user.id}\n"
        f"💬 Bu chat ID: {update.effective_chat.id}\n"
        f"👥 Kayıtlı Grup ID: {load_group_id()}\n"
    )


async def testgrup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_private(update):
        return
    ok = await safe_send_to_saved_group(context, update.effective_chat.id, "✅ Test: Bot gruba mesaj atabiliyor.")
    if ok:
        await update.message.reply_text("✅ Test başarılı: Mesaj gruba gitti.")


async def manual_checklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_private(update):
        return

    cmd = update.message.text.lstrip("/").split("@")[0].lower()
    mapping = {"c12": "12", "c14": "14", "c17": "17", "c20": "20", "c23": "23"}
    key = mapping.get(cmd)
    if not key:
        return

    ok = await safe_send_to_saved_group(context, update.effective_chat.id, checklists[key])
    if ok:
        await update.message.reply_text(f"✅ {key}:00 checklist gruba gönderildi.")


async def manual_siparis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_private(update):
        return

    cmd = update.message.text.lstrip("/").split("@")[0].lower()
    if cmd not in SIPARIS_MESAJ:
        return

    ok = await safe_send_to_saved_group(context, update.effective_chat.id, SIPARIS_MESAJ[cmd])
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

    await safe_send_to_saved_group(
        context,
        update.effective_chat.id,
        f"📝 YENİ ÖDEME PLANLANDI\n\n📅 Her ayın {gun}. günü\n🕒 10:00 (TR)\n💳 {aciklama}"
    )
    await update.message.reply_text(f"✅ Ödeme hatırlatma kuruldu. (Her ay {gun} - 10:00 TR)")


async def odeme_job(context: ContextTypes.DEFAULT_TYPE):
    mesaj = context.job.data
    group_id = load_group_id()
    if group_id:
        await context.bot.send_message(chat_id=group_id, text=f"🔔 ÖDEME ZAMANI\n\n💳 {mesaj}")


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
# JOBS
# =========================

async def checklist_job(context: ContextTypes.DEFAULT_TYPE):
    key = context.job.data
    group_id = load_group_id()
    if group_id:
        await context.bot.send_message(chat_id=group_id, text=checklists[key])


async def siparis_job(context: ContextTypes.DEFAULT_TYPE):
    mesaj = context.job.data
    group_id = load_group_id()
    if group_id:
        await context.bot.send_message(chat_id=group_id, text=mesaj)


# =========================
# MAIN
# =========================

def main():
    app = Application.builder().token(TOKEN).build()
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
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", panel))
    app.add_handler(CommandHandler("id", id_cmd))
    app.add_handler(CommandHandler("testgrup", testgrup))
    app.add_handler(CommandHandler("odeme", odeme))
    app.add_handler(CommandHandler("reset", reset))

    app.add_handler(CommandHandler("setgroup", setgroup))
    app.add_handler(CommandHandler(["c12", "c14", "c17", "c20", "c23"], manual_checklist))
    app.add_handler(CommandHandler(["kolaci", "biraci", "rakici"], manual_siparis))

    # Grup ID otomatik yakalama (gruptaki herhangi bir mesajı görünce kaydeder)
    app.add_handler(MessageHandler(filters.ChatType.GROUPS, on_any_group_message))

    app.run_polling()

if __name__ == "__main__":
    main()
