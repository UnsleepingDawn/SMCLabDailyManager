import json
import os
from glob import glob
from openpyxl import Workbook

from src.utils import TimeParser

from ..common.baseparser import SMCLabBaseParser
from ..config import Config
from .excel_manager import SMCLabInfoManager

class SMCLabBitableParser(SMCLabBaseParser):
    def __init__(self, config: Config=None):
        if config is None:
            config = Config()
        super().__init__(config)
        self.raw_data_path = None
        self.output_path = None

    def _set_info_manager(self):
        self.info_manager = SMCLabInfoManager()

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

class SMCLabInfoParser(SMCLabBitableParser):
    def __init__(self, config: Config = None):
        if config is None:
            config = Config()
        super().__init__(config=config)
        # 这里使用seminar表格的数据获取数据
        self.raw_data_path = config.seminar.raw_path
        self.info_base_path = config.info_base_path

    def _get_info_from_raw_data(self):
        all_records = []
        file_list = sorted(glob(os.path.join(self.raw_data_path, "*seminar_raw*.json")))
        if not file_list:
            raise FileNotFoundError(f"未在 {self.raw_data_path} 中找到任何 seminar*.json 文件")
        for file in file_list:
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
        self.logger.info("共读取 %d 条记录，来自 %d 个 JSON 文件。", len(all_records), len(file_list))
        return all_records

    def save_info_to_excel(self, output_path: str = None):
        """将所有记录保存为 Excel 文件"""
        if not output_path:
            output_path = self.info_base_path
        records = self._get_info_from_raw_data()

        wb = Workbook()
        ws = wb.active
        ws.title = "SMCLab成员信息"

        headers = ["姓名", "年级", "导师", "培养类型", "在读情况", "飞书账号", "学号"]
        ws.append(headers)

        for record in records:
            ws.append([record[h] for h in headers])

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        wb.save(output_path)
        self.logger.info("成员信息文件已保存到：%s", output_path)

class SMCLabSeminarParser(SMCLabBitableParser):
    def __init__(self, config: Config = None):
        if config is None:
            config = Config()
        super().__init__(config=config)
        self.raw_data_path = config.seminar.raw_path
        self.this_sem_path = os.path.join(config.sem_data_path, self._year_semester)

    def _get_all_text_chunk(self, text_chunks):
        """
        从文本块数组中提取所有文本并用空格拼接
        
        Args:
            text_chunks: 文本块数组，格式为 [{"text": "...", "type": "text"}, ...]
        
        Returns:
            str: 所有文本用空格拼接后的字符串
        """
        if not text_chunks or not isinstance(text_chunks, list):
            return ""
        
        texts = []
        for chunk in text_chunks:
            if isinstance(chunk, dict) and "text" in chunk:
                text = chunk.get("text", "").strip()
                if text:
                    texts.append(text)
        
        return " ".join(texts)

    def _get_info_from_raw_data(self):
        all_records = []
        file_list = sorted(glob(os.path.join(self.raw_data_path, "*seminar_raw*.json")))
        if not file_list:
            raise FileNotFoundError(f"未在 {self.raw_data_path} 中找到任何 seminar*.json 文件")
        for file in file_list:
            data = self._load_json(file)
            for item in data.get("items", []):
                fields = item.get("fields", {})
                last_seminar_date = fields.get("上次讲组会时间", None)
                next_seminar_date = fields.get("近期预期", None)
                if last_seminar_date:
                    last_seminar_date = TimeParser.timestamp_ms_to_date_int(last_seminar_date)
                if next_seminar_date:
                    next_seminar_date = TimeParser.timestamp_ms_to_date_int(next_seminar_date)

                record = {
                    "姓名": self._get_nested(fields, ["姓名", 0, "text"]),
                    "上次讲组会时间": last_seminar_date,
                    "近期预期": next_seminar_date,
                    "是否确认": fields.get("是否确认", ""),
                    "会议室": fields.get("_会议室", ""),
                    "顺序": fields.get("_Track", None),
                    "分享主题": self._get_nested(fields, ["分享主题", 0, "text"]),
                    "摘要": self._get_all_text_chunk(fields.get("摘要", []))
                }
                all_records.append(record)
        self.logger.info("共读取 %d 条记录，来自 %d 个 JSON 文件。", len(all_records), len(file_list))
        return all_records

    def save_info_to_excel(self, output_path: str = None):
        """将所有记录保存为 Excel 文件"""
        if not output_path:
            output_path = os.path.join(self.this_sem_path, "seminar_information.xlsx")
        records = self._get_info_from_raw_data()

        wb = Workbook()
        ws = wb.active
        ws.title = "组会信息"

        headers = ["姓名", "上次讲组会时间", "近期预期", "是否确认", "会议室", "顺序", "分享主题", "摘要"]
        ws.append(headers)

        for record in records:
            ws.append([record[h] for h in headers])

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        wb.save(output_path)
        self.logger.info("组会信息已保存到：%s", output_path)

