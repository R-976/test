import os
import sys
import aiohttp
import asyncio
import logging
from random import choice
from pyrogram import Client, filters, idle
from pyrogram.handlers import MessageHandler
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

# ==================== LOGGING ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MULTI-DISPATCHER")

for noisy in ['pyrogram', 'pyrogram.session', 'pyrogram.connection']:
    logging.getLogger(noisy).setLevel(logging.WARNING)

def ignore_peer_errors(loop, context):
    return
    
# ==================== CONFIGURATION ====================
API_ID = int(os.getenv("API_ID", "10796618"))
API_HASH = os.getenv("API_HASH", "4e4b20b4e1e40c90fcb1a7658c800150")
ALIVE_PIC = os.getenv("ALIVE_PIC", "https://telegra.ph/file/a62b9c7d9848afde0569e.jpg")

BOT_TOKENS = [
    "8722343571:AAGb0-cVV3UIlICubXrBQkNgey-ia4lC_hk",
    "8683176658:AAHD6qzboGWR3pD4yr3ODQg1pzopX4gVvk4",
]

SUDO_USERS = [5368154755, 7595462949, 8288876886]
GROUP = [-1001727158017, -1001265778325, -1001625889213, -1001882915379]
MAX_FILE_SIZE = 200 * 1024 * 1024

RR_STATE = {}
RLR_STATE = {}

CMD_LOCK = set()

async def acquire_lock(message: Message) -> bool:
    if not message: return False
    key = f"{message.chat.id}_{message.id}"
    if key in CMD_LOCK: return False
    CMD_LOCK.add(key)
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
    "https://telegra.ph/file/9bcc076fd81dfe3feb291.mp4",
    "https://telegra.ph/file/b7a1a42429a65f64e67af.mp4",
    "https://telegra.ph/file/dc3da5a3eb77ae20fa21d.mp4",
    "https://telegra.ph/file/22b89774a4ba9219d530b.mp4",
    "https://telegra.ph/file/7b15fbca08ae1e73e559c.mp4",
    "https://telegra.ph/file/a9c1dea3f34925bb60686.mp4"
]

# ==================== ROMEO MANAGER ====================

class RomeoManager:
    def __init__(self):
        self.registered_handlers = []
        self.active_clients = []

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
        for i, token in enumerate(tokens, 1):
            if not token.strip(): continue
            try:
                client = Client(name=f"romeo_bot_{i}", api_id=api_id, api_hash=api_hash, bot_token=token.strip(), in_memory=True)
                self.apply_handlers_to_client(client)
                await client.start()
                self.active_clients.append(client)
                me = await client.get_me()
                logger.info(f"✅ Bot #{i} Active: @{me.username}")
            except Exception as e:
                logger.error(f"❌ Failed to start bot index {i}: {e}")
        return self.active_clients

    async def stop_all(self):
        for c in self.active_clients:
            try: await c.stop()
            except: pass
        self.active_clients.clear()

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

async def restart_all_bots(message: Message):
    """Stop all bots and restart the entire process"""
    try:
        await message.reply_text(f"🔄 **Restarting all bots...**\n\n⏳ Bot 2-3 seconds me wapas aayega!")
        for c in romeo.active_clients:
            try: await c.stop()
            except: pass
        romeo.active_clients.clear()
        await asyncio.sleep(1)
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        try:
            await message.reply_text(f"⚠️ Force restarting...\n`{e}`")
        except: pass
        os.execv(sys.executable, [sys.executable] + sys.argv)
        
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
        "• `/restart` → Sare bots restart karo (lag/crash fix)\n"
        "• `/start` , `/alive` , `/ping` , `/help`\n\n"

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

