import os
import sys
import aiohttp
import asyncio
import logging
from random import choice
from pyrogram import Client, filters, idle
from pyrogram.handlers import MessageHandler
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped

# ==================== LOGGING ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MULTI-DISPATCHER")

# ==================== CONFIGURATION ====================
API_ID = int(os.getenv("API_ID", "10796618"))
API_HASH = os.getenv("API_HASH", "4e4b20b4e1e40c90fcb1a7658c800150")
ALIVE_PIC = os.getenv("ALIVE_PIC", "https://telegra.ph/file/a62b9c7d9848afde0569e.jpg")

BOT_TOKENS = [
    "8722343571:AAGb0-cVV3UIlICubXrBQkNgey-ia4lC_hk",
    "8683176658:AAHD6qzboGWR3pD4yr3ODQg1pzopX4gVvk4",
]

SUDO_USERS = [5368154755, 7595462949, 8288876886]

MAX_FILE_SIZE = 200 * 1024 * 1024

MUSIC_QUEUE = {}
DOWNLOADING_STATE = {}
QUEUED_MSG_IDS = set()
SHARED_DOWNLOADS = {}
VC_ACTION_LOCK = {}

# Dynamic Command Lock System (Only 1 bot processes a command)
CMD_LOCK = set()

async def acquire_lock(message: Message) -> bool:
    if not message: return False
    key = f"{message.chat.id}_{message.id}"
    if key in CMD_LOCK: return False
    CMD_LOCK.add(key)
    # Auto clear cache to prevent memory leak
    async def clear():
        await asyncio.sleep(60)
        CMD_LOCK.discard(key)
    asyncio.create_task(clear())
    return True

# ==================== DATA LISTS ====================
RAID = [
    "CHUTIYE TERI MAA KI CHUT ME MERA LUND", "TERI BEHEN KA BHOSDA", "RANDI KE BACHE", 
    "TERI MAA KA BHOSDA", "MADARCHOD", "BETICHOD", "TERI MAA KI CHUT", "NAALI KE KEEDE"
]
LOVE = [
    "I LOVE YOU JAAN", "MERI JAAN HO TUM", "BABU I LOVE YOU", "MISS YOU JAAN", 
    "Sona I Love You", "Jaanu meri jaan", "Tum meri ho"
]
PORM = [
    "https://telegra.ph/file/02525126831006900f86d.mp4",
    "https://telegra.ph/file/206a233c829e24876356a.mp4"
]

# Global Raid States: {chat_id: set(user_ids)}
RR_STATE = {}
RLR_STATE = {}

# ==================== ROMEO MANAGER ====================

class RomeoManager:
    def __init__(self):
        self.registered_handlers = []
        self.active_clients = []
        self.call_clients = {}

    def on_message(self, custom_filters=None):
        def decorator(func):
            self.registered_handlers.append((func, custom_filters))
            return func
        return decorator

    def apply_handlers_to_client(self, client: Client):
        for func, custom_filters in self.registered_handlers:
            if custom_filters is not None:
                client.add_handler(MessageHandler(func, custom_filters))
            else:
                client.add_handler(MessageHandler(func))

    async def start_all(self, tokens, api_id, api_hash):
        self.active_clients.clear()
        self.call_clients.clear()
        for i, token in enumerate(tokens, 1):
            if not token.strip(): continue
            try:
                client = Client(name=f"romeo_bot_{i}", api_id=api_id, api_hash=api_hash, bot_token=token.strip(), in_memory=True)
                self.apply_handlers_to_client(client)
                await client.start()
                self.active_clients.append(client)
                
                pytgcalls_app = PyTgCalls(client)
                @pytgcalls_app.on_stream_end()
                async def stream_end_handler(_, update):
                    await handle_next_track(client, pytgcalls_app, update.chat_id)
                await pytgcalls_app.start()
                self.call_clients[client] = pytgcalls_app
                
                me = await client.get_me()
                logger.info(f"✅ Bot #{i} Active: @{me.username}")
            except Exception as e:
                logger.error(f"❌ Failed to start bot index {i}: {e}")
        return self.active_clients

    async def stop_all(self):
        for c, p in self.call_clients.items():
            try: await p.stop()
            except: pass
        for c in self.active_clients:
            try: await c.stop()
            except: pass
        self.active_clients.clear()
        self.call_clients.clear()

