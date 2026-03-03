"""
编排
"""
from src.config import Config
from src.operate.group_meeting_scheduler import SMCLabGroupMeetingScheduler
from src.data_manager.schedule_parser import SMCLabScheduleParser
from src.crawler.bitable_crawler import SMCLabScheduleCrawler

if __name__ == "__main__":
    config = Config()
    sc = SMCLabScheduleCrawler(config)
    sp = SMCLabScheduleParser(config)
    gms = SMCLabGroupMeetingScheduler(config)
    sc.get_raw_records()
    sp.make_period_summary_json()
    # schedule = gms.schedule_group_meeting(["周三上午", "周三下午"])
    # for key in schedule.keys():
    #     print(key, ":")
    #     for group in schedule[key]:
    #         print(group)

    schedule = gms.schedule_group_meeting(["周三晚上", "周三下午"])
    for key in schedule.keys():
        print(key, ":")
        for group in schedule[key]:
            print(group)