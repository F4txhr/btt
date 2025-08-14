# ======================================================
# ISI LENGKAP FILE: maintenance_bot.py (DENGAN IMPORT YANG BENAR)
# ======================================================

import asyncio
import logging
import os
import signal
import json
import sys
import subprocess
from datetime import datetime, timezone

from telegram import Update
# PERBAIKAN: Impor ParseMode dari telegram.constants
from telegram.constants import ParseMode 
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- KONFIGURASI ---
BOT_TOKEN = "7872111732:AAEbwXGvPVvHZHGSexGDzQRhBu3Axr0cWBQ"
OWNER_ID = 5361605327
NAMA_CHANNEL = "@todconvert_bot"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

shutdown_event = asyncio.Event()

async def maintenance_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Respons standar untuk semua pengguna biasa."""
    end_time_str = "segera"
    try:
        with open("maintenance_info.json", "r") as f:
            info = json.load(f)
            end_time = datetime.fromisoformat(info.get('end_time'))
            now = datetime.now(timezone.utc)
            if end_time > now:
                remaining = end_time - now
                minutes = int(remaining.total_seconds() // 60)
                if minutes > 0:
                    end_time_str = f"sekitar {minutes} menit lagi"
    except Exception: pass

    pesan = (
        f"🔧 *MODE PERBAIKAN*\n\n"
        f"Bot sedang dalam proses pemeliharaan dan diperkirakan akan kembali online *{end_time_str}*\\.\n\n"
        f"Untuk info terbaru, silakan bergabung ke channel kami:\n"
        f"➡️ **{NAMA_CHANNEL}** ⬅️"
    )
    if update.message:
        await update.message.reply_text(pesan, parse_mode=ParseMode.MARKDOWN_V2)

async def maintenance_off_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Perintah KHUSUS OWNER untuk menonaktifkan maintenance."""
    await update.message.reply_text(
        "✅ Sinyal untuk menonaktifkan mode maintenance telah dikirim.\n\n"
        "Bot utama akan kembali online dalam beberapa detik."
    )
    logger.info("Memicu manager.py untuk menonaktifkan mode maintenance...")
    subprocess.Popen(f"{sys.executable} manager.py off", shell=True)

def handle_signal(sig, frame):
    """Menangani sinyal shutdown dari manager.py."""
    logger.info("Menerima sinyal shutdown eksternal untuk bot maintenance...")
    shutdown_event.set()

async def main():
    logger.info("Bot pemeliharaan aktif.")
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("maintenance", maintenance_off_command, filters=filters.User(user_id=OWNER_ID)))
    application.add_handler(MessageHandler(filters.ALL & (~filters.User(user_id=OWNER_ID)), maintenance_response))

    pid_file = "maintenance_bot.pid"
    with open(pid_file, "w") as f: f.write(str(os.getpid()))

    try:
        await application.initialize()
        await application.updater.start_polling()
        await application.start()
        logger.info("Bot pemeliharaan berjalan. Menunggu sinyal shutdown...")
        await shutdown_event.wait()
    finally:
        logger.info("Memulai shutdown bot pemeliharaan...")
        if application.updater and application.updater.running: await application.updater.stop()
        if application.running: await application.stop()
        await application.shutdown()
        
        for f in [pid_file, "maintenance_info.json", "maintenance_job.json"]:
            if os.path.exists(f): os.remove(f)
        logger.info("Bot pemeliharaan telah dimatikan dan file temporary dibersihkan.")

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, handle_signal)
    try: asyncio.run(main())
    except (KeyboardInterrupt, SystemExit): shutdown_event.set()
