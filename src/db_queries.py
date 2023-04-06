import sqlite3 as sql

class DataBase:
    def __init__(self, path:str)->None:
        self.__conn = sql.connect(path)
        self.__cursor = self.__conn.cursor()

        #количество записей
        self.__count = self.__cursor.execute("SELECT COUNT(*) FROM player").fetchone()[0]

    def get_count(self):
        return self.__count

    def exists(self,id:int) -> bool:
        data = self.__conn.execute("SELECT id FROM player WHERE tele_id=?", (id,)).fetchone()
        if data is None:
            return True
        else:
            return False

    def insert(self, id:int, pet_name:str = "undefined") -> None:
        #one more entry in db
        self.__count+=1

        '''self.__add_player(id)
        #self.__add_pet(str)
        #self.__add_inventory()'''
        
        #inserting player
        self.__cursor.execute("""INSERT INTO player(tele_id,pet_id) VALUES (?,?)""", (id, self.__count,))

        #inserting pet
        self.__cursor.execute("""INSERT INTO pet(name,inventory_id) VALUES (?,?)""", (pet_name, self.__count,))

        #inserting inventory
        self.__cursor.execute("""INSERT INTO inventory(id) VALUES (?)""",(self.__count,))

        #saving
        self.__conn.commit()
    
    '''
    def __add_player(self, id:int):
        self.__cursor.execute("""INSERT INTO player(tele_id,pet_id) VALUES (?,?)""", (id, self.count))
    
    def __add_pet(self,name:str):
        self.__cursor.execute("""INSERT INTO pet(name,inventory_id) VALUES (?,?)""", (str, self._count,))
    
    def __add_inventory(self):
        self.__cursor.execute("""INSERT INTO inventory() VALUES""")
'''
    def update(self,tabel:str,id:int, column:str, data) -> None:
        if type(data) is str:
            self.__cursor.execute(f"""UPDATE {tabel} SET {column} = \"{data}\" WHERE id = {id}""")
        else:
            self.__cursor.execute(f"""UPDATE {tabel} SET {column} = {data} WHERE id = {id}""")

        self.__conn.commit()

    def fetchone(self,table:str,id:int,column:str):
        data = self.__cursor.execute(f"""SELECT {column} FROM {table} WHERE id={id}""").fetchone()

        if data is None:
            raise Exception("nothing")
        else:
            return data[0]
