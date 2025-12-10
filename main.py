from src.system import SMCLabDailyManager

import os, sys



if __name__ == "__main__":
    system = SMCLabDailyManager()
    system.send_last_week_summary(use_relay=False,
                                  users = ["梁涵"])
