from src.system import SMCLabDailyManager
from src.config import Config



if __name__ == "__main__":
    config = Config()
    system = SMCLabDailyManager(config)
    # system.test()
    # system.send_last_week_summary(users = ["梁涵"],
    #                             #   use_relay=True, 
    #                               # update_seminar_info=True,
    #                               # update_address_book=True,
    #                               update_all=True,
    #                               # backdoor_delete=True,
    #                               )
    system.send_this_week_seminar_preview(users = ["梁涵"],
                                          update_seminar_info=True,
                                          )

    # system.send_this_week_seminar_attendance(user = ["梁涵"])
    
    # system.send_seminar_attendance_byweek(week = 12)
