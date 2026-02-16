import json
import logging
import os
from zoneinfo import ZoneInfo
from datetime import time, datetime, timedelta
from typing import Dict, Tuple, Optional, Any

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

logging.basicConfig(level=logging.INFO)

# =========================
# AYARLAR
# =========================
TOKEN = "7729207035:AAEW8jA8MqQtGpMzuYGzYrvP_EuPvAgiW3I"
MUDUR_ID = 1753344846
TZ = ZoneInfo("Europe/Istanbul")

CONFIG_FILE = "group_config.json"
REMINDERS_FILE = "reminders.json"

ESCALATE_AFTER_MINUTES = 60  # Ödeme zamanından kaç dk sonra müdüre uyarı

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
# CONFIG (GROUP + PAYMENT PANEL)
# =========================
def load_config() -> Dict[str, Any]:
    # ENV ile GROUP_ID verilirse onu config üzerine bind ederiz
    cfg: Dict[str, Any] = {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f) or {}
    except Exception:
        cfg = {}

    env_gid = os.getenv("GROUP_ID")
    if env_gid:
        try:
            cfg["group_id"] = int(env_gid)
        except Exception:
            pass

    return cfg

def save_config(cfg: Dict[str, Any]) -> None:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def get_group_id() -> Optional[int]:
    cfg = load_config()
    gid = cfg.get("group_id")
    return int(gid) if gid is not None else None

def set_group_id(group_id: int) -> None:
    cfg = load_config()
    cfg["group_id"] = int(group_id)
    save_config(cfg)

def get_payment_panel_message_id() -> Optional[int]:
    cfg = load_config()
    mid = cfg.get("payment_panel_message_id")
    return int(mid) if mid is not None else None

def set_payment_panel_message_id(message_id: int) -> None:
    cfg = load_config()
    cfg["payment_panel_message_id"] = int(message_id)
    save_config(cfg)

def is_private(update: Update) -> bool:
    return bool(update.effective_chat and update.effective_chat.type == "private")

# =========================
# CHECKLIST STATE (RAM)
# =========================
# (chat_id, message_id) -> {"key": "12", "done": {index: "isim"}}
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
        btn_text = f"{mark} {i+1}"
        cb = f"chk|{key}|{i}|{message_id}"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=cb)])
    return InlineKeyboardMarkup(keyboard)

async def send_checklist_to_group(context: ContextTypes.DEFAULT_TYPE, user_chat_id: int, key: str):
    gid = get_group_id()
    if not gid:
        await context.bot.send_message(
            chat_id=user_chat_id,
            text="❌ Kayıtlı grup yok.\nBotu gruba ekle ve grupta bir mesaj yazılsın (otomatik kaydeder) veya grupta /setgroup (müdür)."
        )
        return

    done: Dict[int, str] = {}
    text = build_checklist_text(key, done)
    msg = await context.bot.send_message(chat_id=gid, text=text)
    CHECKLIST_STATE[(gid, msg.message_id)] = {"key": key, "done": done}
    kb = build_checklist_keyboard(key, msg.message_id, done)
    await context.bot.edit_message_reply_markup(chat_id=gid, message_id=msg.message_id, reply_markup=kb)

# =========================
# GRUP ID OTOMATİK YAKALAMA
# =========================
async def on_any_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if not chat:
        return
    if chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        current = get_group_id()
        if current != chat.id:
            set_group_id(chat.id)
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
    set_group_id(chat.id)
    await update.message.reply_text("✅ Grup kaydedildi.")

# =========================
# CHECKLIST BUTON TIKLAMA
# =========================
async def on_checklist_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()

    data = query.data or ""
    try:
        _, key, idx_str, msgid_str = data.split("|")
        idx = int(idx_str)
        msgid = int(msgid_str)
    except Exception:
        return

    if not query.message:
        return

    chat_id = query.message.chat_id
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
# ÖDEME HATIRLATMA + PANEL
# =========================
# id -> {
#   "when_iso": "...",
#   "when_human": "...",
#   "text": "...",
#   "paid": bool,
#   "paid_by": "...",
#   "paid_at": "..."
# }
reminders: Dict[str, Dict[str, Any]] = {}
reminder_counter = 1

