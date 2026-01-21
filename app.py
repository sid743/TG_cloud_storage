import logging
import sqlite3
import uuid
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# --- CONFIGURATION ---
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
CHANNEL_ID = "-1001234567890"  # Your Channel ID (must start with -100)

# --- DATABASE SETUP (Built-in SQLite) ---
# Creates a simple file to store: unique_link_id -> telegram_file_id
conn = sqlite3.connect('filestore.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS files (
        uid TEXT PRIMARY KEY, 
        file_id TEXT, 
        file_type TEXT
    )
''')
conn.commit()

# --- HELPER: GET FILE ID & TYPE ---
def get_file_id(message):
    """Extracts file_id from any message type (Document, Video, Photo, Audio)."""
    if message.document:
        return message.document.file_id, "document"
    elif message.video:
        return message.video.file_id, "video"
    elif message.photo:
        return message.photo[-1].file_id, "photo" # Get highest res photo
    elif message.audio:
        return message.audio.file_id, "audio"
    return None, None

# --- HANDLER 1: UPLOAD FILE ---
async def handle_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_file_id, file_type = get_file_id(update.message)
    
    if not user_file_id:
        await update.message.reply_text("Please send a valid file (Video, Doc, Photo, Audio).")
        return

    # 1. Forward file to Channel (Cloud Storage)
    forwarded_msg = await context.bot.forward_message(chat_id=CHANNEL_ID, from_chat_id=update.effective_chat.id, message_id=update.message.message_id)
    
    # 2. Get the file_id from the forwarded message (Best practice to ensure persistence)
    cloud_file_id, _ = get_file_id(forwarded_msg)

    # 3. Generate a unique short ID (UUID)
    unique_code = str(uuid.uuid4())[:8] # Using first 8 chars for brevity

    # 4. Save to Database
    cursor.execute('INSERT INTO files (uid, file_id, file_type) VALUES (?, ?, ?)', (unique_code, cloud_file_id, file_type))
    conn.commit()

    # 5. Send Link back to user
    bot_username = context.bot.username
    link = f"https://t.me/{bot_username}?start={unique_code}"
    
    await update.message.reply_text(
        f"✅ <b>File Saved!</b>\n\n"
        f"🆔 <b>ID:</b> <code>{unique_code}</code>\n"
        f"🔗 <b>Link:</b> {link}", 
        parse_mode="HTML"
    )

# --- HANDLER 2: RETRIEVE FILE (via Link or ID) ---
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if user clicked a link (e.g. /start 1234abcd)
    if context.args and len(context.args) > 0:
        unique_code = context.args[0]
        
        cursor.execute('SELECT file_id, file_type FROM files WHERE uid = ?', (unique_code,))
        result = cursor.fetchone()

        if result:
            file_id, file_type = result
            await update.message.reply_text("📂 <b>Retrieving file...</b>", parse_mode="HTML")
            
            # Send the file back based on its type
            if file_type == "document":
                await update.message.reply_document(file_id)
            elif file_type == "video":
                await update.message.reply_video(file_id)
            elif file_type == "photo":
                await update.message.reply_photo(file_id)
            elif file_type == "audio":
                await update.message.reply_audio(file_id)
        else:
            await update.message.reply_text("❌ File not found.")
            
    else:
        await update.message.reply_text("👋 Welcome! Send me any file to store it.")

# --- HANDLER 3: RETRIEVE BY TEXT ID ---
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Allow user to just paste the ID code to get the file
    unique_code = update.message.text.strip()
    # Reuse the logic by artificially adding args and calling start_handler
    context.args = [unique_code]
    await start_handler(update, context)

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start_handler))
    # Handle files (Docs, Videos, Photos, Audio)
    application.add_handler(MessageHandler(filters.Document.ALL | filters.VIDEO | filters.PHOTO | filters.AUDIO, handle_file_upload))
    # Handle text (for pasting IDs)
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), text_handler))

    print("Bot is running...")
    application.run_polling()