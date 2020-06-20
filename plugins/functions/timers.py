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
from copy import deepcopy
from random import randint
from time import sleep

from PIL import Image
from pyrogram import Client
from pyrogram.errors import ChannelInvalid, ChannelPrivate, FloodWait, PeerIdInvalid

from .. import glovar
from .channel import send_help, share_data, share_regex_count, share_user_avatar
from .decorators import retry, threaded
from .etc import code, delay, general_link, get_now, lang, thread
from .file import data_to_file, delete_file, get_downloaded_path, save
from .filters import is_class_d_user, is_high_score_user, is_watch_user
from .group import leave_group, save_admins
from .user import get_user
from .telegram import get_admins, get_chat_member, get_members, update_online_status

# Enable logging
logger = logging.getLogger(__name__)


@threaded()
def backup_files(client: Client) -> bool:
    # Backup data files to BACKUP
    result = False

    try:
        for file in glovar.file_list:
            # Check
            if not eval(f"glovar.{file}"):
                continue

            # Share
            share_data(
                client=client,
                receivers=["BACKUP"],
                action="backup",
                action_type="data",
                data=file,
                file=f"data/{file}"
            )
            sleep(5)

        result = True
    except Exception as e:
        logger.warning(f"Backup error: {e}", exc_info=True)

    return result


def interval_hour_01(client: Client) -> bool:
    # Execute every hour
    result = False

    try:
        # Update online status
        delay(randint(0, 600), update_online_status, [client])
        result = True
    except Exception as e:
        logger.warning(f"Interval hour 01 error: {e}", exc_info=True)

    return result


def interval_min_15(client: Client) -> bool:
    # Execute every 15 minutes
    result = False

    try:
        # Basic data
        now = get_now()

        with glovar.locks["message"]:
            user_ids = deepcopy(glovar.user_ids)

        # Check user's avatar
        for uid in user_ids:
            # Do not check banned users
            if uid in glovar.bad_ids["users"]:
                continue

            # Check new joined users
            if not any(now - user_ids[uid]["join"][gid] < glovar.time_new for gid in user_ids[uid]["join"]):
                continue

            # Get user
            user = get_user(client, uid)

            # Check avatar
            if not user or not user.photo:
                continue

            # Get avatar
            file_id = user.photo.big_file_id
            file_ref = ""
            old_id = user_ids[uid]["avatar"]

            if file_id == old_id:
                continue

            glovar.user_ids[uid]["avatar"] = file_id
            save("user_ids")
            image_path = get_downloaded_path(client, file_id, file_ref)

            if not image_path:
                continue

            g_list = list(user_ids[uid]["join"])
            gid = sorted(g_list, key=lambda g: user_ids[uid]["join"][g], reverse=True)[0]

            with Image.open(image_path) as image:
                share_user_avatar(client, gid, uid, 0, image)

            thread(delete_file, (image_path,))

        result = True
    except Exception as e:
        logger.warning(f"Interval min 15 error: {e}", exc_info=True)

    return result


