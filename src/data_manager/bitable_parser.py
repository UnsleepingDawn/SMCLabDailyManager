import json
import os
from glob import glob
from openpyxl import Workbook

from ..common.baseparser import SMCLabBaseParser
from ..config import Config
from .excel_manager import SMCLabInfoManager

class SMCLabBitableParser(SMCLabBaseParser):
    def __init__(self, config: Config=None):
        if config is None:
            config = Config()
        super().__init__(config)
        self.raw_data_path = None
        self.file_list = None
        self.output_path = None
        self.info_manager = SMCLabInfoManager(config)

    def _load_json(self, file_path):
        """读取单个 JSON 文件"""
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _get_nested(self, data_dict, keys):
        """安全地提取嵌套字段"""
        try:
            value = data_dict
            for k in keys:
                value = value[k]
            return value
        except (KeyError, IndexError, TypeError):
            return ""

class SMCLabSeminarParser(SMCLabBitableParser):
    def __init__(self, config: Config = None):
        if config is None:
            config = Config()
        super().__init__(config=config)
        self.raw_data_path = config.seminar.raw_path
        self.file_list = sorted(glob(os.path.join(self.raw_data_path, "*seminar_raw*.json")))
        if not self.file_list:
            raise FileNotFoundError(f"未在 {self.raw_data_path} 中找到任何 seminar*.json 文件")
        self.info_base_path = config.info_base_path

    def parse_all(self):
        all_records = []
        for file in self.file_list:
            data = self._load_json(file)
            for item in data.get("items", []):
                fields = item.get("fields", {})
                record = {
                    "姓名": self._get_nested(fields, ["姓名", 0, "text"]),
                    "年级": fields.get("年级", ""),
                    "导师": fields.get("导师", ""),
                    "培养类型": fields.get("培养类型", ""),
                    "在读情况": fields.get("_在读情况", ""),
                    "飞书账号": self._get_nested(fields, ["_飞书账号", 0, "id"]),
                    "学号": fields.get("_学号", ""),
                }
                all_records.append(record)
        print(f"共读取 {len(all_records)} 条记录，来自 {len(self.file_list)} 个 JSON 文件。")
        return all_records

    def save_to_excel(self, output_path: str = None):
        """将所有记录保存为 Excel 文件"""
        if not output_path:
            output_path = self.info_base_path
        records = self.parse_all()

        wb = Workbook()
        ws = wb.active
        ws.title = "飞书多维表格"

        headers = ["姓名", "年级", "导师", "培养类型", "在读情况", "飞书账号", "学号"]
        ws.append(headers)

        for record in records:
            ws.append([record[h] for h in headers])

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        wb.save(output_path)
        print(f"Excel 文件已保存到：{output_path}")


