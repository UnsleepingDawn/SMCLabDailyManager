import os
import json
import lark_oapi as lark
# from lark_oapi.api.bitable.v1 import *
from lark_oapi.api.attendance.v1 import *

from .SMCLabClient import SMCLabClient
from ..utils import TimeParser, get_semester_and_week
from ..SMCLabDataManager.ExcelManager import SMCLabInfoManager

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
    
    def _check_resp_1(self, resp: SearchGroupResponse):
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
        self._check_resp_1(resp)
        self.group_id = resp.data.group_list[0].group_id

    def _get_group_list_user(self):
        # TODO: 获取需要打卡的人和无需打卡的人
        # 参考：https://open.feishu.cn/document/attendance-v1/group/list_user
        # member_clock_type：设置为2（表示查询无需打卡的人员）
        if not self.group_id:
            self._get_group_id()
            
        has_more = True
        page_token = ""
        page_cnt = 0
        users_list = []

        while(has_more):
            print(f"请求下载第{page_cnt}页...")
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
    
    def get_group_info(self, update = False):
        group_info_path = os.path.join(self.raw_data_path, "attendance_group_info.json")
        if not update and os.path.exists(group_info_path):
            with open(group_info_path, "r", encoding="utf-8") as f:
                group_info = json.load(f)
            self.group_name = group_info.get("group_name", "")
            self.group_id = group_info.get("group_id", 0)
            self.group_users_id_list = group_info.get("group_users_id_list", [])
        else:
            self._get_group_id()
            self._get_group_list_user()
            group_info={}
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
        # 参考：https://open.feishu.cn/document/server-docs/attendance-v1/user_stats_data/query-2?appId=cli_a8cd4e246b70d013
        user_stats_fields_path = os.path.join(self.raw_data_path, "user_stats_fields.json")
        print("获取表头信息...")
        if not update and os.path.exists(user_stats_fields_path):
            print(f"表头信息已经存在: {user_stats_fields_path}")
            # with open(user_stats_fields_path, "r", encoding="utf-8") as f:
            #     user_stats_fields = json.load(f)
        else:
            last_monday, last_friday = TimeParser.get_last_week_date()
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


    def get_last_week_record(self):
        # 收集方式参考: https://open.feishu.cn/document/server-docs/attendance-v1/user_stats_data/query-3?appId=cli_a8cd4e246b70d013
        # 数据结构参考：https://open.feishu.cn/document/server-docs/attendance-v1/user_stats_data/query-2?appId=cli_a8cd4e246b70d013
        # 简单来说：
        # 1. 51503-1-1: 每天第一次上班的打卡结果
        if not self.group_id:
            self.get_group_info()

        raw_data_path = self.raw_data_path
        last_monday, last_friday = TimeParser.get_last_week_date()
        name_id_pair, _, _ = self.info_manager.map_fields("姓名", "user_id")
        user_ids = self.group_users_id_list 
        my_id = name_id_pair["梁涵"]

        # 检查路径存在性
        if not os.path.exists(raw_data_path):
            os.makedirs(raw_data_path, exist_ok=True)
        # 构造请求对象
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
        sem, week = get_semester_and_week()
        resp_page_path = os.path.join(raw_data_path, f"last_week({sem},{week-1})_attendance_raw.json")
        with open(resp_page_path, 'w', encoding='utf-8') as f:
            f.write(resp_json)

        print("下载完成")