def load_reminders():
    global reminders, reminder_counter
    try:
        with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
            reminders = json.load(f) or {}
        if reminders:
            reminder_counter = max(int(k) for k in reminders.keys()) + 1
        else:
            reminder_counter = 1
    except Exception:
        reminders = {}
        reminder_counter = 1

def save_reminders():
    with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(reminders, f, ensure_ascii=False, indent=2)

def payment_keyboard(rid: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ ÖDENDİ", callback_data=f"pay|{rid}")]
    ])

def build_payment_panel_text() -> str:
    lines = ["📌 ÖDEME PANELİ", ""]
    pending = []
    paid = []

    for rid, rem in sorted(reminders.items(), key=lambda x: int(x[0])):
        if rem.get("paid"):
            paid.append((rid, rem))
        else:
            pending.append((rid, rem))

    if not pending and not paid:
        lines.append("Şu an kayıtlı ödeme yok.")
        return "\n".join(lines)

    if pending:
        lines.append("⏳ BEKLEYEN ÖDEMELER")
        for rid, rem in pending:
            lines.append(f"• ID {rid} | {rem.get('when_human')} | {rem.get('text')}")
        lines.append("")

    if paid:
        lines.append("✅ ÖDENENLER")
        for rid, rem in paid:
            lines.append(
                f"• ID {rid} | {rem.get('text')} | Ödeyen: {rem.get('paid_by')} | {rem.get('paid_at')}"
            )

    lines.append("")
    lines.append("Not: Ödeme zamanı gelince ayrıca 🔔 mesajı da düşer.")
    return "\n".join(lines)

def build_payment_panel_keyboard() -> InlineKeyboardMarkup:
    # Panelde sadece bekleyen ödemeler için buton gösterelim
    keyboard = []
    for rid, rem in sorted(reminders.items(), key=lambda x: int(x[0])):
        if not rem.get("paid"):
            keyboard.append([InlineKeyboardButton(f"✅ ÖDENDİ (ID {rid})", callback_data=f"pay|{rid}")])

    if not keyboard:
        keyboard = [[InlineKeyboardButton("✅ Panel Güncel", callback_data="noop")]]

    return InlineKeyboardMarkup(keyboard)

async def ensure_payment_panel(context: ContextTypes.DEFAULT_TYPE) -> Optional[int]:
    """
    Panel mesajı yoksa oluşturur, varsa döner.
    """
    gid = get_group_id()
    if not gid:
        return None

    mid = get_payment_panel_message_id()
    if mid:
        return mid

    msg = await context.bot.send_message(
        chat_id=gid,
        text=build_payment_panel_text(),
        reply_markup=build_payment_panel_keyboard()
    )
    set_payment_panel_message_id(msg.message_id)
    return msg.message_id

async def refresh_payment_panel(context: ContextTypes.DEFAULT_TYPE):
    """
    Panel varsa edit eder. Panel silinmişse yeniden oluşturur.
    """
    gid = get_group_id()
    if not gid:
        return

    mid = await ensure_payment_panel(context)
    if not mid:
        return

    try:
        await context.bot.edit_message_text(
            chat_id=gid,
            message_id=mid,
            text=build_payment_panel_text(),
            reply_markup=build_payment_panel_keyboard()
        )
    except Exception:
        # panel silinmiş olabilir -> yeniden oluştur
        try:
            msg = await context.bot.send_message(
                chat_id=gid,
                text=build_payment_panel_text(),
                reply_markup=build_payment_panel_keyboard()
            )
            set_payment_panel_message_id(msg.message_id)
        except Exception as e:
            logging.warning(f"Panel refresh failed: {e}")

