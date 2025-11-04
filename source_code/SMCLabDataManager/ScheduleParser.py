import json, os 
import pandas as pd
from collections import defaultdict
from pathlib import Path

from ..utils import get_year_semester
from ..SMCLabCrawler.BitableCrawler import SMCLabScheduleCrawler

ABS_PATH = os.path.abspath(__file__)        # SMCLabDailyManager\source_code\SMCLabDataManager\ScheduleParser.py
CURRENT_PATH = os.path.dirname(ABS_PATH)    # SMCLabDailyManager\source_code\SMCLabDataManager
SRC_PATH = os.path.dirname(CURRENT_PATH)    # SMCLabDailyManager\source_code
REPO_PATH = os.path.dirname(SRC_PATH)       # SMCLabDailyManager
RAW_DATA_PATH = os.path.join(REPO_PATH, "data_raw") # SMCLabDailyManager\data_raw
SEM_DATA_PATH = os.path.join(REPO_PATH, "data_semester") # SMCLabDailyManager\data_semester

class SMCLabScheduleParser:
    def __init__(self):
        raw_data_path = os.path.join(RAW_DATA_PATH, "schedule_raw_data")
        raw_json_path = os.path.join(raw_data_path, "resp_page_0.json")
        if not os.path.exists(raw_json_path):
            client = SMCLabScheduleCrawler()
            client.get_raw_records() 
        with open(raw_json_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)["items"]
        self.time_table = self._build_time_table()
        self.days = ["周一", "周二", "周三", "周四", "周五"]
        semester = get_year_semester()
        self.sem_data_path = os.path.join(SEM_DATA_PATH, semester)
        if not os.path.exists(self.sem_data_path):
            os.makedirs(self.sem_data_path, exist_ok=True)
    
    def _build_time_table(self):
        return {
            "上午": {"第1节": ("08:00", "08:55"), "第2节": ("08:55", "09:40"), 
                   "第3节": ("10:10", "11:05"), "第4节": ("11:05", "11:50")},
            "下午": {"第1节": ("14:20", "15:15"), "第2节": ("15:15", "16:00"), 
                   "第3节": ("16:30", "17:15"), "第4节": ("17:25", "18:10")},
            "晚上": {"第1节": ("19:00", "19:55"), "第2节": ("19:55", "20:50"), 
                   "第3节": ("20:50", "21:35")}
        }
    
    def _all_slots(self):
        """返回所有时段元组列表 [('上午','第1节'), ('上午','第2节'), ...]"""
        return [(p, s) for p in self.time_table for s in self.time_table[p]]

    def _collect_schedule(self):
        """提取每个工作日每节课的上课同学名单"""
        schedule = {day: defaultdict(list) for day in self.days}
        for item in self.data:
            fields = item.get("fields", {})
            name = fields.get("姓名", [{}])[0].get("text", "未知")
            for day in self.days:
                slots = fields.get(day, [])
                for slot in slots:
                    if "（当天无课程" in slot or "(当天无课程" in slot:
                        continue
                    schedule[day][slot].append(name)
        return schedule

    def make_schedule_count_xlsx(self):
        output_path = os.path.join(self.sem_data_path, "schedule_count.xlsx")
        schedule = self._collect_schedule()
        records = []
        for period, sub in self.time_table.items():
            for section, (start, end) in sub.items():
                row = {"上课节段": f"{period}-{section}", "时间": f"{start}-{end}"}
                for day in self.days:
                    names = schedule[day].get(f"{period}-{section}", [])
                    row[day] = len(names)
                records.append(row)
        df = pd.DataFrame(records)
        df.to_excel(output_path, index=False)
        print(f"课时人数表已保存: {Path(output_path).absolute()}")

    def make_schedule_names_xlsx(self):
        output_path = os.path.join(self.sem_data_path, "schedule_names.xlsx")
        schedule = self._collect_schedule()
        records = []
        for period, sub in self.time_table.items():
            for section, (start, end) in sub.items():
                row = {"上课节段": f"{period}-{section}", "时间": f"{start}-{end}"}
                for day in self.days:
                    names = schedule[day].get(f"{period}-{section}", [])
                    row[day] = ",".join(names)
                records.append(row)
        df = pd.DataFrame(records)
        df.to_excel(output_path, index=False)
        print(f"课时姓名表已保存: {Path(output_path).absolute()}")

    def make_schedule_by_slot_json(self):
        output_path = os.path.join(self.sem_data_path, "schedule_by_slot.json")
        schedule = self._collect_schedule()
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(schedule, f, ensure_ascii=False, indent=4)
        print(f"每节课学生名单JSON已保存: {Path(output_path).absolute()}")

    def make_period_summary_json(self):
        output_path = os.path.join(self.sem_data_path, "schedule_by_period.json")
        schedule = self._collect_schedule()
        summary = {day: {"上午": set(), "下午": set(), "晚上": set()} for day in self.days}
        for day in self.days:
            for slot, names in schedule[day].items():
                period, _ = slot.split("-")
                summary[day][period].update(names)
        # 转换为列表形式
        summary = {d: {p: list(v) for p, v in ps.items()} for d, ps in summary.items()}
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=4)
        print(f"每日三时段学生名单JSON已保存: {Path(output_path).absolute()}")
