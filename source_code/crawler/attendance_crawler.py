import os, glob
import json
import lark_oapi as lark
# from lark_oapi.api.bitable.v1 import *
from lark_oapi.api.attendance.v1 import *

from ..common.baseclient import SMCLabClient
from ..utils import TimeParser
from ..data_manager.excel_manager import SMCLabInfoManager

ABS_PATH = os.path.abspath(__file__)        # SMCLabDailyManager\source_code\SMCLabCrawler\AttendanceCrawler.py
CURRENT_PATH = os.path.dirname(ABS_PATH)    # SMCLabDailyManager\source_code\SMCLabCrawler
SRC_PATH = os.path.dirname(CURRENT_PATH)    # SMCLabDailyManager\source_code
REPO_PATH = os.path.dirname(SRC_PATH)       # SMCLabDailyManager
RAW_DATA_PATH = os.path.join(REPO_PATH, "data_raw") # SMCLabDailyManager\data_raw
INCRE_DATA_PATH = os.path.join(REPO_PATH, "data_incremental") # SMCLabDailyManager\data_incremental

# 下载考勤原始数据(按周/月/学期/每周组会进行下载)
class SMCLabAttendanceCrawler(SMCLabClient):
    def __init__(self, 
                 page_size: int = 50):
        super().__init__()
        self.raw_data_path = os.path.join(RAW_DATA_PATH, "attendance_raw_data")
        if not os.path.exists(self.raw_data_path):
            os.makedirs(self.raw_data_path, exist_ok=True)
        self.group_name = "SMC考勤"
        self.group_id = 0
        self.group_users_id_list = []
        self.page_size = page_size
        self.info_manager = SMCLabInfoManager()
        self._remove_past_record()
    
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
        # 取最前面那一个
        self.group_id = resp.data.group_list[0].group_id

    def _get_group_list_user(self):   
        # 下载考勤组成员
        # 参考：https://open.feishu.cn/document/attendance-v1/group/list_user
        if not self.group_id:
            self._get_group_id()
            
        has_more = True
        page_token = ""
        page_cnt = 0
        users_list = []
        print(f"正在下载考勤组成员: ")
        while(has_more):
            print(f"\t请求下载第{page_cnt}页...")
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
        self.group_users_id_list = users_id_list
    
    def _remove_past_record(self):
        search_pattern = os.path.join(self.raw_data_path, "last_week*.json")
        for file_path in glob.glob(search_pattern, recursive=True):
            os.remove(file_path)
        file1 = os.path.join(self.raw_data_path, "attendance_group_info.json")
        if os.path.exists(file1):
            os.remove(os.path.join(self.raw_data_path, "attendance_group_info.json"))
        return

    def get_group_info(self, update = False):
        '''
        该函数用于从 attendance_group_info.json 获取考勤组成员的user_id
        ''' 
        group_info_path = os.path.join(self.raw_data_path, "attendance_group_info.json")
        if not update and os.path.exists(group_info_path):
            print("找到已有考勤组信息!")
            with open(group_info_path, "r", encoding="utf-8") as f:
                group_info = json.load(f)
            self.group_name = group_info.get("group_name", "")
            self.group_id = group_info.get("group_id", 0)
            self.group_users_id_list = group_info.get("group_users_id_list", [])
        else:
            self._get_group_list_user()
            group_info={}
            # TODO: 这里好像有问题
            group_info["group_name"] = self.group_name
            group_info["group_id"] = self.group_id
            group_info["group_users_id_list"] = self.group_users_id_list
            with open(group_info_path, 'w', encoding='utf-8') as f:
                json.dump(group_info,
                          f, ensure_ascii=False, indent=4)
        
        print("获取到考勤组信息:")
        print(f"\tgroup_name:\t{self.group_name}")
        print(f"\tgroup_id:\t{self.group_id}")

    def get_user_stats_fields(self, update = False):
        '''
        这个函数下载了考勤的各个字段的信息，没有被任何函数调用
        '''
        # 参考：https://open.feishu.cn/document/server-docs/attendance-v1/user_stats_data/query-2?appId=cli_a8cd4e246b70d013
        user_stats_fields_path = os.path.join(self.raw_data_path, "user_stats_fields.json")
        print("获取表头信息...")
        if not update and os.path.exists(user_stats_fields_path):
            print(f"表头信息已经存在: {user_stats_fields_path}")
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
            with open(user_stats_fields_path, 'w', encoding='utf-8') as f:
                f.write(resp_json)


    def get_last_week_records(self):
        # 收集方式参考: https://open.feishu.cn/document/server-docs/attendance-v1/user_stats_data/query-3?appId=cli_a8cd4e246b70d013
        # 数据结构参考：https://open.feishu.cn/document/server-docs/attendance-v1/user_stats_data/query-2?appId=cli_a8cd4e246b70d013
        # 简单来说：
        # 1. 51503-1-1: 每天第一次上班的打卡结果
        if not self.group_id:
            self.get_group_info()

        raw_data_path = self.raw_data_path
        last_monday, last_friday = TimeParser.get_last_week_period()
        name_id_pair, _, _ = self.info_manager.map_fields("姓名", "user_id")
        user_ids = self.group_users_id_list 
        my_id = name_id_pair["梁涵"]

        # 构造请求对象
        print("下载上周的考勤数据:")
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
        resp_page_path = os.path.join(raw_data_path, f"last_week({self._year_semester},{self._this_week-1})_attendance_raw.json")
        with open(resp_page_path, 'w', encoding='utf-8') as f:
            f.write(resp_json)

        print("下载完成!")

    def get_this_week_seminar_attendance_flow(self):
        if not self.group_id:
            self.get_group_info()
            
        raw_data_path = self.raw_data_path
        this_group_meeting_day, delta = TimeParser.get_this_week_date(3) # TODO: 以后的学期不一定是3
        
        assert delta >= 0
        name_id_pair, _, _ = self.info_manager.map_fields("姓名", "user_id")
        user_ids = self.group_users_id_list
        my_id = name_id_pair["梁涵"]

        # 构造请求对象
        print("下载这周的组会出勤:")
        request: QueryUserStatsDataRequest = QueryUserStatsDataRequest.builder() \
            .employee_type("employee_id") \
            .request_body(QueryUserStatsDataRequestBody.builder()
                .locale("zh")
                .stats_type("daily")
                .start_date(this_group_meeting_day)
                .end_date(this_group_meeting_day)
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
        resp_page_path = os.path.join(raw_data_path, f"last_week({self._year_semester},{self._this_week})_seminar_attendance_raw.json")
        with open(resp_page_path, 'w', encoding='utf-8') as f:
            f.write(resp_json)

        print("下载完成!")

    def get_my_this_week_seminar_attendance_flow(self):
        def split_ids_into_chunks(user_ids):
            if len(user_ids)>50:
                return [user_ids[i:i + 50] for i in range(0, len(user_ids), 50)]
            else:
                return [user_ids]

        if not self.group_id:
            self.get_group_info()
            
        raw_data_path = self.raw_data_path
        this_group_meeting_day, delta = TimeParser.get_this_week_date(3)
        timestamp_from, timestamp_to = TimeParser.get_timestamps(this_group_meeting_day,
                                                                 start_time="1830",
                                                                 end_time="2200")
        assert delta >= 0
        name_id_pair, _, _ = self.info_manager.map_fields("姓名", "user_id")
        user_ids_chunks = split_ids_into_chunks(self.group_users_id_list)
        my_id = name_id_pair["梁涵"]

        # 构造请求对象
        print("下载这周的组会出勤:")
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
            resp_page_path = os.path.join(raw_data_path, f"this_week({self._year_semester},{self._this_week})_seminar_attendance_raw_{count}.json")
            with open(resp_page_path, 'w', encoding='utf-8') as f:
                f.write(resp_json)
            count += 1

        print("下载完成!")
