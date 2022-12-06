from ipaddress import ip_address
import logging
from logging.handlers import RotatingFileHandler
import os
import sys
import socket
import re
from uuid import uuid4, UUID
from configuration import Configuration

ip_address_regex = "^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"

__logger = None 

def get_logger():
    global __logger

    if __logger:
        return __logger
    
    #set libraries loggers format
    logging.basicConfig(format="%(asctime)s [%(levelname)s] %(module)s: %(message)s")

    __logger = logging.getLogger("hostpingbot")
    __logger.propagate = False
    
    if Configuration.DEBUG:
        __logger.setLevel(logging.DEBUG)
    else:
        __logger.setLevel(logging.INFO)

    formatter = logging.Formatter(fmt="%(asctime)s [%(levelname)s] %(module)s: %(message)s")

    """if Configuration.LOG_PATH:
        # log to file
        file_handler = RotatingFileHandler(
            Configuration.LOG_PATH,
            maxBytes=50,
            backupCount=10, 
        )
        file_handler.setFormatter(formatter)
        __logger.addHandler(file_handler)
    """

    if Configuration.LOGS_PATH:
        # log to file
        file_handler = logging.FileHandler(
            os.path.join(Configuration.LOGS_PATH, "main.log")
        )
        file_handler.setFormatter(formatter)
        __logger.addHandler(file_handler)

    # log to console
    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setFormatter(formatter)
    
    __logger.addHandler(stream_handler)
    
    return __logger

def generate_uuid():
    return uuid4()

def is_valid_uuid4(uuid_string):
    try:
        uuid_obj = UUID(uuid_string, version=4)
    except ValueError:
        return False
    return str(uuid_obj) == uuid_string

def dns_resolves(hostname):
    try:
        socket.gethostbyname(hostname)
        return True
    except socket.error:
        return False
    
def is_valid_address(address):
    if re.match(ip_address_regex, address): #it's an ip address
        return True
    
    return dns_resolves(address) # it's an hostname