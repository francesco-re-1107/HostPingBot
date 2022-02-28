from aiogram.types import ReplyKeyboardMarkup
from strings import Strings

class Markups:
    
    def new():
        return ReplyKeyboardMarkup(
            resize_keyboard=True,
            selective=True
        )
    
    default_markup = new().add(Strings.NEW_WATCHDOG, Strings.LIST_WATCHDOGS).add(Strings.DELETE_WATCHDOG)
    select_type_markup = new().add(Strings.POLLING, Strings.PUSH).add(Strings.CANCEL)
    cancel_markup = new().add(Strings.CANCEL)