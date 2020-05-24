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
import pickle
from codecs import getdecoder
from configparser import RawConfigParser
from os import mkdir
from os.path import exists
from shutil import rmtree
from string import ascii_lowercase
from threading import Lock
from typing import Dict, List, Set, Union

from emoji import UNICODE_EMOJI
from yaml import safe_load

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.WARNING,
    filename="log",
    filemode="a"
)
logger = logging.getLogger(__name__)

# Read data from config.ini

# [bots]
avatar_id: int = 0
captcha_id: int = 0
clean_id: int = 0
index_id: int = 0
lang_id: int = 0
long_id: int = 0
noflood_id: int = 0
noporn_id: int = 0
nospam_id: int = 0
tip_id: int = 0
user_id: int = 0
warn_id: int = 0

# [channels]
debug_channel_id: int = 0
hide_channel_id: int = 0

# [custom]
project_link: str = ""
project_name: str = ""

# [emoji]
emoji_ad_single: int = 0
emoji_ad_total: int = 0
emoji_many: int = 0
emoji_protect: str = ""
emoji_wb_single: int = 0
emoji_wb_total: int = 0

# [encrypt]
key: Union[bytes, str] = ""
password: str = ""

# [language]
lang: str = ""
normalize: Union[bool, str] = ""

# [limit]
limit_length: int = 0
limit_message: int = 0

# [mode]
aio: Union[bool, str] = ""
backup: Union[bool, str] = ""

# [time]
date_reset: str = ""
time_begin: int = 0
time_check: int = 0
time_end: int = 0
time_new: int = 0
time_old: int = 0

try:
    config = RawConfigParser()
    config.read("config.ini")

    # [bots]
    avatar_id = int(config["bots"].get("avatar_id", str(avatar_id)))
    captcha_id = int(config["bots"].get("captcha_id", str(captcha_id)))
    clean_id = int(config["bots"].get("clean_id", str(clean_id)))
    index_id = int(config["bots"].get("index_id", str(index_id)))
    lang_id = int(config["bots"].get("lang_id", str(lang_id)))
    long_id = int(config["bots"].get("long_id", str(long_id)))
    noflood_id = int(config["bots"].get("noflood_id", str(noflood_id)))
    noporn_id = int(config["bots"].get("noporn_id", str(noporn_id)))
    nospam_id = int(config["bots"].get("nospam_id", str(nospam_id)))
    tip_id = int(config["bots"].get("tip_id", str(tip_id)))
    user_id = int(config["bots"].get("user_id", str(user_id)))
    warn_id = int(config["bots"].get("warn_id", str(warn_id)))

    # [channels]
    debug_channel_id = int(config["channels"].get("debug_channel_id", str(debug_channel_id)))
    hide_channel_id = int(config["channels"].get("hide_channel_id", str(hide_channel_id)))

    # [custom]
    project_link = config["custom"].get("project_link", project_link)
    project_name = config["custom"].get("project_name", project_name)

    # [emoji]
    emoji_ad_single = int(config["emoji"].get("emoji_ad_single", str(emoji_ad_single)))
    emoji_ad_total = int(config["emoji"].get("emoji_ad_total", str(emoji_ad_total)))
    emoji_many = int(config["emoji"].get("emoji_many", str(emoji_many)))
    emoji_protect = getdecoder("unicode_escape")(config["emoji"].get("emoji_protect", emoji_protect))[0]
    emoji_wb_single = int(config["emoji"].get("emoji_wb_single", str(emoji_wb_single)))
    emoji_wb_total = int(config["emoji"].get("emoji_wb_total", str(emoji_wb_total)))

    # [encrypt]
    key = config["encrypt"].get("key", key)
    key = key.encode("utf-8")
    password = config["encrypt"].get("password", password)

    # [language]
    lang = config["language"].get("lang", lang)
    normalize = config["language"].get("normalize", normalize)
    normalize = eval(normalize)

    # [limit]
    limit_length = int(config["limit"].get("limit_length", str(limit_length)))
    limit_message = int(config["limit"].get("limit_message", str(limit_message)))

    # [mode]
    aio = config["mode"].get("aio", aio)
    aio = eval(aio)
    backup = config["mode"].get("backup", backup)
    backup = eval(backup)

    # [time]
    date_reset = config["time"].get("date_reset", date_reset)
    time_begin = int(config["time"].get("time_begin", str(time_begin)))
    time_check = int(config["time"].get("time_check", str(time_check)))
    time_end = int(config["time"].get("time_end", str(time_end)))
    time_new = int(config["time"].get("time_new", str(time_new)))
    time_old = int(config["time"].get("time_old", str(time_old)))
