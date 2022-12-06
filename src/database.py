from enum import unique
from peewee import *
from uuid import uuid4
from datetime import datetime, timedelta
from utils import generate_uuid, get_logger
from configuration import Configuration
from exceptions.exceptions import WatchdogsLimitExceededException, WatchdogDuplicateException

logger = get_logger()

# initialize db on module import
db = PostgresqlDatabase(
    'hostpingbot',  # Required by Peewee.
    host=Configuration.DATABASE_HOST,
    user=Configuration.DATABASE_USER,
    password=Configuration.DATABASE_PASSWORD,
    thread_safe=True,
    autorollback=True,
    autoconnect=True,
)

class Watchdog(Model):
    
    class Meta:
        database = db

    uuid = UUIDField(primary_key=True)
    name = CharField(null=False)
    is_push = BooleanField(null=False)
    address = CharField(null=True)
    is_enabled = BooleanField(null=False)
    last_update = TimestampField(default=datetime.now())
    check_interval = IntegerField(default=120) # in seconds or IntervalField() from peewee postgres extension
    is_offline = BooleanField(default=False)
    chat_id = BigIntegerField(null=False)

    def __str__(self):
        return f"<{self.uuid}, {self.name}>"

class Db:
    def add_push_watchdog(self, name, chat_id):
        # check watchdogs count limit for chat_id
        if self.has_reached_limits(chat_id):
            raise WatchdogsLimitExceededException()

        if self.is_name_duplicated(name, chat_id):
            raise WatchdogDuplicateException()

        w = Watchdog().create(
            uuid=generate_uuid(), 
            name=name, 
            is_push=True,
            is_enabled=True,
            last_update=datetime.now(),
            chat_id=chat_id
        )

        return w
    
    def add_ping_watchdog(self, name, address, chat_id):
        # check watchdogs count limit for chat_id
        if self.has_reached_limits(chat_id):
            raise WatchdogsLimitExceededException()
        
        if self.is_name_duplicated(name, chat_id):
            raise WatchdogDuplicateException()

        w = Watchdog().create(
            uuid=generate_uuid(), 
            name=name, 
            is_push=False,
            address=address, 
            is_enabled=True,
            last_update=datetime.now(),
            chat_id=chat_id
        )

        return w

    # def add_user(self, id):
    #     return User(id=id).save()
    
    def delete_watchdog(self, uuid):
        return Watchdog.delete_by_id(uuid)
    
    def delete_watchdog_for_user(self, chat_id, name):
        Watchdog.delete().where(Watchdog.chat_id == chat_id, Watchdog.name == name).execute()

    def get_new_offline_hosts(self):
        """
        Used by push_server to check which hosts didn't post updates for check_interval seconds  
        """
        offline_hosts = Watchdog.select().where(
            (int(round(datetime.now().timestamp())) - Watchdog.last_update) > Watchdog.check_interval,
            Watchdog.is_enabled == True,
            Watchdog.is_push == True,
            Watchdog.is_offline == False #offline for the first time
        )

        #set is_offline to True for the newest offline hosts
        Watchdog.update(is_offline=True).where(Watchdog.uuid.in_([w.uuid for w in offline_hosts]))

        return offline_hosts

    def get_hosts_to_ping(self) -> list[Watchdog]:
        """
        Used by pinger to get the polling wa
        """
        return list(Watchdog.select().where(
            Watchdog.is_enabled == True,
            Watchdog.is_push == False,
        ).execute())
    

    def get_watchdog(self, uuid):
        return Watchdog.get_or_none(Watchdog.uuid == uuid)

    def get_watchdogs_for_user(self, chat_id) -> list[Watchdog]:
        return Watchdog.select().where(Watchdog.chat_id == chat_id).order_by(Watchdog.name.asc())

    def has_reached_limits(self, chat_id):
        return Watchdog.select().where(Watchdog.chat_id == chat_id).count() >= Configuration.WATCHDOGS_LIMIT_FOR_USER

    def is_name_duplicated(self, name, chat_id):
        """
        Check if name is duplicated within same user
        """
        return Watchdog.select().where(Watchdog.chat_id == chat_id, Watchdog.name == name).count() > 0

    def push_update(self, uuid):
        return Watchdog.update(last_update=datetime.now(), is_offline=False).where(Watchdog.uuid == uuid).execute() is not None
    
    def set_watchdogs_offline(self, offline_hosts):
        """
        Set is_offline to True
        Used by pinger
        """
        return Watchdog.update(is_offline=True).where(Watchdog.uuid.in_([w.uuid for w in offline_hosts])).execute() is not None

    def set_watchdog_online(self, watchdog):
        return Watchdog.update(is_offline=False).where(Watchdog.uuid == watchdog.uuid).execute() is not None
    
    def get_stats(self):
        return f"Users: {Watchdog.select(Watchdog.chat_id).distinct().count()}\nWatchdogs: {Watchdog.select().count()}\nPing watchdogs: {Watchdog.select().where(Watchdog.is_push == False).count()}\nPush watchdogs: {Watchdog.select().where(Watchdog.is_push == True).count()}"
    

#create tables if they don't exist
db.create_tables([Watchdog])
logger.info("Connected")