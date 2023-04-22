import time

import schedule

from app import bot
from db import db_maker

if __name__ == "__main__":
        db_maker.init()
        #bot.bot.infinity_polling(skip_pending=True) хз, че это
        bot.run_polling()
       # while True:
        #        schedule.run_pending()
        #        time.sleep(1)

