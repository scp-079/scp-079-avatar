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

from PIL import Image
from pyrogram import Client, Filters, Message

from .. import glovar
from ..functions.channel import share_user_avatar
from ..functions.etc import get_full_name, get_now, thread
from ..functions.file import delete_file, get_downloaded_path, save
from ..functions.filters import class_c, class_e, from_user, hide_channel, is_bio_text, is_declared_message
from ..functions.filters import is_new_user, is_nm_text
from ..functions.ids import init_user_id
from ..functions.receive import receive_add_bad, receive_add_except, receive_clear_data, receive_declared_message
from ..functions.receive import receive_regex, receive_remove_bad, receive_remove_except
from ..functions.receive import receive_text_data, receive_version_ask
from ..functions.timers import send_count
from ..functions.telegram import get_user_bio, read_history, read_mention

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.group & from_user & Filters.new_chat_members
                   & ~class_c & ~class_e)
def check_join(client: Client, message: Message) -> bool:
    # Check new joined user
    if glovar.locks["message"].acquire():
        try:
            gid = message.chat.id
            mid = message.message_id
            for new in message.new_chat_members:
                uid = new.id

                # Check if the user is Class D personnel
                if uid in glovar.bad_ids["users"]:
                    continue

                # Check if the user is bot
                if new.is_bot:
                    continue

                # Work with NOSPAM
                name = get_full_name(new)
                if name and is_nm_text(name):
                    continue

                bio = get_user_bio(client, new.username or new.id)
                if bio and is_bio_text(bio):
                    continue

                # Avoid check repeatedly
                if not is_new_user(new):
                    # Update user's join status
                    if init_user_id(uid):
                        glovar.user_ids[uid]["join"][gid] = get_now()
                        save("user_ids")

                    # Check declare status
                    if is_declared_message(None, message):
                        return True

                    # Check avatar
                    if new.photo:
                        file_id = new.photo.big_file_id
                        file_ref = ""
                        old_id = glovar.user_ids[uid]["avatar"]
                        if file_id != old_id:
                            glovar.user_ids[uid]["avatar"] = file_id
                            save("user_ids")
                            image_path = get_downloaded_path(client, file_id, file_ref)
                            if image_path:
                                image = Image.open(image_path)
                                share_user_avatar(client, gid, uid, mid, image)
                                delete_file(image_path)

            return True
        except Exception as e:
            logger.warning(f"Check join error: {e}", exc_info=True)
        finally:
            glovar.locks["message"].release()

    return False


@Client.on_message(~Filters.private & Filters.incoming & Filters.mentioned, group=1)
def mark_mention(client: Client, message: Message) -> bool:
    # Mark mention as read
    try:
        if message.chat:
            cid = message.chat.id
            thread(read_mention, (client, cid))

        return True
    except Exception as e:
        logger.warning(f"Mark mention error: {e}", exc_info=True)

    return False


@Client.on_message(~Filters.private & Filters.incoming, group=2)
def mark_message(client: Client, message: Message) -> bool:
    # Mark messages from groups and channels as read
    try:
        if message.chat:
            cid = message.chat.id
            thread(read_history, (client, cid))

        return True
    except Exception as e:
        logger.warning(f"Mark message error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.channel & hide_channel)
def process_data(client: Client, message: Message) -> bool:
    # Process the data in exchange channel
    try:
        data = receive_text_data(message)
        if data:
            sender = data["from"]
            receivers = data["to"]
            action = data["action"]
            action_type = data["type"]
            data = data["data"]
            # This will look awkward,
            # seems like it can be simplified,
            # but this is to ensure that the permissions are clear,
            # so it is intentionally written like this
            if glovar.sender in receivers:

                if sender == "CLEAN":

                    if action == "add":
                        if action_type == "bad":
                            receive_add_bad(sender, data)

                    elif action == "update":
                        if action_type == "declare":
                            receive_declared_message(data)

                elif sender == "HIDE":

                    if action == "version":
                        if action_type == "ask":
                            receive_version_ask(client, data)

                elif sender == "LANG":

                    if action == "add":
                        if action_type == "bad":
                            receive_add_bad(sender, data)

                    elif action == "update":
                        if action_type == "declare":
                            receive_declared_message(data)

                elif sender == "LONG":

                    if action == "add":
                        if action_type == "bad":
                            receive_add_bad(sender, data)

                    elif action == "update":
                        if action_type == "declare":
                            receive_declared_message(data)

                elif sender == "MANAGE":

                    if action == "add":
                        if action_type == "bad":
                            receive_add_bad(sender, data)
                        elif action_type == "except":
                            receive_add_except(client, data)

                    elif action == "clear":
                        receive_clear_data(action_type, data)

                    elif action == "remove":
                        if action_type == "bad":
                            receive_remove_bad(sender, data)
                        elif action_type == "except":
                            receive_remove_except(client, data)

                elif sender == "NOFLOOD":

                    if action == "add":
                        if action_type == "bad":
                            receive_add_bad(sender, data)

                    elif action == "update":
                        if action_type == "declare":
                            receive_declared_message(data)

                elif sender == "NOPORN":

                    if action == "add":
                        if action_type == "bad":
                            receive_add_bad(sender, data)

                    elif action == "update":
                        if action_type == "declare":
                            receive_declared_message(data)

                elif sender == "NOSPAM":

                    if action == "add":
                        if action_type == "bad":
                            receive_add_bad(sender, data)

                    elif action == "update":
                        if action_type == "declare":
                            receive_declared_message(data)

                elif sender == "RECHECK":

                    if action == "add":
                        if action_type == "bad":
                            receive_add_bad(sender, data)

                    elif action == "update":
                        if action_type == "declare":
                            receive_declared_message(data)

                elif sender == "REGEX":

                    if action == "regex":
                        if action_type == "update":
                            receive_regex(client, message, data)
                        elif action_type == "count":
                            if data == "ask":
                                send_count(client)

                elif sender == "USER":

                    if action == "remove":
                        if action_type == "bad":
                            receive_remove_bad(sender, data)

        return True
    except Exception as e:
        logger.warning(f"Process data error: {e}", exc_info=True)

    return False