class SMCLabWeeklyReportParser(SMCLabBitableParser):
    def __init__(self, config: Config = None):
        if config is None:
            config = Config()
        super().__init__(config=config)
        self.raw_data_path = config.weekly_report.raw_path
        self.weekly_file_list = sorted(glob(os.path.join(self.raw_data_path, "*weekly_report_raw*.json")))
        # 要存在学期数据里的
        self.sem_path = os.path.join(self._sem_data_path, self._year_semester)

    def _get_group_info(self, update = False):
        '''
        该函数用于从 attendance_group_info.json 获取考勤组成员的姓名
        SMCLabAttendanceCrawler.get_group_info()
        ''' 
        group_info_path = os.path.join(self.config.raw_data_path, "attendance_raw_data", "attendance_group_info.json")
        id_name_pair, _, _ = self.info_manager.map_fields("user_id", "姓名")
        if not update and os.path.exists(group_info_path):
            print("找到已有考勤组信息!")
            with open(group_info_path, "r", encoding="utf-8") as f:
                group_info = json.load(f)
            group_users_id_list = group_info.get("group_users_id_list", [])
            group_users_name_list = [id_name_pair[id] for id in group_users_id_list]
        else:
            raise RuntimeError("请先调用SMCLabAttendanceCrawler._get_group_list_user")
        return group_users_name_list

    def _simplify_raw_data(self):
        """
        读取原始上周周报文件并提取核心字段：
        - 姓名
        - 飞书账号
        - 文档链接
        - file_token
        - file_name
        :return: 提取后的简化数据列表
        """
        assert len(self.weekly_file_list)!=0, f"请先下载上周的周报元数据"
        simplified_raw = []
        for file in self.weekly_file_list:
            data = self._load_json(file)
            for item in data.get("items", []):
                fields = item.get("fields", {})
                record = {
                    "姓名": self._get_nested(fields, ["汇报人", 0, "name"]),
                    "飞书账号": self._get_nested(fields, ["汇报人", 0, "id"]),
                    "文档链接": self._get_nested(fields, ["文档链接", 0, "link"]),
                    "file_token": self._get_nested(fields, ["附件", 0, "file_token"]),
                    "file_name": self._get_nested(fields, ["附件", 0, "name"]),
                }
                simplified_raw.append(record)
        print(f"共读取 {len(simplified_raw)} 条记录，来自 {len(self.weekly_file_list)} 个 JSON 文件。")
        return simplified_raw
    
    def _check_name_occurrence(self, simplified_raw, group_users_name_list):
        """
        检查总人员姓名列表中哪些出现在simplified_raw中, 哪些没有出现
        
        Args:
            simplified_raw: list of dict, 每个字典包含"姓名"等键
            group_users_name_list: list of str, 总人员姓名列表
        
        Returns:
            tuple: (出现在simplified_raw中的姓名列表, 没有出现的姓名列表, 额外的人)
        """
        # 从simplified_raw中提取所有姓名
        raw_names = set()
        for item in simplified_raw:
            if "姓名" in item and item["姓名"]:  # 确保姓名键存在且不为空
                raw_names.add(item["姓名"])
        
        # 找出出现和没有出现的姓名
        appeared_names = []
        not_appeared_names = []
        
        for name in group_users_name_list:
            if name in raw_names:
                appeared_names.append(name)
                raw_names.remove(name)
            else:
                not_appeared_names.append(name)
        
        extra_in_raw = list(raw_names)

        return appeared_names, not_appeared_names, extra_in_raw
            
    def last_week_weekly_report_to_txt(self):
        """把上周的周报存为txt"""
        simplified_raw_data = self._simplify_raw_data()
        group_users_name_list = self._get_group_info()
        appeared_names, not_appeared_names, extra_in_raw = self._check_name_occurrence(simplified_raw_data, group_users_name_list)
        # 将列表转换为逗号分隔的字符串
        extra_in_str = ", (" + ", ".join(extra_in_raw) + ")" if len(appeared_names) else ""
        if len(appeared_names):
            appeared_str = ", ".join(appeared_names)
        elif extra_in_str:
            appeared_str = ""
        else:
            appeared_str = "本周未收集到同学们的周报"
        not_appeared_str = ", ".join(not_appeared_names) if len(not_appeared_names) else "本周周报全齐"
        # 写入文件
        sem_week_path = os.path.join(self.sem_path, f"week{self._this_week-1}")
        if not os.path.exists(sem_week_path):
            os.makedirs(sem_week_path, exist_ok=True)
        self.weekly_output_path = os.path.join(sem_week_path, f"SMCLab第{self._this_week-1}周周报统计.txt")

        with open(self.weekly_output_path, 'w', encoding='utf-8') as f:
            f.write(f"{appeared_str}{extra_in_str}\n")  # 第一行：出现的姓名
            f.write(f"{not_appeared_str}")  # 第二行：未出现的姓名
        print(f"周报提交情况已保存: {self.weekly_output_path}")

# ======== 使用示例 ========
if __name__ == "__main__":
    output_file = "output/飞书多维表格汇总.xlsx"

    parser = SMCLabSeminarParser()
    parser.save_to_excel()
