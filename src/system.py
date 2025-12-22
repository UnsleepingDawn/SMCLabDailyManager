import os, sys, glob
import logging
import json
import time
from logging.handlers import RotatingFileHandler
from typing import List

from openpyxl.descriptors.base import NoneSet


# from src.common.baseclient import SMCLabClient
from src.crawler.bitable_crawler import (
    SMCLabWeeklyReportCrawler, 
    SMCLabSeminarCrawler,
    SMCLabSeminarLeaveCrawler,
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
    SMCLabInfoParser,
    SMCLabSeminarParser,
    SMCLabWeeklyReportParser
)
from src.data_manager.seminar_manager import (
    SMCLabSeminarManager
)
from src.data_manager.excel_manager import (
    SMCLabInfoManager
)
from src.message.sender import (
    SMCLabMessageSender
)
from src.config import Config
from src.utils import get_semester_and_week

class SMCLabDailyManager:
    def __init__(self, config: Config = None):
        if not config:
            config = Config()
        self.config = config
        
        self.set_logger()

        _, this_week = get_semester_and_week()
        self._this_week = this_week

        # 发送模块
        self.sender = SMCLabMessageSender(config)
        # 下载模块
        self.attendance_crawler = SMCLabAttendanceCrawler(config)
        self.schedule_crawler = SMCLabScheduleCrawler(config)
        self.weekly_report_crawler = SMCLabWeeklyReportCrawler(config)
        self.seminar_crawler = SMCLabSeminarCrawler(config)
        self.seminar_leave_crawler = SMCLabSeminarLeaveCrawler(config)
        self.address_book_crawler = SMCLabAddressBookCrawler(config)
        # 解析模块
        self.daily_attendance_parser = SMCLabDailyAttendanceParser(config)
        self.seminar_attendance_parser = SMCLabSeminarAttendanceParser(config)
        self.schedule_parser = SMCLabScheduleParser(config)
        self.weekly_report_parser = SMCLabWeeklyReportParser(config)
        self.seminar_parser = SMCLabSeminarParser(config)
        self.seminar_info_parser = SMCLabInfoParser(config)
        self.address_book_parser = SMCLabAddressBookParser(config)
        # 管理模块
        self.seminar_manager = SMCLabSeminarManager(config)

    def set_logger(self):
        self.logger = logging.getLogger(name=self.config.logger_name)
        self.logger.setLevel(logging.DEBUG)
        # 删去之前的log文件
        file_pattern = self.config.logger_file.replace(".log", "*.log")
        for file in glob.glob(file_pattern):
            os.remove(file)
        # 控制台输出器：INFO级别以上的日志输出到控制台
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(self.config.logger_format, datefmt="%Y-%m-%d %H:%M:%S")
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)
        # 文件输出器：DEBUG级别以上的日志输出到文件，文件大小超过max_bytes时轮转
        file_handler = RotatingFileHandler(
            self.config.logger_file, 
            maxBytes=self.config.logger_max_bytes, 
            backupCount=self.config.logger_backup_count
        )
        file_formatter = logging.Formatter(self.config.logger_format, datefmt="%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.propagate = False

    def update_address_book(self):
        # 下载最新的组会表格
        self.seminar_crawler.get_raw_records()
        # 下载通讯录
        self.address_book_crawler.get_raw_records()
        # 下载考勤名单
        self.attendance_crawler.get_group_info(update=True)
        # 把组会表格保存到Excel
        self.seminar_info_parser.save_info_to_excel()
        # 合并信息到Excel
        self.address_book_parser.mark_info_in_excel(update=True)
        last_time_updated = {}
        now = int(time.time())
        last_time_updated["last_address_book_crawle"] = now
        last_time_updated["last_address_book_update"] = now
        last_time_updated["last_seminar_crawle"] = now
        self._update_done_last_time(last_time_updated)

    def send_this_week_seminar_attendance(self, 
                                          user: str = "梁涵",
                                          use_relay: bool =True):
        self.attendance_crawler.get_this_week_seminar_records()
        self.seminar_attendance_parser.get_this_week_attended_names(use_relay=use_relay)
        # 发送消息
        self.sender.send_this_week_seminar_attendance(user)

    def send_last_week_summary(self, 
                               users: str | List[str] = "梁涵",
                               update_all: bool = False,
                               update_address_book: bool = False,
                               update_schedule: bool = False,
                               update_seminar_info: bool = True,
                               use_relay: bool = False,
                               backdoor_delete: bool = False):
        if update_all:
            update_address_book = True
            update_schedule = True
            update_seminar_info = True
        
        info_changed_flag = True if update_address_book or update_schedule else False
            
        weekly_todo_updated = {}
        last_time_updated = {}
        # 更新通讯录
        if update_address_book: # TODO: 不够智能，这里的条件应该判断是否存在文件，如果没有文件依然需要更新
            # 下载最新的组会表格
            self.seminar_crawler.get_raw_records()
            # 下载通讯录
            self.address_book_crawler.get_raw_records()
            # 下载考勤名单
            self.attendance_crawler.get_group_info(update=True)
            # 把组会表格保存到Excel
            self.seminar_info_parser.save_info_to_excel()
            # 合并信息到Excel
            self.address_book_parser.mark_info_in_excel(update=True)
            now = int(time.time())
            last_time_updated["last_address_book_crawle"] = now
            last_time_updated["last_address_book_update"] = now
            last_time_updated["last_seminar_crawle"] = now
            
        # 更新课表
        if update_schedule: # TODO: 不够智能，这里的条件应该判断是否存在文件，如果没有文件依然需要更新
            self.schedule_crawler.get_raw_records() 
            self.schedule_parser.make_period_summary_json()
            now = int(time.time())
            last_time_updated["last_schedule_crawle"] = now

        # 更新组会信息
        if update_seminar_info:
            if not last_time_updated.get("last_seminar_crawle", None):
                self.seminar_crawler.get_raw_records()
            self.seminar_parser.save_info_to_excel()
            self.seminar_manager.update_seminar_schedule()
        
        # 读取 weekly_todo.json 并根据未完成事项执行
        last_week = self._this_week - 1
        todo_items = self._get_todo_items_byweek(week=last_week)
        
        # 根据待办事项状态决定是否执行
        # 下载日常出勤信息
        if not todo_items.get("下载日常出勤信息", False) or update_all or info_changed_flag:
            self.logger.info("执行: 下载日常出勤信息")
            self.attendance_crawler.get_last_week_daily_records()
            self.daily_attendance_parser.last_week_daily_attendance_to_excel()
            weekly_todo_updated["下载日常出勤信息"] = True
        else:
            self.logger.info("跳过: 下载日常出勤信息（已完成）")
        
        # 下载组会出勤信息
        if not todo_items.get("下载组会出勤信息", False) or update_all or info_changed_flag:
            self.logger.info("执行: 下载组会出勤信息")
            self.attendance_crawler.get_last_week_seminar_records()
            self.seminar_leave_crawler.get_last_week_records()
            self.seminar_attendance_parser.get_last_week_attended_names(use_relay, backdoor_delete)
            weekly_todo_updated["下载组会出勤信息"] = True
        else:
            self.logger.info("跳过: 下载组会出勤信息（已完成）")
        
        # 下载周报提交情况
        if not todo_items.get("下载周报提交情况", False) or update_all or info_changed_flag:
            self.logger.info("执行: 下载周报提交情况")
            self.weekly_report_crawler.get_last_week_records()
            self.weekly_report_parser.last_week_weekly_report_to_txt()
            weekly_todo_updated["下载周报提交情况"] = True
        else:
            self.logger.info("跳过: 下载周报提交情况（已完成）")

        # 将完成的任务写回 weekly_todo.json
        if weekly_todo_updated:
            self._update_weekly_todo(week=last_week, updates=weekly_todo_updated)
        if last_time_updated:
            self._update_done_last_time(updates=last_time_updated)
        self.sender.send_last_week_summary(users=users)

    def test(self):
        self.weekly_report_crawler.get_last_week_records()
        self.weekly_report_parser.last_week_weekly_report_to_txt()

    # TODO: 把以下五个函数封装成一个单独的类
    def _get_last_week_todo_items(self) -> dict:
        """
        读取上一周的待办事项，返回一个包含状态的字典。
        若读取失败或不存在对应周数据，返回空字典，调用方将执行所有操作。
        """
        last_week = self._this_week - 1
        return self._get_todo_items_byweek(week=last_week)

    def _get_todo_items_byweek(self, week: int) -> dict:
        """
        读取指定周的待办事项，返回一个包含状态的字典。
        若读取失败或不存在对应周数据，返回空字典，调用方将执行所有操作。
        """
        weekly_todo_path = os.path.join("configs", "todo.json")
        if not os.path.exists(weekly_todo_path):
            return {}
        try:
            with open(weekly_todo_path, 'r', encoding='utf-8') as f:
                weekly_todo_data = json.load(f)
            week_key = f"week{week}"
            weekly_map = weekly_todo_data.get("weekly_todo", {})
            if week_key in weekly_map:
                todo_items = weekly_map[week_key]
                self.logger.info(f"读取到第{week}周的待办事项: {todo_items}")
                return todo_items
        except Exception as e:
            self.logger.warning(f"读取 weekly_todo.json 失败: {e}，将执行所有操作")
        return {}

    def _update_weekly_todo(self, week: int, updates: dict):
        """
        将指定周的待办状态更新为 True，若文件不存在则创建基础结构。
        """
        weekly_todo_path = os.path.join("configs", "todo.json")
        data = {"done_last_time": {},
                "weekly_todo": {}}
        if os.path.exists(weekly_todo_path):
            try:
                with open(weekly_todo_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                self.logger.warning(f"读取 weekly_todo.json 失败，将重新写入基础结构: {e}")

        week_key = f"week{week}"
        weekly_map = data.get("weekly_todo", {})
        week_items = weekly_map.get(week_key, {})
        week_items.update({k: True for k in updates.keys()})
        weekly_map[week_key] = week_items
        data["weekly_todo"] = weekly_map

        try:
            with open(weekly_todo_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            self.logger.info(f"已更新 weekly_todo.json 的 {week_key}: {updates}")
        except Exception as e:
            self.logger.error(f"写入 weekly_todo.json 失败: {e}")

    def _get_done_last_time(self):
        weekly_todo_path = os.path.join("configs", "todo.json")
        if not os.path.exists(weekly_todo_path):
            return {}
        try:
            with open(weekly_todo_path, 'r', encoding='utf-8') as f:
                weekly_todo_data = json.load(f)
            done_last_time = weekly_todo_data.get("done_last_time", {})
            return done_last_time
        except Exception as e:
            self.logger.warning(f"读取 weekly_todo.json 失败: {e}，将执行所有操作")
        return {}

    def _update_done_last_time(self, updates: dict):
        """
        """
        weekly_todo_path = os.path.join("configs", "todo.json")
        data = {"done_last_time": {},
                "weekly_todo": {}}
        if os.path.exists(weekly_todo_path):
            try:
                with open(weekly_todo_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                self.logger.warning(f"读取 weekly_todo.json 失败，将重新写入基础结构: {e}")

        
        done_last_time = data.get("done_last_time", {})
        done_last_time.update(updates)
        data["done_last_time"] = done_last_time

        try:
            with open(weekly_todo_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            self.logger.info(f"已更新 weekly_todo.json 的 done_last_time: {updates}")
        except Exception as e:
            self.logger.error(f"写入 weekly_todo.json 失败: {e}")

