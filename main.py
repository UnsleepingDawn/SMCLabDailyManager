from source_code.common.baseclient import SMCLabClient
from source_code.crawler.bitable_crawler import (
    SMCLabWeeklyReportCrawler, 
    SMCLabGourpMeetingCrawler,
    SMCLabScheduleCrawler
)
from source_code.crawler.address_book_crawler import (
    SMCLabAddressBookCrawler
)
from source_code.crawler.attendance_crawler import (
    SMCLabAttendanceCrawler
)
from source_code.data_manager.schedule_parser import (
    SMCLabScheduleParser
)
from source_code.data_manager.attendance_parser import (
    SMCLabAttendanceParser
)
from source_code.message.sender import (
    SMCLabMessageSender
)

from source_code.app.view.main_window import MainWindow

from qasync import QEventLoop, asyncio
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

import os, sys

def main_app():
    # create application
    app = QApplication(sys.argv)
    app.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    w = MainWindow()
    w.show()

    with loop:
        loop.run_forever()
    loop.close()

if __name__ == "__main__":
    client = SMCLabClient()
    # smclab_gm_client = SMCLabGourpMeetingCrawler()
    # smclab_gm_client.print_basic_info()
    # smclab_gm_client.get_raw_records()

    # smclab_wr_client = SMCLabWeeklyReportCrawler()
    # smclab_wr_client.print_basic_info()
    # smclab_wr_client.get_raw_records()

    # smclab_s_client = SMCLabScheduleCrawler()
    # smclab_s_client.print_basic_info()
    # smclab_s_client.get_raw_records() 

    # smclab_s_parser = SMCLabScheduleParser()
    # smclab_s_parser.make_schedule_count_xlsx()
    # smclab_s_parser.make_schedule_names_xlsx()
    # smclab_s_parser.make_period_summary_json()
    # smclab_s_parser.make_schedule_by_slot_json()

    # smclab_ab_client = SMCLabAddressBookCrawler()
    # smclab_ab_client.get_raw_records() 

    # smclab_a_client = SMCLabAttendanceCrawler()
    # smclab_a_client.get_last_week_record()

    # smclab_a_parser = SMCLabAttendanceParser()
    # smclab_a_parser.last_week_attendance_to_excel(plot=True)

    smclab_sender = SMCLabMessageSender()
    smclab_sender.send_image("梁涵", "D:\\【代码】\\SMCLabDailyManager\\data_semester\\2025-Fall\\week8\\SMCLab第8周考勤统计.png")

    # main_app()