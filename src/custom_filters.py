from aiogram.dispatcher.filters import Filter
from aiogram.types import Message
from configuration import Configuration


class IsAdmin(Filter):
    key = "is_admin"

    async def check(self, message: Message):
        return Configuration.is_admin(str(message.from_user.id))
