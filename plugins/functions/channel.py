# SCP-079-AVATAR - Get new joined member's profile photo
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
from json import dumps
from typing import List, Union

from PIL.Image import Image
from pyrogram import Client

from .. import glovar
from .etc import code_block, thread
from .file import crypt_file, data_to_file, delete_file, get_new_path
from .telegram import send_document, send_message

# Enable logging
logger = logging.getLogger(__name__)


def format_data(sender: str, receivers: List[str], action: str, action_type: str,
                data: Union[bool, dict, int, str] = None) -> str:
    # See https://scp-079.org/exchange/
    text = ""
    try:
        data = {
            "from": sender,
            "to": receivers,
            "action": action,
            "type": action_type,
            "data": data
        }
        text = code_block(dumps(data, indent=4))
    except Exception as e:
        logger.warning(f"Format data error: {e}", exc_info=True)

    return text


def send_help(client: Client, cid: int, text: str) -> bool:
    # Request HIDE to help to send a text in the channel
    try:
        file = data_to_file(text)
        share_data(
            client=client,
            receivers=["HIDE"],
            action="help",
            action_type="send",
            data=cid,
            file=file
        )
    except Exception as e:
        logger.warning(f"Send help error: {e}", exc_info=True)

    return False


def share_data(client: Client, receivers: List[str], action: str, action_type: str,
               data: Union[bool, dict, int, str] = None, file: str = None, encrypt: bool = True) -> bool:
    # Use this function to share data in the channel
    try:
        thread(
            target=share_data_thread,
            args=(client, receivers, action, action_type, data, file, encrypt)
        )

        return True
    except Exception as e:
        logger.warning(f"Share data error: {e}", exc_info=True)

    return False


def share_data_thread(client: Client, receivers: List[str], action: str, action_type: str,
                      data: Union[bool, dict, int, str] = None, file: str = None, encrypt: bool = True) -> bool:
    # Share data thread
    try:
        if glovar.sender in receivers:
            receivers.remove(glovar.sender)

        if not receivers:
            return True

        channel_id = glovar.hide_channel_id

        if file:
            text = format_data(
                sender=glovar.sender,
                receivers=receivers,
                action=action,
                action_type=action_type,
                data=data
            )

            if encrypt:
                # Encrypt the file, save to the tmp directory
                file_path = get_new_path()
                crypt_file("encrypt", file, file_path)
            else:
                # Send directly
                file_path = file

            result = send_document(client, channel_id, file_path, None, text)

            # Delete the tmp file
            if result:
                for f in {file, file_path}:
                    f.startswith("tmp/") and thread(delete_file, (f,))
        else:
            text = format_data(
                sender=glovar.sender,
                receivers=receivers,
                action=action,
                action_type=action_type,
                data=data
            )
            result = send_message(client, channel_id, text)

        # Sending failed due to channel issue
        if result is False:
            return True

        return True
    except Exception as e:
        logger.warning(f"Share data thread error: {e}", exc_info=True)

    return False


def share_regex_count(client: Client, word_type: str) -> bool:
    # Use this function to share regex count to REGEX
    try:
        if not glovar.regex.get(word_type):
            return True

        if not eval(f"glovar.{word_type}_words"):
            return True

        file = data_to_file(eval(f"glovar.{word_type}_words"))
        share_data(
            client=client,
            receivers=["REGEX"],
            action="regex",
            action_type="count",
            data=f"{word_type}_words",
            file=file
        )

        return True
    except Exception as e:
        logger.warning(f"Share regex update error: {e}", exc_info=True)

    return False


def share_user_avatar(client: Client, gid: int, uid: int, mid: int, image: Image) -> bool:
    # Share user's avatar to NOSPAM
    try:
        file = data_to_file(image)
        share_data(
            client=client,
            receivers=["NOSPAM"],
            action="update",
            action_type="avatar",
            data={
                "group_id": gid,
                "user_id": uid,
                "message_id": mid
            },
            file=file
        )

        return True
    except Exception as e:
        logger.warning(f"Share user avatar error: {e}", exc_info=True)
