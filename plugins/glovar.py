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
import pickle
from configparser import RawConfigParser
from os import mkdir
from os.path import exists
from shutil import rmtree
from threading import Lock
from typing import Dict, List, Set, Union

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING,
    filename='log',
    filemode='w'
)
logger = logging.getLogger(__name__)

# Read data from config.ini

# [bots]
avatar_id: int = 0
captcha_id: int = 0
clean_id: int = 0
lang_id: int = 0
long_id: int = 0
noflood_id: int = 0
noporn_id: int = 0
nospam_id: int = 0
recheck_id: int = 0
tip_id: int = 0
user_id: int = 0
warn_id: int = 0

# [channels]
debug_channel_id: int = 0
hide_channel_id: int = 0

# [custom]
backup: Union[str, bool] = ""
date_reset: str = ""
project_link: str = ""
project_name: str = ""
time_new: int = 0
zh_cn: Union[str, bool] = ""

# [encrypt]
key: Union[str, bytes] = ""
password: str = ""

try:
    config = RawConfigParser()
    config.read("config.ini")
    # [bots]
    avatar_id = int(config["bots"].get("avatar_id", avatar_id))
    captcha_id = int(config["bots"].get("captcha_id", captcha_id))
    clean_id = int(config["bots"].get("clean_id", clean_id))
    lang_id = int(config["bots"].get("lang_id", lang_id))
    long_id = int(config["bots"].get("long_id", long_id))
    noflood_id = int(config["bots"].get("noflood_id", noflood_id))
    noporn_id = int(config["bots"].get("noporn_id", noporn_id))
    nospam_id = int(config["bots"].get("nospam_id", nospam_id))
    recheck_id = int(config["bots"].get("recheck_id", recheck_id))
    tip_id = int(config["bots"].get("tip_id", tip_id))
    user_id = int(config["bots"].get("user_id", user_id))
    warn_id = int(config["bots"].get("warn_id", warn_id))
    # [channels]
    debug_channel_id = int(config["channels"].get("debug_channel_id", debug_channel_id))
    hide_channel_id = int(config["channels"].get("hide_channel_id", hide_channel_id))
    # [custom]
    backup = config["custom"].get("backup", backup)
    backup = eval(backup)
    date_reset = config["custom"].get("date_reset", date_reset)
    project_link = config["custom"].get("project_link", project_link)
    project_name = config["custom"].get("project_name", project_name)
    time_new = int(config["custom"].get("time_new", time_new))
    zh_cn = config["custom"].get("zh_cn", zh_cn)
    zh_cn = eval(zh_cn)
    # [encrypt]
    key = config["encrypt"].get("key", key)
    key = key.encode("utf-8")
    password = config["encrypt"].get("password", password)
except Exception as e:
    logger.warning(f"Read data from config.ini error: {e}", exc_info=True)

# Check
if (captcha_id == 0
        or avatar_id == 0
        or clean_id == 0
        or lang_id == 0
        or long_id == 0
        or noflood_id == 0
        or noporn_id == 0
        or nospam_id == 0
        or recheck_id == 0
        or tip_id == 0
        or user_id == 0
        or warn_id == 0
        or debug_channel_id == 0
        or hide_channel_id == 0
        or backup not in {False, True}
        or date_reset in {"", "[DATA EXPUNGED]"}
        or project_link in {"", "[DATA EXPUNGED]"}
        or project_name in {"", "[DATA EXPUNGED]"}
        or time_new == 0
        or zh_cn not in {False, True}
        or key in {"", b"[DATA EXPUNGED]"}
        or password in {"", "[DATA EXPUNGED]"}):
    logger.critical("No proper settings")
    raise SystemExit("No proper settings")

bot_ids: Set[int] = {avatar_id, captcha_id, clean_id, lang_id, long_id, noflood_id,
                     noporn_id, nospam_id, recheck_id, tip_id, user_id, warn_id}

# Languages
lang: Dict[str, str] = {
    # Admin
    "admin_project": (zh_cn and "项目管理员") or "Project Admin",
    # Basic
    "project": (zh_cn and "项目编号") or "Project",
    "colon": (zh_cn and "：") or ": ",
    "action": (zh_cn and "执行操作") or "Action",
    "clear": (zh_cn and "清空数据") or "Clear",
    "more": (zh_cn and "附加信息") or "Extra Info",
    "rollback": (zh_cn and "数据回滚") or "Rollback",
    "reset": (zh_cn and "重置数据") or "Reset Data",
    # Group
    "refresh": (zh_cn and "刷新群管列表") or "Refresh Admin Lists"
}

# Init

declared_message_ids: Dict[int, Set[int]] = {}
# declared_message_ids = {
#     -10012345678: {123}
# }

default_user_status: Dict[str, Union[str, Dict[int, int]]] = {
    "avatar": "",
    "join": {}
}

locks: Dict[str, Lock] = {
    "admin": Lock(),
    "message": Lock(),
    "regex": Lock()
}

regex: Dict[str, bool] = {
    "ad": False,
    "ban": False,
    "bio": False,
    "con": False,
    "nm": False
}

sender: str = "AVATAR"

version: str = "0.0.6"

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
    "users": set()
}
# bad_ids = {
#     "users": {12345678}
# }

except_ids: Dict[str, Set[str]] = {
    "long": set()
}
# except_ids = {
#     "long": {"content"}
# }

user_ids: Dict[int, Dict[str, Union[str, Dict[int, int]]]] = {}
# user_ids = {
#     12345678: {
#         "avatar": "",
#         "join": {
#             -10012345678: 1512345678
#         }
#     }
# }

# Init word variables

for word_type in regex:
    locals()[f"{word_type}_words"]: Dict[str, Dict[str, Union[float, int]]] = {}

# type_words = {
#     "regex": 0
# }

# Load data
file_list: List[str] = ["admin_ids", "bad_ids", "except_ids", "user_ids"]
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

# Start program
copyright_text = (f"SCP-079-{sender} v{version}, Copyright (C) 2019 SCP-079 <https://scp-079.org>\n"
                  "Licensed under the terms of the GNU General Public License v3 or later (GPLv3+)\n")
print(copyright_text)
