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
from time import sleep

from pyrogram import Client

from .. import glovar
from .channel import share_data, share_regex_count
from .file import save
from .telegram import get_admins

# Enable logging
logger = logging.getLogger(__name__)


def backup_files(client: Client) -> bool:
    # Backup data files to BACKUP
    try:
        for file in glovar.file_list:
            try:
                share_data(
                    client=client,
                    receivers=["BACKUP"],
                    action="backup",
                    action_type="data",
                    data=file,
                    file=f"data/{file}"
                )
                sleep(5)
            except Exception as e:
                logger.warning(f"Send backup file {file} error: {e}", exc_info=True)

        return True
    except Exception as e:
        logger.warning(f"Backup error: {e}", exc_info=True)

    return False


def reset_data() -> bool:
    # Reset user data every month
    try:
        glovar.bad_ids = {
            "users": set()
        }
        save("bad_ids")

        glovar.user_ids = {}
        save("user_ids")

        return True
    except Exception as e:
        logger.warning(f"Reset data error: {e}", exc_info=True)

    return False


def send_count(client: Client) -> bool:
    # Send regex count to REGEX
    if glovar.locks["regex"].acquire():
        try:
            for word_type in glovar.regex:
                share_regex_count(client, word_type)
                word_list = list(eval(f"glovar.{word_type}_words"))
                for word in word_list:
                    eval(f"glovar.{word_type}_words")[word] = 0

                save(f"{word_type}_words")

            return True
        except Exception as e:
            logger.warning(f"Send count error: {e}", exc_info=True)
        finally:
            glovar.locks["regex"].release()

    return False


def update_admins(client: Client) -> bool:
    # Update admin list every day
    if glovar.locks["admin"].acquire():
        try:
            group_list = list(glovar.admin_ids)
            for gid in group_list:
                try:
                    admin_members = get_admins(client, gid)
                    if admin_members and any([admin.user.is_self for admin in admin_members]):
                        glovar.admin_ids[gid] = {admin.user.id for admin in admin_members
                                                 if ((not admin.user.is_bot and not admin.user.is_deleted)
                                                     or admin.user.id in glovar.bot_ids)}

                        save("admin_ids")
                except Exception as e:
                    logger.warning(f"Update admin in {gid} error: {e}", exc_info=True)

            return True
        finally:
            glovar.locks["admin"].release()

    return False


def update_status(client: Client, the_type: str) -> bool:
    # Update running status to BACKUP
    try:
        share_data(
            client=client,
            receivers=["BACKUP"],
            action="backup",
            action_type="status",
            data={
                "type": the_type,
                "backup": glovar.backup
            }
        )

        return True
    except Exception as e:
        logger.warning(f"Update status error: {e}", exc_info=True)

    return False
