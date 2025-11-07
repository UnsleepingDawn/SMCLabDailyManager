import json, os

import lark_oapi as lark
from lark_oapi.api.im.v1 import *

from ..common.baseclient import SMCLabClient
from ..data_manager.excel_manager import SMCLabInfoManager
from ..utils import get_semester_and_week

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
        self.post_message = {}

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
    
    def send_last_weekly_summary(self,
                            user: str = "梁涵"):
        # TODO: 思路, 在该文件夹下创建一个模板文件, 用于发送消息, 然后各个函数往里面填值
        name_account = self.name_account
        assert user in name_account.keys(), f"没有找到该用户: {user}"
        receive_name = user
        receive_id = name_account[user]
        semester, week = get_semester_and_week()
        last_week = week - 1

        self.post_message = {
            "zh_cn": {
                "title": f"{semester}第{last_week}周总结",
                "content": [
                    [
                        {
                            "tag": "text",
                            "text": "第一行:",
                            "style": ["bold", "underline"]
                        
                        },
                        {
                            "tag": "a",
                            "href": "http://www.feishu.cn",
                            "text": "超链接",
                            "style": ["bold", "italic"]
                        },
                        {
                            "tag": "at",
                            "user_id": "ou_1avnmsbv3k45jnk34j5",
                            "style": ["lineThrough"]
                        }
                    ],
                    [{
                        "tag": "img",
                        "image_key": "img_7ea74629-9191-4176-998c-2e603c9c5e8g"
                    }],
                    [	
                        {
                            "tag": "text",
                            "text": "第二行:",
                            "style": ["bold", "underline"]
                        },
                        {
                            "tag": "text",
                            "text": "文本测试"
                        }
                    ],
                    [{
                        "tag": "img",
                        "image_key": "img_7ea74629-9191-4176-998c-2e603c9c5e8g"
                    }],
                    [{
                        "tag": "media",
                        "file_key": "file_v2_0dcdd7d9-fib0-4432-a519-41d25aca542j",
                        "image_key": "img_7ea74629-9191-4176-998c-2e603c9c5e8g"
                    }],
                    [{
                        "tag": "emotion",
                        "emoji_type": "SMILE"
                    }],
                    [{
                        "tag": "hr"
                    }],
                    [{
                        "tag": "code_block",
                        "language": "GO",
                        "text": "func main() int64 {\n    return 0\n}"
                    }],
                    [{
                        "tag": "md",
                        "text": "**mention user:**<at user_id=\"ou_xxxxxx\">Tom</at>\n**href:**[Open Platform](https://open.feishu.cn)\n**code block:**\n```GO\nfunc main() int64 {\n    return 0\n}\n```\n**text styles:** **bold**, *italic*, ***bold and italic***, ~underline~,~~lineThrough~~\n> quote content\n\n1. item1\n    1. item1.1\n    2. item2.2\n2. item2\n --- \n- item1\n    - item1.1\n    - item2.2\n- item2"
                    }]
                ]
            },
        }

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
        # 发送单条文本信息给指定人
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
                .receive_id(receive_id)
                .msg_type("text")
                .content(message_string)
                .build()) \
            .build()
        
        resp: CreateMessageResponse = self._client.im.v1.message.create(request)
        self._check_resp(resp)
        print("发送成功")

    def _get_image_key(self, image_path):
        # 获得图片的key
        # 参考: https://open.feishu.cn/document/server-docs/im-v1/image/create
        if not os.path.exists(image_path):
            raise RuntimeError(f"不存在该图片:{image_path}")
        image_binary_data = open(image_path, 'rb')
        
        request: CreateImageRequest = CreateImageRequest.builder() \
            .request_body(CreateImageRequestBody.builder()
                .image_type("message")
                .image(image_binary_data)
                .build()) \
            .build()
        resp: CreateImageResponse = self._client.im.v1.image.create(request)
        self._check_resp(resp)
        return resp.data.image_key

    def send_image(self,
                   user: str,
                   image_path: str):
        # 发送单条信息
        # 参考: https://open.feishu.cn/document/server-docs/im-v1/message-content-description/create_json?appId=cli_a8cd4e246b70d013#7111df05
        name_account = self.name_account
        assert user in name_account.keys(), f"没有找到该用户: {user}"
        receive_name = user
        receive_id = name_account[user]
        image_key = self._get_image_key(image_path)
        message = {
            "image_key": image_key
        }
        message_string = json.dumps(message, ensure_ascii=False)

        request: CreateMessageRequest = CreateMessageRequest.builder() \
            .receive_id_type("open_id") \
            .request_body(CreateMessageRequestBody.builder()
                .receive_id(receive_id)
                .msg_type("image")
                .content(message_string)
                .build()) \
            .build()
        
        resp: CreateMessageResponse = self._client.im.v1.message.create(request)
        self._check_resp(resp)
        print("发送成功")

