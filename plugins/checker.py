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
from typing import Dict, Union

# Enable logging
logger = logging.getLogger(__name__)


def check_all(values: dict) -> bool:
    # Check all values in config.ini
    error = ""

    error += check_bots(values["bots"])
    error += check_channels(values["channels"])
    error += check_custom(values["custom"])
    error += check_emoji(values["emoji"])
    error += check_encrypt(values["encrypt"])
    error += check_language(values["language"])
    error += check_limit(values["limit"])
    error += check_mode(values["mode"])
    error += check_time(values["time"])

    if not error:
        return True

    error = "-" * 24 + f"\nBot refused to start because:\n" + "-" * 24 + f"\n{error}" + "-" * 24
    logger.critical(error)
    raise SystemExit(error)


def check_bots(values: dict) -> str:
    # Check all values in bots section
    result = ""

    for key in values:
        if values[key] <= 0:
            result += f"[ERROR] [bots] {key} - should be a positive integer\n"

    return result


def check_channels(values: Dict[str, Union[bytes, int, str]]) -> str:
    # Check all values in channels section
    result = ""

    for key in values:
        if values[key] >= 0:
            result += f"[ERROR] [channels] {key} - should be a negative integer\n"
        elif key.endswith("channel_id") and not str(values[key]).startswith("-100"):
            result += f"[ERROR] [channels] {key} - please use a channel instead\n"
        elif not str(values[key]).startswith("-100"):
            result += f"[ERROR] [channels] {key} - please use a supergroup instead\n"

    return result


def check_custom(values: dict) -> str:
    # Check all values in custom section
    result = ""

    for key in values:
        if values[key] in {"", "[DATA EXPUNGED]"}:
            result += f"[ERROR] [custom] {key} - please fill something except [DATA EXPUNGED]\n"

    return result


def check_emoji(values: dict) -> str:
    # Check all values in emoji section
    result = ""

    for key in values:
        if key != "emoji_protect" and values[key] <= 0:
            result += f"[ERROR] [emoji] {key} - should be a positive integer"
        elif key == "emoji_protect" and values[key] in {"", "[DATA EXPUNGED]"}:
            result += f"[ERROR] [emoji] {key} - please fill something except [DATA EXPUNGED]\n"

    return result


def check_encrypt(values: dict) -> str:
    # Check all values in encrypt section
    result = ""

    for key in values:
        if key == "key" and key in {b"", b"[DATA EXPUNGED]", "", "[DATA EXPUNGED]"}:
            result += f"[ERROR] [encrypt] {key} - please fill a valid key\n"
        elif key == "password" and key in {"", "[DATA EXPUNGED]"}:
            result += f"[ERROR] [encrypt] {key} - please fill a valid password\n"

    return result


def check_language(values: dict) -> str:
    # Check all values in language section
    result = ""

    for key in values:
        if key == "lang" and values[key] in {"", "[DATA EXPUNGED]"}:
            result += f"[ERROR] [language] {key} - please fill something except [DATA EXPUNGED]\n"
        elif key == "normalize" and values[key] not in {False, True}:
            result += f"[ERROR] [language] {key} - please fill a valid boolean value\n"

    return result


def check_limit(values: dict) -> str:
    # Check all values in limit section
    result = ""

    for key in values:
        if values[key] <= 0:
            result += f"[ERROR] [limit] {key} - should be a positive integer\n"

    return result


def check_mode(values: dict) -> str:
    # Check all values in mode section
    result = ""

    for key in values:
        if values[key] not in {False, True}:
            result += f"[ERROR] [mode] {key} - please fill a valid boolean value\n"

    return result


def check_time(values: dict) -> str:
    # Check all values in time section
    result = ""

    for key in values:
        if key == "date_reset" and values[key] in {"", "[DATA EXPUNGED]"}:
            result += f"[ERROR] [time] {key} - please fill a correct format string\n"
        elif key in {"time_new", "time_old"} and values[key] <= 0:
            result += f"[ERROR] [time] {key} - should be a positive integer\n"

    return result
