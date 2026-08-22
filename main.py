import os
import re
import time
import shutil
import random
import asyncio
from typing import Union, List
from pyrogram import Client, filters
from pyrogram.types import (
    Message, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    CallbackQuery,
    ChatMemberUpdated
)
from pyrogram.enums import ChatMemberStatus, ChatMembersFilter
from pyrogram.errors import UserAlreadyParticipant, UserNotParticipant
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream, AudioQuality, VideoQuality
from pytgcalls.exceptions import NoActiveGroupCall, GroupCallNotFound
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from motor.motor_asyncio import AsyncIOMotorClient

# ==================== CONFIGURATION ====================
API_ID = int(os.environ.get("API_ID", "19031598"))
API_HASH = os.environ.get("API_HASH", "14e2d2af6e6dc769e60991cab81027d5")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "5523050102:AAFMpTYcxftUYAW-L-RSVVCns-uGjfGAF_E")
SESSION_STRING = os.environ.get("SESSION_STRING", "BQCkvkoAU7nTFh4-Q1ZHq7qBh1MwF5RhkDYxSgsrDQYJoD0bvIQilfWDjp4cPnbzDgcd7-mEfy2xCzW26BRNTwnVEa-oz5HU6xD7Zm2_85SlNGzzyBdugP2fr4LS_6ft6HDWHEklqx93N4BN353Ak9Hn8bNN5oGgl72A-YB4Lz-JYw83QSrQphZOAMtDfZbJbgU0mygbgNzLiRj4eSlxJ9uPRp1gnfAUxwSnOaYWOo6DGnC4dsPDR-gVCXy1WX1UHleqlrABsDYLvMiRcJFHAB-emF0nCZisTrRx6Y4It9SaBazWpPWOpa4XWw_umnSYF6-krvqyYgnEnOZ8xQtZBu_LfjxkRQAAAAHwPlCqAA")
MONGO_DB_URI = os.environ.get("MONGO_DB_URI", "mongodb+srv://chatfight:chatfight@chatfight.1va4gdm.mongodb.net/?appName=chatfight")
OWNER_ID = int(os.environ.get("OWNER_ID", "5368154755"))
LOG_GROUP_ID = int(os.environ.get("LOG_GROUP_ID", "-1002935351540"))

SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", "c7ac5c70cda042dca0ae2ef11e0e22c3")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "608e63ab16ae486bb257602bd02cb7a1")
COOKIE_PATH = os.environ.get("COOKIE_PATH", "cookies.txt")

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ==================== CLIENTS & DB ====================
bot = Client("RomeoMusicBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
userbot = Client("RomeoAssistant", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
call_py = PyTgCalls(userbot)

mongo_client = AsyncIOMotorClient(MONGO_DB_URI)
db = mongo_client.RomeoMusic
auth_db = db.auth_users
sudo_db = db.sudo_users
bl_chat_db = db.blacklisted_chats
bl_user_db = db.blacklisted_users
channel_db = db.channel_connect

# Spotify Client
sp = None
if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
    try:
        sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
            client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET
        ))
    except Exception:
        pass

# Group-isolated In-Memory State
QUEUE = {}          # {chat_id: [{"title": str, "file": str, "is_video": bool, "req_by": str}]}
LOOP = {}           # {chat_id: int}
MAINTENANCE = False
BOT_START_TIME = time.time()

# ==================== PERMISSIONS & DB HELPERS ====================
async def is_sudo(user_id: int) -> bool:
    if user_id == OWNER_ID:
        return True
    return bool(await sudo_db.find_one({"user_id": user_id}))

async def is_admin_or_auth(client: Client, chat_id: int, user_id: int) -> bool:
    if await is_sudo(user_id):
        return True
    # Check if Auth in DB
    if await auth_db.find_one({"chat_id": chat_id, "user_id": user_id}):
        return True
    # Check if native Telegram Admin
    try:
        member = await client.get_chat_member(chat_id, user_id)
        if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return True
    except Exception:
        pass
    return False

async def is_banned(user_id: int) -> bool:
    return bool(await bl_user_db.find_one({"user_id": user_id}))

async def is_chat_blacklisted(chat_id: int) -> bool:
    return bool(await bl_chat_db.find_one({"chat_id": chat_id}))

def clean_file(file_path: str):
    if file_path and os.path.exists(file_path) and "downloads" in file_path:
        try:
            os.remove(file_path)
        except Exception:
            pass