romeo = RomeoManager()

async def bot_api(token: str, method: str, **kwargs) -> bool:
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(f"https://api.telegram.org/bot{token}/{method}", json=kwargs) as r:
                return (await r.json()).get("ok", False)
    except: return False

# ==================== HELPERS ====================

async def resolve_target_chat(bot: Client, message: Message):
    args = message.text.split()
    if len(args) > 1 and (args[1].startswith("@") or args[1].lstrip("-").isdigit()):
        try: return await bot.get_chat(args[1])
        except Exception as e:
            await message.reply_text(f"❌ Target resolve fail: `{e}`")
            return None
    return message.chat

async def safe_file_cleanup(file_path: str, is_temp: bool, msg_id=None):
    if msg_id and msg_id in SHARED_DOWNLOADS: SHARED_DOWNLOADS.pop(msg_id, None)
    if msg_id and msg_id in QUEUED_MSG_IDS: QUEUED_MSG_IDS.discard(msg_id)
    if is_temp and file_path and os.path.exists(file_path) and "helper/Audio" not in file_path:
        try: os.remove(file_path)
        except: pass

async def predownload_next_track(bot: Client, chat_id: int):
    queue = MUSIC_QUEUE.get(chat_id, [])
    if len(queue) > 1:
        next_item = queue[1]
        if next_item.get("is_temp") and not next_item.get("downloaded_path") and next_item.get("media_msg"):
            if DOWNLOADING_STATE.get(chat_id): return
            DOWNLOADING_STATE[chat_id] = True
            try:
                path = await bot.download_media(next_item["media_msg"])
                next_item["downloaded_path"] = path
            except: pass
            finally: DOWNLOADING_STATE[chat_id] = False

# ==================== VC SYNC SYSTEM ====================

async def all_bots_action(action: str, chat_id: int, stream=None):
    """Sirf wo bots VC join/pause karenge jo Group me Admin hain (Silently)"""
    tasks = []
    for client, pytgcalls_app in romeo.call_clients.items():
        try:
            me = await client.get_me()
            member = await client.get_chat_member(chat_id, me.id)
            if member.status.value == "administrator" and member.privileges and member.privileges.can_manage_video_chats:
                if action == "pause": tasks.append(pytgcalls_app.pause_stream(chat_id))
                elif action == "resume": tasks.append(pytgcalls_app.resume_stream(chat_id))
                elif action == "leave": tasks.append(pytgcalls_app.leave_group_call(chat_id))
                elif action == "play" and stream:
                    # Naya object for independent streaming
                    is_video = isinstance(stream, AudioVideoPiped)
                    p = stream.path if hasattr(stream, 'path') else None
                    s = AudioVideoPiped(p) if is_video else AudioPiped(p)
                    tasks.append(pytgcalls_app.join_group_call(chat_id, s))
                elif action == "change" and stream:
                    is_video = isinstance(stream, AudioVideoPiped)
                    p = stream.path if hasattr(stream, 'path') else None
                    s = AudioVideoPiped(p) if is_video else AudioPiped(p)
                    tasks.append(pytgcalls_app.change_stream(chat_id, s))
        except Exception:
            continue # Group me nahi hai ya admin nahi hai - chup raho (no error)
    if tasks: return await asyncio.gather(*tasks, return_exceptions=True)
    return []

