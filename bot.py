import sqlite3
import logging
import uuid
import os
from datetime import datetime
from dotenv import load_dotenv  # Import dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, 
    ContextTypes, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    filters
)
from telegram.error import TelegramError

# --- CONFIGURATION ---
# Load environment variables from .env file
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")

# Validation to ensure keys exist
if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN found in .env file.")
if not GROUP_ID:
    raise ValueError("No GROUP_ID found in .env file.")

# --- DATABASE SETUP ---
conn = sqlite3.connect('filestore_v2.db', check_same_thread=False)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        topic_id INTEGER
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS files (
        uid TEXT PRIMARY KEY, 
        file_id TEXT, 
        file_unique_id TEXT, 
        file_type TEXT,
        file_name TEXT,
        owner_id INTEGER
    )
''')
conn.commit()

# --- HELPER: GET FILE METADATA ---
def extract_file_info(message):
    file_id, file_unique_id, file_type, file_name = None, None, None, "Unknown_File"
    
    if message.document:
        file_id = message.document.file_id
        file_unique_id = message.document.file_unique_id
        file_type = "document"
        file_name = message.document.file_name or "Document"
    elif message.video:
        file_id = message.video.file_id
        file_unique_id = message.video.file_unique_id
        file_type = "video"
        file_name = message.caption or f"Video_{datetime.now().strftime('%Y%m%d')}.mp4"
    elif message.photo:
        photo = message.photo[-1]
        file_id = photo.file_id
        file_unique_id = photo.file_unique_id
        file_type = "photo"
        file_name = message.caption or f"Photo_{datetime.now().strftime('%Y%m%d')}.jpg"
    elif message.audio:
        file_id = message.audio.file_id
        file_unique_id = message.audio.file_unique_id
        file_type = "audio"
        file_name = message.audio.file_name or "Audio_Track"

    return file_id, file_unique_id, file_type, file_name

# --- HELPER: MANAGE TOPICS ---
async def get_or_create_topic(context: ContextTypes.DEFAULT_TYPE, user_id: int, user_name: str) -> int:
    cursor.execute('SELECT topic_id FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    
    if row:
        return row['topic_id']
    
    try:
        topic = await context.bot.create_forum_topic(
            chat_id=GROUP_ID, 
            name=f"{user_name} ({user_id})"
        )
        topic_id = topic.message_thread_id
        cursor.execute('INSERT INTO users (user_id, topic_id) VALUES (?, ?)', (user_id, topic_id))
        conn.commit()
        return topic_id
    except TelegramError as e:
        logging.error(f"Failed to create topic: {e}")
        return None

# --- HANDLER 1: UPLOAD FILE ---
async def handle_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.message
    
    file_id, unique_id, file_type, raw_name = extract_file_info(msg)
    if not file_id:
        await msg.reply_text("❌ Unknown file type.")
        return

    await msg.reply_chat_action("upload_document")

    topic_id = await get_or_create_topic(context, user.id, user.first_name)
    if not topic_id:
        await msg.reply_text("❌ Error creating storage topic. Is the bot Admin in the group?")
        return

    try:
        await context.bot.forward_message(
            chat_id=GROUP_ID,
            from_chat_id=msg.chat_id,
            message_id=msg.message_id,
            message_thread_id=topic_id
        )
    except Exception as e:
        await msg.reply_text(f"❌ Storage error: {e}")
        return

    uid = str(uuid.uuid4())[:8]
    cursor.execute('''
        INSERT INTO files (uid, file_id, file_unique_id, file_type, file_name, owner_id) 
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (uid, file_id, unique_id, file_type, raw_name, user.id))
    conn.commit()

    link = f"https://t.me/{context.bot.username}?start={uid}"
    await msg.reply_text(
        f"✅ <b>Saved:</b> {raw_name}\n"
        f"🔗 <b>Link:</b> {link}\n\n"
        f"<i>Only you can access this. Sharing this link triggers an access request.</i>",
        parse_mode=ParseMode.HTML
    )