except Exception as e:
    logger.warning(f"Read data from config.ini error: {e}", exc_info=True)

# Check
if (False
        # [bots]
        or avatar_id == 0
        or captcha_id == 0
        or clean_id == 0
        or index_id == 0
        or lang_id == 0
        or long_id == 0
        or noflood_id == 0
        or noporn_id == 0
        or nospam_id == 0
        or tip_id == 0
        or user_id == 0
        or warn_id == 0

        # [channels]
        or debug_channel_id == 0
        or hide_channel_id == 0

        # [custom]
        or project_link in {"", "[DATA EXPUNGED]"}
        or project_name in {"", "[DATA EXPUNGED]"}

        # [emoji]
        or emoji_ad_single == 0
        or emoji_ad_total == 0
        or emoji_many == 0
        or emoji_protect in {"", "[DATA EXPUNGED]"}
        or emoji_wb_single == 0
        or emoji_wb_total == 0

        # [encrypt]
        or key in {b"", b"[DATA EXPUNGED]", "", "[DATA EXPUNGED]"}
        or password in {"", "[DATA EXPUNGED]"}

        # [language]
        or lang in {"", "[DATA EXPUNGED]"}
        or normalize not in {False, True}

        # [limit]
        or limit_length == 0
        or limit_message == 0

        # [mode]
        or aio not in {False, True}
        or backup not in {False, True}

        # [time]
        or date_reset in {"", "[DATA EXPUNGED]"}
        or time_new == 0
        or time_old == 0):
    logger.critical("No proper settings")
    raise SystemExit("No proper settings")

# Language Dictionary
lang_dict: dict = {}

try:
    with open(f"languages/{lang}.yml", "r", encoding="utf-8") as f:
        lang_dict = safe_load(f)
except Exception as e:
    logger.critical(f"Reading language YAML file failed: {e}", exc_info=True)
    raise SystemExit("Reading language YAML file failed")

# Init

bot_ids: Set[int] = {avatar_id, captcha_id, clean_id, index_id, lang_id, long_id,
                     noflood_id, noporn_id, nospam_id, tip_id, user_id, warn_id}

declared_message_ids: Dict[int, Set[int]] = {}
# declared_message_ids = {
#     -10012345678: {123}
# }

default_user_status: Dict[str, Union[str, Dict[int, int]]] = {
    "avatar": "",
    "join": {},
    "message": {},
    "score": {
        "captcha": 0.0,
        "clean": 0.0,
        "lang": 0.0,
        "long": 0.0,
        "noflood": 0.0,
        "noporn": 0.0,
        "nospam": 0.0,
        "warn": 0.0
    }
}

emoji_set: Set[str] = set(UNICODE_EMOJI)

locks: Dict[str, Lock] = {
    "admin": Lock(),
    "message": Lock(),
    "receive": Lock(),
    "regex": Lock(),
    "white": Lock()
}

receivers: Dict[str, List[str]] = {
    "white": ["ANALYZE", "AVATAR", "CAPTCHA", "CLEAN", "INDEX", "LANG",
              "LONG", "MANAGE", "NOFLOOD", "NOPORN", "NOSPAM", "USER", "WATCH"]
}

regex: Dict[str, bool] = {
    "ad": False,
    "ban": False,
    "bio": False,
    "con": False,
    "iml": False,
    "nm": False,
    "pho": False,
    "spc": False,
    "spe": False
}

for c in ascii_lowercase:
    regex[f"ad{c}"] = False

sender: str = "AVATAR"

version: str = "0.2.4"

# Load data from pickle

# Init dir
try:
    rmtree("tmp")