async def handle_next_track(bot: Client, pytgcalls_app: PyTgCalls, chat_id: int):
    if VC_ACTION_LOCK.get(chat_id): return
    VC_ACTION_LOCK[chat_id] = True
    try:
        queue = MUSIC_QUEUE.get(chat_id, [])
        if queue:
            finished = queue.pop(0)
            curr_path = finished.get("downloaded_path") or finished.get("file")
            await safe_file_cleanup(curr_path, finished.get("is_temp", False), finished.get("msg_id"))

        if not queue:
            await all_bots_action("leave", chat_id)
            MUSIC_QUEUE.pop(chat_id, None)
            return

        next_item = queue[0]
        next_path = next_item.get("downloaded_path")

        if not next_path and next_item.get("is_temp") and next_item.get("media_msg"):
            next_path = await bot.download_media(next_item["media_msg"])
            next_item["downloaded_path"] = next_path
            if next_item.get("msg_id"): SHARED_DOWNLOADS[next_item["msg_id"]] = next_path
        elif not next_path:
            next_path = next_item.get("file")

        s = AudioVideoPiped(next_path) if next_item.get("is_video", False) else AudioPiped(next_path)
        await all_bots_action("change", chat_id, s)
        asyncio.create_task(predownload_next_track(bot, chat_id))
    except: pass
    finally: VC_ACTION_LOCK[chat_id] = False

# ==================== BASIC COMMANDS ====================

@romeo.on_message(filters.command("start", ["/", "."]))
async def start_cmd(bot: Client, message: Message):
    if not await acquire_lock(message): return
    me = await bot.get_me()
    caption = (
        f"**🌟 Welcome to Multi-Bot Assistant (@{me.username}) 🌟**\n\n"
        f"🤖 **Status:** Online & Ready!\n"
        f"👤 **Bot Name:** {me.first_name}\n"
        f"⚡ **Engine:** Romeo Multi-Bot Dispatcher\n\n"
        f"Commands janne ke liye `/help` use karein."
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Support Group", url="https://t.me/RomeoBot_op")],
        [InlineKeyboardButton("📢 Updates Channel", url="https://t.me/Romeo_op")]
    ])
    
    try:
        await message.reply_photo(photo=ALIVE_PIC, caption=caption, reply_markup=buttons)
    except Exception:
        await message.reply_text(caption, reply_markup=buttons)

@romeo.on_message(filters.command("help", ["/", "."]))
async def help_cmd(bot: Client, message: Message):
    if not await acquire_lock(message): return
    help_text = (
        "**📖 Romeo Multi-Bot Ultimate Guide 📖**\n\n"
        "**───────── BASIC COMMANDS ─────────**\n"
        "• `/start` , `/alive` , `/ping` , `/help` , `/queue` \n\n"

        "**───────── MUSIC CONTROLS (Sudo) ─────────**\n"
        "• `/play [target]` , `/skip [target]` , `/pause [target]` \n"
        "• `/resume [target]` , `/leavevc [target]` , `/clearqueue [target]` \n\n"

        "**───────── MASS DESTRUCTION (Sudo) ─────────**\n"
        "• `/banall [target]` → Group ke sabhi members ko ban karein.\n\n"

        "**───────── SPAM & RAID (Sudo) ─────────**\n"
        "• `/spam <count>` → Reply to media/text to spam.\n"
        "• `/raid <count> <user>` → User ko gaali raid karne ke liye.\n"
        "• `/lraid <count> <user>` → User ko love raid karne ke liye.\n"
        "• `/psm <count>` → Adult video spam karne ke liye.\n\n"

        "**───────── REPLY RAID (Sudo) ─────────**\n"
        "• `/rr <user/reply>` → Auto-reply raid (Gaali) activate karein.\n"
        "• `/drr` → Reply raid band karein.\n"
        "• `/rlr <user/reply>` → Auto-reply love raid (Pyaar) activate karein.\n"
        "• `/drlr` → Love reply raid band karein.\n"
        "📝 *Note: Agar dono active hain to 2 msg jayenge (1 gaali, 1 pyaar). Sudo ko sirf pyaar jayega.*\n\n"

        "**───────── PROFILE SETUP (Sudo) ─────────**\n"
        "• `.setname <Name>` , `.setbio <Bio>` , `.setdesc <Desc>` , `.setpic` \n\n"
        "💡 **Targeting Rule:** Command ke aage `@group` ya `groupID` lene par us target group me kaam hoga. Agar nahi doge toh CURRENT group me action hoga!"
    )
    await message.reply_text(help_text)

