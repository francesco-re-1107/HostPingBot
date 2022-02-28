from flask import Flask, request
from utils import get_logger, is_valid_uuid4
from configuration import Configuration
from threading import Thread
import time
from waitress import serve
from database import Db
from bot import MainBot
import os

logger = get_logger()

class PushServer():

    def __init__(self, db: Db, bot: MainBot, check_interval=10):
        self.__db = db
        self.__bot = bot
        self.__check_interval = check_interval

        self.__app = Flask(__name__)
        self.__app.add_url_rule('/status', 'status', self.status)
        self.__app.add_url_rule('/update/<uuid>', 'update', self.update, methods = ['POST'])
        self.__app.register_error_handler(404, self.page_not_found)

    def page_not_found(self, error):
        return 'This route does not exist {}'.format(request.url), 404

    def status(self):
        logger.debug("GET /status")
        return "OK - bot"

    def update(self, uuid):
        logger.debug(f"POST /update/{uuid}")
        
        if not is_valid_uuid4(uuid):
            return "Bad id", 400

        w = self.__db.get_watchdog(uuid)
        if not w:
            return "Bad id", 400

        if not w.is_push:
            return "Bad id (not push)", 400

        if w.is_offline: #host became online
            self.__bot.notify_online_host(w, last_update=w.last_update)

        self.__db.push_update(uuid)

        return "OK"

    
    def __check_updates(self):
        logger.debug("Running check")
        hosts = self.__db.get_new_offline_hosts()
        self.__bot.notify_offline_hosts(hosts)
        self.__db.set_watchdogs_offline(hosts)


    def __schedule_check(self):
        logger.debug(f"Scheduled check every {self.__check_interval} seconds")
        
        while True:
            self.__check_updates()
            time.sleep(self.__check_interval)
            

    def __start_server(self):
        try:
            logger.info("Starting")
            serve(self.__app, host="0.0.0.0", port=Configuration.PUSH_SERVER_PORT)
        except Exception as e:
            logger.error(f"Cannot start: {e}")
            os._exit(1)

    def start(self):
        Thread(target=self.__start_server, daemon=True).start()
        Thread(target=self.__schedule_check, daemon=True).start()
        return self
