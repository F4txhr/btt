#bot.py
import logging
import aiosqlite
import asyncio
import html
import json
import random
import traceback
import telegram
import httpx
import subprocess
import os
import signal
import sys
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from math import radians, cos, sin, asin, sqrt


from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
)
from telegram.constants import ParseMode, ChatAction
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    PicklePersistence,
    JobQueue,
    ApplicationHandlerStop,
)
from collections import deque

# =============================
# CONFIGURATION
# =============================
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", "5361605327"))
DEVELOPER_CHAT_ID = int(os.getenv("DEVELOPER_CHAT_ID", str(OWNER_ID)))

# Global rate limiter config
GLOBAL_RPS = int(os.getenv("GLOBAL_RPS", "25"))
PER_CHAT_DELAY = float(os.getenv("PER_CHAT_DELAY", "1.0"))

# Logger setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Conversation states
( PROFILE_MAIN, P_AGE, P_BIO, P_PHOTO, P_INTERESTS, P_LOCATION, P_MANUAL_INTEREST, P_GENDER,
    SET_FILTER_AGE, SET_FILTER_INTERESTS, SET_FILTER_DISTANCE, SET_FILTER_GENDER,
    QUIZ_QUESTION, QUIZ_ANSWER, CONFIRM_MAINTENANCE
) = range(15)

# Shop items
SHOP_ITEMS = {
    'pro_1_day': {'name': 'Premium - 1 Hari', 'cost': 50, 'duration': timedelta(days=1)},
    'pro_3_day': {'name': 'Premium - 3 Hari', 'cost': 120, 'duration': timedelta(days=3)},
    'pro_7_day': {'name': 'Premium - 1 Minggu', 'cost': 250, 'duration': timedelta(days=7)},
    'pro_1_month': {'name': 'Premium - 1 Bulan', 'cost': 800, 'duration': timedelta(days=30)},
    'pro_1_year': {'name': 'Premium - 1 Tahun', 'cost': 8500, 'duration': timedelta(days=365)},
}

COMMON_INTERESTS = [
    "Musik", "Film", "Gaming", "Olahraga", "Traveling", 
    "Kuliner", "Membaca", "Teknologi", "Seni", "Fotografi",
    "Nongkrong", "Diskusi", "Komedi", "Alam", "Bisnis"
]

shutdown_event = asyncio.Event()

def handle_signal(sig, frame):
    logger.info("Menerima sinyal shutdown eksternal untuk bot utama...")
    shutdown_event.set()


# =============================
# DATABASE FUNCTIONS
# =============================

async def init_db(db):
    """Initialize database tables with a clean and valid SQL query."""
    await db.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            gender TEXT,
            age INTEGER,
            bio TEXT,
            koin INTEGER DEFAULT 0,
            pro_expires_at TEXT,
            karma INTEGER DEFAULT 100,
            profile_pic_id TEXT,
            interests TEXT,
            latitude REAL,
            longitude REAL,
            filter_gender TEXT,
            filter_age_min INTEGER,
            filter_age_max INTEGER,
            filter_interests TEXT,
            filter_distance_km INTEGER
        )
    ''')
    
    await db.execute('''
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            rater_id INTEGER, 
            rated_id INTEGER, 
            rating INTEGER CHECK(rating BETWEEN 1 AND 5), 
            timestamp TEXT
        )
    ''')
    await db.execute('''
        CREATE TABLE IF NOT EXISTS blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            blocker_id INTEGER, 
            blocked_id INTEGER, 
            timestamp TEXT
        )
    ''')
    await db.execute('''
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            question TEXT NOT NULL, 
            answer TEXT NOT NULL
        )
    ''')
    await db.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user1_id INTEGER NOT NULL,
            user2_id INTEGER NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT,
            status TEXT NOT NULL,
            user1_feedback_given INTEGER DEFAULT 0,
            user2_feedback_given INTEGER DEFAULT 0,
            user1_rating INTEGER,
            user2_rating INTEGER
        )
    ''')
    await db.commit()

def get_db(context: ContextTypes.DEFAULT_TYPE) -> aiosqlite.Connection:
    """Get database connection from context"""
    return context.application.db_connection

# =============================
# HELPER FUNCTIONS
# =============================

def parse_time(time_str: str) -> int:
    """Mengubah string waktu (e.g., '10m', '1h') menjadi detik."""
    try:
        unit = time_str[-1].lower()
        value = int(time_str[:-1])
        if unit == 's': return value
        if unit == 'm': return value * 60
        if unit == 'h': return value * 3600
    except (ValueError, IndexError):
        pass
    raise ValueError("Format waktu tidak valid")
    

async def broadcast_job(context: ContextTypes.DEFAULT_TYPE):
    """Job generik untuk mengirim broadcast."""
    job_data = context.job.data
    text_to_send = job_data.get("text")
    if not text_to_send: return
    
    logger.info(f"Menjalankan broadcast job: {text_to_send[:30]}...")
    db = get_db(context)
    all_user_ids = [row[0] for row in await db.execute_fetchall("SELECT user_id FROM user_profiles")]
    if not all_user_ids: return
    
    escaped_text = escape_md(text_to_send)
    await send_broadcast_in_batches(context.bot, all_user_ids, escaped_text, parse_mode=ParseMode.MARKDOWN_V2)
    logger.info(f"Broadcast job ke {len(all_user_ids)} pengguna selesai.")

    
async def trigger_manager_job(context: ContextTypes.DEFAULT_TYPE):
    """Job yang memicu manager.py untuk mode ON atau OFF."""
    mode = context.job.data.get('mode', 'on')
    logger.info(f"Menjalankan job untuk memicu manager.py {mode}")
    subprocess.Popen(f"{sys.executable} manager.py {mode}", shell=True)
    
async def reschedule_maintenance_jobs(application: Application):
    """Membaca file job saat startup dan menjadwalkan ulang jika perlu."""
    try:
        with open("maintenance_job.json", "r") as f:
            job_data = json.load(f)

        now = datetime.now(timezone.utc)

        def schedule_if_future(job_name, callback, run_at_iso, data=None):
            if not run_at_iso:
                return
            target_time = datetime.fromisoformat(run_at_iso)
            if target_time > now:
                delay = (target_time - now).total_seconds()
                application.job_queue.run_once(callback, when=delay, name=job_name, data=data or {})
                logger.info(f"Menjadwalkan ulang job '{job_name}' untuk berjalan dalam {delay:.0f} detik.")

        start_at = job_data.get("start_at")
        end_at = job_data.get("end_at")

        # Derive countdown_at and text if missing
        countdown_at = job_data.get("countdown_at")
        if not countdown_at and start_at:
            start_dt = datetime.fromisoformat(start_at)
            one_minute_before = start_dt - timedelta(minutes=1)
            if one_minute_before > now:
                countdown_at = one_minute_before.isoformat()

        countdown_text = job_data.get("countdown_text") or "⏳ PERHATIAN ⏳\n\nMode pemeliharaan akan diaktifkan dalam 1 menit."

        if countdown_at:
            schedule_if_future("maintenance_countdown", broadcast_job, countdown_at, data={"text": countdown_text})
        schedule_if_future("maintenance_on", trigger_manager_job, start_at, data={"mode": "on"})
        schedule_if_future("maintenance_off", trigger_manager_job, end_at, data={"mode": "off"})
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        logger.info(f"Tidak ada job maintenance yang perlu dijadwalkan ulang: {e}")
        return

COMMAND_LIST = [
    "start", "help", "profil", "search", "stop", "next", "koin", "toko",
    "setfilter", "find" # Tambahkan semua perintah pengguna di sini
]

def _haversine_distance(lat1, lon1, lat2, lon2):
    """Menghitung jarak antara dua titik koordinat dalam kilometer."""
    if not all(isinstance(i, (float, int)) and i is not None for i in [lat1, lon1, lat2, lon2]):
        return float('inf') 

    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    r = 6371
    return c * r
    
# Ganti total fungsi get_city_from_coords Anda dengan versi ini

async def get_city_from_coords(lat: float, lon: float) -> str:
    """
    Mengubah koordinat latitude dan longitude menjadi format "Kabupaten, Provinsi".
    """
    if not lat or not lon:
        return "Tidak diketahui"
    
    # Menggunakan Nominatim (API gratis dari OpenStreetMap)
    # 'accept-language=id' meminta hasil dalam Bahasa Indonesia jika tersedia
    url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lon}&accept-language=id"
    headers = {'User-Agent': 'TelegramAnonymousChatBot/1.0'}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=5.0)
            response.raise_for_status()
            data = response.json()
            
            # Mendapatkan data alamat dari respons
            address = data.get('address', {})
            
            # --- LOGIKA BARU UNTUK PRIORITAS "KABUPATEN, PROVINSI" ---
            
            # Prioritas 1: Cari Kabupaten
            kabupaten = address.get('county')
            
            # Prioritas 2: Jika tidak ada kabupaten, baru cari nama kota/desa sebagai fallback
            if not kabupaten:
                kabupaten = address.get('city') or address.get('town') or address.get('village')
            
            # Cari nama Provinsi
            provinsi = address.get('state') or address.get('region')

            # Gabungkan menjadi format yang diinginkan
            if kabupaten and provinsi:
                return f"{kabupaten}, {provinsi}"
            elif kabupaten:
                return kabupaten # Fallback jika provinsi tidak ditemukan
            else:
                return "Lokasi tidak terdeteksi"

    except Exception as e:
        logger.error(f"Gagal melakukan reverse geocoding untuk {lat},{lon}: {e}")
        return "Tidak dapat mengambil lokasi"

