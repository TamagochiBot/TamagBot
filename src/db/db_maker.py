import sqlite3 as sql

def init():
    connect = sql.connect("testDB.db")

    # database cursor is a mechanism that enables traversal over the records in a database.
    cursor = connect.cursor()

    # INVENTORY TABLE
    cursor.execute('''CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            apples INT NOT NULL DEFAULT 5,
            cookies INT NOT NULL DEFAULT 5
            );
    ''')

    #PLAYER TABLE
    cursor.execute('''CREATE TABLE IF NOT EXISTS player (
            id INTEGER PRIMARY KEY,
            balance INTEGER NOT NULL DEFAULT 0,
            user_name VARCHAR(40) NOT NULL DEFAULT "UNKNOWN",
            pet_name VARCHAR(40) NOT NULL DEFAULT "UNKNOWN",
            health INTEGER NOT NULL DEFAULT 100,
            strength INTEGER NOT NULL DEFAULT 0,
            weapon_damage INTEGER NOT NULL DEFAULT 0,
            inventory_id INTEGER,
            FOREIGN KEY(inventory_id) REFERENCES inventory(id)
            ON DELETE SET NULL ON UPDATE CASCADE
            );
    ''')

    #EVENT TABLE 
    cursor.execute("""CREATE TABLE IF NOT EXISTS event (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            experience INTEGER NOT NULL DEFAULT 0,
            deadline DATETIME DEFAULT NULL,
            FOREIGN KEY(user_id) REFERENCES player(id)
            ON DELETE SET NULL ON UPDATE CASCADE
            );
    """ )

if __name__ == "__main__":
    init()