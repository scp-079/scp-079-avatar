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
from typing import Optional, Union

from pyrogram import Client, User

from .telegram import get_users

# Enable logging
logger = logging.getLogger(__name__)


def get_user(client: Client, uid: Union[int, str]) -> Optional[User]:
    # Get a user
    result = None

    try:
        result = get_users(client, [uid])

        if not result:
            return None

        result = result[0]
    except Exception as e:
        logger.warning(f"Get user error: {e}", exc_info=True)

    return result
