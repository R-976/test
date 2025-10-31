import os
import json
import time
import logging
import asyncio
from os import getenv
from threading import Thread

from flask import Flask

from pyrogram import Client, filters, idle
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import (
    ApiIdInvalid, 
    PhoneNumberInvalid, 
    PhoneCodeInvalid, 
    PhoneCodeExpired, 
    SessionPasswordNeeded, 
    PasswordHashInvalid,
    ApiIdPublishedFlood,
    AccessTokenInvalid,
    FloodWait,
    InputUserDeactivated,
    UserIsBlocked,
    PeerIdInvalid
)
from pyromod import listen
from asyncio.exceptions import TimeoutError

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    ApiIdInvalidError,
    PhoneNumberInvalidError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    SessionPasswordNeededError,
    PasswordHashInvalidError
)

# ==================== CONFIG ====================
API_ID = int(getenv("API_ID", "10796618"))
API_HASH = getenv("API_HASH", "4e4b20b4e1e40c90fcb1a7658c800150")
BOT_TOKEN = getenv("BOT_TOKEN", "8351290809:AAGNTwNVF9i39PmgI-tGp_SpEbaYBjxiveA")
OWNER_ID = int(getenv("OWNER_ID", "5368154755"))
MUST_JOIN = getenv("MUST_JOIN", "RomeoBot_op")

# ==================== DATABASE ====================
DB_FILE = "users_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return {"users": []}

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

async def is_served_user(user_id: int) -> bool:
    db = load_db()
    return user_id in db["users"]

async def get_served_users() -> list:
    db = load_db()
    return db["users"]

async def add_served_user(user_id: int):
    if await is_served_user(user_id):
        return
    db = load_db()
    db["users"].append(user_id)
    save_db(db)

# ==================== FLASK ====================
logging.getLogger("werkzeug").setLevel(logging.ERROR)
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "✅ Session Generator Bot is running!"

@flask_app.route("/healthz")
def healthz():
    return ("", 204)

def run_flask():
    port = int(os.getenv("PORT", "8080"))
    flask_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False, threaded=True)

Thread(target=run_flask, daemon=True).start()

# ==================== BOT SETUP ====================
logging.basicConfig(level=logging.WARNING, format="%(asctime)s - %(levelname)s - %(message)s")

app = Client(
    "SessionGenBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True
)

# ==================== BUTTONS ====================
ask_ques = "**Please choose the python library you want to generate string session for:**"

buttons_ques = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔷 Pyrogram V2 🔷", callback_data="pyrogram")],
    [InlineKeyboardButton("🔷 Pyrogram (Old) 🔷", callback_data="pyrogram1")],
    [InlineKeyboardButton("🔷 Telethon 🔷", callback_data="telethon")],
    [InlineKeyboardButton("🔶 Pyrogram V2 Bot 🔶", callback_data="pyrogram_bot"),
     InlineKeyboardButton("🔶 Telethon Bot 🔶", callback_data="telethon_bot")]
])

gen_button = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔄 Start Generating Session", callback_data="generate")]
])

# ==================== USER DATABASE ====================
@app.on_message(filters.private & ~filters.service, group=1)
async def users_sql(_, msg: Message):
    await add_served_user(msg.from_user.id)

# ==================== START COMMAND ====================
@app.on_message(filters.private & filters.command("start"))
async def start(bot: Client, msg: Message):
    me = await bot.get_me()
    
    # Must Join button
    if MUST_JOIN:
        if MUST_JOIN.startswith("@"):
            link = f"https://t.me/{MUST_JOIN[1:]}"
        else:
            link = f"https://t.me/{MUST_JOIN}"
        
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔷 Start Generating 🔷", callback_data="generate")],
            [InlineKeyboardButton("📢 Join Channel", url=link)]
        ])
    else:
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔷 Start Generating 🔷", callback_data="generate")]
        ])
    
    await msg.reply_text(
        f"👋 **Hey {msg.from_user.mention}!**\n\n"
        f"🤖 **I am {me.mention}**\n"
        f"📱 **String Session Generator Bot**\n\n"
        f"I can generate string sessions for:\n"
        f"• Pyrogram V2 (User & Bot)\n"
        f"• Pyrogram Old (User)\n"
        f"• Telethon (User & Bot)\n\n"
        f"Click below to start! 👇",
        reply_markup=buttons
    )