@romeo.on_message(filters.command(["ping", "alive"], ["/", "."]))
async def ping_cmd(bot: Client, message: Message):
    await message.reply_text("🏓 Pong!")

@romeo.on_message(filters.command(["queue", "q"], ["/", "."]))
async def show_queue_cmd(bot: Client, message: Message):
    if not await acquire_lock(message): return
    target_chat = await resolve_target_chat(bot, message)
    if not target_chat: return
    queue = MUSIC_QUEUE.get(target_chat.id, [])
    if not queue: return await message.reply_text("📭 Queue khali hai.")
    text = f"**📋 Queue:**\n\n▶️ `{queue[0]['title']}`\n\n"
    if len(queue) > 1:
        text += "📑 **Up Next:**\n" + "\n".join(f"`{i}.` {q['title']}" for i, q in enumerate(queue[1:10], 1))
    await message.reply_text(text)

# ==================== VC CONTROLS ====================

@romeo.on_message(filters.command(["play", "vcplay"], ["/", "."]) & filters.user(SUDO_USERS))
async def play_vc_cmd(bot: Client, message: Message):
    if not await acquire_lock(message): return
    target_chat = await resolve_target_chat(bot, message)
    if not target_chat: return

    # Check if ANY bot is admin
    admin_exists = False
    for c in romeo.active_clients:
        try:
            m = await c.get_chat_member(target_chat.id, (await c.get_me()).id)
            if m.status.value == "administrator" and m.privileges and m.privileges.can_manage_video_chats:
                admin_exists = True; break
        except: pass
    if not admin_exists:
        return await message.reply_text("⚠️ **Koi bhi bot is group me Admin (Manage VC) nahi hai!**")

    reply = message.reply_to_message
    msg_id = reply.id if reply else None

    if msg_id and msg_id in QUEUED_MSG_IDS: pass
    else:
        if reply and (reply.audio or reply.video or reply.voice or reply.document):
            if getattr(reply.audio or reply.video or reply.voice or reply.document, "file_size", 0) > MAX_FILE_SIZE:
                return await message.reply_text("❌ File 200MB limit!")
            is_vid = bool(reply.video or (reply.document and "video" in str(getattr(reply.document, "mime_type", ""))))
            item = {"title": getattr(reply.audio or reply.video or reply.document, "file_name", None) or "Track",
                    "media_msg": reply, "msg_id": msg_id, "downloaded_path": None, "is_video": is_vid, "is_temp": True}
        else:
            if not os.path.exists("./helper/Audio/B1.mp3"): return await message.reply_text("❌ Default audio missing.")
            item = {"title": "Default Track", "file": "./helper/Audio/B1.mp3", "downloaded_path": "./helper/Audio/B1.mp3", "msg_id": None, "is_video": False, "is_temp": False}

        if target_chat.id not in MUSIC_QUEUE: MUSIC_QUEUE[target_chat.id] = []
        MUSIC_QUEUE[target_chat.id].append(item)
        if msg_id: QUEUED_MSG_IDS.add(msg_id)

        if len(MUSIC_QUEUE[target_chat.id]) > 1:
            asyncio.create_task(predownload_next_track(bot, target_chat.id))
            return await message.reply_text(f"✅ **Queued #{len(MUSIC_QUEUE[target_chat.id])-1}** | `{item['title']}`")

    sent = await message.reply_text("📥 **Sab Admin Bots VC me join ho rahe hain...**")
    current = MUSIC_QUEUE[target_chat.id][0]
    
    if current.get("msg_id") and current["msg_id"] in SHARED_DOWNLOADS: dl = SHARED_DOWNLOADS[current["msg_id"]]
    elif current.get("is_temp"):
        dl = await bot.download_media(current["media_msg"])
        current["downloaded_path"] = dl
        if current.get("msg_id"): SHARED_DOWNLOADS[current["msg_id"]] = dl
    else: dl = current.get("downloaded_path") or current.get("file")

    stream = AudioVideoPiped(dl) if current.get("is_video") else AudioPiped(dl)
    results = await all_bots_action("play", target_chat.id, stream)
    
    success = sum(1 for r in results if not isinstance(r, Exception))
    if success > 0 or any("already" in str(e).lower() for e in results if isinstance(e, Exception)):
        await sent.edit(f"🎶 **Max Sound Active! ({success} Bots Playing)**\n🎵 `{current['title']}`")
    else:
        MUSIC_QUEUE[target_chat.id].pop(0)
        await sent.edit("❌ **VC Join Error!**")

