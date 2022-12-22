from aiogram.types import ReplyKeyboardMarkup
from strings import Strings
from configuration import Configuration


class Markups:
    def new():
        return ReplyKeyboardMarkup(resize_keyboard=True, selective=True)

    def default(message):
        markup = (
            Markups.new()
            .add(Strings.NEW_WATCHDOG, Strings.LIST_WATCHDOGS)
            .add(Strings.DELETE_WATCHDOG)
        )
        if Configuration.is_admin(str(message.from_user.id)):
            markup.add(Strings.STATS)
        return markup

    select_type = new().add(Strings.TYPE_POLLING, Strings.TYPE_PUSH).add(Strings.CANCEL)
    cancel = new().add(Strings.CANCEL)
