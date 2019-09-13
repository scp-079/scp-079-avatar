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


def share_data(client: Client, receivers: List[str], action: str, action_type: str, data: Union[bool, dict, int, str],
               file: str = None, encrypt: bool = True) -> bool:
    # Use this function to share data in the exchange channel
    try:
        if glovar.sender in receivers:
            receivers.remove(glovar.sender)

        if receivers:
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

                result = send_document(client, channel_id, file_path, text)
                # Delete the tmp file
                if result:
                    for f in {file, file_path}:
                        if "tmp/" in f:
                            thread(delete_file, (f,))
            else:
                text = format_data(
                    sender=glovar.sender,
                    receivers=receivers,
                    action=action,
                    action_type=action_type,
                    data=data
                )
                result = send_message(client, channel_id, text)

            if result is False:
                return True

        return True
    except Exception as e:
        logger.warning(f"Share data error: {e}", exc_info=True)

    return False


def share_user_avatar(client: Client, gid: int, uid: int, mid: int, image: Image) -> bool:
    # Share user's avatar to NOSPAM
    try:
        file = data_to_file(image)
        share_data(
            client=client,
            receivers=glovar.receivers["avatar"],
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
