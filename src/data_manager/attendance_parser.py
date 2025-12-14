import json, os, glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict

from ..utils import TimeParser
from ..common.baseparser import SMCLabBaseParser
from ..crawler.bitable_crawler import SMCLabScheduleCrawler
from ..config import Config

from .schedule_parser import SMCLabScheduleParser
from .excel_manager import SMCLabInfoManager

class SMCLabDailyAttendanceParser(SMCLabBaseParser):
    def __init__(self, config: Config = None):
        if config is None:
            config = Config()
        super().__init__(config)
        self.raw_data_path = config.da_raw_path
        # 要存在学期数据里的
        self.sem_data_path = os.path.join(config.sem_data_path, self._year_semester)
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
        raw_data_files = sorted(glob.glob(os.path.join(self.raw_data_path, f"*_daily_attendance_raw.json")))
        raw_data_file = raw_data_files[-1] # 因为只有一个
        assert os.path.exists(raw_data_file), f"请先下载元数据: {raw_data_file}"
        with open(raw_data_file, "r", encoding="utf-8") as f:
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
        self.logger.info("图像已保存: %s", plot_path)

    def last_week_daily_attendance_to_excel(self, plot = True):
        """把上周的考勤存为表格和图"""
        self.sem_week_path = os.path.join(self.sem_data_path, f"week{self._this_week-1}")
        if not os.path.exists(self.sem_week_path):
            os.makedirs(self.sem_week_path, exist_ok=True)
        self.weekly_output_path = os.path.join(self.sem_week_path, f"SMCLab第{self._this_week-1}周考勤统计.xlsx")

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
        self.logger.info("出席表格已保存: %s", excel_path)

        if plot:
            self._plot_attendance(df_sorted)
    

