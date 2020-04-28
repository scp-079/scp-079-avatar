# SCP-079-AVATAR - Get newly joined member's profile photo
# Copyright (C) 2019-2020 SCP-079 <https://scp-079.org>
#
# This file is part of SCP-079-AVATAR.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
from typing import Generator, Iterable, List, Optional, Union

from pyrogram import ChatMember, Client, InlineKeyboardMarkup, Message, User
from pyrogram.api.functions.account import UpdateStatus
from pyrogram.api.functions.messages import ReadMentions
from pyrogram.api.functions.users import GetFullUser
from pyrogram.api.types import InputPeerUser, InputPeerChannel, UserFull
from pyrogram.errors import ChatAdminRequired, ButtonDataInvalid, ChannelInvalid, ChannelPrivate, FloodWait
from pyrogram.errors import PeerIdInvalid, UsernameInvalid, UsernameNotOccupied, UserNotParticipant

from .decorators import retry

# Enable logging
logger = logging.getLogger(__name__)


@retry
def download_media(client: Client, file_id: str, file_ref: str, file_path: str) -> Optional[str]:
    # Download a media file
    result = None

    try:
        result = client.download_media(message=file_id, file_ref=file_ref, file_name=file_path)
    except FloodWait as e:
        raise e
    except Exception as e:
        logger.warning(f"Download media {file_id} to {file_path} error: {e}", exc_info=True)

    return result


@retry
def get_admins(client: Client, cid: int) -> Union[bool, List[ChatMember], None]:
    # Get a group's admins
    result = None

    try:
        result = client.get_chat_members(chat_id=cid, filter="administrators")
    except FloodWait as e:
        raise e
    except (ChannelInvalid, ChannelPrivate, PeerIdInvalid):
        return False
    except Exception as e:
        logger.warning(f"Get admins in {cid} error: {e}", exc_info=True)

    return result


@retry
def get_chat_member(client: Client, cid: int, uid: int) -> Union[bool, ChatMember, None]:
    # Get information about one member of a chat
    result = None

    try:
        result = client.get_chat_member(chat_id=cid, user_id=uid)
    except FloodWait as e:
        raise e
    except (ChannelInvalid, ChannelPrivate, PeerIdInvalid, UserNotParticipant):
        result = False
    except Exception as e:
        logger.warning(f"Get chat member {uid} in {cid} error: {e}", exc_info=True)

    return result


@retry
def get_members(client: Client, cid: int, query: str = "all") -> Optional[Generator[ChatMember, None, None]]:
    # Get a members generator of a chat
    result = None

    try:
        result = client.iter_chat_members(chat_id=cid, filter=query)
    except FloodWait as e:
        raise e
    except Exception as e:
        logger.warning(f"Get members in {cid} error: {e}", exc_info=True)

    return result


@retry
def get_users(client: Client, uids: Iterable[Union[int, str]]) -> Optional[List[User]]:
    # Get users
    result = None

    try:
        result = client.get_users(user_ids=uids)
    except FloodWait as e:
        raise e
    except PeerIdInvalid:
        return None
    except Exception as e:
        logger.warning(f"Get users {uids} error: {e}", exc_info=True)

    return result


@retry
def get_user_full(client: Client, uid: int) -> Optional[UserFull]:
    # Get a full user
    result = None

    try:
        user_id = resolve_peer(client, uid)

        if not user_id:
            return None

        result = client.send(GetFullUser(id=user_id))
    except FloodWait as e:
        raise e
    except Exception as e:
        logger.warning(f"Get user {uid} full error: {e}", exc_info=True)

    return result


@retry
def leave_chat(client: Client, cid: int, delete: bool = False) -> bool:
    # Leave a channel
    result = False

    try:
        result = client.leave_chat(chat_id=cid, delete=delete) or True
    except FloodWait as e:
        raise e
    except (ChannelInvalid, ChannelPrivate, PeerIdInvalid):
        return False
    except Exception as e:
        logger.warning(f"Leave chat {cid} error: {e}", exc_info=True)

    return result


@retry
def read_history(client: Client, cid: int) -> bool:
    # Mark messages in a chat as read
    result = False

    try:
        result = client.read_history(chat_id=cid) or True
    except FloodWait as e:
        raise e
    except Exception as e:
        logger.warning(f"Read history in {cid} error: {e}", exc_info=True)

    return result


@retry
def read_mention(client: Client, cid: int) -> bool:
    # Mark a mention as read
    result = False

    try:
        peer = resolve_peer(client, cid)

        if not peer:
            return True

        result = client.send(ReadMentions(peer=peer)) or True
    except FloodWait as e:
        raise e
    except Exception as e:
        logger.warning(f"Read mention in {cid} error: {e}", exc_info=True)

    return result


@retry
def resolve_peer(client: Client, pid: Union[int, str]) -> Union[bool, InputPeerChannel, InputPeerUser, None]:
    # Get an input peer by id
    result = None

    try:
        result = client.resolve_peer(pid)
    except FloodWait as e:
        raise e
    except (PeerIdInvalid, UsernameInvalid, UsernameNotOccupied):
        return False
    except Exception as e:
        logger.warning(f"Resolve peer {pid} error: {e}", exc_info=True)

    return result


@retry
def send_document(client: Client, cid: int, document: str, file_ref: str = None, caption: str = "", mid: int = None,
                  markup: InlineKeyboardMarkup = None) -> Union[bool, Message, None]:
    # Send a document to a chat
    result = None

    try:
        result = client.send_document(
            chat_id=cid,
            document=document,
            file_ref=file_ref,
            caption=caption,
            parse_mode="html",
            reply_to_message_id=mid,
            reply_markup=markup
        )
    except FloodWait as e:
        raise e
    except ButtonDataInvalid:
        logger.warning(f"Send document {document} to {cid} - invalid markup: {markup}")
    except (ChannelInvalid, ChannelPrivate, ChatAdminRequired, PeerIdInvalid):
        return False
    except Exception as e:
        logger.warning(f"Send document {document} to {cid} error: {e}", exc_info=True)

    return result


@retry
def send_message(client: Client, cid: int, text: str, mid: int = None,
                 markup: InlineKeyboardMarkup = None) -> Union[bool, Message, None]:
    # Send a message to a chat
    result = None

    try:
        if not text.strip():
            return None

        result = client.send_message(
            chat_id=cid,
            text=text,
            parse_mode="html",
            disable_web_page_preview=True,
            reply_to_message_id=mid,
            reply_markup=markup
        )
    except FloodWait as e:
        raise e
    except ButtonDataInvalid:
        logger.warning(f"Send message to {cid} - invalid markup: {markup}")
    except (ChannelInvalid, ChannelPrivate, ChatAdminRequired, PeerIdInvalid):
        return False
    except Exception as e:
        logger.warning(f"Send message to {cid} error: {e}", exc_info=True)

    return result


@retry
def update_online_status(client: Client, offline: bool = False) -> bool:
    # Update account status
    result = False

    try:
        result = bool(client.send(UpdateStatus(offline=offline))) or True
    except FloodWait as e:
        raise e
    except Exception as e:
        logger.warning(f"Update online status error: {e}", exc_info=True)

    return result
