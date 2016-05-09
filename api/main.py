#!/usr/bin/python3.5
from lib_poe import Tab, Buyout, parse_api, LiveStats
import psycopg2
import json
import pickle
import time
import logging.config
import os
import sys
from apscheduler.schedulers.background import BackgroundScheduler
def display_progress(stats):
    print(stats)
logging_options = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "simple": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt":"%d-%m %H:%M"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simple",
            "stream": "ext://sys.stdout"
        },

        "file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "simple",
            "filename": "parser.log",
            "maxBytes": 10485760,
            "backupCount": 20,
            "encoding": "utf8"
        },
        "warning_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "WARNING",
            "formatter": "simple",
            "filename": "warning.log",
            "maxBytes": 10485760,
            "backupCount": 20,
            "encoding": "utf8"
        },
        "null_handler": {
            "class": "logging.NullHandler",
            "level": "DEBUG"
        }


    },
    "apscheduler": {
        "level": "DEBUG",
        "propagate": "false"
    },
    "root": {
        "level": "DEBUG",
        "handlers": ["file_handler", "warning_handler"]
    }
}
# data = r.text
if __name__ == "__main__":


    logging.config.dictConfig(logging_options)
    logger = logging.getLogger(__name__)
    logging.getLogger("apscheduler").propagate = False
    #addHandler(logging.NullHandler())
        # If there is a lock, don't relaunch a parser
    if os.path.exists("parser.lock"):
        logger.info("Lock file existing, aborting ")
        sys.exit()
    with open("parser.lock", "w+") as f:
        pass
    # db init
    with open('config.json', 'r') as f:
        config = json.load(f)
    db_connection = psycopg2.connect(host=config['db']['host'],
                                     user=config['db']['user'],
                                     password=config['db']['password'],
                                     dbname=config['db']['name'])
    cursor = db_connection.cursor()
    stats = LiveStats()
    #Get the latest change id
    with open('next_change_id', 'r') as f:
        id = f.read()
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: logger.info(stats), 'interval', seconds=10)
    scheduler.start()
    logger.info("Starting parse with id {}".format(id))
    time_start = time.time()
    need_continue = True
    try:
        while need_continue:
            old_id = id
            id = parse_api(id, stats, cursor, db_connection, config["save_mods"], config["save_raw"])
            if id == -1 :
                need_continue = False
            with open('next_change_id', 'w') as f:
                f.write(id)
            if stats.current["time"] < 1.1:
                logger.debug("Sleeping a little to avoid throttling")
                time.sleep(1.1 - stats.current["time"])
            if time_start + 60*10 < time.time():
                need_continue = False
    except Exception as e:
        logger.error("Stopping thread cause {}".format(e))
    finally:
        logger.warning("Stopped parser, deleting lock")
        os.remove("parser.lock")
