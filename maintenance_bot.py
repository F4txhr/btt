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
import fcntl, time

from telegram import Update
# PERBAIKAN: Impor ParseMode dari telegram.constants
from telegram.constants import ParseMode 
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- KONFIGURASI ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MAINT_BOT_TOKEN = os.getenv("MAINT_BOT_TOKEN", BOT_TOKEN)
OWNER_ID = int(os.getenv("OWNER_ID", "5361605327"))
NAMA_CHANNEL = os.getenv("CHANNEL_USERNAME", "@todconvert_bot")
MAINT_ALLOWLIST = set(int(x) for x in os.getenv("MAINT_ALLOWLIST", str(OWNER_ID)).split(",") if x.strip().isdigit())
TOKEN_LOCK_FILE = os.getenv("TOKEN_LOCK_FILE", "token.lock")
TOKEN_LOCK_WAIT_SECONDS = int(os.getenv("TOKEN_LOCK_WAIT_SECONDS", "60"))
_token_lock_fd = None

def acquire_token_lock(timeout_seconds: int = TOKEN_LOCK_WAIT_SECONDS) -> bool:
    global _token_lock_fd
    start_time = time.time()
    _token_lock_fd = os.open(TOKEN_LOCK_FILE, os.O_CREAT | os.O_RDWR)
    while True:
        try:
            fcntl.flock(_token_lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                os.ftruncate(_token_lock_fd, 0)
                os.write(_token_lock_fd, str(os.getpid()).encode())
                os.lseek(_token_lock_fd, 0, os.SEEK_SET)
            except Exception:
                pass
            return True
        except Exception:
            if time.time() - start_time > timeout_seconds:
                return False
            time.sleep(0.2)

def release_token_lock():
    global _token_lock_fd
    try:
        if _token_lock_fd is not None:
            try:
                fcntl.flock(_token_lock_fd, fcntl.LOCK_UN)
            except Exception:
                pass
            try:
                os.close(_token_lock_fd)
            except Exception:
                pass
    finally:
        _token_lock_fd = None

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

    # Allowlist bypass info
    if update.effective_user and update.effective_user.id in MAINT_ALLOWLIST:
        bypass_note = "\n\n(Anda berada dalam allowlist maintenance. Jalankan perintah admin di bot utama jika diperlukan.)"
    else:
        bypass_note = ""

    pesan = (
        f"🔧 *MODE PERBAIKAN*\n\n"
        f"Bot sedang dalam proses pemeliharaan dan diperkirakan akan kembali online *{end_time_str}*\\.\n\n"
        f"Untuk info terbaru, silakan bergabung ke channel kami:\n"
        f"➡️ **{NAMA_CHANNEL}** ⬅️"
        f"{bypass_note}"
    )
    if update.message:
        await update.message.reply_text(pesan, parse_mode=ParseMode.MARKDOWN_V2)

async def maintenance_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/status untuk melihat estimasi kapan maintenance selesai."""
    end_time_str = "segera"
    try:
        with open("maintenance_info.json", "r") as f:
            info = json.load(f)
            end_time = datetime.fromisoformat(info.get('end_time'))
            now = datetime.now(timezone.utc)
            if end_time > now:
                remaining = end_time - now
                minutes = int(remaining.total_seconds() // 60)
                secs = int(remaining.total_seconds() % 60)
                end_time_str = f"{minutes}m {secs}s"
    except Exception:
        pass
    await update.message.reply_text(f"Status maintenance: perkiraan selesai dalam {end_time_str}.")

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
    application = Application.builder().token(MAINT_BOT_TOKEN).build()
    # Hapus webhook jika ada, untuk memastikan long polling tidak bentrok dengan webhook
    try:
        await application.bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        logger.warning(f"Gagal menghapus webhook (abaikan jika tidak diset): {e}")
    
    application.add_handler(CommandHandler("status", maintenance_status))
    application.add_handler(CommandHandler("maintenance", maintenance_off_command, filters=filters.User(user_id=list(MAINT_ALLOWLIST))))
    application.add_handler(MessageHandler(filters.ALL & (~filters.User(user_id=list(MAINT_ALLOWLIST))), maintenance_response))

    pid_file = "maintenance_bot.pid"
    # Guard: jika sudah ada proses lama berjalan, jangan start ganda
    def _is_running(pid: int) -> bool:
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
    if os.path.exists(pid_file):
        try:
            with open(pid_file, "r") as f:
                old_pid = int(f.read().strip() or 0)
            if old_pid and _is_running(old_pid):
                logger.error(f"Maintenance bot sudah berjalan dengan PID {old_pid}. Keluar.")
                return
        except Exception:
            pass
        # bersihkan pid file usang
        try: os.remove(pid_file)
        except Exception: pass
    with open(pid_file, "w") as f:
        f.write(str(os.getpid()))

    try:
        await application.initialize()
        await application.start()
        if not acquire_token_lock():
            logger.error("Gagal mengakuisisi token lock untuk maintenance. Keluar.")
            return
        await application.updater.start_polling()
        logger.info("Bot pemeliharaan berjalan. Menunggu sinyal shutdown...")
        await shutdown_event.wait()
    finally:
        logger.info("Memulai shutdown bot pemeliharaan...")
        if application.updater and application.updater.running: await application.updater.stop()
        if application.running: await application.stop()
        await application.shutdown()
        release_token_lock()
        
        for f in [pid_file, "maintenance_info.json", "maintenance_job.json"]:
            if os.path.exists(f): os.remove(f)
        logger.info("Bot pemeliharaan telah dimatikan dan file temporary dibersihkan.")

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, handle_signal)
    try: asyncio.run(main())
    except (KeyboardInterrupt, SystemExit): shutdown_event.set()
