import json
import os
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
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            else:
                print(f"配置文件 {self.config_path} 不存在")
        except Exception as e:
            print(f"加载配置文件失败: {e}")

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
        
        # 通讯录模块配置
        addressbook_config = self._config.get("addressbook", {})
        self.ab_page_size = addressbook_config.get("page_size", 50)
        self.ab_raw_path = addressbook_config.get("raw_path", "data_raw/address_book_raw_data")
        self.ab_department_id_path = addressbook_config.get("department_id_path", "data_raw/address_book_raw_data/department_id.json")
        self.ab_update_department_id = addressbook_config.get("update_department_id", True)
        self.ab_output_path = addressbook_config.get("output_path", "data_raw/address_book.json")

        # 考勤模块配置
        daily_config = self._config.get("daily_attendance", {})
        self.da_page_size = daily_config.get("page_size", 50)
        self.da_group_name = daily_config.get("group_name", "SMC考勤")
        self.da_raw_path = daily_config.get("raw_path", "data_raw/attendance_raw_data")
        self.da_group_info_path = daily_config.get("group_info_path", "data_raw/attendance_raw_data/group_info.json")
        self.da_update_group_info = daily_config.get("update_group_info", True)
        self.da_output_path = daily_config.get("output_path", "data_raw/attendance.json")

        # 多维表格配置
        bitable_config = self._config.get("bitable", {})
        self.bitable_info_path = bitable_config.get("bitable_info_path", "configs/bitable_info.json")
        self.weekly_report = BitableConfig.from_dict(bitable_config.get("weekly_report", {}))
        self.schedule = BitableConfig.from_dict(bitable_config.get("schedule", {}))
        self.seminar = BitableConfig.from_dict(bitable_config.get("seminar", {}))

