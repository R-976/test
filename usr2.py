import asyncio
import random
import os
import pytz
import logging
from os import getenv
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram import Client, filters, idle
from pymongo import ASCENDING
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from functools import wraps
from typing import Union, Tuple, List, Optional
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from flask import Flask
from threading import Thread

# Configure logging for Flask to reduce verbosity
logging.getLogger("werkzeug").setLevel(logging.ERROR)

# --- ENV VARIABLES FOR DEPLOYMENT ---
API_ID = int(getenv("API_ID", "1903"))
API_HASH = getenv("API_HASH", "")
BOT_TOKEN = getenv("BOT_TOKEN", "")
BOT_USERNAME = getenv("BOT_USERNAME", "")
MONGO_URL = getenv("MONGO_URL", "")
SUDO_USERS = list(map(int, getenv("SUDO_USERS", "5368154755").split()))
START_PIC = "https://graph.org/file/7117b98a990cf90b892da-24696dd1035f2789f5.jpg"

app = Client("stats_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- MongoDB setup ---
client = AsyncIOMotorClient(MONGO_URL)
db = client["message_tracking"]
user_stats = db["user_stats"]
group_stats = db["group_stats"]
user_group_daily_stats = db["user_group_daily_stats"]
blocked_users = db["blocked_users"]
blocked_groups = db["blocked_groups"]
flood_control = db["flood_control"]
removed_entities = db["removed_entities"]

# --- Constants ---
MESSAGE_LIMIT = 5
TIME_WINDOW = 10  # seconds
BLOCK_DURATION = 20 * 60  # seconds
DAILY_RETENTION_DAYS = 32
last_sent_date = None
IST = pytz.timezone("Asia/Kolkata")

# --- FLASK KEEP-ALIVE ---
flask_app = Flask('')
@flask_app.route("/healthz", methods=["GET", "HEAD"])
def healthz():
    return ("", 204)
@flask_app.route("/")
def home():
    return "Stats bot is running!"
def run_flask():
    port = int(os.getenv("PORT", "8080"))
    flask_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False, threaded=True)
Thread(target=run_flask, daemon=True).start()

# --- Utility Functions ---

async def setup_indexes():
    """Setup MongoDB indexes."""
    await flood_control.create_index([("user_id", ASCENDING)], unique=True)
    await removed_entities.create_index("deleted_at", expireAfterSeconds=2592000)

def format_number_dot(num: int) -> str:
    """Formats number with dots as thousands separator."""
    return f"{num:,}".replace(",", ".")

def keyboard_tuple(markup: InlineKeyboardMarkup):
    """Converts InlineKeyboardMarkup to a comparable tuple structure."""
    if not markup:
        return []
    return [[(btn.text, getattr(btn, "callback_data", None), getattr(btn, "url", None)) for btn in row] for row in markup.inline_keyboard]

async def safe_edit_message(message: Union[Message, CallbackQuery], new_text: str = None, new_markup: InlineKeyboardMarkup = None):
    """Safely edits message or its caption/markup, avoiding redundant edits."""
    if isinstance(message, CallbackQuery):
        message = message.message
    if not message:
        return
        
    old_text = message.text or message.caption or ""
    new_text = new_text or ""
    old_markup = message.reply_markup
    new_markup = new_markup or None

    text_changed = old_text.strip() != new_text.strip()
    markup_changed = keyboard_tuple(old_markup) != keyboard_tuple(new_markup)

    if not text_changed and not markup_changed:
        return

    try:
        if message.photo or message.video or message.document:
            if text_changed:
                return await message.edit_caption(new_text, reply_markup=new_markup)
            elif markup_changed:
                return await message.edit_reply_markup(new_markup)
        else:
            return await message.edit_text(new_text, reply_markup=new_markup)
    except Exception as e:
        print(f"[safe_edit_message] Failed: {e}")

async def safe_edit_media(message: Union[Message, CallbackQuery], new_media: InputMediaPhoto, new_markup: InlineKeyboardMarkup = None):
    """Safely edits media/photo message."""
    if isinstance(message, CallbackQuery):
        message = message.message
        
    old_caption = message.caption or ""
    new_caption = getattr(new_media, "caption", "") or ""
    old_markup = message.reply_markup
    new_markup = new_markup or None
    caption_changed = old_caption.strip() != new_caption.strip()
    markup_changed = keyboard_tuple(old_markup) != keyboard_tuple(new_markup)

    try:
        return await message.edit_media(media=new_media, reply_markup=new_markup)
    except Exception as e:
        print(f"[safe_edit_media] edit_media failed: {e}. Falling back...")
        try:
            if caption_changed:
                return await message.edit_caption(new_caption, reply_markup=new_markup)
            elif markup_changed:
                return await message.edit_reply_markup(new_markup)
        except Exception as e2:
            print(f"[safe_edit_media] fallback failed: {e2}")

async def get_user_display(client: Client, user_id: int, doc_data=None) -> Tuple[str, str]:
    """Fetches user name, prioritizing mention link, falling back to cached name, then ID."""
    name = None
    mention = None

    try:
        user = await client.get_users(user_id)
        name = user.first_name
        mention = f"[{name}](tg://user?id={user.id})"
    except Exception:
        cached_user = doc_data if doc_data and doc_data.get("first_name") else await user_stats.find_one({"user_id": user_id})
        
        if cached_user and cached_user.get("first_name"):
            name = cached_user["first_name"]
        else:
            name = f"User {user_id}"
            
        mention = name
            
    return name, mention

async def get_chat_display(client: Client, chat_id: int, doc_data=None) -> str:
    """Fetches chat title, falling back to cached title, then ID."""
    title = None

    try:
        chat = await client.get_chat(chat_id)
        title = chat.title
    except Exception:
        cached_chat = doc_data if doc_data and doc_data.get("group_title") else await group_stats.find_one({"group_id": chat_id})
        
        if cached_chat and cached_chat.get("group_title"):
            title = cached_chat["group_title"]
        else:
            title = f"Group {chat_id}"
            
    return title