class SMCLabSeminarLeaveParser(SMCLabBitableParser):
    def __init__(self, config: Config = None):
        if config is None:
            config = Config()
        super().__init__(config=config)
        self.raw_data_path = config.seminar_leave.raw_path
        self.this_sem_path = os.path.join(config.sem_data_path, self._year_semester)

    def get_leave_list(self, week: int):
        """
        从组会请假下载的源文件中提取名字列表
        
        Returns:
            list: 请假人的名字列表
        """
        file_pattern = os.path.join(
            self.raw_data_path, 
            f"{self._year_semester}_Week{week}_seminar_leave_byweek_raw*.json"
        )
        file_list = sorted(glob(file_pattern))
        
        if not file_list:
            return []
        
        name_list = []
        for file in file_list:
            data = self._load_json(file)
            for item in data.get("items", []):
                fields = item.get("fields", {})
                # 从请假人字段中提取名字
                name = self._get_nested(fields, ["请假人", 0, "name"])
                if name:  # 只添加非空的名字
                    name_list.append(name)
        
        self.logger.info(
            "共读取 %d 个请假人名字，来自 %d 个 JSON 文件。", 
            len(name_list), len(file_list)
        )
        return name_list

    def get_last_week_leave_list(self):
        return self.get_leave_list(self._this_week - 1)

class SMCLabWeeklyReportParser(SMCLabBitableParser):
    def __init__(self, config: Config = None):
        if config is None:
            config = Config()
        super().__init__(config=config)
        self.raw_data_path = config.weekly_report.raw_path
        self.group_info_path = config.da_group_info_path
        self.weekly_file_list = []
        self.info_manager = None
        # 要存在学期数据里的
        self.sem_path = os.path.join(self._sem_data_path, self._year_semester)

    def _get_group_info(self, update = False):
        '''
        该函数用于从 attendance_group_info.json 获取考勤组成员的姓名
        SMCLabAttendanceCrawler.get_group_info()
        ''' 
        group_info_path = self.group_info_path
        if not self.info_manager:
            self._set_info_manager()
        id_name_pair, _, _ = self.info_manager.map_fields("user_id", "姓名")
        if not update and os.path.exists(group_info_path):
            self.logger.info("找到已有考勤组信息!")
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
        self.weekly_file_list = sorted(glob(os.path.join(self.raw_data_path, "*weekly_report_byweek_raw*.json")))
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
        self.logger.info("共读取 %d 条记录，来自 %d 个 JSON 文件。", len(simplified_raw), len(self.weekly_file_list))
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
        self.logger.info("周报提交情况已保存: %s", self.weekly_output_path)

# ======== 使用示例 ========
if __name__ == "__main__":
    output_file = "output/飞书多维表格汇总.xlsx"

    parser = SMCLabInfoParser()
    parser.save_info_to_excel()
