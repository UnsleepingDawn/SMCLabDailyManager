import os
import json
import lark_oapi as lark
from lark_oapi.api.bitable.v1 import *

from .SMCLabClient import SMCLabClient

ABS_PATH = os.path.abspath(__file__)        # SMCLabDailyManager\source_code\SMCLabCrawler\BitableCrawler.py
CURRENT_PATH = os.path.dirname(ABS_PATH)    # SMCLabDailyManager\source_code\SMCLabCrawler
SRC_PATH = os.path.dirname(CURRENT_PATH)    # SMCLabDailyManager\source_code
REPO_PATH = os.path.dirname(SRC_PATH)       # SMCLabDailyManager
RAW_DATA_PATH = os.path.join(REPO_PATH, "data_raw")

# SMCLabDailyManager\source_code\SMCLabCrawler\table_tokens.json
TABLE_TOKENS_JSON_FILE = os.path.join(CURRENT_PATH, "table_tokens.json") 


class SMCLabBitableCrawler(SMCLabClient):
    def __init__(self, *args,
                 table_name: str = None,
                 app_token: str = None,
                 table_id: str = None,
                 page_size: int = 50):
        super().__init__(*args)
        self.table_name = table_name
        self.app_token = app_token
        self.table_id = table_id
        self.page_size = page_size

        # table_token_name 仅用于索引已知表格
        self.table_token_name = None
        self.raw_data_path = os.path.join(RAW_DATA_PATH, "temp_raw_data")
        if table_name:
            self._set_table_name()
            self._set_table_tokens()
    
    def _set_table_name(self):
        if self.table_name == None:
            raise NotImplementedError(f"不允许空的多维表格")
        elif self.table_name == "Weekly Report":
            self.table_token_name = "weekly_report_table"
            self.raw_data_path = os.path.join(RAW_DATA_PATH, "weekly_report_raw_data")
        elif self.table_name == "Group Meeting":
            self.table_token_name = "group_meeting_table"
            self.raw_data_path = os.path.join(RAW_DATA_PATH, "group_meeting_raw_data")
        elif self.table_name == "Schedule":
            self.table_token_name = "schedule_table"
            self.raw_data_path = os.path.join(RAW_DATA_PATH, "schedule_raw_data")
        else:
            raise NotImplementedError(f"还没有适配该多维表格: {self.table_name}")

    def _set_table_tokens(self):
        with open(TABLE_TOKENS_JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        table_info = data[self.table_token_name]
        self.app_token = table_info["app_token"]
        if self.table_name == "Weekly Report" or self.table_name == "Schedule":
            self.table_id = table_info["table_id"][self._year_semester]
        else:
            self.table_id = table_info["table_id"]
        
    def print_basic_info(self):
        print("Year Semester:", self._year_semester)
        print("Tenant Access Token:", self._tenant_access_token)
        print("Bitable Name:", self.table_name)
        print("Bitable Token:", self.app_token)
        print("Bitable Table ID:", self.table_id)

    def get_raw_records(self):
        # 参考: https://open.feishu.cn/api-explorer?apiName=search&from=op_doc&project=bitable&resource=app.table.record&version=v1

        # 按照分页, 一页页下载
        raw_data_path = self.raw_data_path
        has_more = True
        page_token = ""
        page_cnt = 0
        if not os.path.exists(raw_data_path):
            os.makedirs(raw_data_path, exist_ok=True)
        while(has_more):
            print(f"请求下载第{page_cnt}页...")
            request: SearchAppTableRecordRequest = SearchAppTableRecordRequest.builder() \
                .app_token(self.app_token) \
                .table_id(self.table_id) \
                .page_size(self.page_size) \
                .page_token(page_token) \
                .request_body( \
                    SearchAppTableRecordRequestBody.builder()
                    .build()) \
                .build()
            # 发起请求, 接受响应
            resp: SearchAppTableRecordResponse = self.app_table_record.search(request)
            self._assert_resp(resp) # 响应的合法性检查

            # 保存页面
            resp_json = lark.JSON.marshal(resp.data, indent=4)
            resp_page_path = os.path.join(raw_data_path, f"resp_page_{str(page_cnt)}.json")
            with open(resp_page_path, 'w', encoding='utf-8') as f:
                f.write(resp_json)

            # 更新循环状态
            has_more = resp.data.has_more
            page_token = resp.data.page_token
            page_cnt += 1
        print("下载完成")

# 转用于爬取组会名单统计, 用于汇总人员信息, 记录组会信息
class SMCLabWeeklyReportCrawler(SMCLabBitableCrawler):
    def __init__(self, *args):
        super().__init__(*args, table_name = "Weekly Report")

class SMCLabGourpMeetingCrawler(SMCLabBitableCrawler):
    def __init__(self, *args):
        super().__init__(*args, table_name = "Group Meeting")

class SMCLabScheduleCrawler(SMCLabBitableCrawler):
    def __init__(self, *args):
        super().__init__(*args, table_name = "Schedule")