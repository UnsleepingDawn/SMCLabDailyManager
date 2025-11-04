import json
import os
from glob import glob
from openpyxl import Workbook

ABS_PATH = os.path.abspath(__file__)        # SMCLabDailyManager\source_code\SMCLabDataManager\BitableParser.py
CURRENT_PATH = os.path.dirname(ABS_PATH)    # SMCLabDailyManager\source_code\SMCLabDataManager
SRC_PATH = os.path.dirname(CURRENT_PATH)    # SMCLabDailyManager\source_code
REPO_PATH = os.path.dirname(SRC_PATH)       # SMCLabDailyManager
RAW_DATA_PATH = os.path.join(REPO_PATH, "data_raw") # SMCLabDailyManager\data_raw
INCRE_DATA_PATH = os.path.join(REPO_PATH, "data_incremental") # SMCLabDailyManager\data_incremental

class SMCLabBitableParser:
    def __init__(self, bitable_dir: str = None):
        self.bitable_dir = bitable_dir
        self.raw_data_file = os.path.join(RAW_DATA_PATH, bitable_dir)
        self.file_list = sorted(glob(os.path.join(self.raw_data_file, "resp_page_*.json")))
        self.output_path = None

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

class SMCLabMemberInfoParser(SMCLabBitableParser):
    def __init__(self):
        super().__init__(bitable_dir="group_meeting_raw_data")
        if not self.file_list:
            raise FileNotFoundError(f"未在 {self.raw_data_file} 中找到任何 resp_page_*.json 文件")
        self.output_path = os.path.join(INCRE_DATA_PATH, "SMCLab学生基本信息.xlsx")

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
            output_path = self.output_path
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


# ======== 使用示例 ========
if __name__ == "__main__":
    output_file = "output/飞书多维表格汇总.xlsx"

    parser = SMCLabMemberInfoParser()
    parser.save_to_excel()
