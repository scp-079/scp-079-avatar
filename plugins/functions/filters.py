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
import re
from copy import deepcopy

from pyrogram import Filters, Message

from .. import glovar
from .ids import init_group_id
from .file import save

# Enable logging
logger = logging.getLogger(__name__)


def is_class_c(_, message: Message) -> bool:
    # Check if the message is Class C object
    try:
        if message.from_user:
            # Basic data
            uid = message.from_user.id
            gid = message.chat.id

            # Init the group
            if not init_group_id(gid):
                return False

            # Check permission
            if uid in glovar.admin_ids[gid] or uid in glovar.bot_ids or message.from_user.is_self:
                return True
    except Exception as e:
        logger.warning(f"Is class c error: {e}", exc_info=True)

    return False


def is_class_d(_, message: Message) -> bool:
    # Check if the message is Class D object
    try:
        if message.from_user:
            uid = message.from_user.id
            if uid in glovar.bad_ids["users"]:
                return True
    except Exception as e:
        logger.warning(f"Is class d error: {e}", exc_info=True)

    return False


def is_class_e(_, message: Message) -> bool:
    # Check if the message is Class E object
    try:
        if message.from_user:
            # All groups' admins
            uid = message.from_user.id
            admin_ids = deepcopy(glovar.admin_ids)
            for gid in admin_ids:
                if uid in admin_ids[gid]:
                    return True
    except Exception as e:
        logger.warning(f"Is class e error: {e}", exc_info=True)

    return False


def is_declared_message(_, message: Message) -> bool:
    # Check if the message is declared by other bots
    try:
        if message.chat:
            gid = message.chat.id
            mid = message.message_id
            return is_declared_message_id(gid, mid)
    except Exception as e:
        logger.warning(f"Is declared message error: {e}", exc_info=True)

    return False


def is_from_user(_, message: Message) -> bool:
    # Check if the message is sent from a user
    try:
        if message.from_user:
            return True
    except Exception as e:
        logger.warning(f"Is from user error: {e}", exc_info=True)

    return False


def is_hide_channel(_, message: Message) -> bool:
    # Check if the message is sent from the hide channel
    try:
        if message.chat:
            cid = message.chat.id
            if cid == glovar.hide_channel_id:
                return True
    except Exception as e:
        logger.warning(f"Is hide channel error: {e}", exc_info=True)

    return False


class_c = Filters.create(
    name="Class C",
    func=is_class_c
)

class_d = Filters.create(
    name="Class D",
    func=is_class_d
)

class_e = Filters.create(
    name="Class E",
    func=is_class_e
)

declared_message = Filters.create(
    func=is_declared_message,
    name="Declared message"
)

from_user = Filters.create(
    func=is_from_user,
    name="From User"
)

hide_channel = Filters.create(
    func=is_hide_channel,
    name="Hide Channel"
)


def is_ban_text(text: str) -> bool:
    # Check if the text is ban text
    try:
        if is_regex_text("ban", text):
            return True

        if is_regex_text("ad", text) and (is_regex_text("con", text) or is_regex_text("iml", text)):
            return True
    except Exception as e:
        logger.warning(f"Is ban text error: {e}", exc_info=True)

    return False


def is_bio_text(text: str) -> bool:
    # Check if the text is bio text
    try:
        if is_regex_text("bio", text):
            return True

        if is_ban_text(text):
            return True
    except Exception as e:
        logger.warning(f"Is bio text error: {e}", exc_info=True)

    return False


def is_declared_message_id(gid: int, mid: int) -> bool:
    # Check if the message's ID is declared by other bots
    try:
        if mid in glovar.declared_message_ids.get(gid, set()):
            return True
    except Exception as e:
        logger.warning(f"Is declared message id error: {e}", exc_info=True)

    return False


def is_nm_text(text: str) -> bool:
    # Check if the text is nm text
    try:
        if (is_regex_text("nm", text)
                or is_regex_text("ban", text)
                or (is_regex_text("ad", text) and is_regex_text("con", text))
                or is_regex_text("bio", text)):
            return True
    except Exception as e:
        logger.warning(f"Is nm text error: {e}", exc_info=True)

    return False


def is_regex_text(word_type: str, text: str, again: bool = False) -> bool:
    # Check if the text hit the regex rules
    result = False
    try:
        if text:
            if not again:
                text = re.sub(r"\s{2,}", " ", text)
            elif " " in text:
                text = re.sub(r"\s", "", text)
            else:
                return False
        else:
            return False

        for word in list(eval(f"glovar.{word_type}_words")):
            if re.search(word, text, re.I | re.S | re.M):
                result = True

            # Match, count and return
            if result:
                count = eval(f"glovar.{word_type}_words").get(word, 0)
                count += 1
                eval(f"glovar.{word_type}_words")[word] = count
                save(f"{word_type}_words")
                return result

        # Try again
        return is_regex_text(word_type, text, True)
    except Exception as e:
        logger.warning(f"Is regex text error: {e}", exc_info=True)

    return result
