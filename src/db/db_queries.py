import sqlite3 as sql

class DataBase:
    def __init__(self, path:str)->None:
        self.__conn = sql.connect(path,detect_types=sql.PARSE_DECLTYPES, check_same_thread = False)
        self.__cursor = self.__conn.cursor()

    def exists(self,id:int) -> bool:
        data = self.__conn.execute("SELECT id FROM player WHERE id=?", (id,)).fetchone()
        if data is None:
            return True
        else:
            return False
    
    def getPLayerInfo(self, id:int):
        return self.__cursor.execute("SELECT * FROM player WHERE id=?", (id, )).fetchone()


    def insert(self, id:int, pet_name:str = "undefined") -> None:
        #inserting player
        self.__cursor.execute("""INSERT INTO player(id,pet_id) VALUES (?,?)""", (id, id,))

        #inserting pet
        self.__cursor.execute("""INSERT INTO pet(id,name,inventory_id) VALUES (?,?,?)""", (id,pet_name, id,))

        #inserting inventory
        self.__cursor.execute("""INSERT INTO inventory(id) VALUES (?)""",(id,))

        #saving
        self.__conn.commit()

    def update(self,tabel:str,id:int, column:str, data) -> None:
        if type(data) is str:
            self.__cursor.execute(f"""UPDATE {tabel} SET {column} = \"{data}\" WHERE id = {id}""")
        else:
            self.__cursor.execute(f"""UPDATE {tabel} SET {column} = {data} WHERE id = {id}""")

    def save(self):
        self.__conn.commit()

    def fetchone(self,table:str,id:int,column:str):
        data = self.__cursor.execute(f"""SELECT {column} FROM {table} WHERE id={id}""").fetchone()

        if data is None:
            raise Exception("nothing")
        else:
            return data[0]