# ==================== GENERATE COMMAND ====================
@app.on_message(filters.private & filters.command(["generate", "gen", "string", "str"]))
async def generate_command(bot: Client, msg: Message):
    await msg.reply(ask_ques, reply_markup=buttons_ques)

# ==================== STATS COMMAND ====================
@app.on_message(filters.user(OWNER_ID) & filters.command("stats"))
async def stats(bot: Client, msg: Message):
    users = await get_served_users()
    await msg.reply_text(
        f"📊 **Bot Statistics:**\n\n"
        f"👥 Total Users: **{len(users)}**",
        quote=True
    )

# ==================== BROADCAST COMMAND ====================
@app.on_message(filters.user(OWNER_ID) & filters.command("broadcast"))
async def broadcast_command(bot: Client, msg: Message):
    if msg.reply_to_message:
        broadcast_msg = msg.reply_to_message
    else:
        await msg.reply_text(
            "❌ **Please reply to a message to broadcast!**\n\n"
            "**Usage:**\n"
            "Reply to any message with `/broadcast`"
        )
        return
    
    users = await get_served_users()
    total_users = len(users)
    
    if total_users == 0:
        await msg.reply_text("❌ **No users found in database!**")
        return
    
    status_msg = await msg.reply_text(
        f"📡 **Broadcasting started...**\n\n"
        f"👥 Total Users: `{total_users}`\n"
        f"⏳ Please wait..."
    )
    
    success = 0
    failed = 0
    deleted = 0
    blocked = 0
    
    for user_id in users:
        try:
            await broadcast_msg.copy(user_id)
            success += 1
            
            if success % 10 == 0:
                await status_msg.edit_text(
                    f"📡 **Broadcasting...**\n\n"
                    f"👥 Total: `{total_users}`\n"
                    f"✅ Success: `{success}`\n"
                    f"❌ Failed: `{failed}`\n"
                    f"🚫 Blocked: `{blocked}`\n"
                    f"👻 Deleted: `{deleted}`\n\n"
                    f"⏳ In progress..."
                )
            
            await asyncio.sleep(0.1)
            
        except FloodWait as e:
            await asyncio.sleep(e.value)
            try:
                await broadcast_msg.copy(user_id)
                success += 1
            except Exception:
                failed += 1
                
        except InputUserDeactivated:
            deleted += 1
            failed += 1
            
        except UserIsBlocked:
            blocked += 1
            failed += 1
            
        except PeerIdInvalid:
            failed += 1
            
        except Exception as e:
            failed += 1
            print(f"Error broadcasting to {user_id}: {e}")
    
    await status_msg.edit_text(
        f"📡 **Broadcast Completed!**\n\n"
        f"👥 Total Users: `{total_users}`\n"
        f"✅ Successfully Sent: `{success}`\n"
        f"❌ Failed: `{failed}`\n"
        f"🚫 Blocked Bot: `{blocked}`\n"
        f"👻 Deleted Account: `{deleted}`\n\n"
        f"**Success Rate:** `{round((success/total_users)*100, 2)}%`"
    )

