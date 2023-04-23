import sqlite3 as sql


class DataBase:
    def __init__(self, path: str) -> None:
        self.__conn = sql.connect(path, detect_types=sql.PARSE_DECLTYPES, check_same_thread=False)
        self.__cursor = self.__conn.cursor()

    def exists(self, table: str, id: int, column:str = 'id') -> bool:
        """
        Checks if there is a record in the table
        """
        data = self.fetchone(table, id, column)

        if data is None:
            return False
        else:
            return True

    def create_player(self, id: int, user_name: str = "undefined", pet_name: str = "undefined", is_admin:bool = False) -> None:
        """
        Inserts a player in the "player" table
        """
        self.__cursor.execute("""INSERT INTO player(id,is_admin,user_name,pet_name) VALUES (?,?,?,?)""",
                              (id, is_admin, user_name, pet_name,))

        self.save()

    def get_player_id(self,user_name:str) -> int:
        '''
        gets player id by user_name
        if there's no player, return None
        '''
        data = self.__cursor.execute(f"""SELECT id FROM player WHERE user_name = '{user_name}'""").fetchone()
        if data is None:
            return None
        else:
            return int(data[0])

    def is_admin(self, id:int) -> bool:
        return bool(self.__fetchone_player(id,"is_admin"))

    def create_event(self, id: int, event_name:str = "EVENT",description: str = 'none', experience: int = 0, deadline: str = 0) -> None:
        """
        Inserts an event in the "event" table
        """
        self.__cursor.execute("""INSERT INTO event(user_id,event_name,description,experience,deadline) VALUES (?,?,?,?,?)""",
                              (id, event_name, description, experience, deadline))

        self.save()

    def create_regular_event(self, id: int, event_name:str = "EVENT",description: str = 'none', experience: int = 0, deadline: str = 0) -> None:
        """
        Inserts a regular event in the "regular_event" table
        """
        self.__cursor.execute("""INSERT INTO regular_event(user_id,event_name,description,experience,deadline) VALUES (?,?,?,?,?)""",
                              (id, event_name, description, experience, deadline))
        
        self.save()

    def update(self, table: str, id:int, column: str, data, type_of_item:str = '') -> None:
        '''
        Updates a single column record in the table
        requires save() after all changes!
        '''
        match table:
            case "player":
                self.__update_player(id, column, data)
            case "item":
                self.__update_item(id, type_of_item, column, data)
            case "event":
                self.__update_event(id, column, data)
            case "regular_event":
                self.__update_regular_event(id,column,data)
            case _:
                raise ValueError(f"Table does not exist")

    def fetchone(self, table: str, id: int, column: str, type_of_item:str = ''):
        '''
        Fetches one record from the table
        '''
        match table:
            case "player":
                return self.__fetchone_player(id, column)
            case "item":
                return self.__fetchone_item(id, type_of_item, column)
            case "event":
                return self.__fetchone_event(id, column)
            case "regular_event":
                return self.__fetchone_regular(id,column)
            case _:
                raise ValueError(f"Table does not exist")
            
    def fetchall(self, table:str) -> list:
        """
        Fetches all records from the table
        """
        lst = self.__cursor.execute(f"""SELECT * FROM {table}""").fetchall()
        return lst

    def fetchall_in_one(self, table:str, column:str) -> list:
        """
        Fetches all records from the table
        """
        lst = self.__cursor.execute(f"""SELECT {column} FROM {table}""").fetchall()
        return lst

    def count_rows(self, table_name: str) -> int:
        '''
        Counts the number of table rows
        '''
        try:
            data = self.__cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = data.fetchone()[0]

            return count
        except:
            return 0
    
    def get_last_regular(self)->int:
        try:
            data = self.__cursor.execute(f"""SELECT MAX(id) FROM regular_event""").fetchone()
            if data is None:
                return 0
            else:
                return data[0]
        except:
            return 0

    def save(self) -> None:
        """
        Commits changes
        """
        self.__conn.commit()

    def delete_event(self, id: int):
        """
        Deletes event from the "event" table
        """
        self.__cursor.execute(f"""DELETE FROM event WHERE user_id = {id}""")
        self.save()
    
    def delete_regular(self, id: int):
        """
        Deletes event from the "regular_event" table
        """
        self.__cursor.execute(f"""DELETE FROM regular_event WHERE id = {id}""")
        self.save()

    def get_item_mod(self, id:int, type:str) -> str:
        '''
        function takes tele_id and type of item: "helmet", "chestplate", "item1", "item2"
        returns mod of item
        '''
        try:
            item_id = self.get_item_id(id, type)
            data = self.__fetchone_item(item_id, type, "mod")
            if data is None:
                return ''
            else:
                return data[0]
        except:
            return ''
        
    def get_item_stats(self, id:int, type:str) -> int:
        '''
        function takes tele_id and type of item: "helmet", "chestplate", "item1", "item2"
        returns mod of item
        '''
        try:
            item_id = self.get_item_id(id, type)
            data = self.__fetchone_item(item_id, type, "stats")
            if data is None:
                return 0
            else:
                return data[0]
        except:
            return 0
        
    def get_all_items(self, id:int, type:str) -> list():
        '''
        Takes tele_id and returns all items of one type
        '''
        lst = self.__cursor.execute(
            f"""SELECT * FROM item WHERE user_id = {id} AND type = '{type}'""").fetchall()
        return lst
    
    def set_item(self, id:int, type:str, item_id:int) -> None:
        self.__update_player(id,type,item_id)

    def create_item(self, id:int, type:str, name:str, stats:int, mod:str) -> None:
        '''
        Inserts item to the 'item' table
        '''
        self.__cursor.execute("""INSERT INTO item(user_id,type,name,stats,mod) VALUES (?,?,?,?,?)""",
                              (id, type, name, stats, mod,))
        
        self.save()

    def get_item_id(self, id:int,type:str) -> int:
        """
        Gets item_id of worn item
        """
        try:
            item_id = self.__cursor.execute(
                f"""SELECT {type} FROM item""").fetchone()[0]
            
            return None if item_id is None else item_id
        except:
            return None

    def __update_event(self, id: int, column: str, data) -> None:
        if type(data) is str:
            self.__cursor.execute(
                f"""UPDATE event SET {column} = \'{data}\' WHERE user_id = (SELECT id FROM player WHERE id = {id})""")
        else:
            self.__cursor.execute(
                f"""UPDATE event SET {column} = {data} WHERE user_id = (SELECT id FROM player WHERE id = {id})""")

    def __update_regular_event(self,id: int, column:str, data) -> None:
        if type(data) is str:
            self.__cursor.execute(f"""UPDATE regular_event SET {column} = \'{data}\' WHERE id = {id}""")
        else:
            self.__cursor.execute(f"""UPDATE regular_event SET {column} = {data} WHERE id = {id}""")

    def __update_player(self, id: int, column: str, data) -> None:
        if type(data) is str:
            self.__cursor.execute(f"""UPDATE player SET {column} = \'{data}\' WHERE id = {id}""")
        else:
            self.__cursor.execute(f"""UPDATE player SET {column} = {data} WHERE id = {id}""")

    def __update_item(self, id: int, column: str, data) -> None:
        try:
            #item_id = self.__get_item_id(id,type)
            if type(data) is str:
                self.__cursor.execute(
                    f"""UPDATE item SET {column} = \'{data}\' WHERE id = {id}""")
            else:
                self.__cursor.execute(
                    f"""UPDATE item SET {column} = {data} WHERE user_id = {id}""")
        except:
            print("nothing")

    def __fetchone_event(self, id: int, column: str):
        data = self.__cursor.execute(
            f"""SELECT {column} FROM event WHERE user_id=(SELECT id FROM player WHERE id = {id})""").fetchone()

        if data is None:
            return None
        else:
            return data[0]
        
    def __fetchone_regular(self, id: int, column: str):
        data = self.__cursor.execute(
            f"""SELECT {column} FROM regular_event WHERE id = {id}""").fetchone()

        if data is None:
            return None
        else:
            return data[0]

    def __fetchone_item(self, id: int, column: str):
        try:
            #item_id = self.__get_item_id(id,type)
            data = self.__cursor.execute(
                f"""SELECT {column} FROM item WHERE id={id}""").fetchone()

            if data is None:
                return None
            else:
                return data[0]
        except:
            return None

    def __fetchone_player(self, id: int, column: str):
        data = self.__cursor.execute(f"""SELECT {column} FROM player WHERE id={id}""").fetchone()

        if data is None:
            return None
        else:
            return data[0]
