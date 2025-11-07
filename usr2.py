import logging
import asyncio
from os import getenv
from asyncio import create_task, sleep, Lock
from pyrogram import Client, filters, idle
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import AudioPiped, AudioVideoPiped
from pytgcalls.types.input_stream.quality import HighQualityAudio, HighQualityVideo
from pytgcalls.exceptions import NoActiveGroupCall
import traceback

API_ID = int(getenv("API_ID", "10796618"))
API_HASH = getenv("API_HASH", "4e4b20b4e1e40c90fcb1a7658c800150")
STRING_SESSION = getenv("STRING_SESSION", "BQEiZi4AAANrPUa2j8zWuh_6NYpESzWOkGOuxv3io0xUzrvHmrBvC4-QtvwS3zvvdztdkdwbviqXpsQO2WbbskEYV6ype-ee4wfitd0y0CGccOI0ncngKzyKaotCzgjz0O8kiuR7QhDuDzQZBWtitvhVleejrX7VLUMHk4C9dxkcHQ9G2yLs2kT8oGsqqGb3udrkvKWzt3EYCkRZx1IVEcGu3bl8L53bpT8qDMfp2PTuzu2AW3XNK_P45bYGGKPfy7FWOxVQ2Mf7UpHtQJJACDWtq-3BKf5D-rUPXWl6PpSOB6tLF-ekcNWmBbW4DA5z5U1Q92UGGfy852ZDsJjDZrpW1HvzWQAAAAHuDjlWAA")
STRING_SESSION2 = getenv("STRING_SESSION2", "")

clients = []

if STRING_SESSION:
   client = Client("Userbot", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION, in_memory=True)
   clients.append(client)
   call_py1 = PyTgCalls(client)
else:
    client = None
    call_py1 = None
   
if STRING_SESSION2:
   client2 = Client("Userbot2", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION2, in_memory=True)
   clients.append(client2)
   call_py2 = PyTgCalls(client2)
else:
    client2 = None
    call_py2 = None

# --- Universal Settings ---
LOOP_AUTO_END_TIME = 3 * 60 * 60  # 3 hours in seconds
AUTO_VOLUME = 350  # Automatic volume set to 350% (between 300-400%)
CACHE_SIZE = 50   # Message cache size

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Assistant Clients ---
active_calls = [call_py1, call_py2]

# --- Globals ---
LOOP_MODE = {}
LOOP_TASKS = {}
ACTIVE_ASSISTANTS = {}
QUEUE = {}
QUEUE_LOCK = Lock()
MSG_CACHE = {}

# --- Helper Function for Auto Volume ---
async def set_auto_volume(call, chat_id):
    """Automatically set volume to 350% if possible, otherwise keep default 100%"""
    try:
        await call.change_volume_call(chat_id, AUTO_VOLUME)
        logger.info(f"✅ Volume set to {AUTO_VOLUME}% in {chat_id}")
        return AUTO_VOLUME
    except Exception as e:
        logger.warning(f"⚠️ Could not set volume to {AUTO_VOLUME}%, using default 100%: {e}")
        return 100

# --- Core Functions ---
async def add_to_queue(chat_id, songname, msg_id, source_chat_id, type):
    async with QUEUE_LOCK:
        item = [songname, msg_id, source_chat_id, type, 0]
        if chat_id in QUEUE:
            QUEUE[chat_id].append(item)
            return len(QUEUE[chat_id]) - 1
        else:
            QUEUE[chat_id] = [item]
            return 0

def get_queue(chat_id):
    return QUEUE.get(chat_id, [])

async def pop_an_item(chat_id):
    async with QUEUE_LOCK:
        if chat_id in QUEUE and QUEUE[chat_id]:
            QUEUE[chat_id].pop(0)
            return 1
        return 0

async def clear_queue(chat_id):
    async with QUEUE_LOCK:
        if chat_id in QUEUE:
            del QUEUE[chat_id]
            keys_to_remove = [k for k in MSG_CACHE.keys() if k[0] == chat_id]
            for key in keys_to_remove:
                del MSG_CACHE[key]
            return 1
        return 0

