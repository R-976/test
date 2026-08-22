import os
import re
import sys
import time
import shutil
import random
import asyncio
from typing import Union, List
from pyrogram import Client, filters, idle
from pyrogram.types import (
    Message, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    CallbackQuery
)
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import UserAlreadyParticipant, UserNotParticipant, MessageNotModified
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped
from pytgcalls.types.input_stream.quality import HighQualityAudio, HighQualityVideo
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

# ==================== CLIENTS & DB INIT ====================
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
served_chats_db = db.served_chats

# Spotify Setup
sp = None
if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
    try:
        sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
            client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET
        ))
    except Exception:
        pass

QUEUE = {}          # {chat_id: [{"title": str, "file": str, "is_video": bool, "duration": int, "req_by": str, "stream_url": str}]}
LOOP = {}           # {chat_id: int}
SPEED = {}          # {chat_id: float}
MAINTENANCE = False
BOT_START_TIME = time.time()

# ==================== PERMISSIONS & HELPERS ====================
async def is_sudo(user_id: int) -> bool:
    if user_id == OWNER_ID:
        return True
    return bool(await sudo_db.find_one({"user_id": user_id}))

async def is_admin_or_auth(client: Client, chat_id: int, user_id: int) -> bool:
    if await is_sudo(user_id):
        return True
    if await auth_db.find_one({"chat_id": chat_id, "user_id": user_id}):
        return True
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

async def add_served_chat(chat_id: int):
    await served_chats_db.update_one({"chat_id": chat_id}, {"$set": {"chat_id": chat_id}}, upsert=True)

def clean_file(file_path: str):
    if file_path and os.path.exists(file_path) and DOWNLOAD_DIR in file_path:
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
            "duration": int(info.get("duration", 0)),
            "is_video": is_video,
            "stream_url": info.get("webpage_url", query)
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

def player_panel(chat_id: int):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⏸ Pause", callback_data=f"panel_pause_{chat_id}"),
            InlineKeyboardButton("▶️ Resume", callback_data=f"panel_resume_{chat_id}"),
            InlineKeyboardButton("⏭ Skip", callback_data=f"panel_skip_{chat_id}")
        ],
        [
            InlineKeyboardButton("⏹ Stop", callback_data=f"panel_stop_{chat_id}"),
            InlineKeyboardButton("🔁 Loop", callback_data=f"panel_loop_{chat_id}"),
            InlineKeyboardButton("📜 Queue", callback_data=f"panel_queue_{chat_id}")
        ]
    ])

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
                    await call_py.leave_group_call(chat_id)
                except Exception:
                    pass
                return
            track = QUEUE[chat_id][0]

        stream = AudioVideoPiped(track["file"], HighQualityAudio(), HighQualityVideo()) if track["is_video"] else AudioPiped(track["file"], HighQualityAudio())
        try:
            await call_py.change_stream(chat_id, stream)
            await bot.send_message(
                chat_id,
                f"▶️ **Streaming Now:** [{track['title']}]({track.get('stream_url', '')})\n"
                f"**Type:** `{'Video' if track['is_video'] else 'Audio'}` | **Requested By:** {track['req_by']}",
                reply_markup=player_panel(chat_id),
                disable_web_page_preview=True
            )
        except Exception:
            try:
                await call_py.join_group_call(chat_id, stream)
            except Exception as e:
                await bot.send_message(chat_id, f"❌ Error streaming next track: `{e}`")
                await play_next(chat_id)
    else:
        try:
            await call_py.leave_group_call(chat_id)
        except Exception:
            pass

@call_py.on_stream_end()
async def on_stream_end_handler(_, update):
    await play_next(update.chat_id)

