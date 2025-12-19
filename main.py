from src.system import SMCLabDailyManager
from src.config import Config
import os, sys



if __name__ == "__main__":
    config = Config()
    system = SMCLabDailyManager(config)
    system.send_last_week_summary(users = ["梁涵"],
                                  use_relay=False, 
                                #   update_all=True,
                                  )
    # system.update_address_book()
