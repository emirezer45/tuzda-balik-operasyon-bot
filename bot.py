import json
from zoneinfo import ZoneInfo
from datetime import time
from typing import Dict, Tuple

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatType
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

TOKEN = "7729207035:AAFaa8pzRsfoPOabBhfJOnquGsXH2HkMGdk"  
MUDUR_ID = 1753344846
TZ = ZoneInfo("Europe/Istanbul")

CONFIG_FILE = "group_config.json"

# =========================
# CHECKLIST MADDELERİ
# =========================
CHECKLIST_ITEMS = {
    "12": [
        "POS cihazları şarja takıldı mı?",
        "Kasa açıldı mı?",
        "Faturalar sisteme işlendi mi?",
        "Temizlik kontrolü yapıldı mı?",
    ],
    "14": [
        "Eksikler sipariş edildi mi?",
        "Rezervasyonlar kontrol edildi mi?",
        "Faturalar sisteme işlendi mi?",
        "Eksikler tamamlandı mı?",
    ],
    "17": [
        "Servis öncesi son kontrol yapıldı mı?",
        "Personel zamanında geldi mi?",
        "Kasa aktif mi?",
        "Giderler yazıldı mı?",
        "Şirket telefonu cevaplandı mı?",
    ],
    "20": [
        "Problem varsa bildirildi mi?",
        "Paket sistemleri aktif mi?",
        "İşleyiş düzgün mü?",
        "Kasa kontrol edildi mi?",
    ],
    "23": [
        "Paketler sisteme girildi mi?",
        "Z raporları alındı mı?",
        "Gelir gider yazıldı mı?",
        "POS şarja takıldı mı?",
        "Kasa düzenli mi?",
        "Alarm kuruldu mu?",
        "Camlar kapalı mı?",
        "Işıklar kapalı mı?",
        "Masalar düzenli mi?",
    ],
}

SIPARIS_MESAJ = {
    "kolaci": "🥤 Kolacı Siparişi",
    "biraci": "🍺 Biracı Siparişi",
    "rakici": "🥃 Rakıcı Siparişi",
}

# =========================
# GROUP ID KAYIT
# =========================

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

# =========================
# CHECKLIST STATE (RAM)
# =========================
# key: (chat_id, message_id) -> {"key": "12", "done": {index: "isim"}}
CHECKLIST_STATE: Dict[Tuple[int, int], Dict] = {}

def build_checklist_text(key: str, done: Dict[int, str]) -> str:
    items = CHECKLIST_ITEMS[key]
    total = len(items)
    completed = len(done)
    percent = int((completed / total) * 100) if total else 0

    title = f"🕛 {key}:00 Checklist"
    lines = [title, "", f"Tamamlanma: %{percent}", ""]
    for i, item in enumerate(items):
        if i in done:
            lines.append(f"✅ {item} — {done[i]}")
        else:
            lines.append(f"⬜ {item}")
    return "\n".join(lines)

def build_checklist_keyboard(key: str, message_id: int, done: Dict[int, str]) -> InlineKeyboardMarkup:
    items = CHECKLIST_ITEMS[key]
    keyboard = []
    for i in range(len(items)):
        mark = "✅" if i in done else "⬜"
        # kısa buton etiketi
        btn_text = f"{mark} {i+1}"
        cb = f"chk|{key}|{i}|{message_id}"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=cb)])
    return InlineKeyboardMarkup(keyboard)

async def send_checklist_to_group(context: ContextTypes.DEFAULT_TYPE, user_chat_id: int, key: str):
    group_id = load_group_id()
    if not group_id:
        await context.bot.send_message(
            chat_id=user_chat_id,
            text="❌ Kayıtlı grup yok.\nBotu gruba ekle ve grupta bir mesaj yazılsın (otomatik kaydeder) veya grupta /setgroup yaz."
        )
        return

    done: Dict[int, str] = {}
    text = build_checklist_text(key, done)

    msg = await context.bot.send_message(chat_id=group_id, text=text)
    CHECKLIST_STATE[(group_id, msg.message_id)] = {"key": key, "done": done}

    # mesaj id’yi callback_data’ya yazabilmek için mesajdan sonra keyboard ekliyoruz (edit)
    kb = build_checklist_keyboard(key, msg.message_id, done)
    await context.bot.edit_message_reply_markup(chat_id=group_id, message_id=msg.message_id, reply_markup=kb)

# =========================
# GRUPTA ID OTOMATİK YAKALAMA
# =========================

async def on_any_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    chat = update.effective_chat
    if not chat or not update.effective_user:
        return

    if update.effective_user.id != MUDUR_ID:
        return

    if chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        return

    save_group_id(chat.id)
    await update.message.reply_text("✅ Grup kaydedildi.")

# =========================
# CALLBACK (BUTON TIKLAMA)
# =========================

