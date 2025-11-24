from source_code.common.baseclient import SMCLabClient
from source_code.crawler.bitable_crawler import (
    SMCLabWeeklyReportCrawler, 
    SMCLabGroupMeetingCrawler,
    SMCLabScheduleCrawler
)

from source_code.crawler.address_book_crawler import (
    SMCLabAddressBookCrawler
)
from source_code.crawler.attendance_crawler import (
    SMCLabAttendanceCrawler
)

from source_code.data_manager.address_book_parser import (
    SMCLabAddressBookParser
)
from source_code.data_manager.schedule_parser import (
    SMCLabScheduleParser
)
from source_code.data_manager.attendance_parser import (
    SMCLabAttendanceParser
)
from source_code.data_manager.bitable_parser import (
    SMCLabMemberInfoParser,
    SMCLabWeeklyReportParser
)
from source_code.message.sender import (
    SMCLabMessageSender
)

# from source_code.app.view.main_window import MainWindow
# 
# from qasync import QEventLoop, asyncio
# from PySide6.QtCore import Qt
# from PySide6.QtWidgets import QApplication

import os, sys

# def main_app():
#     # create application
#     # app = QApplication(sys.argv)
#     # app.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings)
#     # loop = QEventLoop(app)
#     # asyncio.set_event_loop(loop)
# 
#     # w = MainWindow()
#     # w.show()
# 
#     # with loop:
#     #     loop.run_forever()
#     # loop.close()

def send_last_week_summary():
    sender = SMCLabMessageSender()
    # 课表部分
    schedule_crawler = SMCLabScheduleCrawler()
    schedule_crawler.get_raw_records() 
    schedule_parser = SMCLabScheduleParser()
    schedule_parser.make_period_summary_json()
    # 出勤部分
    attendance_crawler = SMCLabAttendanceCrawler()
    attendance_crawler.get_last_week_records()
    attendance_parser = SMCLabAttendanceParser()
    attendance_parser.last_week_attendance_to_excel()
    # 周报部分
    weekly_report_crawler = SMCLabWeeklyReportCrawler()
    weekly_report_crawler.get_last_week_records()
    weekly_report_parser = SMCLabWeeklyReportParser()
    weekly_report_parser.last_week_weekly_report_to_txt()
    address_book_parser = SMCLabAddressBookParser()
    address_book_parser.merge()

    sender.send_last_weekly_summary("陈旭")

def amend_info_every_semester():
    # 组会表格部分
    group_meeting_crawler = SMCLabGroupMeetingCrawler()
    group_meeting_crawler.get_raw_records()
    member_info_parser = SMCLabMemberInfoParser()
    member_info_parser.save_to_excel()
    # 通讯录部分
    address_book_crawler = SMCLabAddressBookCrawler()
    address_book_crawler.get_raw_records() 
    address_book_parser = SMCLabAddressBookParser()
    address_book_parser.merge_info_to_excel()


if __name__ == "__main__":
    # client = SMCLabClient()

    send_last_week_summary()
    # amend_info_every_semester()
