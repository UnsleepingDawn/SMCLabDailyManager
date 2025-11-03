import os
import json
import lark_oapi as lark
# from lark_oapi.api.bitable.v1 import *
from lark_oapi.api.attendance.v1 import *

from .SMCLabClient import SMCLabClient
from ..utils import TimeParser
ABS_PATH = os.path.abspath(__file__)        # SMCLabDailyManager\source_code\SMCLabCrawler\AttendanceCrawler.py
CURRENT_PATH = os.path.dirname(ABS_PATH)    # SMCLabDailyManager\source_code\SMCLabCrawler
SRC_PATH = os.path.dirname(CURRENT_PATH)    # SMCLabDailyManager\source_code
REPO_PATH = os.path.dirname(SRC_PATH)       # SMCLabDailyManager
RAW_DATA_PATH = os.path.join(REPO_PATH, "data_raw")

# 下载考勤原始数据(按周/月/学期/每周组会进行下载)
class SMCLaAttendanceCrawler(SMCLabClient):
    def __init__(self):
        super().__init__()
        self.raw_data_path = os.path.join(RAW_DATA_PATH, "attendance_raw_data")

    def get_attendance_group_id(self):
        # TODO: 获取目标考勤组的 ID
        # 参考：https://open.feishu.cn/document/server-docs/attendance-v1/group/search?appId=cli_a8cd4e246b70d013
        return

    def get_attendance_group_list(self):
        # TODO: 获取需要打卡的人和无需打卡的人
        # 参考：https://open.feishu.cn/document/server-docs/attendance-v1/group/list?appId=cli_a8cd4e246b70d013
        # member_clock_type：设置为2（表示查询无需打卡的人员）
        return

    def get_last_week_record(self):
        # 参考: https://open.feishu.cn/document/server-docs/attendance-v1/user_stats_data/query-3?appId=cli_a8cd4e246b70d013

        # 按照分页, 一页页下载
        raw_data_path = self.raw_data_path
        # 获得上周的周一和周五
        last_monday, last_friday = TimeParser.get_last_week_date()
        # TODO: user_ids, my id
        user_ids = [] # 最多两百个
        my_id = ""
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
                .user_id("my_id")
                .build()) \
            .build()
        # 发起请求, 接受响应
        resp: QueryUserStatsDataResponse = self._client.attendance.v1.user_stats_data.query(request)
        self._assert_resp(resp) # 响应的合法性检查

        # 保存页面
        resp_json = lark.JSON.marshal(resp.data, indent=4)
        resp_page_path = os.path.join(raw_data_path, f"last_week_attendance.json")
        with open(resp_page_path, 'w', encoding='utf-8') as f:
            f.write(resp_json)

        print("下载完成")