# ==================== HELP DICTIONARY ====================
HELP_DATA = {
    "1": """<b><u>ᴀᴅᴍɪɴ ᴄᴏᴍᴍᴀɴᴅs :</b></u>\n\n/pause : ᴩᴀᴜsᴇ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ ᴩʟᴀʏɪɴɢ sᴛʀᴇᴀᴍ.\n/resume : ʀᴇsᴜᴍᴇ ᴛʜᴇ ᴩᴀᴜsᴇᴅ sᴛʀᴇᴀᴍ.\n/skip : sᴋɪᴩ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ ᴩʟᴀʏɪɴɢ sᴛʀᴇᴀᴍ.\n/stop or /end : ᴄʟᴇᴀʀs ᴛʜᴇ ǫᴜᴇᴜᴇ ᴀɴᴅ ᴇɴᴅs sᴛʀᴇᴀᴍ.\n/player : ɢᴇᴛ ɪɴᴛᴇʀᴀᴄᴛɪᴠᴇ ᴩʟᴀʏᴇʀ ᴩᴀɴᴇʟ.\n/queue : sʜᴏᴡs ǫᴜᴇᴜᴇᴅ ᴛʀᴀᴄᴋs.""",
    "2": """<b><u>ᴀᴜᴛʜ ᴜsᴇʀs :</b></u>\n\n/auth [username/id] : ᴀᴅᴅ ᴀ ᴜsᴇʀ ᴛᴏ ᴀᴜᴛʜ ʟɪsᴛ.\n/unauth [username/id] : ʀᴇᴍᴏᴠᴇ ᴀᴜᴛʜ ᴜsᴇʀ.\n/authusers : sʜᴏᴡs ᴀᴜᴛʜ ᴜsᴇʀs ʟɪsᴛ.""",
    "3": """<u><b>ʙʀᴏᴀᴅᴄᴀsᴛ ғᴇᴀᴛᴜʀᴇ</b></u> [SUDO ONLY] :\n\n/broadcast [msg] : ʙʀᴏᴀᴅᴄᴀsᴛ ᴛᴏ sᴇʀᴠᴇᴅ ᴄʜᴀᴛs.\n-pin : ᴩɪɴs ʙʀᴏᴀᴅᴄᴀsᴛ ᴍᴇssᴀɢᴇ.\n-user : ʙʀᴏᴀᴅᴄᴀsᴛs ᴛᴏ ʙᴏᴛ ᴜsᴇʀs.""",
    "4": """<u><b>ᴄʜᴀᴛ ʙʟᴀᴄᴋʟɪsᴛ :</b></u> [SUDO ONLY]\n\n/blacklistchat [ID] : ʙʟᴀᴄᴋʟɪsᴛ ᴀ ᴄʜᴀᴛ.\n/whitelistchat [ID] : ᴡʜɪᴛᴇʟɪsᴛ ᴄʜᴀᴛ.\n/blacklistedchat : sʜᴏᴡs ʙʟᴀᴄᴋʟɪsᴛ ʟɪsᴛ.""",
    "5": """<u><b>ʙʟᴏᴄᴋ ᴜsᴇʀs:</b></u> [SUDO ONLY]\n\n/block [username/id] : ʙʟᴏᴄᴋ ᴜsᴇʀ ғʀᴏᴍ ʙᴏᴛ.\n/unblock [username/id] : ᴜɴʙʟᴏᴄᴋs ᴜsᴇʀ.\n/blockedusers : sʜᴏᴡs ʙʟᴏᴄᴋᴇᴅ ᴜsᴇʀs.""",
    "6": """<u><b>ᴄʜᴀɴɴᴇʟ ᴩʟᴀʏ :</b></u>\n\n/cplay : sᴛʀᴇᴀᴍ ᴀᴜᴅɪᴏ ɪɴ ᴄʜᴀɴɴᴇʟ ᴠᴄ.\n/cvplay : sᴛʀᴇᴀᴍ ᴠɪᴅᴇᴏ ɪɴ ᴄʜᴀɴɴᴇʟ ᴠᴄ.\n/channelplay [ID/disable] : ʟɪɴᴋ ᴄʜᴀɴɴᴇʟ.""",
    "7": """<u><b>ɢʟᴏʙᴀʟ ʙᴀɴ :</b></u> [SUDO ONLY]\n\n/gban [user] : ɢʟᴏʙᴀʟ ʙᴀɴ ᴜsᴇʀ.\n/ungban [user] : ᴜɴɢʙᴀɴ ᴜsᴇʀ.\n/gbannedusers : sʜᴏᴡs ɢʙᴀɴɴᴇᴅ ᴜsᴇʀs.""",
    "8": """<b><u>ʟᴏᴏᴘ sᴛʀᴇᴀᴍ :</b></u>\n\n/loop [1-10/disable] : ᴇɴᴀʙʟᴇs/ᴅɪsᴀʙʟᴇs ʟᴏᴏᴘ.""",
    "9": """<u><b>ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ ᴍᴏᴅᴇ</b></u> [SUDO ONLY] :\n\n/maintenance [enable/disable] : ᴛᴏɢɢʟᴇ ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ ᴍᴏᴅᴇ.""",
    "10": """<b><u>ᴘɪɴɢ & sᴛᴀᴛs :</b></u>\n\n/start : sᴛᴀʀᴛs ʙᴏᴛ.\n/help : ɢᴇᴛ ʜᴇʟᴩ ᴍᴇɴᴜ.\n/ping : sʜᴏᴡs ᴩɪɴɢ & ᴜᴩᴛɪᴍᴇ.\n/stats : sʜᴏᴡs sᴛᴀᴛs.""",
    "11": """<u><b>ᴩʟᴀʏ ᴄᴏᴍᴍᴀɴᴅs :</b></u>\n\n/play or /vplay : sᴛʀᴇᴀᴍ ᴀᴜᴅɪᴏ/ᴠɪᴅᴇᴏ ɪɴ ᴠᴄ.\n/playforce or /vplayforce : ғᴏʀᴄᴇ sᴛʀᴇᴀᴍ.""",
    "12": """<b><u>sʜᴜғғʟᴇ ǫᴜᴇᴜᴇ :</b></u>\n\n/shuffle : sʜᴜғғʟᴇs ǫᴜᴇᴜᴇ.\n/queue : sʜᴏᴡs ǫᴜᴇᴜᴇ.""",
    "13": """<b><u>sᴇᴇᴋ sᴛʀᴇᴀᴍ :</b></u>\n\n/seek [seconds] : sᴇᴇᴋ ғᴏʀᴡᴀʀᴅ.\n/seekback [seconds] : sᴇᴇᴋ ʙᴀᴄᴋᴡᴀʀᴅ.""",
    "14": """<b><u>sᴏɴɢ ᴅᴏᴡɴʟᴏᴀᴅ</b></u>\n\n/song [name/url] : ᴅᴏᴡɴʟᴏᴀᴅ ᴀᴜᴅɪᴏ ᴛʀᴀᴄᴋ.""",
    "15": """<b><u>sᴘᴇᴇᴅ ᴄᴏᴍᴍᴀɴᴅs :</b></u>\n\n/speed or /playback [0.5-2.0] : ᴀᴅᴊᴜsᴛ sᴩᴇᴇᴅ."""
}

