from utils import get_logger, is_valid_address, time_delta_to_string
from aiogram.utils.exceptions import BotBlocked, TelegramAPIError, RetryAfter
from configuration import Configuration
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters import Text
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from exceptions.exceptions import WatchdogsLimitExceededException, WatchdogDuplicateException
from database import Db
from markups import Markups
from custom_filters import IsAdmin
from datetime import datetime
from strings import Strings
import asyncio
import os

logger = get_logger()
bot_loop: asyncio.BaseEventLoop = None

# Watchdog creation form FSM states
class WatchdogCreation(StatesGroup):
    name = State()
    type = State()
    address = State()

# Watchdog deletion form FSM states
class WatchdogDeletion(StatesGroup):
    select = State()

class MainBot:

    def __init__(self, db: Db):
        self.__db = db
        self.__storage = RedisStorage2('localhost', 6379, db=5, pool_size=10, prefix='watchdog_fsm')
        try:
            self.__bot = Bot(token=Configuration.TELEGRAM_BOT_TOKEN)
            self.__dp = Dispatcher(self.__bot, storage=self.__storage)
        except Exception as e:
            logger.error(f"Cannot start: {e}")
            os._exit(1)

        
        self.__register_handlers()

    def __register_handlers(self):
        """
        Register endpoints for the Telegram bot
        """
        self.__dp.register_message_handler(
            self.__send_welcome, 
            commands=['start', 'help']
        )

        self.__dp.register_message_handler(
            self.__send_stats, 
            IsAdmin(), 
            commands=['stats']
        )

        self.__dp.register_message_handler(
            self.__list_watchdogs,
            commands=['list'],
            state='*'
        )

        self.__dp.register_message_handler(
            self.__list_watchdogs,
            Text(equals=Strings.LIST_WATCHDOGS, ignore_case=True), 
            state='*'
        )

        self.__dp.register_message_handler(
            self.__cancel_handler,
            commands=['cancel'],
            state='*'
        )

        self.__dp.register_message_handler(
            self.__cancel_handler,
            Text(equals=Strings.CANCEL, ignore_case=True), 
            state='*'
        )

        self.__dp.register_message_handler(
            self.__new_watchdog,
            commands=['new'],
            state='*'
        )

        self.__dp.register_message_handler(
            self.__new_watchdog,
            Text(equals=Strings.NEW_WATCHDOG, ignore_case=True), 
            state='*'
        )

        self.__dp.register_message_handler(
            self.__delete_watchdog,
            Text(equals=Strings.DELETE_WATCHDOG, ignore_case=True), 
            state='*'
        )

        self.__dp.register_message_handler(
            self.__delete_watchdog,
            commands=['delete'],
            state='*'
        )

        self.__dp.register_message_handler(
            self.__delete_selected_watchdog,
            state=WatchdogDeletion.select
        )

        self.__dp.register_message_handler(
            self.__process_name,
            state=WatchdogCreation.name
        )

        self.__dp.register_message_handler(
            self.__process_type,
            state=WatchdogCreation.type
        )

        self.__dp.register_message_handler(
            self.__process_address,
            state=WatchdogCreation.address
        )

    def __send_message_to_user(self, chat_id, message):
        bot_loop.create_task(
            self.__bot.send_message(chat_id, message)
        )

    def notify_offline_host(self, watchdog):
        self.__send_message_to_user(watchdog.chat_id, f"🔴 {watchdog.name} is OFFLINE right now")

    def notify_offline_hosts(self, watchdogs):
        for w in watchdogs:
            self.notify_offline_host(w)

    def notify_online_host(self, watchdog, last_update=None):
        if last_update is not None:
            total_seconds = (datetime.now() - last_update).total_seconds()
            
            down_for = time_delta_to_string(total_seconds)
            
            self.__send_message_to_user(watchdog.chat_id, f"🟢 {watchdog.name} is back ONLINE\n\nIt\'s been down for {down_for}")
        else:
            self.__send_message_to_user(watchdog.chat_id, f"🟢 {watchdog.name} is back ONLINE")


    async def __send_welcome(self, message: types.Message):
        """
        This handler will be called when user sends `/start` or `/help` command
        """
        await message.answer(Strings.WELCOME_MESSAGE, parse_mode="HTML", reply_markup=Markups.default_markup)
    
    async def __send_stats(self, message: types.Message):
        """
        This handler will be called when ADMIN sends `/stats` command
        """
        await message.answer(self.__db.get_stats(), reply_markup=Markups.default_markup)

    async def __list_watchdogs(self, message: types.Message):
        """
        This handler will be called when user sends `/list` command
        """
        watchdogs_list = self.__db.get_watchdogs_for_user(chat_id=message.chat.id)

        if len(watchdogs_list) == 0:
            await message.answer("You have no watchdogs", reply_markup=Markups.default_markup)
            return

        summary = "Here you can find your watchdogs\n\n"

        for w in watchdogs_list:
            if w.is_push:
                summary += f"{('🟢','🔴')[bool(w.is_offline)]} <b>{w.name}</b>\n🔄 <code>{Configuration.BASE_URL}/update/{str(w.uuid)}</code>\n🕑 Last update: <i>{w.last_update}</i>\n\n"
            else:
                summary += f"{('🟢','🔴')[bool(w.is_offline)]} <b>{w.name}</b> (<code>{w.address}</code>)\n\n"
        
        await message.answer(summary, parse_mode="HTML", reply_markup=Markups.default_markup)

    async def __new_watchdog(self, message: types.Message):
        """
        This handler will be called when user sends `/new` command
        """
        if self.__db.has_reached_limits(chat_id=message.chat.id):
            await message.answer(f"You've rechead watchdogs number limit ({Configuration.WATCHDOGS_LIMIT_FOR_USER})", reply_markup=Markups.default_markup)
            return

        # set state
        await WatchdogCreation.name.set()

        await message.answer("Please input a name", reply_markup=Markups.cancel_markup)

    async def __delete_watchdog(self, message: types.Message):
        list_markup = Markups.new()

        watchdogs = self.__db.get_watchdogs_for_user(chat_id=message.chat.id)

        if len(watchdogs) == 0:
            await message.answer("You have no watchdogs", reply_markup=Markups.default_markup)
            return

        list_markup.add(Strings.CANCEL)
        
        for w in watchdogs:
            list_markup.add(w.name)


        await WatchdogDeletion.select.set()

        await message.answer(f"Select which watchdog you'd like to delete", reply_markup=list_markup)
    
    async def __delete_selected_watchdog(self, message: types.Message, state: FSMContext):
        self.__db.delete_watchdog_for_user(chat_id=message.chat.id, name=message.text)

        await state.finish()

        await message.answer(f"Deleted watchdog {message.text}", reply_markup=Markups.default_markup)


    async def __process_type(self, message: types.Message, state: FSMContext):
        if message.text == "Polling (ping)":
            is_push = False
        elif message.text == "Push (http)":
            is_push = True
        else:
            await message.reply(f"Please select a type from below\n", reply_markup=Markups.select_type_markup)
            return

        if is_push:    
            async with state.proxy() as data:
                try:
                    w = self.__db.add_push_watchdog(data['name'], message.chat.id)
                    
                    logger.debug(f"Created {w}")
                    
                    await message.answer(f"Created watchdog {w.name}\n\nMake a POST request to\n<code>{Configuration.BASE_URL}/update/{str(w.uuid)}</code> every 2 minutes", reply_markup=Markups.default_markup, parse_mode='HTML')
                
                except WatchdogsLimitExceededException:
                    await message.answer(f"You've rechead watchdogs number limit ({Configuration.WATCHDOGS_LIMIT_FOR_USER})\n", reply_markup=Markups.default_markup)
            
            # reset state
            await state.finish()
            
        else:
            await WatchdogCreation.address.set()

            await message.answer("Please write address (ip or hostname)", reply_markup=Markups.cancel_markup)

    async def __process_address(self, message: types.Message, state: FSMContext):
        
        if not is_valid_address(message.text):
            await message.answer(f"{message.text} is not a valid address\n", reply_markup=Markups.cancel_markup)
            return

        async with state.proxy() as data:
            data['address'] = message.text
        
        try:
            logger.debug(f"Creating watchdog with name {data['name']} and address {data['address']} for user {message.chat.id}")
            w = self.__db.add_ping_watchdog(data['name'], data['address'], message.chat.id)
            
            logger.debug(f"Created {w}")
            await message.answer(f"Created watchdog {w.name}", reply_markup=Markups.default_markup)
        except WatchdogsLimitExceededException:
            await message.answer(f"You've rechead watchdogs number limit ({Configuration.WATCHDOGS_LIMIT_FOR_USER})", reply_markup=Markups.default_markup)
        except WatchdogDuplicateException:
            await message.answer(f"Duplicate watchdogs name error", reply_markup=Markups.cancel_markup)

    async def __process_name(self, message: types.Message, state: FSMContext):
        truncated_name = message.text[:64]
        
        if self.__db.is_name_duplicated(name=truncated_name, chat_id=message.chat.id):
            await message.answer(f"You already have a watchdog named {truncated_name}", reply_markup=Markups.cancel_markup)
            return
        
        async with state.proxy() as data:
            data['name'] = truncated_name
        
        # Set state
        await WatchdogCreation.type.set()

        await message.answer("Please select the watchdog type you prefer", reply_markup=Markups.select_type_markup)

    async def __cancel_handler(self, message: types.Message, state: FSMContext):
        """
        Allow user to cancel any action
        """
        current_state = await state.get_state()
        if current_state is None:
            return

        logger.debug('Cancelling state %r', current_state)

        # Cancel state and inform user about it
        await state.finish()

        # And remove keyboard
        await message.answer('Cancelled', reply_markup=Markups.default_markup)

    def __exception_handler(self, loop, context):
        ex = context.get('exception')

        if isinstance(ex, BotBlocked):
            logger.info(f"Bot blocked by user")
        elif isinstance(ex, TelegramAPIError):
            logger.warn(f"Telegram API error: {ex}")
        elif isinstance(ex, RetryAfter):
            logger.warn(f"API Flooded: {ex}")
        else:
            logger.error(f"Exception occured: {context['message']}")

    def run(self):
        global bot_loop
        bot_loop = asyncio.get_event_loop()
        bot_loop.set_exception_handler(self.__exception_handler)
        try:
            logger.info("Starting")
            executor.start_polling(self.__dp, loop=bot_loop)
        except Exception as e:
            logger.error(f"Cannot start: {e}")
            os._exit(1)
        