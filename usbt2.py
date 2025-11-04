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
OWNER_ID = int(getenv("OWNER_ID", "8225104035"))
STRING_SESSION = getenv("STRING_SESSION", "BQCkvkoAABXx6RmFR0EKhAD7R1mgsUabKT7V9yNoY2z2jpEZr5KIVXTmCHa0eIwLSLYY73q682hTaw1HfQ5Nct7UrSayeYfwH57SpnCoPhKShrTXZD2BoTDN0u_-LWofdW-rueobtmUMe0XFg3K5wpbzWM7ou6y2r-y2prmpQ5fGCbURLbsZm_iXoYKOwCZoi3_dVMMLV2DWnG6D2cJEX0fsP8CcC28tfq3ygUSrJSuZn85CM3EWcHLVgqjBlkgQSYVnZIt_UPUX9vx3TjKbZm5WRZwQfGklCUgkPJQNjI1W1CWBT63BjCDoeu-Zk_Q0bdB6_vZzZeeouzqt7KpCJCiuZJ8QmwAAAAHqQSCjAA")
SUDO_USERS = list(map(int, getenv("SUDO_USERS", "8225104035").split()))
ALIVE_PIC = getenv("ALIVE_PIC", "https://telegra.ph/file/a62b9c7d9848afde0569e.jpg")
BIO_FALLBACK = getenv("BIO", "Romeo Userbot")

# ================================== GLOBALS ================================= #

START_TIME = datetime.utcnow()
SUDO_USERS.append(OWNER_ID)

# State lists
spam_chats = []
ACTIVATE_RLIST = []  # Reply Raid
ACTIVATE_LLIST = []  # Reply Love Raid