# ==================== SESSION GENERATOR ====================
async def generate_session(bot: Client, msg: Message, telethon=False, old_pyro=False, is_bot=False):
    if telethon:
        ty = "Telethon"
    else:
        ty = "Pyrogram"
        if not old_pyro:
            ty += " V2"
    if is_bot:
        ty += " Bot"
    
    await msg.reply(f"🚀 **Starting {ty} Session Generation...**")
    user_id = msg.chat.id
    
    # Ask for API_ID
    api_id_msg = await bot.ask(
        user_id, 
        "📝 **Send your API_ID**\n\n"
        "💡 Click /skip to use bot's API\n"
        "❌ Click /cancel to cancel",
        filters=filters.text
    )
    if await cancelled(api_id_msg):
        return
    
    if api_id_msg.text == "/skip":
        api_id = API_ID
        api_hash = API_HASH
    else:
        try:
            api_id = int(api_id_msg.text)
        except ValueError:
            await api_id_msg.reply(
                "❌ **Invalid API_ID!** Must be an integer.\n\n"
                "Please start again.",
                quote=True,
                reply_markup=gen_button
            )
            return
        
        # Ask for API_HASH
        api_hash_msg = await bot.ask(
            user_id,
            "📝 **Now send your API_HASH**\n\n❌ Click /cancel to cancel",
            filters=filters.text
        )
        if await cancelled(api_hash_msg):
            return
        api_hash = api_hash_msg.text.strip()
    
    # Ask for Phone/Bot Token
    if not is_bot:
        t = "📱 **Send your PHONE NUMBER** with country code\n\n" \
            "Example: `+919876543210`\n\n❌ Click /cancel to cancel"
    else:
        t = "🤖 **Send your BOT TOKEN**\n\n" \
            "Example: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`\n\n❌ Click /cancel to cancel"
    
    phone_number_msg = await bot.ask(user_id, t, filters=filters.text)
    if await cancelled(phone_number_msg):
        return
    phone_number = phone_number_msg.text.strip()
    
    if not is_bot:
        await msg.reply("📤 **Sending OTP...**")
    else:
        await msg.reply("🔐 **Logging as Bot...**")
    
    # Create Client
    if telethon and is_bot:
        client = TelegramClient(StringSession(), api_id, api_hash)
    elif telethon:
        client = TelegramClient(StringSession(), api_id, api_hash)
    elif is_bot:
        client = Client(name="bot", api_id=api_id, api_hash=api_hash, bot_token=phone_number, in_memory=True)
    elif old_pyro:
        client = Client(":memory:", api_id=api_id, api_hash=api_hash)
    else:
        client = Client(name="user", api_id=api_id, api_hash=api_hash, in_memory=True)
    
    await client.connect()
    
    # Send Code
    try:
        code = None
        if not is_bot:
            if telethon:
                code = await client.send_code_request(phone_number)
            else:
                code = await client.send_code(phone_number)
    except (ApiIdInvalid, ApiIdInvalidError):
        await msg.reply(
            "❌ **Invalid API_ID/API_HASH combination!**\n\nPlease start again.",
            reply_markup=gen_button
        )
        await client.disconnect()
        return
    except (PhoneNumberInvalid, PhoneNumberInvalidError):
        await msg.reply(
            "❌ **Invalid Phone Number!**\n\nPlease start again.",
            reply_markup=gen_button
        )
        await client.disconnect()
        return
    
    # Ask for OTP
    try:
        phone_code_msg = None
        if not is_bot:
            phone_code_msg = await bot.ask(
                user_id,
                "📨 **OTP sent to your Telegram account!**\n\n"
                "📝 Send OTP in this format: `1 2 3 4 5`\n"
                "⏱ Timeout: 10 minutes\n\n"
                "❌ Click /cancel to cancel",
                filters=filters.text,
                timeout=600
            )
            if await cancelled(phone_code_msg):
                await client.disconnect()
                return
    except TimeoutError:
        await msg.reply(
            "⏱ **Timeout!** 10 minutes exceeded.\n\nPlease start again.",
            reply_markup=gen_button
        )
        await client.disconnect()
        return
    
    # Sign In
    if not is_bot:
        phone_code = phone_code_msg.text.replace(" ", "").strip()
        try:
            if telethon:
                await client.sign_in(phone_number, phone_code, password=None)
            else:
                await client.sign_in(phone_number, code.phone_code_hash, phone_code)
        except (PhoneCodeInvalid, PhoneCodeInvalidError):
            await msg.reply(
                "❌ **Invalid OTP!**\n\nPlease start again.",
                reply_markup=gen_button
            )
            await client.disconnect()
            return
        except (PhoneCodeExpired, PhoneCodeExpiredError):
            await msg.reply(
                "❌ **OTP Expired!**\n\nPlease start again.",
                reply_markup=gen_button
            )
            await client.disconnect()
            return
        except (SessionPasswordNeeded, SessionPasswordNeededError):
            try:
                two_step_msg = await bot.ask(
                    user_id,
                    "🔐 **Your account has 2-Step Verification!**\n\n"
                    "📝 Send your password (exactly as set, case-sensitive)\n"
                    "⏱ Timeout: 5 minutes\n\n"
                    "⚠️ **Note:** Copy-paste your password carefully!\n"
                    "❌ Click /cancel to cancel",
                    filters=filters.text,
                    timeout=300
                )
                
                if await cancelled(two_step_msg):
                    await client.disconnect()
                    return
                    
            except TimeoutError:
                await msg.reply(
                    "⏱ **Timeout!** 5 minutes exceeded.\n\nPlease start again.",
                    reply_markup=gen_button
                )
                await client.disconnect()
                return
            
            try:
                password = two_step_msg.text
                
                if telethon:
                    await client.sign_in(password=password)
                else:
                    await client.check_password(password=password)
                    
            except (PasswordHashInvalid, PasswordHashInvalidError):
                await two_step_msg.reply(
                    "❌ **Invalid Password!**\n\n"
                    "⚠️ **Troubleshooting:**\n"
                    "• Password is case-sensitive\n"
                    "• Copy-paste it carefully\n"
                    "• Check for extra spaces\n"
                    "• Make sure it's your correct 2FA password\n\n"
                    "Please start again.",
                    quote=True,
                    reply_markup=gen_button
                )
                await client.disconnect()
                return
            except Exception as e:
                await two_step_msg.reply(
                    f"❌ **Error:** `{str(e)}`\n\n"
                    "Please start again.",
                    quote=True,
                    reply_markup=gen_button
                )
                await client.disconnect()
                return
    else:
        try:
            if telethon:
                await client.start(bot_token=phone_number)
            else:
                await client.sign_in_bot(phone_number)
        except Exception as e:
            await msg.reply(
                f"❌ **Bot login failed!**\n\n"
                f"Error: `{str(e)}`",
                reply_markup=gen_button
            )
            await client.disconnect()
            return
    
    # Generate String Session
    string_session = None
    try:
        if telethon:
            if not client.is_connected():
                await client.connect()
            string_session = client.session.save()
        else:
            if not is_bot:
                try:
                    me = await client.get_me()
                    print(f"✅ Logged in as: {me.first_name} ({me.id})")
                except Exception as e:
                    print(f"⚠️ Get me error: {e}")
            
            string_session = await client.export_session_string()
        
        if not string_session or len(string_session) < 10:
            raise Exception("Generated session string is empty or too short!")
        
        print(f"✅ Session generated! Length: {len(string_session)}")
        
    except Exception as e:
        print(f"❌ Session generation error: {e}")
        await msg.reply(
            f"❌ **Failed to generate session!**\n\n"
            f"Error: `{str(e)}`\n\n"
            f"Please try again.",
            reply_markup=gen_button
        )
        await client.disconnect()
        return
    
    if not string_session:
        await msg.reply(
            "❌ **Session generation failed!**\n\n"
            "Session string is empty. Please try again.",
            reply_markup=gen_button
        )
        await client.disconnect()
        return
    
    # Send session to user
    text = (
        f"✅ **{ty.upper()} STRING SESSION**\n\n"
        f"`{string_session}`\n\n"
        f"⚠️ **Keep it safe and don't share!**\n"
        f"🤖 **Generated by:** @{(await bot.get_me()).username}"
    )
    
    try:
        if not is_bot:
            await client.send_message("me", text)
    except Exception as e:
        print(f"⚠️ Could not send to saved messages: {e}")
    
    try:
        await bot.send_message(msg.chat.id, text)
    except Exception as e:
        print(f"❌ Error sending session: {e}")
        try:
            await bot.send_message(msg.chat.id, f"✅ **{ty.upper()} STRING SESSION**\n\n**Session String:**")
            await bot.send_message(msg.chat.id, f"`{string_session}`")
            await bot.send_message(msg.chat.id, f"⚠️ **Keep it safe and don't share!**\n🤖 **Generated by:** @{(await bot.get_me()).username}")
        except Exception as e2:
            print(f"❌ Failed to send session: {e2}")
    
    await client.disconnect()
    
    await bot.send_message(
        msg.chat.id,
        f"✅ **Successfully generated {ty} string session!**\n\n"
        f"📬 Check your **Saved Messages** for a copy!"
    )

