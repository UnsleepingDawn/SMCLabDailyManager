import os, glob
import json
import lark_oapi as lark
from lark_oapi.api.bitable.v1 import *

from ..common.baseclient import SMCLabClient
from ..utils import TimeParser, get_semester_and_week
from ..config import Config


class SMCLabBitableCrawler(SMCLabClient):
    def __init__(self, config: Config = None):
        if config is None:
            config = Config()
        super().__init__(config)
        # 来自配置文件
        self.table_name = None
        self._page_size = None
        self.raw_data_path = None

        # 需要读取多维表格token的配置
        self._bitable_tokens_path = config.bitable_info_path
        self._table_id = None
        self._app_token = None
        
    def _set_table_tokens(self):
        raise NotImplementedError("父类方法")

    def _remove_past_record(self):
        # raise NotImplementedError("父类方法")
        search_pattern = os.path.join(self.raw_data_path, f"*{self.table_name}*.json")
        for file_path in glob.glob(search_pattern, recursive=True):
            os.remove(file_path)
        return
    
    def print_basic_info(self):
        self.logger.debug("Year Semester: %s", self._year_semester)
        self.logger.debug("Tenant Access Token: %s", self._tenant_access_token)
        self.logger.debug("Bitable Name: %s", self.table_name)
        self.logger.debug("Bitable Token: %s", self._app_token)
        self.logger.debug("Bitable Table ID: %s", self._table_id)

    def get_raw_records(self):
        # 参考: https://open.feishu.cn/api-explorer?apiName=search&from=op_doc&project=bitable&resource=app.table.record&version=v1
        # 按照分页, 一页页下载
        self._remove_past_record()
        raw_data_path = self.raw_data_path
        has_more = True
        page_token = ""
        page_cnt = 0
        self.logger.info("正在下载多维表格：%s:", self.table_name)
        while(has_more):
            self.logger.info("请求下载第%d页...", page_cnt)
            request: SearchAppTableRecordRequest = SearchAppTableRecordRequest.builder() \
                .app_token(self._app_token) \
                .table_id(self._table_id) \
                .page_size(self._page_size) \
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
            resp_page_path = os.path.join(raw_data_path, f"{self._year_semester}_Week{self._this_week}_{self.table_name}_raw_{page_cnt}.json")
            with open(resp_page_path, 'w', encoding='utf-8') as f:
                f.write(resp_json)

            # 更新循环状态
            has_more = resp.data.has_more
            page_token = resp.data.page_token
            page_cnt += 1
        self.logger.info("下载完成")

class SMCLabWeeklyReportCrawler(SMCLabBitableCrawler):
    # 这是一个需要爬取部分记录的表格, 但是依然内置了爬所有记录的方法get_raw_records()
    def __init__(self, config: Config = None):
        if config is None:
            config = Config()
        super().__init__(config)
        self.table_name = "weekly_report"
        self.raw_data_path = config.weekly_report.raw_path
        self._page_size = config.weekly_report.page_size
        self._set_table_tokens()
        if not os.path.exists(self.raw_data_path):
            os.makedirs(self.raw_data_path, exist_ok=True)

    def _set_table_tokens(self):
        with open(self._bitable_tokens_path, "r", encoding="utf-8") as f:
            all_table_info = json.load(f)
        table_info = all_table_info[self.table_name]
        self._app_token = table_info["app_token"]
        self._table_id = table_info["table_id"][self._year_semester]

    def get_raw_records_by_week(self, week: int = None):
        # 按周筛选返回响应
        if not week:
            week = self._this_week - 1

        self._remove_past_weekly_records()
        raw_data_path = self.raw_data_path
        has_more = True
        page_token = ""
        page_cnt = 0
        self.logger.info("正在下载第%d周周报记录：", week)
        while(has_more):
            self.logger.info("请求下载第%d页...", page_cnt)
            request: SearchAppTableRecordRequest = SearchAppTableRecordRequest.builder() \
                .app_token(self._app_token) \
                .table_id(self._table_id) \
                .page_size(self._page_size) \
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
                                          f"{self._year_semester}_Week{week}_{self.table_name}_byweek_raw_{page_cnt}.json")
            
            with open(resp_page_path, 'w', encoding='utf-8') as f:
                f.write(resp_json)

            # 更新循环状态
            has_more = resp.data.has_more
            page_token = resp.data.page_token
            page_cnt += 1
        self.logger.info("下载完成")

    def get_last_week_records(self):
        self.get_raw_records_by_week()
    
    def _remove_past_weekly_records(self):
        # 删除所有的上周记录
        search_pattern = os.path.join(self.raw_data_path, f"{self._year_semester}_Week{self._this_week - 1}*{self.table_name}*.json")
        for file_path in glob.glob(search_pattern, recursive=True):
            os.remove(file_path)
        return

class SMCLabSeminarCrawler(SMCLabBitableCrawler):
    # 这是一个需要爬取所有记录的表格
    def __init__(self, config: Config = None):
        if config is None:
            config = Config()
        super().__init__(config)
        self.table_name = "seminar"
        self.raw_data_path = config.seminar.raw_path
        self._page_size = config.seminar.page_size
        self._set_table_tokens()
        if not os.path.exists(self.raw_data_path):
            os.makedirs(self.raw_data_path, exist_ok=True)

    def _set_table_tokens(self):
        with open(self._bitable_tokens_path, "r", encoding="utf-8") as f:
            all_table_info = json.load(f)
        table_info = all_table_info[self.table_name]
        self._app_token = table_info["app_token"]
        self._table_id = table_info["table_id"]


class SMCLabScheduleCrawler(SMCLabBitableCrawler):
    # 这是一个需要爬取所有记录的表格
    def __init__(self, config: Config = None):
        if config is None:
            config = Config()
        super().__init__(config)
        self.table_name = "schedule"
        self.raw_data_path = config.schedule.raw_path
        self._page_size = config.schedule.page_size
        self._set_table_tokens()
        if not os.path.exists(self.raw_data_path):
            os.makedirs(self.raw_data_path, exist_ok=True)

    def _set_table_tokens(self):
        with open(self._bitable_tokens_path, "r", encoding="utf-8") as f:
            all_table_info = json.load(f)
        table_info = all_table_info[self.table_name]
        self._app_token = table_info["app_token"]
        self._table_id = table_info["table_id"][self._year_semester]