# ==================== MEDIA ENGINE ====================
def download_stream(query: str, is_video: bool = False) -> dict:
    file_id = f"{int(time.time())}_{random.randint(100, 999)}"
    out_tmpl = os.path.join(DOWNLOAD_DIR, f"{file_id}.%(ext)s")
    
    ydl_opts = {
        "format": "best[height<=720]" if is_video else "bestaudio/best",
        "outtmpl": out_tmpl,
        "noplaylist": True,
        "quiet": True,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "default_search": "ytsearch",
    }
    if os.path.exists(COOKIE_PATH):
        ydl_opts["cookiefile"] = COOKIE_PATH

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=True)
        if "entries" in info:
            info = info["entries"][0]
        
        file_path = ydl.prepare_filename(info)
        return {
            "title": info.get("title", "Unknown Stream"),
            "file": file_path,
            "duration": info.get("duration", 0),
            "is_video": is_video
        }

def parse_spotify(url: str):
    if not sp:
        return None
    if "track" in url:
        res = sp.track(url)
        return [f"{res['name']} {res['artists'][0]['name']}"]
    elif "playlist" in url:
        res = sp.playlist_tracks(url)
        return [f"{item['track']['name']} {item['track']['artists'][0]['name']}" for item in res['items'] if item.get('track')]
    elif "album" in url:
        res = sp.album_tracks(url)
        return [f"{item['name']} {item['artists'][0]['name']}" for item in res['items']]
    return None

# ==================== PLAYBACK DISPATCHER ====================
async def play_next(chat_id: int):
    if chat_id in QUEUE and QUEUE[chat_id]:
        if LOOP.get(chat_id, 0) > 0:
            track = QUEUE[chat_id][0]
            LOOP[chat_id] -= 1
        else:
            old_track = QUEUE[chat_id].pop(0)
            clean_file(old_track["file"])
            if not QUEUE[chat_id]:
                try:
                    await call_py.leave_call(chat_id)
                except Exception:
                    pass
                return

            track = QUEUE[chat_id][0]

        stream = MediaStream(
            track["file"],
            audio_parameters=AudioQuality.HIGH,
            video_parameters=VideoQuality.HD_720p if track["is_video"] else None,
            video_flags=MediaStream.Flags.IGNORE if not track["is_video"] else None
        )
        try:
            await call_py.play(chat_id, stream)
            await bot.send_message(
                chat_id,
                f"▶️ **Streaming Now:** `{track['title']}`\n"
                f"**Type:** `{'Video' if track['is_video'] else 'Audio'}` | **Requested By:** {track['req_by']}"
            )
        except Exception as e:
            await bot.send_message(chat_id, f"❌ Error streaming next track: `{e}`")
            await play_next(chat_id)
    else:
        try:
            await call_py.leave_call(chat_id)
        except Exception:
            pass

@call_py.on_stream_end()
async def on_stream_end_handler(_, update):
    await play_next(update.chat_id)

# ==================== COMMAND HANDLERS ====================

@bot.on_message(filters.command("start"))
async def start_handler(_, m: Message):
    if await is_banned(m.from_user.id):
        return
    if m.chat.type != m.chat.type.PRIVATE:
        return await m.reply_text("✨ **Romeo Music Bot is active!**")
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Romeo To Group", url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true")],
        [InlineKeyboardButton("📚 Help Commands", callback_data="help_menu_main")]
    ])
    await m.reply_text("👋 **Welcome to Romeo Music Bot!**\nHigh-Quality VC Music & Video Streamer.", reply_markup=keyboard)

@bot.on_message(filters.command("help"))
async def help_handler(_, m: Message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Admin", callback_data="help_admin"), InlineKeyboardButton("Auth", callback_data="help_auth")],
        [InlineKeyboardButton("Play & Loop", callback_data="help_loop"), InlineKeyboardButton("Channel", callback_data="help_channel")],
        [InlineKeyboardButton("Sudo & Misc", callback_data="help_misc"), InlineKeyboardButton("Broadcast", callback_data="help_broadcast")]
    ])
    await m.reply_text("📖 **Select a category to view commands:**", reply_markup=keyboard)

