import os
import json
import lark_oapi as lark
# from lark_oapi.api.bitable.v1 import *
from lark_oapi.api.contact.v3 import *

from SMCLabClient import SMCLabClient

ABS_PATH = os.path.abspath(__file__)        # SMCLabDailyManager\source_code\SMCLabCrawler\AddressBookCrawler.py
CURRENT_PATH = os.path.dirname(ABS_PATH)    # SMCLabDailyManager\source_code\SMCLabCrawler
SRC_PATH = os.path.dirname(CURRENT_PATH)    # SMCLabDailyManager\source_code
REPO_PATH = os.path.dirname(SRC_PATH)       # SMCLabDailyManager
RAW_DATA_PATH = os.path.join(REPO_PATH, "data_raw")

class SMCLabAddressBookCrawler(SMCLabClient):
    def __init__(self,
                 page_size: int = 50):
        super().__init__()
        self.page_size = page_size
        self.raw_data_path = os.path.join(RAW_DATA_PATH, "address_book_raw_data")
    
    def get_department_id_list(self):
        # 参考 https://open.feishu.cn/api-explorer/cli_a8cd4e246b70d013?apiName=children&from=op_doc&project=contact&resource=department&version=v3
        # 构造请求对象
        has_more = True
        page_token = None
        page_cnt = 0
        request: ChildrenDepartmentRequest = ChildrenDepartmentRequest.builder() \
            .department_id("0") \
            .user_id_type("open_id") \
            .department_id_type("open_department_id") \
            .fetch_child(True) \
            .page_size(50) \
            .build()

        
        while(has_more):
            print(f"请求下载第{page_cnt}页...")
            # 发起请求
            option = lark.RequestOption.builder().user_access_token("u-deeqbJTWN2TpAPG46I0QtX0g3lwMg0WhoE00h1o22HEP").build()
            response: ChildrenDepartmentResponse = self._client.contact.v3.department.children(request, option)

        # 处理失败返回
        if not response.success():
            lark.logger.error(
                f"client.contact.v3.department.children failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}")
            return