import configparser
import os

config = configparser.ConfigParser()
config.read(["/etc/hostpingbot/config.ini", "config.ini", "../config.ini"])

if "Telegram" not in config:
    exit("Telegram config not found in config.ini")

if "Database" not in config:
    exit("Database config not found in config.ini")


class Configuration:
    DATABASE_HOST = config.get("Database", "Host", fallback=None) or "localhost"
    DATABASE_USER = config.get("Database", "User", fallback=None) or ""
    DATABASE_PASSWORD = config.get("Database", "Password", fallback=None) or ""
    TELEGRAM_BOT_TOKEN = config.get("Telegram", "Token", fallback=None) or exit(
        "Telegram token not found in config.ini"
    )
    TELEGRAM_ADMIN_USER_ID = config.get("Telegram", "AdminUserId", fallback=None)
    PUSH_SERVER_PORT = config.getint("PushServer", "Port", fallback=5000)
    WATCHDOGS_LIMIT_FOR_USER = config.getint(
        "Other", "WatchdogsLimitForUser", fallback=10
    )
    LOGS_PATH = config.get("Other", "LogsPath", fallback=None)
    DEBUG = config.getboolean("Other", "Debug", fallback=False)
    BASE_URL = config.get(
        "PushServer", "BaseUrl", fallback=f"http://localhost:{PUSH_SERVER_PORT}"
    )

    def is_admin(user_id):
        if not Configuration.TELEGRAM_ADMIN_USER_ID:
            return False

        return user_id == Configuration.TELEGRAM_ADMIN_USER_ID


def exit(message):
    print(message)
    os._exit(1)