class SMCLabSeminarAttendanceParser(SMCLabBaseParser):
    def __init__(self, config: Config = None) -> None:
        if config is None:
            config = Config()
        super().__init__(config)
        self.raw_data_path = os.path.join(config.raw_data_path, "attendance_raw_data")
        self.sem_path = os.path.join(self._sem_data_path, self._year_semester)
        self.name_and_id = None

    def _set_info_manager(self):
        info_manager = SMCLabInfoManager()
        self.name_and_id, _, _ = info_manager.map_fields("user_id","姓名")

    def _get_attendance_group_list(self):
        '''
        加载理应参会的同学
        '''
        group_info_path = os.path.join(self.raw_data_path, "attendance_group_info.json")
        if not self.name_and_id:
            self._set_info_manager()
        with open(group_info_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        ids = data.get("group_users_id_list", [])
        self.expected_attendees = set([self.name_and_id[id] for id in ids])

    def load_attendees_from_relay(self, week: int) -> set:
        """
        加载txt文件中的人名集合
        """
        file_path = os.path.join(self.raw_data_path, f"{self._year_semester}_Week{week}_seminar_attendance_relay.txt")
        # 检查文件是否存在，如果不存在则创建
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('')  # 创建空文件
            print(f"文件 {file_path} 不存在，已创建空文件")
        
        # 检查文件是否为空
        while os.path.getsize(file_path) <= 4:  # 文件大小小于等于4字节视为空文件
            print(f"文件 {file_path} 为空，请在文件中添加出席人员信息")
            print("操作完成后，请输入(yes/y)继续读取文件：")
            user_input = input().strip().lower()
            if user_input in ['yes', 'y']:
                break                
        
        # 读取文件内容
        attendees = set()
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    # 查找第一个点，之后的内容为姓名和位置描述
                    if '.' in line:
                        # 提取点之后的内容，然后提取第一个空格之前的内容作为姓名
                        name_part = line.split('.', 1)[1].strip()
                        name = name_part.split()[0]
                        attendees.add(name)
        return attendees

    def _backdoor_delete_spec_names(self, not_attended_names: set):
        """
        删除指定姓名的记录
        """
        # 交互式排除人员
        # TODO: 251209 把这里的名单存到一个文件里
        print("\n=== 交互式排除未出勤人员 ===")
        print("请输入要从名单中排除的人名（按q回车退出）：")
        
        while True:
            user_input = input("输入姓名或q退出: ").strip()
            if user_input.lower() == 'q':
                print("退出交互式排除")
                break
            if user_input in not_attended_names:
                not_attended_names.discard(user_input)
                print(f"已从名单中排除: {user_input}")
            else:
                print(f"{user_input} 不在未出勤名单中")
        return not_attended_names


    def get_attended_names_byweek(self, 
                                  use_relay: bool = True,
                                  week: int = None,
                                  backdoor_delete: bool = False):
        """
        获取指定周所有考勤文件中出现的人员姓名列表（去重）
        """
        # 筛选指定周的考勤文件
        if week is None:
            week = self._this_week
        if not self.name_and_id:
            self._set_info_manager()
        raw_data_files = sorted(glob.glob(os.path.join(self.raw_data_path, f"{self._year_semester}_Week{week}*seminar_attendance_raw*.json"), recursive=True))

        # 使用集合来去重
        attended_names = set()
        self._get_attendance_group_list()

        not_attended_names = self.expected_attendees
        if use_relay:
            # 通过群里的接龙结果输出出勤
            attended_names = self.load_attendees_from_relay(week)
            not_attended_names -= attended_names
        if not use_relay or (use_relay and not attended_names):
            # 通过打卡流水输出出勤
            for file_path in raw_data_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    # 提取所有user_id
                    user_flow_results = data.get("user_flow_results", [])
                    for record in user_flow_results:
                        user_id = record.get("user_id", None)
                        type_attendance = record.get("type")
                        if user_id and user_id in self.name_and_id:
                            name = self.name_and_id[user_id]
                            if name and (type_attendance==0 or type_attendance==6):  # 确保姓名不为空
                                attended_names.add(name)
                                not_attended_names.discard(name)
                except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
                    self.logger.error("处理文件 %s 时出错: %s", file_path, e)
                    continue

        # TODO: 根据请假和上课情况进行自动排除，但是目前只能这么干
        # 打印未出勤人员名单
        self.logger.info("=== 未出勤人员名单 ===")
        if not_attended_names:
            self.logger.info("共有 %d 人未出勤：", len(not_attended_names))
            for i, name in enumerate(sorted(not_attended_names), 1):
                self.logger.info("%d. %s", i, name)
        else:
            self.logger.info("所有人员均已出勤")
        
        # 交互式排除人员
        if backdoor_delete:
            not_attended_names = self._backdoor_delete_spec_names(not_attended_names)
        
        # 保存到文件
        attended_names_list = sorted(list(attended_names))
        not_attended_names_list = sorted(list(not_attended_names))
        attended_str = ", ".join(attended_names_list) if len(attended_names_list) else "本周未收集到同学们的打卡流水"
        not_attended_str = ", ".join(not_attended_names_list) if len(not_attended_names_list) else "本周打卡流水全齐"
        sem_week_path = os.path.join(self.sem_path, f"week{week}")
        output_path = os.path.join(sem_week_path, f"SMCLab第{week}周组会考勤统计.txt")
        if not os.path.exists(sem_week_path):
            os.makedirs(sem_week_path, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"{attended_str}\n")  # 第一行：出现的姓名
            f.write(f"{not_attended_str}")  # 第二行：未出现的姓名
        self.logger.info("组会出勤: %s", attended_names)
        self.logger.info("组会未出勤: %s", not_attended_names)
        # 转换为列表并按字母排序返回

    def get_last_week_attended_names(self, use_relay: bool = False):
        return self.get_attended_names_byweek(week=self._this_week-1, use_relay=use_relay)

    def get_this_week_attended_names(self, use_relay: bool = True):
        return self.get_attended_names_byweek(week=self._this_week, use_relay=use_relay)
