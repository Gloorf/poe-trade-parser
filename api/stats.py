# In the end, i want to know :
# - How much items are available, with the league origin
# - The number of active players in each league. 
# An active player is a player with activity in at least one of his tabs
from lib_poe import Tab, Player
import psycopg2
import json
import pickle
import time
if __name__ == "__main__":
    # db init
    with open('config.json', 'r') as f:
        config = json.load(f)
    db_connection = psycopg2.connect(host=config['db']['host'],
                                     user=config['db']['user'],
                                     password=config['db']['password'],
                                     dbname=config['db']['name'])
    cursor = db_connection.cursor()
    tabs = []
    players = []
    cursor.execute("SELECT * FROM tabs")
    answer = cursor.fetchall()
    print("DB answered")
    for id_sql, id, owner, name, buyout, league, nb_items, last_update in answer:
        tmp = Tab(id, owner, name, buyout)
        tmp.last_update = last_update
        tmp.league = league
        tmp.nb_items = nb_items
        tabs.append(tmp)
    cursor.execute("SELECT player, league, last_update, nb_items FROM players_league ORDER BY player")
    answer = cursor.fetchall()
    previous = ""
    for player, league, last_update, nb_items in answer:
        if player != previous:
            tmp = Player(player)
            tmp.add_stats(league, nb_items, last_update)
            players.append(tmp)
            previous = player
        else:
            players[-1].add_stats(league, nb_items, last_update)
                
    print("I've got {} tabs and {} players".format(len(tabs), len(players)))
    time = str(int(time.time()))
    with open("statistics/tabs-"+time, "wb") as f:
        pickle.dump(tabs, f)
    with open("statistics/players-"+time, "wb") as f:
        pickle.dump(players, f)