def help_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Admin", callback_data="h_1"), InlineKeyboardButton("Auth", callback_data="h_2"), InlineKeyboardButton("Broadcast", callback_data="h_3")],
        [InlineKeyboardButton("Blacklist", callback_data="h_4"), InlineKeyboardButton("Block", callback_data="h_5"), InlineKeyboardButton("Channel", callback_data="h_6")],
        [InlineKeyboardButton("GBan", callback_data="h_7"), InlineKeyboardButton("Loop", callback_data="h_8"), InlineKeyboardButton("Maintenance", callback_data="h_9")],
        [InlineKeyboardButton("Ping", callback_data="h_10"), InlineKeyboardButton("Play", callback_data="h_11"), InlineKeyboardButton("Shuffle", callback_data="h_12")],
        [InlineKeyboardButton("Seek", callback_data="h_13"), InlineKeyboardButton("Song", callback_data="h_14"), InlineKeyboardButton("Speed", callback_data="h_15")],
        [InlineKeyboardButton("🔙 Close", callback_data="h_close")]
    ])

# ==================== MAIN HANDLERS ====================

@bot.on_message(filters.command("start"))
async def start_handler(_, m: Message):
    if await is_banned(m.from_user.id):
        return
    if m.chat.type != m.chat.type.PRIVATE:
        await add_served_chat(m.chat.id)
        return await m.reply_text("✨ **Romeo Music Bot is online!**")
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Romeo To Group", url=f"https://t.me/{(await bot.get_me()).username}?startgroup=true")],
        [InlineKeyboardButton("📚 Help Commands", callback_data="h_main")]
    ])
    await m.reply_text("👋 **Welcome to Romeo Music Bot!**\nHigh-Quality VC Music & Video Streamer.", reply_markup=keyboard)

