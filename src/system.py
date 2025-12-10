import os, sys, glob
import logging
from logging.handlers import RotatingFileHandler

from openpyxl.descriptors.base import NoneSet


# from src.common.baseclient import SMCLabClient
from src.crawler.bitable_crawler import (
    SMCLabWeeklyReportCrawler, 
    SMCLabSeminarCrawler,
    SMCLabScheduleCrawler
)

from src.crawler.address_book_crawler import (
    SMCLabAddressBookCrawler
)
from src.crawler.attendance_crawler import (
    SMCLabAttendanceCrawler
)

from src.data_manager.address_book_parser import (
    SMCLabAddressBookParser
)
from src.data_manager.schedule_parser import (
    SMCLabScheduleParser
)
from src.data_manager.attendance_parser import (
    SMCLabDailyAttendanceParser,
    SMCLabSeminarAttendanceParser
)
from src.data_manager.bitable_parser import (
    SMCLabSeminarParser,
    SMCLabWeeklyReportParser
)
from src.message.sender import (
    SMCLabMessageSender
)
from src.config import Config

class SMCLabDailyManager:
    def __init__(self, config: Config = None):
        if not config:
            config = Config()
        self.config = config
        
        self.set_logger()
        # 发送模块
        self.sender = SMCLabMessageSender(config)
        # 下载模块
        self.attendance_crawler = SMCLabAttendanceCrawler(config)
        self.schedule_crawler = SMCLabScheduleCrawler(config)
        self.weekly_report_crawler = SMCLabWeeklyReportCrawler(config)
        self.seminar_crawler = SMCLabSeminarCrawler(config)
        self.address_book_crawler = SMCLabAddressBookCrawler(config)
        # 解析模块
        self.daily_attendance_parser = SMCLabDailyAttendanceParser(config)
        self.seminar_attendance_parser = SMCLabSeminarAttendanceParser(config)
        self.schedule_parser = SMCLabScheduleParser(config)
        self.weekly_report_parser = SMCLabWeeklyReportParser(config)
        self.seminar_parser = SMCLabSeminarParser(config)
        self.address_book_parser = SMCLabAddressBookParser(config)

    def set_logger(self):
        self.logger = logging.getLogger(name=self.config.logger_name)
        self.logger.setLevel(logging.DEBUG)
        # 删去之前的log文件
        file_pattern = self.config.logger_file.replace(".log", "*.log")
        for file in glob.glob(file_pattern):
            os.remove(file)
        # 控制台输出器：INFO级别以上的日志输出到控制台
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter("%(levelname)s - %(message)s")
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)
        # 文件输出器：DEBUG级别以上的日志输出到文件，文件大小超过max_bytes时轮转
        file_handler = RotatingFileHandler(
            self.config.logger_file, 
            maxBytes=self.config.logger_max_bytes, 
            backupCount=self.config.logger_backup_count
        )
        file_formatter = logging.Formatter(self.config.logger_format)
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.propagate = False

    def update_address_book(self):
        # 下载最新的组会表格
        self.seminar_crawler.get_raw_records()
        # 下载通讯录
        self.address_book_crawler.get_raw_records()
        # 把组会表格保存到Excel
        self.seminar_parser.save_to_excel()
        # 合并信息到Excel
        self.address_book_parser.merge_info_to_excel()

    def send_this_week_seminar_attendance(self, 
                                          user: str = "梁涵",
                                          use_relay: bool =True):
        self.attendance_crawler.get_this_week_seminar_records()
        self.seminar_attendance_parser.get_this_week_attended_names(use_relay=use_relay)
        # 发送消息
        self.sender.send_this_week_seminar_attendance(user)

    def send_last_week_summary(self, 
                               users: str or List[str] = "梁涵",
                               update_schedule: bool = False,
                               update_address_book: bool = False,
                               use_relay: bool = True):
        # 更新通讯录
        if update_address_book:
            self.update_address_book()
        # 更新课表
        if update_schedule:
            self.schedule_crawler.get_raw_records() 
            self.schedule_parser.make_period_summary_json()
        # 下载出席记录
        self.attendance_crawler.get_last_week_daily_records()
        self.attendance_crawler.get_last_week_seminar_records()
        self.seminar_attendance_parser.get_last_week_attended_names(use_relay=use_relay)
        self.daily_attendance_parser.last_week_daily_attendance_to_excel()
        # 周报部分
        self.weekly_report_crawler.get_last_week_records()
        self.weekly_report_parser.last_week_weekly_report_to_txt()

        self.sender.send_last_week_summary(users=users)
