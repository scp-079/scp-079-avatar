# SCP-079-AVATAR - Get new joined member's profile photo
# Copyright (C) 2019 SCP-079 <https://scp-079.org>
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
from typing import Iterable, List, Optional, Union

from pyrogram import ChatMember, Client, InlineKeyboardMarkup, Message, User
from pyrogram.api.functions.messages import GetStickerSet, ReadMentions
from pyrogram.api.functions.users import GetFullUser
from pyrogram.api.types import InputPeerUser, InputPeerChannel, InputStickerSetShortName, StickerSet, UserFull
from pyrogram.api.types.messages import StickerSet as messages_StickerSet
from pyrogram.errors import ChannelInvalid, ChannelPrivate, FloodWait, PeerIdInvalid
from pyrogram.errors import UsernameInvalid, UsernameNotOccupied, UserNotParticipant

from .etc import t2t, wait_flood

# Enable logging
logger = logging.getLogger(__name__)


def download_media(client: Client, file_id: str, file_ref: str, file_path: str):
    # Download a media file
    result = None
    try:
        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                result = client.download_media(message=file_id, file_ref=file_ref, file_name=file_path)
            except FloodWait as e:
                flood_wait = True
                wait_flood(e)
    except Exception as e:
        logger.warning(f"Download media {file_id} to {file_path} error: {e}", exc_info=True)

    return result


def get_admins(client: Client, cid: int) -> Optional[Union[bool, List[ChatMember]]]:
    # Get a group's admins
    result = None
    try:
        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                result = client.get_chat_members(chat_id=cid, filter="administrators")
            except FloodWait as e:
                flood_wait = True
                wait_flood(e)
            except (PeerIdInvalid, ChannelInvalid, ChannelPrivate):
                return False
    except Exception as e:
        logger.warning(f"Get admins in {cid} error: {e}", exc_info=True)

    return result


def get_chat_member(client: Client, cid: int, uid: int) -> Optional[ChatMember]:
    # Get information about one member of a chat
    result = None
    try:
        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                result = client.get_chat_member(chat_id=cid, user_id=uid)
            except FloodWait as e:
                flood_wait = True
                wait_flood(e)
            except UserNotParticipant:
                result = False
    except Exception as e:
        logger.warning(f"Get chat member error: {e}", exc_info=True)

    return result


def get_users(client: Client, uids: Iterable[Union[int, str]]) -> Optional[List[User]]:
    # Get users
    result = None
    try:
        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                result = client.get_users(user_ids=uids)
            except FloodWait as e:
                flood_wait = True
                wait_flood(e)
            except PeerIdInvalid:
                return None
    except Exception as e:
        logger.warning(f"Get users error: {e}", exc_info=True)

    return result


def get_user_bio(client: Client, uid: int, normal: bool = False) -> Optional[str]:
    # Get user's bio
    result = None
    try:
        user_id = resolve_peer(client, uid)
        if user_id:
            flood_wait = True
            while flood_wait:
                flood_wait = False
                try:
                    user: UserFull = client.send(GetFullUser(id=user_id))
                    if user and user.about:
                        result = t2t(user.about, normal)
                except FloodWait as e:
                    flood_wait = True
                    wait_flood(e)
    except Exception as e:
        logger.warning(f"Get user bio error: {e}", exc_info=True)

    return result


def read_history(client: Client, cid: int) -> bool:
    # Mark messages in a chat as read
    try:
        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                client.read_history(chat_id=cid)
            except FloodWait as e:
                flood_wait = True
                wait_flood(e)

        return True
    except Exception as e:
        logger.warning(f"Read history error: {e}", exc_info=True)

    return False


def read_mention(client: Client, cid: int) -> bool:
    # Mark a mention as read
    try:
        peer = resolve_peer(client, cid)
        if peer:
            flood_wait = True
            while flood_wait:
                flood_wait = False
                try:
                    client.send(ReadMentions(peer=peer))
                except FloodWait as e:
                    flood_wait = True
                    wait_flood(e)

            return True
    except Exception as e:
        logger.warning(f"Read mention error: {e}", exc_info=True)

    return False


def resolve_peer(client: Client, pid: Union[int, str]) -> Optional[Union[bool, InputPeerChannel, InputPeerUser]]:
    # Get an input peer by id
    result = None
    try:
        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                result = client.resolve_peer(pid)
            except FloodWait as e:
                flood_wait = True
                wait_flood(e)
            except (PeerIdInvalid, UsernameInvalid, UsernameNotOccupied):
                return False
    except Exception as e:
        logger.warning(f"Resolve peer error: {e}", exc_info=True)

    return result


def send_document(client: Client, cid: int, document: str, file_ref: str = None, caption: str = "", mid: int = None,
                  markup: InlineKeyboardMarkup = None) -> Optional[Union[bool, Message]]:
    # Send a document to a chat
    result = None
    try:
        flood_wait = True
        while flood_wait:
            flood_wait = False
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
                flood_wait = True
                wait_flood(e)
            except (PeerIdInvalid, ChannelInvalid, ChannelPrivate):
                return False
    except Exception as e:
        logger.warning(f"Send document to {cid} error: {e}", exec_info=True)

    return result


def send_message(client: Client, cid: int, text: str, mid: int = None,
                 markup: InlineKeyboardMarkup = None) -> Optional[Union[bool, Message]]:
    # Send a message to a chat
    result = None
    try:
        if text.strip():
            flood_wait = True
            while flood_wait:
                flood_wait = False
                try:
                    result = client.send_message(
                        chat_id=cid,
                        text=text,
                        parse_mode="html",
                        disable_web_page_preview=True,
                        reply_to_message_id=mid,
                        reply_markup=markup
                    )
                except FloodWait as e:
                    flood_wait = True
                    wait_flood(e)
                except (PeerIdInvalid, ChannelInvalid, ChannelPrivate):
                    return False
    except Exception as e:
        logger.warning(f"Send message to {cid} error: {e}", exc_info=True)

    return result
