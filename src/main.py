from app import bot
from db import db_maker

if __name__ == "__main__":
    try:
        db_maker.init()
        bot.run_polling()
    except:
        print('DataBase ERROR')
    