async def get_active_call(chat_id):
    call = ACTIVE_ASSISTANTS.get(chat_id)
    if call:
        return call
    for call in active_calls:
        try:
            if await call.is_connected(chat_id):
                ACTIVE_ASSISTANTS[chat_id] = call
                return call
        except:
            continue
    return None

async def get_msg_stream(client, source_chat_id, msg_id, is_video=False):
    cache_key = (source_chat_id, msg_id)
    if cache_key in MSG_CACHE:
        msg = MSG_CACHE[cache_key]
    else:
        try:
            msg = await client.get_messages(source_chat_id, msg_id)
            if not msg:
                raise Exception("Message not found")
            if len(MSG_CACHE) > CACHE_SIZE:
                for key in list(MSG_CACHE.keys())[:10]:
                    del MSG_CACHE[key]
            MSG_CACHE[cache_key] = msg
        except FloodWait as e:
            await sleep(e.x)
            return await get_msg_stream(client, source_chat_id, msg_id, is_video)
        except Exception as e:
            raise
    
    if is_video:
        return AudioVideoPiped(msg, HighQualityAudio(), HighQualityVideo())
    else:
        return AudioPiped(msg, HighQualityAudio())

async def auto_end_loop(chat_id, client):
    try:
        await sleep(LOOP_AUTO_END_TIME)
        call = await get_active_call(chat_id)
        if call:
            try:
                await call.leave_group_call(chat_id)
            except:
                pass
        await clear_queue(chat_id)
        LOOP_MODE.pop(chat_id, None)
        LOOP_TASKS.pop(chat_id, None)
        ACTIVE_ASSISTANTS.pop(chat_id, None)
        try:
            await client.send_message(chat_id, f"⏰ Auto-ended loop after {LOOP_AUTO_END_TIME//3600} hours.")
        except:
            pass
    except:
        pass

# --- Stream End Handler ---
async def stream_end_handler(client, update):
    chat_id = update.chat_id
    try:
        queue = get_queue(chat_id)
        if not queue:
            await client.leave_group_call(chat_id)
            await clear_queue(chat_id)
            LOOP_MODE.pop(chat_id, None)
            ACTIVE_ASSISTANTS.pop(chat_id, None)
            task = LOOP_TASKS.pop(chat_id, None)
            if task:
                task.cancel()
            return
        
        if not LOOP_MODE.get(chat_id):
            await pop_an_item(chat_id)
        
        new_queue = get_queue(chat_id)
        if not new_queue:
            await client.leave_group_call(chat_id)
            await clear_queue(chat_id)
            LOOP_MODE.pop(chat_id, None)
            ACTIVE_ASSISTANTS.pop(chat_id, None)
            task = LOOP_TASKS.pop(chat_id, None)
            if task:
                task.cancel()
            return
        
        name, msg_id, source_chat_id, type, _ = new_queue[0]
        try:
            stream = await get_msg_stream(client, source_chat_id, msg_id, type == "Video")
            await client.change_stream(chat_id, stream)
            
            # Auto-set volume after stream change
            await set_auto_volume(client, chat_id)
            
            status = f"🎶 Now playing: `{name}`"
            if LOOP_MODE.get(chat_id):
                status += " 🔁"
            if len(new_queue) > 1:
                status += f" | Queue: {len(new_queue)-1}"
            await client.send_message(chat_id, status)
        except Exception as e:
            logger.error(f"Stream change failed: {e}")
            await pop_an_item(chat_id)
            if get_queue(chat_id):
                await stream_end_handler(client, update)
            else:
                await client.leave_group_call(chat_id)
                await clear_queue(chat_id)
                ACTIVE_ASSISTANTS.pop(chat_id, None)
                LOOP_MODE.pop(chat_id, None)
    except Exception as e:
        logger.error(f"Stream end error: {traceback.format_exc()}")

# --- Register Handlers ---
for call in active_calls:
    if call is not None:
        @call.on_stream_end()
        async def _handler(client, update):
            await stream_end_handler(client, update)

