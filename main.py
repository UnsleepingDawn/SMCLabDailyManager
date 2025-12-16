from src.system import SMCLabDailyManager
from src.config import Config
import os, sys



if __name__ == "__main__":
    config = Config()
    system = SMCLabDailyManager(config)
    # system.send_last_week_summary(use_relay=False,
    #                               users = ["梁涵"])
    system.update_address_book()
