# 📁 Sid's Telegram Unlimited File Store Bot 

An advanced Telegram bot that turns a **Telegram Supergroup** into your own **unlimited, free cloud storage**.

---

## Features 

- **Topic-Based Storage**  
  Automatically creates a unique forum topic for every user to keep files neatly organized.

- **Secure Sharing**  
  Share file links with others. If the requester isn’t the owner, you receive an **Approve / Deny** request.

- **Environment-Based Configuration**  
  Secure and clean setup using `.env` files.

---

## Step 1: Create Your Bot

1. Open Telegram and search for **@BotFather**
2. Click **Start** and type `/newbot`
3. Name your bot (example: `My File Store`)
4. Choose a username (must end with `bot`)
5. Copy the **API Token** provided by BotFather  

> ⚠️ **Important:** Keep this token secret.

---

## Step 2: Create Your Storage Group

1. Create a **New Group** (not a Channel)
2. Go to **Group Info → Edit → Permissions**
3. Enable **Topics** (this converts the group into a Supergroup with forums)
4. Add your bot to the group as an **Administrator**
5. Grant the bot permissions to:
   - Manage Topics
   - Post Messages

---

## Step 3: Get the Group ID

1. Send any message in the group (example: `hello`)
2. Forward that message to **@JsonDumpBot** (or any ID bot)
3. Look for the `forward_from_chat` section
4. Copy the `id` value (usually starts with `-100`)

**Example:**
```text
-1001234567890
```

---

## Step 4: Configure the Environment

1. Create a file named `.env` in the same directory as `bot.py`
2. Add the following contents:

```ini
BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
GROUP_ID=-1001234567890
```

### Variable Explanation

- **BOT_TOKEN** – The token received from BotFather  
- **GROUP_ID** – The ID of your Telegram Supergroup

---

## Step 5: Install & Run

### Prerequisites
- Python 3.9 or higher installed

### Install Dependencies

```bash
pip install python-telegram-bot python-dotenv
```

### Run the Bot

```bash
python bot.py
```

---

## How to Use

### Uploading Files

- Send any file (Document, Video, Photo, Audio) to the bot
- The bot creates a **private topic** for you in the storage group
- You receive a **unique retrieval link**

### Downloading & Sharing

- **Owner Access:** Click the link to download instantly
- **Sharing:** Send the link to someone else
- The bot notifies you when they attempt access
- Approve or deny access using:
  - ✅ Approve
  - ❌ Deny

---

## Available Commands

```text
/start  - Wake up the bot
/list   - View all files you have uploaded
```

---

Happy storing 
            -sid
