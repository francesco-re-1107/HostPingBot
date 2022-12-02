from bot import MainBot
from pinger import Pinger
from push_server import PushServer
from database import Db
import os
from utils import get_logger

logger = get_logger()

def main():
    db = Db()
    bot = MainBot(db)
    ps = PushServer(db, bot, check_interval=10).start()
    pinger = Pinger(db, bot, interval=60).start()

    try:
        bot.run()
    except Exception as e:
        logger.error("Error in bot")
        logger.error(e)
        os._exit(1)

if __name__ == "__main__":
    main()