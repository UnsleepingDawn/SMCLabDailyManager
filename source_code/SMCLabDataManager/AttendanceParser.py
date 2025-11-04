import json, os

from typing import List, Dict

from ..utils import TimeParser, get_year_semester, get_semester_and_week

ABS_PATH = os.path.abspath(__file__)        # SMCLabDailyManager\source_code\SMCLabDataManager\AttendanceParser.py
CURRENT_PATH = os.path.dirname(ABS_PATH)    # SMCLabDailyManager\source_code\SMCLabDataManager
SRC_PATH = os.path.dirname(CURRENT_PATH)    # SMCLabDailyManager\source_code
REPO_PATH = os.path.dirname(SRC_PATH)       # SMCLabDailyManager
RAW_DATA_PATH = os.path.join(REPO_PATH, "data_raw")
SEM_DATA_PATH = os.path.join(REPO_PATH, "data_semester")

class SMCLabAttendanceParser:
    def __init__(self):
        sem, week = get_semester_and_week()
        self.raw_data_path = os.path.join(RAW_DATA_PATH, "attendance_raw_data")
        self.input_path = os.path.join(self.raw_data_path, f"last_week({sem},{week-1})_attendance_raw.json")
        assert os.path.exists(self.input_path), "请先下载元数据"
        self.output_path = self.input_path.replace("_raw.json", "_simplified.json")
        self.weekly_summary_path = self.output_path.replace("_simplified.json", "_weekly_summary.json")
        self.sem_data_path = os.path.join(SEM_DATA_PATH, sem)
        self.schedule_path = os.path.join(self.sem_data_path, "schedule_by_period.json")
        
        self.simplified = []

    def simplify_raw_data(self):
        """
        读取原始考勤文件并提取核心字段：
        - name(姓名)
        - user_id(用户ID)
        - date(日期，对应 code=51201)
        - weekday(星期)
        - status(打卡结果，对应 code=51503-1-1)

        :return: 提取后的简化数据列表
        """
        # === 读取原始文件 ===

        with open(self.input_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        simplified = []

        # === 遍历每个用户记录 ===
        for record in data.get("user_datas", []):
            name = record.get("name")
            user_id = record.get("user_id")

            date = None
            status = None

            for d in record.get("datas", []):
                if d.get("code") == "51201":
                    date = d.get("value")
                elif d.get("code") == "51503-1-1":
                    status = d.get("value")

            if name and date and status:
                simplified.append({
                    "name": name,
                    "user_id": user_id,
                    "date": date,
                    "weekday": TimeParser.get_weekday_iso(date),
                    "status": status
                })

        # === 保存结果到文件 ===
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(simplified, f, ensure_ascii=False, indent=4)

        print(f"已生成简化文件：{self.output_path}")
        self.simplified = simplified

    def generate_weekly_summary(self) -> Dict[str, Dict]:
        if len(self.simplified) == 0:
            self.simplify_raw_data()

        summary = {}

        for item in self.simplified:
            name = item["name"]
            user_id = item["user_id"]
            date = item["date"]
            status = item["status"]

            if name not in summary:
                summary[name] = {
                    "user_id": user_id,
                    "week": {}
                }

            summary[name]["week"][date] = status

        with open(self.weekly_summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=4)

        print(f"已生成每周出勤汇总文件：{self.weekly_summary_path}")
    
    def mark_class_absence(self, weekly_summary_path: str = None) -> Dict[str, Dict]:
        # === 读取课表 ===
        schedule_path = self.schedule_path
        assert os.path.exists(schedule_path), "请先下载课表, 并运行解析器里的make_schedule_by_slot_json函数"
        with open(schedule_path, "r", encoding="utf-8") as f:
            schedule = json.load(f)

        # === 读取出勤数据 ===
        weekly_summary_path = self.weekly_summary_path
        if not os.path.exists(weekly_summary_path):
            self.generate_weekly_summary()
        
        with open(weekly_summary_path, "r", encoding="utf-8") as f:
            weekly_summary = json.load(f)

        # === 遍历出勤数据并修改 ===
        for name, info in weekly_summary.items():
            for date, status in info["week"].items():
                if status == "缺卡":
                    weekday_cn = TimeParser.get_weekday_iso(date)
                    # 检查是否在“上午”课表中
                    if weekday_cn and name in schedule.get(weekday_cn, {}).get("上午", []):
                        info["week"][date] = "上课"

        # === 保存修改结果 ===
        updated_path = weekly_summary_path.replace(".json", "_updated.json")
        with open(updated_path, "w", encoding="utf-8") as f:
            json.dump(weekly_summary, f, ensure_ascii=False, indent=4)

        print(f"已更新课表缺卡修正文件：{updated_path}")
        return weekly_summary

