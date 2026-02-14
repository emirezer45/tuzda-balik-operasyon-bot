from datetime import time
import logging
import sqlite3
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os

TOKEN = os.getenv("TOKEN")
GROUP_ID = -5143299793

logging.basicConfig(level=logging.INFO)

conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

# DATABASE
cursor.execute("CREATE TABLE IF NOT EXISTS odemeler (isim TEXT, tutar REAL, vade TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS ciro (tarih TEXT, tutar REAL)")
cursor.execute("CREATE TABLE IF NOT EXISTS rezervasyon (isim TEXT, saat TEXT)")
conn.commit()

# YETKI
def yetkili(update):
    return update.effective_chat.id == GROUP_ID

async def checklist_12(context):
    await context.bot.send_message(chat_id=GROUP_ID, text="12:00 Açılış Checklist")

async def checklist_14(context):
    await context.bot.send_message(chat_id=GROUP_ID, text="14:00 Kasa Checklist")

async def checklist_15(context):
    await context.bot.send_message(chat_id=GROUP_ID, text="15:00 Temizlik Checklist")

async def checklist_19(context):
    await context.bot.send_message(chat_id=GROUP_ID, text="19:00 Servis Checklist")

async def checklist_23(context):
    await context.bot.send_message(chat_id=GROUP_ID, text="23:00 Kasa Kontrol Checklist")
# KOMUTLAR
async def odeme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not yetkili(update): return
    isim = context.args[0]
    tutar = float(context.args[1])
    vade = context.args[2]
    cursor.execute("INSERT INTO odemeler VALUES (?,?,?)", (isim,tutar,vade))
    conn.commit()
    await update.message.reply_text("Ödeme kaydedildi.")

async def odemeler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not yetkili(update): return
    cursor.execute("SELECT * FROM odemeler")
    rows = cursor.fetchall()
    text = "Ödemeler:\n"
    for r in rows:
        text += f"{r[0]} - {r[1]} TL - {r[2]}\n"
    await update.message.reply_text(text)

async def ciro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not yetkili(update): return
    tutar = float(context.args[0])
    tarih = datetime.now().strftime("%d-%m-%Y")
    cursor.execute("INSERT INTO ciro VALUES (?,?)",(tarih,tutar))
    conn.commit()
    await update.message.reply_text("Ciro kaydedildi.")

async def rezervasyon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not yetkili(update): return
    isim = context.args[0]
    saat = context.args[1]
    cursor.execute("INSERT INTO rezervasyon VALUES (?,?)",(isim,saat))
    conn.commit()
    await update.message.reply_text("Rezervasyon eklendi.")

async def rezervasyonlar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not yetkili(update): return
    cursor.execute("SELECT * FROM rezervasyon")
    rows = cursor.fetchall()
    text = "Rezervasyonlar:\n"
    for r in rows:
        text += f"{r[0]} - {r[1]}\n"
    await update.message.reply_text(text)

async def hatirlat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not yetkili(update): return
    dakika = int(context.args[0])
    mesaj = " ".join(context.args[1:])
    context.job_queue.run_once(lambda c: c.bot.send_message(chat_id=GROUP_ID,text=mesaj), dakika*60)
    await update.message.reply_text("Hatırlatma kuruldu.")

# OTOMATIK Vade Kontrol
async def vade_kontrol(context):
    bugun = datetime.now().strftime("%d-%m-%Y")
    cursor.execute("SELECT * FROM odemeler WHERE vade=?", (bugun,))
    rows = cursor.fetchall()
    for r in rows:
        await context.bot.send_message(chat_id=GROUP_ID,text=f"BUGÜN VADE: {r[0]} - {r[1]} TL")

 async def zamanlayici(application):

    application.job_queue.run_daily(checklist_12, time=time(hour=12, minute=0))
    application.job_queue.run_daily(checklist_14, time=time(hour=14, minute=0))
    application.job_queue.run_daily(checklist_15, time=time(hour=15, minute=0))
    application.job_queue.run_daily(checklist_19, time=time(hour=19, minute=0))
    application.job_queue.run_daily(checklist_23, time=time(hour=23, minute=0))

    application.job_queue.run_repeating(vade_kontrol, interval=3600, first=10)

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("odeme", odeme))
    app.add_handler(CommandHandler("odemeler", odemeler))
    app.add_handler(CommandHandler("ciro", ciro))
    app.add_handler(CommandHandler("rezervasyon", rezervasyon))
    app.add_handler(CommandHandler("rezervasyonlar", rezervasyonlar))
    app.add_handler(CommandHandler("hatirlat", hatirlat))

    app.post_init = zamanlayici

    app.run_polling()

if __name__ == "__main__":
    main()