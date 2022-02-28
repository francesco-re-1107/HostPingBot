from aiogram.dispatcher.filters import Filter
from aiogram.types import Message
from configuration import Configuration

class IsAdmin(Filter):
    key = "is_admin"

    async def check(self, message: Message):
        if Configuration.TELEGRAM_ADMIN_USER_ID is None:
            return False

        return str(message.from_user.id) == Configuration.TELEGRAM_ADMIN_USER_ID