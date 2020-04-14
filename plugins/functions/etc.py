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
from html import escape
from random import choice, uniform
from string import ascii_letters, digits
from threading import Thread, Timer
from time import sleep, time
from typing import Any, Callable, Union
from unicodedata import normalize

from opencc import convert
from pyrogram import Message, User
from pyrogram.errors import FloodWait

from .. import glovar

# Enable logging
logger = logging.getLogger(__name__)


def code(text: Any) -> str:
    # Get a code text
    try:
        text = str(text).strip()

        if text:
            return f"<code>{escape(text)}</code>"
    except Exception as e:
        logger.warning(f"Code error: {e}", exc_info=True)

    return ""


def code_block(text: Any) -> str:
    # Get a code block text
    try:
        text = str(text).rstrip()

        if text:
            return f"<pre>{escape(text)}</pre>"
    except Exception as e:
        logger.warning(f"Code block error: {e}", exc_info=True)

    return ""


def delay(secs: int, target: Callable, args: list) -> bool:
    # Call a function with delay
    try:
        t = Timer(secs, target, args)
        t.daemon = True
        t.start()

        return True
    except Exception as e:
        logger.warning(f"Delay error: {e}", exc_info=True)

    return False


def general_link(text: Union[int, str], link: str) -> str:
    # Get a general link
    result = ""

    try:
        text = str(text).strip()
        link = link.strip()

        if text and link:
            result = f'<a href="{link}">{escape(text)}</a>'
    except Exception as e:
        logger.warning(f"General link error: {e}", exc_info=True)

    return result


def get_full_name(user: User, normal: bool = False, printable: bool = False) -> str:
    # Get user's full name
    text = ""

    try:
        if not user or user.is_deleted:
            return ""

        text = user.first_name

        if user.last_name:
            text += f" {user.last_name}"

        if text and normal:
            text = t2t(text, normal, printable)
    except Exception as e:
        logger.warning(f"Get full name error: {e}", exc_info=True)

    return text


def get_now() -> int:
    # Get time for now
    result = 0

    try:
        result = int(time())
    except Exception as e:
        logger.warning(f"Get now error: {e}", exc_info=True)

    return result


def get_text(message: Message, normal: bool = False, printable: bool = False) -> str:
    # Get message's text
    text = ""

    try:
        if not message:
            return ""

        the_text = message.text or message.caption

        if the_text:
            text += the_text

        if text:
            text = t2t(text, normal, printable)
    except Exception as e:
        logger.warning(f"Get text error: {e}", exc_info=True)

    return text


def lang(text: str) -> str:
    # Get the text
    result = ""

    try:
        result = glovar.lang.get(text, text)
    except Exception as e:
        logger.warning(f"Lang error: {e}", exc_info=True)

    return result


def mention_id(uid: int) -> str:
    # Get a ID mention string
    result = ""

    try:
        result = general_link(f"{uid}", f"tg://user?id={uid}")
    except Exception as e:
        logger.warning(f"Mention id error: {e}", exc_info=True)

    return result


def random_str(i: int) -> str:
    # Get a random string
    text = ""

    try:
        text = "".join(choice(ascii_letters + digits) for _ in range(i))
    except Exception as e:
        logger.warning(f"Random str error: {e}", exc_info=True)

    return text


def t2t(text: str, normal: bool, printable: bool, simplified: bool = False) -> str:
    # Convert the string, text to text
    try:
        if not text:
            return ""

        if normal:
            for special in ["spc", "spe"]:
                text = "".join(eval(f"glovar.{special}_dict").get(t, t) for t in text)

            text = normalize("NFKC", text)

        if printable:
            text = "".join(t for t in text if t.isprintable() or t in {"\n", "\r", "\t"})

        if (normal or simplified) and glovar.zh_cn:
            text = convert(text, config="t2s.json")
    except Exception as e:
        logger.warning(f"T2T error: {e}", exc_info=True)

    return text


def thread(target: Callable, args: tuple, daemon: bool = True) -> bool:
    # Call a function using thread
    try:
        t = Thread(target=target, args=args)
        t.daemon = daemon
        t.start()

        return True
    except Exception as e:
        logger.warning(f"Thread error: {e}", exc_info=True)

    return False


def wait_flood(e: FloodWait) -> bool:
    # Wait flood secs
    try:
        sleep(e.x + uniform(0.5, 1.0))

        return True
    except Exception as e:
        logger.warning(f"Wait flood error: {e}", exc_info=True)

    return False