# --- Main Commands ---
@Client.on_message(filters.command(["rvc", "rvcraid", "rv"], ["/", "!", "."]) & filters.group)
async def rvc_play(client: Client, message: Message):
    await message.delete()
    reply = message.reply_to_message
    args = message.text.split()
    
    if not reply or len(args) < 2:
        return await client.send_message(message.chat.id, "**Usage:** `/rvc <target_group>` reply to audio/video")
    
    try:
        chat = await client.get_chat(args[1])
        chat_id = chat.id
    except:
        return await client.send_message(message.chat.id, "❌ Invalid group")
    
    media = reply.audio or reply.video or reply.voice or reply.document
    if not media:
        return await client.send_message(message.chat.id, "❌ Reply must be audio/video")
    
    sent = await client.send_message(message.chat.id, "🎵 Starting stream...")
    
    songname = media.file_name or "Untitled"
    is_video = reply.video or (reply.document and reply.document.mime_type and reply.document.mime_type.startswith("video/"))
    
    try:
        stream = await get_msg_stream(client, reply.chat.id, reply.id, is_video)
    except Exception as e:
        return await sent.edit(f"❌ Stream failed: {str(e)}")
    
    queue = get_queue(chat_id)
    if queue:
        pos = await add_to_queue(chat_id, songname, reply.id, reply.chat.id, "Video" if is_video else "Audio")
        return await sent.edit(f"✅ Queued #{pos + 1} in {chat.title}\n🎵 `{songname}`")
    
    for call in active_calls:
        try:
            await call.join_group_call(chat_id, stream)
            
            # 🔊 Auto-set volume to 350% after joining
            volume_set = await set_auto_volume(call, chat_id)
            
            await add_to_queue(chat_id, songname, reply.id, reply.chat.id, "Video" if is_video else "Audio")
            ACTIVE_ASSISTANTS[chat_id] = call
            
            volume_info = f" [🔊 {volume_set}%]" if volume_set == AUTO_VOLUME else ""
            return await sent.edit(f"🚀 Started in {chat.title}{volume_info}\n🎶 `{songname}`")
            
        except NoActiveGroupCall:
            return await sent.edit(f"❌ No voice chat in {chat.title}")
        except FloodWait as e:
            await sleep(e.x)
            continue
        except:
            continue
    
    await sent.edit("❌ Failed to join")

@Client.on_message(filters.command(["end", "e", "stop"], ["/", "!", "."]) & filters.group)
async def end_raid(client: Client, message: Message):
    await message.delete()
    args = message.text.split()
    if len(args) < 2:
        return await client.send_message(message.chat.id, "**Usage:** `/end <target_group>`")
    
    try:
        chat = await client.get_chat(args[1])
        chat_id = chat.id
    except:
        return await client.send_message(message.chat.id, "❌ Invalid group")
    
    call = await get_active_call(chat_id)
    if call:
        try:
            await call.leave_group_call(chat_id)
        except:
            pass
    
    await clear_queue(chat_id)
    LOOP_MODE.pop(chat_id, None)
    ACTIVE_ASSISTANTS.pop(chat_id, None)
    task = LOOP_TASKS.pop(chat_id, None)
    if task:
        task.cancel()
    
    await client.send_message(message.chat.id, f"🛑 Ended in `{chat.title}`")

@Client.on_message(filters.command(["pause", "ps", "p"], ["/", "!", "."]) & filters.group)
async def pause_raid(client: Client, message: Message):
    await message.delete()
    args = message.text.split()
    if len(args) < 2:
        return await client.send_message(message.chat.id, "**Usage:** `/pause <target_group>`")
    
    try:
        chat = await client.get_chat(args[1])
        call = await get_active_call(chat.id)
        if not call:
            return await client.send_message(message.chat.id, f"❌ Not playing in `{chat.title}`")
        await call.pause_stream(chat.id)
        await client.send_message(message.chat.id, f"⏸️ Paused in `{chat.title}`")
    except Exception as e:
        await client.send_message(message.chat.id, f"❌ {e}")