@bot.on_callback_query(filters.regex("^help_"))
async def help_callback(_, query: CallbackQuery):
    cat = query.data.split("_")[1]
    pages = {
        "admin": "<b><u>ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅs :</b></u>\n\n/pause : Pause current stream\n/resume : Resume stream\n/skip : Skip current track\n/stop or /end : Stop and clear queue\n/queue : Show queue tracks\n/shuffle : Shuffle queue",
        "auth": "<b><u>ᴀᴜᴛʜ ᴜsᴇʀs :</b></u>\n\n/auth [user] : Group admins can add auth users\n/unauth [user] : Remove auth users\n/authusers : View chat auth users",
        "broadcast": "<b><u>ʙʀᴏᴀᴅᴄᴀsᴛ :</b></u>\n\n/broadcast [msg] : Broadcast to active groups\n-pin : Pin message",
        "blacklist": "<b><u>ʙʟᴀᴄᴋʟɪsᴛ :</b></u>\n\n/blacklistchat [ID] : Blacklist chat\n/whitelistchat [ID] : Whitelist chat",
        "channel": "<b><u>ᴄʜᴀɴɴᴇʟ ᴩʟᴀʏ :</b></u>\n\n/cplay : Play in connected channel\n/cvplay : Video play in channel\n/channelplay [ID/Disable] : Link group to channel",
        "loop": "<b><u>ʟᴏᴏᴘ :</b></u>\n\n/loop [1-10/disable] : Repeat current stream",
        "misc": "<b><u>ᴘɪɴɢ & sᴛᴀᴛs :</b></u>\n\n/ping : Check latency\n/stats : Bot stats\n/song [query] : Direct download audio"
    }
    if cat == "menu":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Admin", callback_data="help_admin"), InlineKeyboardButton("Auth", callback_data="help_auth")],
            [InlineKeyboardButton("Play & Loop", callback_data="help_loop"), InlineKeyboardButton("Channel", callback_data="help_channel")],
            [InlineKeyboardButton("Sudo & Misc", callback_data="help_misc"), InlineKeyboardButton("Broadcast", callback_data="help_broadcast")]
        ])
        return await query.message.edit("📖 **Select a category:**", reply_markup=keyboard)
    
    text = pages.get(cat, "No information.")
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="help_menu_main")]])
    await query.message.edit(text, reply_markup=kb)

# --- PLAY LOGIC (MULTI-GROUP ISOLATED) ---
@bot.on_message(filters.command(["play", "vplay", "cplay", "cvplay", "playforce", "vplayforce"]) & ~filters.private)
async def play_handler(client: Client, m: Message):
    if MAINTENANCE and not await is_sudo(m.from_user.id):
        return await m.reply_text("⚙️ Bot is currently under maintenance.")
    if await is_banned(m.from_user.id) or await is_chat_blacklisted(m.chat.id):
        return

    chat_id = m.chat.id
    cmd = m.command[0]
    is_video = "v" in cmd
    is_force = "force" in cmd

    if cmd.startswith("c"):
        c_data = await channel_db.find_one({"chat_id": m.chat.id})
        if not c_data:
            return await m.reply_text("❌ Channel connected nahi hai. Link via `/channelplay [ID]`")
        chat_id = c_data["channel_id"]

    if len(m.command) < 2 and not m.reply_to_message:
        return await m.reply_text("❗ Song name ya audio/video file reply karke play karein.")

    status_msg = await m.reply_text("🔍 **Processing Stream...**")

    # Assistant Check
    try:
        await client.get_chat_member(chat_id, (await userbot.get_me()).id)
    except UserNotParticipant:
        try:
            invitelink = await client.export_chat_invite_link(chat_id)
            await userbot.join_chat(invitelink)
        except Exception as e:
            return await status_msg.edit(f"❌ Assistant failed to join group: `{e}`")

    tracks_to_queue = []
    if m.reply_to_message and (m.reply_to_message.audio or m.reply_to_message.video or m.reply_to_message.document):
        media = m.reply_to_message.audio or m.reply_to_message.video or m.reply_to_message.document
        await status_msg.edit("📥 **Downloading Telegram Media...**")
        file_path = await m.reply_to_message.download(file_name=DOWNLOAD_DIR + "/")
        tracks_to_queue.append({
            "title": getattr(media, "file_name", "Telegram File"),
            "file": file_path,
            "duration": getattr(media, "duration", 0),
            "is_video": is_video or bool(m.reply_to_message.video),
            "req_by": m.from_user.mention
        })
    else:
        query = m.text.split(None, 1)[1]
        if "open.spotify.com" in query:
            spotify_queries = parse_spotify(query)
            if not spotify_queries:
                return await status_msg.edit("❌ Spotify stream load nahi ho paya.")
            await status_msg.edit(f"🔎 Spotify tracks fetching: `{len(spotify_queries)}` tracks...")
            for sq in spotify_queries[:8]:
                data = await asyncio.get_event_loop().run_in_executor(None, download_stream, sq, is_video)
                data["req_by"] = m.from_user.mention
                tracks_to_queue.append(data)
        else:
            await status_msg.edit("📥 **Downloading via Engine...**")
            data = await asyncio.get_event_loop().run_in_executor(None, download_stream, query, is_video)
            data["req_by"] = m.from_user.mention
            tracks_to_queue.append(data)

    if not tracks_to_queue:
        return await status_msg.edit("❌ Audio/Video extract nahi ho payi.")

    if chat_id not in QUEUE:
        QUEUE[chat_id] = []

    if is_force:
        QUEUE[chat_id] = tracks_to_queue + QUEUE[chat_id]
        await play_next(chat_id)
        return await status_msg.edit(f"⚡ **Force Playing:** `{tracks_to_queue[0]['title']}`")

    if not QUEUE[chat_id]:
        QUEUE[chat_id].extend(tracks_to_queue)
        first = QUEUE[chat_id][0]
        stream = MediaStream(
            first["file"],
            audio_parameters=AudioQuality.HIGH,
            video_parameters=VideoQuality.HD_720p if first["is_video"] else None,
            video_flags=MediaStream.Flags.IGNORE if not first["is_video"] else None
        )
        try:
            await call_py.play(chat_id, stream)
            await status_msg.edit(f"▶️ **Started Streaming:** `{first['title']}`")
        except NoActiveGroupCall:
            clean_file(first["file"])
            QUEUE[chat_id].clear()
            await status_msg.edit("❌ Voice Chat active nahi hai. Group VC start karein.")
        except Exception as e:
            clean_file(first["file"])
            QUEUE[chat_id].clear()
            await status_msg.edit(f"❌ Playback Error: `{e}`")
    else:
        QUEUE[chat_id].extend(tracks_to_queue)
        await status_msg.edit(f"➕ **Queued at #{len(QUEUE[chat_id]) - 1}:** `{tracks_to_queue[0]['title']}`")

