import os
import sys
import time
import random
import asyncio
import logging
from io import BytesIO
from datetime import datetime
from platform import python_version
from os import getenv
from pyrogram import Client, filters, idle, __version__
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import FloodWait, UsernameOccupied

# ==================== LOGGING SETUP ====================
for logger_name in ["werkzeug", "pyrogram", "asyncio", "httpx", "urllib3"]:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)

# ==================== FLASK SERVER FOR RENDER ====================
from flask import Flask
from threading import Thread

flask_app = Flask(__name__)
flask_app.logger.disabled = True

@flask_app.route("/")
def home():
    return "✅ Bot System is Running!"

@flask_app.route("/health")
def health():
    return "OK", 200

@flask_app.route("/healthz")
def healthz():
    return "", 204

def run_flask():
    port = int(getenv("PORT", 8080))
    print(f"🌐 Flask server starting on port {port}...")
    flask_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False, threaded=True)

flask_thread = Thread(target=run_flask, daemon=True)
flask_thread.start()
print("✅ Flask server started successfully!")

# ==================== CONFIG ====================
API_ID = int(getenv("API_ID", "10796618"))
API_HASH = getenv("API_HASH", "4e4b20b4e1e40c90fcb1a7658c800150")
BOT_TOKEN = getenv("BOT_TOKEN", "8351290809:AAFahqEdQgI1KKiHDWBHZVrGRYqLwz0IkG4")
OWNER_ID = int(getenv("OWNER_ID", "8288876886"))
STRING_SESSION = getenv("STRING_SESSION", "BQEiZi4AAANrPUa2j8zWuh_6NYpESzWOkGOuxv3io0xUzrvHmrBvC4-QtvwS3zvvdztdkdwbviqXpsQO2WbbskEYV6ype-ee4wfitd0y0CGccOI0ncngKzyKaotCzgjz0O8kiuR7QhDuDzQZBWtitvhVleejrX7VLUMHk4C9dxkcHQ9G2yLs2kT8oGsqqGb3udrkvKWzt3EYCkRZx1IVEcGu3bl8L53bpT8qDMfp2PTuzu2AW3XNK_P45bYGGKPfy7FWOxVQ2Mf7UpHtQJJACDWtq-3BKf5D-rUPXWl6PpSOB6tLF-ekcNWmBbW4DA5z5U1Q92UGGfy852ZDsJjDZrpW1HvzWQAAAAHuDjlWAA")
SUDO_USERS = list(map(int, getenv("SUDO_USERS", "7041789891").split()))
ALIVE_PIC = getenv("ALIVE_PIC", "https://telegra.ph/file/a62b9c7d9848afde0569e.jpg")

# ==================== GLOBALS ====================
START_TIME = datetime.utcnow()
SUDO_USERS.append(OWNER_ID)

# State management
spam_chats = []
ACTIVATE_RLIST = {}  # {hoster_id: [user_ids]}
ACTIVATE_LLIST = {}  # {hoster_id: [user_ids]}
HOSTED_CLIENTS = {}  # {user_id: client_instance}
ORIGINAL_PROFILES = {}  # {user_id: profile_data}

# Content Lists
LOVE = [
    "𝒀𝒂𝒓 𝑨𝒑𝒌𝒊 𝑩𝒂𝒕𝒆𝒏 𝑺𝒖𝒏 𝑲𝒂𝒓 𝑻𝒐 𝑴𝒖𝒋𝒆 𝑨𝒑𝒌𝒐 𝑴𝒆𝒓𝒊 𝑱𝒂𝒂𝒏𝒖 𝑩𝒂𝒏𝒐𝒈𝒊 𝑨𝒘𝒂𝒓𝒅 𝑫𝒆𝒏𝒆 𝑲𝒂 𝑴𝒂𝒏 𝑲𝒂𝒓 𝑹𝒂𝒉𝒂 𝒉𝒂𝒊",
    "आप इतने क्यूट हो की अगर MSG ना भी करना चाहू. तो भी हाथ खुद कीपैड पर चलने लगता है !",
    "मै तो सिर्फ तुम्हारे प्यार का नशा करता हु , एंड उसके हेंग ओवर के आगे कोई और नशे की जरुरत नहीं है !",
    "कुछ ऐसे हस्दे ज़िन्दगी मैं होते है🤔🤔, के इंसान तो बच जाता है मगर ज़िंदा नहीं रहता😂💓",
    "तुम्हारी मुस्कान देख कर मेरा दिल पिघल जाता है 💖",
    "जब से तुम मिली हो, ज़िंदगी जन्नत बन गई है 🌹"
]