@Client.on_message(filters.command(["resume", "rs", "r"], ["/", "!", "."]) & filters.group)
async def resume_raid(client: Client, message: Message):
    await message.delete()
    args = message.text.split()
    if len(args) < 2:
        return await client.send_message(message.chat.id, "**Usage:** `/resume <target_group>`")
    
    try:
        chat = await client.get_chat(args[1])
        call = await get_active_call(chat.id)
        if not call:
            return await client.send_message(message.chat.id, f"❌ Not playing in `{chat.title}`")
        await call.resume_stream(chat.id)
        
        # Re-apply volume after resume
        await set_auto_volume(call, chat.id)
        
        await client.send_message(message.chat.id, f"▶️ Resumed in `{chat.title}`")
    except Exception as e:
        await client.send_message(message.chat.id, f"❌ {e}")

@Client.on_message(filters.command(["skip", "skp", "sk", "sp"], ["/", "!", "."]) & filters.group)
async def skip_track(client: Client, message: Message):
    await message.delete()
    args = message.text.split()
    if len(args) < 2:
        return await client.send_message(message.chat.id, "**Usage:** `/skip <target_group>`")
    
    try:
        chat = await client.get_chat(args[1])
        chat_id = chat.id
    except:
        return await client.send_message(message.chat.id, "❌ Invalid group")
    
    call = await get_active_call(chat_id)
    if not call:
        return await client.send_message(message.chat.id, "❌ Not playing")
    
    queue = get_queue(chat_id)
    if not queue:
        return await client.send_message(message.chat.id, "❌ Empty queue")
    
    if LOOP_MODE.get(chat_id):
        name, msg_id, source_chat_id, type, _ = queue[0]
        try:
            stream = await get_msg_stream(client, source_chat_id, msg_id, type == "Video")
            await call.change_stream(chat_id, stream)
            
            # Auto-set volume after stream change
            await set_auto_volume(call, chat_id)
            
            return await client.send_message(message.chat.id, f"🔁 Replaying: `{name}`")
        except:
            pass
    
    if len(queue) <= 1:
        await call.leave_group_call(chat_id)
        await clear_queue(chat_id)
        ACTIVE_ASSISTANTS.pop(chat_id, None)
        return await client.send_message(message.chat.id, f"⏭️ Queue ended in `{chat.title}`")
    
    await pop_an_item(chat_id)
    new_queue = get_queue(chat_id)
    if new_queue:
        name, msg_id, source_chat_id, type, _ = new_queue[0]
        try:
            stream = await get_msg_stream(client, source_chat_id, msg_id, type == "Video")
            await call.change_stream(chat_id, stream)
            
            # Auto-set volume after stream change
            await set_auto_volume(call, chat_id)
            
            await client.send_message(message.chat.id, f"⏭️ Skipped\n▶️ Now: `{name}`")
        except Exception as e:
            await client.send_message(message.chat.id, f"❌ {e}")

@Client.on_message(filters.command(["loop", "lp", "l"], ["/", "!", "."]) & filters.group)
async def toggle_loop(client: Client, message: Message):
    await message.delete()
    args = message.text.split()
    if len(args) < 2:
        return await client.send_message(message.chat.id, "**Usage:** `/loop <target_group>`")
    
    try:
        chat = await client.get_chat(args[1])
        chat_id = chat.id
    except:
        return await client.send_message(message.chat.id, "❌ Invalid group")
    
    if LOOP_MODE.get(chat_id):
        LOOP_MODE.pop(chat_id, None)
        task = LOOP_TASKS.pop(chat_id, None)
        if task:
            task.cancel()
        return await client.send_message(message.chat.id, f"❌ Loop OFF in `{chat.title}`")
    
    LOOP_MODE[chat_id] = True
    task = create_task(auto_end_loop(chat_id, client))
    LOOP_TASKS[chat_id] = task
    await client.send_message(message.chat.id, f"🔁 Loop ON in `{chat.title}` (auto-off: {LOOP_AUTO_END_TIME//3600}h)")

async def start_bot():
    for cli in clients:
        try:
            await cli.start()
            ex = await cli.get_me()
            print(f"Started {ex.first_name} 🔥")
        except Exception as e:
            print(f"{e}")
            
#   START ASSISTANT ONLY FOR VCRAID
    if call_py1:
        await call_py1.start()
    if call_py2:
        await call_py2.start()
    
    await idle()

loop = asyncio.get_event_loop()
loop.run_until_complete(start_bot())