# --- AUTH SYSTEM (ADMINS ADD NON-ADMINS) ---
@bot.on_message(filters.command("auth") & ~filters.private)
async def auth_cmd(client: Client, m: Message):
    # Check if command sender is Admin/Owner of the chat
    try:
        member = await client.get_chat_member(m.chat.id, m.from_user.id)
        if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER] and not await is_sudo(m.from_user.id):
            return await m.reply_text("❌ Sirf Group Admins hi kisi ko Auth User bana sakte hain.")
    except Exception:
        return

    user = m.reply_to_message.from_user if m.reply_to_message else None
    if not user and len(m.command) > 1:
        try:
            user = await client.get_users(m.command[1])
        except Exception:
            return await m.reply_text("❌ User find nahi ho paya.")
    if not user:
        return await m.reply_text("Kisi user ke message ko reply karein ya username/id dein.")

    await auth_db.update_one({"chat_id": m.chat.id, "user_id": user.id}, {"$set": {"user_id": user.id, "name": user.first_name}}, upsert=True)
    await m.reply_text(f"✅ {user.mention} ko **Auth List** me add kar diya gaya hai. Ab wo bina admin rights ke bhi music manage kar sakta hai.")

@bot.on_message(filters.command("unauth") & ~filters.private)
async def unauth_cmd(client: Client, m: Message):
    try:
        member = await client.get_chat_member(m.chat.id, m.from_user.id)
        if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER] and not await is_sudo(m.from_user.id):
            return await m.reply_text("❌ Sirf Group Admins hi user ko Unauth kar sakte hain.")
    except Exception:
        return

    user = m.reply_to_message.from_user if m.reply_to_message else None
    if not user and len(m.command) > 1:
        try:
            user = await client.get_users(m.command[1])
        except Exception:
            return await m.reply_text("❌ User find nahi ho paya.")
    if not user:
        return await m.reply_text("Reply karein ya username/id mention karein.")

    await auth_db.delete_one({"chat_id": m.chat.id, "user_id": user.id})
    await m.reply_text(f"❌ {user.mention} ko Auth List se remove kar diya gaya.")

