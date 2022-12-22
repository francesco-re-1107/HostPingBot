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
            self.__send_stats, 
            IsAdmin(), 
            Text(equals=Strings.STATS, ignore_case=False), 
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
        self.__send_message_to_user(watchdog.chat_id, Strings.OFFLINE_MESSAGE(watchdog.name))

    def notify_offline_hosts(self, watchdogs):
        for w in watchdogs:
            self.notify_offline_host(w)

    def notify_online_host(self, watchdog, last_update=None):
        if last_update is not None:
            total_seconds = (datetime.now() - last_update).total_seconds()
            
            down_for = time_delta_to_string(total_seconds)
            
            self.__send_message_to_user(watchdog.chat_id, Strings.ONLINE_MESSAGE_WITH_TIME(watchdog.name, down_for))
        else:
            self.__send_message_to_user(watchdog.chat_id, Strings.ONLINE_MESSAGE(watchdog.name))


    async def __send_welcome(self, message: types.Message):
        """
        This handler will be called when user sends `/start` or `/help` command
        """
        limit = Configuration.WATCHDOGS_LIMIT_FOR_USER
        await message.answer(Strings.WELCOME_MESSAGE(limit), parse_mode="HTML", reply_markup=Markups.default(message))
    
    async def __send_stats(self, message: types.Message):
        """
        This handler will be called when ADMIN sends `/stats` command
        """
        await message.answer(self.__db.get_stats(), reply_markup=Markups.default(message))

    async def __list_watchdogs(self, message: types.Message):
        """
        This handler will be called when user sends `/list` command
        """
        watchdogs_list = self.__db.get_watchdogs_for_user(chat_id=message.chat.id)

        if len(watchdogs_list) == 0:
            await message.answer(Strings.NO_WATCHDOGS, reply_markup=Markups.default(message))
            return

        summary = Strings.LIST_WATCHDOGS_HEADER

        for w in watchdogs_list:
            if w.is_push:
                url = Configuration.BASE_URL + "/update/" + str(w.uuid)
                last_update = time_delta_to_string((datetime.now() - w.last_update).total_seconds())
                summary += Strings.LIST_WATCHDOGS_PUSH_ITEM(w.name, url, not bool(w.is_offline), last_update)
            else:
                summary += Strings.LIST_WATCHDOGS_PING_ITEM(w.name, w.address, not bool(w.is_offline))
        
        await message.answer(summary, parse_mode="HTML", reply_markup=Markups.default(message))

    async def __new_watchdog(self, message: types.Message):
        """
        This handler will be called when user sends `/new` command
        """
        if self.__db.has_reached_limits(chat_id=message.chat.id):
            limit = Configuration.WATCHDOGS_LIMIT_FOR_USER
            await message.answer(Strings.ERROR_WATCHDOGS_LIMIT_EXCEEDED(limit), reply_markup=Markups.default(message))
            return

        # set state
        await WatchdogCreation.name.set()

        await message.answer(Strings.INPUT_NAME, reply_markup=Markups.cancel)

    async def __delete_watchdog(self, message: types.Message):
        list_markup = Markups.new()

        watchdogs = self.__db.get_watchdogs_for_user(chat_id=message.chat.id)

        if len(watchdogs) == 0:
            await message.answer(Strings.NO_WATCHDOGS, reply_markup=Markups.default(message))
            return

        list_markup.add(Strings.CANCEL)
        
        for w in watchdogs:
            list_markup.add(w.name)

        await WatchdogDeletion.select.set()

        await message.answer(Strings.INPUT_DELETE_WATCHDOG, reply_markup=list_markup)
    
    async def __delete_selected_watchdog(self, message: types.Message, state: FSMContext):
        deleted = self.__db.delete_watchdog_for_user(chat_id=message.chat.id, name=message.text)

        await state.finish()
        
        if not deleted:
            await message.answer(Strings.ERROR_DELETING_WATCHDOG)
            return

        await message.answer(Strings.DELETED_WATCHDOG_MESSAGE(message.text), reply_markup=Markups.default(message))


    async def __process_type(self, message: types.Message, state: FSMContext):
        if message.text == Strings.TYPE_POLLING:
            is_push = False
        elif message.text == Strings.TYPE_PUSH:
            is_push = True
        else:
            await message.reply(Strings.INPUT_TYPE, reply_markup=Markups.select_type)
            return

        if is_push:    
            async with state.proxy() as data:
                try:
                    w = self.__db.add_push_watchdog(data['name'], message.chat.id)
                    
                    logger.debug(f"Created {w}")
                    
                    url = Configuration.BASE_URL + "/update/" + str(w.uuid)
                    await message.answer(Strings.CREATED_PUSH_WATCHDOG_MESSAGE(w.name, url), reply_markup=Markups.default(message), parse_mode='HTML')
                
                except WatchdogsLimitExceededException:
                    limit = Configuration.WATCHDOGS_LIMIT_FOR_USER
                    await message.answer(Strings.ERROR_WATCHDOGS_LIMIT_EXCEEDED(limit), reply_markup=Markups.default(message))
            
            # reset state
            await state.finish()
            
        else:
            await WatchdogCreation.address.set()

            await message.answer(Strings.INPUT_ADDRESS, reply_markup=Markups.cancel)

    async def __process_address(self, message: types.Message, state: FSMContext):
        
        if not is_valid_address(message.text):
            await message.answer(Strings.ERROR_INVALID_ADDRESS(message.text), reply_markup=Markups.cancel)
            return

        async with state.proxy() as data:
            data['address'] = message.text
        
        try:
            logger.debug(f"Creating watchdog with name {data['name']} and address {data['address']} for user {message.chat.id}")
            w = self.__db.add_ping_watchdog(data['name'], data['address'], message.chat.id)
            
            logger.debug(f"Created {w}")
            await message.answer(Strings.CREATED_PING_WATCHDOG_MESSAGE(data['name'], data['address']), reply_markup=Markups.default(message))
        except WatchdogsLimitExceededException:
            limit = Configuration.WATCHDOGS_LIMIT_FOR_USER
            await message.answer(Strings.ERROR_WATCHDOGS_LIMIT_EXCEEDED(limit), reply_markup=Markups.default(message))
        except WatchdogDuplicateException:
            await message.answer(Strings.ERROR_WATCHDOG_DUPLICATE(data['name']), reply_markup=Markups.cancel)

    async def __process_name(self, message: types.Message, state: FSMContext):
        truncated_name = message.text[:64]
        
        if self.__db.is_name_duplicated(name=truncated_name, chat_id=message.chat.id):
            await message.answer(Strings.ERROR_WATCHDOG_DUPLICATE(truncated_name), reply_markup=Markups.cancel)
            return
        
        async with state.proxy() as data:
            data['name'] = truncated_name
        
        # Set state
        await WatchdogCreation.type.set()

        await message.answer(Strings.INPUT_TYPE, reply_markup=Markups.select_type)

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
        await message.answer(Strings.CANCELLED, reply_markup=Markups.default(message))

    def __exception_handler(self, loop, context):
        ex = context.get('exception')

        if isinstance(ex, BotBlocked):
            logger.info(f"Bot blocked by user")
        elif isinstance(ex, TelegramAPIError):
            logger.warn(f"Telegram API error: {ex}")
        elif isinstance(ex, RetryAfter):
            logger.warn(f"API Flooded: {ex}")
        elif isinstance(ex, Exception):
            logger.error(f"Exception occured: {ex}")
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
        