async def cancelled(msg):
    if "/cancel" in msg.text:
        await msg.reply("❌ **Cancelled!**", quote=True, reply_markup=gen_button)
        return True
    elif "/restart" in msg.text:
        await msg.reply("🔄 **Restarted!**", quote=True, reply_markup=gen_button)
        return True
    elif "/skip" in msg.text:
        return False
    elif msg.text.startswith("/"):
        await msg.reply("❌ **Cancelled!**", quote=True)
        return True
    else:
        return False

# ==================== CALLBACKS ====================
@app.on_callback_query()
async def handle_callbacks(bot: Client, callback_query: CallbackQuery):
    query = callback_query.data
    
    if query == "generate":
        await callback_query.answer()
        await callback_query.message.reply(ask_ques, reply_markup=buttons_ques)
    
    elif query.startswith("pyrogram") or query.startswith("telethon"):
        try:
            if query == "pyrogram":
                await callback_query.answer("⚠️ Pyrogram V2 sessions only work with updated bots!", show_alert=True)
                await generate_session(bot, callback_query.message)
            
            elif query == "pyrogram1":
                await callback_query.answer("📱 Pyrogram Old Version", show_alert=True)
                await generate_session(bot, callback_query.message, old_pyro=True)
            
            elif query == "pyrogram_bot":
                await callback_query.answer("🤖 Pyrogram V2 Bot Session", show_alert=True)
                await generate_session(bot, callback_query.message, is_bot=True)
            
            elif query == "telethon_bot":
                await callback_query.answer("🤖 Telethon Bot Session", show_alert=True)
                await generate_session(bot, callback_query.message, telethon=True, is_bot=True)
            
            elif query == "telethon":
                await callback_query.answer("📱 Telethon User Session", show_alert=True)
                await generate_session(bot, callback_query.message, telethon=True)
        
        except Exception as e:
            print(f"Callback error: {e}")
            await callback_query.message.reply(f"❌ **An error occurred!**\n\nError: `{str(e)}`")

# ==================== RUN BOT ====================
if __name__ == "__main__":
    print("🚀 Starting Session Generator Bot...")
    print("=" * 50)
    
    try:
        app.start()
        me = app.get_me()
        print(f"✅ Bot: @{me.username}")
        print(f"🔐 Must Join: {MUST_JOIN if MUST_JOIN else 'Not Set'}")
        print("=" * 50)
        print("✅ Bot is ready!")
        print("=" * 50)
        
        idle()
        
    except (ApiIdInvalid, ApiIdPublishedFlood):
        raise Exception("❌ Invalid API_ID/API_HASH!")
    except AccessTokenInvalid:
        raise Exception("❌ Invalid BOT_TOKEN!")
    finally:
        app.stop()
        print("👋 Bot stopped!")
