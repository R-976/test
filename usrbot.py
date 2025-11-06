import os
import sys
import json
import random
import asyncio
import re
from time import time
from datetime import datetime
from platform import python_version
from os import getenv

from pyrogram import Client, filters, idle, enums, __version__
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import FloodWait

from PIL import Image

# ================================== CONFIG ================================== #

API_ID = int(getenv("API_ID", "10796618"))
API_HASH = getenv("API_HASH", "4e4b20b4e1e40c90fcb1a7658c800150")
BOT_TOKEN = getenv("BOT_TOKEN", "7239889663:AAHGtiWGzzW2jmBilVr7XCJILQgF7LJwWJo")
OWNER_ID = int(getenv("OWNER_ID", "7041789891"))
STRING_SESSION = getenv("STRING_SESSION", "AQCkvkoAnnHGkIIZQ5yHyPJnOayPezXh1mqEdr9r-at5XO4GoaKaQgDHTNsMHShsAuXfIfQ8_eHoOu4JfDOgscr_gFmhYNGZ0pH-ASBVpaOBTMSQxBBiNfyCE0Sc7-lI-Qi2S-g68tbIj8WtVw8AACtGTtmIyIaBTR_s2LzYDjUozB1y2UTCsh_zHFWlttZ7975tnovdJfJYabxXWuYmQXQBurnG9AihGX8sJwK268TCujpqF8Vl8khbc6V1QscNoifU26uRofKGWTSRBR54PqiMVqvXeOiKmQQd_39L9MS5GrhCs-OpEtsEknyGMPPPkIqvzcZZ3pvot4xd4SKfIoiQlLx0UwAAAAHv15psAA")
SUDO_USERS = list(map(int, getenv("SUDO_USERS", "7041789891").split()))
ALIVE_PIC = getenv("ALIVE_PIC", "https://telegra.ph/file/a62b9c7d9848afde0569e.jpg")
BIO_FALLBACK = getenv("BIO", "Romeo Userbot")

# ================================== GLOBALS ================================= #

START_TIME = datetime.utcnow()
SUDO_USERS.append(OWNER_ID)

# State lists
spam_chats = []
ACTIVATE_RLIST = []  # Reply Raid
ACTIVATE_LLIST = []  # Reply Love Raid

# Temporary hosted clients dictionary
HOSTED_CLIENTS = {}  # {user_id: client_instance}

# Content Lists
LOVE = [
    "𝒀𝒂𝒓 𝑨𝒑𝒌𝒊 𝑩𝒂𝒕𝒆𝒏 𝑺𝒖𝒏 𝑲𝒂𝒓 𝑻𝒐 𝑴𝒖𝒋𝒆 𝑨𝒑𝒌𝒐 𝑴𝒆𝒓𝒊 𝑱𝒂𝒂𝒏𝒖 𝑩𝒂𝒏𝒐𝒈𝒊 𝑨𝒘𝒂𝒓𝒅 𝑫𝒆𝒏𝒆 𝑲𝒂 𝑴𝒂𝒏 𝑲𝒂𝒓 𝑹𝒂𝒉𝒂 𝒉𝒂𝒊",
    "आप इतने क्यूट हो की अगर 𝑴𝑺𝑮 ना भी करना चाहू. तो भी हाथ खुद कीपैड पर चलने लगता है !",
    "मै तो सिर्फ तुम्हारे प्यार का नशा करता हु , एंड उसके हेंग ओवर के आगे कोई और नशे की जरुरत नहीं है !",
    "कुछ ऐसे हस्दे ज़िन्दगी मैं होते है🤔🤔, के इंसान तो बच जाता है मगर ज़िंदा नहीं रहता😂💓",
]
RAID = [
    "𝐌𝐀𝐃𝐀𝐑𝐂𝐇𝐎𝐃", "BHOSDIKE", "LAAAWEEE KE BAAAAAL",
    "TERA MAA MERI FAN", "TERI SEXY BAHEN KI CHUT OP",
]
PORM = [
    "https://telegra.ph/file/9bcc076fd81dfe3feb291.mp4",
    "https://telegra.ph/file/b7a1a42429a65f64e67af.mp4",
    "https://telegra.ph/file/a8bf6c6df8a48e4a306ca.jpg",
    "https://telegra.ph/file/af9e3f98da0bd937adf6e.jpg",
]

