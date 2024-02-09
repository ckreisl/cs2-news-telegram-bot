from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CS2_UPDATE_CHECK_INTERVAL = int(os.getenv('CS2_UPDATE_CHECK_INTERVAL', 900))

LOCAL_CHAT_STORE_FILEPATH = os.getenv('LOCAL_CHAT_STORE_FILEPATH', None)
LOCAL_LATEST_POST_STORE_FILEPATH = os.getenv(
    'LOCAL_LATEST_POST_STORE_FILEPATH', None)

CHAT_SPAM_INTERVAL_MS = int(os.getenv('CHAT_SPAM_INTERVAL_MS', 750))
CHAT_BAN_TIMEOUT_SECONDS = int(os.getenv('CHAT_BAN_TIMEOUT_SECONDS', 600))
CHAT_MAX_STRIKES = int(os.getenv('CHAT_MAX_STRIKES', 3))
