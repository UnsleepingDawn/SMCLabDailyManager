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
        self.raw_data_file = os.path.join(self.raw_data_path, f"last_week({sem},{week-1})_attendance_raw.json")
        # 处理过程的中间数据
        self.simplified_path = self.raw_data_file.replace("_raw.json", "_simplified.json")
        self.weekly_summary_path = self.raw_data_file.replace("_raw.json", "_weekly_summary.json")
        self.weekly_summary_updated_path = self.raw_data_file.replace("_raw.json", "_weekly_summary_updated.json")
        # 要存在学期数据里的
        self.sem_data_path = os.path.join(SEM_DATA_PATH, sem)
        self.sem_week_path = os.path.join(self.sem_data_path, f"week{week-1}")
        if not os.path.exists(self.sem_week_path):
            os.makedirs(self.sem_week_path, exist_ok=True)
        self.weekly_output_path = os.path.join(self.sem_week_path, f"SMCLab第{week-1}周考勤统计.xlsx")
        # 课表
        self.schedule_path = os.path.join(self.sem_data_path, "schedule_by_period.json")


    def _simplify_raw_data(self):
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
        assert os.path.exists(self.raw_data_file), f"请先下载元数据: {self.raw_data_file}"
        with open(self.raw_data_file, "r", encoding="utf-8") as f:
            raw = json.load(f)

        simplified_raw = []

        # === 遍历每个用户记录 ===
        for record in raw.get("user_datas", []):
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
                simplified_raw.append({
                    "name": name,
                    "user_id": user_id,
                    "date": date,
                    "weekday": TimeParser.get_weekday_iso(date),
                    "status": status
                })

        # === 保存结果到文件 ===
        return simplified_raw

    def _generate_last_week_attendance(self, simplified_raw) -> Dict[str, Dict]:
        '''
        总结每周出勤情况
        '''
        last_week_attendance = {}

        for item in simplified_raw:
            name = item["name"]
            user_id = item["user_id"]
            date = item["date"]
            status = item["status"]

            if name not in last_week_attendance:
                last_week_attendance[name] = {
                    "user_id": user_id,
                    "week": {}
                }

            last_week_attendance[name]["week"][date] = status

        return last_week_attendance
    
    def _amend_class_absence(self, weekly_summary) -> Dict[str, Dict]:
        '''
        根据课表, 把因为课表导致的缺勤/迟到标记为"上课"
        '''
        # === 读取课表 ===
        schedule_path = self.schedule_path
        # assert os.path.exists(schedule_path), "请先下载课表, 并运行解析器里的make_schedule_by_slot_json函数"
        if not os.path.exists(schedule_path):
            schedule_parser = SMCLabScheduleParser()
            schedule_parser.make_period_summary_json()
        with open(schedule_path, "r", encoding="utf-8") as f:
            schedule = json.load(f)

        # === 遍历出勤数据并修改 ===
        for name, info in weekly_summary.items():
            for date, status in info["week"].items():
                if status != "正常":
                    weekday_cn = TimeParser.get_weekday_iso(date)
                    # 检查是否在“上午”课表中
                    if weekday_cn and name in schedule.get(weekday_cn, {}).get("上午", []):
                        info["week"][date] = "上课"

        weekly_summary_with_mark = weekly_summary

        return weekly_summary_with_mark

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
        plot_path = self.weekly_output_path.replace('.xlsx', '.png')
        plt.savefig(plot_path, dpi=600, bbox_inches='tight')
        print(f"图像已保存: {plot_path}")

    def last_week_attendance_to_excel(self, plot = True):
        """把上周的考勤存为表格和图"""
        excel_path = self.weekly_output_path
        simplified_raw_data = self._simplify_raw_data()
        last_week_attendance = self._generate_last_week_attendance(simplified_raw_data)
        last_week_attendance_with_mark = self._amend_class_absence(last_week_attendance)

        table_data = []
        
        for name, info in last_week_attendance_with_mark.items():
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
        print(f"表格已保存: {excel_path}")

        if plot:
            self._plot_attendance(df_sorted)
    