# --- Decorator ---
def require_not_blocked(func):
    @wraps(func)
    async def wrapper(client, update, *args, **kwargs):
        try:
            user_id = update.from_user.id if hasattr(update, 'from_user') and update.from_user else None
            chat_id = (update.chat.id if isinstance(update, Message) else update.message.chat.id) if hasattr(update, 'chat') or (hasattr(update, 'message') and hasattr(update.message, 'chat')) else None
            
            if not user_id: 
                return

            # Check blocks
            blocked_u = await blocked_users.find_one({"user_id": user_id})
            blocked_g = await blocked_groups.find_one({"group_id": chat_id}) if chat_id else None

            if blocked_u:
                text = "🚫 You are blocked from using this bot."
                if isinstance(update, Message):
                    return await update.reply(text)
                elif isinstance(update, CallbackQuery):
                    return await update.answer(text, show_alert=True)
                
            if blocked_g:
                text = "🚫 This group is blocked from using this bot."
                if isinstance(update, Message):
                    return await update.reply(text)
                elif isinstance(update, CallbackQuery):
                    return await update.answer(text, show_alert=True)
                    
            # Check flood control
            flood = await flood_control.find_one({"user_id": user_id})
            if flood and flood.get("blocked_until"):
                now = datetime.utcnow()
                if now < flood["blocked_until"]:
                    text = "⌛ You're temporarily restricted due to flooding. Please wait."
                    if isinstance(update, Message):
                        return await update.reply(text)
                    elif isinstance(update, CallbackQuery):
                        return await update.answer(text, show_alert=True)

            return await func(client, update, *args, **kwargs)

        except Exception as e:
            print(f"[ERROR in require_not_blocked]: {e}")
            return

    return wrapper

# --- Image Generation ---
FONTS_DIR = "./fonts"
fallback_fonts = [
    "Symbola.ttf", "NotoSans-Regular.ttf", "NotoColorEmoji.ttf", "NotoSansSymbols2-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Apple Color Emoji.ttc",
    "C:\\Windows\\Fonts\\seguiemj.ttf",
]
loaded_fonts = []
for path in [os.path.join(FONTS_DIR, f) if not f.startswith("/") and ":" not in f else f for f in fallback_fonts]:
    if os.path.exists(path):
        try:
            loaded_fonts.append(ImageFont.truetype(path, size=24))
        except:
            pass

def get_fallback_font(char, size):
    for font in loaded_fonts:
        try:
            if font.getmask(char).getbbox():
                return font.font_variant(size=size)
        except:
            continue
    return ImageFont.load_default()

def draw_unicode_text(draw, pos, text, size, fill):
    x, y = pos
    for char in text:
        font = get_fallback_font(char, size)
        width = font.getlength(char if char != " " else " ")
        draw.text((x, y), char, font=font, fill=fill)
        x += max(width, size * 0.4) if char == " " else width

