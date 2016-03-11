from lib_poe import Tab, Buyout, parse_api, LiveStats
import psycopg2
import json
import pickle
import time
from apscheduler.schedulers.background import BackgroundScheduler
def display_progress(stats):
    print(stats)

# data = r.text
if __name__ == "__main__":
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
    scheduler.add_job(lambda: print(stats), 'interval', seconds=5)
    scheduler.start()
    print("Starting parse with id {}".format(id))
    need_continue = True
    while need_continue:
        old_id = id
        id = parse_api(id, stats, cursor, db_connection, config["save_mods"])
        if id == -1 :
            need_continue = False
        print("Parsed id {} : {}".format(old_id, stats.current_to_str()))
        with open('next_change_id', 'w') as f:
            f.write(id)
        if stats.current["time"] < 1.1:
            print("Sleeping a little to avoid throttling")
            time.sleep(1.1 - stats.current["time"])
