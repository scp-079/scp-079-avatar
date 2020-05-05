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
from copy import deepcopy
from json import loads
from typing import Any

from pyrogram import Client, Message

from .. import glovar
from .channel import send_help, share_data
from .etc import code, crypt_str, general_link, get_int, get_text, lang, mention_id
from .file import crypt_file, data_to_file, delete_file, get_new_path, get_downloaded_path, save
from .ids import init_group_id, init_user_id
from .timers import update_admins
from .user import get_user

# Enable logging
logger = logging.getLogger(__name__)


def receive_add_bad(sender: str, data: dict) -> bool:
    # Receive bad objects that other bots shared
    result = False

    try:
        # Basic data
        the_id = data["id"]
        the_type = data["type"]

        # Receive bad channel
        if sender == "MANAGE" and the_type == "channel":
            glovar.bad_ids["channels"].add(the_id)

        # Receive bad user
        elif the_type == "user":
            glovar.bad_ids["users"].add(the_id)

        save("bad_ids")

        return True
    except Exception as e:
        logger.warning(f"Receive add bad error: {e}", exc_info=True)

    return result


def receive_add_except(client: Client, data: dict) -> bool:
    # Receive a object and add it to except list
    result = False

    try:
        # Basic data
        the_id = data["id"]
        the_type = data["type"]

        # Receive except content
        if the_type not in {"long"}:
            return False

        the_user = get_user(client, the_id)

        if not the_user or not the_user.photo:
            return False

        file_id = the_user.photo.big_file_id
        glovar.except_ids["long"].add(file_id)
        save("except_ids")

        result = True
    except Exception as e:
        logger.warning(f"Receive add except error: {e}", exc_info=True)

    return result