# Restricted Groups
GROUP = [-1001265778325, -1001625889213, -1001678976340]
VERIFIED_USERS = [5368154755, 5353539036, 5392070730] # Devs, etc.

# ============================ INITIALIZING CLIENTS ============================ #

# Hoster Bot Client
app = Client(
    name="HosterBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True
)

# Main Userbot Client (Owner's)
client = Client(
    name="Userbot",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=STRING_SESSION,
    in_memory=True
)

# ================================== HELPERS ================================== #

async def eor(message: Message, text: str, **kwargs):
    """Edit own message or reply to the user's message."""
    if message.from_user.is_self:
        return await message.edit_text(text, **kwargs)
    return await message.reply_text(text, **kwargs)

def get_text(message: Message):
    """Extract text from a command message."""
    text = message.text or ""
    if " " in text:
        return text.split(None, 1)[1]
    return None

async def get_user(message: Message, text: str):
    """Get user from a message."""
    if message.reply_to_message:
        return message.reply_to_message.from_user
    if not text:
        return None
    
    try:
        if text.strip().isdigit():
            return await client.get_users(int(text))
        else:
            return await client.get_users(text)
    except Exception:
        return None

async def _human_time_duration(seconds):
    """Convert seconds to a human-readable format."""
    if seconds == 0:
        return 'inf'
    parts = []
    for unit, div in (('Week', 604800), ('Day', 86400), ('Hour', 3600), ('Min', 60), ('Sec', 1)):
        amount, seconds = divmod(int(seconds), div)
        if amount > 0:
            parts.append(f'{amount} {unit}{"s" if amount > 1 else ""}')
    return ', '.join(parts)

