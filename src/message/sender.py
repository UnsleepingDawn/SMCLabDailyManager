import json, os

import lark_oapi as lark
from lark_oapi.api.im.v1 import *

from ..common.baseclient import SMCLabClient
from ..data_manager.excel_manager import SMCLabInfoManager
from ..utils import get_semester_and_week
from ..config import Config

ABS_PATH = os.path.abspath(__file__)        # SMCLabDailyManager\source_code\message\sender.py
CURRENT_PATH = os.path.dirname(ABS_PATH)    # SMCLabDailyManager\source_code\message
SRC_PATH = os.path.dirname(CURRENT_PATH)    # SMCLabDailyManager\source_code
REPO_PATH = os.path.dirname(SRC_PATH)       # SMCLabDailyManager
RAW_DATA_PATH = os.path.join(REPO_PATH, "data_raw")
SEM_DATA_PATH = os.path.join(REPO_PATH, "data_semester")

class SMCLabMessageSender(SMCLabClient):
    def __init__(self, config: Config = None):
        if config is None:
            config = Config()
        super().__init__(config)
        self.info_manager = SMCLabInfoManager(config)
        # 姓名与飞书账号的映射, 用于根据人名发送
        name_account, _, _ = self.info_manager.map_fields("姓名", "飞书账号")
        self.name_account = name_account
        self.bitable_info = self._get_bitable_info(config.bitable_info_path)
        self.post_template_path = config.post_template_path
        self.post_message = None

    def _get_bitable_info(self, path: str):
        # 获得
        bitable_info_file = path
        with open(bitable_info_file, 'r', encoding='utf-8') as f:
            bitable_info = json.load(f)
        return bitable_info

    def _weekly_generate_daily_attendance(self, 
                                   sem: str, 
                                   week: int):
        # 生成出勤一览图
        attendance_plot_path = os.path.join(self._sem_data_path, sem, f"week{week}", f"SMCLab第{week}周考勤统计.png")
        assert os.path.exists(attendance_plot_path), "请先调用SMCLabAttendanceParser.last_week_attendance_to_excel()"
        attendance_plot_key = self._get_image_key(attendance_plot_path)
        return attendance_plot_key
    
    def _weekly_generate_seminar_attendance(self, 
                                           sem: str, 
                                           week: int):
        seminar_attendance_txt_path = os.path.join(self._sem_data_path, sem, f"week{week}", f"SMCLab第{week}周组会考勤统计.txt")
        assert os.path.exists(seminar_attendance_txt_path), "请先调用SMCLabSeminarAttendanceParser.get_attendee_names()"
        with open(seminar_attendance_txt_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            assert len(lines) == 2, "组会考勤统计文件格式不对！"
            appeared_str = lines[0].strip()
            not_appeared_str = lines[1].strip()
        return appeared_str, not_appeared_str
    
    def _weekly_generate_weekly_report_submission(self,
                                      sem: str, 
                                      week: int):
        # 生成周报链接
        weekly_report_url = self.bitable_info["weekly_report"]["url"][sem]

        weekly_report_txt_path = os.path.join(self._sem_data_path, sem, f"week{week}", f"SMCLab第{week}周周报统计.txt")
        assert os.path.exists(weekly_report_txt_path), "请先调用SMCLabWeeklyReportParser.last_week_weekly_report_to_txt()"
        with open(weekly_report_txt_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            assert len(lines) == 2, "周报统计文件格式不对！"
            appeared_str = lines[0].strip()
            not_appeared_str = lines[1].strip()
            
        return weekly_report_url, appeared_str, not_appeared_str
    
    def monthly_generate_attendance(self, 
                                    professor: str = ""):
        # TODO: 生成月度考勤数据的可拼接消息结构
        return
    
    def monthly_generate_gm_attendance(self, 
                                       professor: str = ""):
        # TODO: 生成月度组会考勤数据的可拼接消息结构
        return
    
    def monthly_generate_wr_submission(self,
                                       professor: str = ""):
        # TODO: 生成周报提交情况的可拼接消息结构
        return
    
    def send_weekly_summary(self,
                            week: int = None,
                            last_week: bool = True,
                            users: str or List[str] = "梁涵"):
        # TODO: 思路, 在该文件夹下创建一个模板文件, 用于发送消息, 然后各个函数往里面填值
        name_account = self.name_account
        if isinstance(users, str):
            users = [users]
        
        for user in users:
            assert user in name_account.keys(), f"没有找到该用户: {user}"
        receive_names = users
        receive_ids = [name_account[user] for user in users]
        semester, this_week = get_semester_and_week()
        if not week:
            week = this_week
        if last_week:
            week -= 1

        # 加载发送给陈旭老师的模板
        with open(self.post_template_path, "r", encoding="utf-8") as f:
            self.post_message = json.load(f)

        # 在此处构造数据
        image_key = self._weekly_generate_daily_attendance(semester, week)
        weekly_report_url, appeared_str, not_appeared_str =self._weekly_generate_weekly_report_submission(semester, week)
        self.post_message["zh_cn"]["title"] = f"{semester}-第{week}周总结"
        self.post_message["zh_cn"]["content"][1][0]["image_key"] = image_key
        self.post_message["zh_cn"]["content"][3][0]["href"] = weekly_report_url
        self.post_message["zh_cn"]["content"][4][1]["text"] = appeared_str
        self.post_message["zh_cn"]["content"][5][1]["text"] = not_appeared_str

        post_string = json.dumps(self.post_message, ensure_ascii=False)
        # 构造请求对象
        for receive_id in receive_ids:
            request: CreateMessageRequest = CreateMessageRequest.builder() \
                .receive_id_type("open_id") \
                .request_body(CreateMessageRequestBody.builder()
                    .receive_id(receive_id)
                    .msg_type("post")
                    .content(post_string)
                    .build()) \
                .build()
            
            resp: CreateMessageResponse = self._client.im.v1.message.create(request)
            self._check_resp(resp)
            print(f"SMC每周总结发送成功: To {receive_names}")
        return

    def send_this_weekly_summary(self,
                                 users: str or List[str] = "梁涵"):
        self.send_weekly_summary(users)
        return

    def send_last_weekly_summary(self,
                                 users: str or List[str] = "梁涵"):
        self.send_weekly_summary(last_week=True, users=users)
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

