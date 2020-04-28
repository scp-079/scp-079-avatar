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

from PIL import Image
from pyrogram import Client, Filters, Message

from typing import List

from .. import glovar
from ..functions.channel import share_user_avatar
from ..functions.decorators import threaded
from ..functions.etc import get_hour, get_now, get_text
from ..functions.file import delete_file, get_downloaded_path, save
from ..functions.filters import authorized_group, class_d, declared_message, detect_nospam, from_user, hide_channel
from ..functions.filters import is_class_d_user, is_declared_message, is_watch_user, is_valid_character, white_user
from ..functions.ids import init_group_id, init_user_id
from ..functions.receive import receive_add_bad, receive_add_except, receive_clear_data, receive_declared_message
from ..functions.receive import receive_kicked_user, receive_refresh, receive_regex, receive_remove_bad
from ..functions.receive import receive_remove_except, receive_remove_score, receive_remove_white, receive_rollback
from ..functions.receive import receive_status_ask, receive_user_score, receive_version_ask, receive_watch_user
from ..functions.receive import receive_text_data
from ..functions.timers import backup_files, send_count
from ..functions.telegram import read_history, read_mention

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.group & ~Filters.service & ~Filters.bot
                   & authorized_group
                   & from_user & ~class_d & ~white_user
                   & ~declared_message)
