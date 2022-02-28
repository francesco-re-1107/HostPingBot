from bot import MainBot
from pinger import Pinger
from push_server import PushServer
from database import Db


def main():
    db = Db()
    bot = MainBot(db)
    ps = PushServer(db, bot, check_interval=10).start()
    pinger = Pinger(db, bot, interval=60).start()

    bot.run()

if __name__ == "__main__":
    main()