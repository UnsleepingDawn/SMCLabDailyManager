import os
import json
import logging
import pulp
import math
from collections import defaultdict

from ..config import Config
from ..utils import get_semester_and_week
from ..data_manager.excel_manager import SMCLabInfoManager


class SMCLabGroupMeetingScheduler:
    """小组会议调度器，用于自动安排小组会议时间"""

    def __init__(self, config: Config = None) -> None:
        """
        初始化调度器

        Args:
            config: 配置对象, 若为None则使用默认配置
        """
        if config is None:
            config = Config()

        # 初始化 logger
        self.logger = logging.getLogger(config.logger_name)
        self._incre_data_path = config.incre_data_path
        self._sem_data_path = config.sem_data_path
        self._year_semester, self._this_week = get_semester_and_week()

        self.advisor = "陈旭"
        self.periods = config.default_periods
        self.max_groups_per_period = config.max_groups_per_period
        self.name_list = []
        self.already_grouped = []
        self.course_schedule = {}

    def reset_time(self):
        """重置学期和周次信息"""
        self._year_semester, self._this_week = get_semester_and_week()

    def build_student_list(self, advisor: str = None, from_file: bool = True) -> list:
        """
        获取指定导师名下需要开会的学生名单

        Args:
            advisor: 导师姓名, 若为None则使用初始化时的导师

        Returns:
            学生姓名列表
        """
        if from_file:
            group_meeting_name_list_path = os.path.join(
                self._sem_data_path, self._year_semester, "group_meeting_name_list.json"
            )
            if os.path.exists(group_meeting_name_list_path):
                with open(group_meeting_name_list_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, list):
                    raise ValueError(
                        f"group_meeting_name_list.json 格式错误：期望列表，实际为 {type(data).__name__}"
                    )
                self.name_list = data
                self.logger.info(f"已从文件加载学生名单，共 {len(data)} 人")
                return self.name_list
            else:
                with open(group_meeting_name_list_path, "w", encoding="utf-8") as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
                self.logger.info(
                    f"已创建空的学生名单文件: {group_meeting_name_list_path}"
                )

        if advisor is None:
            advisor = self.advisor

        info_manager = SMCLabInfoManager()
        mapping, missing, _ = info_manager.map_fields(
            "导师", "姓名", "在读情况", "in", ["在读", "临近毕业"]
        )

        if advisor not in mapping:
            self.logger.warning(f"未找到导师 '{advisor}' 的学生信息")
            self.name_list = []
            raise RuntimeError()
        else:
            students = mapping[advisor]
            # 确保返回列表格式
            if isinstance(students, list):
                self.name_list = students
            else:
                self.name_list = [students]

        self.logger.info(
            f"已获取 {advisor} 老师的学生名单，共 {len(self.name_list)} 人"
        )
        return self.name_list

    def fetch_course_schedule(self, semester: str = None) -> dict:
        """
        读取指定学期的课程日程文件

        Args:
            semester: 学期标识(如 "2025-Fall"), 若为None则使用当前学期

        Returns:
            课程日程字典，格式为 {周几: {时段: [人名列表]}}
        """
        if semester is None:
            semester = self._year_semester

        schedule_path = os.path.join(
            self._sem_data_path, semester, "schedule_by_period.json"
        )

        if not os.path.exists(schedule_path):
            self.logger.error(f"课程日程文件不存在: {schedule_path}")
            raise FileNotFoundError(f"课程日程文件不存在: {schedule_path}")

        with open(schedule_path, "r", encoding="utf-8") as f:
            self.course_schedule = json.load(f)

        self.logger.info(f"已加载学期 {semester} 的课程日程")
        return self.course_schedule

    def fetch_already_grouped(self, semester: str = None) -> list:
        """
        读取已分组信息

        Args:
            semester: 学期标识, 若为None则使用当前学期

        Returns:
            已分组的嵌套列表，如 [["张三", "李四"], ["王五", "赵六"]]
        """
        if semester is None:
            semester = self._year_semester
        already_grouped_path = os.path.join(
            self._sem_data_path, semester, "already_grouped.json"
        )

        if os.path.exists(already_grouped_path):
            with open(already_grouped_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 检查是否为嵌套列表
            if not isinstance(data, list):
                raise ValueError(
                    f"already_grouped.json 格式错误：期望列表，实际为 {type(data).__name__}"
                )
            for idx, group in enumerate(data):
                if not isinstance(group, list):
                    raise ValueError(
                        f"already_grouped.json 格式错误：第 {idx} 项期望为列表，实际为 {type(group).__name__}"
                    )
            self.already_grouped = data
            self.logger.info(f"已加载已分组信息，共 {len(data)} 组")
        else:
            # 文件不存在，创建空列表
            self.already_grouped = []
            with open(already_grouped_path, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            self.logger.info(f"已创建空的已分组文件: {already_grouped_path}")

        return self.already_grouped

    def schedule_group_meeting(
        self,
        periods: list = None,
        max_groups_per_period: int = None,
        name_list: list = None,
        already_grouped: list = None,
        schedule: dict = None,
    ) -> dict:
        """
        使用整数线性规划安排小组会议

        Args:
            periods: 可用的时间段列表，如 ["周一上午", "周一下午", "周二上午"]
            max_groups_per_period: 每个非最后时间段最多安排的小组数
            already_grouped: 已确定要在一起的人员分组，如 [["张三", "李四"], ["王五", "赵六"]]
            name_list: 参与人员名单，若为None则使用 self.name_list
            schedule: 课程日程，若为None则使用 self.course_schedule

        Returns:
            调度结果，格式为 {时间段: [[小组1成员], [小组2成员], ...]}
        """
        if periods is None:
            periods = self.periods
        if max_groups_per_period is None:
            max_groups_per_period = self.max_groups_per_period
        if name_list is None:
            if not self.name_list:
                self.build_student_list()
            name_list = self.name_list
        if already_grouped is None:
            if not self.already_grouped:
                self.fetch_already_grouped()
            already_grouped = self.already_grouped
        if schedule is None:
            if not self.course_schedule:
                self.fetch_course_schedule()
            schedule = self.course_schedule

        if not name_list:
            raise ValueError("名单为空，请先调用 build_name_list() 获取名单")
        if not schedule:
            raise ValueError("课程日程为空，请先调用 fetch_course_schedule() 加载日程")

        return self._ilp(
            periods=periods,
            max_groups_per_period=max_groups_per_period,
            name_list=name_list,
            schedule=schedule,
            already_grouped=already_grouped,
        )

    def _ilp(
        self,
        periods: list,
        max_groups_per_period: int,
        name_list: list,
        schedule: dict,
        already_grouped: list,
    ):
        I = list(range(len(name_list)))  # 成员集合
        P = list(range(len(periods)))  # 时段集合
        G = list(range(math.ceil(len(name_list) / 2)))  # 潜在的小组集合

        name2id = {name: i for i, name in enumerate(name_list)}
        last_p = P[-1]

        # 人在某半天是否有课
        busy = {}
        for i, name in enumerate(name_list):
            for p, period in enumerate(periods):
                day, half = period[:2], period[2:]
                busy[i, p] = name in schedule.get(day, {}).get(half, [])

        prob = pulp.LpProblem("Unified_Group_Meeting", pulp.LpMinimize)

        # 决策变量
        y = pulp.LpVariable.dicts(
            "y", (I, G), 0, 1, cat="Binary"
        )  # 成员i是否被分配到小组g
        x = pulp.LpVariable.dicts(
            "x", (G, P), 0, 1, cat="Binary"
        )  # 小组g是否被安排在半天p汇报
        z = pulp.LpVariable.dicts("z", G, 0, 1, cat="Binary")  # 表示小组g是否被实际使用
        # 新变量
        s2 = pulp.LpVariable.dicts("s2", G, 0, 1, cat="Binary")  # 小组规模是否为2
        s3 = pulp.LpVariable.dicts("s3", G, 0, 1, cat="Binary")  # 小组规模是否为3
        s4 = pulp.LpVariable.dicts("s4", G, 0, 1, cat="Binary")  # 小组规模是否为4
        l = pulp.LpVariable.dicts(
            "l", G, 0, 1, cat="Binary"
        )  # 最后半天使用指示变量, 表示小组 g 是否被安排在最后一个半天时段
        # 常量
        m = max_groups_per_period

        # 目标：最小化小组数量
        alpha = 2

        prob += pulp.lpSum(1 * s2[g] + 5 * s4[g] + alpha * l[g] for g in G)

        # 每人一个组
        for i in I: # 每位成员必须且只能属于一个小组
            prob += pulp.lpSum(y[i][g] for g in G) == 1

        # 小组规模
        for g in G: # 小组规模必须为 2、3 或 4，且与激活状态一致
            size = pulp.lpSum(y[i][g] for i in I)

            prob += s2[g] + s3[g] + s4[g] == z[g]
            prob += size == 2 * s2[g] + 3 * s3[g] + 4 * s4[g]

        # 小组只在一个半天
        for g in G: # 每个激活的小组必须且只能安排在一个半天汇报
            prob += pulp.lpSum(x[g][p] for p in P) == z[g]

        # 非最后半天容量
        for p in P: # 除最后一个半天外，每个半天最多允许 m 个小组汇报
            if p != last_p:
                prob += pulp.lpSum(x[g][p] for g in G) <= m

        # 课程冲突
        for i in I: # 有课程冲突，则其所在小组不能安排在该半天
            for g in G:
                for p in P:
                    if busy[i, p]:
                        prob += y[i][g] + x[g][p] <= 1

        # 提前组队
        for group in already_grouped:
            ids = [name2id[x] for x in group]
            for g in G:
                for i in ids[1:]:
                    prob += y[ids[0]][g] == y[i][g]
                    
        for g in G: # 小组是否使用最后一个半天
            prob += l[g] == x[g][last_p]

        status = prob.solve(pulp.PULP_CBC_CMD(msg=False))
        if pulp.LpStatus[status] != "Optimal":
            raise RuntimeError("无可行解")

        # 输出
        result = defaultdict(list)
        for g in G:
            if pulp.value(z[g]) == 1:
                members = [name_list[i] for i in I if pulp.value(y[i][g]) == 1]
                for p in P:
                    if pulp.value(x[g][p]) == 1:
                        result[periods[p]].append(members)

        return dict(result)