@bot.on_message(filters.command("help"))
async def help_cmd_handler(_, m: Message):
    await m.reply_text("📖 **Click any button below to see command usage:**", reply_markup=help_buttons())

@bot.on_callback_query(filters.regex("^h_"))
async def help_callback_handler(_, query: CallbackQuery):
    page = query.data.split("_")[1]
    if page == "close":
        return await query.message.delete()
    if page == "main":
        return await query.message.edit("📖 **Click any button below to see command usage:**", reply_markup=help_buttons())
    
    text = HELP_DATA.get(page, "No information.")
    back_kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Help Menu", callback_data="h_main")]])
    try:
        await query.message.edit(text, reply_markup=back_kb)
    except MessageNotModified:
        pass

# --- PLAY LOGIC ---
@bot.on_message(filters.command(["play", "vplay", "cplay", "cvplay", "playforce", "vplayforce"]) & ~filters.private)
async def play_handler(client: Client, m: Message):
    await add_served_chat(m.chat.id)
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

    # Assistant Group Join
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
            "req_by": m.from_user.mention,
            "stream_url": ""
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
        stream = AudioVideoPiped(first["file"], HighQualityAudio(), HighQualityVideo()) if first["is_video"] else AudioPiped(first["file"], HighQualityAudio())
        try:
            await call_py.join_group_call(chat_id, stream)
            await status_msg.edit(
                f"▶️ **Started Streaming:** [{first['title']}]({first.get('stream_url', '')})\n"
                f"**Type:** `{'Video' if first['is_video'] else 'Audio'}` | **Requested By:** {first['req_by']}",
                reply_markup=player_panel(chat_id),
                disable_web_page_preview=True
            )
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

# --- PLAYER PANEL ---
@bot.on_message(filters.command(["player", "cplayer"]) & ~filters.private)
async def player_panel_cmd(client: Client, m: Message):
    if not await is_admin_or_auth(client, m.chat.id, m.from_user.id):
        return await m.reply_text("❌ Permission Denied.")
    if m.chat.id not in QUEUE or not QUEUE[m.chat.id]:
        return await m.reply_text("📭 Nothing is playing right now.")
    curr = QUEUE[m.chat.id][0]
    await m.reply_text(
        f"🎧 **Interactive Music Panel**\n\n"
        f"🎵 **Track:** `{curr['title']}`\n"
        f"👤 **Requested By:** {curr['req_by']}",
        reply_markup=player_panel(m.chat.id)
    )

@bot.on_callback_query(filters.regex("^panel_"))
async def player_panel_buttons(client: Client, query: CallbackQuery):
    action, chat_id = query.data.split("_")[1], int(query.data.split("_")[2])
    if not await is_admin_or_auth(client, chat_id, query.from_user.id):
        return await query.answer("❌ Permission Denied!", show_alert=True)
    
    if action == "pause":
        try:
            await call_py.pause_stream(chat_id)
            await query.answer("⏸ Stream Paused!")
        except Exception as e:
            await query.answer(f"Error: {e}", show_alert=True)
    elif action == "resume":
        try:
            await call_py.resume_stream(chat_id)
            await query.answer("▶️ Stream Resumed!")
        except Exception as e:
            await query.answer(f"Error: {e}", show_alert=True)
    elif action == "skip":
        await query.answer("⏭ Skipped!")
        await play_next(chat_id)
    elif action == "stop":
        if chat_id in QUEUE:
            for t in QUEUE[chat_id]:
                clean_file(t["file"])
            QUEUE[chat_id].clear()
        try:
            await call_py.leave_group_call(chat_id)
        except Exception:
            pass
        await query.answer("⏹ Stream Stopped!")
    elif action == "loop":
        LOOP[chat_id] = 3 if LOOP.get(chat_id, 0) == 0 else 0
        await query.answer(f"🔁 Loop set to {LOOP[chat_id]} repeats!")
    elif action == "queue":
        if chat_id not in QUEUE or not QUEUE[chat_id]:
            return await query.answer("Queue is empty!", show_alert=True)
        msg = "\n".join([f"{i+1}. {t['title'][:30]}" for i, t in enumerate(QUEUE[chat_id])])
        await query.answer(f"Queue:\n{msg}", show_alert=True)

