import os
import logging
import json
import pytz
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Set IST timezone
IST = pytz.timezone("Asia/Kolkata")

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File paths
REMINDERS_FILE = "reminders.json"
TAG_USERS_FILE = "tag_users.json"
AIRDROPS_FILE = "airdrops.json"

# Function to load/save data
def load_data(filename):
    if os.path.exists(filename):
        with open(filename, "r") as file:
            return json.load(file)
    return {}

def save_data(filename, data):
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)

# Load JSON data
reminders = load_data(REMINDERS_FILE)
airdrops = load_data(AIRDROPS_FILE)

# Scheduler for reminders
scheduler = BackgroundScheduler()
scheduler.start()

# Start Command
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Use /set_reminder, /list_reminders, /delete_reminder, /add_airdrop, /list_airdrops, /delete_airdrop.")

# Set Reminder
async def set_reminder(update: Update, context: CallbackContext):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /set_reminder HH:MM Reminder text")
        return

    time, text = args[0], " ".join(args[1:])
    user_id = str(update.message.chat_id)

    if user_id not in reminders:
        reminders[user_id] = []
    reminders[user_id].append({"time": time, "text": text})
    save_data(REMINDERS_FILE, reminders)

    # Schedule Reminder
    hour, minute = map(int, time.split(":"))
    scheduler.add_job(send_reminder, "cron", hour=hour, minute=minute, timezone=IST, args=[user_id, text])

    await update.message.reply_text(f"✅ Reminder set for {time} IST")

# List Reminders
async def list_reminders(update: Update, context: CallbackContext):
    user_id = str(update.message.chat_id)
    if user_id in reminders and reminders[user_id]:
        msg = "\n".join([f"🕒 {r['time']} - {r['text']}" for r in reminders[user_id]])
        await update.message.reply_text(f"📌 Your Reminders:\n{msg}")
    else:
        await update.message.reply_text("❌ No reminders set.")

# Delete Reminder
async def delete_reminder(update: Update, context: CallbackContext):
    args = context.args
    if len(args) != 1:
        await update.message.reply_text("Usage: /delete_reminder HH:MM")
        return

    time = args[0]
    user_id = str(update.message.chat_id)

    if user_id in reminders:
        reminders[user_id] = [r for r in reminders[user_id] if r["time"] != time]
        save_data(REMINDERS_FILE, reminders)
        await update.message.reply_text(f"✅ Reminder at {time} deleted.")
    else:
        await update.message.reply_text("❌ No reminders found.")

# Send Reminder
async def send_reminder(user_id, text):
    try:
        context = Application.builder().token(BOT_TOKEN).build()
        await context.bot.send_message(chat_id=user_id, text=f"⏰ Reminder: {text} (IST)")
    except Exception as e:
        logger.error(f"Error sending reminder: {e}")

# Add Airdrop
async def add_airdrop(update: Update, context: CallbackContext):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /add_airdrop AirdropName Deadline(YYYY-MM-DD)")
        return

    name, deadline = args[0], args[1]
    user_id = str(update.message.chat_id)

    if user_id not in airdrops:
        airdrops[user_id] = []
    airdrops[user_id].append({"name": name, "deadline": deadline})
    save_data(AIRDROPS_FILE, airdrops)

    await update.message.reply_text(f"✅ Airdrop '{name}' added with deadline {deadline}")

# List Airdrops
async def list_airdrops(update: Update, context: CallbackContext):
    user_id = str(update.message.chat_id)
    if user_id in airdrops and airdrops[user_id]:
        msg = "\n".join([f"📌 {a['name']} - Deadline: {a['deadline']}" for a in airdrops[user_id]])
        await update.message.reply_text(f"📌 Your Airdrops:\n{msg}")
    else:
        await update.message.reply_text("❌ No airdrops added.")

# Delete Airdrop
async def delete_airdrop(update: Update, context: CallbackContext):
    args = context.args
    if len(args) != 1:
        await update.message.reply_text("Usage: /delete_airdrop AirdropName")
        return

    name = args[0]
    user_id = str(update.message.chat_id)

    if user_id in airdrops:
        airdrops[user_id] = [a for a in airdrops[user_id] if a["name"] != name]
        save_data(AIRDROPS_FILE, airdrops)
        await update.message.reply_text(f"✅ Airdrop '{name}' deleted.")
    else:
        await update.message.reply_text("❌ No airdrops found.")

# Register Handlers
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set_reminder", set_reminder))
    app.add_handler(CommandHandler("list_reminders", list_reminders))
    app.add_handler(CommandHandler("delete_reminder", delete_reminder))
    app.add_handler(CommandHandler("add_airdrop", add_airdrop))
    app.add_handler(CommandHandler("list_airdrops", list_airdrops))
    app.add_handler(CommandHandler("delete_airdrop", delete_airdrop))

    logger.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