# --- HANDLER 2: LIST FILES ---
async def list_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cursor.execute('SELECT uid, file_name, file_type FROM files WHERE owner_id = ?', (user_id,))
    files = cursor.fetchall()
    
    if not files:
        await update.message.reply_text("📂 You have no files stored.")
        return
        
    text = "📂 <b>Your Files:</b>\n\n"
    for f in files:
        link = f"https://t.me/{context.bot.username}?start={f['uid']}"
        text += f"🔹 <a href='{link}'>{f['file_name']}</a> ({f['file_type']})\n"
        
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

# --- HANDLER 3: RETRIEVE / START ---
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("👋 Welcome! Send me files to store them.")
        return

    uid = context.args[0]
    requester_id = update.effective_user.id
    requester_name = update.effective_user.first_name
    
    cursor.execute('SELECT * FROM files WHERE uid = ?', (uid,))
    file_data = cursor.fetchone()
    
    if not file_data:
        await update.message.reply_text("❌ File not found.")
        return

    owner_id = file_data['owner_id']

    if requester_id == owner_id:
        await send_file(update.message, file_data['file_id'], file_data['file_type'])
        return

    await update.message.reply_text("🔒 <b>File is protected.</b> Request sent to owner...", parse_mode=ParseMode.HTML)
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"ok_{uid}_{requester_id}"),
            InlineKeyboardButton("❌ Deny", callback_data=f"no_{uid}_{requester_id}")
        ]
    ])
    
    try:
        await context.bot.send_message(
            chat_id=owner_id,
            text=f"🔔 <b>Access Request</b>\n\n"
                 f"👤 <b>User:</b> {requester_name}\n"
                 f"📄 <b>File:</b> {file_data['file_name']}\n"
                 f"Do you want to send this file to them?",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    except Exception:
        await update.message.reply_text("❌ Could not contact file owner.")

# --- HELPER: SEND FILE WRAPPER ---
async def send_file(message_object, file_id, file_type, caption=None):
    if file_type == "document":
        await message_object.reply_document(file_id, caption=caption)
    elif file_type == "video":
        await message_object.reply_video(file_id, caption=caption)
    elif file_type == "photo":
        await message_object.reply_photo(file_id, caption=caption)
    elif file_type == "audio":
        await message_object.reply_audio(file_id, caption=caption)

# --- HANDLER 4: CALLBACKS ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('_')
    action = data[0]
    uid = data[1]
    requester_id = int(data[2])
    
    if action == "no":
        await query.edit_message_text(f"❌ Request denied.")
        try:
            await context.bot.send_message(requester_id, f"❌ Your request for file access was denied.")
        except:
            pass
            
    elif action == "ok":
        cursor.execute('SELECT file_id, file_type, file_name FROM files WHERE uid = ?', (uid,))
        file_data = cursor.fetchone()
        
        if file_data:
            await query.edit_message_text(f"✅ Access granted to user.")
            try:
                await context.bot.send_message(requester_id, f"✅ <b>Request Approved!</b> Incoming file:", parse_mode=ParseMode.HTML)
                if file_data['file_type'] == "document":
                    await context.bot.send_document(requester_id, file_data['file_id'])
                elif file_data['file_type'] == "video":
                    await context.bot.send_video(requester_id, file_data['file_id'])
                elif file_data['file_type'] == "photo":
                    await context.bot.send_photo(requester_id, file_data['file_id'])
                elif file_data['file_type'] == "audio":
                    await context.bot.send_audio(requester_id, file_data['file_id'])
            except Exception as e:
                await query.edit_message_text(f"✅ Approved, but failed to send: {e}")

# --- MAIN ---
if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("list", list_files))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.Document.ALL | filters.VIDEO | filters.PHOTO | filters.AUDIO, handle_file_upload))

    print("Bot is running...")
    application.run_polling()
