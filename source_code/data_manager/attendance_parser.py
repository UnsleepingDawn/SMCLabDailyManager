import json, os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict

from ..utils import TimeParser, get_year_semester, get_semester_and_week
from ..crawler.bitable_crawler import SMCLabScheduleCrawler
from .schedule_parser import SMCLabScheduleParser

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
        self.updated_path = self.weekly_summary_path.replace(".json", "_updated.json")
        # 要存在学期数据里的
        self.sem_data_path = os.path.join(SEM_DATA_PATH, sem)
        self.sem_week_path = os.path.join(self.sem_data_path, f"week{week-1}")
        if not os.path.exists(self.sem_week_path):
            os.makedirs(self.sem_week_path, exist_ok=True)
        self.excel_path = os.path.join(self.sem_week_path, f"SMCLab第{week-1}周考勤统计.xlsx")
        # 课表
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
        # assert os.path.exists(schedule_path), "请先下载课表, 并运行解析器里的make_schedule_by_slot_json函数"
        if not os.path.exists(schedule_path):
            schedule_parser = SMCLabScheduleParser()
            schedule_parser.make_period_summary_json()
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
        self.updated_path = weekly_summary_path.replace(".json", "_updated.json")
        with open(self.updated_path, "w", encoding="utf-8") as f:
            json.dump(weekly_summary, f, ensure_ascii=False, indent=4)

        print(f"已更新课表缺卡修正文件：{self.updated_path}")
        return weekly_summary

    def _plot_attendance(self, df):
                
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']  # 用来正常显示中文标签
        plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
        bar_color = ["#C268C8", "#6BD6D8"]

        # 取前15个同学
        top_15 = df.head(15)
        # 对满足条件的同学姓名进行匿名化处理
        for i in range(len(top_15)):
            if top_15.iloc[i]['缺卡次数'] == 0 and top_15.iloc[i]['迟到次数'] < 3:
                top_15.iloc[i, top_15.columns.get_loc('姓名')] = '***'
        # 创建图形
        fig, ax = plt.subplots(figsize=(5.5, 3), dpi=600)
        
        # 设置柱状图的位置和宽度
        x = range(len(top_15))
        bar_width = 0.35
        
        # 绘制柱状图
        bars1 = ax.bar([i - bar_width/2 for i in x], 
                       top_15['缺卡次数'], 
                       bar_width, 
                       label='缺卡次数', 
                       hatch='xx',
                       edgecolor='black',
                       color=bar_color[0], 
                       alpha=0.7)
        bars2 = ax.bar([i + bar_width/2 for i in x], 
                       top_15['迟到次数'], 
                       bar_width, 
                       label='迟到次数', 
                       hatch='///', 
                       edgecolor='black',
                       color=bar_color[1], 
                       alpha=0.7)
        
        # 设置图表属性
        # ax.set_xlabel('姓名', fontsize=15)
        ax.set_ylabel('次数', fontsize=15)
        ax.set_ylim(0, 6)
        ax.set_yticks(np.arange(0, 6, 1))
        ax.set_title('缺卡和迟到次数统计(前15名)(已排除上课)', fontsize=16, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(top_15['姓名'], rotation=45, ha='right')
        ax.legend(loc='upper center', ncol=2)
        ax.grid(True, axis='y', alpha=0.5, linestyle='--', linewidth=0.5)

        # 调整布局
        plt.tight_layout()
        
        # 保存图片
        plot_path = self.excel_path.replace('.xlsx', '.png')
        plt.savefig(plot_path, dpi=600, bbox_inches='tight')
        print(f"图表已保存: {plot_path}")

    def last_week_attendance_to_excel(self, plot = True):
        """简化版的考勤转换函数"""
        updated_path = self.updated_path
        excel_path = self.excel_path
        if not os.path.exists(updated_path):
            self.mark_class_absence()
        with open(updated_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        table_data = []
        
        for name, info in data.items():
            # 获取并按日期排序考勤记录
            week_data = info['week']
            sorted_dates = sorted(week_data.keys())
            
            # 创建行数据
            row = {'姓名': name}
            
            # 添加每日考勤
            for _, date in enumerate(sorted_dates, 1):
                weekday = TimeParser.get_weekday_iso(date)
                row[weekday] = week_data[date]
            
            # 统计缺卡次数
            row['缺卡次数'] = sum(1 for status in week_data.values() if status == '缺卡')
            row['迟到次数'] = sum(1 for status in week_data.values() if status == '迟到')
            
            table_data.append(row)
        
        # 创建DataFrame并保存
        df = pd.DataFrame(table_data)
        df_sorted = df.sort_values(by=['缺卡次数', '迟到次数'], ascending=[False, False])
        df_sorted.to_excel(excel_path, index=False)
        print(f"表格文件已保存: {excel_path}")

        if plot:
            self._plot_attendance(df_sorted)
        return df
    