from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import CallbackContext


logger = logging.getLogger(__name__)


def superadmin(func):
    def wrapper(self, update: Update, context: CallbackContext):
        if update.message.from_user.id != 10320841:
            logger.warning(
                f'Unauthorized access by \n \
                    user: {update.message.from_user.username} \n \
                    id: {update.message.from_user.id} \n \
                    is_bot: {update.message.from_user.is_bot}')
            logger.warning(f'msg={update.message.text}')
            return
        return func(self, update, context)
    return wrapper
