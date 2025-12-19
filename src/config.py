import json
import os
import logging
from dataclasses import dataclass
from typing import Any

@dataclass
class BitableConfig:
    page_size: int = None
    raw_path: str = None
    
    @classmethod
    def from_dict(cls, config_dict: dict):
        return cls(**{
            k: v for k, v in config_dict.items() 
            if k in cls.__annotations__
        })

class Config:
    def __init__(self, config_path="configs/config.json"):
        """
        初始化配置类
        从config.json文件读取配置到类属性中
        
        Args:
            config_path (str): 配置文件路径
        """
        self.config_path = config_path
        self._config = {}
        self._load_config()
        self._set_attributes()
    
    def _load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)

    def _set_attributes(self):
        """将配置项设置为类属性"""
        # 各类路径配置
        path_config = self._config.get("paths", {})
        self.src_path = path_config.get("src_path", "src")
        self.raw_data_path = path_config.get("raw_data_path", "data_raw")
        self.sem_data_path = path_config.get("sem_data_path", "data_sem")
        self.incre_data_path = path_config.get("incre_data_path", "data_incre")
        self.configs_path = path_config.get("configs_path", "configs")

        self.info_base_path = path_config.get("info_base_path", "data_incre/SMCLab学生基础信息.xlsx")
        self.info_plus_path = path_config.get("info_plus_path", "data_incre/SMCLab学生扩展信息.xlsx")

        self.app_tokens_path = path_config.get("app_tokens_path", "configs/app_tokens.json")
        self.bitable_info_path = path_config.get("bitable_info_path", "configs/bitable_info.json")
        self.last_tenant_path = path_config.get("last_tenant_path", "configs/last_tenant.json")
        self.sysu_schedule_path = path_config.get("sysu_schedule_path", "configs/sysu_schedule.json")
        self.sysu_semesters_path = path_config.get("sysu_semesters_path", "configs/sysu_semesters.json")
        self.weekly_todo_path = path_config.get("weekly_todo_path", "configs/weekly_todo.json")
        
        self.post_template_path = path_config.get("post_template_path", "configs/post_template/smc_sum_last_week.json")

        # 日志模块配置
        logger_config = self._config.get("logger", {})
        self.logger_name = logger_config.get("name", "SMCLabDailyManager")
        self.logger_format = logger_config.get("format", "%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s")
        self.logger_level = logger_config.get("level", "INFO")
        self.logger_file = logger_config.get("file", "logs/smclab_daily_manager.log")
        self.logger_max_bytes = logger_config.get("max_bytes", 10485760)
        self.logger_backup_count = logger_config.get("backup_count", 5)

        # 通讯录模块配置
        addressbook_config = self._config.get("addressbook", {})
        self.ab_page_size = addressbook_config.get("page_size", 50)
        self.ab_raw_path = addressbook_config.get("raw_path", "data_raw/address_book_raw_data")
        self.ab_department_id_path = addressbook_config.get("department_id_path", "data_raw/address_book_raw_data/department_id.json")
        self.ab_update_department_id = addressbook_config.get("update_department_id", True)
        self.ab_output_path = addressbook_config.get("output_path", "data_raw/address_book.json")

        # 考勤模块配置
        daily_attendance_config = self._config.get("daily_attendance", {})
        self.da_page_size = daily_attendance_config.get("page_size", 50)
        self.da_group_name = daily_attendance_config.get("group_name", "SMC考勤")
        self.da_raw_path = daily_attendance_config.get("raw_path", "data_raw/attendance_raw_data")
        self.da_group_info_path = daily_attendance_config.get("group_info_path", "data_raw/attendance_raw_data/group_info.json")
        self.da_output_path = daily_attendance_config.get("output_path", "data_raw/attendance.json")

        seminar_attendance_config = self._config.get("seminar_attendance", {})
        self.sa_seminar_start_time = seminar_attendance_config.get("seminar_start_time", 1900)
        self.sa_seminar_end_time = seminar_attendance_config.get("seminar_end_time", 2030)

        # 多维表格配置
        bitable_config = self._config.get("bitable", {})
        self.bitable_info_path = bitable_config.get("bitable_info_path", "configs/bitable_info.json")
        self.weekly_report = BitableConfig.from_dict(bitable_config.get("weekly_report", {}))
        self.schedule = BitableConfig.from_dict(bitable_config.get("schedule", {}))
        self.seminar = BitableConfig.from_dict(bitable_config.get("seminar", {}))
        self.seminar_leave = BitableConfig.from_dict(bitable_config.get("seminar_leave", {}))

        # 小组会议安排配置
        group_meeting_config = self._config.get("group_meeting_scheduler", {})
        self.max_groups_per_period = group_meeting_config.get("max_groups_per_period", 4)
        self.default_periods = group_meeting_config.get("default_periods", [])