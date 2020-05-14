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
from typing import List

from pyrogram import ChatMember, Client

from .. import glovar
from .decorators import threaded
from .file import save
from .telegram import leave_chat

# Enable logging
logger = logging.getLogger(__name__)


@threaded
def leave_group(client: Client, gid: int) -> bool:
    # Leave a group, clear it's data
    result = False

    try:
        glovar.left_group_ids.add(gid)
        save("left_group_ids")
        leave_chat(client, gid, True)

        glovar.admin_ids.pop(gid, set())
        save("admin_ids")

        glovar.deleted_ids.pop(gid, set())
        save("deleted_ids")

        glovar.trust_ids.pop(gid, set())
        save("trust_ids")

        glovar.declared_message_ids.pop(gid, set())

        result = True
    except Exception as e:
        logger.warning(f"Leave group error: {e}", exc_info=True)

    return result


def save_admins(gid: int, admin_members: List[ChatMember]) -> bool:
    # Save the group's admin list
    result = False

    try:
        # Admin list
        glovar.admin_ids[gid] = {admin.user.id for admin in admin_members
                                 if (((not admin.user.is_bot and not admin.user.is_deleted)
                                      and admin.can_delete_messages
                                      and admin.can_restrict_members)
                                     or admin.status == "creator"
                                     or admin.user.id in glovar.bot_ids)}
        save("admin_ids")

        # Trust list
        glovar.trust_ids[gid] = {admin.user.id for admin in admin_members
                                 if ((not admin.user.is_bot and not admin.user.is_deleted)
                                     or admin.user.id in glovar.bot_ids)}
        save("trust_ids")

        result = True
    except Exception as e:
        logger.warning(f"Save admins error: {e}", exc_info=True)

    return result