# ================================== HOSTER BOT COMMANDS ================================ #

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
        "• `/status` - Check karo ki aapka userbot chal raha hai ya nahi\n\n"
        "**Owner:** @Romeo_RJ_143"
    )
    buttons = [
        [InlineKeyboardButton("📣 Support Group", url="https://t.me/RomeoBot_op")],
        [InlineKeyboardButton("🔔 Updates Channel", url="https://t.me/Romeo_op")]
    ]
    await message.reply_photo(
        photo=ALIVE_PIC,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@app.on_message(filters.command(["host", "clone"], ["/", "!", "."]) & filters.private)
async def host_client_command(_, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "❌ **Session String nahi diya!**\n\n"
            "✅ **Correct Usage:** `/host YOUR_SESSION_STRING`"
        )

    user_id = message.from_user.id
    
    # Check if user already has a hosted client
    if user_id in HOSTED_CLIENTS:
        return await message.reply_text(
            "⚠️ **Aapka userbot pehle se active hai!**\n"
            "Pehle `/stop` command use karo, phir dubara host karo."
        )
    
    session_string = message.command[1]
    op = await message.reply_text("🔄 **Aapka userbot start ho raha hai...**")
    
    try:
        # Create new client for this user
        client_name = f"userbot_{user_id}_{int(time())}"
        new_client = Client(
            name=client_name,
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=session_string,
            in_memory=True,
            no_updates=False
        )
        
        # Start the client
        await new_client.start()
        user = await new_client.get_me()
        
        # Store client in dictionary
        HOSTED_CLIENTS[user_id] = new_client
        
        # Register all userbot handlers for this client
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
        
        await message.reply_text(
            f"**✅ Aapka Userbot Active Hai!**\n\n"
            f"**👤 Account:** {me.first_name}\n"
            f"**🆔 ID:** `{me.id}`\n"
            f"**⏱️ Uptime:** `{uptime}`\n"
            f"**📊 Total Hosted Users:** `{len(HOSTED_CLIENTS)}`"
        )
    except Exception as e:
        await message.reply_text(f"❌ **Error:** `{e}`")

@app.on_message(filters.command("restart", ["/", "!"]) & filters.private)
async def restart_command(_, message: Message):
    user_id = message.from_user.id
    
    # Check if user is owner or sudo
    if user_id not in SUDO_USERS:
        return await message.reply_text("❌ **Sirf Owner/Sudo users ye command use kar sakte hain!**")
    
    op = await message.reply_text("🔄 **Restarting bot and clearing all hosted clients...**")
    
    # Stop all hosted clients
    for uid, user_client in list(HOSTED_CLIENTS.items()):
        try:
            await user_client.stop()
        except:
            pass
    
    HOSTED_CLIENTS.clear()
    
    await op.edit(
        "✅ **Bot restarted successfully!**\n"
        "• Sare hosted userbots deactivate ho gaye hain\n"
        "• Users ko dubara host karna hoga"
    )
    
    # Restart the bot (this will exit the script, you need process manager to restart it)
    os.execl(sys.executable, sys.executable, *sys.argv)

# ========================= REGISTER USERBOT HANDLERS ========================= #

async def register_userbot_handlers(user_client: Client, owner_id: int):
    """Register all userbot handlers for a hosted client"""
    
    # Helper function specific to this client
    async def client_eor(message: Message, text: str, **kwargs):
        if message.from_user.is_self:
            return await message.edit_text(text, **kwargs)
        return await message.reply_text(text, **kwargs)
    
    # HELP Command
    @user_client.on_message(filters.command("help", ".") & filters.me)
    async def help_cmd(_, message: Message):
        help_text = """
**✨ Romeo Userbot Commands ✨**

**Basic:**
• `.alive` - Check bot status
• `.ping` - Check response time  
• `.help` - Show this message

**Spam:**
• `.raid <count> <user>` - Raid a user
• `.lraid <count> <user>` - Love raid
• `.dmraid <count> <user>` - DM raid
• `.pornspam <count>` - Spam adult content
• `.sspam <count>` - Spam stickers
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
        await client_eor(message, help_text)
    
    # ALIVE Command
    @user_client.on_message(filters.command(["alive", "ping"], ".") & filters.me)
    async def alive_cmd(_, message: Message):
        start = time()
        uptime_sec = (datetime.utcnow() - START_TIME).total_seconds()
        uptime = await _human_time_duration(int(uptime_sec))
        ping_ms = (time() - start) * 1000
        
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
            await client_eor(message, caption)
    
    # RAID Commands
    @user_client.on_message(filters.command(["raid", "r"], ".") & filters.me)
    async def raid_cmd(_, message: Message):
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
                return await client_eor(message, "`Usage: .raid <count> <user/reply>`")
                
            if message.reply_to_message:
                user = message.reply_to_message.from_user
            elif target_str:
                try:
                    user = await user_client.get_users(target_str)
                except:
                    return await client_eor(message, "`User not found!`")
            else:
                return await client_eor(message, "`Reply to user or give username/id!`")
                
            if user.id in SUDO_USERS or user.id in VERIFIED_USERS:
                return await client_eor(message, f"`Can't raid {user.first_name}!`")
                
            await message.delete()
            for _ in range(count):
                await user_client.send_message(
                    message.chat.id, 
                    f"{user.mention} {random.choice(RAID)}"
                )
                await asyncio.sleep(0.3)
                
        except Exception as e:
            await client_eor(message, f"`Error: {e}`")
    
    # LOVE RAID Command
    @user_client.on_message(filters.command(["lraid", "lr"], ".") & filters.me)
    async def lraid_cmd(_, message: Message):
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
                return await client_eor(message, "`Usage: .lraid <count> <user/reply>`")
                
            if message.reply_to_message:
                user = message.reply_to_message.from_user
            elif target_str:
                try:
                    user = await user_client.get_users(target_str)
                except:
                    return await client_eor(message, "`User not found!`")
            else:
                return await client_eor(message, "`Reply to user or give username/id!`")
                
            await message.delete()
            for _ in range(count):
                await user_client.send_message(
                    message.chat.id, 
                    f"{user.mention} {random.choice(LOVE)}"
                )
                await asyncio.sleep(0.3)
                
        except Exception as e:
            await client_eor(message, f"`Error: {e}`")
    
    # PORNSPAM Command
    @user_client.on_message(filters.command(["pornspam", "psm"], ".") & filters.me)
    async def pornspam_cmd(_, message: Message):
        if message.chat.id in GROUP:
            return await client_eor(message, "`Can't spam in this group!`")
            
        try:
            count = int(message.command[1]) if len(message.command) > 1 else 5
        except:
            return await client_eor(message, "`Usage: .pornspam <count>`")
            
        await message.delete()
        for _ in range(count):
            try:
                await user_client.send_video(message.chat.id, video=random.choice(PORM))
                await asyncio.sleep(0.5)
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except:
                pass
    
    # HANG Command
    @user_client.on_message(filters.command("hang", ".") & filters.me)
    async def hang_cmd(_, message: Message):
        if message.chat.id in GROUP:
            return await client_eor(message, "`Can't spam in this group!`")
            
        try:
            count = int(message.command[1]) if len(message.command) > 1 else 5
        except:
            return await client_eor(message, "`Usage: .hang <count>`")
            
        await message.delete()
        hang_text = "⃟" * 1000
        for _ in range(count):
            await user_client.send_message(message.chat.id, hang_text)
            await asyncio.sleep(0.5)
    
    # CLONE Command
    @user_client.on_message(filters.command("clone", ".") & filters.me)
    async def clone_cmd(_, message: Message):
        text = get_text(message)
        
        if message.reply_to_message:
            user = message.reply_to_message.from_user
        elif text:
            try:
                user = await user_client.get_users(text)
            except:
                return await client_eor(message, "`User not found!`")
        else:
            return await client_eor(message, "`Reply to user or give username/id!`")
            
        op = await client_eor(message, "`Cloning profile...`")
        
        try:
            # Get target user's info
            target_chat = await user_client.get_chat(user.id)
            
            # Delete current photos
            async for photo in user_client.get_chat_photos("me"):
                await user_client.delete_profile_photos(photo.file_id)
            
            # Set new photos
            async for photo in user_client.get_chat_photos(user.id, limit=3):
                await user_client.set_profile_photo(photo=photo.file_id)
            
            # Update profile
            await user_client.update_profile(
                first_name=user.first_name or "User",
                last_name=user.last_name or "",
                bio=target_chat.bio or ""
            )
            
            await op.edit(f"**✅ Successfully cloned {user.first_name}'s profile!**")
            
        except Exception as e:
            await op.edit(f"`Error: {e}`")
    
    # REVERT Command
    @user_client.on_message(filters.command("revert", ".") & filters.me)
    async def revert_cmd(_, message: Message):
        await client_eor(message, 
            "`⚠️ Profile revert feature requires backup!`\n"
            "Please manually update your profile."
        )
    
    # TAG ALL Command
    @user_client.on_message(filters.command("all", ".") & filters.me)
    async def tagall_cmd(_, message: Message):
        chat_id = message.chat.id
        text = get_text(message) or "Hello Everyone!"
        
        await message.delete()
        
        members_text = ""
        count = 0
        
        async for member in user_client.get_chat_members(chat_id):
            if member.user.is_bot or member.user.is_deleted:
                continue
                
            members_text += f"[{member.user.first_name}](tg://user?id={member.user.id}) "
            count += 1
            
            if count == 5:
                await user_client.send_message(chat_id, f"{text}\n\n{members_text}")
                members_text = ""
                count = 0
                await asyncio.sleep(2)
                
        if members_text:
            await user_client.send_message(chat_id, f"{text}\n\n{members_text}")

# ================================== MAIN ================================== #

async def start_bots():
    print("INFO: Starting Hoster Bot...")
    await app.start()
    print("INFO: Hoster Bot started successfully!")
    
    print("INFO: Starting Owner's Userbot...")
    await client.start()
    me = await client.get_me()
    print(f"INFO: Owner's Userbot started as {me.first_name} ({me.id})")
    
    # Register handlers for owner's userbot
    await register_userbot_handlers(client, OWNER_ID)
    
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
