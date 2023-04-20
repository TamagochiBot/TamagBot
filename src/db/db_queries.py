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
        # inserting inventory
        inventory_id = self.__cursor.execute("""INSERT INTO inventory DEFAULT VALUES""").lastrowid

        # inserting player
        self.__cursor.execute("""INSERT INTO player(id,is_admin,user_name,pet_name,inventory_id) VALUES (?,?,?,?,?)""",
                              (id, is_admin, user_name, pet_name, inventory_id,))

        self.save()

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

    def update(self, table: str, id:int, column: str, data) -> None:
        '''
        Updates a single column record in the table
        '''
        match table:
            case "player":
                self.__update_player(id, column, data)
            case "inventory":
                self.__update_inventory(id, column, data)
            case "event":
                self.__update_event(id, column, data)
            case "regular_event":
                self.__update_regular_event(id,column,data)
            case _:
                raise ValueError(f"Table does not exist")

    def fetchone(self, table: str, id: int, column: str):
        '''
        Fetches one record from the table
        '''
        match table:
            case "player":
                return self.__fetchone_player(id, column)
            case "inventory":
                return self.__fetchone_inventory(id, column)
            case "event":
                return self.__fetchone_event(id, column)
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
        data = self.__cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = data.fetchone()[0]

        return count

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

    def __update_event(self, id: int, column: str, data) -> None:
        if type(data) is str:
            self.__cursor.execute(
                f"""UPDATE event SET {column} = \'{data}\' WHERE user_id = (SELECT id FROM player WHERE id = {id})""")
        else:
            self.__cursor.execute(
                f"""UPDATE event SET {column} = {data} WHERE user_id = (SELECT id FROM player WHERE id = {id})""")

    def __update_regular_event(self,id: int, column:str, data):
        if type(data) is str:
            self.__cursor.execute(f"""UPDATE regular_event SET {column} = \'{data}\' WHERE id = {id}""")
        else:
            self.__cursor.execute(f"""UPDATE regular_event SET {column} = {data} WHERE id = {id}""")

    def __update_player(self, id: int, column: str, data) -> None:
        if type(data) is str:
            self.__cursor.execute(f"""UPDATE player SET {column} = \'{data}\' WHERE id = {id}""")
        else:
            self.__cursor.execute(f"""UPDATE player SET {column} = {data} WHERE id = {id}""")

    def __update_inventory(self, id: int, column: str, data) -> None:
        if type(data) is str:
            self.__cursor.execute(
                f"""UPDATE inventory SET {column} = \'{data}\' WHERE id = (SELECT inventory_id FROM player WHERE id = {id})""")
        else:
            self.__cursor.execute(
                f"""UPDATE inventory SET {column} = {data} WHERE id = (SELECT inventory_id FROM player WHERE id = {id})""")

    def __fetchone_event(self, id: int, column: str):
        data = self.__cursor.execute(
            f"""SELECT {column} FROM event WHERE user_id=(SELECT id FROM player WHERE id = {id})""").fetchone()

        if data is None:
            return None
        else:
            return data[0]

    def __fetchone_inventory(self, id: int, column: str):
        data = self.__cursor.execute(
            f"""SELECT {column} FROM inventory WHERE id=(SELECT inventory_id FROM player WHERE id = {id})""").fetchone()

        if data is None:
            return None
        else:
            return data[0]

    def __fetchone_player(self, id: int, column: str):
        data = self.__cursor.execute(f"""SELECT {column} FROM player WHERE id={id}""").fetchone()

        if data is None:
            return None
        else:
            return data[0]
        