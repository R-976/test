import os
import re
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message

# --- Configs ---
API_ID = 10796618                 # Apna API_ID daalein
API_HASH = "4e4b20b4e1e40c90fcb1a7658c800150"   # Apna API_HASH daalein
BOT_TOKEN = "5431733777:AAEdXWoT08HlQWlDfbVu5JMAfRgHXonbDxM" # Apna BOT_TOKEN daalein

app = Client("yt_command_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

YOUTUBE_REGEX = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'


def extract_video_id(url: str) -> str:
    match = re.search(YOUTUBE_REGEX, url)
    return match.group(1) if match else None


async def search_youtube(query: str):
    """Search YouTube via web scrape if name is provided"""
    url = f"https://www.youtube.com/results?search_query={aiohttp.helpers.quote(query)}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                return None
            html = await resp.text()
    video_ids = re.findall(r"\"videoId\":\"([a-zA-Z0-9_-]{11})\"", html)
    return video_ids[0] if video_ids else None


async def fetch_streams(video_id: str):
    """Innertube Android API request to get direct audio & video CDN URLs"""
    endpoint = "https://www.youtube.com/youtubei/v1/player"
    payload = {
        "videoId": video_id,
        "context": {
            "client": {
                "clientName": "ANDROID",
                "clientVersion": "19.09.37",
                "androidSdkVersion": 30,
                "hl": "en",
                "gl": "US"
            }
        }
    }
    headers = {
        "User-Agent": "com.google.android.youtube/19.09.37 (Linux; U; Android 11) gzip",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(endpoint, json=payload, headers=headers) as resp:
            if resp.status != 200:
                return None, None, None
            data = await resp.json()

    title = data.get("videoDetails", {}).get("title", f"media_{video_id}")
    streaming_data = data.get("streamingData", {})
    formats = streaming_data.get("formats", [])
    adaptive_formats = streaming_data.get("adaptiveFormats", [])

    # 1. Progressive Video Stream (Audio + Video combined)
    video_streams = [f for f in formats if "url" in f and "video/mp4" in f.get("mimeType", "")]
    if not video_streams:
        video_streams = [f for f in formats if "url" in f]
    best_video = max(video_streams, key=lambda x: x.get("bitrate", 0))["url"] if video_streams else None

    # 2. Dedicated Audio Track Stream
    audio_streams = [f for f in adaptive_formats if "url" in f and "audio" in f.get("mimeType", "")]
    best_audio = max(audio_streams, key=lambda x: x.get("bitrate", 0))["url"] if audio_streams else best_video

    return best_video, best_audio, title


async def download_file(stream_url: str, output_path: str):
    """Direct chunk streaming download"""
    headers = {"User-Agent": "com.google.android.youtube/19.09.37 (Linux; U; Android 11)"}
    async with aiohttp.ClientSession() as session:
        async with session.get(stream_url, headers=headers) as resp:
            if resp.status != 200:
                return False
            with open(output_path, "wb") as f:
                async for chunk in resp.content.iter_chunked(1024 * 1024):
                    if chunk:
                        f.write(chunk)
    return True


@app.on_message(filters.command("start"))
async def start_handler(_, message: Message):
    await message.reply_text(
        "👋 **YouTube Music & Video Downloader Bot**\n\n"
        "**Available Commands:**\n"
        "• `/play <song name or link>` - Audio download karega 🎵\n"
        "• `/vplay <video name or link>` - Video download karega 🎬\n\n"
        "**Example:**\n"
        "`/play Kesariya`\n"
        "`/vplay https://youtu.be/xxxxxx`"
    )


# --- /play Command Handler (Audio Only) ---
@app.on_message(filters.command("play"))
async def play_audio_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("❗ **Usage:** `/play <song name or YouTube link>`")

    query = message.text.split(None, 1)[1].strip()
    status_msg = await message.reply_text("🔍 **Searching Audio...**")

    # 1. Check if input is link or name
    video_id = extract_video_id(query)
    if not video_id:
        video_id = await search_youtube(query)
        if not video_id:
            return await status_msg.edit_text("❌ Koi audio/song nahi mila.")

    try:
        # 2. Get stream URL
        _, audio_url, title = await fetch_streams(video_id)
        if not audio_url:
            return await status_msg.edit_text("❌ Audio stream unavailable.")

        await status_msg.edit_text(f"📥 **Downloading Audio:** `{title}`...")

        # 3. Download audio file
        file_path = f"{video_id}.m4a"
        success = await download_file(audio_url, file_path)
        if not success or not os.path.exists(file_path):
            return await status_msg.edit_text("❌ Download fail ho gaya.")

        await status_msg.edit_text("📤 **Uploading Audio...**")

        # 4. Send Audio
        await client.send_audio(
            chat_id=message.chat.id,
            audio=file_path,
            title=title,
            caption=f"🎵 **{title}**\n\n🔗 `https://youtu.be/{video_id}`"
        )
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"⚠️ **Error:** `{str(e)}`")

    finally:
        if os.path.exists(f"{video_id}.m4a"):
            os.remove(f"{video_id}.m4a")


# --- /vplay Command Handler (Video Only) ---
@app.on_message(filters.command("vplay"))
async def vplay_video_handler(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("❗ **Usage:** `/vplay <video name or YouTube link>`")

    query = message.text.split(None, 1)[1].strip()
    status_msg = await message.reply_text("🔍 **Searching Video...**")

    # 1. Check if input is link or name
    video_id = extract_video_id(query)
    if not video_id:
        video_id = await search_youtube(query)
        if not video_id:
            return await status_msg.edit_text("❌ Koi video nahi mili.")

    try:
        # 2. Get stream URL
        video_url, _, title = await fetch_streams(video_id)
        if not video_url:
            return await status_msg.edit_text("❌ Video stream unavailable.")

        await status_msg.edit_text(f"📥 **Downloading Video:** `{title}`...")

        # 3. Download video file
        file_path = f"{video_id}.mp4"
        success = await download_file(video_url, file_path)
        if not success or not os.path.exists(file_path):
            return await status_msg.edit_text("❌ Download fail ho gaya.")

        await status_msg.edit_text("📤 **Uploading Video...**")

        # 4. Send Video
        await client.send_video(
            chat_id=message.chat.id,
            video=file_path,
            caption=f"🎬 **{title}**\n\n🔗 `https://youtu.be/{video_id}`",
            supports_streaming=True
        )
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"⚠️ **Error:** `{str(e)}`")

    finally:
        if os.path.exists(f"{video_id}.mp4"):
            os.remove(f"{video_id}.mp4")


if __name__ == "__main__":
    print("Bot is running...")
    app.run()