except Exception as e:
    logger.info(f"Remove tmp error: {e}")

for path in ["data", "tmp"]:
    if not exists(path):
        mkdir(path)

# Init ids variables

admin_ids: Dict[int, Set[int]] = {}
# admin_ids = {
#     -10012345678: {12345678}
# }

bad_ids: Dict[str, Set[int]] = {
    "channels": set(),
    "users": set()
}
# bad_ids = {
#     "channels": {-10012345678},
#     "users": {12345678}
# }

deleted_ids: Dict[int, Set[int]] = {}
# deleted_ids = {
#     -10012345678: {123}
# }

except_ids: Dict[str, Set[str]] = {
    "long": set()
}
# except_ids = {
#     "long": {"content"}
# }

flooded_ids: Set[int] = set()
# flooded_ids = {-10012345678}

left_group_ids: Set[int] = set()
# left_group_ids = {-10012345678}

trust_ids: Dict[int, Set[int]] = {}
# trust_ids = {
#     -10012345678: {12345678}
# }

user_ids: Dict[int, Dict[str, Union[str, Dict[Union[int, str], Union[float, int, Set[int]]]]]] = {}
# user_ids = {
#     12345678: {
#         "avatar": "",
#         "join": {
#             -10012345678: 1512345678
#         },
#         "message": {
#             -10012345678: {123}
#         },
#         "score": {
#             "captcha": 0.0,
#             "clean": 0.0,
#             "lang": 0.0,
#             "long": 0.0,
#             "noflood": 0.0,
#             "noporn": 0.0,
#             "nospam": 0.0,
#             "warn": 0.0
#         }
#     }
# }

watch_ids: Dict[str, Dict[int, int]] = {
    "ban": {},
    "delete": {}
}
# watch_ids = {
#     "ban": {
#         12345678: 0
#     },
#     "delete": {
#         12345678: 0
#     }
# }

white_ids: Set[int] = set()
# white_ids = {12345678}

white_kicked_ids: Set[int] = set()
# white_kicked_ids = {87654321}

white_wait_ids: Dict[int, Set[int]] = {}
# white_wait_ids = {
#     12345678: {-10012345678}
# }

# Init word variables

for word_type in regex:
    locals()[f"{word_type}_words"]: Dict[str, Dict[str, Union[float, int]]] = {}

# type_words = {
#     "regex": 0
# }

# Load data
file_list: List[str] = ["admin_ids", "bad_ids", "deleted_ids", "except_ids", "flooded_ids", "left_group_ids",
                        "trust_ids", "user_ids", "watch_ids", "white_ids", "white_kicked_ids", "white_wait_ids"]
file_list += [f"{f}_words" for f in regex]

for file in file_list:
    try:
        try:
            if exists(f"data/{file}") or exists(f"data/.{file}"):
                with open(f"data/{file}", "rb") as f:
                    locals()[f"{file}"] = pickle.load(f)
            else:
                with open(f"data/{file}", "wb") as f:
                    pickle.dump(eval(f"{file}"), f)
        except Exception as e:
            logger.error(f"Load data {file} error: {e}", exc_info=True)

            with open(f"data/.{file}", "rb") as f:
                locals()[f"{file}"] = pickle.load(f)
    except Exception as e:
        logger.critical(f"Load data {file} backup error: {e}", exc_info=True)
        raise SystemExit("[DATA CORRUPTION]")

# Generate special characters dictionary
for special in ["spc", "spe"]:
    locals()[f"{special}_dict"]: Dict[str, str] = {}

    for rule in locals()[f"{special}_words"]:
        # Check keys
        if "[" not in rule:
            continue

        # Check value
        if "?#" not in rule:
            continue

        keys = rule.split("]")[0][1:]
        value = rule.split("?#")[1][1]

        for k in keys:
            locals()[f"{special}_dict"][k] = value

# Start program
copyright_text = (f"SCP-079-{sender} v{version}, Copyright (C) 2019-2020 SCP-079 <https://scp-079.org>\n"
                  "Licensed under the terms of the GNU General Public License v3 or later (GPLv3+)\n")
print(copyright_text)