def check(_: Client, message: Message) -> bool:
    # Check message sent from users
    result = False

    glovar.locks["message"].acquire()

    try:
        # Basic data
        gid = message.chat.id
        uid = message.from_user.id
        mid = message.message_id
        hour = get_hour()
        now = message.date or get_now()

        # Check hour
        if (hour < glovar.time_begin < glovar.time_end
                or glovar.time_begin < glovar.time_end < hour
                or glovar.time_end < hour < glovar.time_begin):
            return False

        # Check white wait status
        if glovar.white_wait_ids.get(uid, set()):
            return False

        # Check watch status
        if is_watch_user(message.from_user, "ban", now) or is_watch_user(message.from_user, "delete", now):
            return False

        # Check message text
        message_text = "".join(t for t in get_text(message) if is_valid_character(t)).strip()

        if not message_text:
            return False

        if len(message_text) < glovar.limit_length:
            return False

        # Init user id
        if not init_user_id(uid):
            return False

        # Record message id
        if not glovar.user_ids[uid]["message"].get(gid, set()):
            glovar.user_ids[uid]["message"][gid] = set()

        glovar.user_ids[uid]["message"][gid].add(mid)
        save("user_ids")

        result = True
    except Exception as e:
        logger.warning(f"Check error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return result


@Client.on_message(Filters.incoming & Filters.group & Filters.new_chat_members
                   & authorized_group
                   & from_user & ~class_d & ~white_user
                   & ~declared_message)
def check_join(client: Client, message: Message) -> bool:
    # Check new joined user
    result = False

    glovar.locks["message"].acquire()

    try:
        # Basic data
        gid = message.chat.id
        mid = message.message_id
        now = message.date or get_now()

        # Check NOSPAM
        if glovar.nospam_id not in glovar.admin_ids.get(gid, set()):
            return False

        for new in message.new_chat_members:
            # Basic data
            uid = new.id

            # Check if the user is Class D personnel
            if is_class_d_user(new):
                continue

            # Check if the user is bot
            if new.is_bot:
                continue

            # Work with NOSPAM
            if detect_nospam(client, gid, new):
                continue

            # Check declare status
            if is_declared_message(None, message):
                return True

            # Init the user's status
            if not init_user_id(uid):
                continue

            # Update user's join status
            glovar.user_ids[uid]["join"][gid] = now
            save("user_ids")

            # Check avatar
            if not new.photo:
                continue

            file_id = new.photo.big_file_id
            file_ref = ""
            old_id = glovar.user_ids[uid]["avatar"]

            if file_id == old_id:
                continue

            glovar.user_ids[uid]["avatar"] = file_id
            save("user_ids")
            image_path = get_downloaded_path(client, file_id, file_ref)

            if not image_path:
                continue

            image = Image.open(image_path)
            share_user_avatar(client, gid, uid, mid, image)
            delete_file(image_path)

        result = True
    except Exception as e:
        logger.warning(f"Check join error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return result


@Client.on_message(Filters.incoming & Filters.channel & Filters.mentioned, group=1)
@threaded()
def mark_mention(client: Client, message: Message) -> bool:
    # Mark mention as read
    result = False

    try:
        if not message.chat:
            return False

        cid = message.chat.id

        if cid != glovar.hide_channel_id:
            return False

        read_mention(client, cid)
        result = True
    except Exception as e:
        logger.warning(f"Mark mention error: {e}", exc_info=True)

    return result


@Client.on_message(Filters.incoming & Filters.channel, group=2)
@threaded()
def mark_message(client: Client, message: Message) -> bool:
    # Mark messages as read
    result = False

    try:
        if not message.chat:
            return False

        cid = message.chat.id

        if cid != glovar.hide_channel_id:
            return False

        read_history(client, cid)
        result = True
    except Exception as e:
        logger.warning(f"Mark message error: {e}", exc_info=True)

    return result


@Client.on_message((Filters.incoming or glovar.aio) & Filters.channel
                   & hide_channel)
def process_data(client: Client, message: Message) -> bool:
    # Process the data in exchange channel
    result = False

    glovar.locks["receive"].acquire()

    try:
        data = receive_text_data(message)

        if not data:
            return False

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

            if sender == "CAPTCHA":

                if action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)
                    elif action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "CLEAN":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(sender, data)
                    elif action_type == "watch":
                        receive_watch_user(data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)
                    elif action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "HIDE":

                if action == "version":
                    if action_type == "ask":
                        receive_version_ask(client, data)

            elif sender == "LANG":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(sender, data)
                    elif action_type == "watch":
                        receive_watch_user(data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)
                    elif action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "LONG":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(sender, data)
                    elif action_type == "watch":
                        receive_watch_user(data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)
                    elif action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "MANAGE":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(sender, data)
                    elif action_type == "except":
                        receive_add_except(client, data)

                elif action == "backup":

                    if action_type == "now":
                        backup_files(client)
                    elif action_type == "rollback":
                        receive_rollback(client, message, data)

                elif action == "clear":
                    receive_clear_data(client, action_type, data)

                elif action == "remove":
                    if action_type == "bad":
                        receive_remove_bad(data)
                    elif action_type == "except":
                        receive_remove_except(client, data)
                    elif action_type == "score":
                        receive_remove_score(data)
                    elif action_type == "white":
                        receive_remove_white(data)

                elif action == "status":
                    if action_type == "ask":
                        receive_status_ask(client, data)

                elif action == "update":
                    if action_type == "refresh":
                        receive_refresh(client, data)

            elif sender == "NOFLOOD":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(sender, data)
                    elif action_type == "watch":
                        receive_watch_user(data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)
                    elif action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "NOPORN":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(sender, data)
                    elif action_type == "watch":
                        receive_watch_user(data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)
                    elif action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "NOSPAM":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(sender, data)
                    elif action_type == "watch":
                        receive_watch_user(data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)
                    elif action_type == "score":
                        receive_user_score(sender, data)

            elif sender == "REGEX":

                if action == "regex":
                    if action_type == "update":
                        receive_regex(client, message, data)
                    elif action_type == "count":
                        data == "ask" and send_count(client)

            elif sender == "USER":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(sender, data)

        elif "USER" in receivers:

            if sender == "WARN":

                if action == "help":
                    if action_type == "delete":
                        receive_kicked_user(client, data)

        result = True
    except Exception as e:
        logger.warning(f"Process data error: {e}", exc_info=True)
    finally:
        glovar.locks["receive"].release()

    return result


@Client.on_deleted_messages()
def deleted(_: Client, messages: List[Message]) -> bool:
    # Deleted messages
    result = False

    glovar.locks["message"].acquire()

    try:
        group_list = set(glovar.admin_ids)

        for message in messages:
            if not message.chat:
                continue

            gid = message.chat.id
            mid = message.message_id

            if gid in glovar.left_group_ids:
                continue

            if gid not in group_list:
                continue

            if not init_group_id(gid):
                continue

            glovar.deleted_ids[gid].add(mid)

        save("deleted_ids")

        result = True
    except Exception as e:
        logger.warning(f"Deleted error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return result
