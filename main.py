#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

from apscheduler.schedulers.background import BackgroundScheduler
from pyrogram import Client

from plugins import glovar
from plugins.functions.timers import backup_files, reset_data, send_count
from plugins.functions.timers import update_admins, update_status

# Enable logging
logger = logging.getLogger(__name__)

# Config session
app = Client(session_name="account")

# Timer
scheduler = BackgroundScheduler()
scheduler.add_job(update_status, "cron", [app], minute=30)
scheduler.add_job(backup_files, "cron", [app], hour=20)
scheduler.add_job(send_count, "cron", [app], hour=21)
scheduler.add_job(reset_data, "cron", day=glovar.reset_day, hour=22)
scheduler.add_job(update_admins, "cron", [app], hour=22, minute=30)
scheduler.start()

# Hold
app.run()
