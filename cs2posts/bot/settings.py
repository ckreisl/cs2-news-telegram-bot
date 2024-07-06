from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CS2_UPDATE_CHECK_INTERVAL = int(os.getenv('CS2_UPDATE_CHECK_INTERVAL', 900))

# Database filepaths (default: sqlite.db for both if None)
CHAT_DB_FILEPATH = os.getenv('CHAT_DB_FILEPATH', None)
POST_DB_FILEPATH = os.getenv('POST_DB_FILEPATH', None)

# Backup filepaths (default: /backups/backup.db if None)
CHAT_DB_BACKUP_FILEPATH = os.getenv('CHAT_DB_BACKUP_FILEPATH', None)
CHAT_DB_BACKUP_INTERVAL = int(os.getenv('CHAT_DB_BACKUP_INTERVAL', 86400))

CHAT_SPAM_INTERVAL_MS = int(os.getenv('CHAT_SPAM_INTERVAL_MS', 750))
CHAT_BAN_TIMEOUT_SECONDS = int(os.getenv('CHAT_BAN_TIMEOUT_SECONDS', 600))
CHAT_MAX_STRIKES = int(os.getenv('CHAT_MAX_STRIKES', 3))

# On startup import chats and posts from a JSON file (old behavior)
IMPORT_CHATS_FROM_JSON = os.getenv('IMPORT_CHATS_FROM_JSON', None)
IMPORT_POSTS_FROM_JSON = os.getenv('IMPORT_POSTS_FROM_JSON', None)
