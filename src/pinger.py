from datetime import datetime
from icmplib import multiping
from icmplib import NameLookupError
import time
from threading import Thread
from utils import get_logger
from database import Db
from bot import MainBot
import os

logger = get_logger()

class Pinger:

    def __init__(self, db: Db, bot: MainBot, interval=120, p_count=2, p_interval=0.05, p_concurrent_tasks=100, p_payload_size=8, p_offline_repeat_count=3):
        self.__db = db
        self.__bot = bot
        self.__interval = interval
        self.__hosts = []
        self.__p_count = p_count
        self.__p_interval = p_interval
        self.__p_concurrent_tasks = p_concurrent_tasks
        self.__p_payload_size = p_payload_size
        self.__offline_repeat_count = p_offline_repeat_count

        logger.debug("Ready")
            
    def __schedule(self):
        logger.debug(f"Scheduled ping every {self.__interval} seconds")
        
        while True:
            try:
                start_time = datetime.now()
                self.__ping_hosts()
                total_seconds = (datetime.now() - start_time).total_seconds()
                logger.debug(f"Took {total_seconds} seconds to ping")
                
                left_waiting_time = max(0, self.__interval - total_seconds)
                time.sleep(left_waiting_time)
            except Exception as e:
                logger.error("Error in pinger")
                logger.error(e)
                os._exit(1)

    def __ping_hosts(self):
        logger.debug("Running ping")

        self.__fetch_hosts()

        hosts_to_ping = self.__hosts
        retries = 0

        while retries < 5:
            try:
                for _ in range(self.__offline_repeat_count):
                    results = multiping(
                        [h.address for h in hosts_to_ping],
                        count = self.__p_count,
                        interval = self.__p_interval,
                        concurrent_tasks = self.__p_concurrent_tasks,
                        payload_size = self.__p_payload_size,
                        privileged=False
                    )

                    online_hosts = []

                    for i,r in enumerate(results):
                        if r.is_alive:
                            online_hosts.append(hosts_to_ping[i])
                    
                    for h in online_hosts:
                        if h.is_offline: #host became online    
                            self.__bot.notify_online_host(h)
                            self.__db.set_watchdog_online(h)

                        hosts_to_ping.remove(h)

                    if len(hosts_to_ping) == 0:
                        break
                break
            except NameLookupError as e:
                logger.error("NameLookupError")
                retries += 1
            except Exception as e:
                logger.error(e)
                retries += 1

        if len(hosts_to_ping) != 0:
            logger.debug(f"{len(hosts_to_ping)} hosts are down")
            
            #notify users
            new_offline_hosts = [h for h in hosts_to_ping if not h.is_offline]
            self.__bot.notify_offline_hosts(new_offline_hosts)
            self.__db.set_watchdogs_offline(new_offline_hosts)
        
        

    def __fetch_hosts(self):
        self.__hosts = self.__db.get_hosts_to_ping()
    
    def start(self):
        logger.info("Started")
        Thread(target=self.__schedule, daemon=True).start()
        return self