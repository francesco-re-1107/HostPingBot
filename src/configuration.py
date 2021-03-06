import configparser
import os

config = configparser.ConfigParser()
config.read('/etc/hostpingbot/config.ini')

if 'Telegram' not in config:
    exit("Telegram config not found in config.ini")

if 'Database' not in config:
    exit("Database config not found in config.ini")

class Configuration():
    DATABASE_HOST = config.get('Database', 'Host', fallback=None) or "localhost"
    DATABASE_USER = config.get('Database', 'User', fallback=None) or exit("Database user not found")
    DATABASE_PASSWORD = config.get('Database', 'Password', fallback=None) or exit("Database password not found")
    TELEGRAM_BOT_TOKEN = config.get('Telegram', 'Token', fallback=None) or exit("Telegram token not found")
    TELEGRAM_ADMIN_USER_ID = config.get('Telegram', 'AdminUserId', fallback=None)
    PUSH_SERVER_PORT = config.getint('PushServer', 'Port', fallback=5000)
    WATCHDOGS_LIMIT_FOR_USER = config.getint('Other', 'WatchdogsLimitForUser', fallback=10)
    LOGS_PATH = config.get('Other', 'LogsPath', fallback=None)
    DEBUG = config.getboolean('Other', 'Debug', fallback=False)
    BASE_URL = config.get('PushServer', 'BaseUrl', fallback=f"http://localhost:{PUSH_SERVER_PORT}")

def exit(message):
    print(message)
    os._exit(1)