# HostPingBot
This is a Telegram bot for detecting down hosts.

[![Deploy](https://github.com/francesco-re-1107/HostPingBot/actions/workflows/deploy.yml/badge.svg)](https://github.com/francesco-re-1107/HostPingBot/actions/workflows/deploy.yml)

https://t.me/HostPingBot

## Requirements
- Python 3
- Redis server
- PostgreSQL server

## Install and run

```
git clone https://github.com/francesco-re-1107/HostPingBot
cd HostPingBot
pip install -r requirements.txt

mv example_config.ini /etc/hostpingbot/config.ini
nano /etc/hostpingbot/config.ini

#edit config then start

python src/main.py
```

