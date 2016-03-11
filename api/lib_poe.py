import json
import requests
from io import BytesIO
from struct import pack
import copy
import time
import hashlib
import datetime
class Player:
    def __init__(self, name):
        self.name = name
        self.tabs = []
        self.stats = []
    def add_stats(self, league, nb_items, last_update):
        self.stats.append({"league": league, "nb_items": nb_items, "last_update": last_update})
    def __eq__(self, other):
        return self.name == other.name
    def __hash__(self):
        return hash(self.name)
          

class Tab:
    def __init__(self, id, owner, name, buyout):
        self.owner = owner
        self.id = id
        self.name = name
        self.items = []
        self.buyout = buyout

    def add_item(self, data):
        try:
            # if buyout is no price, use the tab b/o
            bo = Buyout.from_text(data["note"])
            if bo.is_none():
                bo = self.buyout
        # if there is no note, we use tab buyout
        except KeyError:
            bo = self.buyout
        name = data["name"].replace("<<set:MS>><<set:M>><<set:S>>", "") + " " + data["typeLine"].replace("<<set:MS>><<set:M>><<set:S>>", "")
        item = Item(data["id"], self.id, self.owner, data, bo, data["league"],
                    name.strip())
        self.items.append(item)

    def set_league(self):
        if len(self.items) == 0:
            self.league = "none"
        else:
            self.league = self.items[0].league

    def save_db(self, cursor, conn, save_mods):
        sql = """INSERT INTO tabs (id, owner, name, buyout, league, item_count, last_update) SELECT %s, %s, %s, %s, %s, %s, NOW()
         WHERE NOT EXISTS (SELECT 1 FROM tabs WHERE id=%s);"""
        cursor.execute(sql, (self.id, self.owner, self.name, str(self.buyout),
                             self.league, len(self.items), self.id))
        sql = "INSERT INTO players (name) SELECT %s WHERE NOT EXISTS (SELECT 1 FROM players WHERE name=%s)" 
        cursor.execute(sql, (self.owner,self.owner))
        # If no record matching player.id_sql + league exists, create a new one
        # Else update the old one (with the current date)
        sql = """INSERT INTO players_league (player, league, last_update, nb_items) 
        SELECT p.name , %s, NOW(), 0 FROM players p WHERE name=%s
        AND NOT EXISTS (SELECT 1 FROM players_league WHERE player=p.name AND league=%s)"""
        cursor.execute(sql, (self.league, self.owner,
                             self.league))


        self.save_items(cursor, conn, save_mods)

    
    def save_items(self, cursor, conn, save_mods):
        sql = "DELETE FROM items WHERE tab_id=%s"
        cursor.execute(sql, (self.id,))
        conn.commit()
        
        use_binary = True 
        # First we save the meta (id, tab_id, owner ...)
        if use_binary:
            self.save_items_meta_binary(self.items, cursor, conn)
        else:
            self.save_items_meta_normal(self.items, cursor, conn)
        need_update = []
        if not save_mods:
            return
        # then we check if some mods needs to be changed
        for i in self.items:
            sql = "SELECT mods FROM items_mods WHERE id=%s"
            cursor.execute(sql, (i.id, ))
            if cursor.rowcount > 0:
                # We have 1 item matching, check if the mods are the same
                row = cursor.fetchone()
                n_mods = json.loads(row[0])
                if i.mods != n_mods:
                    need_update.append(i)
                    cursor.execute("DELETE FROM items_mods WHERE id=%s", (i.id,))
            else:
                # We have no item matching, so we need to add in the DB the item
                need_update.append(i)
        conn.commit()
        #finally, we change the mods who needs to be changed
        if use_binary:
            self.save_items_mods_binary(need_update, cursor, conn)
        else:
            self.save_items_mods_normal(need_update, cursor, conn)

    
    def save_items_meta_normal(self, items, cursor, conn):
        for i in items:
            sql = "INSERT INTO items (id, tab_id, owner, buyout, league, name) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (i.id, self.id, i.owner,
                                 str(i.buyout), i.league, i.name))
        conn.commit()

    
    def save_items_meta_binary(self, items, cursor, conn):
        # Here comes the fun
        cpy = BytesIO()
        cpy.write(pack('!11sii', b'PGCOPY\n\377\r\n\0', 0, 0))  # Header
        for i in items:
            bo = bytes(str(i.buyout), 'utf-8')
            id = bytes(i.id, 'utf-8')
            owner = bytes(i.owner, 'utf-8')
            tab_id = bytes(self.id, 'utf-8')
            league = bytes(i.league, 'utf-8')
            name = bytes(i.name, 'utf-8')
            cpy.write(pack('!h', 6))  # Number of column inserted
            cpy.write(pack('!i', len(id)) + id)
            cpy.write(pack('!i', len(tab_id)) + tab_id)
            cpy.write(pack('!i', len(owner)) + owner)
            cpy.write(pack('!i', len(bo)) + bo)
            cpy.write(pack('!i', len(league)) + league)
            cpy.write(pack('!i', len(name)) + name)
        cpy.write(pack('!h', -1))  # End of file
        cpy.seek(0)
        sql = "COPY items (id, tab_id, owner, buyout, league, name) FROM STDIN WITH BINARY"
        cursor.copy_expert(sql, cpy)
        conn.commit()

    
    def save_items_mods_normal(self, items, cursor, conn):
        for i in items:
            mods = json.dumps(i.mods)
            sql = "INSERT INTO items_mods (id, mods) VALUES (%s, %s)" 
            cursor.execute(sql, (i.id, mods))
            conn.commit()



    
    def save_items_mods_binary(self, items, cursor, conn):
        cpy = BytesIO()
        cpy.write(pack('!11sii', b'PGCOPY\n\377\r\n\0', 0, 0))  # Header
        for i in items:
            id = bytes(i.id, 'utf-8')
            mods = bytes(json.dumps(i.mods), "utf-8")
            cpy.write(pack('!h', 2))  # Number of column inserted
            cpy.write(pack('!i', len(id)) + id)
            cpy.write(pack('!i', len(mods)) + mods)
        cpy.write(pack('!h', -1))  # End of file
        cpy.seek(0)
        sql = "COPY items_mods (id, mods) FROM STDIN WITH BINARY"
        cursor.copy_expert(sql, cpy)
        conn.commit()


