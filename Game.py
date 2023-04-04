import pickle
import sqlite3


conn = sqlite3.connect('test.db')
c = conn.cursor()
conn.commit()
c.execute('''CREATE TABLE IF NOT EXISTS test (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        obj BLOB
        );
''')


class Player:
    def __init__(self, lvl, name, role):
        self.lvl = int(lvl)
        self.name = name
        self.role = role




a = Player(2, 'rom', 'pal')

with sqlite3.connect('test.db') as connect:
    cur = connect.cursor()
    cur.execute('''INSERT INTO test (obj) VALUES (?);''', (pickle.dumps(a),))
    connect.commit()

with sqlite3.connect('test.db') as connect:
    cur = connect.cursor()
    cur.execute('SELECT obj FROM test WHERE user_id = ?', (1,))
    row = cur.fetchone()
    connect.commit()
    deserialized_person = pickle.loads(row[0])

print(deserialized_person.name)


def intodb(indentificator, a):
    with sqlite3.connect('test.db') as connect:
        cur = connect.cursor()
        cur.execute('''INSERT INTO (user_id,test) (obj) VALUES (?);''', (indentificator, pickle.dumps(a)))
        connect.commit()

def fromdb(identificator):
    cur = connect.cursor()
    cur.execute('SELECT obj FROM test WHERE user_id = ?', (identificator,))
    row = cur.fetchone()
    connect.commit()
    deserialized_person = pickle.loads(row[0])
    return deserialized_person

