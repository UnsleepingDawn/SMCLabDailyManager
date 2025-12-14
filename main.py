from src.system import SMCLabDailyManager

import os, sys



if __name__ == "__main__":
    system = SMCLabDailyManager()
    # system.update_address_book()
    system.send_last_week_summary(use_relay=False)