async def send_payment_reminder(context: ContextTypes.DEFAULT_TYPE):
    """
    A seçeneği: ödeme zamanı gelince ayrıca gruba uyarı mesajı at.
    """
    rid = str(context.job.data)
    rem = reminders.get(rid)
    if not rem:
        return
    if rem.get("paid"):
        return

    gid = get_group_id()
    if not gid:
        return

    await ensure_payment_panel(context)
    await refresh_payment_panel(context)

    await context.bot.send_message(
        chat_id=gid,
        text=f"🔔 ÖDEME ZAMANI (ID: {rid})\n\n💳 {rem['text']}\n🕒 {rem['when_human']}\n\nÖdendi ise butona bas ⬇️",
        reply_markup=payment_keyboard(rid)
    )

async def escalate_payment_if_unpaid(context: ContextTypes.DEFAULT_TYPE):
    rid = str(context.job.data)
    rem = reminders.get(rid)
    if not rem:
        return
    if rem.get("paid"):
        return

    try:
        await context.bot.send_message(
            chat_id=MUDUR_ID,
            text=(
                f"🚨 ÖDEME UYARISI (ÖDENMEDİ)\n\n"
                f"ID: {rid}\n"
                f"Zaman: {rem.get('when_human')}\n"
                f"Açıklama: {rem.get('text')}\n\n"
                f"Not: Ödeme mesajında 'ÖDENDİ' işaretlenmedi."
            )
        )
    except Exception as e:
        logging.warning(f"Manager DM failed: {e}")

def schedule_loaded_reminders(job_queue):
    now = datetime.now(TZ)
    for rid, rem in reminders.items():
        try:
            when_dt = datetime.fromisoformat(rem["when_iso"])
            if when_dt.tzinfo is None:
                when_dt = when_dt.replace(tzinfo=TZ)
        except Exception:
            continue

        if when_dt <= now:
            continue

        job_queue.run_once(send_payment_reminder, when=when_dt, data=int(rid), name=f"pay_{rid}")
        esc_time = when_dt + timedelta(minutes=ESCALATE_AFTER_MINUTES)
        job_queue.run_once(escalate_payment_if_unpaid, when=esc_time, data=int(rid), name=f"esc_{rid}")

# =========================
# ÖDEME BUTONU (ÖDENDİ)
# =========================
async def on_payment_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    data = query.data or ""
    if data == "noop":
        await query.answer("✅", show_alert=False)
        return

    await query.answer()
    try:
        _, rid = data.split("|", 1)
    except Exception:
        return

    rem = reminders.get(rid)
    if not rem:
        await query.answer("Bu ödeme kaydı yok / silinmiş.", show_alert=True)
        return

    if rem.get("paid"):
        await query.answer("Zaten ödendi ✅", show_alert=True)
        return

    who = query.from_user.first_name or "Bilinmiyor"
    paid_at = datetime.now(TZ).strftime("%d.%m.%Y %H:%M (TR)")

    rem["paid"] = True
    rem["paid_by"] = who
    rem["paid_at"] = paid_at
    save_reminders()

    # escalation job varsa kaldır
    for j in context.job_queue.jobs():
        if j.name == f"esc_{rid}":
            j.schedule_removal()

    # Paneli güncelle
    await refresh_payment_panel(context)

    # Butonlu uyarı mesajını da edit edelim (mümkünse)
    try:
        await query.edit_message_text(
            f"✅ ÖDEME ÖDENDİ (ID: {rid})\n\n"
            f"💳 {rem['text']}\n"
            f"🕒 Plan: {rem['when_human']}\n\n"
            f"Ödeyen: {who}\n"
            f"Saat: {paid_at}"
        )
    except Exception:
        pass

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
    gid = get_group_id()
    mid = get_payment_panel_message_id()
    await update.message.reply_text(
        "📌 TÜM KOMUTLAR\n\n"
        "/start → Botu başlat\n"
        "/panel → Komut listesi\n"
        "/id → ID bilgileri\n"
        "/testgrup → Gruba test\n\n"
        "MANUEL CHECKLIST (butonlu):\n"
        "/c12 /c14 /c17 /c20 /c23\n\n"
        "MANUEL SİPARİŞ:\n"
        "/kolaci /biraci /rakici\n\n"
        "ÖDEME:\n"
        "/panelodeme → Ödeme panelini gruba sabitle\n"
        "/odeme 25.02.2026 14:30 Kredi Kartı\n"
        "/hatirlatmalar\n"
        "/iptal ID\n\n"
        "YÖNETİCİ:\n"
        "/reset → (Sadece Müdür) tüm ödeme hatırlatmalarını temizler\n\n"
        f"✅ Kayıtlı Grup: {gid if gid else 'YOK'}\n"
        f"📌 Panel Mesaj ID: {mid if mid else 'YOK'}\n"
        f"⏱ Ödenmezse Müdür Uyarı: {ESCALATE_AFTER_MINUTES} dk"
    )