async def end_chat_session(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Ends a chat session, notifies the partner, and returns the session_id."""
    db = get_db(context)
    chat_partners = context.bot_data.setdefault('chat_partners', {})
    
    partner_id = chat_partners.get(user_id)
    session_id = context.application.user_data.get(user_id, {}).get('current_session_id')

    if not (partner_id and session_id):
        return None

    end_time_iso = datetime.now(timezone.utc).isoformat()
    await db.execute(
        "UPDATE chat_sessions SET end_time = ?, status = 'ended' WHERE session_id = ?",
        (end_time_iso, session_id)
    )
    await db.commit()

    await safe_send_message(context.bot, partner_id, "Pasangan Anda telah menghentikan chat.")
    
    reset_user_chat(context, user_id, partner_id)

    return session_id

async def update_karma(db: aiosqlite.Connection, user_id: int, change: int):
    """Menambah atau mengurangi karma pengguna dan memastikannya tetap dalam batas."""
    await db.execute(
        "UPDATE user_profiles SET karma = MAX(0, MIN(200, karma + ?)) WHERE user_id = ?",
        (change, user_id)
    )
    await db.commit()
    logger.info(f"Karma untuk user {user_id} diubah sebanyak {change}.")


def escape_md(text: str) -> str:
    """Escape special MarkdownV2 characters"""
    chars_to_escape = r'_*[]()~`>#+-.=|{}!'
    return "".join(f'\\{char}' if char in chars_to_escape else char for char in text)

def auto_update_profile(func):
    """Decorator to automatically update user profile"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if user and hasattr(context.application, 'db_connection'):
            db = get_db(context)
            try:
                async with db.execute("SELECT user_id FROM user_profiles WHERE user_id = ?", (user.id,)) as cursor:
                    if await cursor.fetchone() is None:
                        await db.execute(
                            "INSERT INTO user_profiles (user_id, username, koin) VALUES (?, ?, 0)", 
                            (user.id, user.username or "")
                        )
                    elif user.username and user.username != "":
                        await db.execute(
                            "UPDATE user_profiles SET username = ? WHERE user_id = ?", 
                            (user.username, user.id)
                        )
                    await db.commit()
            except Exception as e: 
                logger.error(f"Failed to update user profile {user.id}: {e}")
        return await func(update, context, *args, **kwargs)
    return wrapper

async def get_admin_contact(context: ContextTypes.DEFAULT_TYPE) -> str:
    """Get admin contact info"""
    try:
        admin_chat = await context.bot.get_chat(chat_id=OWNER_ID)
        if admin_chat.username:
            return f"@{admin_chat.username.replace('_', '\\_')}"
        return f"[{admin_chat.first_name}](tg://user?id={OWNER_ID})"
    except Exception as e:
        logger.error(f"Failed to get admin chat info: {e}")
        return "Admin"

async def is_user_pro(db, user_id: int) -> bool:
    """Check if user has active premium status"""
    async with db.execute(
        "SELECT pro_expires_at FROM user_profiles WHERE user_id = ?", 
        (user_id,)
    ) as cursor:
        row = await cursor.fetchone()
        if row and row[0]:
            try:
                expire_date = datetime.fromisoformat(row[0])
                return expire_date > datetime.now(timezone.utc)
            except (ValueError, TypeError): 
                return False
    return False

async def is_blocked(db, user1_id, user2_id):
    """Check if users have blocked each other"""
    async with db.execute(
        """SELECT 1 FROM blocks 
           WHERE (blocker_id=? AND blocked_id=?) 
           OR (blocker_id=? AND blocked_id=?)""", 
        (user1_id, user2_id, user2_id, user1_id)
    ) as c:
        return await c.fetchone() is not None

async def block_user(db, blocker_id, blocked_id):
    """Block a user"""
    async with db.execute(
        "SELECT 1 FROM blocks WHERE blocker_id=? AND blocked_id=?", 
        (blocker_id, blocked_id)
    ) as c:
        if await c.fetchone(): 
            return False
    
    ts = datetime.now(timezone.utc).isoformat()
    await db.execute(
        "INSERT INTO blocks (blocker_id, blocked_id, timestamp) VALUES (?, ?, ?)", 
        (blocker_id, blocked_id, ts)
    )
    await db.commit()
    return True

async def save_rating(db, rater_id, rated_id, rating):
    """Save user rating"""
    ts = datetime.now(timezone.utc).isoformat()
    await db.execute(
        "INSERT INTO ratings (rater_id, rated_id, rating, timestamp) VALUES (?, ?, ?, ?)", 
        (rater_id, rated_id, rating, ts)
    )
    await db.commit()

async def get_user_profile_data(db, user_id):
    """Get complete user profile data"""
    db.row_factory = aiosqlite.Row
    async with db.execute(
        "SELECT * FROM user_profiles WHERE user_id = ?", 
        (user_id,)
    ) as c:
        row = await c.fetchone()
        db.row_factory = None  # Reset to default
        return dict(row) if row else None

def reset_user_chat(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Secara paksa membersihkan semua data sesi aktif untuk seorang pengguna."""
    chat_partners = context.bot_data.setdefault('chat_partners', {})
    
    partner_id = chat_partners.pop(user_id, None)
    if partner_id:
        chat_partners.pop(partner_id, None)
    
    if user_id in context.application.user_data:
        context.application.user_data[user_id].pop('current_session_id', None)
    
    if partner_id and partner_id in context.application.user_data:
        context.application.user_data[partner_id].pop('current_session_id', None)
    
    # Hapus juga dari antrian untuk jaga-jaga
    remove_from_queue(context, user_id)
    if partner_id:
        remove_from_queue(context, partner_id)

    logger.info(f"Pembersihan paksa untuk user {user_id} dan partner {partner_id}")

_rate_lock = asyncio.Lock()
_global_window = deque()  # timestamps of recent sends
_last_per_chat: dict[int, float] = {}

async def _acquire_send_slot(chat_id: int):
    """Acquire a send slot respecting global RPS and per-chat delay."""
    loop = asyncio.get_running_loop()
    while True:
        async with _rate_lock:
            now = loop.time()
            # Clean global window (older than 1s)
            while _global_window and (now - _global_window[0]) > 1.0:
                _global_window.popleft()

            # Check per-chat delay
            last = _last_per_chat.get(chat_id, 0.0)
            per_chat_wait = max(0.0, PER_CHAT_DELAY - (now - last))

            global_ok = len(_global_window) < GLOBAL_RPS

            if per_chat_wait == 0.0 and global_ok:
                _last_per_chat[chat_id] = now
                _global_window.append(now)
                return

            sleep_for = per_chat_wait if not global_ok else 0.05
        await asyncio.sleep(max(0.05, sleep_for))

async def safe_edit_message_text(bot, text: str, chat_id: int, message_id: int, **kwargs):
    """Safely edit a message with rate limit and error handling."""
    try:
        await _acquire_send_slot(chat_id)
        await bot.edit_message_text(text=text, chat_id=chat_id, message_id=message_id, **kwargs)
        return True
    except RetryAfter as e:
        await asyncio.sleep(getattr(e, 'retry_after', 1) + 0.1)
        try:
            await _acquire_send_slot(chat_id)
            await bot.edit_message_text(text=text, chat_id=chat_id, message_id=message_id, **kwargs)
            return True
        except Exception:
            return False
    except Exception:
        return False

async def safe_send_message(bot, chat_id: int, text: str, **kwargs):
    """Safely send message with limiter and RetryAfter handling. Returns the message object on success, None on failure."""
    try:
        await _acquire_send_slot(chat_id)
        return await bot.send_message(chat_id=chat_id, text=text, **kwargs)
    except RetryAfter as e:
        await asyncio.sleep(getattr(e, 'retry_after', 1) + 0.1)
        try:
            await _acquire_send_slot(chat_id)
            return await bot.send_message(chat_id=chat_id, text=text, **kwargs)
        except Exception:
            return None
    except Exception:
        return None

async def send_broadcast_in_batches(bot, user_ids: List[int], text: str, *, parse_mode=None, batch_size: int = 25, delay_seconds: float = 1.0):
    """Send broadcast messages in batches to respect Telegram rate limits."""
    for idx in range(0, len(user_ids), batch_size):
        chunk = user_ids[idx: idx + batch_size]
        await asyncio.gather(*[safe_send_message(bot, uid, text, parse_mode=parse_mode) for uid in chunk])
        if idx + batch_size < len(user_ids):
            await asyncio.sleep(delay_seconds)

async def edit_broadcast_in_batches(bot, text: str, id_to_msg_id: dict[int, int], *, batch_size: int = 25, inter_chunk_delay: float = 0.2, **kwargs):
    """Edit broadcast messages in batches to respect rate limits."""
    items = list(id_to_msg_id.items())
    for idx in range(0, len(items), batch_size):
        chunk = items[idx: idx + batch_size]
        await asyncio.gather(*[safe_edit_message_text(bot, text, uid, mid, **kwargs) for uid, mid in chunk])
        if idx + batch_size < len(items):
            await asyncio.sleep(inter_chunk_delay)

# =============================
# COMMAND HANDLERS
# =============================
@auto_update_profile
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    admin_contact_link = await get_admin_contact(context)
    welcome_text = (
        f"👋 **Selamat Datang di Obloran Anonim\\!**\n\n"
        f"Temukan teman baru untuk mengobrol secara rahasia dan aman\\. "
        f"Terkadang, akan ada *Event Kuis* berhadiah koin yang bisa ditukar dengan fitur premium\\!\n\n"
        f"**Perintah Utama:**\n"
        f"• /profil \\- Buat atau perbarui profilmu\\.\n"
        f"• /search \\- Mulai mencari pasangan chat acak\\.\n"
        f"• /find \\- Mencari pasangan dengan filter \\(Premium\\)\\.\n"
        f"• /koin \\- Cek saldo koin kamu\\.\n"
        f"• /toko \\- Lihat hadiah yang bisa ditukar\\.\n"
        f"• /help \\- Tampilkan semua perintah\\.\n\n"
        f"Jika menemukan masalah, hubungi {admin_contact_link}\\."
    )
    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN_V2)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    user_id = update.effective_user.id
    help_text = (
        "ℹ️ **Daftar Perintah Bot**\n\n"
        "*/profil* \\- Membuat atau memperbarui profil Anda\\.\n"
        "*/search* \\- Mencari pasangan chat acak\\.\n"
        "*/find* \\- Mencari pasangan dengan filter premium \\(jika aktif\\)\\.\n"
        "*/setfilter* \\- Mengatur filter pencarian \\(Premium\\)\\.\n"
        "*/stop* \\- Menghentikan sesi chat saat ini\\.\n"
        "*/koin* \\- Mengecek jumlah koin Anda\\.\n"
        "*/toko* \\- Menukar koin dengan status premium\\.\n"
        "*/help* \\- Menampilkan pesan bantuan ini\\."
    )
    
    if user_id == OWNER_ID:
        admin_help_text = (
            "\n\n👑 *Perintah Khusus Admin*\n"
            "*/grantpro \\<user\\_id\\> \\<hari\\>* \\- Memberi status Pro\\.\n"
            "*/addquiz* \\- Menambah kuis baru\\.\n"
            "*/listquizzes* \\- Melihat semua kuis\\.\n"
            "*/delquiz \\<id\\>* \\- Menghapus kuis\\.\n"
            "*/startquiznow* \\- Memulai Event Kuis secara manual\\.\n"
            "*/prunesessions* \\- Menghapus database lama\\."
            "*/maintenance \\<on\\>* \\- Maintenance\\."
        )
        help_text += admin_help_text
    
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN_V2)

# =============================
#  PROFILE HANDLERS
# =============================
@auto_update_profile
async def profil_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if remove_from_queue(context, update.effective_user.id):
        await update.message.reply_text("Pencarian dibatalkan saat masuk ke menu profil.")
    await display_profile_menu(update, context)
    return PROFILE_MAIN

async def display_profile_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = get_db(context)
    profile = await get_user_profile_data(db, user_id)
    def format_interests(s): return ', '.join([i.capitalize() for i in s.split(',')]) if s else 'Belum diatur'
    
    menu_text = (
        "👤 *Menu Profil Anda*\n\n"
        "Klik tombol di bawah untuk mengatur informasi profil Anda\\.\n\n"
        f"• *Gender:* `{escape_md(profile.get('gender') or 'Belum diatur')}`\n"
        f"• *Usia:* `{escape_md(str(profile.get('age') or 'Belum diatur'))}`\n"
        f"• *Bio:* `{escape_md(profile.get('bio') or 'Belum diatur')}`\n"
        f"• *Minat:* `{escape_md(format_interests(profile.get('interests')))}`\n"
        f"• *Lokasi:* `{'Sudah diatur' if profile.get('latitude') else 'Belum diatur'}`\n"
        f"• *Foto Profil:* `{'Sudah diatur' if profile.get('profile_pic_id') else 'Belum diatur'}`"
    )
    keyboard = [
        [InlineKeyboardButton("🚻 Gender", callback_data="p_edit_gender"), InlineKeyboardButton("🎂 Usia", callback_data="p_edit_age")],
        [InlineKeyboardButton("📝 Bio", callback_data="p_edit_bio"), InlineKeyboardButton("🖼️ Foto", callback_data="p_edit_photo")],
        [InlineKeyboardButton("🎨 Minat", callback_data="p_edit_interests"), InlineKeyboardButton("📍 Lokasi", callback_data="p_edit_location")],
        [InlineKeyboardButton("✅ Selesai & Tutup", callback_data="p_close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    chat_id = update.effective_chat.id
    
    message_id_to_delete = context.user_data.pop('profile_message_id', None)
    if message_id_to_delete:
        try: await context.bot.delete_message(chat_id=chat_id, message_id=message_id_to_delete)
        except Exception: pass
    
    sent_message = await context.bot.send_message(chat_id, menu_text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2)
    context.user_data['profile_message_id'] = sent_message.message_id
    
async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Helper untuk menggambar ulang menu utama dan kembali ke state PROFILE_MAIN."""
    query = update.callback_query
    if query:
        await query.answer()
    await display_profile_menu(update, context)
    return PROFILE_MAIN

async def p_prompt_for_input(update: Update, context: ContextTypes.DEFAULT_TYPE, field: str, new_state: int):
    query = update.callback_query; await query.answer()
    prompts = {
        'age': "Silakan kirimkan usia Anda \\(angka saja, misal: 25\\)\\.",
        'bio': "Silakan kirimkan bio singkat Anda\\.",
        'photo': "Silakan kirimkan satu foto untuk profil anonim Anda\\."
    }
    await query.edit_message_text(prompts[field], parse_mode=ParseMode.MARKDOWN_V2)
    return new_state

async def p_receive_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.isdigit() or not 13 <= int(update.message.text) <= 100:
        await update.message.reply_text("Input tidak valid. Harap kirim angka antara 13 dan 100.")
        return P_AGE
    db = get_db(context)
    await db.execute("UPDATE user_profiles SET age = ? WHERE user_id = ?", (int(update.message.text), update.effective_user.id))
    await db.commit()
    await update.message.delete()
    await display_profile_menu(update, context)
    return PROFILE_MAIN

async def p_receive_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db(context)
    await db.execute("UPDATE user_profiles SET bio = ? WHERE user_id = ?", (update.message.text, update.effective_user.id))
    await db.commit()
    await update.message.delete()
    await display_profile_menu(update, context)
    return PROFILE_MAIN

async def p_receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db(context)
    await db.execute("UPDATE user_profiles SET profile_pic_id = ? WHERE user_id = ?", (update.message.photo[-1].file_id, update.effective_user.id))
    await db.commit()
    await update.message.delete()
    await display_profile_menu(update, context)
    return PROFILE_MAIN

async def p_edit_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query; await query.answer()
    keyboard = [
        [InlineKeyboardButton("Laki-laki", callback_data="p_set_gender_Laki-laki"), InlineKeyboardButton("Perempuan", callback_data="p_set_gender_Perempuan")],
        [InlineKeyboardButton("<< Kembali", callback_data="p_back_main")]
    ]
    await query.edit_message_text("Pilih jenis kelamin Anda:", reply_markup=InlineKeyboardMarkup(keyboard))
    return P_GENDER

async def p_set_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    gender = query.data.split('_')[-1]
    db = get_db(context)
    await db.execute("UPDATE user_profiles SET gender = ? WHERE user_id = ?", (gender, query.from_user.id))
    await db.commit()
    await query.answer(f"Gender diatur ke {gender}")
    await display_profile_menu(update, context)
    return PROFILE_MAIN

async def p_edit_interests_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, is_new=False):
    query = update.callback_query; await query.answer()
    user_id = query.from_user.id
    if is_new or 'temp_interests' not in context.user_data:
        db = get_db(context)
        profile = await get_user_profile_data(db, user_id)
        context.user_data['temp_interests'] = [i for i in (profile.get('interests') or "").split(',') if i]
    selected_interests = set(context.user_data.get('temp_interests', []))
    keyboard = []; row = []
    for interest in COMMON_INTERESTS:
        text = f"{'✅ ' if interest.lower() in selected_interests else ''}{interest}"
        row.append(InlineKeyboardButton(text, callback_data=f"p_toggle_{interest.lower()}"))
        if len(row) == 3: keyboard.append(row); row = []
    if row: keyboard.append(row)
    keyboard.append([InlineKeyboardButton("✏️ Tambah Manual", callback_data="p_manual_interest_prompt")])
    keyboard.append([InlineKeyboardButton("💾 Simpan", callback_data="p_save_interests"), InlineKeyboardButton("<< Kembali", callback_data="p_back_main_from_interest")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    display_interests = ", ".join(sorted([i.capitalize() for i in selected_interests])) or "Belum ada"
    text = (f"🎨 *Pilih Minat Anda*\n\nKlik untuk memilih minat\\. Pilihan ini akan ditampilkan di profil Anda\\.\n\n*Pilihan saat ini:* `{escape_md(display_interests)}`")
    try: await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2)
    except telegram.error.BadRequest as e:
        if "Message is not modified" not in str(e): logger.error(f"Error editing interest menu: {e}")
    return P_INTERESTS

async def p_toggle_interest_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    interest = query.data.split('_', 2)[2]
    selected_interests = context.user_data.get('temp_interests', [])
    if interest in selected_interests: selected_interests.remove(interest)
    else: selected_interests.append(interest)
    context.user_data['temp_interests'] = selected_interests
    return await p_edit_interests_menu(update, context)

async def p_prompt_manual_interest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    await query.edit_message_text("Kirim satu minat yang ingin Anda tambahkan \\(maks 20 karakter\\)\\.", parse_mode=ParseMode.MARKDOWN_V2)
    return P_MANUAL_INTEREST

async def p_receive_manual_interest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    manual_interest = update.message.text.strip().lower()
    if ',' in manual_interest or len(manual_interest) > 20:
        await update.message.reply_text("Harap masukkan hanya satu minat (maks 20 karakter), tanpa koma.")
        return P_MANUAL_INTEREST
    selected_interests = set(context.user_data.get('temp_interests', [])); selected_interests.add(manual_interest)
    context.user_data['temp_interests'] = list(selected_interests)
    await update.message.delete()
    
    keyboard = []; row = []
    for interest in COMMON_INTERESTS:
        text = f"{'✅ ' if interest.lower() in selected_interests else ''}{interest}"
        row.append(InlineKeyboardButton(text, callback_data=f"p_toggle_{interest.lower()}"))
        if len(row) == 3: keyboard.append(row); row = []
    if row: keyboard.append(row)
    keyboard.append([InlineKeyboardButton("✏️ Tambah Manual", callback_data="p_manual_interest_prompt")])
    keyboard.append([InlineKeyboardButton("💾 Simpan", callback_data="p_save_interests"), InlineKeyboardButton("<< Kembali", callback_data="p_back_main_from_interest")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    display_interests = ", ".join(sorted([i.capitalize() for i in selected_interests])) or "Belum ada"
    text = (f"🎨 *Pilih Minat Anda*\n\nKlik untuk memilih minat\\. Pilihan ini akan ditampilkan di profil Anda\\.\n\n*Pilihan saat ini:* `{escape_md(display_interests)}`")
    profile_message_id = context.user_data.get('profile_message_id')
    if profile_message_id:
        try: await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=profile_message_id, text=text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2)
        except Exception: await display_profile_menu(update, context)
    return P_INTERESTS

async def p_save_interests_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer("Minat berhasil disimpan!")
    db = get_db(context)
    final_interests = ",".join(sorted(list(set(context.user_data.pop('temp_interests', [])))))
    await db.execute("UPDATE user_profiles SET interests = ? WHERE user_id = ?", (final_interests, query.from_user.id))
    await db.commit()
    await display_profile_menu(update, context)
    return PROFILE_MAIN

async def p_prompt_for_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    await query.message.delete()
    context.user_data.pop('profile_message_id', None)
    kb = ReplyKeyboardMarkup([[KeyboardButton("📍 Bagikan Lokasi Saya", request_location=True)]], resize_keyboard=True, one_time_keyboard=True)
    prompt_msg = await update.effective_chat.send_message("Tekan tombol di bawah untuk membagikan lokasi Anda.", reply_markup=kb)
    context.user_data['prompt_message_id'] = prompt_msg.message_id
    return P_LOCATION

async def p_receive_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = get_db(context)
    await db.execute("UPDATE user_profiles SET latitude = ?, longitude = ? WHERE user_id = ?", (update.message.location.latitude, update.message.location.longitude, update.effective_user.id))
    await db.commit()
    prompt_msg_id = context.user_data.pop('prompt_message_id', None)
    if prompt_msg_id:
        try: await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=prompt_msg_id)
        except Exception: pass
    await update.message.delete()
    await update.effective_chat.send_message("Lokasi berhasil disimpan!", reply_markup=ReplyKeyboardRemove())
    await display_profile_menu(update, context)
    return PROFILE_MAIN

async def p_close(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    await query.message.delete()
    context.user_data.pop('profile_message_id', None)
    await safe_send_message(context.bot, query.from_user.id, "Menu profil ditutup.")
    return ConversationHandler.END
    
    
# =============================
# CHAT & SEARCH HANDLERS
# =============================

# --- FUNGSI-FUNGSI BANTUAN (DEFINISIKAN DULU) ---

def _haversine_distance(lat1, lon1, lat2, lon2):
    """Menghitung jarak antara dua titik koordinat dalam kilometer."""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    r = 6371
    return c * r

async def ice_breaker_callback(context: ContextTypes.DEFAULT_TYPE):
    """Ice breaker job callback"""
    job = context.job
    user1_id, user2_id = job.data['user1'], job.data['user2']
    chat_partners = context.bot_data.setdefault('chat_partners', {})
    if user1_id in chat_partners and chat_partners[user1_id]['partner_id'] == user2_id:
        text = "🧊 *Ice Breaker\\!* Coba tanyakan 3 hal yang disukai pasanganmu\\."
        await safe_send_message(context.bot, user1_id, text, parse_mode=ParseMode.MARKDOWN_V2)
        await safe_send_message(context.bot, user2_id, text, parse_mode=ParseMode.MARKDOWN_V2)

def schedule_ice_breaker(context: ContextTypes.DEFAULT_TYPE, user1_id: int, user2_id: int):
    """Schedule ice breaker message"""
    job_name = f"icebreaker_{min(user1_id, user2_id)}_{max(user1_id, user2_id)}"
    for job in context.job_queue.get_jobs_by_name(job_name): 
        job.schedule_removal()
    context.job_queue.run_once(
        ice_breaker_callback, 
        when=timedelta(minutes=2), 
        data={'user1': user1_id, 'user2': user2_id}, 
        name=job_name
    )

# HAPUS FUNGSI is_match LAMA ANDA
# GANTI DENGAN FUNGSI BARU INI

def calculate_match_score(user_a: dict, user_b: dict) -> float:
    """
    Menghitung skor kecocokan antara dua pengguna (0 hingga 100).
    Skor -1 berarti mereka tidak cocok sama sekali (misal, filter gender gagal).
    """
    p1, p2 = user_a['profile'], user_b['profile']
    
    # --- BOBOT PRIORITAS ---
    WEIGHTS = {
        'gender': 100,  # Bobot gender sangat tinggi, jika gagal, skor langsung -1
        'karma': 0.40,  # Karma punya bobot 40%
        'location': 0.30, # Lokasi 30%
        'interests': 0.20, # Minat 20%
        'age': 0.10,    # Usia 10%
    }
    
    # --- FUNGSI BANTUAN UNTUK FILTER PREMIUM ---
    def check_premium_filters(u_filter, u_target):
        if not u_filter.get('use_filters', False):
            return True
        
        f_profile, t_profile = u_filter['profile'], u_target['profile']
        
        # 1. Validasi Gender (SANGAT WAJIB)
        filter_gender = f_profile.get('filter_gender')
        if filter_gender:
            if filter_gender == 'opposite' and f_profile.get('gender') == t_profile.get('gender'): return False
            if filter_gender == 'same' and f_profile.get('gender') != t_profile.get('gender'): return False

        # Validasi filter lain yang bersifat "keras" (jika diatur, wajib dipenuhi)
        if f_profile.get('filter_age_min') and (t_profile.get('age') or 0) < f_profile['filter_age_min']: return False
        if f_profile.get('filter_age_max') and (t_profile.get('age') or 0) > f_profile['filter_age_max']: return False
        
        return True

    # Jika salah satu gagal validasi filter wajib, langsung return skor -1
    if not (check_premium_filters(user_a, user_b) and check_premium_filters(user_b, user_a)):
        return -1.0

    # --- PENGHITUNGAN SKOR PARSIAL (0-100) ---
    
    # 1. Skor Karma
    karma_diff = abs(p1.get('karma', 100) - p2.get('karma', 100))
    # Semakin kecil perbedaan, semakin dekat skor ke 100
    score_karma = max(0, 100 - karma_diff) 

    # 2. Skor Lokasi
    score_location = 0.0
    if p1.get('latitude') and p2.get('latitude'):
        dist = _haversine_distance(p1['latitude'], p1['longitude'], p2['latitude'], p2['longitude'])
        # Asumsikan jarak "baik" adalah di bawah 50km. Lebih dari itu skornya menurun.
        score_location = max(0, 100 - (dist * 2))

    # 3. Skor Minat
    score_interests = 0.0
    p1_interests = set(i.strip() for i in (p1.get('interests') or '').lower().split(',') if i)
    p2_interests = set(i.strip() for i in (p2.get('interests') or '').lower().split(',') if i)
    if p1_interests and p2_interests:
        common_interests = len(p1_interests.intersection(p2_interests))
        total_interests = len(p1_interests.union(p2_interests))
        if total_interests > 0:
            score_interests = (common_interests / total_interests) * 100

    # 4. Skor Usia
    age_diff = abs((p1.get('age') or 25) - (p2.get('age') or 25))
    # Semakin kecil perbedaan usia, semakin tinggi skornya
    score_age = max(0, 100 - (age_diff * 5))

    # --- HITUNG SKOR TOTAL BERDASARKAN BOBOT ---
    total_score = (
        (score_karma * WEIGHTS['karma']) +
        (score_location * WEIGHTS['location']) +
        (score_interests * WEIGHTS['interests']) +
        (score_age * WEIGHTS['age'])
    )
    
    return total_score

async def create_match(context: ContextTypes.DEFAULT_TYPE, user_a: dict, user_b: dict):
    """Fungsi bantuan untuk membuat pasangan. HANYA menggunakan bot_data."""
    db = get_db(context)
    chat_partners = context.bot_data.setdefault('chat_partners', {})
    user_a_id, user_b_id = user_a['user_id'], user_b['user_id']
    
    now_iso = datetime.now(timezone.utc).isoformat()
    cursor = await db.execute("INSERT INTO chat_sessions (user1_id, user2_id, start_time, status) VALUES (?, ?, ?, 'active')", (user_a_id, user_b_id, now_iso))
    await db.commit()
    session_id = cursor.lastrowid
    
    chat_partners[user_a_id] = {'partner_id': user_b_id, 'session_id': session_id}
    chat_partners[user_b_id] = {'partner_id': user_a_id, 'session_id': session_id}
    
    await send_match_profiles(context, user_a, user_b)
    schedule_ice_breaker(context, user_a_id, user_b_id)
    logger.info(f"Matched user {user_a_id} with {user_b_id}")

async def send_match_profiles(context: ContextTypes.DEFAULT_TYPE, user_a: dict, user_b: dict):
    user_a_id, user_b_id = user_a['user_id'], user_b['user_id']
    profile_a, profile_b = user_a['profile'], user_b['profile']
    distance_km_str = None
    if profile_a.get('latitude') and profile_b.get('latitude'):
        dist = _haversine_distance(profile_a['latitude'], profile_a['longitude'], profile_b['latitude'], profile_b['longitude'])
        distance_km_str = f"{dist:.1f} km"

    async def send_profile(send_to_id, partner_profile):
        final_location_line = "Lokasi tidak dibagikan"
        if partner_profile.get('latitude') and partner_profile.get('longitude'):
            city_name = await get_city_from_coords(partner_profile['latitude'], partner_profile['longitude'])
            if distance_km_str: final_location_line = f"{city_name} - {distance_km_str}"
            else: final_location_line = city_name
        
        interests_str = ", ".join([i.capitalize() for i in partner_profile.get('interests', '').split(',') if i]) if partner_profile.get('interests') else "Belum diatur"
        
        caption = (
            f"✨ *Pasangan Ditemukan\\!* ✨\n\n"
            f"🚻 *Gender:* {escape_md(str(partner_profile.get('gender', 'N/A')))}\n"
            f"🎂 *Usia:* {escape_md(str(partner_profile.get('age', 'N/A')))}\n"
            f"🎨 *Minat:* {escape_md(interests_str)}\n"
            f"📍 *Lokasi:* {escape_md(final_location_line)}\n\n"
            f"📝 *Bio:* {escape_md(partner_profile.get('bio', 'Tidak ada bio\\.'))}"
        )
        try:
            if partner_profile.get('profile_pic_id'):
                await context.bot.send_photo(chat_id=send_to_id, photo=partner_profile['profile_pic_id'], caption=caption, parse_mode=ParseMode.MARKDOWN_V2)
            else:
                await context.bot.send_message(chat_id=send_to_id, text=caption, parse_mode=ParseMode.MARKDOWN_V2)
        except Exception as e:
            logger.error(f"Gagal mengirim profil ke {send_to_id}: {e}")
            await context.bot.send_message(send_to_id, "Pasangan ditemukan\\! Anda sekarang bisa mulai mengobrol\\.", parse_mode=ParseMode.MARKDOWN_V2)

    await asyncio.gather(send_profile(user_a_id, profile_b), send_profile(user_b_id, profile_a))

# GANTI TOTAL FUNGSI try_match_users ANDA DENGAN INI

async def try_match_users(context: ContextTypes.DEFAULT_TYPE):
    """
    Mencocokkan pengguna secara instan berdasarkan skor kecocokan tertinggi.
    """
    db = get_db(context)
    waiting_queue = context.bot_data.setdefault('waiting_queue', [])
    
    # Kita akan memproses antrean sampai tidak ada lagi pasangan yang bisa dibuat
    while len(waiting_queue) >= 2:
        best_pair = None
        highest_score = -1.0
        
        # Cari semua kemungkinan pasangan dan hitung skornya
        for i in range(len(waiting_queue)):
            for j in range(i + 1, len(waiting_queue)):
                user_a = waiting_queue[i]
                user_b = waiting_queue[j]

                # Lewati jika sudah pernah diblokir
                if await is_blocked(db, user_a['user_id'], user_b['user_id']):
                    continue
                
                score = calculate_match_score(user_a, user_b)
                
                # Jika skor saat ini lebih tinggi dari yang terbaik sejauh ini
                if score > highest_score:
                    highest_score = score
                    best_pair = (user_a, user_b)

        # Setelah memeriksa semua pasangan, jika ditemukan pasangan terbaik
        # dengan skor di atas ambang batas (misal, 40), pasangkan mereka.
        if best_pair and highest_score >= 40:
            user_a, user_b = best_pair
            logger.info(f"Pasangan terbaik ditemukan: {user_a['user_id']} & {user_b['user_id']} dengan skor {highest_score:.2f}")
            
            await create_match(context, user_a, user_b)
            
            # Hapus mereka dari antrean dan ulangi loop untuk mencari pasangan terbaik berikutnya
            waiting_queue = [u for u in waiting_queue if u not in (user_a, user_b)]
        else:
            # Jika tidak ada lagi pasangan yang skornya layak, hentikan proses
            break
            
    # Simpan sisa antrean yang tidak berhasil dicocokkan
    context.bot_data['waiting_queue'] = waiting_queue

@auto_update_profile
async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Satu-satunya perintah untuk memulai pencarian. Cerdas & Adaptif."""
    user_id = update.effective_user.id
    chat_partners = context.bot_data.setdefault('chat_partners', {})
    waiting_queue = context.bot_data.setdefault('waiting_queue', [])
    db = get_db(context)

    # Drain mode: jika maintenance akan segera dimulai (< 5 menit), tolak pencarian baru
    try:
        with open("maintenance_info.json", "r") as f:
            info = json.load(f)
            end_time = info.get("end_time")
            start_at = info.get("start_at")
            now = datetime.now(timezone.utc)
            if start_at:
                start_dt = datetime.fromisoformat(start_at)
                if (start_dt - now).total_seconds() <= 300 and (start_dt - now).total_seconds() > 0:
                    await update.message.reply_text("⚠️ Bot memasuki mode perbaikan sebentar lagi. Pencarian baru sementara dinonaktifkan.")
                    return
    except Exception:
        pass

    if user_id in chat_partners:
        await update.message.reply_text("**Anda sudah berada dalam sesi chat\\.**\n\nGunakan */next* atau */stop*\\.", parse_mode=ParseMode.MARKDOWN_V2)
        return
    if any(q['user_id'] == user_id for q in waiting_queue):
        await update.message.reply_text("Anda sudah dalam antrian pencarian.")
        return

    profile = await get_user_profile_data(db, user_id)
    if not profile or not profile.get('gender') or not profile.get('age'):
        await update.message.reply_text("Profil Anda belum lengkap. Silakan gunakan /profil untuk melengkapinya.")
        return

    is_premium = await is_user_pro(db, user_id)
    user_has_filters = profile.get('filter_gender') or profile.get('filter_age_min')
    use_filters = is_premium and user_has_filters

    if is_premium and not user_has_filters:
        await update.message.reply_text("Anda adalah pengguna Premium! ✨\nUntuk pencarian spesifik, atur preferensi di /setfilter\\.\nSaat ini, pencarian akan dilakukan secara acak\\.")

    await update.message.reply_text("🔍 Mencari pasangan...")
    queue_item = {'user_id': user_id, 'use_filters': use_filters, 'profile': profile}
    waiting_queue.append(queue_item)
    await try_match_users(context)

@auto_update_profile
async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mengakhiri sesi chat atau membatalkan pencarian dengan andal."""
    user_id = update.effective_user.id
    chat_partners = context.bot_data.setdefault('chat_partners', {})
    
    if user_id in chat_partners:
        session_info = chat_partners[user_id]
        partner_id, session_id = session_info['partner_id'], session_info['session_id']
        db = get_db(context)

        await db.execute("UPDATE chat_sessions SET end_time = ?, status = 'ended' WHERE session_id = ?", (datetime.now(timezone.utc).isoformat(), session_id))
        await db.commit()
        
        await safe_send_message(context.bot, partner_id, "Pasangan Anda telah menghentikan obrolan.")
        
        feedback_keyboard = [[InlineKeyboardButton("Beri Feedback & Opsi 💬", callback_data=f"feedback_menu_session_{session_id}"), InlineKeyboardButton("Tutup ❌", callback_data="feedback_close")]]
        await update.message.reply_text("Anda telah menghentikan sesi.", reply_markup=InlineKeyboardMarkup(feedback_keyboard))
        await safe_send_message(context.bot, partner_id, "Sesi telah berakhir.", reply_markup=InlineKeyboardMarkup(feedback_keyboard))
        
        chat_partners.pop(user_id, None)
        chat_partners.pop(partner_id, None)
        
    elif remove_from_queue(context, user_id):
        await update.message.reply_text("Pencarian pasangan telah dibatalkan.")
    else:
        await update.message.reply_text("Anda tidak sedang dalam sesi chat atau antrian pencarian.")

@auto_update_profile
async def next_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mengakhiri sesi saat ini dan langsung memulai pencarian baru."""
    await stop_command(update, context)
    context.job_queue.run_once(lambda ctx: asyncio.create_task(search_command(update, ctx)), 0.5, name=f"next_search_{update.effective_user.id}")

async def direct_relay_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Relay messages between chat partners"""
    user_id = update.effective_user.id
    chat_partners = context.bot_data.setdefault('chat_partners', {})
    if user_id not in chat_partners: return
    
    session_info = chat_partners.get(user_id)
    if not session_info: return
    partner_id = session_info['partner_id']
    message = update.message
    await context.bot.send_chat_action(chat_id=partner_id, action=ChatAction.TYPING)
    
    try:
        await _acquire_send_slot(partner_id)
        if message.text: await context.bot.send_message(partner_id, text=message.text)
        elif message.photo: await context.bot.send_photo(partner_id, photo=message.photo[-1].file_id, caption=message.caption)
        elif message.video: await context.bot.send_video(partner_id, video=message.video.file_id, caption=message.caption)
        elif message.voice: await context.bot.send_voice(partner_id, voice=message.voice.file_id)
        elif message.sticker: await context.bot.send_sticker(partner_id, sticker=message.sticker.file_id)
    except Exception as e:
        logger.error(f"Gagal relay pesan dari {user_id} ke {partner_id}: {e}")
        await update.message.reply_text("Gagal mengirim pesan. Sesi dihentikan.")
        # Lakukan pembersihan paksa di sini
        await stop_command(update, context)

# =============================
# FEEDBACK HANDLERS
# =============================

async def _build_and_update_feedback_menu(query: Update, context: ContextTypes.DEFAULT_TYPE, session_id: int, custom_message: str = None):
    """Membangun dan menampilkan menu feedback Like/Dislike berdasarkan status saat ini."""
    db = get_db(context)
    user_id = query.from_user.id
    
    # Gunakan aiosqlite.Row untuk akses kolom via nama
    db.row_factory = aiosqlite.Row
    async with db.execute("SELECT * FROM chat_sessions WHERE session_id = ?", (session_id,)) as cursor:
        session = await cursor.fetchone()
    db.row_factory = None # Reset ke default

    if not session:
        await query.edit_message_text("❌ Error: Sesi ini tidak valid lagi.")
        return

    partner_id = session['user2_id'] if session['user1_id'] == user_id else session['user1_id']
    is_user1 = (session['user1_id'] == user_id)
    
    user_rating = session['user1_rating'] if is_user1 else session['user2_rating']
    is_partner_blocked = await is_blocked(db, user_id, partner_id)

    # Bangun Teks Pesan
    message_parts = [custom_message or "Silakan memberikan feedback untuk partner"]
    if user_rating == 1: message_parts.append("\n- Terima kasih sudah memberikan  feedback ")
    elif user_rating == -1: message_parts.append("\n- Terima kasih sudah memberikan feedback ")
    if is_partner_blocked: message_parts.append("\n- Anda telah memblokir pengguna ini.")
    
    keyboard = []
    
    # Baris Rating Like/Dislike
    rating_row = []
    if user_rating is None:
        rating_row.append(InlineKeyboardButton("👍", callback_data=f"rate_like_session_{session_id}"))
        rating_row.append(InlineKeyboardButton("👎", callback_data=f"rate_dislike_session_{session_id}"))
    elif user_rating == 1: rating_row.append(InlineKeyboardButton("Anda Menyukai Sesi Ini ✅", callback_data="noop"))
    elif user_rating == -1: rating_row.append(InlineKeyboardButton("Anda Tidak Menyukai Sesi Ini ❌", callback_data="noop"))
    keyboard.append(rating_row)

    # Baris Aksi (Lapor & Blokir)
    action_row = []
    action_row.append(InlineKeyboardButton("Laporkan Pengguna 🚨", callback_data=f"report_init_session_{session_id}"))
    if not is_partner_blocked:
        action_row.append(InlineKeyboardButton("Blokir Pengguna 🚫", callback_data=f"block_session_{session_id}"))
    else:
        action_row.append(InlineKeyboardButton("Telah Diblokir ✅", callback_data="noop"))
    keyboard.append(action_row)

    # Baris Selesai
    keyboard.append([InlineKeyboardButton("Selesai ✅", callback_data=f"feedback_done_session_{session_id}")])
    
    await query.edit_message_text(text="\n".join(message_parts), reply_markup=InlineKeyboardMarkup(keyboard))

async def show_full_feedback_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Membuka menu feedback lengkap."""
    query = update.callback_query
    try:
        session_id = int(query.data.split('_')[-1])
        await _build_and_update_feedback_menu(query, context, session_id)
    except (IndexError, ValueError):
        await query.answer("Callback data tidak valid.", show_alert=False)

async def rate_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Memproses rating Suka/Tidak Suka."""
    query = update.callback_query
    parts = query.data.split('_')
    action, session_id = parts[1], int(parts[3])
    rating_value = 1 if action == 'like' else -1
    
    rater_id = query.from_user.id
    db = get_db(context)

    async with db.execute("SELECT user1_id, user2_id FROM chat_sessions WHERE session_id = ?", (session_id,)) as c:
        users = await c.fetchone()
    if not users: return
    
    partner_id = users[1] if users[0] == rater_id else users[0]
    is_rater_user1 = (users[0] == rater_id)

    rating_field = 'user1_rating' if is_rater_user1 else 'user2_rating'
    await db.execute(f"UPDATE chat_sessions SET {rating_field} = ? WHERE session_id = ?", (rating_value, session_id))
    
    custom_message = "Feedback Anda disimpan!"
    if rating_value == 1:
        await update_karma(db, partner_id, 5)
        await query.answer("👍")
    else:
        await update_karma(db, partner_id, -10)
        await query.answer("👎")
        custom_message = "Jika pengguna ini bermasalah, pertimbangkan untuk Melaporkan atau Memblokirnya."
    
    await db.commit()
    await _build_and_update_feedback_menu(query, context, session_id, custom_message=custom_message)

async def block_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Memproses blokir dan menggambar ulang menu."""
    query = update.callback_query
    session_id = int(query.data.split('_')[-1])
    
    blocker_id = query.from_user.id
    db = get_db(context)

    async with db.execute("SELECT user1_id, user2_id FROM chat_sessions WHERE session_id = ?", (session_id,)) as c:
        users = await c.fetchone()
    if not users: return

    blocked_id = users[1] if users[0] == blocker_id else users[0]

    await block_user(db, blocker_id=blocker_id, blocked_id=blocked_id)
    await query.answer("Pengguna diblokir!")
    await _build_and_update_feedback_menu(query, context, session_id, custom_message="Pengguna telah diblokir.")

async def show_report_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan semua opsi kategori laporan."""
    query = update.callback_query
    session_id = int(query.data.split('_')[-1])
    await query.answer()

    report_categories = [
        ("🔞 Konten Ilegal/Porno", "illegal"), ("💔 Pelecehan Seksual", "harassment"),
        ("🗣️ Ujaran Kebencian/SARA", "hate_speech"), ("💰 Penipuan/Scam", "scam"),
        ("📢 Spam/Promosi", "spam"), ("🙄 Kasar/Tdk Menyenangkan", "rude")
    ]
    keyboard = [[InlineKeyboardButton(text, callback_data=f"submit_report_{code}_session_{session_id}")] for text, code in report_categories]
    keyboard.append([InlineKeyboardButton("<< Kembali", callback_data=f"feedback_menu_session_{session_id}")])

    await query.edit_message_text("Pilih alasan yang paling sesuai untuk melaporkan pengguna ini:", reply_markup=InlineKeyboardMarkup(keyboard))

async def submit_report_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Memproses laporan, mengurangi karma, dan kembali ke menu feedback."""
    query = update.callback_query
    parts = query.data.split('_')
    reason_code, session_id = parts[2], int(parts[4])

    report_details = {
        'illegal': {"penalty": -50, "text": "Konten Ilegal/Pornografi"}, 'harassment': {"penalty": -40, "text": "Pelecehan Seksual"},
        'hate_speech': {"penalty": -30, "text": "Ujaran Kebencian/SARA"}, 'scam': {"penalty": -30, "text": "Penipuan/Scam"},
        'spam': {"penalty": -15, "text": "Spam/Promosi"}, 'rude': {"penalty": -10, "text": "Kasar/Tidak Menyenangkan"}
    }
    details = report_details.get(reason_code)
    if not details: return

    db = get_db(context)
    reporter_id = query.from_user.id
    
    async with db.execute("SELECT user1_id, user2_id FROM chat_sessions WHERE session_id = ?", (session_id,)) as c:
        users = await c.fetchone()
    if not users: return
        
    reported_id = users[1] if users[0] == reporter_id else users[0]

    await update_karma(db, reported_id, details['penalty'])

    report_message = (
        f"🚨 <b>Laporan Pengguna Baru</b> 🚨\n\n"
        f"<b>Pelapor:</b> <code>{reporter_id}</code>\n<b>Terlapor:</b> <code>{reported_id}</code>\n"
        f"<b>Sesi ID:</b> <code>{session_id}</code>\n<b>Alasan:</b> {html.escape(details['text'])} (Karma {details['penalty']})"
    )
    await context.bot.send_message(chat_id=DEVELOPER_CHAT_ID, text=report_message, parse_mode=ParseMode.HTML)
    
    await query.answer("Laporan telah dikirim. Terima kasih!", show_alert=False)
    await _build_and_update_feedback_menu(query, context, session_id, custom_message=f"Laporan Anda ('{details['text']}') telah dikirim.")

async def feedback_done_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menyelesaikan sesi feedback dan menghapus tombol."""
    query = update.callback_query
    session_id, user_id = int(query.data.split('_')[-1]), query.from_user.id
    
    db = get_db(context)
    async with db.execute("SELECT user1_id FROM chat_sessions WHERE session_id = ?", (session_id,)) as c:
        res = await c.fetchone()
    if not res: return
        
    feedback_field = 'user1_feedback_given' if res[0] == user_id else 'user2_feedback_given'
    await db.execute(f"UPDATE chat_sessions SET {feedback_field} = 1 WHERE session_id = ?", (session_id,))
    await db.commit()
    
    await query.answer()
    await query.edit_message_text("Terima kasih atas feedback Anda. ✅")

async def feedback_close_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menghapus pesan feedback atas permintaan pengguna."""
    query = update.callback_query
    await query.answer()
    await query.message.delete()

# =============================
# PREMIUM FILTER HANDLERS
# =============================
# GANTI TOTAL FUNGSI set_filter_command ANDA DENGAN INI

@auto_update_profile
async def set_filter_command(update: Update, context: ContextTypes.DEFAULT_TYPE, is_edit: bool = False) -> int:
    """Memulai atau menampilkan menu utama untuk mengatur filter premium."""
    user_id = update.effective_user.id
    db = get_db(context)
    
    if update.message:
        if remove_from_queue(context, user_id): await update.message.reply_text("Pencarian dibatalkan.")
        if not await is_user_pro(db, user_id):
            await update.message.reply_text("Perintah ini hanya untuk pengguna Premium.")
            return ConversationHandler.END

    profile = await get_user_profile_data(db, user_id)
    if not profile: return ConversationHandler.END
    
    # --- PERBAIKAN DI SINI ---
    def format_interests(s: Optional[str]) -> str:
        # Jika s adalah None atau string kosong, langsung kembalikan 'Apapun'
        if not s:
            return 'Apapun'
        # Jika tidak, baru lakukan split dan join
        return ', '.join([i.strip().capitalize() for i in s.split(',') if i])

    text = (
        "⚙️ *Atur Filter Pencarian Premium*\n\n"
        "Gunakan menu di bawah untuk mengatur preferensi pencarian Anda\\.\n\n"
        f"\\- Gender Dicari: *{escape_md((profile.get('filter_gender') or 'Apapun').capitalize())}*\n"
        f"\\- Rentang Usia: *{profile.get('filter_age_min') or 'N/A'} \\ - {profile.get('filter_age_max') or 'N/A'}*\n"
        f"\\- Minat Dicari: *{escape_md(format_interests(profile.get('filter_interests')))}*\n"
        f"\\- Jarak Maksimal: *{f'{profile.get("filter_distance_km")} km' if profile.get('filter_distance_km') else 'N/A'}*\n"
    )
    keyboard = [
        [InlineKeyboardButton("🚻 Gender", callback_data="filter_gender"), InlineKeyboardButton("🎂 Usia", callback_data="filter_age")],
        [InlineKeyboardButton("🎨 Minat", callback_data="filter_interests"), InlineKeyboardButton("📍 Jarak", callback_data="filter_distance")],
        [InlineKeyboardButton("🗑️ Reset Semua Filter", callback_data="filter_reset_all")],
        [InlineKeyboardButton("✅ Selesai", callback_data="filter_close")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.answer()
        try:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2)
        except telegram.error.BadRequest as e:
            if "Message is not modified" not in str(e):
                logger.error(f"Error editing filter menu: {e}")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2)
    
    return SET_FILTER_GENDER

async def filter_gender_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query; await query.answer()
    keyboard = [
        [InlineKeyboardButton("Lawan Jenis", callback_data="set_gender_opposite")],
        [InlineKeyboardButton("Sama Jenis", callback_data="set_gender_same")],
        [InlineKeyboardButton("Apapun", callback_data="set_gender_any")],
        [InlineKeyboardButton("<< Kembali", callback_data="filter_main_menu")],
    ]
    await query.edit_message_text("Pilih preferensi gender yang ingin Anda temui:", reply_markup=InlineKeyboardMarkup(keyboard))
    return SET_FILTER_GENDER

async def set_gender_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    pref = query.data.split('_', 2)[2]
    db = get_db(context)
    filter_value = None if pref == "any" else pref
    await db.execute("UPDATE user_profiles SET filter_gender = ? WHERE user_id = ?", (filter_value, query.from_user.id))
    await db.commit()
    await query.answer(f"Filter gender diatur ke: {pref.capitalize()}")
    return await set_filter_command(update, context) # Kembali ke menu utama

async def filter_age_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query; await query.answer()
    await query.edit_message_text("Masukkan rentang usia \\(contoh: `18-25`\\)\\.\nKetik /cancel untuk membatalkan\\.", parse_mode=ParseMode.MARKDOWN_V2)
    return SET_FILTER_AGE

async def set_filter_age_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    db = get_db(context)
    try:
        min_age, max_age = map(int, text.split('-'))
        if not 13 <= min_age <= max_age <= 100: raise ValueError
        await db.execute("UPDATE user_profiles SET filter_age_min = ?, filter_age_max = ? WHERE user_id = ?", (min_age, max_age, update.effective_user.id))
        await db.commit()
        await update.message.reply_text(f"Filter usia berhasil diatur ke {min_age}-{max_age} tahun.", reply_markup=ReplyKeyboardRemove())
    except (ValueError, IndexError):
        await update.message.reply_text("Format tidak valid. Gunakan `min-max`, contoh: `18-25`.", reply_markup=ReplyKeyboardRemove())
        return SET_FILTER_AGE
    await update.message.delete()
    return await set_filter_command(update, context)
    
# Ganti fungsi filter_interests_menu_callback

async def filter_interests_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, is_new=False):
    query = update.callback_query
    user_id = query.from_user.id
    
    if is_new or 'temp_filter_interests' not in context.user_data:
        db = get_db(context)
        profile = await get_user_profile_data(db, user_id)
        saved_interests = (profile.get('filter_interests') or "").split(',')
        context.user_data['temp_filter_interests'] = [i for i in saved_interests if i]

    selected_interests = set(context.user_data.get('temp_filter_interests', []))

    keyboard = []
    row = []
    for interest in COMMON_INTERESTS:
        text = f"{'✅ ' if interest.lower() in selected_interests else ''}{interest}"
        row.append(InlineKeyboardButton(text, callback_data=f"f_toggle_{interest.lower()}"))
        if len(row) == 3: keyboard.append(row); row = []
    if row: keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton("💾 Simpan", callback_data="f_save_interests"),
        InlineKeyboardButton("<< Kembali", callback_data="filter_main_menu"),
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    display_interests = ", ".join(sorted([i.capitalize() for i in selected_interests])) or "Belum ada"
    
    # PERBAIKAN: Escape titik di akhir kalimat
    text = (
        "🎨 *Atur Filter Minat*\n\n"
        "Pilih minat yang ingin Anda cari\\. Pasangan harus memiliki setidaknya SATU dari minat yang Anda pilih\\.\n\n"
        f"*Filter saat ini:* `{escape_md(display_interests)}`"
    )
    
    await query.answer()
    try:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2)
    except telegram.error.BadRequest as e:
        if "Message is not modified" not in str(e): logger.error(f"Error editing filter interest menu: {e}")

    return SET_FILTER_INTERESTS

async def filter_toggle_interest_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangani saat pengguna menekan tombol minat untuk FILTER."""
    query = update.callback_query
    # Ekstrak minat dari callback data (misal: f_toggle_gaming -> gaming)
    interest = query.data.split('_', 2)[2]
    
    # Gunakan key 'temp_filter_interests' untuk menghindari konflik dengan profil
    selected_interests = context.user_data.get('temp_filter_interests', [])
    
    # Tambah atau hapus minat dari daftar sementara
    if interest in selected_interests:
        selected_interests.remove(interest)
    else:
        selected_interests.append(interest)
    context.user_data['temp_filter_interests'] = selected_interests
    
    # Gambar ulang menu filter dengan state yang sudah diperbarui
    return await filter_interests_menu_callback(update, context)

async def filter_save_interests_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menyimpan filter minat yang dipilih ke database."""
    query = update.callback_query
    db = get_db(context)
    
    # Ambil data final dari user_data, urutkan, dan gabungkan jadi string
    final_interests = ",".join(sorted(list(set(context.user_data.get('temp_filter_interests', [])))))
    
    # Simpan ke database
    await db.execute(
        "UPDATE user_profiles SET filter_interests = ? WHERE user_id = ?",
        (final_interests, query.from_user.id)
    )
    await db.commit()
    
    await query.answer("Filter minat berhasil disimpan!")
    
    # Bersihkan data sementara
    context.user_data.pop('temp_filter_interests', None)
    
    # Kembali ke menu filter utama
    return await set_filter_command(update, context, is_edit=True)

async def filter_distance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Meminta input untuk filter jarak."""
    query = update.callback_query
    await query.answer()
    context.user_data['in_filter_conv'] = True
    await query.message.reply_text(
        "Masukkan jarak maksimal pencarian dalam kilometer (hanya angka, misal: `50`).\nKetik /cancel untuk kembali."
    )
    return SET_FILTER_DISTANCE

async def set_filter_distance_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menerima dan menyimpan filter jarak."""
    text = update.message.text.strip()
    db = get_db(context)
    
    if not text.isdigit() or not 1 <= int(text) <= 10000:
        await update.message.reply_text("Input tidak valid. Harap masukkan angka antara 1 dan 10.000.")
        return SET_FILTER_DISTANCE
        
    distance = int(text)
    await db.execute(
        "UPDATE user_profiles SET filter_distance_km = ? WHERE user_id = ?",
        (distance, update.effective_user.id)
    )
    await db.commit()
    await update.message.reply_text(f"Filter jarak berhasil diatur ke {distance} km.")
    
    # Hapus flag dan kembali ke menu utama filter
    del context.user_data['in_filter_conv']
    await set_filter_command(update, context)
    return -1

async def filter_reset_interests_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menghapus filter minat dari database."""
    query = update.callback_query
    db = get_db(context)
    await db.execute("UPDATE user_profiles SET filter_interests = NULL WHERE user_id = ?", (query.from_user.id,))
    await db.commit()
    await query.answer("Filter minat dihapus!")
    await set_filter_command(update, context, is_edit=True)

async def filter_reset_distance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menghapus filter jarak dari database."""
    query = update.callback_query
    db = get_db(context)
    await db.execute("UPDATE user_profiles SET filter_distance_km = NULL WHERE user_id = ?", (query.from_user.id,))
    await db.commit()
    await query.answer("Filter jarak dihapus!")
    await set_filter_command(update, context, is_edit=True)
    
async def filter_reset_all_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    db = get_db(context)
    await db.execute(
        "UPDATE user_profiles SET filter_gender = NULL, filter_age_min = NULL, filter_age_max = NULL, filter_interests = NULL, filter_distance_km = NULL WHERE user_id = ?",
        (query.from_user.id,)
    )
    await db.commit()
    await query.answer("Semua filter telah dihapus!", show_alert=True)
    return await set_filter_command(update, context)
    
async def filter_close_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query; await query.answer()
    await query.message.delete()
    await safe_send_message(context.bot, query.from_user.id, "Filter berhasil disimpan.")
    return ConversationHandler.END

# =============================
# QUIZ, COIN & SHOP HANDLERS
# =============================
async def process_quiz_answers(context: ContextTypes.DEFAULT_TYPE):
    """Process quiz answers and select winners"""
    if 'current_quiz' not in context.bot_data: 
        return
        
    job_data = context.job.data
    quiz_answer = job_data['answer']
    participants = job_data['participants']
    
    correct_answerers = [
        uid for uid, ans in participants.items() 
        if ans.lower().strip() == quiz_answer.lower().strip()
    ]
    num_winners = min(5, len(correct_answerers))
    winners = random.sample(correct_answerers, num_winners) if num_winners > 0 else []
    
    db = get_db(context)
    for winner_id in winners:
        await db.execute(
            "UPDATE user_profiles SET koin = koin + 50 WHERE user_id = ?", 
            (winner_id,)
        )
        await db.commit()
        await safe_send_message(
            context.bot, 
            winner_id, 
            "🎉 **SELAMAT\\!** 🎉\n\nKamu terpilih sebagai pemenang dan mendapatkan *50 Koin*\\!", 
            parse_mode=ParseMode.MARKDOWN_V2
        )

    logger.info(f"Quiz event completed. Winners: {winners}")
    context.bot_data.pop('current_quiz', None)

async def quiz_event_callback(context: ContextTypes.DEFAULT_TYPE):
    """Quiz event callback"""
    db = get_db(context)
    async with db.execute(
        "SELECT question, answer FROM quizzes ORDER BY RANDOM() LIMIT 1"
    ) as c:
        quiz = await c.fetchone()
        
    if not quiz:
        schedule_next_quiz_event(context.job_queue)
        return

    question, answer = quiz
    context.bot_data['current_quiz'] = {
        'question': question, 
        'answer': answer, 
        'participants': {}
    }
    active_users = set(context.bot_data.get('chat_partners', {}).keys())

    if not active_users:
        schedule_next_quiz_event(context.job_queue)
        return

    # Notify users about upcoming quiz
    for uid in active_users:
        context.application.user_data[uid]['in_quiz_event'] = True
        await safe_send_message(
            context.bot, 
            uid, 
            "‼️ **PERHATIAN** ‼️\n\nEvent Kuis dimulai dalam *10 detik*\\! Chat dijeda sementara\\.", 
            parse_mode=ParseMode.MARKDOWN_V2
        )

    await asyncio.sleep(10)

    # Start quiz
    for uid in active_users:
        await safe_send_message(
            context.bot, 
            uid, 
            f"**EVENT KUIS DIMULAI\\!**\n\n`{question}`", 
            parse_mode=ParseMode.MARKDOWN_V2
        )
    
    # Schedule answer processing
    context.job_queue.run_once(
        process_quiz_answers, 
        60, 
        data={
            'answer': answer, 
            'participants': context.bot_data['current_quiz']['participants']
        }, 
        name="process_answers"
    )
    schedule_next_quiz_event(context.job_queue)

def schedule_next_quiz_event(job_queue: JobQueue):
    """Schedule next quiz event"""
    delay = random.randint(2 * 86400, 4 * 86400)  # 2-4 days
    job_queue.run_once(
        quiz_event_callback, 
        delay, 
        name="global_quiz_event"
    )
    logger.info(f"Next quiz event in {delay / 3600:.2f} hours.")

async def quiz_event_answer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quiz answers"""
    if context.user_data.get('in_quiz_event'):
        answer = update.message.text
        if context.bot_data.get('current_quiz'):
            context.bot_data['current_quiz']['participants'][update.effective_user.id] = answer
        del context.user_data['in_quiz_event']
        await update.message.reply_text("Jawabanmu dicatat. Terima kasih! Chat dilanjutkan.")
        raise ApplicationHandlerStop

async def koin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /koin command"""
    db = get_db(context)
    async with db.execute(
        "SELECT koin FROM user_profiles WHERE user_id = ?", 
        (update.effective_user.id,)
    ) as c:
        koin = (await c.fetchone() or [0])[0]
        
    await update.message.reply_text(
        f"💰 Saldo Anda: *{koin} Koin*", 
        parse_mode=ParseMode.MARKDOWN_V2
    )

async def toko_command(update: Update | InlineKeyboardMarkup, context: ContextTypes.DEFAULT_TYPE):
    """Handle /toko command"""
    user_id = update.effective_user.id
    db = get_db(context)
    async with db.execute(
        "SELECT koin, pro_expires_at FROM user_profiles WHERE user_id = ?", 
        (user_id,)
    ) as c:
        koin, pro_expires_at = (await c.fetchone() or [0, None])

    text = f"🛒 *Toko & Premium*\n\nSaldo Anda: *{koin} Koin*\n\n"
    text += "Tukarkan koin dengan keuntungan eksklusif untuk mengakses */find*\\!\n\n"
    
    keyboard = []
    for item_id, item in SHOP_ITEMS.items():
        button_text = f"{item['name']} - {item['cost']} Koin"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"buy_{item_id}")])
    
    text += "\n💸 *Top Up Koin:*\nSegera Hadir\\!\n\n"
    
    # Build status text
    raw_status_text = "Pengguna Biasa"
    if pro_expires_at:
        try:
            expire_date = datetime.fromisoformat(pro_expires_at)
            if expire_date > datetime.now(timezone.utc):
                raw_status_text = f"Premium, berakhir pada {expire_date.strftime('%d-%m-%Y %H:%M')} UTC"
        except ValueError:
            raw_status_text = "Pengguna Biasa (Format tanggal salah)"

    # Escape status text
    escaped_status_text = escape_md(raw_status_text)
    text += f"ℹ️ *Status Anda:*\n_{escaped_status_text}_"

    # Handle both command and callback cases
    if isinstance(update, Update) and update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                text, 
                reply_markup=InlineKeyboardMarkup(keyboard), 
                parse_mode=ParseMode.MARKDOWN_V2
            )
        except Exception as e:
            if "Message is not modified" not in str(e):
                logger.error(f"Failed to edit shop message: {e}")
    else:
        await update.message.reply_text(
            text, 
            reply_markup=InlineKeyboardMarkup(keyboard), 
            parse_mode=ParseMode.MARKDOWN_V2
        )

async def buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle purchase callback"""
    query = update.callback_query
    item_id = query.data.split('_', 1)[1]
    item = SHOP_ITEMS.get(item_id)
    if not item: 
        return

    user_id = query.from_user.id
    db = get_db(context)
    async with db.execute(
        "SELECT koin, pro_expires_at FROM user_profiles WHERE user_id = ?", 
        (user_id,)
    ) as c:
        koin, current_expiry_str = (await c.fetchone() or [0, None])
    
    if koin < item['cost']:
        await query.answer("Maaf, koin Anda tidak cukup.", show_alert=False)
        return
    
    await query.answer()
    new_koin = koin - item['cost']
    
    now = datetime.now(timezone.utc)
    start_time = now
    
    if current_expiry_str:
        current_expiry = datetime.fromisoformat(current_expiry_str)
        if current_expiry > now: 
            start_time = current_expiry

    new_expiry = start_time + item['duration']
    
    await db.execute(
        "UPDATE user_profiles SET koin = ?, pro_expires_at = ? WHERE user_id = ?", 
        (new_koin, new_expiry.isoformat(), user_id)
    )
    await db.commit()
    
    formatted_expiry = escape_md(new_expiry.strftime('%d-%m-%Y %H:%M'))
    success_text = (
        f"✅ Pembelian berhasil\\! Anda sekarang Premium hingga {formatted_expiry} UTC\\\\. "
        f"Selamat menikmati fitur `/find` dan `/setfilter`\\!"
    )
    await query.message.reply_text(
        success_text, 
        parse_mode=ParseMode.MARKDOWN_V2
    )
    
    await toko_command(update, context)

# =============================
# ADMIN HANDLERS
# =============================
def owner_only(func):
    """Decorator for owner-only commands"""
    async def wrapper(update, context):
        if update.effective_user.id != OWNER_ID: 
            return
        return await func(update, context)
    return wrapper
    

@owner_only
async def maintenance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Perintah /maintenance tanpa argumen (untuk cek status)
    if not context.args:
        # ... (kode status Anda yang sudah benar ada di sini)
        return ConversationHandler.END # Langsung akhiri

    # Perintah /maintenance off (untuk pembatalan darurat)
    if context.args[0].lower() == 'off':
        # ... (kode off Anda yang sudah benar ada di sini)
        return ConversationHandler.END # Langsung akhiri

    # Alur untuk /maintenance on
    try:
        if context.args[0].lower() == 'on' and len(context.args) == 3:
            start_delay_str, duration_str = context.args[1], context.args[2]
            start_delay_seconds = parse_time(start_delay_str); duration_seconds = parse_time(duration_str)
            if start_delay_seconds < 10: # Minimal 10 detik untuk proses
                await update.message.reply_text("Waktu mulai minimal 10 detik (10s)."); return ConversationHandler.END
            
            context.user_data['maintenance_details'] = locals()
            summary_text = (f"Konfirmasi jadwal:\n\n• Mulai dalam: *{start_delay_str}*\n• Durasi: *{duration_str}*\n\nLanjutkan?")
            keyboard = [[InlineKeyboardButton("✅ Konfirmasi", callback_data="confirm_maint"), InlineKeyboardButton("❌ Batal", callback_data="cancel_maint")]]
            await update.message.reply_text(summary_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
            return CONFIRM_MAINTENANCE
        else: raise ValueError
    except Exception:
        await update.message.reply_text("Format salah. Gunakan:\n`/maintenance on <waktu> <durasi>`", parse_mode=ParseMode.MARKDOWN)
        return ConversationHandler.END

@owner_only
async def confirm_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query; await query.answer()
    details = context.user_data.pop('maintenance_details', None)
    if not details:
        await query.edit_message_text("Data jadwal kedaluwarsa."); return ConversationHandler.END

    start_sec, duration_sec = details['start_delay_seconds'], details['duration_seconds']
    start_str, duration_str = details['start_delay_str'], details['duration_str']
    now = datetime.now(timezone.utc)
    start_at = now + timedelta(seconds=start_sec)
    end_at = now + timedelta(seconds=start_sec + duration_sec)
    
    # Simpan info job ke file
    job_info = {"start_at": start_at.isoformat(), "end_at": end_at.isoformat(), "start_delay": start_str, "duration": duration_str}
    with open("maintenance_job.json", "w") as f: json.dump(job_info, f)
    with open("maintenance_info.json", "w") as f: json.dump({"start_at": start_at.isoformat(), "end_time": end_at.isoformat(), "duration": duration_str}, f)

    # 1. Kirim broadcast awal
    initial_message = (f"🔧 PENGUMUMAN 🔧\n\nBot akan memasuki mode perbaikan dalam *{start_str}* dan akan berlangsung selama *{duration_str}*.")
    context.job_queue.run_once(broadcast_job, when=1, data={'text': initial_message})

    # 2. Jadwalkan broadcast hitung mundur, HANYA jika waktu > 1 menit
    if start_sec > 60:
        countdown_text = f"⏳ PERHATIAN ⏳\n\nMode pemeliharaan akan diaktifkan dalam 1 menit."
        context.job_queue.run_once(broadcast_job, when=start_sec - 60, name="maintenance_countdown", data={'text': countdown_text})
    
    # 3. Jadwalkan pemicu ON dan OFF
    context.job_queue.run_once(trigger_manager_job, when=start_sec, name="maintenance_on", data={'mode': 'on'})
    context.job_queue.run_once(trigger_manager_job, when=start_sec + duration_sec, name="maintenance_off", data={'mode': 'off'})
    
    await query.edit_message_text(f"✅ *Siklus Maintenance Otomatis Dijadwalkan*", parse_mode=ParseMode.MARKDOWN)
    return ConversationHandler.END

@owner_only
async def prune_sessions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Memulai proses pembersihan data sesi chat yang sudah 'dingin' dan lama."""
    db = get_db(context)
    two_months_ago_iso = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    
    async with db.execute(
        """SELECT COUNT(*) FROM chat_sessions 
           WHERE start_time < ? AND user1_feedback_given = 1 AND user2_feedback_given = 1""", 
        (two_months_ago_iso,)
    ) as cursor:
        count = (await cursor.fetchone() or [0])[0]

    if count == 0:
        await update.message.reply_text("✅ Tidak ada data sesi 'dingin' (lebih dari 2 bulan dan kedua pihak sudah memberi feedback) yang perlu dibersihkan.")
        return

    keyboard = [[InlineKeyboardButton(f"YA, HAPUS {count} SESI DINGIN", callback_data="confirm_prune_sessions")]]
    await update.message.reply_text(
        f"⚠️ **PERHATIAN** ⚠️\n\nAnda akan menghapus *{count}* data sesi chat yang telah selesai dan lebih tua dari 2 bulan.\n\n"
        f"Tindakan ini tidak dapat diurungkan. Yakin?",
        reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN
    )

@owner_only
async def confirm_prune_sessions_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangani konfirmasi dan mengeksekusi penghapusan data sesi 'dingin'."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("⚙️ Sedang memproses pembersihan data...", reply_markup=None)
    db = get_db(context)
    cutoff_date_iso = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    
    cursor = await db.execute(
        """DELETE FROM chat_sessions WHERE start_time < ? AND user1_feedback_given = 1 AND user2_feedback_given = 1""", 
        (cutoff_date_iso,)
    )
    await db.commit()
    await query.edit_message_text(f"✅ **Pembersihan Selesai**. Sebanyak *{cursor.rowcount}* data sesi lama telah dihapus.", parse_mode=ParseMode.MARKDOWN)
    
@owner_only
async def add_quiz_start(update, context):
    """Start quiz addition process"""
    await update.message.reply_text("Kirim pertanyaan kuis:")
    return QUIZ_QUESTION

async def quiz_question_received(update, context):
    """Receive quiz question"""
    context.user_data['new_quiz_question'] = update.message.text
    await update.message.reply_text("Kirim jawabannya:")
    return QUIZ_ANSWER

async def quiz_answer_received(update, context):
    """Receive quiz answer and save to database"""
    question = context.user_data.pop('new_quiz_question')
    answer = update.message.text
    
    db = get_db(context)
    await db.execute(
        "INSERT INTO quizzes (question, answer) VALUES (?, ?)", 
        (question, answer)
    )
    await db.commit()
    await update.message.reply_text("Kuis disimpan!")
    return ConversationHandler.END

@owner_only
async def list_quizzes(update, context):
    """List all quizzes"""
    db = get_db(context)
    async with db.execute(
        "SELECT id, question, answer FROM quizzes ORDER BY id"
    ) as c:
        quizzes = await c.fetchall()
        
    if not quizzes:
        await update.message.reply_text("Database kuis kosong.")
        return
        
    message_parts = ["*Daftar Kuis:*\n\n"]
    for qid, q, a in quizzes:
        escaped_q = escape_md(q)
        escaped_a = escape_md(a)
        message_parts.append(
            f"*ID: {qid}* \\| P: {escaped_q} \\| A: {escaped_a}\n"
        )
        
    await update.message.reply_text(
        "".join(message_parts), 
        parse_mode=ParseMode.MARKDOWN_V2
    )

@owner_only
async def delete_quiz(update, context):
    """Delete a quiz"""
    if not context.args: 
        return
        
    try:
        qid = int(context.args[0])
        db = get_db(context)
        await db.execute(
            "DELETE FROM quizzes WHERE id = ?", 
            (qid,)
        )
        await db.commit()
        await update.message.reply_text(f"Kuis ID {qid} dihapus.")
    except (ValueError, IndexError): 
        await update.message.reply_text("ID tidak valid.")

@owner_only
async def start_quiz_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manually start quiz event"""
    await update.message.reply_text("Memulai Event Kuis Global secara manual...")
    
    # Remove any existing manual quiz jobs
    for job in context.job_queue.get_jobs_by_name("manual_quiz_event_admin"): 
        job.schedule_removal()
    
    context.job_queue.run_once(
        quiz_event_callback, 
        1, 
        name="manual_quiz_event_admin"
    )

@owner_only
async def grant_pro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Grant premium status to user"""
    try:
        user_id = int(context.args[0])
        duration_days = int(context.args[1])
        
        if duration_days <= 0:
            await update.message.reply_text("Durasi harus lebih dari 0 hari.")
            return

    except (IndexError, ValueError):
        await update.message.reply_text("Format salah. Gunakan: /grantpro <user_id> <jumlah_hari>")
        return

    db = get_db(context)
    
    # Check if user exists
    async with db.execute(
        "SELECT pro_expires_at FROM user_profiles WHERE user_id = ?", 
        (user_id,)
    ) as cursor:
        user_row = await cursor.fetchone()
        if user_row is None:
            await update.message.reply_text(
                f"Pengguna dengan ID {user_id} tidak ditemukan. "
                "Pastikan pengguna tersebut pernah memulai bot."
            )
            return
    
    # Calculate new expiry date
    now = datetime.now(timezone.utc)
    start_time = now
    current_expiry_str = user_row[0]

    # Extend existing premium if active
    if current_expiry_str:
        try:
            current_expiry = datetime.fromisoformat(current_expiry_str)
            if current_expiry > now:
                start_time = current_expiry
        except ValueError:
            pass

    new_expiry = start_time + timedelta(days=duration_days)
    
    # Update database
    await db.execute(
        "UPDATE user_profiles SET pro_expires_at = ? WHERE user_id = ?", 
        (new_expiry.isoformat(), user_id)
    )
    await db.commit()
    
    # Send confirmation to admin and notification to user
    formatted_expiry = new_expiry.strftime('%d-%m-%Y %H:%M')
    await update.message.reply_text(
        f"✅ Berhasil! Pengguna {user_id} sekarang Premium hingga {formatted_expiry} UTC."
    )
    
    await safe_send_message(
        context.bot,
        chat_id=user_id,
        text=(
            f"🎉 Selamat! Anda telah diberikan status **Premium** oleh admin "
            f"sampai *{escape_md(formatted_expiry)} UTC*\\.\n\n"
            f"Anda sekarang dapat menggunakan perintah `/find` dan `/setfilter`\\!"
        ),
        parse_mode=ParseMode.MARKDOWN_V2
    )

# =============================
# ERROR HANDLER
# =============================
# GANTI SELURUH FUNGSI ERROR_HANDLER LAMA ANDA DENGAN YANG INI
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors by logging and sending a safe, truncated message to the developer."""
    logger.error("Exception while handling an update:", exc_info=context.error)
    
    # Abaikan error "Message is not modified" karena tidak kritis.
    if isinstance(context.error, telegram.error.BadRequest) and "Message is not modified" in str(context.error):
        return
        
    # --- 1. Siapkan traceback ---
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)
    
    # --- 2. Siapkan info update yang relevan ---
    update_info = "No update object available."
    if isinstance(update, Update):
        user_info = f"User: {update.effective_user.id}" if update.effective_user else "N/A"
        chat_info = f"Chat: {update.effective_chat.id}" if update.effective_chat else "N/A"
        update_info = f"{user_info}, {chat_info}"
    
    # --- 3. Bangun pesan dengan pemotongan yang cerdas ---
    # Batas Telegram adalah 4096. Kita ambil margin aman di 4000.
    header = "<b>⚠️ Exception Ditemukan ⚠️</b>\n\n"
    error_info = f"<b>Error:</b>\n<pre>{html.escape(str(context.error))}</pre>\n\n"
    update_context_info = f"<b>Konteks:</b>\n<pre>{html.escape(update_info)}</pre>\n\n"
    
    # Hitung sisa karakter yang tersedia untuk traceback
    available_len = 4000 - len(header) - len(error_info) - len(update_context_info)
    
    # Potong traceback dari belakang, karena bagian terakhir biasanya yang paling penting
    truncated_tb = tb_string
    if len(truncated_tb) > available_len:
        truncated_tb = "...\n" + truncated_tb[-available_len:]

    traceback_info = f"<b>Traceback:</b>\n<pre>{html.escape(truncated_tb)}</pre>"
    
    message = header + error_info + update_context_info + traceback_info

    # --- 4. Kirim pesan ---
    try:
        await context.bot.send_message(
            chat_id=DEVELOPER_CHAT_ID, 
            text=message, 
            parse_mode=ParseMode.HTML
        )
    except telegram.error.BadRequest:
        # Jika pesan yang sudah dipotong pun masih terlalu panjang, kirim versi yang sangat ringkas.
        fallback_message = (
            f"<b>⚠️ Exception Terjadi</b>\n"
            f"<b>Error:</b> <pre>{html.escape(str(context.error))}</pre>\n\n"
            f"Traceback terlalu panjang untuk dikirim."
        )
        await context.bot.send_message(
            chat_id=DEVELOPER_CHAT_ID,
            text=fallback_message,
            parse_mode=ParseMode.HTML
        )
        
# STARTUP JOB & SHUTDOWN

async def run_startup_tasks(application: Application):
    """Menjalankan tugas setelah bot siap."""
    application.job_queue.run_once(broadcast_startup_job, 3)
    schedule_next_quiz_event(application.job_queue)
    logger.info("Tugas startup telah dijadwalkan.")

async def broadcast_startup_job(context: ContextTypes.DEFAULT_TYPE):
    """Tugas yang sebenarnya untuk mengirim broadcast startup."""
    db = get_db(context)
    all_user_ids = []
    async with db.execute("SELECT user_id FROM user_profiles") as cursor:
        rows = await cursor.fetchall()
    all_user_ids = [row[0] for row in rows]
    if not all_user_ids: return

    logger.info(f"Memulai broadcast startup ke {len(all_user_ids)} pengguna...")
    startup_text = escape_md("✅ Bot Kembali Online ✅\n\nTerima kasih telah menunggu! Bot sekarang sudah aktif dan siap digunakan kembali. Selamat mengobrol!")
    await send_broadcast_in_batches(context.bot, all_user_ids, startup_text, parse_mode=ParseMode.MARKDOWN_V2)
    logger.info("Broadcast startup selesai.")


async def broadcast_shutdown(application: Application):
    """Broadcasts a neater shutdown countdown, updating every second."""
    db = getattr(application, 'db_connection', None)
    all_user_ids = []
    if db:
        async with db.execute("SELECT user_id FROM user_profiles") as cursor:
            rows = await cursor.fetchall()
        all_user_ids = [row[0] for row in rows]
    if not all_user_ids: 
        return

    logger.info(f"Memulai broadcast shutdown rapi ke {len(all_user_ids)} pengguna...")
    
    broadcast_messages = {}
    countdown_seconds = 10
    
    initial_text = f"🔧 PENGUMUMAN 🔧\n\nBot akan segera offline untuk pemeliharaan. Shutdown dalam: {countdown_seconds} detik."

    # Kirim pesan awal dalam batch dan simpan message_id
    batch_size = 25
    for idx in range(0, len(all_user_ids), batch_size):
        chunk = all_user_ids[idx: idx + batch_size]
        sent_messages = await asyncio.gather(
            *[safe_send_message(application.bot, uid, initial_text) for uid in chunk]
        )
        for j, msg in enumerate(sent_messages):
            if msg:
                broadcast_messages[chunk[j]] = msg.message_id
        if idx + batch_size < len(all_user_ids):
            await asyncio.sleep(1)

    # Update countdown tiap detik, edit pesan dalam batch
    for i in range(countdown_seconds - 1, 0, -1):
        await asyncio.sleep(1)
        text = f"🔧 PENGUMUMAN 🔧\n\nBot akan segera offline untuk pemeliharaan. Shutdown dalam: {i} detik."
        await edit_broadcast_in_batches(application.bot, text, broadcast_messages)

    await asyncio.sleep(1)
    final_countdown_text = "🔧 PENGUMUMAN 🔧\n\nBot sedang dalam proses shutdown..."
    await edit_broadcast_in_batches(application.bot, final_countdown_text, broadcast_messages)
    await asyncio.sleep(0.5)

    final_text = "Bot sedang offline. Sampai jumpa lagi! 👋"
    await send_broadcast_in_batches(application.bot, all_user_ids, final_text)
    
    # Hapus pesan countdown dalam batch
    items = list(broadcast_messages.items())
    for idx in range(0, len(items), batch_size):
        chunk = items[idx: idx + batch_size]
        await asyncio.gather(
            *[application.bot.delete_message(chat_id=uid, message_id=mid) for uid, mid in chunk]
        )
        if idx + batch_size < len(items):
            await asyncio.sleep(1)
    logger.info("Broadcast shutdown selesai.")

# =============================
# MAIN FUNCTION
# =============================
# GANTI TOTAL FUNGSI main() LAMA ANDA DENGAN YANG INI

async def main() -> None:
    """Main application setup and run with full manual control."""
    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .persistence(PicklePersistence(filepath="bot_persistence.pkl"))
        .build()
    )
    
    # Pastikan tidak ada webhook agar long polling tidak konflik
    try:
        await application.bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        logger.warning(f"Gagal menghapus webhook (abaikan jika tidak diset): {e}")
    
    try:
        application.db_connection = await aiosqlite.connect('bot_database.db')
        await init_db(application.db_connection)
    except Exception as e:
        logger.critical(f"KRITIS: Gagal koneksi DB: {e}")
        return
    
    # --- Conversation Handlers ---

    profil_conv = ConversationHandler(
        entry_points=[CommandHandler('profil', profil_command)],
        states={
            PROFILE_MAIN: [
                CallbackQueryHandler(p_edit_gender, pattern="^p_edit_gender$"),
                CallbackQueryHandler(lambda u, c: p_prompt_for_input(u, c, 'age', P_AGE), pattern="^p_edit_age$"),
                CallbackQueryHandler(lambda u, c: p_prompt_for_input(u, c, 'bio', P_BIO), pattern="^p_edit_bio$"),
                CallbackQueryHandler(lambda u, c: p_prompt_for_input(u, c, 'photo', P_PHOTO), pattern="^p_edit_photo$"),
                CallbackQueryHandler(lambda u, c: p_edit_interests_menu(u, c, is_new=True), pattern="^p_edit_interests$"),
                CallbackQueryHandler(p_prompt_for_location, pattern="^p_edit_location$"),
                CallbackQueryHandler(p_close, pattern="^p_close$"),
            ],
            P_GENDER: [
                CallbackQueryHandler(p_set_gender, pattern="^p_set_gender_"),
                CallbackQueryHandler(back_to_main_menu, pattern="^p_back_main$"),
            ],
            P_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, p_receive_age)],
            P_BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, p_receive_bio)],
            P_PHOTO: [MessageHandler(filters.PHOTO, p_receive_photo)],
            P_LOCATION: [MessageHandler(filters.LOCATION, p_receive_location)],
            P_INTERESTS: [
                CallbackQueryHandler(p_toggle_interest_callback, pattern="^p_toggle_"),
                CallbackQueryHandler(p_prompt_manual_interest, pattern="^p_manual_interest_prompt$"),
                CallbackQueryHandler(p_save_interests_callback, pattern="^p_save_interests$"),
                CallbackQueryHandler(back_to_main_menu, pattern="^p_back_main_from_interest$"),
            ],
            P_MANUAL_INTEREST: [MessageHandler(filters.TEXT & ~filters.COMMAND, p_receive_manual_interest)],
        },
        fallbacks=[CommandHandler('cancel', p_close)],
        per_user=True, per_chat=True, per_message=False, allow_reentry=True
    )

    # GANTI TOTAL BLOK set_filter_conv DI FUNGSI main() DENGAN INI

    set_filter_conv = ConversationHandler(
        entry_points=[CommandHandler('setfilter', set_filter_command)],
        states={
            # State ini adalah "hub" utama untuk semua menu
            SET_FILTER_GENDER: [
                CallbackQueryHandler(filter_gender_callback, pattern="^filter_gender$"),
                CallbackQueryHandler(set_gender_callback, pattern="^set_gender_"),
                CallbackQueryHandler(filter_age_callback, pattern="^filter_age$"),
                CallbackQueryHandler(lambda u, c: filter_interests_menu_callback(u, c, is_new=True), pattern="^filter_interests$"),
                CallbackQueryHandler(filter_distance_callback, pattern="^filter_distance$"),
                CallbackQueryHandler(filter_reset_all_callback, pattern="^filter_reset_all$"),
                # Tombol kembali dari submenu akan memanggil set_filter_command lagi
                CallbackQueryHandler(set_filter_command, pattern="^filter_main_menu$"),
            ],
            # State terpisah untuk input yang membutuhkan pesan teks
            SET_FILTER_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_filter_age_received)],
            SET_FILTER_INTERESTS: [
                CallbackQueryHandler(filter_toggle_interest_callback, pattern="^f_toggle_"),
                CallbackQueryHandler(filter_save_interests_callback, pattern="^f_save_interests$"),
                CallbackQueryHandler(set_filter_command, pattern="^filter_main_menu$"),
            ],
            SET_FILTER_DISTANCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_filter_distance_received)],
        },
        fallbacks=[
            CommandHandler('cancel', filter_close_command),
            CallbackQueryHandler(filter_close_command, pattern="^filter_close$")
        ],
        per_user=True, per_chat=True, per_message=False, allow_reentry=True
    )

    add_quiz_conv = ConversationHandler(
        entry_points=[CommandHandler('addquiz', add_quiz_start)],
        states={
            QUIZ_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, quiz_question_received)],
            QUIZ_ANSWER: [MessageHandler(filters.TEXT & ~filters.COMMAND, quiz_answer_received)]
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)],
    )
    
    maintenance_conv = ConversationHandler(
    entry_points=[CommandHandler('maintenance', maintenance_command)],
    states={
        CONFIRM_MAINTENANCE: [
            CallbackQueryHandler(confirm_maintenance, pattern="^confirm_maint$"),
        ],
    },
    fallbacks=[CallbackQueryHandler(lambda u,c: u.callback_query.edit_message_text("Aksi dibatalkan.") or ConversationHandler.END, pattern="^cancel_maint$")],
    per_user=True, per_chat=True
    )
    
    # --- Register Handlers ---
    application.add_handler(profil_conv)
    application.add_handler(set_filter_conv)
    application.add_handler(add_quiz_conv)
    application.add_handler(maintenance_conv)

    # Command Handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("search", search_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("next", next_command))
    application.add_handler(CommandHandler("koin", koin_command))
    application.add_handler(CommandHandler("toko", toko_command))

    # Admin Command Handlers
    application.add_handler(CommandHandler("listquizzes", list_quizzes))
    application.add_handler(CommandHandler("delquiz", delete_quiz))
    application.add_handler(CommandHandler("startquiznow", start_quiz_now))
    application.add_handler(CommandHandler("grantpro", grant_pro))
    application.add_handler(CommandHandler("prunesessions", prune_sessions_command))
    application.add_handler(CommandHandler("maintenance", maintenance_command))
    
    # Global CallbackQuery Handlers
    application.add_handler(CallbackQueryHandler(show_full_feedback_menu_callback, pattern="^feedback_menu_session_"))
    application.add_handler(CallbackQueryHandler(feedback_close_callback, pattern="^feedback_close$"))
    application.add_handler(CallbackQueryHandler(feedback_done_callback, pattern="^feedback_done_session_"))
    application.add_handler(CallbackQueryHandler(rate_callback, pattern="^rate_"))
    application.add_handler(CallbackQueryHandler(block_callback, pattern="^block_session_"))
    application.add_handler(CallbackQueryHandler(show_report_menu_callback, pattern="^report_init_session_"))
    application.add_handler(CallbackQueryHandler(submit_report_callback, pattern="^submit_report_"))
    application.add_handler(CallbackQueryHandler(buy_callback, pattern="^buy_"))
    application.add_handler(CallbackQueryHandler(confirm_prune_sessions_callback, pattern="^confirm_prune_sessions$"))
    application.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.answer(), pattern="^noop$"))

    # Message Handlers (diurutkan berdasarkan prioritas)
    application.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, quiz_event_answer_handler), group=-1)
    application.add_handler(MessageHandler(filters.ChatType.PRIVATE & (filters.TEXT | filters.PHOTO | filters.VIDEO | filters.Sticker.ALL | filters.VOICE) & ~filters.COMMAND, direct_relay_handler), group=0)
    
    # Error Handler
    application.add_error_handler(error_handler)

    # --- Run the bot ---
    pid_file = "main_bot.pid"
    # Guard single instance via pid file
    def _is_running(pid: int) -> bool:
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
    # Deteksi: jika maintenance_bot masih berjalan, tangani otomatis sebelum start
    try:
        maint_pids = set()
        maint_pid_file = "maintenance_bot.pid"
        if os.path.exists(maint_pid_file):
            try:
                with open(maint_pid_file, "r") as f:
                    mpid = int((f.read() or "0").strip())
                if mpid and _is_running(mpid):
                    maint_pids.add(mpid)
            except Exception:
                pass
        # Fallback grep via ps untuk memastikan tidak ada proses orphan
        try:
            out = subprocess.check_output(["ps", "-eo", "pid,cmd"], text=True)
            for line in out.splitlines():
                if "maintenance_bot.py" in line and "grep" not in line:
                    try:
                        pid_str = line.strip().split(None, 1)[0]
                        gpid = int(pid_str)
                        if _is_running(gpid):
                            maint_pids.add(gpid)
                    except Exception:
                        continue
        except Exception:
            pass
        if maint_pids:
            # Beri tahu owner dan coba matikan otomatis
            try:
                await application.bot.send_message(chat_id=OWNER_ID, text=f"⚠️ Maintenance bot terdeteksi berjalan (PID: {sorted(list(maint_pids))}). Mencoba mematikan otomatis...")
            except Exception:
                pass
            try:
                subprocess.run([sys.executable, "manager.py", "off"], check=False)
            except Exception:
                pass
            # Tunggu sebentar lalu cek ulang
            await asyncio.sleep(3)
            re_alive = False
            try:
                refreshed = set()
                if os.path.exists(maint_pid_file):
                    try:
                        with open(maint_pid_file, "r") as f:
                            mpid2 = int((f.read() or "0").strip())
                        if mpid2 and _is_running(mpid2):
                            refreshed.add(mpid2)
                    except Exception:
                        pass
                out2 = subprocess.check_output(["ps", "-eo", "pid,cmd"], text=True)
                for line in out2.splitlines():
                    if "maintenance_bot.py" in line and "grep" not in line:
                        try:
                            gpid = int(line.strip().split(None, 1)[0])
                            if _is_running(gpid):
                                refreshed.add(gpid)
                        except Exception:
                            continue
                if refreshed:
                    re_alive = True
                    maint_pids = refreshed
            except Exception:
                pass
            if re_alive:
                try:
                    await application.bot.send_message(chat_id=OWNER_ID, text=f"❌ Gagal mematikan maintenance otomatis. PID masih aktif: {sorted(list(maint_pids))}. Jalankan 'python manager.py off' atau kill proses secara manual.")
                except Exception:
                    pass
                return
            else:
                try:
                    await application.bot.send_message(chat_id=OWNER_ID, text="✅ Maintenance berhasil dimatikan otomatis. Melanjutkan startup bot utama.")
                except Exception:
                    pass
    except Exception as e:
        logger.warning(f"Gagal melakukan deteksi proses maintenance: {e}")
    if os.path.exists(pid_file):
        try:
            with open(pid_file, "r") as f:
                old = int(f.read().strip() or 0)
            if old and _is_running(old):
                logger.error(f"Bot utama sudah berjalan dengan PID {old}. Keluar.")
                return
        except Exception:
            pass
        try: os.remove(pid_file)
        except Exception: pass
    with open(pid_file, "w") as f:
        f.write(str(os.getpid()))
    try:
        await application.initialize()
        await reschedule_maintenance_jobs(application)
        await application.start()
        await application.updater.start_polling(drop_pending_updates=True)
        logger.info("Bot utama berjalan.")
        await shutdown_event.wait()
    finally:
        logger.info("Memulai shutdown bot utama...")
        if application.updater and application.updater.running: await application.updater.stop()
        if application.running: await application.stop()
        await application.shutdown()
        if hasattr(application, 'db_connection'): await application.db_connection.close()
        if os.path.exists(pid_file): os.remove(pid_file)
        logger.info("Bot utama telah dimatikan.")
        
        if hasattr(application, 'db_connection') and application.db_connection:
            await application.db_connection.close()
            logger.info("Database connection closed.")
        
        logger.info("Shutdown complete.")

def remove_from_queue(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    """Remove user from waiting queue"""
    waiting_queue = context.bot_data.setdefault('waiting_queue', [])
    user_in_queue = next(
        (item for item in waiting_queue if item['user_id'] == user_id),
        None
    )
    if user_in_queue:
        waiting_queue.remove(user_in_queue)
        return True
    return False

if __name__ == '__main__':
    # Menambahkan penanganan sinyal sistem (SIGTERM)
    signal.signal(signal.SIGTERM, handle_signal)
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutdown manual (Ctrl+C) terdeteksi untuk bot utama.")
        shutdown_event.set()
        
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program exited cleanly.")
        