@bot.on_message(filters.command("authusers") & ~filters.private)
async def authusers_cmd(_, m: Message):
    users = auth_db.find({"chat_id": m.chat.id})
    msg = f"**👥 Auth Users in {m.chat.title}:**\n\n"
    count = 0
    async for u in users:
        count += 1
        msg += f"**{count}.** `{u.get('name', 'User')}` [`{u['user_id']}`]\n"
    if count == 0:
        return await m.reply_text("Is group me koi Auth User add nahi hai.")
    await m.reply_text(msg)

# --- PLAYBACK CONTROLS ---
@bot.on_message(filters.command(["pause", "cpause"]) & ~filters.private)
async def pause_handler(client: Client, m: Message):
    if not await is_admin_or_auth(client, m.chat.id, m.from_user.id):
        return await m.reply_text("❌ Permission Denied (Admins/Auth only).")
    try:
        await call_py.pause_stream(m.chat.id)
        await m.reply_text("⏸ **Stream paused.**")
    except Exception as e:
        await m.reply_text(f"❌ Error: `{e}`")

@bot.on_message(filters.command(["resume", "cresume"]) & ~filters.private)
async def resume_handler(client: Client, m: Message):
    if not await is_admin_or_auth(client, m.chat.id, m.from_user.id):
        return await m.reply_text("❌ Permission Denied (Admins/Auth only).")
    try:
        await call_py.resume_stream(m.chat.id)
        await m.reply_text("▶️ **Stream resumed.**")
    except Exception as e:
        await m.reply_text(f"❌ Error: `{e}`")

@bot.on_message(filters.command(["skip", "cskip", "next"]) & ~filters.private)
async def skip_handler(client: Client, m: Message):
    if not await is_admin_or_auth(client, m.chat.id, m.from_user.id):
        return await m.reply_text("❌ Permission Denied (Admins/Auth only).")
    if m.chat.id in QUEUE and QUEUE[m.chat.id]:
        await m.reply_text("⏭ **Skipping to next track...**")
        await play_next(m.chat.id)
    else:
        await m.reply_text("❌ Queue empty hai.")

@bot.on_message(filters.command(["stop", "end", "cstop", "cend"]) & ~filters.private)
async def stop_handler(client: Client, m: Message):
    if not await is_admin_or_auth(client, m.chat.id, m.from_user.id):
        return await m.reply_text("❌ Permission Denied (Admins/Auth only).")
    if m.chat.id in QUEUE:
        for t in QUEUE[m.chat.id]:
            clean_file(t["file"])
        QUEUE[m.chat.id].clear()
    LOOP[m.chat.id] = 0
    try:
        await call_py.leave_call(m.chat.id)
        await m.reply_text("⏹ **Stream stopped & queue cleared.**")
    except Exception as e:
        await m.reply_text(f"❌ Error: `{e}`")

@bot.on_message(filters.command(["queue", "cqueue"]) & ~filters.private)
async def queue_handler(_, m: Message):
    if m.chat.id not in QUEUE or not QUEUE[m.chat.id]:
        return await m.reply_text("📭 **Queue empty hai.**")
    msg = "**📜 Current Group Queue:**\n\n"
    for i, t in enumerate(QUEUE[m.chat.id]):
        msg += f"**{i+1}.** `{t['title']}` | By: {t['req_by']}\n"
    await m.reply_text(msg)

@bot.on_message(filters.command(["shuffle", "cshuffle"]) & ~filters.private)
async def shuffle_handler(client: Client, m: Message):
    if not await is_admin_or_auth(client, m.chat.id, m.from_user.id):
        return await m.reply_text("❌ Permission Denied.")
    if m.chat.id in QUEUE and len(QUEUE[m.chat.id]) > 1:
        first = QUEUE[m.chat.id][0]
        rest = QUEUE[m.chat.id][1:]
        random.shuffle(rest)
        QUEUE[m.chat.id] = [first] + rest
        await m.reply_text("🔀 **Queue shuffled.**")
    else:
        await m.reply_text("❌ Kam se kam 2 queued songs chahiye shuffle ke liye.")

@bot.on_message(filters.command(["loop", "cloop"]) & ~filters.private)
async def loop_handler(client: Client, m: Message):
    if not await is_admin_or_auth(client, m.chat.id, m.from_user.id):
        return await m.reply_text("❌ Permission Denied.")
    if len(m.command) < 2:
        return await m.reply_text("Usage: `/loop [1-10/disable]`")
    val = m.command[1].lower()
    if val in ["disable", "off", "0"]:
        LOOP[m.chat.id] = 0
        await m.reply_text("🔁 **Loop disabled.**")
    elif val.isdigit() and 1 <= int(val) <= 10:
        LOOP[m.chat.id] = int(val)
        await m.reply_text(f"🔁 **Loop set to {val} repeats.**")
    else:
        await m.reply_text("Invalid value. 1-10 choose karein ya 'disable'.")