def receive_flood_users(client: Client, message: Message) -> bool:
    # Receive flood users' status
    result = False

    glovar.locks["message"].acquire()

    try:
        users = receive_file_data(client, message)

        if users is None:
            return False

        for uid in list(users):
            if not init_user_id(uid):
                continue

            glovar.user_ids[uid]["join"] -= users[uid]["groups"]
            glovar.user_ids[uid]["score"]["captcha"] = users[uid]["score"]

        save("user_ids")
    except Exception as e:
        logger.warning(f"Receive flood users error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return result


def receive_captcha_kicked_user(data: dict) -> bool:
    # Receive CAPTCHA kicked user
    result = False

    glovar.locks["message"].acquire()

    try:
        # Basic data
        gid = data["group_id"]
        uid = data["user_id"]

        # Check user status
        if not glovar.user_ids.get(uid, {}):
            return True

        glovar.user_ids[uid]["join"].pop(gid, 0)
        save("user_ids")
    except Exception as e:
        logger.warning(f"Receive captcha kicked user error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return result


def receive_clear_data(client: Client, data_type: str, data: dict) -> bool:
    # Receive clear data command
    result = False

    glovar.locks["message"].acquire()

    try:
        # Basic data
        aid = data["admin_id"]
        the_type = data["type"]

        # Clear bad data
        if data_type == "bad":
            if the_type == "channels":
                glovar.bad_ids["channels"] = set()
            elif the_type == "users":
                glovar.bad_ids["users"] = set()

            save("bad_ids")

        # Clear except data
        elif data_type == "except":
            if the_type == "long":
                glovar.except_ids["long"] = set()

            save("except_ids")

        # Clear user data
        elif data_type == "user":
            if the_type == "all":
                glovar.user_ids = {}
            elif the_type == "new":
                for uid in list(glovar.user_ids):
                    glovar.user_ids[uid]["join"] = {}

            save("user_ids")

        # Clear watch data
        elif data_type == "watch":
            if the_type == "all":
                glovar.watch_ids = {
                    "ban": {},
                    "delete": {}
                }
            elif the_type == "ban":
                glovar.watch_ids["ban"] = {}
            elif the_type == "delete":
                glovar.watch_ids["delete"] = {}

            save("watch_ids")

        # Send debug message
        text = (f"{lang('project')}{lang('colon')}{general_link(glovar.project_name, glovar.project_link)}\n"
                f"{lang('admin_project')}{lang('colon')}{mention_id(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('clear'))}\n"
                f"{lang('more')}{lang('colon')}{code(f'{data_type} {the_type}')}\n")
        send_help(client, glovar.debug_channel_id, text)
    except Exception as e:
        logger.warning(f"Receive clear data: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return result


def receive_declared_message(data: dict) -> bool:
    # Update declared message's id
    result = False

    try:
        # Basic data
        gid = data["group_id"]
        mid = data["message_id"]

        if not glovar.admin_ids.get(gid):
            return False

        if init_group_id(gid):
            glovar.declared_message_ids[gid].add(mid)

        result = True
    except Exception as e:
        logger.warning(f"Receive declared message error: {e}", exc_info=True)

    return result


def receive_file_data(client: Client, message: Message, decrypt: bool = True) -> Any:
    # Receive file's data from exchange channel
    result = None

    try:
        if not message.document:
            return None

        file_id = message.document.file_id
        file_ref = message.document.file_ref
        path = get_downloaded_path(client, file_id, file_ref)

        if not path:
            return None

        if decrypt:
            # Decrypt the file, save to the tmp directory
            path_decrypted = get_new_path()
            crypt_file("decrypt", path, path_decrypted)
            path_final = path_decrypted
        else:
            # Read the file directly
            path_decrypted = ""
            path_final = path

        with open(path_final, "rb") as f:
            result = pickle.load(f)

        for f in {path, path_decrypted}:
            delete_file(f)
    except Exception as e:
        logger.warning(f"Receive file error: {e}", exc_info=True)

    return result


def receive_refresh(client: Client, data: int) -> bool:
    # Receive refresh
    result = False

    try:
        # Basic data
        aid = data

        # Update admins
        update_admins(client)

        # Send debug message
        text = (f"{lang('project')}{lang('colon')}{general_link(glovar.project_name, glovar.project_link)}\n"
                f"{lang('admin_project')}{lang('colon')}{mention_id(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('refresh'))}\n")
        send_help(client, glovar.debug_channel_id, text)

        result = True
    except Exception as e:
        logger.warning(f"Receive refresh error: {e}", exc_info=True)

    return result


def receive_regex(client: Client, message: Message, data: str) -> bool:
    # Receive regex
    result = False

    glovar.locks["regex"].acquire()

    try:
        file_name = data
        word_type = file_name.split("_")[0]

        if word_type not in glovar.regex:
            return False

        words_data = receive_file_data(client, message)

        if words_data is None:
            return False

        pop_set = set(eval(f"glovar.{file_name}")) - set(words_data)
        new_set = set(words_data) - set(eval(f"glovar.{file_name}"))

        for word in pop_set:
            eval(f"glovar.{file_name}").pop(word, 0)

        for word in new_set:
            eval(f"glovar.{file_name}")[word] = 0

        save(file_name)

        # Regenerate special characters dictionary if possible
        if file_name not in {"spc_words", "spe_words"}:
            return False

        special = file_name.split("_")[0]
        exec(f"glovar.{special}_dict = {{}}")

        for rule in words_data:
            # Check keys
            if "[" not in rule:
                continue

            # Check value
            if "?#" not in rule:
                continue

            keys = rule.split("]")[0][1:]
            value = rule.split("?#")[1][1]

            for k in keys:
                eval(f"glovar.{special}_dict")[k] = value

        result = True
    except Exception as e:
        logger.warning(f"Receive regex error: {e}", exc_info=True)
    finally:
        glovar.locks["regex"].release()

    return result


def receive_remove_bad(data: dict) -> bool:
    # Receive removed bad objects
    result = False

    try:
        # Basic data
        the_id = data["id"]
        the_type = data["type"]

        # Remove bad channel
        if the_type == "channel":
            glovar.bad_ids["channels"].discard(the_id)

        # Remove bad user
        elif the_type == "user":
            glovar.bad_ids["users"].discard(the_id)
            glovar.watch_ids["ban"].pop(the_id, {})
            glovar.watch_ids["delete"].pop(the_id, {})
            save("watch_ids")
            glovar.user_ids[the_id] = deepcopy(glovar.default_user_status)
            save("user_ids")

        save("bad_ids")

        result = True
    except Exception as e:
        logger.warning(f"Receive remove bad error: {e}", exc_info=True)

    return result


def receive_remove_except(client: Client, data: dict) -> bool:
    # Receive a object and remove it from except list
    result = False

    try:
        # Basic data
        the_id = data["id"]
        the_type = data["type"]

        # Receive except content
        if the_type not in {"long"}:
            return False

        the_user = get_user(client, the_id)

        if not the_user or not the_user.photo:
            return False

        file_id = the_user.photo.big_file_id
        glovar.except_ids["long"].discard(file_id)
        save("except_ids")

        result = True
    except Exception as e:
        logger.warning(f"Receive remove except error: {e}", exc_info=True)

    return result


def receive_remove_score(data: int) -> bool:
    # Receive remove user's score
    result = False

    glovar.locks["message"].acquire()

    try:
        # Basic data
        uid = data

        if not glovar.user_ids.get(uid):
            return False

        glovar.user_ids[uid] = deepcopy(glovar.default_user_status)
        save("user_ids")

        result = True
    except Exception as e:
        logger.warning(f"Receive remove score error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return result


def receive_remove_watch(data: int) -> bool:
    # Receive removed watching users
    result = False

    try:
        # Basic data
        uid = data

        # Reset watch status
        glovar.watch_ids["ban"].pop(uid, 0)
        glovar.watch_ids["delete"].pop(uid, 0)
        save("watch_ids")

        result = True
    except Exception as e:
        logger.warning(f"Receive remove watch error: {e}", exc_info=True)

    return result


def receive_remove_white(data: int) -> bool:
    # Receive removed withe users
    result = False

    glovar.locks["white"].acquire()

    try:
        # Basic data
        uid = data

        if not init_user_id(uid):
            return False

        # White ids
        glovar.white_ids.discard(uid)
        save("white_ids")

        # Wait ids
        glovar.white_wait_ids.pop(uid, {})
        save("white_wait_ids")

        # User ids
        glovar.user_ids[uid]["message"] = {}
        save("user_ids")

        result = True
    except Exception as e:
        logger.warning(f"Receive remove white error: {e}", exc_info=True)
    finally:
        glovar.locks["white"].release()

    return result


def receive_rollback(client: Client, message: Message, data: dict) -> bool:
    # Receive rollback data
    result = False

    try:
        # Basic data
        aid = data["admin_id"]
        the_type = data["type"]
        the_data = receive_file_data(client, message)

        if the_data is None:
            return False

        exec(f"glovar.{the_type} = the_data")
        save(the_type)

        # Send debug message
        text = (f"{lang('project')}{lang('colon')}{general_link(glovar.project_name, glovar.project_link)}\n"
                f"{lang('admin_project')}{lang('colon')}{mention_id(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('rollback'))}\n"
                f"{lang('more')}{lang('colon')}{code(the_type)}\n")
        send_help(client, glovar.debug_channel_id, text)

        result = True
    except Exception as e:
        logger.warning(f"Receive rollback error: {e}", exc_info=True)

    return result


def receive_status_ask(client: Client, data: dict) -> bool:
    # Receive status request
    result = False

    glovar.locks["white"].acquire()
    glovar.locks["message"].acquire()

    try:
        # Basic data
        aid = data["admin_id"]
        mid = data["message_id"]

        watching_users_count = len([uid for uid in glovar.user_ids if glovar.user_ids[uid].get("message", {})])
        waiting_users_count = len(glovar.white_wait_ids)
        white_users_count = len(glovar.white_ids)

        status = {
            lang("watching_users"): f"{watching_users_count} {lang('members')}",
            lang("waiting_users"): f"{waiting_users_count} {lang('members')}",
            lang("white_users"): f"{white_users_count} {lang('members')}"
        }

        file = data_to_file(status)

        result = share_data(
            client=client,
            receivers=["MANAGE"],
            action="status",
            action_type="reply",
            data={
                "admin_id": aid,
                "message_id": mid
            },
            file=file
        )
    except Exception as e:
        logger.warning(f"Receive status ask error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()
        glovar.locks["white"].release()

    return result


def receive_text_data(message: Message) -> dict:
    # Receive text's data from exchange channel
    result = {}

    try:
        text = get_text(message)

        if not text:
            return {}

        result = loads(text)
    except Exception as e:
        logger.warning(f"Receive text data error: {e}")

    return result


def receive_user_score(project: str, data: dict) -> bool:
    # Receive and update user's score
    result = False

    glovar.locks["message"].acquire()

    try:
        # Basic data
        project = project.lower()
        uid = data["id"]

        if not init_user_id(uid):
            return False

        score = data["score"]
        glovar.user_ids[uid]["score"][project] = score
        save("user_ids")

        result = True
    except Exception as e:
        logger.warning(f"Receive user score error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return result


def receive_version_ask(client: Client, data: dict) -> bool:
    # Receive version info request
    result = False

    try:
        # Basic data
        aid = data["admin_id"]
        mid = data["message_id"]

        result = share_data(
            client=client,
            receivers=["HIDE"],
            action="version",
            action_type="reply",
            data={
                "admin_id": aid,
                "message_id": mid,
                "version": glovar.version
            }
        )
    except Exception as e:
        logger.warning(f"Receive version ask error: {e}", exc_info=True)

    return result


def receive_warn_kicked_user(client: Client, data: dict) -> bool:
    # Receive WARN banned user
    result = False

    try:
        # Basic data
        uid = data["user_id"]

        # Check kicked list
        if uid in glovar.white_kicked_ids:
            return False

        # Add to kicked list
        glovar.white_kicked_ids.add(uid)
        save("white_kicked_ids")

        # Remove white user
        receive_remove_white(uid)

        # Share the info
        share_data(
            client=client,
            receivers=glovar.receivers["white"],
            action="remove",
            action_type="white",
            data=uid
        )
    except Exception as e:
        logger.warning(f"Receive warn banned user error: {e}", exc_info=True)

    return result


def receive_watch_user(data: dict) -> bool:
    # Receive watch users that other bots shared
    result = False

    try:
        # Basic data
        the_type = data["type"]
        uid = data["id"]
        until = data["until"]

        # Decrypt the data
        until = crypt_str("decrypt", until, glovar.key)
        until = get_int(until)

        # Add to list
        if the_type == "ban":
            glovar.watch_ids["ban"][uid] = until
        elif the_type == "delete":
            glovar.watch_ids["delete"][uid] = until
        else:
            return False

        save("watch_ids")

        result = True
    except Exception as e:
        logger.warning(f"Receive watch user error: {e}", exc_info=True)

    return result