def reset_data(client: Client) -> bool:
    # Reset user data every month
    result = False

    glovar.locks["white"].acquire()
    glovar.locks["message"].acquire()

    try:
        glovar.bad_ids["users"] = set()
        save("bad_ids")

        glovar.deleted_ids = {}
        save("deleted_ids")

        glovar.user_ids = {}
        save("user_ids")

        glovar.watch_ids = {
            "ban": {},
            "delete": {}
        }
        save("watch_ids")

        glovar.white_kicked_ids = set()
        save("white_kicked_ids")

        glovar.white_wait_ids = {}
        save("white_wait_ids")

        # Send debug message
        text = (f"{lang('project')}{lang('colon')}{general_link(glovar.project_name, glovar.project_link)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('reset'))}\n")
        send_help(client, glovar.debug_channel_id, text)

        result = True
    except Exception as e:
        logger.warning(f"Reset data error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()
        glovar.locks["white"].release()

    return result


def send_count(client: Client) -> bool:
    # Send regex count to REGEX
    result = False

    glovar.locks["regex"].acquire()

    try:
        for word_type in glovar.regex:
            share_regex_count(client, word_type)
            word_list = list(eval(f"glovar.{word_type}_words"))

            for word in word_list:
                eval(f"glovar.{word_type}_words")[word] = 0

            save(f"{word_type}_words")

        result = True
    except Exception as e:
        logger.warning(f"Send count error: {e}", exc_info=True)
    finally:
        glovar.locks["regex"].release()

    return result


def update_admins(client: Client) -> bool:
    # Update admin list every day
    result = False

    glovar.locks["admin"].acquire()

    try:
        # Basic data
        group_list = list(glovar.admin_ids)

        for gid in group_list:
            admin_members = get_admins(client, gid)

            if admin_members is False:
                leave_group(client, gid)
                continue

            if not admin_members:
                continue

            # Save the admin list
            save_admins(gid, admin_members)

        result = True
    except Exception as e:
        logger.warning(f"Update admin error: {e}", exc_info=True)
    finally:
        glovar.locks["admin"].release()

    return result


def update_status(client: Client, the_type: str) -> bool:
    # Update running status to BACKUP
    result = False

    try:
        result = share_data(
            client=client,
            receivers=["BACKUP"],
            action="backup",
            action_type="status",
            data={
                "type": the_type,
                "backup": glovar.backup
            }
        )
    except Exception as e:
        logger.warning(f"Update status error: {e}", exc_info=True)

    return result


def white_check(client: Client) -> bool:
    # White list check
    result = False

    glovar.locks["white"].acquire()

    try:
        # Basic data
        now = get_now()

        # Get white ids
        for uid in list(glovar.white_wait_ids):
            glovar.user_ids[uid]["message"] = {}
            gids = glovar.white_wait_ids.pop(uid, set())

            if is_class_d_user(uid):
                continue

            if is_high_score_user(uid, False) > 1.2:
                continue

            if any(glovar.user_ids[uid]["score"][project] for project in ["noflood", "warn"]):
                continue

            if is_watch_user(uid, "delete", now) or is_watch_user(uid, "ban", now):
                continue

            if uid in glovar.white_kicked_ids:
                continue

            if not all(member and member.status == "member"
                       for member in [get_chat_member(client, gid, uid) for gid in gids]):
                continue

            glovar.white_ids.add(uid)

        save("user_ids")
        glovar.white_ids = glovar.white_ids | {uid for gid in list(glovar.trust_ids) for uid in glovar.trust_ids[gid]}
        save("white_ids")
        glovar.white_wait_ids = {}
        save("white_wait_ids")

        # Share white list
        file = data_to_file(glovar.white_ids)
        share_data(
            client=client,
            receivers=glovar.receivers["white"],
            action="add",
            action_type="white",
            file=file
        )

        # Get white wait ids
        with glovar.locks["message"]:
            user_ids = deepcopy(glovar.user_ids)

        for gid in list(glovar.admin_ids):
            white_wait(client, gid, user_ids, now)

        save("user_ids")
        save("white_wait_ids")

        result = True
    except Exception as e:
        logger.warning(f"White check error: {e}", exc_info=True)
    finally:
        glovar.locks["white"].release()

    return result


@retry
def white_wait(client: Client, gid: int, user_ids: dict, now: int) -> bool:
    # Get white wait ids
    result = False

    try:
        members = get_members(client, gid, "all")

        if not members:
            return False

        valid_members = filter(lambda m: m and m.user and user_ids.get(m.user.id, {}), members)

        for member in valid_members:
            if member.status != "member":
                continue

            uid = member.user.id
            joined = member.joined_date

            if now - joined < glovar.time_old:
                continue

            if is_class_d_user(uid):
                continue

            if is_high_score_user(uid, False) > 1.2:
                continue

            if any(glovar.user_ids[uid]["score"][project] for project in ["noflood", "warn"]):
                continue

            if is_watch_user(uid, "delete", now) or is_watch_user(uid, "ban", now):
                continue

            if uid in glovar.white_kicked_ids:
                continue

            if glovar.white_wait_ids.get(uid, set()):
                continue

            if not any(len(messages) > glovar.limit_message
                       for messages in [{mid for mid in user_ids[uid]["message"][group_id]
                                         if mid not in glovar.deleted_ids[group_id]}
                                        for group_id in list(user_ids[uid]["message"])]):
                continue

            glovar.user_ids[uid]["message"] = {}
            glovar.white_wait_ids[uid] = set(user_ids[uid]["message"])

        result = True
    except FloodWait as e:
        raise e
    except (ChannelInvalid, ChannelPrivate, PeerIdInvalid):
        leave_group(client, gid)
    except Exception as e:
        logger.warning(f"White wait error: {e}", exc_info=True)

    return result
