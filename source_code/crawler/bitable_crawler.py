import os, glob
import json
import lark_oapi as lark
from lark_oapi.api.bitable.v1 import *

from ..common.baseclient import SMCLabClient
from ..utils import TimeParser, get_semester_and_week

ABS_PATH = os.path.abspath(__file__)        # SMCLabDailyManager\source_code\SMCLabCrawler\BitableCrawler.py
CURRENT_PATH = os.path.dirname(ABS_PATH)    # SMCLabDailyManager\source_code\SMCLabCrawler
SRC_PATH = os.path.dirname(CURRENT_PATH)    # SMCLabDailyManager\source_code
REPO_PATH = os.path.dirname(SRC_PATH)       # SMCLabDailyManager
RAW_DATA_PATH = os.path.join(REPO_PATH, "data_raw")

TABLE_TOKENS_JSON_FILE = os.path.join("config", "bitable_info.json") 


class SMCLabBitableCrawler(SMCLabClient):
    def __init__(self,
                 table_name: str = None,
                 app_token: str = None,
                 table_id: str = None,
                 page_size: int = 50):
        super().__init__()
        self.table_name = table_name
        self.app_token = app_token
        self.table_id = table_id
        self.page_size = page_size

        # table_token_name 仅用于索引已知表格
        self.table_token_name = None
        self.raw_data_path = None
        if table_name:
            self._set_table_name()
            self._set_table_tokens()
            if not os.path.exists(self.raw_data_path):
                os.makedirs(self.raw_data_path, exist_ok=True)
            
    
    def _set_table_name(self):
        if self.table_name == None:
            raise NotImplementedError(f"不允许空的多维表格")
        elif self.table_name == "Weekly Report":
            self.table_token_name = "weekly_report"
            self.raw_data_path = os.path.join(RAW_DATA_PATH, "weekly_report_raw_data")
        elif self.table_name == "Group Meeting":
            self.table_token_name = "group_meeting"
            self.raw_data_path = os.path.join(RAW_DATA_PATH, "group_meeting_raw_data")
        elif self.table_name == "Schedule":
            self.table_token_name = "freshman_schedule"
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

    def _remove_past_record(self):
        search_pattern = os.path.join(self.raw_data_path, "resp_page_*.json")
        for file_path in glob.glob(search_pattern, recursive=True):
            os.remove(file_path)
        return
    
    def print_basic_info(self):
        print("Year Semester:", self._year_semester)
        print("Tenant Access Token:", self._tenant_access_token)
        print("Bitable Name:", self.table_name)
        print("Bitable Token:", self.app_token)
        print("Bitable Table ID:", self.table_id)

    def get_raw_records(self):
        # 参考: https://open.feishu.cn/api-explorer?apiName=search&from=op_doc&project=bitable&resource=app.table.record&version=v1
        # 按照分页, 一页页下载
        self._remove_past_record()
        raw_data_path = self.raw_data_path
        has_more = True
        page_token = ""
        page_cnt = 0
        print(f"正在下载多维表格：{self.table_name}:")
        while(has_more):
            print(f"\t请求下载第{page_cnt}页...")
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
            self._check_resp(resp) # 响应的合法性检查

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

class SMCLabWeeklyReportCrawler(SMCLabBitableCrawler):
    # 这是一个需要爬取部分记录的表格, 但是依然内置了爬所有记录的方法get_raw_records()
    def __init__(self, *args):
        super().__init__(*args, 
                         table_name = "Weekly Report",
                         page_size = 500)

    def get_raw_records_by_week(self, week: int = None):
        # 按周筛选返回响应
        if not week:
            week = self._this_week - 1
            resp_page_name = "last_week"
        else:
            resp_page_name = ""

        self._remove_past_weekly_records()
        raw_data_path = self.raw_data_path
        has_more = True
        page_token = ""
        page_cnt = 0
        print(f"正在下载第{week}周周报记录：")
        while(has_more):
            print(f"\t请求下载第{page_cnt}页...")
            request: SearchAppTableRecordRequest = SearchAppTableRecordRequest.builder() \
                .app_token(self.app_token) \
                .table_id(self.table_id) \
                .page_size(self.page_size) \
                .page_token(page_token) \
                .request_body(SearchAppTableRecordRequestBody.builder()
                    .field_names(["汇报人", "附件", "文档链接"])
                    .filter(FilterInfo.builder()
                        .conjunction("and")
                        .conditions([Condition.builder()
                            .field_name("_Week")
                            .operator("is")
                            .value([f"{week}"])
                            .build(), 
                            Condition.builder()
                            .field_name("WeekdayValid")
                            .operator("is")
                            .value(["true"])
                            .build()
                            ])
                        .build())
                    .automatic_fields(False)
                    .build()) \
                .build()
            resp: SearchAppTableRecordResponse = self.app_table_record.search(request)
            self._check_resp(resp) # 响应的合法性检查

            # 保存页面
            resp_json = lark.JSON.marshal(resp.data, indent=4)
            resp_page_path = os.path.join(raw_data_path, 
                                          f"{resp_page_name}({self._year_semester},{week})_page_{str(page_cnt)}.json")
            
            with open(resp_page_path, 'w', encoding='utf-8') as f:
                f.write(resp_json)

            # 更新循环状态
            has_more = resp.data.has_more
            page_token = resp.data.page_token
            page_cnt += 1
        print("下载完成")

    def get_last_week_records(self):
        self.get_raw_records_by_week()
    
    def _remove_past_weekly_records(self):
        # 删除所有的上周记录
        search_pattern = os.path.join(self.raw_data_path, "last_week*.json")
        for file_path in glob.glob(search_pattern, recursive=True):
            os.remove(file_path)
        return

class SMCLabGourpMeetingCrawler(SMCLabBitableCrawler):
    # 这是一个需要爬取所有记录的表格
    def __init__(self, *args):
        super().__init__(*args, table_name = "Group Meeting")

class SMCLabScheduleCrawler(SMCLabBitableCrawler):
    # 这是一个需要爬取所有记录的表格
    def __init__(self, *args):
        super().__init__(*args, table_name = "Schedule")