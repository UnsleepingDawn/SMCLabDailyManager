import json, os

import lark_oapi as lark
from lark_oapi.api.im.v1 import *

from ..common.baseclient import SMCLabClient
from ..data_manager.excel_manager import SMCLabInfoManager
ABS_PATH = os.path.abspath(__file__)        # SMCLabDailyManager\source_code\message\sender.py
CURRENT_PATH = os.path.dirname(ABS_PATH)    # SMCLabDailyManager\source_code\message
SRC_PATH = os.path.dirname(CURRENT_PATH)    # SMCLabDailyManager\source_code
REPO_PATH = os.path.dirname(SRC_PATH)       # SMCLabDailyManager
RAW_DATA_PATH = os.path.join(REPO_PATH, "data_raw")
SEM_DATA_PATH = os.path.join(REPO_PATH, "data_semester")

class SMCLabMessageSender(SMCLabClient):
    def __init__(self):
        super().__init__()
        self.info_manager = SMCLabInfoManager()

    def weekly_generate_attendance(self, 
                                   professor: str = ""):
        # 生成考勤数据的可拼接消息结构
        return
    
    def weekly_generate_gm_attendance(self, 
                                      professor: str = ""):
        # 生成组会考勤数据的可拼接消息结构
        return
    
    def weekly_generate_wr_submission(self,
                                      professor: str = ""):
        # 生成周报提交情况的可拼接消息结构
        return
    
    def monthly_generate_attendance(self, 
                                    professor: str = ""):
        # 生成考勤数据的可拼接消息结构
        return
    
    def monthly_generate_gm_attendance(self, 
                                       professor: str = ""):
        # 生成组会考勤数据的可拼接消息结构
        return
    
    def monthly_generate_wr_submission(self,
                                       professor: str = ""):
        # 生成周报提交情况的可拼接消息结构
        return
    
    def send_weekly_summary(self,
                            to_who: str = "陈旭"):
        name_account, _, _ = self.info_manager.map_fields("姓名", "飞书账号")
        assert to_who in name_account.keys(), f"没有找到该用户: {to_who}"
        receive_name = to_who
        receive_id = name_account[to_who]
        
        return

        

def main():
    # 创建client
    client = lark.Client.builder() \
        .app_id("YOUR_APP_ID") \
        .app_secret("YOUR_APP_SECRET") \
        .log_level(lark.LogLevel.DEBUG) \
        .build()

    # 构造请求对象
    request: CreateMessageRequest = CreateMessageRequest.builder() \
        .receive_id_type("open_id") \
        .request_body(CreateMessageRequestBody.builder()
            .receive_id("ou_1df99022ddb02b52947cd7a76f42df3b")
            .msg_type("text")
            .content("{\"text\":\"test content\"}")
            .build()) \
        .build()

    # 发起请求
    response: CreateMessageResponse = client.im.v1.message.create(request)

    # 处理失败返回
    if not response.success():
        lark.logger.error(
            f"client.im.v1.message.create failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}")
        return

    # 处理业务结果
    lark.logger.info(lark.JSON.marshal(response.data, indent=4))


if __name__ == "__main__":
    main()