# Content Lists
LOVE = [
    "𝒀𝒂𝒓 𝑨𝒑𝒌𝒊 𝑩𝒂𝒕𝒆𝒏 𝑺𝒖𝒏 𝑲𝒂𝒓 𝑻𝒐 𝑴𝒖𝒋𝒆 𝑨𝒑𝒌𝒐 “𝑴𝒆𝒓𝒊 𝑱𝒂𝒂𝒏𝒖 𝑩𝒂𝒏𝒐𝒈𝒊” 𝑨𝒘𝒂𝒓𝒅 𝑫𝒆𝒏𝒆 𝑲𝒂 𝑴𝒂𝒏 𝑲𝒂𝒓 𝑹𝒂𝒉𝒂 𝒉𝒂𝒊",
    "आप इतने क्यूट हो की अगर 𝑴𝑺𝑮 ना भी करना चाहू. तो भी हाथ खुद कीपैड पर चलने लगता है !",
    "मै तो सिर्फ तुम्हारे प्यार का नशा करता हु , एंड उसके हेंग ओवर के आगे कोई और नशे की जरुरत नहीं है !",
    "कुछ ऐसे हस्दे ज़िन्दगी मैं होते है🤔🤔, के इंसान तो बच जाता है मगर ज़िंदा नहीं रहता😂💓",
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

# Userbot Client
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

async def convert_to_image(message: Message, client: Client) -> str:
    """Convert a sticker to a PNG image."""
    try:
        sticker_path = await client.download_media(message, file_name="temp_sticker.webp")
        with Image.open(sticker_path) as img:
            image_path = "sticker.png"
            img.save(image_path, "png")
        os.remove(sticker_path)
        return image_path
    except Exception as e:
        print(f"Error converting sticker: {e}")
        return None

# ================================== HELP COMMAND ================================== #

HELP_TEXT = """
**✨ Userbot Help Menu ✨**

Yeh ek Userbot hai jo aapke Telegram experience ko behtar banane ke liye banaya gaya hai. Neeche diye gaye commands ka istemal karein.
Sabhi commands ke aage `.` (dot) lagana zaroori hai.

**📝 Utility Commands**
`alive`: Bot zinda hai ya nahi, check karne ke liye.
`ping`: Bot ka server response time check karne ke liye.
`help`: Yeh help message dekhne ke liye.
`all [message]`: Group ke sabhi members ko tag karne ke liye.
`cancel`: `all` command ko rokne ke liye.
`tg [reply to media/text]`: Media ya text ko telegra.ph link me convert karne ke liye.

**🤡 Fun & Spam Commands**
`raid <count> <user/reply>`: Kisi user par gaaliyon ki barsaat karne ke liye.
`lraid <count> <user/reply>`: Kisi user par pyaar bhare messages ki barsaat.
`dmraid <count> <user/reply>`: User ke DM me gaaliyan bhejne ke liye.
`dmlraid <count> <user/reply>`: User ke DM me pyaar bhejne ke liye.
`sspam <count> [reply to sticker]`: Kisi sticker ko baar baar bhejne ke liye.
`pornspam <count>`: Random porn videos/images spam karne ke liye.
`hang <count>`: Screen hang karne wala message bhejne ke liye.
`emoji [text/reply]`: Text ko emoji art me convert karne ke liye.
`cmoji <emoji> [text/reply]`: Custom emoji se text art banane ke liye.

**🎭 Account Cloning**
`clone <user/reply>`: Kisi aur user ka profile (Naam, Bio, DP) copy karne ke liye.
`revert`: Apne original profile par wapas aane ke liye.

**🔄 Reply Raids (Automatic)**
`rr <user/reply>`: User ke har message par automatic gaali wala reply dene ke liye activate karein.
`drr <user/reply>`: Reply Raid deactivate karne ke liye.
`rlr <user/reply>`: User ke har message par automatic pyaar wala reply dene ke liye activate karein.
`drlr <user/reply>`: Reply Love Raid deactivate karne ke liye.

**👨‍💻 Owner:** @Romeo_RJ_143
"""

@client.on_message(filters.command("help", ".") & filters.me)
async def help_command(_, message: Message):
    await eor(message, HELP_TEXT)

# ================================== BASIC COMMANDS ================================== #

@client.on_message(filters.command(["alive", "ping"], ".") & filters.me)
async def alive_ping(_, message: Message):
    start = time()
    uptime_sec = (datetime.utcnow() - START_TIME).total_seconds()
    uptime = await _human_time_duration(int(uptime_sec))
    ping_ms = (time() - start) * 1000
    
    caption = (
        f"**✨ Romeo Userbot is Alive!**\n\n"
        f"**Ping:** `{ping_ms:.2f}ms`\n"
        f"**Uptime:** `{uptime}`\n"
        f"**Python:** `{python_version()}`\n"
        f"**Pyrogram:** `{__version__}`\n"
        f"**Owner:** {client.me.mention}"
    )
    
    if message.command[0].lower() == "alive":
        await message.reply_photo(photo=ALIVE_PIC, caption=caption)
    else: # ping
        await eor(message, caption)

# =============================== CLONE COMMANDS =============================== #

ORIGINAL_DATA_FILE = "Original_Profile.json"

def load_original_data():
    if os.path.exists(ORIGINAL_DATA_FILE):
        with open(ORIGINAL_DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_original_data(data):
    with open(ORIGINAL_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

@client.on_message(filters.command("clone", ".") & filters.me)
async def clone_profile(_, message: Message):
    text = get_text(message)
    user_to_clone = await get_user(message, text)
    if not user_to_clone:
        return await eor(message, "`❌ Kiska profile clone karu? User batao.`")

    op = await eor(message, "`🔄 Cloning process shuru ho raha hai...`")
    
    # Backup original profile if not already done
    my_id = str(client.me.id)
    all_data = load_original_data()
    if my_id not in all_data:
        await op.edit("`📦 Aapke original profile ka backup le raha hu...`")
        try:
            me = await client.get_me()
            my_chat = await client.get_chat(me.id)
            original_photos = [p async for p in client.get_chat_photos("me")]
            photo_paths = []
            for idx, photo in enumerate(original_photos):
                path = await client.download_media(photo.file_id, file_name=f"original_photo_{my_id}_{idx}.jpg")
                photo_paths.append(path)
            
            all_data[my_id] = {
                "first_name": me.first_name or "", "last_name": me.last_name or "",
                "bio": my_chat.bio or "", "username": me.username or "",
                "photos": photo_paths
            }
            save_original_data(all_data)
        except Exception as e:
            return await op.edit(f"`❌ Backup failed: {e}`")

    # Start cloning
    try:
        await op.edit("`📸 Profile pictures download kar raha hu...`")
        target_chat = await client.get_chat(user_to_clone.id)
        
        # Delete current photos
        current_photos = [p.file_id async for p in client.get_chat_photos("me")]
        if current_photos:
            await client.delete_profile_photos(current_photos)

        # Set new photos
        async for photo in client.get_chat_photos(user_to_clone.id, limit=5): # limit to 5 to avoid floodwaits
            await client.set_profile_photo(photo=photo.file_id)

        await op.edit("`✏️ Profile details update kar raha hu...`")
        await client.update_profile(
            first_name=user_to_clone.first_name or "User",
            last_name=user_to_clone.last_name or "",
            bio=target_chat.bio or ""
        )
        await op.edit(f"**✅ Clone Successful!**\nAb aap **{user_to_clone.first_name}** jaise dikh rahe ho.")
    except Exception as e:
        await op.edit(f"`❌ Cloning failed: {e}`")

@client.on_message(filters.command("revert", ".") & filters.me)
async def revert_profile(_, message: Message):
    op = await eor(message, "`🔄 Original profile par wapas ja raha hu...`")
    my_id = str(client.me.id)
    all_data = load_original_data()

    if my_id not in all_data:
        await op.edit("`⚠️ Koi backup nahi mila! Fallback settings use kar raha hu.`")
        await client.update_profile(first_name="Romeo", last_name="Userbot", bio=BIO_FALLBACK)
        return

    try:
        original = all_data[my_id]
        
        # Delete cloned photos
        current_photos = [p.file_id async for p in client.get_chat_photos("me")]
        if current_photos:
            await client.delete_profile_photos(current_photos)
        
        # Restore original photos
        for photo_path in reversed(original["photos"]):
            if os.path.exists(photo_path):
                await client.set_profile_photo(photo=photo_path)
                os.remove(photo_path)
        
        # Restore profile details
        await client.update_profile(
            first_name=original["first_name"], last_name=original["last_name"], bio=original["bio"]
        )
        if original["username"]:
            try: await client.set_username(original["username"])
            except: pass
        
        del all_data[my_id]
        save_original_data(all_data)
        
        await op.edit("**✅ Revert Successful!**\nAapka original profile wapas aa gaya hai.")
    except Exception as e:
        await op.edit(f"`❌ Revert failed: {e}`")

# ============================== SPAM & FUN COMMANDS ============================== #

async def process_spam_command(message: Message, is_dm=False):
    """Helper to process spam command arguments and user checks."""
    text = get_text(message)
    
    try:
        count_str, target_str = (text or "").split(None, 1)
        count = int(count_str)
    except (ValueError, AttributeError):
        if message.reply_to_message and text and text.isdigit():
            count = int(text)
            target_str = None
        else:
            await eor(message, f"`❓ Usage: .{message.command[0]} <count> <user/reply>`")
            return None, None
            
    user = await get_user(message, target_str)
    if not user:
        await eor(message, "`❌ User nahi mila. ID/Username do ya reply karo.`")
        return None, None

    if not is_dm and message.chat.id in GROUP:
        await eor(message, "`🚫 Is group me spamming allowed nahi hai.`")
        return None, None

    if user.id in SUDO_USERS or user.id in VERIFIED_USERS:
        await eor(message, f"`😒 {user.first_name} ko spam nahi kar sakta.`")
        return None, None
        
    return user, count

@client.on_message(filters.command(["raid", "r"], ".") & filters.me)
async def raid_command(_, message: Message):
    user, count = await process_spam_command(message)
    if not user: return
    
    await message.delete()
    for _ in range(count):
        await client.send_message(message.chat.id, f"{user.mention} {random.choice(RAID)}")
        await asyncio.sleep(0.2)

@client.on_message(filters.command(["lraid", "lr"], ".") & filters.me)
async def love_raid_command(_, message: Message):
    user, count = await process_spam_command(message)
    if not user: return
    
    await message.delete()
    for _ in range(count):
        await client.send_message(message.chat.id, f"{user.mention} {random.choice(LOVE)}")
        await asyncio.sleep(0.2)

@client.on_message(filters.command(["dmraid", "dmr"], ".") & filters.me)
async def dm_raid_command(_, message: Message):
    user, count = await process_spam_command(message, is_dm=True)
    if not user: return
    
    await eor(message, f"`✅ {user.first_name} ke DM me raid shuru! ({count} messages)`")
    for _ in range(count):
        await client.send_message(user.id, random.choice(RAID))
        await asyncio.sleep(0.3)

@client.on_message(filters.command(["dmlraid", "dmlr"], ".") & filters.me)
async def dm_love_raid_command(_, message: Message):
    user, count = await process_spam_command(message, is_dm=True)
    if not user: return
    
    await eor(message, f"`✅ {user.first_name} ke DM me love raid shuru! ({count} messages)`")
    for _ in range(count):
        await client.send_message(user.id, random.choice(LOVE))
        await asyncio.sleep(0.3)

@client.on_message(filters.command(["pornspam", "psm"], ".") & filters.me)
async def porn_spam_command(_, message: Message):
    if message.chat.id in GROUP:
        return await eor(message, "`🚫 Is group me spamming allowed nahi hai.`")
    
    try:
        count = int(message.command[1])
    except (ValueError, IndexError):
        return await eor(message, "`❓ Usage: .pornspam <count>`")
        
    await message.delete()
    for _ in range(count):
        try:
            await client.send_video(message.chat.id, video=random.choice(PORM))
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception:
            pass # Ignore if a link is broken

@client.on_message(filters.command(["sspam", "stickerspam"], ".") & filters.me)
async def sticker_spam_command(_, message: Message):
    if message.chat.id in GROUP:
        return await eor(message, "`🚫 Is group me spamming allowed nahi hai.`")
    if not message.reply_to_message or not message.reply_to_message.sticker:
        return await eor(message, "`❓ Kisi sticker ko reply karke count batao.`")
    
    try:
        count = int(message.command[1])
    except (ValueError, IndexError):
        return await eor(message, "`❓ Usage: .sspam <count> [reply to sticker]`")
        
    sticker_id = message.reply_to_message.sticker.file_id
    await message.delete()
    for _ in range(count):
        await client.send_sticker(message.chat.id, sticker_id)
        await asyncio.sleep(0.1)

@client.on_message(filters.command("hang", ".") & filters.me)
async def hang_command(_, message: Message):
    if message.chat.id in GROUP:
        return await eor(message, "`🚫 Is group me spamming allowed nahi hai.`")
    try:
        count = int(message.command[1])
    except (ValueError, IndexError):
        return await eor(message, "`❓ Usage: .hang <count>`")
        
    await message.delete()
    hang_text = "⃟" * 10000  # A shorter but still effective string
    for _ in range(count):
        await client.send_message(message.chat.id, hang_text)
        await asyncio.sleep(0.3)

# =============================== UTILITY COMMANDS =============================== #

@client.on_message(filters.command("all", ".") & filters.me)
async def mention_all_command(_, message: Message):
    chat_id = message.chat.id
    text = get_text(message) or ""
    
    if chat_id in spam_chats:
        return await eor(message, "`✋ Ek tagall process pehle se chal raha hai.`")

    await message.delete()
    spam_chats.append(chat_id)
    
    members_text = ""
    count = 0
    async for member in client.get_chat_members(chat_id):
        if chat_id not in spam_chats:
            break
        if member.user.is_bot or member.user.is_deleted:
            continue
        
        members_text += f"[{member.user.first_name}](tg://user?id={member.user.id}) "
        count += 1
        
        if count == 5:
            await client.send_message(chat_id, f"{text}\n{members_text}")
            members_text = ""
            count = 0
            await asyncio.sleep(2)
            
    if members_text and chat_id in spam_chats:
        await client.send_message(chat_id, f"{text}\n{members_text}")

    if chat_id in spam_chats:
        spam_chats.remove(chat_id)

@client.on_message(filters.command("cancel", ".") & filters.me)
async def cancel_spam_command(_, message: Message):
    if message.chat.id not in spam_chats:
        return await eor(message, "`🤔 Yahan koi tagall nahi chal raha hai.`")
    
    spam_chats.remove(message.chat.id)
    await eor(message, "`✅ Tagall process rok diya gaya hai.`")


# =============================== EMOJI ART (Kept as is due to complexity) =============================== #

rtext = ["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z","0","1","2","3","4","5","6","7","8","9",]
remoji = ["⁭\n                    💖\n                  💖💖\n               💖💖💖\n            💖💖 💖💖\n          💖💖    💖💖\n        💖💖       💖💖\n      💖💖💖💖💖💖\n     💖💖💖💖💖💖💖\n   💖💖                 💖💖\n  💖💖                    💖💖\n💖💖                       💖💖\n","⁭\n💗💗💗💗💗💗💗\n💗💗💗💗💗💗💗💗\n💗💗                     💗💗\n💗💗                     💗💗\n💗💗💗💗💗💗💗💗\n💗💗💗💗💗💗💗💗\n💗💗                     💗💗\n💗💗                     💗💗\n💗💗💗💗💗💗💗💗\n💗💗💗💗💗💗💗\n","⁭\n          💛💛💛💛💛💛\n     💛💛💛💛💛💛💛💛\n   💛💛                      💛💛\n 💛💛\n💛💛\n💛💛\n 💛💛\n   💛💛                      💛💛\n     💛💛💛💛💛💛💛💛\n         💛💛💛💛💛💛\n","⁭\n💙💙💙💙💙💙💙\n💙💙💙💙💙💙💙💙\n💙💙                      💙💙\n💙💙                         💙💙\n💙💙                         💙💙\n💙💙                         💙💙\n💙💙                         💙💙\n💙💙                      💙💙\n💙💙💙💙💙💙💙💙\n💙💙💙💙💙💙💙\n","⁭\n💟💟💟💟💟💟💟💟\n💟💟💟💟💟💟💟💟\n💟💟\n💟💟\n💟💟💟💟💟💟\n💟💟💟💟💟💟\n💟💟\n💟💟\n💟💟💟💟💟💟💟💟\n💟💟💟💟💟💟💟💟\n","⁭\n💚💚💚💚💚💚💚💚\n💚💚💚💚💚💚💚💚\n💚💚\n💚💚\n💚💚💚💚💚💚\n💚💚💚💚💚💚\n💚💚\n💚💚\n💚💚\n💚💚\n","⁭\n          💜💜💜💜💜💜\n     💜💜💜💜💜💜💜💜\n   💜💜                     💜💜\n 💜💜\n💜💜                💜💜💜💜\n💜💜                💜💜💜💜\n 💜💜                        💜💜\n   💜💜                      💜💜\n     💜💜💜💜💜💜💜💜\n          💜💜💜💜💜💜\n","⁭\n💖💖                        💖💖\n💖💖                        💖💖\n💖💖                        💖💖\n💖💖                        💖💖\n💖💖💖💖💖💖💖💖💖\n💖💖💖💖💖💖💖💖💖\n💖💖                        💖💖\n💖💖                        💖💖\n💖💖                        💖💖\n💖💖                        💖💖\n","⁭\n💗💗💗💗💗💗\n💗💗💗💗💗💗\n          💗💗\n          💗💗\n          💗💗\n          💗💗\n          💗💗\n          💗💗\n💗💗💗💗💗💗\n💗💗💗💗💗💗\n","⁭\n         💛💛💛💛💛💛\n         💛💛💛💛💛💛\n                  💛💛\n                  💛💛\n                  💛💛\n                  💛💛\n💛💛          💛💛\n  💛💛       💛💛\n   💛💛💛💛💛\n      💛💛💛💛\n","⁭\n💙💙                  💙💙\n💙💙             💙💙\n💙💙        💙💙\n💙💙   💙💙\n💙💙💙💙\n💙💙 💙💙\n💙💙     💙💙\n💙💙         💙💙\n💙💙              💙💙\n💙💙                   💙💙\n","⁭\n💟💟\n💟💟\n💟💟\n💟💟\n💟💟\n💟💟\n💟💟\n💟💟\n💟💟💟💟💟💟💟💟\n💟💟💟💟💟💟💟💟\n","⁭\n💚💚                              💚💚\n💚💚💚                      💚💚💚\n💚💚💚💚            💚💚💚💚\n💚💚    💚💚    💚💚    💚💚\n💚💚        💚💚💚        💚💚\n💚💚             💚             💚💚\n💚💚                              💚💚\n💚💚                              💚💚\n💚💚                              💚💚\n💚💚                              💚💚\n","⁭\n💜💜                           💜💜\n💜💜💜                       💜💜\n💜💜💜💜                 💜💜\n💜💜  💜💜               💜💜\n💜💜     💜💜            💜💜\n💜💜         💜💜        💜💜\n💜💜             💜💜    💜💜\n💜💜                 💜💜💜💜\n💜💜                     💜💜💜\n💜💜                          💜💜\n","⁭\n           💖💖💖💖💖\n     💖💖💖💖💖💖💖\n   💖💖                   💖💖\n 💖💖                       💖💖\n💖💖                         💖💖\n💖💖                         💖💖\n 💖💖                       💖💖\n   💖💖                   💖💖\n      💖💖💖💖💖💖💖\n            💖💖💖💖💖\n","⁭\n💗💗💗💗💗💗💗\n💗💗💗💗💗💗💗💗\n💗💗                     💗💗\n💗💗                     💗💗\n💗💗💗💗💗💗💗💗\n💗💗💗💗💗💗💗\n💗💗\n💗💗\n💗💗\n💗💗\n","⁭\n           💛💛💛💛💛\n      💛💛💛💛💛💛💛\n   💛💛                    💛💛\n 💛💛                        💛💛\n💛💛                           💛💛\n💛💛              💛💛     💛💛\n 💛💛               💛💛 💛💛\n   💛💛                   💛💛\n      💛💛💛💛💛💛💛💛\n           💛💛💛💛💛   💛💛\n","⁭\n💙💙💙💙💙💙💙\n💙💙💙💙💙💙💙💙\n💙💙                     💙💙\n💙💙                     💙💙\n💙💙💙💙💙💙💙💙\n💙💙💙💙💙💙💙\n💙💙    💙💙\n💙💙         💙💙\n💙💙              💙💙\n💙💙                  💙💙\n","⁭\n       💟💟💟💟💟\n  💟💟💟💟💟💟💟\n  💟💟                 💟💟\n💟💟\n  💟💟💟💟💟💟\n      💟💟💟💟💟💟\n                            💟💟\n💟💟                 💟💟\n  💟💟💟💟💟💟💟\n       💟💟💟💟💟\n","⁭\n💚💚💚💚💚💚💚💚\n💚💚💚💚💚💚💚💚\n               💚💚\n               💚💚\n               💚💚\n               💚💚\n               💚💚\n               💚💚\n               💚💚\n","⁭\n💜💜                      💜💜\n💜💜                      💜💜\n💜💜                      💜💜\n💜💜                      💜💜\n💜💜                      💜💜\n💜💜                      💜💜\n💜💜                      💜💜\n  💜💜                  💜💜\n      💜💜💜💜💜💜\n            💜💜💜💜\n","⁭\n💖💖                              💖💖\n  💖💖                          💖💖\n    💖💖                      💖💖\n      💖💖                  💖💖\n         💖💖              💖💖\n           💖💖         💖💖\n             💖💖     💖💖\n               💖💖 💖💖\n                  💖💖💖\n                       💖\n","⁭\n💗💗                               💗💗\n💗💗                               💗💗\n💗💗                               💗💗\n💗💗                               💗💗\n💗💗              💗            💗💗\n 💗💗           💗💗          💗💗\n 💗💗        💗💗💗       💗💗\n  💗💗   💗💗  💗💗   💗💗\n   💗💗💗💗      💗💗💗💗\n    💗💗💗             💗💗💗\n","⁭\n💛💛                    💛💛\n   💛💛              💛💛\n      💛💛        💛💛\n         💛💛  💛💛\n            💛💛💛\n            💛💛💛\n         💛💛 💛💛\n      💛💛       💛💛\n   💛💛             💛💛\n💛💛                   💛💛\n","⁭\n💙💙                    💙💙\n   💙💙              💙💙\n      💙💙        💙💙\n         💙💙  💙💙\n            💙💙💙\n              💙💙\n              💙💙\n              💙💙\n              💙💙\n              💙💙\n","⁭\n 💟💟💟💟💟💟💟\n 💟💟💟💟💟💟💟\n                       💟💟\n                   💟💟\n               💟💟\n           💟💟\n       💟💟\n   💟💟\n💟💟💟💟💟💟💟\n💟💟💟💟💟💟💟\n","⁭\n       💗💗💗💗\n   💗💗💗💗💗💗\n💗💗               💗💗\n💗💗               💗💗\n💗💗               💗💗\n💗💗               💗💗\n💗💗               💗💗\n💗💗               💗💗\n   💗💗💗💗💗💗\n        💗💗💗💗\n","⁭\n          💙💙\n     💙💙💙\n💙💙 💙💙\n          💙💙\n          💙💙\n          💙💙\n          💙💙\n          💙💙\n     💙💙💙💙\n     💙💙💙💙\n","⁭\n    💟💟💟💟💟\n  💟💟💟💟💟💟\n💟💟          💟💟\n                💟💟\n             💟💟\n          💟💟\n       💟💟\n    💟💟\n  💟💟💟💟💟💟\n  💟💟💟💟💟💟\n","⁭\n     💛💛💛💛\n  💛💛💛💛💛\n💛💛         💛💛\n                   💛💛\n            💛💛💛\n            💛💛💛\n                   💛💛\n💛💛         💛💛\n  💛💛💛💛💛\n     💛💛💛💛\n","⁭\n                         💖💖\n                    💖💖💖\n              💖💖 💖💖\n          💖💖     💖💖\n     💖💖          💖💖\n💖💖               💖💖\n💖💖💖💖💖💖💖💖💖\n💖💖💖💖💖💖💖💖💖\n                         💖💖\n                         💖💖\n","⁭\n💚💚💚💚💚💚\n💚💚💚💚💚💚\n💚💚\n 💚💚💚💚💚\n   💚💚💚💚💚\n                    💚💚\n                    💚💚\n💚💚          💚💚\n  💚💚💚💚💚\n     💚💚💚💚\n","⁭\n        💜💜💜💜\n    💜💜💜💜💜\n💜💜\n\n💜💜\n💜💜💜💜💜💜\n💜💜💜💜💜💜💜\n💜💜               💜💜\n💜💜               💜💜\n    💜💜💜💜💜💜\n        💜💜💜💜\n","⁭\n💗💗💗💗💗💗💗\n💗💗💗💗💗💗💗\n                      💗💗\n                     💗💗\n                   💗💗\n                 💗💗\n               💗💗\n             💗💗\n           💗💗\n         💗💗\n","⁭\n        💙💙💙💙\n   💙💙💙💙💙💙\n💙💙               💙💙\n💙💙               💙💙\n   💙💙💙💙💙💙\n   💙💙💙💙💙💙\n💙💙               💙💙\n💙💙               💙💙\n   💙💙💙💙💙💙\n        💙💙💙💙\n","⁭\n        💟💟💟💟\n   💟💟💟💟💟💟\n💟💟               💟💟\n💟💟               💟💟\n 💟💟💟💟💟💟💟\n      💟💟💟💟💟💟\n                         💟💟\n                        💟💟\n  💟💟💟💟💟💟\n       💟💟💟💟\n"]
rtemoji = ["⁭\n                    {cj}\n                  {cj}{cj}\n               {cj}{cj}{cj}\n            {cj}{cj} {cj}{cj}\n          {cj}{cj}    {cj}{cj}\n        {cj}{cj}       {cj}{cj}\n      {cj}{cj}{cj}{cj}{cj}{cj}\n     {cj}{cj}{cj}{cj}{cj}{cj}{cj}\n   {cj}{cj}                 {cj}{cj}\n  {cj}{cj}                    {cj}{cj}\n{cj}{cj}                       {cj}{cj}\n","⁭\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}                     {cj}{cj}\n{cj}{cj}                     {cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}                     {cj}{cj}\n{cj}{cj}                     {cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n","⁭\n          {cj}{cj}{cj}{cj}{cj}{cj}\n     {cj}{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n   {cj}{cj}                      {cj}{cj}\n {cj}{cj}\n{cj}{cj}\n{cj}{cj}\n {cj}{cj}\n   {cj}{cj}                      {cj}{cj}\n     {cj}{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n         {cj}{cj}{cj}{cj}{cj}{cj}\n","⁭\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}                      {cj}{cj}\n{cj}{cj}                         {cj}{cj}\n{cj}{cj}                         {cj}{cj}\n{cj}{cj}                         {cj}{cj}\n{cj}{cj}                         {cj}{cj}\n{cj}{cj}                      {cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n","⁭\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}\n{cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}\n{cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n","⁭\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}\n{cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}\n{cj}{cj}\n{cj}{cj}\n{cj}{cj}\n","⁭\n          {cj}{cj}{cj}{cj}{cj}{cj}\n     {cj}{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n   {cj}{cj}                     {cj}{cj}\n {cj}{cj}\n{cj}{cj}                {cj}{cj}{cj}{cj}\n{cj}{cj}                {cj}{cj}{cj}{cj}\n {cj}{cj}                        {cj}{cj}\n   {cj}{cj}                      {cj}{cj}\n     {cj}{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n          {cj}{cj}{cj}{cj}{cj}{cj}\n","⁭\n{cj}{cj}                        {cj}{cj}\n{cj}{cj}                        {cj}{cj}\n{cj}{cj}                        {cj}{cj}\n{cj}{cj}                        {cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}                        {cj}{cj}\n{cj}{cj}                        {cj}{cj}\n{cj}{cj}                        {cj}{cj}\n{cj}{cj}                        {cj}{cj}\n","⁭\n{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}\n          {cj}{cj}\n          {cj}{cj}\n          {cj}{cj}\n          {cj}{cj}\n          {cj}{cj}\n          {cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}\n","⁭\n         {cj}{cj}{cj}{cj}{cj}{cj}\n         {cj}{cj}{cj}{cj}{cj}{cj}\n                  {cj}{cj}\n                  {cj}{cj}\n                  {cj}{cj}\n                  {cj}{cj}\n{cj}{cj}          {cj}{cj}\n  {cj}{cj}       {cj}{cj}\n   {cj}{cj}{cj}{cj}{cj}\n      {cj}{cj}{cj}{cj}\n","⁭\n{cj}{cj}                  {cj}{cj}\n{cj}{cj}             {cj}{cj}\n{cj}{cj}        {cj}{cj}\n{cj}{cj}   {cj}{cj}\n{cj}{cj}{cj}{cj}\n{cj}{cj} {cj}{cj}\n{cj}{cj}     {cj}{cj}\n{cj}{cj}         {cj}{cj}\n{cj}{cj}              {cj}{cj}\n{cj}{cj}                   {cj}{cj}\n","⁭\n{cj}{cj}\n{cj}{cj}\n{cj}{cj}\n{cj}{cj}\n{cj}{cj}\n{cj}{cj}\n{cj}{cj}\n{cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n","⁭\n{cj}{cj}                              {cj}{cj}\n{cj}{cj}{cj}                      {cj}{cj}{cj}\n{cj}{cj}{cj}{cj}            {cj}{cj}{cj}{cj}\n{cj}{cj}    {cj}{cj}    {cj}{cj}    {cj}{cj}\n{cj}{cj}        {cj}{cj}{cj}        {cj}{cj}\n{cj}{cj}             {cj}             {cj}{cj}\n{cj}{cj}                              {cj}{cj}\n{cj}{cj}                              {cj}{cj}\n{cj}{cj}                              {cj}{cj}\n{cj}{cj}                              {cj}{cj}\n","⁭\n{cj}{cj}                           {cj}{cj}\n{cj}{cj}{cj}                       {cj}{cj}\n{cj}{cj}{cj}{cj}                 {cj}{cj}\n{cj}{cj}  {cj}{cj}               {cj}{cj}\n{cj}{cj}     {cj}{cj}            {cj}{cj}\n{cj}{cj}         {cj}{cj}        {cj}{cj}\n{cj}{cj}             {cj}{cj}    {cj}{cj}\n{cj}{cj}                 {cj}{cj}{cj}{cj}\n{cj}{cj}                     {cj}{cj}{cj}\n{cj}{cj}                          {cj}{cj}\n","⁭\n           {cj}{cj}{cj}{cj}{cj}\n     {cj}{cj}{cj}{cj}{cj}{cj}{cj}\n   {cj}{cj}                   {cj}{cj}\n {cj}{cj}                       {cj}{cj}\n{cj}{cj}                         {cj}{cj}\n{cj}{cj}                         {cj}{cj}\n {cj}{cj}                       {cj}{cj}\n   {cj}{cj}                   {cj}{cj}\n      {cj}{cj}{cj}{cj}{cj}{cj}{cj}\n            {cj}{cj}{cj}{cj}{cj}\n","⁭\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}                     {cj}{cj}\n{cj}{cj}                     {cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}\n{cj}{cj}\n{cj}{cj}\n{cj}{cj}\n","⁭\n           {cj}{cj}{cj}{cj}{cj}\n      {cj}{cj}{cj}{cj}{cj}{cj}{cj}\n   {cj}{cj}                    {cj}{cj}\n {cj}{cj}                        {cj}{cj}\n{cj}{cj}                           {cj}{cj}\n{cj}{cj}              {cj}{cj}     {cj}{cj}\n {cj}{cj}               {cj}{cj} {cj}{cj}\n   {cj}{cj}                   {cj}{cj}\n      {cj}{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n           {cj}{cj}{cj}{cj}{cj}   {cj}{cj}\n","⁭\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}                     {cj}{cj}\n{cj}{cj}                     {cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}    {cj}{cj}\n{cj}{cj}         {cj}{cj}\n{cj}{cj}              {cj}{cj}\n{cj}{cj}                  {cj}{cj}\n","⁭\n       {cj}{cj}{cj}{cj}{cj}\n  {cj}{cj}{cj}{cj}{cj}{cj}{cj}\n  {cj}{cj}                 {cj}{cj}\n{cj}{cj}\n  {cj}{cj}{cj}{cj}{cj}{cj}\n      {cj}{cj}{cj}{cj}{cj}{cj}\n                            {cj}{cj}\n{cj}{cj}                 {cj}{cj}\n  {cj}{cj}{cj}{cj}{cj}{cj}{cj}\n       {cj}{cj}{cj}{cj}{cj}\n","⁭\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n               {cj}{cj}\n               {cj}{cj}\n               {cj}{cj}\n               {cj}{cj}\n               {cj}{cj}\n               {cj}{cj}\n               {cj}{cj}\n","⁭\n{cj}{cj}                      {cj}{cj}\n{cj}{cj}                      {cj}{cj}\n{cj}{cj}                      {cj}{cj}\n{cj}{cj}                      {cj}{cj}\n{cj}{cj}                      {cj}{cj}\n{cj}{cj}                      {cj}{cj}\n{cj}{cj}                      {cj}{cj}\n  {cj}{cj}                  {cj}{cj}\n      {cj}{cj}{cj}{cj}{cj}{cj}\n            {cj}{cj}{cj}{cj}\n","⁭\n{cj}{cj}                              {cj}{cj}\n  {cj}{cj}                          {cj}{cj}\n    {cj}{cj}                      {cj}{cj}\n      {cj}{cj}                  {cj}{cj}\n         {cj}{cj}              {cj}{cj}\n           {cj}{cj}         {cj}{cj}\n             {cj}{cj}     {cj}{cj}\n               {cj}{cj} {cj}{cj}\n                  {cj}{cj}{cj}\n                       {cj}\n","⁭\n{cj}{cj}                               {cj}{cj}\n{cj}{cj}                               {cj}{cj}\n{cj}{cj}                               {cj}{cj}\n{cj}{cj}                               {cj}{cj}\n{cj}{cj}              {cj}            {cj}{cj}\n {cj}{cj}           {cj}{cj}          {cj}{cj}\n {cj}{cj}        {cj}{cj}{cj}       {cj}{cj}\n  {cj}{cj}   {cj}{cj}  {cj}{cj}   {cj}{cj}\n   {cj}{cj}{cj}{cj}      {cj}{cj}{cj}{cj}\n    {cj}{cj}{cj}             {cj}{cj}{cj}\n","⁭\n{cj}{cj}                    {cj}{cj}\n   {cj}{cj}              {cj}{cj}\n      {cj}{cj}        {cj}{cj}\n         {cj}{cj}  {cj}{cj}\n            {cj}{cj}{cj}\n            {cj}{cj}{cj}\n         {cj}{cj} {cj}{cj}\n      {cj}{cj}       {cj}{cj}\n   {cj}{cj}             {cj}{cj}\n{cj}{cj}                   {cj}{cj}\n","⁭\n{cj}{cj}                    {cj}{cj}\n   {cj}{cj}              {cj}{cj}\n      {cj}{cj}        {cj}{cj}\n         {cj}{cj}  {cj}{cj}\n            {cj}{cj}{cj}\n              {cj}{cj}\n              {cj}{cj}\n              {cj}{cj}\n              {cj}{cj}\n              {cj}{cj}\n","⁭\n {cj}{cj}{cj}{cj}{cj}{cj}{cj}\n {cj}{cj}{cj}{cj}{cj}{cj}{cj}\n                       {cj}{cj}\n                   {cj}{cj}\n               {cj}{cj}\n           {cj}{cj}\n       {cj}{cj}\n   {cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n","⁭\n       {cj}{cj}{cj}{cj}\n   {cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}               {cj}{cj}\n{cj}{cj}               {cj}{cj}\n{cj}{cj}               {cj}{cj}\n{cj}{cj}               {cj}{cj}\n{cj}{cj}               {cj}{cj}\n{cj}{cj}               {cj}{cj}\n   {cj}{cj}{cj}{cj}{cj}{cj}\n        {cj}{cj}{cj}{cj}\n","⁭\n          {cj}{cj}\n     {cj}{cj}{cj}\n{cj}{cj} {cj}{cj}\n          {cj}{cj}\n          {cj}{cj}\n          {cj}{cj}\n          {cj}{cj}\n          {cj}{cj}\n     {cj}{cj}{cj}{cj}\n     {cj}{cj}{cj}{cj}\n","⁭\n    {cj}{cj}{cj}{cj}{cj}\n  {cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}          {cj}{cj}\n                {cj}{cj}\n             {cj}{cj}\n          {cj}{cj}\n       {cj}{cj}\n    {cj}{cj}\n  {cj}{cj}{cj}{cj}{cj}{cj}\n  {cj}{cj}{cj}{cj}{cj}{cj}\n","⁭\n     {cj}{cj}{cj}{cj}\n  {cj}{cj}{cj}{cj}{cj}\n{cj}{cj}         {cj}{cj}\n                   {cj}{cj}\n            {cj}{cj}{cj}\n            {cj}{cj}{cj}\n                   {cj}{cj}\n{cj}{cj}         {cj}{cj}\n  {cj}{cj}{cj}{cj}{cj}\n     {cj}{cj}{cj}{cj}\n","⁭\n                         {cj}{cj}\n                    {cj}{cj}{cj}\n              {cj}{cj} {cj}{cj}\n          {cj}{cj}     {cj}{cj}\n     {cj}{cj}          {cj}{cj}\n{cj}{cj}               {cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n                         {cj}{cj}\n                         {cj}{cj}\n","⁭\n{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}\n {cj}{cj}{cj}{cj}{cj}\n   {cj}{cj}{cj}{cj}{cj}\n                    {cj}{cj}\n                    {cj}{cj}\n{cj}{cj}          {cj}{cj}\n  {cj}{cj}{cj}{cj}{cj}\n     {cj}{cj}{cj}{cj}\n","⁭\n        {cj}{cj}{cj}{cj}\n    {cj}{cj}{cj}{cj}{cj}\n{cj}{cj}\n\n{cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}               {cj}{cj}\n{cj}{cj}               {cj}{cj}\n    {cj}{cj}{cj}{cj}{cj}{cj}\n        {cj}{cj}{cj}{cj}\n","⁭\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}{cj}{cj}{cj}{cj}{cj}\n                      {cj}{cj}\n                     {cj}{cj}\n                   {cj}{cj}\n                 {cj}{cj}\n               {cj}{cj}\n             {cj}{cj}\n           {cj}{cj}\n         {cj}{cj}\n","⁭\n        {cj}{cj}{cj}{cj}\n   {cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}               {cj}{cj}\n{cj}{cj}               {cj}{cj}\n   {cj}{cj}{cj}{cj}{cj}{cj}\n   {cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}               {cj}{cj}\n{cj}{cj}               {cj}{cj}\n   {cj}{cj}{cj}{cj}{cj}{cj}\n        {cj}{cj}{cj}{cj}\n","⁭\n        {cj}{cj}{cj}{cj}\n   {cj}{cj}{cj}{cj}{cj}{cj}\n{cj}{cj}               {cj}{cj}\n{cj}{cj}               {cj}{cj}\n {cj}{cj}{cj}{cj}{cj}{cj}{cj}\n      {cj}{cj}{cj}{cj}{cj}{cj}\n                         {cj}{cj}\n                        {cj}{cj}\n  {cj}{cj}{cj}{cj}{cj}{cj}\n       {cj}{cj}{cj}{cj}\n",]

@client.on_message(filters.command(["emoji", "ej"], ".") & filters.me)
async def emoji_command(_, message: Message):
    op = await eor(message, "`Emojifying...`")
    args = get_text(message) or (message.reply_to_message.text if message.reply_to_message else None)
    if not args:
        return await op.edit("`❓ Text do emojify karne ke liye.`")

    result = ""
    for a in args:
        if a.lower() in rtext:
            result += remoji[rtext.index(a.lower())]
        else:
            result += a
    await op.edit(result)

@client.on_message(filters.command(["cmoji", "cj"], ".") & filters.me)
async def cmoji_command(_, message: Message):
    op = await eor(message, "`Emojifying...`")
    args = get_text(message) or (message.reply_to_message.text if message.reply_to_message else None)
    if not args:
        return await op.edit("`❓ Usage: .cmoji <emoji> <text>`")

    try:
        emoji, text = args.split(" ", 1)
    except ValueError:
        text = args
        emoji = "😎"

    result = ""
    for a in text:
        if a.lower() in rtext:
            result += rtemoji[rtext.index(a.lower())].format(cj=emoji)
        else:
            result += a
    await op.edit(result)
    
# ================================ HOSTER BOT COMMANDS ================================ #

@app.on_message(filters.command("start", ["/", "!", "."]) & filters.private)
async def start_hoster_command(_, message: Message):
    caption = (
        "**Hello!**\n"
        "I'm Romeo Userbot Hoster.\n"
        "If you want to make your own userbot, you need a Pyrogram (v2) Session String.\n"
        "You can get it from @RJssgbot.\n\n"
        "Once you have the string, use the command below:\n"
        "`/host YOUR_SESSION_STRING`"
    )
    buttons = [
        [InlineKeyboardButton("• Support Group •", url="https://t.me/RomeoBot_op")],
        [InlineKeyboardButton("• Updates Channel •", url="https://t.me/Romeo_op")]
    ]
    await message.reply_photo(
        photo=ALIVE_PIC,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@app.on_message(filters.command(["host", "cl", "clone"], ["/", "!", "."]))
async def host_client_command(_, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("`❓ Usage: /host <SESSION_STRING>`")

    session_string = message.command[1]
    op = await message.reply_text("`🔄 Aapka client start ho raha hai...`")
    
    try:
        # We give it a random name to allow multiple users to host
        client_name = f"userbot_{message.from_user.id}"
        new_client = Client(
            name=client_name,
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=session_string,
            in_memory=True
        )
        await new_client.start()
        user = await new_client.get_me()
        
        # We can't keep the client running here, so we just confirm it works and stop.
        # The user has to deploy the main script on their own server.
        await new_client.stop()
        
        await op.edit(
            f"**✅ Client Successfully Started & Checked!**\n\n"
            f"**ID:** `{user.id}`\n"
            f"**Name:** `{user.first_name}`\n"
            f"**Username:** `@{user.username}`\n\n"
            "Ab aap is session string ko apne server par deploy kar sakte hain."
        )
    except Exception as e:
        await op.edit(f"**❌ Error:** `{e}`\n\nPlease make sure your Session String is valid.")

# ============================== REPLY RAID COMMANDS ============================== #

async def toggle_reply_raid(message: Message, raid_list: list, list_name: str, action: str):
    """Helper to add/remove users from reply raid lists."""
    user = await get_user(message, get_text(message))
    if not user:
        return await eor(message, "`❌ User nahi mila. ID/Username do ya reply karo.`")
    
    if user.id in SUDO_USERS or user.id in VERIFIED_USERS:
        return await eor(message, f"`😒 {user.first_name} ke saath yeh nahi kar sakta.`")

    if action == "add":
        if user.id in raid_list:
            return await eor(message, f"`😒 {user.first_name} pehle se hi {list_name} list me hai.`")
        raid_list.append(user.id)
        await eor(message, f"`✅ {user.first_name} ko {list_name} me add kar diya gaya hai.`")
    else: # remove
        if user.id not in raid_list:
            return await eor(message, f"`🤷‍♂️ {user.first_name} {list_name} list me hai hi nahi.`")
        raid_list.remove(user.id)
        await eor(message, f"`✅ {user.first_name} ko {list_name} se hata diya gaya hai.`")

@client.on_message(filters.command(["rr", "replyraid"], ".") & filters.me)
async def add_reply_raid(_, message: Message):
    await toggle_reply_raid(message, ACTIVATE_RLIST, "Reply Raid", "add")

@client.on_message(filters.command(["drr", "dreplyraid"], ".") & filters.me)
async def remove_reply_raid(_, message: Message):
    await toggle_reply_raid(message, ACTIVATE_RLIST, "Reply Raid", "remove")

@client.on_message(filters.command(["rlr", "replyloveraid"], ".") & filters.me)
async def add_reply_love_raid(_, message: Message):
    await toggle_reply_raid(message, ACTIVATE_LLIST, "Reply Love Raid", "add")

@client.on_message(filters.command(["drlr", "dreplyloveraid"], ".") & filters.me)
async def remove_reply_love_raid(_, message: Message):
    await toggle_reply_raid(message, ACTIVATE_LLIST, "Reply Love Raid", "remove")

@client.on_message(filters.incoming & ~filters.me & ~filters.service)
async def watch_raids(_, message: Message):
    if not message.from_user: return
    user_id = message.from_user.id
    
    if user_id in ACTIVATE_RLIST:
        await asyncio.sleep(0.3)
        await message.reply_text(f"{message.from_user.mention} {random.choice(RAID)}")
    
    if user_id in ACTIVATE_LLIST:
        await asyncio.sleep(0.3)
        await message.reply_text(f"{message.from_user.mention} {random.choice(LOVE)}")

# ================================== MAIN ================================== #

async def start_bots():
    print("INFO: Starting Hoster Bot...")
    await app.start()
    print("INFO: Hoster Bot started.")
    
    print("INFO: Starting Userbot...")
    await client.start()
    me = await client.get_me()
    print(f"INFO: Userbot started as {me.first_name} ({me.id}).")
    
    await idle()

if __name__ == "__main__":
    print("========================================")
    print("   Romeo Userbot Starting Up...   ")
    print("========================================")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_bots()) 
