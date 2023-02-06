from flask import Flask, request, send_file
from utils import get_logger, is_valid_uuid4
from configuration import Configuration
from threading import Thread
import time
from waitress import serve
from database import Db
from bot import MainBot
import os

logger = get_logger()

NO_CACHE_HEADERS = {"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}

class PushServer:
    def __init__(self, db: Db, bot: MainBot, check_interval=10):
        self.__db = db
        self.__bot = bot
        self.__check_interval = check_interval

        self.__app = Flask(__name__)
        self.__app.add_url_rule("/status/<uuid>", "status", self.status)
        self.__app.add_url_rule("/badge/<uuid>", "badge", self.badge, )
        self.__app.add_url_rule(
            "/update/<uuid>", "update", self.update, methods=["POST"]
        )
        self.__app.register_error_handler(404, self.page_not_found)

    def page_not_found(self, error):
        return "This page does not exist {}".format(request.url), 404

    def status(self, uuid):
        logger.debug(f"GET /status/{uuid}")
        
        if not is_valid_uuid4(uuid):
            return "Bad id", 400

        w = self.__db.get_watchdog(uuid)
        if not w:
            return "Bad id", 400

        result = {
            "id": uuid,
            "online": not w.is_offline
        }

        return result, 200, NO_CACHE_HEADERS

    def badge(self, uuid):
        logger.debug(f"GET /badge/{uuid}")

        if not is_valid_uuid4(uuid):
            return "Bad id", 400

        w = self.__db.get_watchdog(uuid)
        if not w:
            return "Bad id", 400

        current_dir = os.path.dirname(os.path.realpath(__file__))
        filename = "offline.svg" if w.is_offline else "online.svg"
        filename = os.path.join(current_dir, "static", filename)

        return send_file(filename, mimetype="image/svg+xml"), NO_CACHE_HEADERS

    def update(self, uuid):
        logger.debug(f"POST /update/{uuid}")

        if not is_valid_uuid4(uuid):
            return "Bad id", 400

        w = self.__db.get_watchdog(uuid)
        if not w:
            return "Bad id", 400

        if not w.is_push:
            return "Bad id (not push)", 400

        if w.is_offline:  # host became online
            self.__bot.notify_online_host(w, last_update=w.last_update)

        self.__db.set_watchdog_online(uuid)

        return "OK"

    def __check_updates(self):
        logger.debug("Running check")
        hosts = self.__db.get_new_offline_hosts()
        self.__bot.notify_offline_hosts(hosts)
        self.__db.set_watchdogs_offline(hosts)

    def __schedule_check(self):
        logger.debug(f"Scheduled check every {self.__check_interval} seconds")

        while True:
            try:
                self.__check_updates()
                time.sleep(self.__check_interval)
            except Exception as e:
                logger.error("Error checking push server updates")
                logger.error(e)
                os._exit(1)

    def __start_server(self):
        try:
            logger.info("Starting")
            serve(self.__app, host="0.0.0.0", port=Configuration.PUSH_SERVER_PORT)
        except Exception as e:
            logger.error(f"Error starting push server: {e}")
            logger.error(e)
            os._exit(1)

    def start(self):
        Thread(target=self.__start_server, daemon=True).start()
        Thread(target=self.__schedule_check, daemon=True).start()
        return self
