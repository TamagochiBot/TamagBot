from src.db.db_queries import DataBase

db = DataBase('testDB.db')


class Player:
    def __init__(self):
        self._id = 0

    def setId(self, id):
        self._id = id

    def getBalance(self):
        return db.fetchone(table='player', id=self._id, column='balance')