@romeo.on_message(filters.command(["skip", "vcskip"], ["/", "."]) & filters.user(SUDO_USERS))
async def skip_vc_cmd(bot: Client, message: Message):
    if not await acquire_lock(message): return
    target_chat = await resolve_target_chat(bot, message)
    if not target_chat or not MUSIC_QUEUE.get(target_chat.id): return await message.reply_text("📭 Queue khali hai.")
    await message.reply_text("⏭️ **Skipping in all bots...**")
    await handle_next_track(bot, list(romeo.call_clients.values())[0], target_chat.id)

@romeo.on_message(filters.command(["pause", "vcpause"], ["/", "."]) & filters.user(SUDO_USERS))
async def pause_vc_cmd(bot: Client, message: Message):
    if not await acquire_lock(message): return
    target_chat = await resolve_target_chat(bot, message)
    await all_bots_action("pause", target_chat.id)
    await message.reply_text("⏸️ **Sare bots pause ho gaye.**")

@romeo.on_message(filters.command(["resume", "vcresume"], ["/", "."]) & filters.user(SUDO_USERS))
async def resume_vc_cmd(bot: Client, message: Message):
    if not await acquire_lock(message): return
    target_chat = await resolve_target_chat(bot, message)
    await all_bots_action("resume", target_chat.id)
    await message.reply_text("▶️ **Sare bots resume ho gaye.**")

@romeo.on_message(filters.command(["leavevc", "stopvc"], ["/", "."]) & filters.user(SUDO_USERS))
async def leave_vc_cmd(bot: Client, message: Message):
    if not await acquire_lock(message): return
    target_chat = await resolve_target_chat(bot, message)
    if not target_chat: return
    for item in MUSIC_QUEUE.pop(target_chat.id, []):
        await safe_file_cleanup(item.get("downloaded_path") or item.get("file"), item.get("is_temp", False), item.get("msg_id"))
    VC_ACTION_LOCK.pop(target_chat.id, None)
    await all_bots_action("leave", target_chat.id)
    await message.reply_text("🛑 **Sare bots ne VC chhod diya.**")

@romeo.on_message(filters.command(["clearqueue", "cqueue"], ["/", "."]) & filters.user(SUDO_USERS))
async def clear_queue_cmd(bot: Client, message: Message):
    if not await acquire_lock(message): return
    target_chat = await resolve_target_chat(bot, message)
    queue = MUSIC_QUEUE.get(target_chat.id, [])
    if not queue: return await message.reply_text("📭 Khali hai.")
    for item in queue[1:]:
        await safe_file_cleanup(item.get("downloaded_path"), item.get("is_temp"), item.get("msg_id"))
    MUSIC_QUEUE[target_chat.id] = [queue[0]]
    await message.reply_text("🗑️ **Queue clear!**")

# ==================== PROFILE CUSTOMIZATION ====================

@romeo.on_message(filters.command(["setname","setbio","setdesc","setpic"], ["/","."]) & filters.user(SUDO_USERS))
async def profile_cmd(bot: Client, message: Message):
    if not await acquire_lock(message): return
    cmd = message.command[0].lower()
    if cmd == "setpic":
        if not message.reply_to_message or not message.reply_to_message.photo: return
        op = await message.reply_text("🔄 DP update ho rahi hai...")
        file = await bot.download_media(message.reply_to_message.photo)
        for c in romeo.active_clients:
            try: await c.set_profile_photo(photo=file)
            except: pass
        if os.path.exists(file): os.remove(file)
        return await op.edit("✅ DP Updated!")

    if len(message.command) < 2: return
    text = message.text.split(None, 1)[1]
    api_map = {"setname": ("setMyName", {"name": text}), "setbio": ("setMyShortDescription", {"short_description": text}), "setdesc": ("setMyDescription", {"description": text})}
    method, payload = api_map[cmd]
    for token in BOT_TOKENS: await bot_api(token.strip(), method, **payload)
    await message.reply_text(f"✅ `{cmd}` → `{text}` applied!")

