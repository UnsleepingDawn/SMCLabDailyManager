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
        name_account, _, _ = self.info_manager.map_fields("姓名", "飞书账号")
        self.name_account = name_account

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
                            user: str = "梁涵"):
        name_account = self.name_account
        assert user in name_account.keys(), f"没有找到该用户: {user}"
        receive_name = user
        receive_id = name_account[user]

        # 构造请求对象
        request: CreateMessageRequest = CreateMessageRequest.builder() \
            .receive_id_type("open_id") \
            .request_body(CreateMessageRequestBody.builder()
                .receive_id("receive_id")
                .msg_type("text")
                .content("{\"text\":\"test content\"}")
                .build()) \
            .build()
        return

    def send_text(self,
                  user: str,
                  message: str):
        # 参考: https://open.feishu.cn/document/server-docs/im-v1/message-content-description/create_json#45e0953e
        name_account = self.name_account
        assert user in name_account.keys(), f"没有找到该用户: {user}"
        receive_name = user
        receive_id = name_account[user]
        message = {
            "text": message
        }
        message_string = json.dumps(message, ensure_ascii=False)

        request: CreateMessageRequest = CreateMessageRequest.builder() \
            .receive_id_type("open_id") \
            .request_body(CreateMessageRequestBody.builder()
                .receive_id("receive_id")
                .msg_type("text")
                .content(message_string)
                .build()) \
            .build()
        
        resp: CreateMessageResponse = self._client.im.v1.message.create(request)
        self._check_resp(resp)
        print("发送成功")

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