async def on_checklist_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    await query.answer()
    data = query.data or ""
    # chk|12|0|12345
    try:
        _, key, idx_str, msgid_str = data.split("|")
        idx = int(idx_str)
        msgid = int(msgid_str)
    except Exception:
        return

    chat_id = query.message.chat_id if query.message else None
    if chat_id is None:
        return

    state = CHECKLIST_STATE.get((chat_id, msgid))
    if not state or state.get("key") != key:
        await query.answer("Bu checklist eski / bot yeniden başladı.", show_alert=True)
        return

    done: Dict[int, str] = state["done"]
    if idx in done:
        await query.answer("Zaten işaretlenmiş ✅", show_alert=True)
        return

    user_name = query.from_user.first_name or "Bilinmiyor"
    done[idx] = user_name

    new_text = build_checklist_text(key, done)
    new_kb = build_checklist_keyboard(key, msgid, done)

    await query.edit_message_text(new_text, reply_markup=new_kb)

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
    gid = load_group_id()
    await update.message.reply_text(
        "📌 TÜM KOMUTLAR\n\n"
        "/start → Botu başlat\n"
        "/panel → Komut listesi\n"
        "/id → ID bilgileri\n"
        "/testgrup → Gruba test mesajı\n\n"
        "MANUEL CHECKLIST (butonlu):\n"
        "/c12 /c14 /c17 /c20 /c23\n\n"
        "MANUEL SİPARİŞ:\n"
        "/kolaci /biraci /rakici\n\n"
        "YÖNETİCİ:\n"
        "/reset → (Sadece Müdür) ödeme hatırlatmaları temizler\n\n"
        f"✅ Kayıtlı Grup ID: {gid if gid else 'YOK'}"
    )

async def id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_private(update):
        return
    gid = load_group_id()
    await update.message.reply_text(
        f"🆔 ID Bilgileri\n\n"
        f"👤 User ID: {update.effective_user.id}\n"
        f"💬 Bu chat ID: {update.effective_chat.id}\n"
        f"👥 Kayıtlı Grup ID: {gid}\n"
    )

async def testgrup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_private(update):
        return
    gid = load_group_id()
    if not gid:
        await update.message.reply_text("❌ Kayıtlı grup yok. Botu gruba ekle ve grupta bir mesaj yaz.")
        return
    try:
        await context.bot.send_message(chat_id=gid, text="✅ Test: Bot gruba mesaj atabiliyor.")
        await update.message.reply_text("✅ Test başarılı.")
    except Exception as e:
        await update.message.reply_text(f"❌ Test başarısız. Hata: {e}")

async def manual_checklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_private(update):
        return
    cmd = update.message.text.lstrip("/").split("@")[0].lower()
    mapping = {"c12": "12", "c14": "14", "c17": "17", "c20": "20", "c23": "23"}
    key = mapping.get(cmd)
    if not key:
        return
    await send_checklist_to_group(context, update.effective_chat.id, key)

async def manual_siparis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_private(update):
        return
    cmd = update.message.text.lstrip("/").split("@")[0].lower()
    if cmd not in SIPARIS_MESAJ:
        return
    gid = load_group_id()
    if not gid:
        await update.message.reply_text("❌ Kayıtlı grup yok. Botu gruba ekle ve grupta mesaj yaz.")
        return
    await context.bot.send_message(chat_id=gid, text=SIPARIS_MESAJ[cmd])
    await update.message.reply_text("✅ Sipariş mesajı gruba gönderildi.")

# =========================
# ÖDEME (İstersen sonra ekleriz)
# RESET SADECE ÖRNEK: ödeme joblarını silmek için isim bazlı yapıyorduk
# =========================

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
# OTOMATİK JOB: CHECKLIST
# =========================

async def checklist_job(context: ContextTypes.DEFAULT_TYPE):
    key = context.job.data
    gid = load_group_id()
    if not gid:
        return

    # butonlu checklist gönder
    done: Dict[int, str] = {}
    text = build_checklist_text(key, done)
    msg = await context.bot.send_message(chat_id=gid, text=text)
    CHECKLIST_STATE[(gid, msg.message_id)] = {"key": key, "done": done}
    kb = build_checklist_keyboard(key, msg.message_id, done)
    await context.bot.edit_message_reply_markup(chat_id=gid, message_id=msg.message_id, reply_markup=kb)

async def siparis_job(context: ContextTypes.DEFAULT_TYPE):
    gid = load_group_id()
    if not gid:
        return
    await context.bot.send_message(chat_id=gid, text=context.job.data)

# =========================
# MAIN
# =========================

def main():
    app = Application.builder().token(TOKEN).build()
    job_queue = app.job_queue

    # otomatik checklistler (TR saati)
    for k in ["12", "14", "17", "20", "23"]:
        job_queue.run_daily(checklist_job, time(int(k), 0, tzinfo=TZ), data=k, name=f"chk_{k}")

    # otomatik sipariş günleri (TR saati)
    job_queue.run_daily(siparis_job, time(11, 0, tzinfo=TZ), days=(6,), data="🥤 Pazar - Kolacı Siparişi", name="sip_kolaci")
    job_queue.run_daily(siparis_job, time(11, 0, tzinfo=TZ), days=(0,), data="🍺 Pazartesi - Biracı Siparişi", name="sip_biraci")
    job_queue.run_daily(siparis_job, time(11, 0, tzinfo=TZ), days=(2,), data="🥃 Çarşamba - Rakıcı Siparişi", name="sip_rakici")

    # grup id otomatik yakala
    app.add_handler(MessageHandler(filters.ChatType.GROUPS, on_any_group_message))
    app.add_handler(CommandHandler("setgroup", setgroup))

    # komutlar (özelden)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("panel", panel))
    app.add_handler(CommandHandler("id", id_cmd))
    app.add_handler(CommandHandler("testgrup", testgrup))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler(["c12", "c14", "c17", "c20", "c23"], manual_checklist))
    app.add_handler(CommandHandler(["kolaci", "biraci", "rakici"], manual_siparis))

    # buton handler
    app.add_handler(CallbackQueryHandler(on_checklist_button, pattern=r"^chk\|"))

    app.run_polling()

if __name__ == "__main__":
    main()