# --- CONTROLS ---
@bot.on_message(filters.command(["pause", "cpause"]) & ~filters.private)
async def pause_handler(client: Client, m: Message):
    if not await is_admin_or_auth(client, m.chat.id, m.from_user.id):
        return await m.reply_text("❌ Permission Denied.")
    try:
        await call_py.pause_stream(m.chat.id)
        await m.reply_text("⏸ **Stream paused.**")
    except Exception as e:
        await m.reply_text(f"❌ Error: `{e}`")

@bot.on_message(filters.command(["resume", "cresume"]) & ~filters.private)
async def resume_handler(client: Client, m: Message):
    if not await is_admin_or_auth(client, m.chat.id, m.from_user.id):
        return await m.reply_text("❌ Permission Denied.")
    try:
        await call_py.resume_stream(m.chat.id)
        await m.reply_text("▶️ **Stream resumed.**")
    except Exception as e:
        await m.reply_text(f"❌ Error: `{e}`")

@bot.on_message(filters.command(["skip", "cskip", "next"]) & ~filters.private)
async def skip_handler(client: Client, m: Message):
    if not await is_admin_or_auth(client, m.chat.id, m.from_user.id):
        return await m.reply_text("❌ Permission Denied.")
    if m.chat.id in QUEUE and QUEUE[m.chat.id]:
        await m.reply_text("⏭ **Skipping to next track...**")
        await play_next(m.chat.id)
    else:
        await m.reply_text("❌ Queue empty hai.")

@bot.on_message(filters.command(["stop", "end", "cstop", "cend"]) & ~filters.private)
async def stop_handler(client: Client, m: Message):
    if not await is_admin_or_auth(client, m.chat.id, m.from_user.id):
        return await m.reply_text("❌ Permission Denied.")
    if m.chat.id in QUEUE:
        for t in QUEUE[m.chat.id]:
            clean_file(t["file"])
        QUEUE[m.chat.id].clear()
    LOOP[m.chat.id] = 0
    try:
        await call_py.leave_group_call(m.chat.id)
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

# --- AUTH SYSTEM ---
@bot.on_message(filters.command("auth") & ~filters.private)
async def auth_cmd(client: Client, m: Message):
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
        return await m.reply_text("Reply karein ya username/id provide karein.")

    await auth_db.update_one({"chat_id": m.chat.id, "user_id": user.id}, {"$set": {"user_id": user.id, "name": user.first_name}}, upsert=True)
    await m.reply_text(f"✅ {user.mention} ko **Auth List** me add kar diya gaya hai.")

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
        return await m.reply_text("Reply karein ya username/id provide karein.")

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

# --- SUDO & SYSTEM COMMANDS ---
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

@bot.on_message(filters.command("gbannedusers") & filters.user(OWNER_ID))
async def gbanned_list(_, m: Message):
    users = bl_user_db.find()
    msg = "**🚫 Globally Banned Users:**\n\n"
    async for u in users:
        msg += f"• `{u['user_id']}`\n"
    await m.reply_text(msg)

@bot.on_message(filters.command("block") & filters.user(OWNER_ID))
async def block_user_cmd(client: Client, m: Message):
    user = m.reply_to_message.from_user if m.reply_to_message else None
    if not user and len(m.command) > 1:
        user = await client.get_users(m.command[1])
    if not user:
        return await m.reply_text("Reply to user or provide ID.")
    await bl_user_db.update_one({"user_id": user.id}, {"$set": {"user_id": user.id}}, upsert=True)
    await m.reply_text(f"⛔ User `{user.id}` blocked.")

@bot.on_message(filters.command("unblock") & filters.user(OWNER_ID))
async def unblock_user_cmd(client: Client, m: Message):
    user = m.reply_to_message.from_user if m.reply_to_message else None
    if not user and len(m.command) > 1:
        user = await client.get_users(m.command[1])
    if not user:
        return await m.reply_text("Reply to user or provide ID.")
    await bl_user_db.delete_one({"user_id": user.id})
    await m.reply_text(f"✅ User `{user.id}` unblocked.")