async def id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_private(update):
        return
    gid = get_group_id()
    mid = get_payment_panel_message_id()
    await update.message.reply_text(
        f"🆔 ID Bilgileri\n\n"
        f"User: {update.effective_user.id}\n"
        f"Chat: {update.effective_chat.id}\n"
        f"Kayıtlı Grup: {gid}\n"
        f"Panel Mesaj ID: {mid}\n"
    )

async def testgrup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_private(update):
        return
    gid = get_group_id()
    if not gid:
        await update.message.reply_text("❌ Kayıtlı grup yok. Botu gruba ekle ve grupta bir mesaj yaz.")
        return
    try:
        await context.bot.send_message(chat_id=gid, text="✅ Test: Bot gruba mesaj atabiliyor.")
        await update.message.reply_text("✅ Test başarılı.")
    except Exception as e:
        await update.message.reply_text(f"❌ Test başarısız: {e}")

async def panelodeme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_private(update):
        return
    gid = get_group_id()
    if not gid:
        await update.message.reply_text("❌ Kayıtlı grup yok. Önce botu gruba ekle ve grupta mesaj yaz.")
        return

    await ensure_payment_panel(context)
    await refresh_payment_panel(context)
    await update.message.reply_text("✅ Ödeme paneli gruba sabitlendi/güncellendi.")

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

    gid = get_group_id()
    if not gid:
        await update.message.reply_text("❌ Kayıtlı grup yok. Botu gruba ekle ve grupta mesaj yaz.")
        return

    await context.bot.send_message(chat_id=gid, text=SIPARIS_MESAJ[cmd])
    await update.message.reply_text("✅ Sipariş mesajı gruba gönderildi.")

async def odeme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global reminder_counter
    if not is_private(update):
        return

    # /odeme 25.02.2026 14:30 Kredi Kartı
    if len(context.args) < 3:
        await update.message.reply_text("Kullanım:\n/odeme 25.02.2026 14:30 Kredi Kartı")
        return

    gid = get_group_id()
    if not gid:
        await update.message.reply_text("❌ Kayıtlı grup yok. Önce botu gruba ekle ve grupta mesaj yaz.")
        return

    tarih = context.args[0]
    saat_str = context.args[1]
    aciklama = " ".join(context.args[2:]).strip()

    try:
        when_dt = datetime.strptime(f"{tarih} {saat_str}", "%d.%m.%Y %H:%M").replace(tzinfo=TZ)
    except Exception:
        await update.message.reply_text("Format yanlış.\nÖrn: /odeme 25.02.2026 14:30 Kredi Kartı")
        return

    now = datetime.now(TZ)
    if when_dt <= now:
        await update.message.reply_text("Geçmiş tarih/saat girdin.")
        return

    rid = str(reminder_counter)
    reminder_counter += 1

    reminders[rid] = {
        "when_iso": when_dt.isoformat(),
        "when_human": f"{tarih} {saat_str} (TR)",
        "text": aciklama,
        "paid": False,
        "paid_by": "",
        "paid_at": "",
    }
    save_reminders()

    # Paneli oluştur/güncelle
    await ensure_payment_panel(context)
    await refresh_payment_panel(context)

    # job kur: ödeme zamanı + escalation
    context.job_queue.run_once(send_payment_reminder, when=when_dt, data=int(rid), name=f"pay_{rid}")
    esc_time = when_dt + timedelta(minutes=ESCALATE_AFTER_MINUTES)
    context.job_queue.run_once(escalate_payment_if_unpaid, when=esc_time, data=int(rid), name=f"payment_{rid}"