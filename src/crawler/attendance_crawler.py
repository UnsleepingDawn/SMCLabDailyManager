import os, glob
import json
import lark_oapi as lark
# from lark_oapi.api.bitable.v1 import *
from lark_oapi.api.attendance.v1 import *

from ..common.baseclient import SMCLabClient
from ..utils import TimeParser
from ..data_manager.excel_manager import SMCLabInfoManager
from ..data_manager.seminar_manager import SMCLabSeminarManager
from ..config import Config
# 下载考勤原始数据(按周/月/学期/每周组会进行下载)
class SMCLabAttendanceCrawler(SMCLabClient):
    def __init__(self, 
                 config: Config = None):
        if config is None:
            config = Config()
        super().__init__(config)
        self.raw_data_path = config.da_raw_path
        if not os.path.exists(self.raw_data_path):
            os.makedirs(self.raw_data_path, exist_ok=True)
        self.page_size = config.da_page_size
        self.group_name = config.da_group_name
        self.group_info_path = config.da_group_info_path
        # 会根据 group_name 来获取 group_id
        self.group_id = 0
        self.group_users_id_list = []
        self.group_users_name_list = []
        # 组会相关配置
        self.seminar_start_time = config.sa_seminar_start_time
        self.seminar_end_time = config.sa_seminar_end_time

        self.info_manager = None
        self.seminar_weekday_map = None
    
    def _set_info_manager(self):
        self.info_manager = SMCLabInfoManager()

    def _set_seminar_manager(self):
        seminar_manager = SMCLabSeminarManager()
        self.seminar_weekday_map = seminar_manager.get_seminar_weekday_map()

    def _check_resp(self, resp: SearchGroupResponse):
        assert resp.code == 0
        assert len(resp.data.group_list) != 0, "未查询到考勤组"

    def _check_resp_2(self, resp: ListUserGroupResponse):
        assert resp.code == 0
        assert len(resp.data.users) != 0, "未查询到考勤组成员"

    def _check_resp_3(self, resp: QueryUserStatsFieldResponse):
        assert resp.code == 0
        
    def _check_resp_4(self, resp: QueryUserStatsDataResponse):
        assert resp.code == 0

    def _get_group_id(self):
        # 获取目标考勤组的 ID
        # 参考：https://open.feishu.cn/document/server-docs/attendance-v1/group/search?appId=cli_a8cd4e246b70d013

        # 发起请求
        request: SearchGroupRequest = SearchGroupRequest.builder() \
            .request_body(SearchGroupRequestBody.builder()
                .group_name(self.group_name)
                .build()) \
            .build()

        resp: SearchGroupResponse = self._client.attendance.v1.group.search(request)
        self._check_resp(resp)
        # 取最前面那一个作为目标考勤组
        self.group_id = resp.data.group_list[0].group_id

    def _get_group_list_user(self, save_name_list: bool = False):   
        # 下载考勤组成员
        # 参考：https://open.feishu.cn/document/attendance-v1/group/list_user
        if not self.group_id:
            self._get_group_id()
        if not self.info_manager and save_name_list:
            self._set_info_manager()
            id_name_pair, _, _ = self.info_manager.map_fields("user_id", "姓名")
        has_more = True
        page_token = ""
        page_cnt = 0
        users_list = []
        self.logger.info("正在下载考勤组成员: ")
        while(has_more):
            self.logger.info("\t请求下载第%d页...", page_cnt)
            # 构造请求对象
            request: ListUserGroupRequest = ListUserGroupRequest.builder() \
                .group_id(self.group_id) \
                .employee_type("employee_id") \
                .dept_type("open_id") \
                .page_size(50) \
                .page_token(page_token) \
                .member_clock_type(1) \
                .build()

            # 发起请求
            resp: ListUserGroupResponse = self._client.attendance.v1.group.list_user(request)
            self._check_resp_2(resp) # 响应的合法性检查

            # 保存页面
            users_list.extend(resp.data.users)

            # 更新循环状态
            has_more = resp.data.has_more
            page_token = resp.data.page_token
            page_cnt += 1

        users_id_list = [user.user_id for user in users_list]
        if save_name_list:
            users_name_list = [id_name_pair[user_id] for user_id in users_id_list]
            self.group_users_name_list = users_name_list
        self.group_users_id_list = users_id_list
        
    
    def _remove_past_daily_record(self):
        search_pattern = os.path.join(self.raw_data_path, "*daily_attendance*.json")
        for file_path in glob.glob(search_pattern, recursive=True):
            os.remove(file_path)

    def _remove_past_seminar_record(self):
        search_pattern = os.path.join(self.raw_data_path, "*seminar_attendance*.json")
        for file_path in glob.glob(search_pattern, recursive=True):
            os.remove(file_path)
        # search_pattern = os.path.join(self.raw_data_path, "*seminar_attendance*.txt")
        # for file_path in glob.glob(search_pattern, recursive=True):
        #     os.remove(file_path)


    def get_group_info(self, update: bool = True):
        '''
        该函数用于从 attendance_group_info.json 获取考勤组成员的user_id
        ''' 
        group_info_path = self.group_info_path
        if not update and os.path.exists(group_info_path):
            self.logger.info("找到已有考勤组信息!")
            with open(group_info_path, "r", encoding="utf-8") as f:
                group_info = json.load(f)
            self.group_name = group_info.get("group_name", "")
            self.group_id = group_info.get("group_id", 0)
            self.group_users_id_list = group_info.get("group_users_id_list", [])
            self.group_users_name_list = group_info.get("group_users_name_list", [])
        else:
            self._get_group_list_user()
            group_info={}
            # TODO: 这里好像有问题
            group_info["group_name"] = self.group_name
            group_info["group_id"] = self.group_id
            group_info["group_users_id_list"] = self.group_users_id_list
            group_info["group_users_name_list"] = self.group_users_name_list
            with open(group_info_path, 'w', encoding='utf-8') as f:
                json.dump(group_info,
                          f, ensure_ascii=False, indent=4)
        
        self.logger.info("获取到考勤组信息:")
        self.logger.info(f"group_name: {self.group_name}")
        self.logger.info(f"group_id: {self.group_id}")

    def get_fields(self, update = False):
        '''
        这个函数下载了考勤的各个字段的信息，没有被任何函数调用
        '''
        # 参考：https://open.feishu.cn/document/server-docs/attendance-v1/user_stats_data/query-2?appId=cli_a8cd4e246b70d013
        fields_path = os.path.join(self.raw_data_path, "fields.json")
        self.logger.info("获取表头信息...")
        if not update and os.path.exists(fields_path):
            self.logger.info("表头信息已经存在: %s", fields_path)
        else:
            last_monday, last_friday = TimeParser.get_last_week_period()
            request: QueryUserStatsFieldRequest = QueryUserStatsFieldRequest.builder() \
                .employee_type("employee_id") \
                .request_body(QueryUserStatsFieldRequestBody.builder()
                    .locale("zh")
                    .stats_type("daily")
                    .start_date(last_monday)
                    .end_date(last_friday)
                    .build()) \
                .build()
            resp: QueryUserStatsFieldResponse = self._client.attendance.v1.user_stats_field.query(request)
            self._check_resp_3(resp)

            # 保存页面
            resp_json = lark.JSON.marshal(resp.data, indent=4)
            with open(fields_path, 'w', encoding='utf-8') as f:
                f.write(resp_json)


    def get_last_week_daily_records(self, 
                                    update_group_info: bool = True):
        # TODO: 写成get_daily_records_byweek
        # 收集方式参考: https://open.feishu.cn/document/server-docs/attendance-v1/user_stats_data/query-3?appId=cli_a8cd4e246b70d013
        # 数据结构参考：https://open.feishu.cn/document/server-docs/attendance-v1/user_stats_data/query-2?appId=cli_a8cd4e246b70d013
        # 与组会打卡查询不同，这里下载的是考勤统计数据：UserStatsData
        # 我们只需要看这个字段：
        # 1. 51503-1-1: 每天第一次上班的打卡结果
        if not self.group_id:
            self.get_group_info(update_group_info)
        if not self.info_manager:
            self._set_info_manager()

        self._remove_past_daily_record()
        raw_data_path = self.raw_data_path
        last_monday, last_friday = TimeParser.get_last_week_period()
        name_id_pair, _, _ = self.info_manager.map_fields("姓名", "user_id")
        user_ids = self.group_users_id_list 
        my_id = name_id_pair["梁涵"]

        # 构造请求对象
        self.logger.info("下载上周的考勤数据:")
        request: QueryUserStatsDataRequest = QueryUserStatsDataRequest.builder() \
            .employee_type("employee_id") \
            .request_body(QueryUserStatsDataRequestBody.builder()
                .locale("zh")
                .stats_type("daily")
                .start_date(last_monday)
                .end_date(last_friday)
                .user_ids(user_ids)
                .need_history(False)
                .current_group_only(True)
                .user_id(my_id)
                .build()) \
            .build()
        # 发起请求, 接受响应
        resp: QueryUserStatsDataResponse = self._client.attendance.v1.user_stats_data.query(request)
        self._check_resp_4(resp) # 响应的合法性检查

        # 保存页面
        resp_json = lark.JSON.marshal(resp.data, indent=4)
        resp_page_path = os.path.join(raw_data_path, f"{self._year_semester}_Week{self._this_week-1}_daily_attendance_raw.json")
        with open(resp_page_path, 'w', encoding='utf-8') as f:
            f.write(resp_json)

        self.logger.info("下载完成!")

    def get_seminar_records_byweek(self, 
                                   week: int, 
                                   update_group_info: bool = True):
        # 参考https://open.feishu.cn/document/server-docs/attendance-v1/user_task/query-2
        # 与日常考勤查询不同，这里下载的是打卡流水数据：UserFlow
        def split_ids_into_chunks(user_ids):
            if len(user_ids)>50:
                return [user_ids[i:i + 50] for i in range(0, len(user_ids), 50)]
            else:
                return [user_ids]
        
        if not self.group_id:
            self.get_group_info(update_group_info) # 保证self.group_users_id_list存在
        self._remove_past_seminar_record()
        if not self.seminar_weekday_map:
            self._set_seminar_manager()
        raw_data_path = self.raw_data_path
        # 返回周几开会
        seminar_weekday = self.seminar_weekday_map.get(str(week), None)
        if not seminar_weekday:
            self.logger.info(f"第{week}周没有组会")
            return
        if week > self._this_week:
            raise ValueError(f"week {week} 大于当前周 {self._this_week}")
        if week == self._this_week:
            seminar_date, delta = TimeParser.get_this_week_date(weekday=seminar_weekday)
            assert delta >= 0, f"当前周 {self._this_week} 开组会"
        else:
            seminar_date = TimeParser.get_week_date(weekday=seminar_weekday, week=week)
        # 用于查询流水区间
        query_start_time = str(self.seminar_start_time - 100)
        query_end_time = str(self.seminar_end_time + 100)
        timestamp_from, timestamp_to = TimeParser.get_sec_level_timestamps(seminar_date,
                                                                 start_time=query_start_time,
                                                                 end_time=query_end_time)
        
        user_ids_chunks = split_ids_into_chunks(self.group_users_id_list)

        # 构造请求对象
        self.logger.info(f"下载{week}周的组会出勤:")
        count = 0
        for user_ids in user_ids_chunks:
            request: QueryUserFlowRequest = QueryUserFlowRequest.builder() \
                .employee_type("employee_id") \
                .include_terminated_user(True) \
                .request_body(QueryUserFlowRequestBody.builder()\
                            .user_ids(user_ids) \
                            .check_time_from(timestamp_from)
                            .check_time_to(timestamp_to)
                            .build()) \
                .build()
            # 发起请求, 接受响应
            resp: QueryUserFlowResponse = self._client.attendance.v1.user_flow.query(request)
            self._check_resp_4(resp) # 响应的合法性检查

            # 保存页面
            resp_json = lark.JSON.marshal(resp.data, indent=4)
            resp_page_path = os.path.join(raw_data_path, f"{self._year_semester}_Week{week}_seminar_attendance_raw_{count}.json")
            with open(resp_page_path, 'w', encoding='utf-8') as f:
                f.write(resp_json)
            count += 1

        self.logger.info("下载完成!")

    def get_this_week_seminar_records(self, 
                                      update_group_info: bool = True):
        self.get_seminar_records_byweek(self._this_week, update_group_info)

    def get_last_week_seminar_records(self,
                                      update_group_info: bool = True):
        self.get_seminar_records_byweek(self._this_week-1, update_group_info)