@bot.on_message(filters.command("blacklistchat") & filters.user(OWNER_ID))
async def bl_chat_cmd(_, m: Message):
    if len(m.command) < 2:
        return await m.reply_text("Usage: `/blacklistchat [Chat ID]`")
    c_id = int(m.command[1])
    await bl_chat_db.update_one({"chat_id": c_id}, {"$set": {"chat_id": c_id}}, upsert=True)
    await m.reply_text(f"⛔ Chat `{c_id}` blacklisted.")

@bot.on_message(filters.command("whitelistchat") & filters.user(OWNER_ID))
async def wl_chat_cmd(_, m: Message):
    if len(m.command) < 2:
        return await m.reply_text("Usage: `/whitelistchat [Chat ID]`")
    c_id = int(m.command[1])
    await bl_chat_db.delete_one({"chat_id": c_id})
    await m.reply_text(f"✅ Chat `{c_id}` whitelisted.")

@bot.on_message(filters.command("broadcast") & filters.user(OWNER_ID))
async def broadcast_cmd(client: Client, m: Message):
    if len(m.command) < 2 and not m.reply_to_message:
        return await m.reply_text("Usage: `/broadcast [-pin] [-user] [message]`")
    
    is_pin = "-pin" in m.text
    is_user = "-user" in m.text
    
    clean_text = m.text.replace("-pin", "").replace("-user", "").split(None, 1)
    text = clean_text[1] if len(clean_text) > 1 else ""
    
    sent = 0
    chats = served_chats_db.find() if not is_user else bl_user_db.find()
    async for c in chats:
        c_id = c.get("chat_id") or c.get("user_id")
        try:
            if m.reply_to_message:
                msg = await m.reply_to_message.forward(c_id)
            else:
                msg = await client.send_message(c_id, text)
            if is_pin:
                await msg.pin(disable_notification=False)
            sent += 1
            await asyncio.sleep(0.2)
        except Exception:
            pass
    await m.reply_text(f"📢 Broadcast completed to `{sent}` targets.")

@bot.on_message(filters.command("maintenance") & filters.user(OWNER_ID))
async def maintenance_switch(_, m: Message):
    global MAINTENANCE
    if len(m.command) < 2:
        return await m.reply_text("Usage: `/maintenance enable` ya `/maintenance disable`")
    action = m.command[1].lower()
    if action == "enable":
        MAINTENANCE = True
        await m.reply_text("⚙️ **Maintenance mode enabled.**")
    elif action == "disable":
        MAINTENANCE = False
        await m.reply_text("✅ **Maintenance mode disabled.**")

@bot.on_message(filters.command("ping"))
async def ping_cmd(_, m: Message):
    start = time.time()
    msg = await m.reply_text("🏓 Pinging...")
    delta = (time.time() - start) * 1000
    uptime = int(time.time() - BOT_START_TIME)
    await msg.edit(f"🏓 **Pong!** `{delta:.2f} ms`\n⏱ **Uptime:** `{uptime}` sec")

@bot.on_message(filters.command("stats"))
async def stats_cmd(_, m: Message):
    served_c = await served_chats_db.count_documents({})
    blocked_u = await bl_user_db.count_documents({})
    await m.reply_text(
        f"📊 **Romeo Music Bot Stats:**\n\n"
        f"• **Active Chats in Memory:** `{len(QUEUE)}`\n"
        f"• **Total Served Chats:** `{served_c}`\n"
        f"• **Blocked Users:** `{blocked_u}`\n"
        f"• **Maintenance:** `{'Enabled' if MAINTENANCE else 'Disabled'}`"
    )

# ==================== RUNNER ====================
async def start_bot():
    await bot.start()
    await userbot.start()
    await call_py.start()
    me = await bot.get_me()
    return me.username

async def stop_bot():
    await bot.stop()
    await userbot.stop()
    await call_py.stop()
    me = await bot.get_me()
    return me.username

if __name__ == "__main__":
    async def run_standalone():
        await start_bot()
        print("------------------------------------------")
        print(" Romeo Music Bot (Production Ready) Online")
        print("------------------------------------------")
        await idle()
        await stop_bot()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_standalone())
