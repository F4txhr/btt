import logging
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
)
from telegram.constants import ParseMode
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
)
import telegram.error

# Import helpers from the main bot module
from bot import (
    get_db,
    get_user_profile_data,
    escape_md,
    remove_from_queue,
    safe_send_message,
    auto_update_profile,
    COMMON_INTERESTS,
)

logger = logging.getLogger(__name__)

# Conversation states for profile
(
    PROFILE_MAIN,
    P_AGE,
    P_BIO,
    P_PHOTO,
    P_INTERESTS,
    P_LOCATION,
    P_MANUAL_INTEREST,
    P_GENDER,
) = range(8)

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
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id_to_delete)
        except Exception:
            pass

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
    query = update.callback_query
    await query.answer()
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
    query = update.callback_query
    await query.answer()
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
    query = update.callback_query
    if query:
        await query.answer()
        user_id = query.from_user.id
    else:  # Called from a message handler
        user_id = update.effective_user.id

    if is_new or 'temp_interests' not in context.user_data:
        db = get_db(context)
        profile = await get_user_profile_data(db, user_id)
        context.user_data['temp_interests'] = [i for i in (profile.get('interests') or "").split(',') if i]
    selected_interests = set(context.user_data.get('temp_interests', []))
    keyboard = []
    row = []
    for interest in COMMON_INTERESTS:
        text = f"{'✅ ' if interest.lower() in selected_interests else ''}{interest}"
        row.append(InlineKeyboardButton(text, callback_data=f"p_toggle_{interest.lower()}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("✏️ Tambah Manual", callback_data="p_manual_interest_prompt")])
    keyboard.append([InlineKeyboardButton("💾 Simpan", callback_data="p_save_interests"), InlineKeyboardButton("<< Kembali", callback_data="p_back_main_from_interest")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    display_interests = ", ".join(sorted([i.capitalize() for i in selected_interests])) or "Belum ada"
    text = (f"🎨 *Pilih Minat Anda*\n\nKlik untuk memilih minat\\. Pilihan ini akan ditampilkan di profil Anda\\.\n\n*Pilihan saat ini:* `{escape_md(display_interests)}`")
    try:
        if query:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2)
        else:  # From message handler, we need to find the original menu message and edit it
            profile_message_id = context.user_data.get('profile_message_id')
            if profile_message_id:
                await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=profile_message_id, text=text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2)
    except telegram.error.BadRequest as e:
        if "Message is not modified" not in str(e):
            logger.error(f"Error editing interest menu: {e}")
    return P_INTERESTS

async def p_toggle_interest_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    interest = query.data.split('_', 2)[2]
    selected_interests = context.user_data.get('temp_interests', [])
    if interest in selected_interests:
        selected_interests.remove(interest)
    else:
        selected_interests.append(interest)
    context.user_data['temp_interests'] = selected_interests
    return await p_edit_interests_menu(update, context)

async def p_prompt_manual_interest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Kirim satu minat yang ingin Anda tambahkan \\(maks 20 karakter\\)\\.", parse_mode=ParseMode.MARKDOWN_V2)
    return P_MANUAL_INTEREST

async def p_receive_manual_interest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    manual_interest = update.message.text.strip().lower()
    if ',' in manual_interest or len(manual_interest) > 20:
        await update.message.reply_text("Harap masukkan hanya satu minat (maks 20 karakter), tanpa koma.")
        return P_MANUAL_INTEREST
    selected_interests = set(context.user_data.get('temp_interests', []))
    selected_interests.add(manual_interest)
    context.user_data['temp_interests'] = list(selected_interests)
    await update.message.delete()

    # Redraw the menu directly
    await p_edit_interests_menu(update, context)
    return P_INTERESTS

async def p_save_interests_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Minat berhasil disimpan!")
    db = get_db(context)
    final_interests = ",".join(sorted(list(set(context.user_data.pop('temp_interests', [])))))
    await db.execute("UPDATE user_profiles SET interests = ? WHERE user_id = ?", (final_interests, query.from_user.id))
    await db.commit()
    await display_profile_menu(update, context)
    return PROFILE_MAIN

async def p_prompt_for_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
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
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=prompt_msg_id)
        except Exception:
            pass
    await update.message.delete()
    await update.effective_chat.send_message("Lokasi berhasil disimpan!", reply_markup=ReplyKeyboardRemove())
    await display_profile_menu(update, context)
    return PROFILE_MAIN

async def p_close(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.delete()
    context.user_data.pop('profile_message_id', None)
    await safe_send_message(context.bot, query.from_user.id, "Menu profil ditutup.")
    return ConversationHandler.END

# Define the conversation handler
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