# --- SONG DOWNLOAD ---
@bot.on_message(filters.command("song"))
async def song_downloader(_, m: Message):
    if len(m.command) < 2:
        return await m.reply_text("Usage: `/song [title/link]`")
    query = m.text.split(None, 1)[1]
    status = await m.reply_text("🔎 **Searching & Downloading audio...**")
    try:
        data = await asyncio.get_event_loop().run_in_executor(None, download_stream, query, False)
        await m.reply_audio(audio=data["file"], title=data["title"], performer="RomeoMusicBot")
        await status.delete()
        clean_file(data["file"])
    except Exception as e:
        await status.edit(f"❌ Download failed: `{e}`")

# --- CHANNEL PLAY ---
@bot.on_message(filters.command("channelplay") & ~filters.private)
async def channelplay_cmd(client: Client, m: Message):
    if not await is_admin_or_auth(client, m.chat.id, m.from_user.id):
        return await m.reply_text("❌ Permission Denied.")
    if len(m.command) < 2:
        return await m.reply_text("Usage: `/channelplay [Channel ID/Username]` or `/channelplay disable`")
    if m.command[1].lower() == "disable":
        await channel_db.delete_one({"chat_id": m.chat.id})
        return await m.reply_text("✅ Channel unlinked.")
    try:
        channel = await client.get_chat(m.command[1])
        await channel_db.update_one({"chat_id": m.chat.id}, {"$set": {"channel_id": channel.id}}, upsert=True)
        await m.reply_text(f"✅ Group connected to channel: `{channel.title}`")
    except Exception as e:
        await m.reply_text(f"❌ Channel link error: `{e}`")

# --- SUDO & SYSTEM ---
@bot.on_message(filters.command("gban") & filters.user(OWNER_ID))
async def gban_cmd(client: Client, m: Message):
    user = m.reply_to_message.from_user if m.reply_to_message else None
    if not user and len(m.command) > 1:
        user = await client.get_users(m.command[1])
    if not user:
        return await m.reply_text("Reply to user or provide username.")
    await bl_user_db.update_one({"user_id": user.id}, {"$set": {"user_id": user.id}}, upsert=True)
    await m.reply_text(f"🚫 Globally banned `{user.id}`.")

@bot.on_message(filters.command("ungban") & filters.user(OWNER_ID))
async def ungban_cmd(client: Client, m: Message):
    user = m.reply_to_message.from_user if m.reply_to_message else None
    if not user and len(m.command) > 1:
        user = await client.get_users(m.command[1])
    if not user:
        return await m.reply_text("Reply to user or provide username.")
    await bl_user_db.delete_one({"user_id": user.id})
    await m.reply_text(f"✅ Globally unbanned `{user.id}`.")

@bot.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_cmd(client: Client, m: Message):
    if len(m.command) < 2 and not m.reply_to_message:
        return await m.reply_text("Usage: `/broadcast [message]` or reply.")
    text = m.text.split(None, 1)[1] if len(m.command) > 1 else None
    sent = 0
    async for dialog in userbot.get_dialogs():
        if dialog.chat.type in [dialog.chat.type.GROUP, dialog.chat.type.SUPERGROUP]:
            try:
                if m.reply_to_message:
                    await m.reply_to_message.forward(dialog.chat.id)
                else:
                    await client.send_message(dialog.chat.id, text)
                sent += 1
                await asyncio.sleep(0.2)
            except Exception:
                pass
    await m.reply_text(f"📢 Broadcast sent to `{sent}` groups.")

@bot.on_message(filters.command("ping"))
async def ping_cmd(_, m: Message):
    start = time.time()
    msg = await m.reply_text("🏓 Pinging...")
    delta = (time.time() - start) * 1000
    uptime = int(time.time() - BOT_START_TIME)
    await msg.edit(f"🏓 **Pong!** `{delta:.2f} ms`\n⏱ **Uptime:** `{uptime}` sec")

# ==================== RUNNER ====================
async def main():
    await bot.start()
    await userbot.start()
    await call_py.start()
    print("------------------------------------------")
    print(" Romeo Music Bot (Multi-Group Mode) Ready ")
    print("------------------------------------------")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
