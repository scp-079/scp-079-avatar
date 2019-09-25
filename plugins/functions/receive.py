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
from copy import deepcopy
from json import loads
from typing import Any

from pyrogram import Client, Message

from .. import glovar
from .channel import share_data
from .etc import get_text, thread
from .file import crypt_file, delete_file, get_new_path, get_downloaded_path, save
from .ids import init_group_id
from .timers import update_admins
from .user import get_user

# Enable logging
logger = logging.getLogger(__name__)


def receive_add_except(client: Client, data: dict) -> bool:
    # Receive a object and add it to except list
    try:
        the_id = data["id"]
        the_type = data["type"]
        # Receive except contents
        if the_type == "long":
            the_user = get_user(client, the_id)
            if the_user:
                if the_user.photo:
                    file_id = the_user.photo.big_file_id
                    glovar.except_ids["long"].add(file_id)

        save("except_ids")

        return True
    except Exception as e:
        logger.warning(f"Receive add except error: {e}", exc_info=True)

    return False


def receive_add_bad(_: str, data: dict) -> bool:
    # Receive bad users or channels that other bots shared
    try:
        the_id = data["id"]
        the_type = data["type"]
        if the_type == "user":
            glovar.bad_ids["users"].add(the_id)

        save("bad_ids")

        return True
    except Exception as e:
        logger.warning(f"Receive add bad error: {e}", exc_info=True)

    return False


def receive_clear_data(data_type: str, data: dict) -> bool:
    # Receive clear data command
    try:
        the_type = data["type"]
        if data_type == "bad":
            if the_type == "users":
                glovar.bad_ids["users"] = set()

            save("bad_ids")
        elif data_type == "except":
            if the_type == "long":
                glovar.except_ids["long"] = set()

            save("except_ids")
        elif data_type == "user":
            if the_type == "all":
                glovar.user_ids = {}
            elif the_type == "new":
                for uid in list(glovar.user_ids):
                    glovar.user_ids[uid]["join"] = {}

            save("user_ids")
    except Exception as e:
        logger.warning(f"Receive clear data: {e}", exc_info=True)

    return False


def receive_declared_message(data: dict) -> bool:
    # Update declared message's id
    try:
        gid = data["group_id"]
        mid = data["message_id"]
        if glovar.admin_ids.get(gid):
            if init_group_id(gid):
                glovar.declared_message_ids[gid].add(mid)
                return True
    except Exception as e:
        logger.warning(f"Receive declared message error: {e}", exc_info=True)

    return False


def receive_file_data(client: Client, message: Message, decrypt: bool = False) -> Any:
    # Receive file's data from exchange channel
    data = None
    try:
        if message.document:
            file_id = message.document.file_id
            file_ref = message.document.file_ref
            path = get_downloaded_path(client, file_id, file_ref)
            if path:
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
                    data = pickle.load(f)

                for f in {path, path_decrypted}:
                    thread(delete_file, (f,))
    except Exception as e:
        logger.warning(f"Receive file error: {e}", exc_info=True)

    return data


def receive_refresh(client: Client, _: int) -> bool:
    # Receive refresh
    try:
        update_admins(client)

        return True
    except Exception as e:
        logger.warning(f"Receive refresh error: {e}", exc_info=True)

    return False


def receive_regex(client: Client, message: Message, data: str) -> bool:
    # Receive regex
    glovar.locks["regex"].acquire()
    try:
        file_name = data
        word_type = file_name.split("_")[0]
        if word_type not in glovar.regex:
            return True

        words_data = receive_file_data(client, message, True)
        if words_data:
            pop_set = set(eval(f"glovar.{file_name}")) - set(words_data)
            new_set = set(words_data) - set(eval(f"glovar.{file_name}"))
            for word in pop_set:
                eval(f"glovar.{file_name}").pop(word, 0)

            for word in new_set:
                eval(f"glovar.{file_name}")[word] = 0

            save(file_name)

        return True
    except Exception as e:
        logger.warning(f"Receive regex error: {e}", exc_info=True)
    finally:
        glovar.locks["regex"].release()

    return False


def receive_remove_bad(_: str, data: dict) -> bool:
    # Receive removed bad objects
    try:
        the_id = data["id"]
        the_type = data["type"]
        if the_type == "user":
            glovar.bad_ids["users"].discard(the_id)
            if glovar.user_ids.get(the_id):
                glovar.user_ids[the_id] = deepcopy(glovar.default_user_status)

            save("user_ids")

        save("bad_ids")

        return True
    except Exception as e:
        logger.warning(f"Receive remove bad error: {e}", exc_info=True)

    return False


def receive_remove_except(client: Client, data: dict) -> bool:
    # Receive a object and remove it from except list
    try:
        the_id = data["id"]
        the_type = data["type"]
        # Receive except contents
        if the_type == "long":
            the_user = get_user(client, the_id)
            if the_user:
                if the_user.photo:
                    file_id = the_user.photo.big_file_id
                    glovar.except_ids["long"].discard(file_id)

        save("except_ids")

        return True
    except Exception as e:
        logger.warning(f"Receive remove except error: {e}", exc_info=True)

    return False


def receive_text_data(message: Message) -> dict:
    # Receive text's data from exchange channel
    data = {}
    try:
        text = get_text(message)
        if text:
            data = loads(text)
    except Exception as e:
        logger.warning(f"Receive data error: {e}")

    return data


def receive_version_ask(client: Client, data: dict) -> bool:
    # Receive version info request
    try:
        aid = data["admin_id"]
        mid = data["message_id"]
        share_data(
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

        return True
    except Exception as e:
        logger.warning(f"Receive version ask error: {e}", exc_info=True)

    return False