# ==================== DESTRUCTION (DISTRIBUTED) ====================

@romeo.on_message(filters.command("banall", ["/", "."]) & filters.user(SUDO_USERS))
async def banall_cmd(bot: Client, message: Message):
    if not await acquire_lock(message): return
    target_chat = await resolve_target_chat(bot, message)
    if not target_chat: return
    
    admin_bots = []
    for c in romeo.active_clients:
        try:
            m = await c.get_chat_member(target_chat.id, (await c.get_me()).id)
            if m.status.value == "administrator" and m.privileges and m.privileges.can_restrict_members:
                admin_bots.append(c)
        except: pass
        
    if not admin_bots: return await message.reply_text("❌ **Koi bot Admin nahi hai.**")
    
    sent = await message.reply_text(f"🚀 **Banall started with {len(admin_bots)} Bots in Parallel...**")
    ban_count = 0; idx = 0; tasks = []
    
    async for member in bot.get_chat_members(target_chat.id):
        if member.user.id in SUDO_USERS or member.user.is_self: continue
        # Divide bans equally among all admin bots for max speed
        c_bot = admin_bots[idx % len(admin_bots)]
        tasks.append(c_bot.ban_chat_member(target_chat.id, member.user.id))
        ban_count += 1; idx += 1
        
        if len(tasks) >= len(admin_bots) * 5:
            await asyncio.gather(*tasks, return_exceptions=True)
            tasks.clear()
            await asyncio.sleep(0.2) # Flood protection
            
    if tasks: await asyncio.gather(*tasks, return_exceptions=True)
    await sent.edit(f"✅ **Banned `{ban_count}` members using {len(admin_bots)} bots.**")

# ==================== MAX SPAM/RAID ====================

async def get_member_bots(chat_id: int):
    members = []
    for c in romeo.active_clients:
        try: 
            await c.get_chat_member(chat_id, (await c.get_me()).id)
            members.append(c)
        except: pass
    return members

@romeo.on_message(filters.command(["spam", "s"], ["/", "."]) & filters.user(SUDO_USERS))
async def spam_cmd(bot: Client, message: Message):
    if not await acquire_lock(message): return
    args = message.text.split()
    if len(args) < 2: return
    try: count = int(args[1])
    except: return
    await message.delete()
    
    members = await get_member_bots(message.chat.id)
    if not members: return

    for _ in range(count):
        if message.reply_to_message:
            tasks = [c.copy_message(message.chat.id, message.chat.id, message.reply_to_message.id) for c in members]
        elif len(args) > 2:
            txt = message.text.split(None, 2)[2]
            tasks = [c.send_message(message.chat.id, txt) for c in members]
        await asyncio.gather(*tasks, return_exceptions=True)
        await asyncio.sleep(0.1)

@romeo.on_message(filters.command(["raid", "r", "lraid", "lr"], ["/", "."]) & filters.user(SUDO_USERS))
async def raid_cmd(bot: Client, message: Message):
    if not await acquire_lock(message): return
    parts = message.text.split(); cmd = parts[0].lower()
    try: count = int(parts[1]) if len(parts) > 1 else 5
    except: return
    user = message.reply_to_message.from_user if message.reply_to_message else None
    if not user and len(parts) > 2:
        try: user = await bot.get_users(parts[2])
        except: return
    if not user: return
    await message.delete()
    
    members = await get_member_bots(message.chat.id)
    lst = LOVE if "lraid" in cmd or "lr" in cmd else RAID
    mention = f"@{user.username}" if user.username else f"[{user.first_name}](tg://user?id={user.id})"
    
    for _ in range(count):
        tasks = [c.send_message(message.chat.id, f"{mention} {choice(lst)}") for c in members]
        await asyncio.gather(*tasks, return_exceptions=True)
        await asyncio.sleep(0.5)

