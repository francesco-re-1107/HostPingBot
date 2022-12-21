from ipaddress import ip_address
import logging
from logging.handlers import RotatingFileHandler
import os
import sys
import socket
from uuid import uuid4, UUID
from configuration import Configuration

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
        ip = ip_address(socket.gethostbyname(hostname))
        return not ip.is_private #for hostnames like localhost
    except socket.error: #dns error
        return False
    except ValueError: #the returned ip is not valid
        return False
    
def is_valid_address(address):
    try:
        ip = ip_address(address) # it's an ip address
        return not ip.is_private #private ips are not allowed
    except ValueError:
        return dns_resolves(address) # it's a hostname

def time_delta_to_string(seconds):
    """
    Converts a time delta in seconds to a string of the form "Xd Yh Zm"
    where X are days, Y are hours and Z are minutes
    """
    minutes = seconds//60
    hours = minutes//60
    days = hours//24

    if seconds < 3600:
        return f"{minutes}m"
    elif seconds < 86400:
        return f"{hours}h {minutes%60}m"
    else:
        return f"{days}d {hours%24}h {minutes%60}m"