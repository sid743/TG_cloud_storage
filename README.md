# 📁 Telegram Unlimited File Store Bot

This is a simple tool that turns a Telegram Channel into your own unlimited, free cloud storage.

## How it works
1. You send a file to the bot.
2. The bot saves it in a private channel (your free cloud).
3. The bot gives you a short link or ID.
4. You (or anyone with the link) can get the file back instantly.

---

## 🛠 Step 1: Create Your Bot
1. Open Telegram and search for **@BotFather**
2. Click **Start** and type `/newbot`
3. Name your bot (example: My File Store)
4. Choose a username (must end with `bot`)
5. Copy the API Token given by BotFather  
   Example:
   ```
   123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
   ```
   ⚠️ Keep this token secret

---

## ☁️ Step 2: Create Your Storage Channel
1. Create a **New Channel** (Private)
2. Open Channel Info → Administrators → Add Admin
3. Add your bot
4. Allow **Post Messages** permission

---

## 🆔 Step 3: Get the Channel ID
1. Send any message in the channel (example: hello)
2. Forward it to **@JsonDumpBot**
3. Look for `forward_from_chat`
4. Copy the `id` value (starts with `-100`)

Example:
```
-1001234567890
```

---

## 📝 Step 4: Configure the Code
Open `main.py` and replace:

```python
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
```

with your bot token.

Replace:

```python
CHANNEL_ID = "-1001234567890"
```

with your channel ID.

Save the file.

---

## 🚀 Step 5: Install & Run
Make sure Python is installed.

Install dependency:
```bash
pip install python-telegram-bot
```

Run the bot:
```bash
python main.py
```

---

## ❓ How to Use
- **Upload:** Send any file to the bot
- **Download:** Click the link or send the short ID back to the bot

---