@romeo.on_message(filters.command(["psm"], ["/", "."]) & filters.user(SUDO_USERS))
async def psm_cmd(bot: Client, message: Message):
    if not await acquire_lock(message): return
    try: count = int(message.command[1]) if len(message.command) > 1 else 5
    except: count = 5
    await message.delete()
    members = await get_member_bots(message.chat.id)
    for _ in range(count):
        tasks = [c.send_video(message.chat.id, video=choice(PORM)) for c in members]
        await asyncio.gather(*tasks, return_exceptions=True)
        await asyncio.sleep(1)

# ==================== REPLY RAID ====================

@romeo.on_message(filters.command(["rr", "rlr"], ["/", "."]) & filters.user(SUDO_USERS))
async def activate_rr(bot: Client, message: Message):
    if not await acquire_lock(message): return
    cmd = message.command[0].lower()
    user = message.reply_to_message.from_user if message.reply_to_message else None
    if not user and len(message.command) > 1:
        try: user = await bot.get_users(message.command[1])
        except: return
    if not user: return
    
    state_dict = RLR_STATE if "rlr" in cmd else RR_STATE
    if message.chat.id not in state_dict: state_dict[message.chat.id] = set()
    state_dict[message.chat.id].add(user.id)
    await message.reply_text(f"✅ **Activated** for {user.mention}!")

@romeo.on_message(filters.command(["drr", "drlr"], ["/", "."]) & filters.user(SUDO_USERS))
async def stop_rr(bot: Client, message: Message):
    if not await acquire_lock(message): return
    cmd = message.command[0].lower()
    user = message.reply_to_message.from_user if message.reply_to_message else None
    if not user and len(message.command) > 1:
        try: user = await bot.get_users(message.command[1])
        except: return
    if not user: return await message.reply_text("⚠️ User specify karo!")
    
    state_dict = RLR_STATE if "drlr" in cmd else RR_STATE
    chat_users = state_dict.get(message.chat.id, set())
    if user.id in chat_users:
        chat_users.remove(user.id)
        if not chat_users: state_dict.pop(message.chat.id, None)
        await message.reply_text(f"❌ **Deactivated** for {user.mention}!")

@romeo.on_message(filters.incoming & filters.group)
async def rr_logic_handler(bot: Client, message: Message):
    # Lock isme nahi laga, taaki SARE bots gaali/love ek saath bhej sakein (Max Effect)
    if not message.from_user: return
    uid = message.from_user.id
    if uid in RR_STATE.get(message.chat.id, set()) and uid not in SUDO_USERS:
        await message.reply_text(f"[{message.from_user.first_name}](tg://user?id={uid}) {choice(RAID)}")
    if uid in RLR_STATE.get(message.chat.id, set()):
        await message.reply_text(f"[{message.from_user.first_name}](tg://user?id={uid}) {choice(LOVE)}")

# ==================== STARTUP ====================

async def start_bot():
    bots = await romeo.start_all(BOT_TOKENS, API_ID, API_HASH)
    if not bots:
        raise Exception("No valid bot tokens initialized.")
    first_bot = await bots[0].get_me()
    return first_bot.username

async def stop_bot():
    await romeo.stop_all()

# ==================== STANDALONE RUNNER ====================

if __name__ == "__main__":
    async def main_standalone():
        try:
            bots = await romeo.start_all(BOT_TOKENS, API_ID, API_HASH)
            print("=" * 50)
            print(f"🚀 Romeo Multi-Bot Active ({len(bots)} Bots)")
            print("=" * 50)
            await idle()
        finally:
            await romeo.stop_all()

    try:
        asyncio.run(main_standalone())
    except KeyboardInterrupt:
        print("\n👋 System shut down.")
