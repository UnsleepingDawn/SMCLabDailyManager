"""
测试SMCLabSeminarManager类
"""
from src.config import Config
from src.operate.gourp_meeting_scheduler import SMCLabGroupMeetingScheduler


if __name__ == "__main__":
    config = Config
    gms = SMCLabGroupMeetingScheduler()
    schedule = gms.schedule_group_meeting(["周四上午", "周四下午"])
    for key in schedule.keys():
        print(key, ":")
        for group in schedule[key]:
            print(group)