RAID = [
    "A", "B", "C",
    "D", "E", "F"
]

PORM = [
    "https://telegra.ph/file/9bcc076fd81dfe3feb291.mp4",
    "https://telegra.ph/file/b7a1a42429a65f64e67af.mp4",
    "https://telegra.ph/file/a8bf6c6df8a48e4a306ca.jpg",
    "https://telegra.ph/file/af9e3f98da0bd937adf6e.jpg"
]

GROUP = [-1001265778325, -1001625889213, -1001678976340]
VERIFIED_USERS = [5368154755, 5353539036, 5392070730]

# ==================== CLIENTS ====================
app = Client("HosterBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)
client = Client("Userbot", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION, in_memory=True)

# ==================== HELPER FUNCTIONS ====================

async def eor(message: Message, text: str, **kwargs):
    """Edit or Reply to message"""
    try:
        if message.from_user.is_self:
            return await message.edit_text(text, **kwargs)
        return await message.reply_text(text, **kwargs)
    except:
        return None

def get_text(message: Message):
    """Extract text from command"""
    text = message.text or ""
    if " " in text:
        return text.split(None, 1)[1]
    return None

async def get_user(message: Message, text: str, user_client: Client):
    """Get user from message or text"""
    try:
        if message.reply_to_message and message.reply_to_message.from_user:
            return message.reply_to_message.from_user
        
        if not text:
            return None
        
        text = text.strip()
        if text.startswith("@"):
            text = text[1:]
        
        if text.isdigit():
            return await user_client.get_users(int(text))
        else:
            return await user_client.get_users(text)
    except:
        return None

async def _human_time_duration(seconds):
    """Convert seconds to readable format"""
    if seconds == 0:
        return 'inf'
    parts = []
    for unit, div in [('Week', 604800), ('Day', 86400), ('Hour', 3600), ('Min', 60), ('Sec', 1)]:
        amount, seconds = divmod(int(seconds), div)
        if amount > 0:
            parts.append(f'{amount} {unit}{"s" if amount > 1 else ""}')
    return ', '.join(parts)

async def generate_unique_username(user_client: Client, base_username: str):
    """Generate unique username by appending last letter"""
    if not base_username:
        return None
    
    base_username = base_username.replace("@", "")
    last_letter = base_username[-1]
    
    # Only attempt: Repeat last letter (1-11 times)
    for i in range(1, 11):
        new_username = base_username + (last_letter * i)
        
        # Check if username is too long (Telegram limit is 32 characters)
        if len(new_username) > 32:
            break
            
        try:
            await user_client.set_username(new_username)
            return new_username
        except UsernameOccupied:
            continue
        except FloodWait as e:
            # Handle flood wait
            await asyncio.sleep(e.value)
            try:
                await user_client.set_username(new_username)
                return new_username
            except:
                continue
        except Exception as e:
            # Don't break on other errors, continue trying
            print(f"Error setting username {new_username}: {e}")
            continue
    
    return None

async def save_original_profile(user_client: Client, user_id: int):
    """Save user's original profile data"""
    try:
        me = await user_client.get_me()
        my_chat = await user_client.get_chat("me")
        
        photos_data = []
        async for photo in user_client.get_chat_photos("me", limit=3):
            photo_bytes = await user_client.download_media(photo.file_id, in_memory=True)
            photos_data.append(bytes(photo_bytes.getvalue()))
        
        ORIGINAL_PROFILES[user_id] = {
            "first_name": me.first_name or "",
            "last_name": me.last_name or "",
            "bio": my_chat.bio or "",
            "username": me.username or "",
            "photos_data": photos_data
        }
        return True
    except:
        return False

async def restore_original_profile(user_client: Client, user_id: int):
    """Restore user's original profile data"""
    try:
        if user_id not in ORIGINAL_PROFILES:
            return False
        
        original_data = ORIGINAL_PROFILES[user_id]
        
        # Delete current photos
        async for photo in user_client.get_chat_photos("me"):
            await user_client.delete_profile_photos(photo.file_id)
        
        # Restore photos
        for photo_bytes in original_data.get("photos_data", []):
            photo_file = BytesIO(photo_bytes)
            photo_file.name = "photo.jpg"
            await user_client.set_profile_photo(photo=photo_file)
        
        # Restore profile info
        await user_client.update_profile(
            first_name=original_data.get("first_name", ""),
            last_name=original_data.get("last_name", ""),
            bio=original_data.get("bio", "")[:140]
        )
        
        # Restore username
        if original_data.get("username"):
            try:
                await user_client.set_username(original_data.get("username"))
            except:
                pass
        
        del ORIGINAL_PROFILES[user_id]
        return True
    except:
        return False

# ==================== HOSTER BOT COMMANDS ====================

@app.on_message(filters.command("start", ["/", "!", "."]) & filters.private)
async def start_hoster_command(_, message: Message):
    caption = (
        "**🌟 Welcome to Romeo Userbot Hoster 🌟**\n\n"
        "🤖 Main aapko instant userbot provide karta hun!\n"
        "📱 Aapko sirf Pyrogram V2 Session String chahiye.\n"
        "🔗 Session String @RJssgbot se le sakte hain.\n\n"
        "**Commands:**\n"
        "• `/host <SESSION_STRING>` - Apna userbot activate karo\n"
        "• `/stop` - Apna userbot deactivate karo\n"
        "• `/status` - Check karo ka aapka userbot chal raha hai ya nahi\n\n"
        "**Only Owner Commands:**\n"
        "• `/restart` - Restart bot\n"
        "• `/listraid` - Show all active raids\n"
        "• `/clearraid` - Clear all raids\n\n"
        "**Owner:** @Romeo_RJ_143"
    )
    buttons = [
        [InlineKeyboardButton("📣 Support Group", url="https://t.me/RomeoBot_op")],
        [InlineKeyboardButton("🔔 Updates Channel", url="https://t.me/Romeo_op")]
    ]
    await message.reply_photo(ALIVE_PIC, caption=caption, reply_markup=InlineKeyboardMarkup(buttons))

@app.on_message(filters.command(["host", "clone"], ["/", "!", "."]) & filters.private)
async def host_client_command(_, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "❌ **Session String nahi diya!**\n\n"
            "✅ **Correct Usage:** `/host YOUR_SESSION_STRING`"
        )
    
    user_id = message.from_user.id
    
    if user_id in HOSTED_CLIENTS:
        return await message.reply_text(
            "⚠️ **Aapka userbot pehle se active hai!**\n"
            "Pehle `/stop` command use karo, phir dubara host karo."
        )
    
    session_string = message.command[1]
    op = await message.reply_text("🔄 **Aapka userbot start ho raha hai...**")
    
    try:
        client_name = f"userbot_{user_id}_{int(time.time())}"
        new_client = Client(
            name=client_name,
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=session_string,
            in_memory=True,
            no_updates=False
        )
        
        await new_client.start()
        user = await new_client.get_me()
        
        HOSTED_CLIENTS[user_id] = new_client
        
        if user_id not in ACTIVATE_RLIST:
            ACTIVATE_RLIST[user_id] = []
        if user_id not in ACTIVATE_LLIST:
            ACTIVATE_LLIST[user_id] = []
        
        await register_userbot_handlers(new_client, user_id)
        
        await op.edit(
            f"**✅ Userbot Successfully Activated!**\n\n"
            f"**👤 Account:** {user.first_name}\n"
            f"**🆔 ID:** `{user.id}`\n"
            f"**📝 Username:** @{user.username if user.username else 'None'}\n\n"
            f"**💡 Ab aap apne account pe `.help` command use kar sakte hain!**\n"
            f"**⏹️ Stop karne ke liye:** `/stop`"
        )
    except Exception as e:
        if user_id in HOSTED_CLIENTS:
            del HOSTED_CLIENTS[user_id]
        await op.edit(
            f"**❌ Error ho gaya!**\n\n"
            f"**Error:** `{str(e)}`\n\n"
            f"Please check:\n"
            f"• Session String valid hai ya nahi\n"
            f"• Internet connection theek hai ya nahi"
        )

@app.on_message(filters.command("stop", ["/", "!"]) & filters.private)
async def stop_client_command(_, message: Message):
    user_id = message.from_user.id
    
    if user_id not in HOSTED_CLIENTS:
        return await message.reply_text(
            "❌ **Aapka koi userbot active nahi hai!**\n"
            "Pehle `/host SESSION_STRING` use karo."
        )
    
    try:
        await HOSTED_CLIENTS[user_id].stop()
        del HOSTED_CLIENTS[user_id]
        
        if user_id in ACTIVATE_RLIST:
            del ACTIVATE_RLIST[user_id]
        if user_id in ACTIVATE_LLIST:
            del ACTIVATE_LLIST[user_id]
        if user_id in ORIGINAL_PROFILES:
            del ORIGINAL_PROFILES[user_id]
        
        await message.reply_text(
            "✅ **Aapka userbot successfully stop ho gaya!**\n"
            "Dubara activate karne ke liye `/host` command use karo."
        )
    except Exception as e:
        await message.reply_text(f"❌ **Error:** `{e}`")

@app.on_message(filters.command("status", ["/", "!"]) & filters.private)
async def status_command(_, message: Message):
    user_id = message.from_user.id
    
    if user_id not in HOSTED_CLIENTS:
        return await message.reply_text(
            "❌ **Aapka koi userbot active nahi hai!**\n"
            "Activate karne ke liye: `/host SESSION_STRING`"
        )
    
    try:
        user_client = HOSTED_CLIENTS[user_id]
        me = await user_client.get_me()
        uptime_sec = (datetime.utcnow() - START_TIME).total_seconds()
        uptime = await _human_time_duration(int(uptime_sec))
        
        raid_count = len(ACTIVATE_RLIST.get(user_id, []))
        love_raid_count = len(ACTIVATE_LLIST.get(user_id, []))
        
        await message.reply_text(
            f"**✅ Aapka Userbot Active Hai!**\n\n"
            f"**👤 Account:** {me.first_name}\n"
            f"**🆔 ID:** `{me.id}`\n"
            f"**⏱️ Uptime:** `{uptime}`\n"
            f"**📊 Total Hosted Users:** `{len(HOSTED_CLIENTS)}`\n"
            f"**🔄 Profile Cloned:** `{'Yes' if user_id in ORIGINAL_PROFILES else 'No'}`\n"
            f"**🔥 Active Raids:** `{raid_count}`\n"
            f"**💕 Active Love Raids:** `{love_raid_count}`"
        )
    except Exception as e:
        await message.reply_text(f"❌ **Error:** `{e}`")

# Admin Commands
@app.on_message(filters.command("restart", ["/", "!"]) & filters.private)
async def restart_command(_, message: Message):
    user_id = message.from_user.id
    
    if user_id not in SUDO_USERS:
        return await message.reply_text("❌ **Sirf Owner/Sudo users ye command use kar sakte hain!**")
    
    op = await message.reply_text("🔄 **Restarting bot and clearing all hosted clients...**")
    
    for uid, user_client in list(HOSTED_CLIENTS.items()):
        try:
            await user_client.stop()
        except:
            pass
    
    HOSTED_CLIENTS.clear()
    ORIGINAL_PROFILES.clear()
    ACTIVATE_RLIST.clear()
    ACTIVATE_LLIST.clear()
    
    await op.edit(
        "✅ **Bot restarted successfully!**\n"
        "• Sare hosted userbots deactivate ho gaye hain\n"
        "• Users ko dubara host karna hoga"
    )
    
    os.execl(sys.executable, sys.executable, *sys.argv)

@app.on_message(filters.command("listraid", ["/", "!"]) & filters.private)
async def bot_list_raids(_, message: Message):
    user_id = message.from_user.id
    
    if user_id not in SUDO_USERS:
        return await message.reply_text("❌ **Sirf Owner/Sudo users ye command use kar sakte hain!**")
    
    raid_text = "**📋 All Active Reply Raids:**\n\n"
    total_raids = 0
    total_love_raids = 0
    
    for hoster_id, raid_list in ACTIVATE_RLIST.items():
        if raid_list:
            raid_text += f"**🔥 User {hoster_id}'s Raids:** {len(raid_list)} targets\n"
            total_raids += len(raid_list)
    
    for hoster_id, raid_list in ACTIVATE_LLIST.items():
        if raid_list:
            raid_text += f"**💕 User {hoster_id}'s Love Raids:** {len(raid_list)} targets\n"
            total_love_raids += len(raid_list)
    
    raid_text += f"\n**📊 Total Stats:**\n"
    raid_text += f"• Normal Raids: `{total_raids}`\n"
    raid_text += f"• Love Raids: `{total_love_raids}`\n"
    raid_text += f"• Active Hosters: `{len(HOSTED_CLIENTS)}`"
    
    await message.reply_text(raid_text)

@app.on_message(filters.command("clearraid", ["/", "!"]) & filters.private)
async def bot_clear_all_raids(_, message: Message):
    user_id = message.from_user.id
    
    if user_id not in SUDO_USERS:
        return await message.reply_text("❌ **Sirf Owner/Sudo users ye command use kar sakte hain!**")
    
    ACTIVATE_RLIST.clear()
    ACTIVATE_LLIST.clear()
    
    await message.reply_text(
        "**✅ All Reply Raids Cleared!**\n\n"
        "• Sabhi hosters ke raids clear kar diye gaye hain\n"
        "• Ab koi reply raid active nahi hai"
    )

# ==================== REGISTER USERBOT HANDLERS ====================

async def register_userbot_handlers(user_client: Client, owner_id: int):
    """Register all userbot handlers for a hosted client"""
    
    @user_client.on_message(filters.command("help", ".") & filters.me)
    async def help_cmd(_, message: Message):
        help_text = """
**✨ Romeo Userbot Commands ✨**

**Basic:**
• `.alive` - Check bot status
• `.ping` - Check response time  
• `.help` - Show this message

**Spam Commands:**
• `.spam [count]` - Reply to any media/text to spam
• `.raid <count> <user>` - Raid a user
• `.lraid <count> <user>` - Love raid
• `.pornspam <count>` - Adult content spam
• `.hang <count>` - Hang messages

**Profile:**
• `.clone <user>` - Clone someone's profile
• `.revert` - Revert to original profile

**Utility:**
• `.all [text]` - Tag all members
• `.cancel` - Stop tagging

**Reply Raids:**
• `.rr <user>` - Activate reply raid
• `.drr <user>` - Deactivate reply raid
• `.rlr <user>` - Activate love reply raid
• `.drlr <user>` - Deactivate love reply raid

**Owner:** @Romeo_RJ_143
        """
        await eor(message, help_text)
    
    @user_client.on_message(filters.command(["alive", "ping"], ".") & filters.me)
    async def alive_cmd(_, message: Message):
        start = time.time()
        uptime_sec = (datetime.utcnow() - START_TIME).total_seconds()
        uptime = await _human_time_duration(int(uptime_sec))
        ping_ms = (time.time() - start) * 1000
        
        caption = (
            f"**✨ Romeo Userbot is Alive!**\n\n"
            f"**⚡ Ping:** `{ping_ms:.2f}ms`\n"
            f"**⏱️ Uptime:** `{uptime}`\n"
            f"**🐍 Python:** `{python_version()}`\n"
            f"**🔥 Pyrogram:** `{__version__}`\n"
            f"**👤 User:** {message.from_user.mention}"
        )
        
        if message.command[0].lower() == "alive":
            await message.reply_photo(photo=ALIVE_PIC, caption=caption)
            await message.delete()
        else:
            await eor(message, caption)
    
    @user_client.on_message(filters.command("clone", ".") & filters.me)
    async def clone_cmd(_, message: Message):
        if owner_id in ORIGINAL_PROFILES:
            return await eor(message, 
                "⚠️ **Already cloned someone's profile!**\n"
                "Use `.revert` first to restore original profile."
            )
        
        text = get_text(message)
        user = await get_user(message, text, user_client)
        
        if not user:
            return await eor(message, "`Reply to user or give username/id!`")
        
        op = await eor(message, "`🔄 Cloning profile...`")
        
        try:
            await op.edit("`📸 Saving your original profile...`")
            saved = await save_original_profile(user_client, owner_id)
            
            if not saved:
                return await op.edit("`❌ Failed to save original profile!`")
            
            await op.edit("`🎯 Getting target user's profile...`")
            target_chat = await user_client.get_chat(user.id)
            
            await op.edit("`🗑️ Clearing current profile photos...`")
            async for photo in user_client.get_chat_photos("me"):
                await user_client.delete_profile_photos(photo.file_id)
            
            await op.edit("`📷 Setting new profile photos...`")
            photo_count = 0
            async for photo in user_client.get_chat_photos(user.id, limit=3):
                photo_bytes = await user_client.download_media(photo.file_id, in_memory=True)
                await user_client.set_profile_photo(photo=photo_bytes)
                photo_count += 1
            
            await op.edit("`📝 Updating profile info...`")
            new_bio = target_chat.bio[:140] if target_chat.bio else ""
            
            await user_client.update_profile(
                first_name=user.first_name or "User",
                last_name=user.last_name or "",
                bio=new_bio
            )
            
            # Try to set username if target has one
            username_status = "Not Changed"
            if user.username:
                await op.edit("`🔤 Trying to set unique username...`")
                new_username = await generate_unique_username(user_client, user.username)
                if new_username:
                    username_status = f"@{new_username}"
                else:
                    username_status = "Could not set (all variations taken or error)"
            
            await op.edit(
                f"**✅ Successfully Cloned Profile!**\n\n"
                f"**👤 Cloned:** {user.first_name}\n"
                f"**🆔 User ID:** `{user.id}`\n"
                f"**📷 Photos Cloned:** `{photo_count}`\n"
                f"**📝 Username:** `{username_status}`\n\n"
                f"**💡 Use** `.revert` **to restore original profile**"
            )
        except Exception as e:
            if owner_id in ORIGINAL_PROFILES:
                await restore_original_profile(user_client, owner_id)
            await op.edit(f"`❌ Error: {e}`")
    
    @user_client.on_message(filters.command("revert", ".") & filters.me)
    async def revert_cmd(_, message: Message):
        if owner_id not in ORIGINAL_PROFILES:
            return await eor(message,
                "⚠️ **No saved profile data found!**\n"
                "You haven't cloned any profile yet."
            )
        
        op = await eor(message, "`🔄 Reverting to original profile...`")
        
        success = await restore_original_profile(user_client, owner_id)
        
        if success:
            await op.edit(
                "**✅ Profile Successfully Reverted!**\n\n"
                "Your original profile has been restored.\n"
                "• Profile photos ✅\n"
                "• Name & Bio ✅\n"
                "• Username ✅"
            )
        else:
            await op.edit("❌ **Failed to revert profile!**")
    
    @user_client.on_message(filters.command("spam", ".") & filters.me)
    async def spam_cmd(_, message: Message):
        if not message.reply_to_message:
            return await eor(message, "`Reply to a message!`")
        
        try:
            count = int(message.command[1]) if len(message.command) > 1 else 10
        except:
            return await eor(message, "`Invalid count!`")
        
        if count > 100 or count < 1:
            return await eor(message, "`Count should be 1-100!`")
        
        reply = message.reply_to_message
        await message.delete()
        
        for _ in range(count):
            try:
                if reply.sticker:
                    await user_client.send_sticker(message.chat.id, reply.sticker.file_id)
                elif reply.animation:
                    await user_client.send_animation(message.chat.id, reply.animation.file_id)
                elif reply.photo:
                    await user_client.send_photo(message.chat.id, reply.photo.file_id)
                elif reply.video:
                    await user_client.send_video(message.chat.id, reply.video.file_id)
                elif reply.voice:
                    await user_client.send_voice(message.chat.id, reply.voice.file_id)
                elif reply.text:
                    await user_client.send_message(message.chat.id, reply.text)
                elif reply.caption:
                    await user_client.send_message(message.chat.id, reply.caption)
                
                await asyncio.sleep(0.3)
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except:
                continue
    
    # Combined RAID and LRAID handler
    @user_client.on_message(filters.command(["raid", "r", "lraid", "lr"], ".") & filters.me)
    async def raid_cmd(_, message: Message):
        is_love = message.command[0][0] == 'l'
        text = get_text(message)
        
        try:
            if text:
                parts = text.split(None, 1)
                count = int(parts[0])
                target_str = parts[1] if len(parts) > 1 else None
            elif message.reply_to_message:
                count = int(message.command[1]) if len(message.command) > 1 else 10
                target_str = None
            else:
                return await eor(message, f"`Usage: .{'l' if is_love else ''}raid <count> <user>`")
            
            if message.reply_to_message:
                user = message.reply_to_message.from_user
            elif target_str:
                user = await user_client.get_users(target_str)
            else:
                return await eor(message, "`Reply to user or give username/id!`")
            
            if user.id in SUDO_USERS or user.id in VERIFIED_USERS:
                return await eor(message, f"`Can't raid {user.first_name}!`")
            
            await message.delete()
            
            for _ in range(count):
                raid_msg = random.choice(LOVE if is_love else RAID)
                await user_client.send_message(message.chat.id, f"{user.mention} {raid_msg}")
                await asyncio.sleep(0.3)
        except Exception as e:
            await eor(message, f"`Error: {e}`")
    
    # Combined PORNSPAM and HANG handler
    @user_client.on_message(filters.command(["pornspam", "psm", "hang"], ".") & filters.me)
    async def spam_cmds(_, message: Message):
        if message.chat.id in GROUP:
            return await eor(message, "`Can't spam in this group!`")
        
        try:
            count = int(message.command[1]) if len(message.command) > 1 else 5
        except:
            return await eor(message, f"`Usage: .{message.command[0]} <count>`")
        
        await message.delete()
        is_hang = message.command[0] == "hang"
        romeo = "⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰😈꙰꙰꙰꙰꙰꙰⃟꙰⃟꙰⃟꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰😈꙰꙰꙰꙰꙰꙰⃟꙰⃟꙰⃟꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰😈꙰꙰꙰꙰꙰꙰⃟꙰⃟꙰⃟꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰😈꙰꙰꙰꙰꙰꙰⃟꙰⃟꙰⃟꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰⃟꙰⃟꙰⃟꙰꙰"
        
        for _ in range(count):
            try:
                if is_hang:
                    await user_client.send_message(message.chat.id, romeo)
                else:
                    await user_client.send_video(message.chat.id, video=random.choice(PORM))
                await asyncio.sleep(0.5)
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except:
                pass
    
    @user_client.on_message(filters.command("all", ".") & filters.me)
    async def tagall_cmd(_, message: Message):
        text = get_text(message) or "Hello Everyone!"
        await message.delete()
        
        members_text = ""
        count = 0
        
        async for member in user_client.get_chat_members(message.chat.id):
            if member.user.is_bot or member.user.is_deleted:
                continue
            
            members_text += f"[{member.user.first_name}](tg://user?id={member.user.id}) "
            count += 1
            
            if count == 5:
                await user_client.send_message(message.chat.id, f"{text}\n\n{members_text}")
                members_text = ""
                count = 0
                await asyncio.sleep(2)
        
        if members_text:
            await user_client.send_message(message.chat.id, f"{text}\n\n{members_text}")
    
    @user_client.on_message(filters.command("cancel", ".") & filters.me)
    async def cancel_cmd(_, message: Message):
        global spam_chats
        if message.chat.id in spam_chats:
            spam_chats.remove(message.chat.id)
            await eor(message, "`✅ Tagging cancelled!`")
        else:
            await eor(message, "`❌ No active tagging in this chat!`")
    
    # Reply Raid commands
    @user_client.on_message(filters.command(["rr", "rlr"], ".") & filters.me)
    async def activate_raid(_, message: Message):
        is_love = message.command[0] == "rlr"
        text = get_text(message)
        user = await get_user(message, text, user_client)
        
        if not user:
            return await eor(message, "`Reply to user or give username/id!`")
        
        if user.id in SUDO_USERS or user.id in VERIFIED_USERS:
            return await eor(message, f"`Can't raid sudo/verified users!`")
        
        raid_list = ACTIVATE_LLIST if is_love else ACTIVATE_RLIST
        
        if owner_id not in raid_list:
            raid_list[owner_id] = []
        
        if user.id in raid_list[owner_id]:
            return await eor(message, f"`Already activated for {user.first_name}!`")
        
        raid_list[owner_id].append(user.id)
        
        emoji = "💕" if is_love else "✅"
        raid_type = "Love Reply" if is_love else "Reply"
        await eor(message, f"**{emoji} {raid_type} Raid Activated!**\n**User:** {user.mention}")
    
    @user_client.on_message(filters.command(["drr", "drlr"], ".") & filters.me)
    async def deactivate_raid(_, message: Message):
        is_love = message.command[0] == "drlr"
        text = get_text(message)
        user = await get_user(message, text, user_client)
        
        if not user:
            return await eor(message, "`Reply to user or give username/id!`")
        
        raid_list = ACTIVATE_LLIST if is_love else ACTIVATE_RLIST
        sender = await user_client.get_me()
        
        if sender.id in SUDO_USERS:
            deactivated = False
            for hoster_id, raids in list(raid_list.items()):
                if user.id in raids:
                    raid_list[hoster_id].remove(user.id)
                    deactivated = True
            
            if deactivated:
                raid_type = "Love Reply" if is_love else "Reply"
                await eor(message, f"**❌ {raid_type} Raid Deactivated by Admin!**\n**Target:** {user.mention}")
            else:
                await eor(message, f"`Not activated for {user.first_name}!`")
        else:
            if owner_id not in raid_list or user.id not in raid_list[owner_id]:
                return await eor(message, f"`Not activated for {user.first_name}!`")
            
            raid_list[owner_id].remove(user.id)
            raid_type = "Love Reply" if is_love else "Reply"
            await eor(message, f"**❌ {raid_type} Raid Deactivated!**\n**User:** {user.mention}")
    
    @user_client.on_message(filters.incoming & ~filters.bot & ~filters.service)
    async def auto_reply_raid(_, message: Message):
        if not message.from_user:
            return
        
        user_id = message.from_user.id
        
        if owner_id in ACTIVATE_RLIST and user_id in ACTIVATE_RLIST[owner_id]:
            try:
                await user_client.send_message(
                    message.chat.id,
                    f"{message.from_user.mention} {random.choice(RAID)}",
                    reply_to_message_id=message.id
                )
            except:
                pass
        
        elif owner_id in ACTIVATE_LLIST and user_id in ACTIVATE_LLIST[owner_id]:
            try:
                await user_client.send_message(
                    message.chat.id,
                    f"{message.from_user.mention} {random.choice(LOVE)}",
                    reply_to_message_id=message.id
                )
            except:
                pass

# ==================== MAIN ====================

async def start_bots():
    print("INFO: Starting Hoster Bot...")
    await app.start()
    print("INFO: Hoster Bot started successfully!")
    
    print("INFO: Starting Owner's Userbot...")
    await client.start()
    me = await client.get_me()
    print(f"INFO: Owner's Userbot started as {me.first_name} ({me.id})")
    
    await register_userbot_handlers(client, OWNER_ID)
    
    if OWNER_ID not in ACTIVATE_RLIST:
        ACTIVATE_RLIST[OWNER_ID] = []
    if OWNER_ID not in ACTIVATE_LLIST:
        ACTIVATE_LLIST[OWNER_ID] = []
    
    print("========================================")
    print("   Romeo Userbot System Ready!   ")
    print("========================================")
    
    await idle()

if __name__ == "__main__":
    print("========================================")
    print("   Romeo Userbot Starting Up...   ")
    print("========================================")
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_bots())