class Item:
    def __init__(self, id, tab_id, owner, mods, buyout, league, name):
        self.id = id
        self.tab_id = tab_id
        self.owner = owner
        self.mods = mods
        self.buyout = buyout
        self.league = league
        self.name = name


class Buyout:
    buyout_tags = ["~b/o", "~price"]
    # buyout_type = ["b/o", "price", "none"]
    currency = ["alt", "fuse", "alch", "chaos", "gcp", "exa", "chrom", "jew",
                "chance",  "chisel",  "scour", "blessed", "regret", "regal",
                "divine", "vaal"]

    def __init__(self, type, currency, value):
        self.type = type
        self.value = value
        self.currency = currency

    @classmethod
    def from_text(cls, text):
        match = [x for x in cls.buyout_tags if x in text]
        if match:
            ty = match[0]
        else:
            ty = ""
        match = [x for x in cls.currency if x in text]
        if match:
            currency = match[0]
        else:
            currency = ""
        # If no currency found or no type, assume there is no buyout
        if not currency or not ty:
            return cls("none", "", 0.0)
        #  truc ~b/o 500 exa bidule
        # so we have ["whatever shit before", "500 exa whatever shit after"]
        d = text.split(ty)[1]
        # Take whatever is before the currency name
        value = d.split(currency)[0]
        return cls(ty, currency, value)

    def is_none(self):
        return self.type == "none"

    def __str__(self):
        return "{} {} {}".format(self.type, self.value, self.currency)


def parse_api(id, stats, cursor, db_connection, save_mods):
    """
    Put items/tab from the API in DB
    return next_change_id
    """
    stats.new_iter()
    BASE_URL = 'http://www.pathofexile.com/api/public-stash-tabs'
    url = BASE_URL + "?id=" + id
    stats.start_fetch()
    r = requests.get(url, headers={'Accept-Encoding': 'gzip'})
    data = json.loads(r.text)
    with open('changes/'+id, 'w+') as f:
        f.write(r.text)
    stats.end_fetch()
    stats.start_process()
    nb_items = 0
    for tab in data["stashes"]:
        bo = Buyout.from_text(tab["stash"])
        tmp = Tab(tab["id"], tab["accountName"], tab["stash"], bo)
        for item in tab["items"]:
            tmp.add_item(item)
            nb_items += 1
        tmp.set_league()
        tmp.save_db(cursor, db_connection, save_mods)
    stats.end_process()
    stats.end_iter(nb_items)
    return data["next_change_id"]


class LiveStats:
    BASE_VALUE = {"start": 0, "end": 0, "time": 0,
                  "start_fetch": 0, "end_fetch": 0, "time_fetch": 0,
                  "start_process": 0, "end_process": 0, "time_process": 0,
                  "items": 0, "speed": 0, "speed_fetch": 0,
                  "speed_process": 0
                  }

    def __init__(self):
        self.current = copy.copy(LiveStats.BASE_VALUE)
        self.history = []

    def new_iter(self):
        self.history.append(self.current)
        self.current = copy.copy(LiveStats.BASE_VALUE)
        self.current["start"] = time.time()

    def start_fetch(self):
        self.current["start_fetch"] = time.time()

    def end_fetch(self):
        self.current["end_fetch"] = time.time()

    def start_process(self):
        self.current["start_process"] = time.time()

    def end_process(self):
        self.current["end_process"] = time.time()

    def end_iter(self, nb_items):
        self.current["items"] = nb_items
        self.current["end"] = time.time()
        self.current["time"] = self.current["end"] - self.current["start"]
        self.current["time_fetch"] = self.current["end_fetch"] - self.current["start_fetch"]
        self.current["time_process"] = self.current["end_process"] - self.current["start_process"]
        self.current["speed"] = self.current["items"] / self.current["time"]
        self.current["speed_fetch"] = self.current["items"] / self.current["time_fetch"]
        self.current["speed_process"] = self.current["items"] / self.current["time_process"]

    def current_to_str(self):
        out = "parsed {} items ; fetch took {}s, process took {}s.".format(
            self.current["items"], self.current["time_fetch"], self.current["time_process"])
        out += "fetch speed is {} item/s, process speed is {} item/s".format(
            self.current["speed_fetch"], self.current["speed_process"])
        return out
    
    # Return average data since the first iter. Doesn't take in account current
    def __str__(self):
        if len(self.history) == 0:
            return "Wait for at least one iteration to be completed !"

        total_items = sum([x["items"] for x in self.history]) 
        total_time_fetch = sum([x["time_fetch"] for x in self.history])
        total_time_process = sum([x["time_process"] for x in self.history])
        speed_fetch = total_items / total_time_fetch
        speed_process = total_items / total_time_process
        out = "Status : parsed {} total items ; fetch took {}s, process took {}s.".format(
            total_items, total_time_fetch, total_time_process)
        out += "fetch speed is {} item/s, process speed is {} item/s".format(
            speed_fetch, speed_process)
        return out