@romeo.on_message(filters.command(["restart", "reboot"], ["/", "."]) & filters.user(SUDO_USERS))
async def restart_cmd(bot: Client, message: Message):
    if not await acquire_lock(message): return
    await restart_all_bots(message)

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
    if target_chat in GROUP: return await message.reply_text("**Sorry !! i Can't do magic Here.**")
    
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
        c_bot = admin_bots[idx % len(admin_bots)]
        tasks.append(c_bot.ban_chat_member(target_chat.id, member.user.id))
        ban_count += 1; idx += 1
        
        if len(tasks) >= len(admin_bots) * 5:
            await asyncio.gather(*tasks, return_exceptions=True)
            tasks.clear()
            await asyncio.sleep(0.2)
            
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
        else:
            break  # ✅agar reply bhi nahi aur text bhi nahi to tasks define nahi hoga ( kuch nahi diya to loop tod do )
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
    if user in SUDO_USERS: return await message.reply_text("This guy is a sudo users.")
    await message.delete()
    
    members = await get_member_bots(message.chat.id)
    rj = LOVE if "lraid" in cmd or "lr" in cmd else RAID
    mention = f"@{user.username}" if user.username else f"[{user.first_name}](tg://user?id={user.id})"
    
    for _ in range(count):
        tasks = [c.send_message(message.chat.id, f"{mention} {choice(rj)}") for c in members]
        await asyncio.gather(*tasks, return_exceptions=True)
        await asyncio.sleep(0.5)

@romeo.on_message(filters.command(["psm"], ["/", "."]) & filters.user(SUDO_USERS))
async def psm_cmd(bot: Client, message: Message):
    if not await acquire_lock(message): return
    target_chat = await resolve_target_chat(bot, message)
    if not target_chat: return
    if target_chat in GROUP: return await message.reply_text("**Sorry !! i Can't do magic Here.**")
    
    try: count = int(message.command[1]) if len(message.command) > 1 else 5
    except: count = 5
    await message.delete()
    members = await get_member_bots(message.chat.id)
    for _ in range(count):
        tasks = [c.send_video(message.chat.id, video=choice(PORM)) for c in members]
        await asyncio.gather(*tasks, return_exceptions=True)
        await asyncio.sleep(1)

# ==================== REPLY RAID ====================

@romeo.on_message(filters.command(["rr", "replyraid", "rlr", "replyloveraid"], ["/", "."]) & filters.user(SUDO_USERS))
async def activate_rr(bot: Client, message: Message):
    if not await acquire_lock(message): return
    cmd = message.command[0].lower()
    user = message.reply_to_message.from_user if message.reply_to_message else None
    if not user and len(message.command) > 1:
        try: user = await bot.get_users(message.command[1])
        except: return
    if not user: return
    
    state_dict = RR_STATE if "rr" in cmd or "replyraid" in cmd else RLR_STATE
    if message.chat.id not in state_dict: state_dict[message.chat.id] = set()
    state_dict[message.chat.id].add(user.id)
    await message.reply_text(f"✅ **Activated** for {user.mention}!")

@romeo.on_message(filters.command(["drr", "dreplyraid", "drlr", "dreplyloveraid"], ["/", "."]) & filters.user(SUDO_USERS))
async def stop_rr(bot: Client, message: Message):
    if not await acquire_lock(message): return
    cmd = message.command[0].lower()
    user = message.reply_to_message.from_user if message.reply_to_message else None
    if not user and len(message.command) > 1:
        try: user = await bot.get_users(message.command[1])
        except: return
    if not user: return await message.reply_text("⚠️ User specify karo!")
    
    state_dict = RR_STATE  if "drr" in cmd or "dreplyraid" in cmd else RLR_STATE
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
    rj = f"@{message.from_user.username}" if message.from_user.username else f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"
    if uid in RR_STATE.get(message.chat.id, set()) and uid not in SUDO_USERS:
        await message.reply_text(f"{rj} {choice(RAID)}")
    if uid in RLR_STATE.get(message.chat.id, set()):
        await message.reply_text(f"{rj} {choice(LOVE)}")

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
