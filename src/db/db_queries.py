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
    
    def add_head_skin(self, id:int, skin:str):
        all_heads = "".join(i+";" for i in self.get_all_head_skins(id)) + skin + ";"
        self.__update_player(id,"available_head_skins", all_heads)

    def add_body_skin(self, id:int, skin:str):
        all_bodies = "".join(i+";" for i in self.get_all_body_skins(id)) + skin + ";"
        self.__update_player(id,"available_body_skins", all_bodies)

    def add_weapon_skin(self, id:int, skin:str):
        all_weapons = "".join(i+";" for i in self.get_all_weapon_skins(id)) + skin + ";"
        self.__update_player(id,"available_weapon_skins", all_weapons)

    def set_exp(self, id:int, exp:int) -> None:
        self.__update_player(id, "experience", exp)

    def set_lvl(self, id:int, lvl:int) -> None:
        self.__update_player(id, "level", lvl)

    def set_user_name(self, id:int, name:str) -> None:
        self.__update_player(id,"user_name",name)

    def set_pet_name(self, id:int, name:str) -> None:
        self.__update_player(id,"pet_name",name)

    def set_health(self, id:int, health:int) -> None:
        self.__update_player(id,"health", health)

    def set_strength(self, id:int, strength:int) -> None:
        self.__update_player(id,"strength", strength)
    
    def set_balance(self, id:int, balance:int) -> None:
        self.__update_player(id, "balance", balance)

    def set_head_skin(self, id:int, skin:str) -> None:
        self.__update_player(id, "head_skin", skin)

    def set_body_skin(self, id:int, skin:str) -> None:
        self.__update_player(id, "body_skin", skin)
    
    def set_weapon_skin(self, id:int, skin:str) -> None:
        self.__update_player(id, "weapon_skin", skin)

    def get_bronze_count(self,id:int) -> int:
        lst = self.__fetchone_player(id, "cases").split(";")
        return int(lst[0])
    
    def get_silver_count(self,id:int) -> int:
        lst = self.__fetchone_player(id, "cases").split(";")
        return int(lst[1])
    
    def get_gold_count(self,id:int) -> int:
        lst = self.__fetchone_player(id, "cases").split(";")
        return int(lst[2])
    
    def get_skin_count(self,id:int) -> int:
        lst = self.__fetchone_player(id, "cases").split(";")
        return int(lst[3])
    
    def set_bronze_count(self,id:int, count:int) -> None:
        lst = self.__fetchone_player(id, "cases").split(";")
        lst[0] = str(count)
        string = "".join(i + ';' for i in lst if i != '')
        self.__update_player(id,"cases",string)
    
    def set_silver_count(self,id:int, count:int) -> None:
        lst = self.__fetchone_player(id, "cases").split(";")
        lst[1] = str(count)
        string = "".join(i + ';' for i in lst if i != '')
        self.__update_player(id,"cases",string)
    
    def set_gold_count(self,id:int, count:int) -> None:
        lst = self.__fetchone_player(id, "cases").split(";")
        lst[2] = str(count)
        string = "".join(i + ';' for i in lst if i != '')
        self.__update_player(id,"cases",string)
    
    def set_skin_count(self,id:int, count:int) -> int:
        lst = self.__fetchone_player(id, "cases").split(";")
        lst[3] = str(count)
        string = "".join(i + ';' for i in lst if i != '')
        self.__update_player(id,"cases",string)

    def get_all_head_skins(self,id:int) -> list:
        return list(string for string in self.__fetchone_player(id, "available_head_skins").split(";") if string != '')
    
    def get_all_body_skins(self,id:int) -> list:
        return list(string for string in self.__fetchone_player(id, "available_body_skins").split(";") if string != '')
    
    def get_all_weapon_skins(self,id:int) -> list:
        return list(string for string in self.__fetchone_player(id, "available_weapon_skins").split(";") if string != '')

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

    def get_user_name(self, id:int) -> str:
        return self.__fetchone_player(id, "user_name")
    
    def get_level(self, id:int) -> int:
        return self.__fetchone_player(id, "level")
    
    def get_pet_name(self, id:int) -> str:
        return self.__fetchone_player(id, "pet_name")
    
    def get_experience(self, id:int) -> int:
        return self.__fetchone_player(id, "experience")
    
    def get_health(self, id:int) -> int:
        return self.__fetchone_player(id, "health")
    
    def get_strength(self, id:int) -> int:
        return self.__fetchone_player(id, "strength")

    def get_balance(self, id:int) -> int:
        return self.__fetchone_player(id, "balance")

    def get_head_skin(self, id:int) -> str:
        return self.__fetchone_player(id, "head_skin")
    
    def get_body_skin(self, id:int) -> str:
        return self.__fetchone_player(id, "body_skin")
    
    def get_weapon_skin(self, id:int) -> str:
        return self.__fetchone_player(id, "weapon_skin")

    def is_admin(self, id:int) -> bool:
        return bool(self.__fetchone_player(id,"is_admin"))

    def create_event(self, id: int, event_name:str = "EVENT",description: str = 'none', experience: int = 0, deadline: str = 0) -> None:
        """
        Inserts an event in the "event" table
        """
        self.__cursor.execute("""INSERT INTO event(user_id,event_name,description,experience,deadline) VALUES (?,?,?,?,?)""",
                              (id, event_name, description, experience, deadline))

        self.save()

    def create_regular_event(self, id:int ,tele_id: int, event_name:str = "EVENT",description: str = 'none', experience: int = 0, deadline: str = 0) -> None:
        """
        Inserts a regular event in the "regular_event" table
        """
        self.__cursor.execute("""INSERT INTO regular_event(id,user_id,event_name,description,experience,deadline) VALUES (?,?,?,?,?,?)""",
                              (id, tele_id, event_name, description, experience, deadline))
        
        self.save()

    def delete_event(self, id: int) -> None:
        """
        Deletes event from the "event" table
        """
        self.__cursor.execute(f"""DELETE FROM event WHERE user_id = {id}""")
        self.save()
    
    def delete_regular(self, id: int) -> None:
        """
        Deletes event from the "regular_event" table
        """
        self.__cursor.execute(f"""DELETE FROM regular_event WHERE id = {id}""")
        self.save()
    
    def get_last_regular(self)->int:
        try:
            data = self.__cursor.execute(f"""SELECT MAX(id) FROM regular_event""").fetchone()
            if data[0] is None:
                return 0
            else:
                return data[0]
        except:
            return 0

    def get_event_name(self, tele_id:int) -> str:
        return self.__fetchone_event(tele_id, "event_name")
    
    def get_event_description(self, tele_id:int) -> str:
        return self.__fetchone_event(tele_id, "description")
    
    def get_event_experience(self, tele_id:int) -> int:
        return self.__fetchone_event(tele_id, "experience")
    
    def get_event_deadline(self, tele_id:int) -> str:
        return self.__fetchone_event(tele_id, "deadline")
    
    def set_event_name(self, tele_id:int, name:str) -> None:
        self.__update_event(tele_id, "name", name)
    
    def set_event_description(self, tele_id:int, description:str) -> None:
        self.__update_event(tele_id, "description",description)
    
    def set_event_experience(self, tele_id:int,exp:int) -> None:
        self.__update_event(tele_id, "experience", exp)
    
    def set_event_deadline(self, tele_id:int, deadline:str) -> None:
        self.__update_event(tele_id, "deadline",deadline)
    
    def get_regular_name(self, id:int) -> str:
        return self.__fetchone_regular(id, "event_name")
    
    def get_regular_description(self, id:int) -> str:
        return self.__fetchone_regular(id, "description")
    
    def get_regular_experience(self, id:int) -> int:
        return self.__fetchone_regular(id, "experience")

    def get_regular_deadline(self, id:int) -> str:
        return self.__fetchone_regular(id, "deadline")
    
    def get_regular_players(self, id:int) -> str:
        return self.__fetchone_regular(id, "list_of_players")
    
    def add_regular_player(self, id:int, name:str):
        players = self.get_regular_players(id)
        players += f" {name}"
        self.set_regular_players(id,players)
    
    def set_regular_players(self, id:int, lst:str):
        self.__update_regular_event(id, "list_of_players", lst)
    
    def set_regular_name(self, id:int, name:str) -> None:
        self.__update_regular_event(id, "name", name)
    
    def set_regular_description(self, id:int, description:str) -> None:
        self.__update_regular_event(id, "description",description)
    
    def set_regular_experience(self, id:int,exp:int) -> None:
        self.__update_regular_event(id, "experience", exp)
    
    def set_regular_deadline(self, id:int, deadline:str) -> None:
        self.__update_regular_event(id, "deadline",deadline)

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

    def save(self) -> None:
        """
        Commits changes
        """
        self.__conn.commit()

    def create_item(self, id:int, type:str, name:str, rarity:str, stats:int, mod:str) -> int:
        '''
        Inserts item to the 'item' table
        return id of item
        '''
        item_id = self.__cursor.execute("""INSERT INTO item(user_id,type,name,rarity,stats,mod) VALUES (?,?,?,?,?,?)""",
                              (id, type, name, rarity, stats, mod,)).lastrowid

        self.save()
        return int(item_id)

    def set_item_type(self, item_id:int, type:str) -> None:
        self.__update_item(item_id,"type", type)

    def set_item_name(self, item_id:int, name:str) -> None:
        self.__update_item(item_id,"name", name)
    
    def set_item_rarity(self, item_id:int, rarity:str) -> None:
        self.__update_item(item_id, "rarity", rarity)

    def set_item_stats(self, item_id:int, stats:int) -> None:
        self.__update_item(item_id,"stats", stats)
    
    def set_item_mod(self, item_id:int, mod:str) -> None:
        self.__update_item(item_id,"mod", mod)

    def get_worn_item_mod(self, tele_id:int, type:str) -> str:
        '''
        function takes tele_id and type of item: "helmet", "chestplate", "item1", "item2"
        returns mod of item
        '''
        try:
            item_id = self.get_item_id(tele_id, type)
            data = self.__fetchone_item(item_id, "mod")
            if data is None:
                return ''
            else:
                return data
        except:
            return ''
        
    def get_worn_item_stats(self, tele_id:int, type:str) -> int:
        '''
        function takes tele_id and type of item: "helmet", "chestplate", "item1", "item2"
        returns mod of item
        '''
        try:
            item_id = self.get_item_id(tele_id, type)
            data = self.__fetchone_item(item_id, "stats")
            if data is None:
                return 0
            else:
                return data
        except Exception as e:
            print(e.args)
            return 0
        
    def get_worn_item_name(self, tele_id:int, type:str) -> str:
        '''
        function takes tele_id and type of item: "helmet", "chestplate", "item1", "item2"
        returns name of item
        '''
        try:
            item_id = self.get_item_id(tele_id, type)
            data = str(self.__fetchone_item(item_id, "name"))
      
            if data is None:
                return "none"
            else:
                return data
        except Exception as e:
            print(e.args)
            return ""  
        
    def get_worn_item_rarity(self, tele_id:int, type:str) -> str:
        '''
        function takes tele_id and type of item: "helmet", "chestplate", "item1", "item2"
        returns name of item
        '''
        try:
            item_id = self.get_item_id(tele_id, type)
            data = self.__fetchone_item(item_id, "rarity")
           
            if data is None:
                return "none"
            else:
                return data
        except Exception as e:
            print(e.args)
            return "none"  

    def get_all_items(self, tele_id:int, type:str) -> list():
        '''
        Takes tele_id and returns all items of one type
        '''
        lst = self.__cursor.execute(
            f"""SELECT * FROM item WHERE user_id = {tele_id} AND type = '{type}'""").fetchall()
        return lst
    
    def set_item(self, tele_id:int, type:str, item_id:int) -> None:
        self.__update_player(tele_id,type,item_id)

    def get_item_id(self, tele_id:int,type:str) -> int:
        """
        Gets item_id of worn item
        """
        try:
            item_id = self.__fetchone_player(tele_id, type)
            if item_id is None:
                return None
            else:
                return item_id
            
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