def draw_half_rounded_bar(image, pos, size, start_color, end_color):
    width, height = size
    x0, y0 = pos
    if width <= height:
        draw = ImageDraw.Draw(image)
        for x in range(width):
            ratio = x / width if width else 0
            color = tuple(int(start * (1 - ratio) + end * ratio) for start, end in zip(start_color, end_color))
            draw.line([(x0 + x, y0), (x0 + x, y0 + height)], fill=color)
        return
    gradient = Image.new("RGB", (width, height))
    for x in range(width):
        ratio = x / width
        color = tuple(int(start * (1 - ratio) + end * ratio) for start, end in zip(start_color, end_color))
        for y in range(height):
            gradient.putpixel((x, y), color)
    mask = Image.new("L", (width, height), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rectangle([0, 0, width - height // 2, height], fill=255)
    draw_mask.pieslice([width - height, 0, width, height], 270, 90, fill=255)
    image.paste(gradient, pos, mask)

def generate_rank_thumbnail(title: str, data: list) -> BytesIO:
    """Generates a ranking thumbnail image based on data."""
    width = 1080
    bar_height, bar_gap = 30, 12
    margins = {"top": 100, "bottom": 60, "left": 250, "right": 160}
    height = margins["top"] + margins["bottom"] + len(data) * (bar_height + bar_gap)

    image = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    chess_box_size = 40
    color1, color2 = (30, 5, 10), (40, 10, 20)
    for y in range(0, height, chess_box_size):
        for x in range(0, width, chess_box_size):
            fill_color = color1 if (x // chess_box_size + y // chess_box_size) % 2 == 0 else color2
            draw.rectangle([x, y, x + chess_box_size, y + chess_box_size], fill=fill_color)

    box_color = (60, 20, 30)
    box = (30, margins["top"] - 20, width - 30, margins["top"] - 20 + len(data) * (bar_height + bar_gap + 5))
    draw.rounded_rectangle(box, radius=20, fill=box_color)
    title_font = get_fallback_font(title, 48)
    title_width = title_font.getlength(title)
    draw_unicode_text(draw, ((width - title_width) // 2, 20), title, 48, "#ffffff")
    max_count = max((count for _, count in data if count > 0), default=1)

    for idx, (name, count) in enumerate(data):
        y = margins["top"] + idx * (bar_height + bar_gap)
        bar_len = int((width - margins["left"] - margins["right"]) * (count / max_count)) if max_count > 0 else 10
        bar_len = max(bar_len, 10)
        bar_x = margins["left"]
        draw_half_rounded_bar(image, (bar_x, y), (bar_len, bar_height), (220, 110, 110), (200, 80, 80))
        draw_unicode_text(draw, (60, y + 4), name[:14], 22, "#ffffff")
        count_str = format_number_dot(count)
        count_font = get_fallback_font(count_str, 20)
        text_x = bar_x + bar_len - count_font.getlength(count_str) - 20
        draw_unicode_text(draw, (text_x, y + 5), count_str, 20, "#ffffff")

    def draw_corner_text(text, y, size):
        font = get_fallback_font(text, size)
        x = width - font.getlength(text) - 40
        draw_unicode_text(draw, (x, y), text, size, "#bbbbbb")

    draw_corner_text("ROMEO-RJ", 30, 24)
    draw_corner_text(datetime.now().strftime("%Y-%m-%d"), height - 35, 24)

    output = BytesIO()
    image.save(output, format="PNG")
    output.name = "points_rankings.png"
    output.seek(0)
    return output

# --- CORE RANKING LOGIC ---
async def fetch_and_render_rankings(
    client: Client, 
    period: str, 
    chat_id: Optional[int] = None,
    entity_type: str = None  # Added to handle topusers/topgroups
) -> Tuple[str, List, InlineKeyboardMarkup, str]:
    """
    Fetches ranking data and prepares the text, chart data, and keyboard.
    Returns: (text, chart_data, keyboard, title)
    """
    now = datetime.utcnow()
    today_str = now.strftime("%Y-%m-%d")
    date_filter = {}
    title = ""
    
    # Determine entity type from period if contains topusers/topgroups
    if "topusers" in period:
        entity_type = "users"
        period = period.replace("topusers_", "")
    elif "topgroups" in period:
        entity_type = "groups"
        period = period.replace("topgroups_", "")
    
    # 1. Determine Filters and Title
    if chat_id:
        # Group Rankings (/rankings command logic)
        date_filter = {"chat_id": chat_id}
        if period == "today":
            date_filter["date"] = today_str
            title = "💥 Today's Top Members"
        elif period == "week":
            start_date = (now - timedelta(days=7)).strftime("%Y-%m-%d")
            date_filter["date"] = {"$gte": start_date}
            title = "💥 This Week's Top Members"
        elif period == "month":
            start_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")
            date_filter["date"] = {"$gte": start_date}
            title = "💥 This Month's Top Members"
        elif period == "yesterday":
            yesterday_str = (now - timedelta(days=1)).strftime("%Y-%m-%d")
            date_filter["date"] = yesterday_str
            title = "🌙 Yesterday's Top Members"
        else:  # Overall for Group
            title = "💥 All-Time Top Members"
    else:
        # Global Rankings (/topusers or /topgroups logic)
        if period == "today":
            date_filter["date"] = today_str
            title = "🔥 Top Users Today" if entity_type == "users" else "🏆 Top Groups Today"
        elif period == "week":
            start_date = (now - timedelta(days=7)).strftime("%Y-%m-%d")
            date_filter["date"] = {"$gte": start_date}
            title = "🔥 Top Users This Week" if entity_type == "users" else "🏆 Top Groups This Week"
        elif period == "month":
            start_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")
            date_filter["date"] = {"$gte": start_date}
            title = "🔥 Top Users This Month" if entity_type == "users" else "🏆 Top Groups This Month"
        else:  # Overall
            title = "🔥 Top Users Overall" if entity_type == "users" else "🏆 Top Groups Overall"

    # 2. Fetch Data
    results = []
    total_messages = 0
    
    if period == "overall":
        # Use primary stats collections for overall
        if chat_id:
            # Overall for specific group - aggregate from daily stats
            pipeline = [
                {"$match": {"chat_id": chat_id}},
                {"$group": {"_id": "$user_id", "total_messages": {"$sum": "$message_count"}}},
                {"$sort": {"total_messages": -1}},
                {"$limit": 10}
            ]
            results = await user_group_daily_stats.aggregate(pipeline).to_list(length=10)
            
            agg = await user_group_daily_stats.aggregate([
                {"$match": {"chat_id": chat_id}},
                {"$group": {"_id": None, "total": {"$sum": "$message_count"}}}
            ]).to_list(1)
            total_messages = agg[0]["total"] if agg and agg[0] else 0
        else:
            # Global overall
            if entity_type == "users":
                results = await user_stats.find().sort("message_count", -1).limit(10).to_list(length=10)
                agg = await user_stats.aggregate([
                    {"$group": {"_id": None, "total": {"$sum": "$message_count"}}}
                ]).to_list(1)
            else:  # groups
                results = await group_stats.find().sort("message_count", -1).limit(10).to_list(length=10)
                agg = await group_stats.aggregate([
                    {"$group": {"_id": None, "total": {"$sum": "$message_count"}}}
                ]).to_list(1)
            total_messages = agg[0]["total"] if agg and agg[0] else 0
    else:
        # Daily/Weekly/Monthly from user_group_daily_stats
        if chat_id:
            # Specific group rankings
            pipeline = [
                {"$match": date_filter},
                {"$group": {"_id": "$user_id", "total_messages": {"$sum": "$message_count"}}},
                {"$sort": {"total_messages": -1}},
                {"$limit": 10}
            ]
        else:
            # Global rankings
            group_field = "$user_id" if entity_type == "users" else "$chat_id"
            pipeline = [
                {"$match": date_filter},
                {"$group": {"_id": group_field, "total_messages": {"$sum": "$message_count"}}},
                {"$sort": {"total_messages": -1}},
                {"$limit": 10}
            ]
        
        results = await user_group_daily_stats.aggregate(pipeline).to_list(length=10)
        
        # Calculate total for the period
        agg_total = await user_group_daily_stats.aggregate([
            {"$match": date_filter},
            {"$group": {"_id": None, "total": {"$sum": "$message_count"}}}
        ]).to_list(1)
        total_messages = agg_total[0]["total"] if agg_total and agg_total[0] else 0

    # 3. Format Text and Chart Data
    chart_data = []
    text = f"**{title} {'in This Group' if chat_id else ''}:**\n\n"
    
    if results:
        for i, doc in enumerate(results):
            if period == "overall" and not chat_id:
                # From primary stats collections
                if entity_type == "users":
                    entity_id = doc.get("user_id")
                    count = doc.get("message_count", 0)
                else:
                    entity_id = doc.get("group_id")
                    count = doc.get("message_count", 0)
            else:
                # From aggregation
                entity_id = doc.get("_id")
                count = doc.get("total_messages", 0)
            
            if not entity_id:
                continue
                
            if (chat_id and period != "overall") or (not chat_id and entity_type == "users"):
                # Show user info
                name, mention = await get_user_display(client, entity_id, doc if period == "overall" and not chat_id else None)
                text += f"{i+1}.👤 {mention} - {format_number_dot(count)}\n"
                chart_data.append((name, count))
            else:
                # Show group info
                name = await get_chat_display(client, entity_id, doc if period == "overall" and not chat_id else None)
                text += f"{i+1}.👥 {name} - {format_number_dot(count)}\n"
                chart_data.append((name, count))
    else:
        text += "No data available."
        chart_data = [("No Data", 1)]

    text += f"\n\n✉️ Total messages: {format_number_dot(total_messages)}"
    
    # 4. Create Keyboard
    def tab_button(label, value, is_active, chat_id_val=None):
        prefix = " ✅" if is_active else ""
        if chat_id_val:
            cb_data = f"rankings_{value}_{chat_id_val}"
        elif entity_type == "users":
            cb_data = f"topusers_{value}"
        elif entity_type == "groups":
            cb_data = f"topgroups_{value}"
        else:
            cb_data = f"rankings_{value}_{chat_id}"
        return InlineKeyboardButton(f"🔘 {label}{prefix}", callback_data=cb_data)

    keyboard_rows = [
        [tab_button("Today", "today", period == "today", chat_id)],
        [
            tab_button("This Week", "week", period == "week", chat_id), 
            tab_button("This Month", "month", period == "month", chat_id)
        ],
        [tab_button("Overall", "overall", period == "overall", chat_id)]
    ]
    
    if period == "yesterday" and chat_id:
        keyboard_rows[0].insert(0, tab_button("Yesterday", "yesterday", True, chat_id))
        
    keyboard = InlineKeyboardMarkup(keyboard_rows)

    chart_data = [(name, count) for name, count in chart_data if count > 0] or [("No Data", 1)]

    return text, chart_data, keyboard, title

# --- Background Cleanup Task ---
async def cleanup_old_daily_stats():
    """Removes daily stats older than 32 days for storage optimization."""
    while True:
        try:
            await asyncio.sleep(6 * 3600)  # Check every 6 hours
            
            now_utc = datetime.utcnow()
            thirty_two_days_ago_str = (now_utc - timedelta(days=DAILY_RETENTION_DAYS)).strftime("%Y-%m-%d")

            print(f"🧹 Running daily stats cleanup for data older than {thirty_two_days_ago_str} (UTC)")
            delete_result = await user_group_daily_stats.delete_many(
                {"date": {"$lt": thirty_two_days_ago_str}}
            )
            print(f"✅ Cleanup complete. Deleted {delete_result.deleted_count} old daily stat documents.")

        except Exception as e:
            print(f"❌ Critical error in cleanup_old_daily_stats: {e}")
            await asyncio.sleep(7200)

# --- Admin Commands ---

@app.on_message(filters.command("reset") & filters.user(SUDO_USERS))
async def reset_stats(client, message: Message):
    try:
        await flood_control.delete_many({})
        await message.reply("✅ All flood control data has been reset.")
    except Exception as e:
        await message.reply(f"Failed to reset stats: {e}")

@app.on_message(filters.command(["addmsg", "removemsg"]) & filters.user(SUDO_USERS))
async def handle_msg_count(client, message: Message):
    cmd = message.command[0].lower()
    is_add = cmd == "addmsg"
    
    try:
        parts = message.text.strip().split()
        if len(parts) != 4:
            return await message.reply("❌ Usage: `/addmsg <id> <user/group> <count>` or `/removemsg <id> <user/group> <count>`")
            
        target_id = int(parts[1])
        target_type = parts[2].lower()
        count = int(parts[3])
        
        if count <= 0:
            return await message.reply("❌ Message count must be greater than 0.")
        
        if target_type not in ["user", "group"]:
            return await message.reply("❌ Invalid type. Use `user` or `group`.")
        
        change_val = count if is_add else -count
        now = datetime.utcnow()
        
        if target_type == "user":
            await user_stats.update_one(
                {"user_id": target_id},
                {"$inc": {"message_count": change_val}, "$set": {"last_active": now}},
                upsert=True
            )
            action = "Added" if is_add else "Removed"
            await message.reply(f"✅ {action} `{count}` messages {'to' if is_add else 'from'} **user ID** `{target_id}`.")
        else:
            await group_stats.update_one(
                {"group_id": target_id},
                {"$inc": {"message_count": change_val}, "$set": {"last_active": now}},
                upsert=True
            )
            action = "Added" if is_add else "Removed"
            await message.reply(f"✅ {action} `{count}` messages {'to' if is_add else 'from'} **group ID** `{target_id}`.")
            
    except ValueError:
        return await message.reply("❌ Invalid input. Ensure IDs and count are integers.")
    except Exception as e:
        return await message.reply(f"⚠️ Error: `{e}`")

@app.on_message(filters.command(["addrankingmsg", "removerankingmsg"]) & filters.user(SUDO_USERS))
async def handle_ranking_msg_count(client, message: Message):
    cmd = message.command[0].lower()
    is_add = cmd == "addrankingmsg"
    
    try:
        parts = message.text.strip().split()
        if len(parts) != 4:
            return await message.reply("❌ Usage: `/addrankingmsg <user_id> <chat_id> <count>` or `/removerankingmsg <user_id> <chat_id> <count>`")
        
        user_id = int(parts[1])
        chat_id = int(parts[2])
        count = int(parts[3])
        
        if count <= 0:
            return await message.reply("❌ Message count must be greater than 0.")
        
        change_val = count if is_add else -count
        now = datetime.utcnow()
        today_str = now.strftime("%Y-%m-%d")
        
        # Update all stats
        await asyncio.gather(
            user_group_daily_stats.update_one(
                {"user_id": user_id, "chat_id": chat_id, "date": today_str},
                {"$inc": {"message_count": change_val}},
                upsert=True
            ),
            user_stats.update_one(
                {"user_id": user_id},
                {"$inc": {"message_count": change_val}, "$set": {"last_active": now}},
                upsert=True
            ),
            group_stats.update_one(
                {"group_id": chat_id},
                {"$inc": {"message_count": change_val}, "$set": {"last_active": now}},
                upsert=True
            )
        )
        
        action = "Added" if is_add else "Removed"
        await message.reply(
            f"✅ {action} `{count}` messages for user `{user_id}` in chat `{chat_id}`.\n"
            f"Affected: Group rankings, Global rankings, Profile stats."
        )
        
    except ValueError:
        return await message.reply("❌ Invalid input. Ensure IDs and count are integers.")
    except Exception as e:
        return await message.reply(f"⚠️ Error: `{e}`")

@app.on_message(filters.command(["remove", "removes"]) & filters.user(SUDO_USERS))
async def remove_entity(client, message: Message):
    if len(message.command) != 3:
        return await message.reply("❌ Usage: /remove <id> <user|group>")
    try:
        entity_id = int(message.command[1])
        entity_type = message.command[2].lower()
        if entity_type not in ["user", "group"]:
            return await message.reply("❌ Invalid type. Use 'user' or 'group'.")
        now = datetime.utcnow()
        if entity_type == "user":
            user_data = await user_stats.find_one({"user_id": entity_id})
            daily_data = await user_group_daily_stats.find({"user_id": entity_id}).to_list(None)
            archive = {"entity_id": entity_id, "entity_type": "user", "user_stats": user_data, "daily_stats": daily_data, "deleted_at": now}
            await removed_entities.insert_one(archive)
            await asyncio.gather(
                user_stats.delete_many({"user_id": entity_id}),
                user_group_daily_stats.delete_many({"user_id": entity_id})
            )
            await message.reply(f"✅ User {entity_id} removed and archived for 30 days.")
        else:
            group_data = await group_stats.find_one({"group_id": entity_id})
            daily_data = await user_group_daily_stats.find({"chat_id": entity_id}).to_list(None)
            archive = {"entity_id": entity_id, "entity_type": "group", "group_stats": group_data, "daily_stats": daily_data, "deleted_at": now}
            await removed_entities.insert_one(archive)
            await asyncio.gather(
                group_stats.delete_many({"group_id": entity_id}),
                user_group_daily_stats.delete_many({"chat_id": entity_id})
            )
            await message.reply(f"✅ Group {entity_id} removed and archived for 30 days.")
    except Exception as e:
        await message.reply(f"⚠️ Error: {e}")

@app.on_message(filters.command(["recover", "tryrecover"]) & filters.user(SUDO_USERS))
async def recover_entity(client, message: Message):
    if len(message.command) != 3:
        return await message.reply("❌ Usage: /recover <id> <user|group>")
    try:
        entity_id = int(message.command[1])
        entity_type = message.command[2].lower()
        doc = await removed_entities.find_one({"entity_id": entity_id, "entity_type": entity_type})
        if not doc:
            return await message.reply("❌ No recovery data found or expired.")
        
        tasks = []
        if entity_type == "user":
            if doc.get("user_stats"):
                tasks.append(user_stats.insert_one(doc["user_stats"]))
            if doc.get("daily_stats"):
                tasks.append(user_group_daily_stats.insert_many(doc["daily_stats"]))
        else:
            if doc.get("group_stats"):
                tasks.append(group_stats.insert_one(doc["group_stats"]))
            if doc.get("daily_stats"):
                tasks.append(user_group_daily_stats.insert_many(doc["daily_stats"]))
                
        tasks.append(removed_entities.delete_one({"_id": doc["_id"]}))
        await asyncio.gather(*tasks)
        await message.reply(f"✅ {entity_type.capitalize()} {entity_id} recovered successfully.")
    except Exception as e:
        await message.reply(f"⚠️ Error during recovery: {e}")

@app.on_message(filters.command(["listremoved", "removedlist"]) & filters.user(SUDO_USERS))
async def list_removed_entities(client, message: Message):
    try:
        removed = await removed_entities.find().to_list(length=100)
        if not removed:
            return await message.reply("✅ No entities are currently in the removal archive.")
        users, groups, now = [], [], datetime.utcnow()
        for doc in removed:
            entity_id = doc["entity_id"]
            removed_at = doc.get("deleted_at")
            days_left = max(0, 30 - (now - removed_at).days) if removed_at else "Unknown"
            
            if doc["entity_type"] == "user":
                name, mention = await get_user_display(client, entity_id, doc.get("user_stats"))
                users.append(f"• {mention} (`{entity_id}`) — {days_left}d left")
            else:
                name = await get_chat_display(client, entity_id, doc.get("group_stats"))
                groups.append(f"• **{name}** (`{entity_id}`) — {days_left}d left")
                
        text = "**🗃️ Removed Entities (Grace Period):**\n\n"
        if users: 
            text += "**👤 Users:**\n" + "\n".join(users) + "\n\n"
        if groups: 
            text += "**👥 Groups:**\n" + "\n".join(groups)
        await message.reply(text, disable_web_page_preview=True)
    except Exception as e:
        await message.reply(f"⚠️ Error listing removed entities: {e}")

@app.on_message(filters.command("block") & filters.user(SUDO_USERS))
async def block_user_or_group(client, message: Message):
    try:
        if len(message.command) < 3:
            return await message.reply("❌ Usage: /block <id> <user|group> [reason]")
        entity_id = int(message.command[1])
        entity_type = message.command[2].lower()
        reason = " ".join(message.command[3:]) or "No reason provided"
        if entity_type not in ["user", "group"]: 
            return await message.reply("❌ Invalid type. Use 'user' or 'group'.")

        collection = blocked_users if entity_type == "user" else blocked_groups
        field = "user_id" if entity_type == "user" else "group_id"
        if await collection.find_one({field: entity_id}):
            return await message.reply(f"ℹ️ {entity_type.capitalize()} {entity_id} is already blocked.")
        await collection.insert_one({
            field: entity_id, "reason": reason, "blocked_by": message.from_user.id, "blocked_at": datetime.utcnow()
        })
        await message.reply(f"✅ Successfully blocked {entity_type} {entity_id}\nReason: {reason}")
    except ValueError:
        return await message.reply("❌ Invalid ID. Must be an integer.")
    except Exception as e:
        await message.reply(f"⚠️ Error blocking: {str(e)}")

@app.on_message(filters.command("unblock") & filters.user(SUDO_USERS))
async def unblock_user_or_group(client, message: Message):
    try:
        if len(message.command) != 3: 
            return await message.reply("❌ Usage: /unblock <id> <user|group>")
        entity_id = int(message.command[1])
        entity_type = message.command[2].lower()
        if entity_type not in ["user", "group"]: 
            return await message.reply("❌ Invalid type. Use 'user' or 'group'.")
        
        collection = blocked_users if entity_type == "user" else blocked_groups
        field = "user_id" if entity_type == "user" else "group_id"
        result = await collection.delete_one({field: entity_id})
        if result.deleted_count:
            await message.reply(f"✅ Successfully unblocked {entity_type} {entity_id}")
        else:
            await message.reply(f"ℹ️ {entity_type.capitalize()} {entity_id} was not found in blocklist.")
    except ValueError:
        return await message.reply("❌ Invalid ID. Must be an integer.")
    except Exception as e:
        await message.reply(f"⚠️ Error unblocking: {str(e)}")

@app.on_message(filters.command(["blockinfo", "blockreason"]) & filters.user(SUDO_USERS))
async def check_block_reason(client, message: Message):
    try:
        if len(message.command) < 3: 
            return await message.reply("❌ Usage: /blockinfo <ID> <user|group>")
        entity_id = int(message.command[1])
        entity_type = message.command[2].lower()
        if entity_type not in ["user", "group"]: 
            return await message.reply("❌ Invalid type. Must be 'user' or 'group'.")
        
        collection = blocked_users if entity_type == "user" else blocked_groups
        field = "user_id" if entity_type == "user" else "group_id"
        blocked_entry = await collection.find_one({field: entity_id})
        
        if not blocked_entry: 
            return await message.reply(f"ℹ️ {entity_type.capitalize()} {entity_id} is not blocked.")
        
        reason = blocked_entry.get("reason", "No reason provided")
        blocked_by = blocked_entry.get("blocked_by", "Unknown")
        blocked_at = blocked_entry.get("blocked_at", "Unknown time")
        if isinstance(blocked_at, datetime): 
            blocked_at = blocked_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Fixed await issue
        if entity_type == "user":
            entity_name, _ = await get_user_display(client, entity_id)
        else:
            entity_name = await get_chat_display(client, entity_id)

        response = (
            f"🔍 Block Information for {entity_type.capitalize()}\n\n"
            f"🆔 {entity_name} (`{entity_id}`)\n"
            f"📝 Reason: {reason}\n"
            f"🛡️ Blocked by: {blocked_by}\n"
            f"⏰ Blocked at: {blocked_at}"
        )
        await message.reply(response)
    except ValueError:
        return await message.reply("❌ Invalid ID. Must be an integer.")
    except Exception as e:
        await message.reply(f"⚠️ Error fetching block information: {str(e)}")

@app.on_message(filters.command(["listblocked", "listblock", "blocklist"]) & filters.user(SUDO_USERS))
async def list_blocked_entities(client, message: Message):
    try:
        entity_type = message.command[1].lower() if len(message.command) > 1 else None
        if entity_type not in [None, "user", "group"]: 
            return await message.reply("❌ Invalid type. Use 'user' or 'group'.")
        
        responses = []
        if entity_type in [None, "user"]:
            user_list = await blocked_users.find().to_list(length=100)
            if user_list:
                responses.append("👤 Blocked Users:")
                for u in user_list:
                    name, _ = await get_user_display(client, u['user_id'])
                    responses.append(f"• {u['user_id']} ({name}) - {u.get('reason', 'No reason')} (by {u.get('blocked_by', 'unknown')})")
        if entity_type in [None, "group"]:
            group_list = await blocked_groups.find().to_list(length=100)
            if group_list:
                responses.append("\n👥 Blocked Groups:")
                for g in group_list:
                    title = await get_chat_display(client, g['group_id'])
                    responses.append(f"• {g['group_id']} ({title}) - {g.get('reason', 'No reason')} (by {g.get('blocked_by', 'unknown')})")
        
        if not responses:
            await message.reply("ℹ️ No blocked entities found.")
        else:
            response_text = "\n".join(responses)
            if len(response_text) > 4096:
                chunks = [response_text[i:i + 4000] for i in range(0, len(response_text), 4000)]
                for chunk in chunks:
                    await message.reply(chunk)
            else:
                await message.reply(response_text)
    except Exception as e:
        await message.reply(f"⚠️ Error listing blocked entities: {str(e)}")

# --- Command Handlers ---
@app.on_message(filters.command(["rankings", "ranking"]) & filters.group)
@require_not_blocked
async def show_rankings(client, message: Message):
    try:
        chat_id = message.chat.id
        processing_msg = await message.reply("⏳ Processing rankings...")
        
        text, chart_data, keyboard, title = await fetch_and_render_rankings(client, "today", chat_id)

        thumb = generate_rank_thumbnail(title, chart_data)
        if thumb and thumb.getbuffer().nbytes > 0:
            await processing_msg.delete()
            await message.reply_photo(thumb, caption=text, reply_markup=keyboard)
        else:
            await processing_msg.edit_text(text, reply_markup=keyboard)

    except Exception as e:
        print(f"Error in /rankings: {e}")

@app.on_message(filters.command(["topusers", "topuser"]))
@require_not_blocked
async def show_top_users(client, message: Message):
    try:
        processing_msg = await message.reply("⏳ Gathering top users data...")

        text, chart_data, keyboard, title = await fetch_and_render_rankings(client, "today", None, "users")

        thumb = generate_rank_thumbnail(title, chart_data)
        if thumb and thumb.getbuffer().nbytes > 0:
            await processing_msg.delete()
            await message.reply_photo(thumb, caption=text, reply_markup=keyboard)
        else:
            await processing_msg.edit_text(text, reply_markup=keyboard)

    except Exception as e:
        print(f"Error in /topusers: {e}")

@app.on_message(filters.command(["topgroups", "topgroup"]))
@require_not_blocked
async def show_top_groups(client, message: Message):
    try:
        processing_msg = await message.reply("⏳ Analyzing group activity...")

        text, chart_data, keyboard, title = await fetch_and_render_rankings(client, "today", None, "groups")

        thumb = generate_rank_thumbnail(title, chart_data)
        if thumb and thumb.getbuffer().nbytes > 0:
            await processing_msg.delete()
            await message.reply_photo(thumb, caption=text, reply_markup=keyboard)
        else:
            await processing_msg.edit_text(text, reply_markup=keyboard)

    except Exception as e:
        print(f"Error in /topgroups: {e}")

@app.on_message(filters.command(["mystats", "stats", "profile"]))
@require_not_blocked
async def show_mystats(client, message: Message):
    try:
        if message.chat.type == "private":
            return await message.reply("This command works best in groups!")
        if not message.from_user:
            return await message.reply("Couldn't identify your user account.")
        
        processing_msg = await message.reply("⏳ Calculating your stats...")
        user_id = message.from_user.id
        chat_id = message.chat.id
        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        week_start = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        # Async aggregation for all required data points
        results = await asyncio.gather(
            user_group_daily_stats.find_one({"user_id": user_id, "chat_id": chat_id, "date": today_str}),
            user_group_daily_stats.aggregate([{"$match": {"user_id": user_id, "date": today_str}}, {"$group": {"_id": None, "total": {"$sum": "$message_count"}}}]).to_list(1),
            user_group_daily_stats.aggregate([{"$match": {"user_id": user_id, "date": {"$gte": week_start}}}, {"$group": {"_id": None, "total": {"$sum": "$message_count"}}}]).to_list(1),
            user_stats.find_one({"user_id": user_id}),
            user_group_daily_stats.aggregate([{"$match": {"date": today_str}}, {"$group": {"_id": None, "total": {"$sum": "$message_count"}}}]).to_list(1),
            user_group_daily_stats.aggregate([{"$match": {"date": today_str}}, {"$group": {"_id": "$user_id", "total_messages": {"$sum": "$message_count"}}}, {"$sort": {"total_messages": -1}}]).to_list(None)
        )
        
        # Extract results
        today_chat_count = results[0]["message_count"] if results[0] else 0
        today_all_count = results[1][0]["total"] if results[1] else 0
        weekly_count = results[2][0]["total"] if results[2] else 0
        total_count = results[3]["message_count"] if results[3] else 0
        total_today = results[4][0]["total"] if results[4] else 0
        ranked = results[5]

        # Compute percentage and rank
        percent_today = (today_all_count / total_today * 100) if total_today else 0
        rank = next((i + 1 for i, r in enumerate(ranked) if r["_id"] == user_id), "N/A")
        
        text = (
            f"**📊 Your Message Stats**\n\n"
            f"• **Today (This Chat):** {format_number_dot(today_chat_count)} messages\n"
            f"• **Today (All Chats):** {format_number_dot(today_all_count)} messages\n"
            f"• **This Week:** {format_number_dot(weekly_count)} messages\n"
            f"• **All Time:** {format_number_dot(total_count)} messages\n\n"
            f"🏅 **Today Rank:** {rank}\n"
            f"📈 **Today Contribution:** {percent_today:.2f}%\n\n"
            f"Keep chatting to climb the rankings! 🚀"
        )
        await processing_msg.edit_text(text)
    except Exception as e:
        print(f"Error in /profile: {e}")
        try:
            await processing_msg.edit_text(f"⚠️ An error occurred while calculating stats.")
        except:
            pass

# --- Callback Handlers ---

@app.on_callback_query(filters.regex(r"rankings_(today|week|month|overall)_(-?\d+)"))
@require_not_blocked
async def rankings_callback(client, callback_query: CallbackQuery):
    try:
        await callback_query.answer()
        data_parts = callback_query.data.split("_")
        period = data_parts[1]
        chat_id = int(data_parts[2])
        
        text, chart_data, keyboard, title = await fetch_and_render_rankings(client, period, chat_id)
        
        thumb = generate_rank_thumbnail(title, chart_data)
        if thumb and thumb.getbuffer().nbytes > 0:
            await safe_edit_media(callback_query, InputMediaPhoto(thumb, caption=text), keyboard)
        else:
            await safe_edit_message(callback_query, text, keyboard)

    except Exception as e:
        await safe_edit_message(callback_query, f"Error: {str(e)}")

@app.on_callback_query(filters.regex(r"topusers_(today|week|month|overall)"))
@require_not_blocked
async def topusers_callback(client, callback_query: CallbackQuery):
    try:
        await callback_query.answer()
        period = callback_query.data.split("_")[1]
        
        text, chart_data, keyboard, title = await fetch_and_render_rankings(client, period, None, "users")

        thumb = generate_rank_thumbnail(title, chart_data)
        if thumb and thumb.getbuffer().nbytes > 0:
            await safe_edit_media(callback_query, InputMediaPhoto(thumb, caption=text), keyboard)
        else:
            await safe_edit_message(callback_query, text, keyboard)

    except Exception as e:
        await safe_edit_message(callback_query, f"Error: {str(e)}")

@app.on_callback_query(filters.regex(r"topgroups_(today|week|month|overall)"))
@require_not_blocked
async def topgroups_callback(client, callback_query: CallbackQuery):
    try:
        await callback_query.answer()
        period = callback_query.data.split("_")[1]
        
        text, chart_data, keyboard, title = await fetch_and_render_rankings(client, period, None, "groups")

        thumb = generate_rank_thumbnail(title, chart_data)
        if thumb and thumb.getbuffer().nbytes > 0:
            await safe_edit_media(callback_query, InputMediaPhoto(thumb, caption=text), keyboard)
        else:
            await safe_edit_message(callback_query, text, keyboard)

    except Exception as e:
        await safe_edit_message(callback_query, f"Error: {str(e)}")

# --- Help & Start Commands ---

@app.on_message(filters.command("help") & filters.private)
async def help_command(client, message):
    text = (
        "**🛠️ Available Commands**\n\n"
        "**General:**\n"
        "`/start` — Welcome message\n"
        "`/help` — Show this help message\n"
        "`/profile` — See your personal message stats\n\n"
        "**Group Statistics:**\n"
        "`/rankings` — Show top 10 active members in this chat\n"
        "`/topusers` — Show top 10 users (overall)\n"
        "`/topgroups` — Show top 10 groups (overall)\n\n"
        "_Make sure the bot is admin in groups for accurate tracking._"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add me to a group", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
        [InlineKeyboardButton("🏠 Back to Start", callback_data="start_menu")],
        [
            InlineKeyboardButton("Support", url="https://t.me/RomeoBot_op"),
            InlineKeyboardButton("Channel", url="https://t.me/Romeo_op")
        ]
    ])
    await message.reply_photo(photo=START_PIC, caption=text, reply_markup=keyboard)

@app.on_callback_query(filters.regex("help_menu"))
async def help_callback(client, callback_query):
    await callback_query.answer()
    text = (
        "**🛠️ Available Commands**\n\n"
        "**General:**\n"
        "`/start` — Welcome message\n"
        "`/help` — Show this help message\n"
        "`/profile` — See your personal message stats\n\n"
        "**Group Statistics:**\n"
        "`/rankings` — Show top 10 active members in this chat\n"
        "`/topusers` — Show top 10 users (overall)\n"
        "`/topgroups` — Show top 10 groups (overall)\n\n"
        "_Make sure the bot is admin in groups for accurate tracking._"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add me to a group", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
        [InlineKeyboardButton("🏠 Back to Start", callback_data="start_menu")]
    ])
    await callback_query.message.edit_text(text, reply_markup=keyboard)

@app.on_callback_query(filters.regex("start_menu"))
async def start_callback(client, callback_query):
    await callback_query.answer()
    text = (
        "**👋 Hello! I'm a Message Tracker Bot.**\n\n"
        "I help track user activity and message counts in your groups.\n"
        "Add me to a group and promote me as **admin** to get started.\n\n"
        "**Useful commands:**\n"
        "`/help` — Show all available commands\n"
        "`/profile` — See your personal message stats\n"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add me to a group", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
        [InlineKeyboardButton("📖 Help", callback_data="help_menu")]
    ])
    await callback_query.message.edit_text(text, reply_markup=keyboard)

@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    text = (
        "**👋 Hello! I'm a Message Tracker Bot.**\n\n"
        "I help track user activity and message counts in your groups.\n"
        "Add me to a group and promote me as **admin** to get started.\n\n"
        "**Useful commands:**\n"
        "`/help` — Show all available commands\n"
        "`/profile` — See your personal message stats\n"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add me to a group", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
        [InlineKeyboardButton("📖 Help", callback_data="help_menu")],
        [
            InlineKeyboardButton("Support", url="https://t.me/RomeoBot_op"),
            InlineKeyboardButton("Channel", url="https://t.me/Romeo_op")
        ]
    ])
    await message.reply_photo(photo=START_PIC, caption=text, reply_markup=keyboard)

# --- Message Tracking ---
@app.on_message(filters.group & ~filters.bot & ~filters.service)
async def track_user_messages(client, message: Message):
    try:
        if not message.from_user or message.from_user.is_bot:
            return
        
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        if (await blocked_users.find_one({"user_id": user_id})) or \
           (await blocked_groups.find_one({"group_id": chat_id})):
            return
            
        now = datetime.utcnow()
        today_str = now.strftime("%Y-%m-%d")
        
        user_data = await flood_control.find_one({"user_id": user_id})
        
        # Check for active block
        if user_data and user_data.get("blocked_until") and now < user_data["blocked_until"]:
            if not user_data.get("warned"):
                await flood_control.update_one({"user_id": user_id}, {"$set": {"warned": True, "released": False}}, upsert=True)
                await message.reply("Flood detected! You must wait 20 minutes before messages are counted again.")
            return

        # Release from block if time passed
        if user_data and user_data.get("blocked_until") and now >= user_data["blocked_until"] and not user_data.get("released"):
            await message.reply("You are now released.")
            await flood_control.update_one({"user_id": user_id}, {"$set": {"released": True, "warned": False, "timestamps": []}})
            user_data = None
            
        # Process new message for flood check
        timestamps = user_data.get("timestamps", []) if user_data else []
        timestamps = [ts for ts in timestamps if (now - ts).total_seconds() <= TIME_WINDOW]
        timestamps.append(now)
        
        if len(timestamps) >= MESSAGE_LIMIT:
            await flood_control.update_one({"user_id": user_id}, 
                {"$set": {"blocked_until": now + timedelta(seconds=BLOCK_DURATION), "warned": False, "released": False, "timestamps": []}}, upsert=True)
            return await message.reply("Flood detected! You must wait 20 minutes before messages are counted again.")

        await flood_control.update_one({"user_id": user_id}, {"$set": {"timestamps": timestamps}}, upsert=True)
        
        # Update Stats with cached names
        await asyncio.gather(
            user_group_daily_stats.update_one(
                {"user_id": user_id, "chat_id": chat_id, "date": today_str},
                {"$inc": {"message_count": 1}}, 
                upsert=True
            ),
            user_stats.update_one(
                {"user_id": user_id},
                {"$inc": {"message_count": 1}, "$set": {"last_active": now, "first_name": message.from_user.first_name}},
                upsert=True
            ),
            group_stats.update_one(
                {"group_id": chat_id},
                {"$inc": {"message_count": 1}, "$set": {"last_active": now, "group_title": message.chat.title}},
                upsert=True
            )
        )
    except Exception as e:
        print(f"Error tracking message: {e}")

@app.on_message(filters.command(["hlp", "hp", "hl"]) & filters.user(SUDO_USERS))
async def hlp_command(client, message):
    text = (
        "**🛠️ Available Commands Only SudoUsers**\n\n"
        "**General:**\n"
        "`/reset` — Reset flood control data\n"
        "`/block` — block id user/group [reason]\n"
        "`/unblock` — unblock id user/group\n"
        "`/blocklist` — blocklist [user/group]\n"
        "`/blockinfo` — blockinfo id user/group\n"
        "`/remove` — remove id user/group\n"
        "`/recover` — recover id user/group\n"
        "`/removedlist` — Show removed entities\n"
        "`/addmsg` — addmsg id user/group count\n"
        "`/removemsg` — removemsg id user/group count\n"
        "`/addrankingmsg` — addrankingmsg user_id chat_id count\n"
        "`/removerankingmsg` — removerankingmsg user_id chat_id count\n"
        "`/senddaily` — Send daily rankings manually\n"
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add me to a group", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
        [InlineKeyboardButton("🏠 Back to Start", callback_data="start_menu")]
    ])
    await message.reply_photo(photo=START_PIC, caption=text, reply_markup=keyboard)

# --- Daily Rankings ---
async def send_daily_rankings():
    global last_sent_date
    while True:
        try:
            now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
            now_ist = now_utc.astimezone(IST)
            current_date = now_ist.strftime("%Y-%m-%d")
            
            # Auto Cleanup (Run shortly after midnight IST)
            if now_ist.hour == 0 and 5 <= now_ist.minute <= 30:
                thirty_two_days_ago_str = (now_utc - timedelta(days=DAILY_RETENTION_DAYS)).strftime("%Y-%m-%d")
                delete_result = await user_group_daily_stats.delete_many({"date": {"$lt": thirty_two_days_ago_str}})
                print(f"✅ Auto Cleanup: Deleted {delete_result.deleted_count} daily stats older than {thirty_two_days_ago_str}")

            # Daily Send Logic (Run shortly after midnight IST)
            if now_ist.hour == 0 and now_ist.minute < 5 and last_sent_date != current_date:
                last_sent_date = current_date
                yesterday = now_ist.date() - timedelta(days=1)
                yesterday_str = yesterday.strftime("%Y-%m-%d")
                
                print(f"⏰ Sending daily rankings for {yesterday_str} at {now_ist.strftime('%H:%M:%S')} IST")
                
                group_ids = await user_group_daily_stats.distinct("chat_id", {"date": yesterday_str})
                
                for chat_id in group_ids:
                    try:
                        text, chart_data, keyboard, title = await fetch_and_render_rankings(app, "yesterday", chat_id)
                        
                        thumb = generate_rank_thumbnail(title, chart_data)
                        
                        if thumb and thumb.getbuffer().nbytes > 0:
                            await app.send_photo(chat_id=chat_id, photo=thumb, caption=text, reply_markup=keyboard)
                        else:
                            await app.send_message(chat_id=chat_id, text=text, reply_markup=keyboard)
                            
                        print(f"✅ Sent daily ranking to {chat_id}")
                        await asyncio.sleep(1)
                            
                    except Exception as e:
                        print(f"⚠️ Failed to send daily ranking to {chat_id}: {e}")
                        continue
                
                print(f"✅ Daily rankings dispatch completed.")
                
            await asyncio.sleep(30)
            
        except Exception as e:
            print(f"❌ Critical error in send_daily_rankings loop: {e}")
            await asyncio.sleep(60)

@app.on_message(filters.command("senddaily") & filters.user(SUDO_USERS))
async def manual_daily_send(client, message: Message):
    try:
        now_ist = datetime.now(IST)
        yesterday = now_ist.date() - timedelta(days=1)
        yesterday_str = yesterday.strftime("%Y-%m-%d")
        
        await message.reply(f"📤 Manually sending yesterday's ({yesterday_str}) rankings to all active groups...")
        
        # Manual Cleanup
        thirty_two_days_ago_str = (datetime.utcnow() - timedelta(days=DAILY_RETENTION_DAYS)).strftime("%Y-%m-%d")
        delete_result = await user_group_daily_stats.delete_many({"date": {"$lt": thirty_two_days_ago_str}})
        
        group_ids = await user_group_daily_stats.distinct("chat_id", {"date": yesterday_str})
        
        if not group_ids:
            return await message.reply("❌ No groups found with yesterday's activity")
        
        sent_count, failed_count = 0, 0
        
        for chat_id in group_ids:
            try:
                text, chart_data, keyboard, title = await fetch_and_render_rankings(app, "yesterday", chat_id)
                
                thumb = generate_rank_thumbnail(title, chart_data)
                
                if thumb and thumb.getbuffer().nbytes > 0:
                    await app.send_photo(chat_id=chat_id, photo=thumb, caption=text, reply_markup=keyboard)
                else:
                    await app.send_message(chat_id=chat_id, text=text, reply_markup=keyboard)
                
                sent_count += 1
                await asyncio.sleep(1)
                
            except Exception as e:
                failed_count += 1
                print(f"Failed to send to {chat_id}: {e}")
        
        await message.reply(
            f"✅ Manual send complete!\n"
            f"📤 Sent: {sent_count} groups\n"
            f"❌ Failed: {failed_count} groups\n"
            f"🧹 Cleanup: Deleted {delete_result.deleted_count} old daily stats."
        )
        
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

# --- Start Bot ---
async def start_bot():
    await setup_indexes()
    await app.start()
    print("LOG: Founded Bot token Booting..")
    print("STATS BOT SUCCESSFULLY STARTED ✅✅")
    
    # Launch background tasks
    asyncio.create_task(send_daily_rankings())
    asyncio.create_task(cleanup_old_daily_stats())
    
    await idle()
    print("Bot stopped")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_bot())
