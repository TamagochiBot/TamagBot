import sqlite3 as sql

def init():
    connect = sql.connect("testDB.db")

    # database cursor is a mechanism that enables traversal over the records in a database.
    cursor = connect.cursor()

    #PLAYER TABLE
    cursor.execute('''CREATE TABLE IF NOT EXISTS player (
            id INTEGER PRIMARY KEY,
            is_admin BOOLEAN NOT NULL DEFAULT 0,
            balance INTEGER NOT NULL DEFAULT 0,
            level INTEGER NOT NULL DEFAULT 1,
            experience INTEGER NOT NULL DEFAULT 0,
            helmet INTEGER DEFAULT NULL,
            chestplate INTEGER DEFAULT NULL,
            item1 INTEGER DEFAULT NULL,
            item2 INTEGER DEFAULT NULL,
            user_name VARCHAR(40) NOT NULL DEFAULT 'UNKNOWN',
            pet_name VARCHAR(40) NOT NULL DEFAULT 'UNKNOWN',
            health INTEGER NOT NULL DEFAULT 100,
            strength INTEGER NOT NULL DEFAULT 0,
            weapon_damage INTEGER NOT NULL DEFAULT 0,
            head_skin TEXT NOT NULL DEFAULT 'default',
            available_head_skins NOT NULL DEFAULT '',
            available_body_skins NOT NULL DEFAULT '',
            available_weapon_skins NOT NULL DEFAULT '',
            body_skin TEXT NOT NULL DEFAULT 'default',
            weapon_skin TEXT NOT NULL DEFAULT 'default'
            );
    ''')

     # ITEMS TABLE
    cursor.execute('''CREATE TABLE IF NOT EXISTS item (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type VARCHAR(40) NOT NULL DEFAULT '',
            name VARCHAR(40) NOT NULL DEFAULT '',
            rarity VARCHAR(40) NOT NULL DEFAULT 'common',
            stats INTEGER NOT NULL DEFAULT 0,
            mod TEXT NOT NULL DEFAULT '',
            FOREIGN KEY(user_id) REFERENCES player(id)
            ON DELETE CASCADE ON UPDATE CASCADE
            );
    ''')

    # UNREGULAR EVENT TABLE 
    cursor.execute("""CREATE TABLE IF NOT EXISTS event (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_name VARCHAR(40) NOT NULL DEFAULT '',
            user_id INTEGER NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            experience INTEGER NOT NULL DEFAULT 0,
            deadline DATETIME DEFAULT NULL,
            FOREIGN KEY(user_id) REFERENCES player(id)
            ON DELETE SET NULL ON UPDATE CASCADE
            );
    """ )

     # REGULAR EVENT TABLE 
    cursor.execute("""CREATE TABLE IF NOT EXISTS regular_event (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_name VARCHAR(40) NOT NULL DEFAULT '',
            user_id INTEGER NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            experience INTEGER NOT NULL DEFAULT 0,
            deadline TEXT DEFAULT NULL,
            list_of_players TEXT NOT NULL DEFAULT '',
            FOREIGN KEY(user_id) REFERENCES player(id)
            ON DELETE SET NULL ON UPDATE CASCADE
            );
    """ )

if __name__ == "__main__":
    init()