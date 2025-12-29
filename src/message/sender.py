import json, os
import copy

import lark_oapi as lark
from lark_oapi.api.im.v1 import *

from ..common.baseclient import SMCLabClient
from ..data_manager.excel_manager import SMCLabInfoManager
from ..utils import TimeParser, get_semester_and_week
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
        self.semester_info_path = config.semester_info_path
        self.weekly_summary_template_path = config.weekly_summary_template_path
        self.seminar_preview_template_path = config.seminar_preview_template_path
        self.name_account = None

    def _set_info_manager(self):
        info_manager = SMCLabInfoManager()
        self.name_account, _, _ = info_manager.map_fields("姓名", "飞书账号")

    def _fetch_daily_attendance(self, 
                                          sem: str, 
                                          week: int):
        # 生成出勤一览图
        attendance_plot_path = os.path.join(self._sem_data_path, sem, f"week{week}", f"SMCLab第{week}周考勤统计.png")
        assert os.path.exists(attendance_plot_path), "请先调用SMCLabAttendanceParser.last_week_attendance_to_excel()"
        attendance_plot_key = self._get_image_key(attendance_plot_path)
        return attendance_plot_key
    
    def _fetch_seminar_attendance(self, 
                                  sem: str, 
                                  week: int):
        '''
        生成第week周组会考勤统计的字符串:
        第一行为到了的, 第二行没到, 格式为:
        张三, 李四, 王五
        赵六, 钱七
        '''
        seminar_attendance_txt_path = os.path.join(self._sem_data_path, sem, f"week{week}", f"SMCLab第{week}周组会考勤统计.txt")
        if not os.path.exists(seminar_attendance_txt_path):
            return "", ""
        appeared_str = ""
        not_appeared_str = ""
        with open(seminar_attendance_txt_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            assert len(lines) == 2, "组会考勤统计文件格式不对！"
            appeared_str = lines[0].strip()
            not_appeared_str = lines[1].strip()
        return appeared_str, not_appeared_str
    
    def _fetch_seminar_preview(self, sem: str, week: int):
        def check_seminar_item(seminar_info_item):
            assert seminar_info_item.get("happened", True) == False, "该周组会已经开过"
            assert seminar_info_item.get("room", None), "请指定开会地点"
            presentations = seminar_info_item.get("presentations", [])
            assert len(presentations) > 0
            count = 1
            for presentation in presentations:
                presenter = presentation.get("presenter", None)
                track = presentation.get("track", None)
                assert presenter, "怎么没有名字"
                assert track == count, f"{presenter}的顺序({track})应该是{count}"
                assert presentation.get("title", None), f"{presenter}怎么没有提交标题!"
                assert presentation.get("abstract", None), f"{presenter}怎么没有提交摘要!"
                count += 1

        seminar_info_path = os.path.join(self._sem_data_path, sem, f"seminar_information.json")
        assert os.path.exists(seminar_info_path), "请先下载组会多维表格"
        
        with open(seminar_info_path, "r", encoding="utf-8") as f:
            seminar_info = json.load(f)

        target_seminar_info = None
        for seminar_info_item in seminar_info:
            if seminar_info_item.get("week", None) == week:
                check_seminar_item(seminar_info_item)
                target_seminar_info = seminar_info_item 
        # TODO: 不要使用assert进行运行时检查, 为空的时候发送空消息
        assert target_seminar_info, f"没有找到{week}周的组会信息, 请确认该周是否真的有组会"
        return target_seminar_info

    def _build_seminar_preview_content(self):
        
        # 加载发送给陈旭老师的模板
        with open(self.seminar_preview_template_path, "r", encoding="utf-8") as f:
            post_message = json.load(f)

        # 在此处构造数据
        target_seminar_info = self._fetch_seminar_preview(self._year_semester, self._this_week)
        presentations = target_seminar_info.get("presentations")
        
        post_message["zh_cn"]["title"] = f"{self._year_semester}-第{self._this_week}周组会通知"
        template_content_list = post_message["zh_cn"]["content"]
        new_content_list = []
        # 处理三个演讲者的预告
        for pre in presentations:
            presentation_content = copy.deepcopy(template_content_list[0])
            presentation_content[1]["text"] = str(pre["track"])
            presentation_content[3]["text"] = str(pre["title"])
            presentation_content[5]["text"] = str(pre["presenter"])
            presentation_content[7]["text"] = str(pre["abstract"])
            new_content_list.append(presentation_content)
        # 根据实际情况是否
        with open(self.semester_info_path, "r", encoding="utf-8") as f:
            semester_info = json.load(f)
        this_semester_info = semester_info[self._year_semester]
        # 添加预告时间段的文本
        period_content = template_content_list[1].copy()
        period_content[2]["text"] = TimeParser.get_weekday_iso(target_seminar_info["weekday"])
        seminar_start_time = str(this_semester_info["default_seminar_start_time"])
        seminar_end_time = str(this_semester_info["default_seminar_end_time"])
        seminar_start_time = seminar_start_time[:2]+":"+seminar_start_time[2:]
        seminar_end_time = seminar_end_time[:2]+":"+seminar_end_time[2:]
        seminar_period = seminar_start_time+"-"+seminar_end_time
        period_content[3]["text"] = seminar_period
        new_content_list.append(period_content)
        # 添加地点的文本
        room_content = template_content_list[2].copy()
        room_content[1]["text"] = target_seminar_info["room"]
        new_content_list.append(room_content)
        # 根据是否既定组会日期, 决定是否发送线上链接
        tecent_content = template_content_list[3].copy()
        if this_semester_info["default_seminar_weekday"] == target_seminar_info["weekday"]:
            tecent_meeting_str = "(点击链接入会，或添加至会议列表)\n"
            tecent_meeting_str += this_semester_info["default_seminar_tecent_link"]
            tecent_meeting_str += "\n腾讯会议: "
            tecent_meeting_str += this_semester_info["default_seminar_tecent_id"]
            tecent_content[1]["text"] = tecent_meeting_str
        else:
            tecent_content[1]["text"] = "(由于本周组会时间调整, 腾讯会议号另行通知)"
        new_content_list.append(tecent_content)

        post_message["zh_cn"]["content"] = new_content_list
        return post_message

    def _fetch_weekly_report_submission(self,
                                        sem: str, 
                                        week: int):
        # 生成周报链接
        with open(self.semester_info_path, "r", encoding="utf-8") as f:
            seminar_info = json.load(f)
        weekly_report_url = seminar_info[sem]["bitable"]["weekly_report"]["url"]

        weekly_report_txt_path = os.path.join(self._sem_data_path, sem, f"week{week}", f"SMCLab第{week}周周报统计.txt")
        assert os.path.exists(weekly_report_txt_path), "请先调用SMCLabWeeklyReportParser.last_week_weekly_report_to_txt()"
        with open(weekly_report_txt_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            assert len(lines) == 2, "周报统计文件格式不对！"
            appeared_str = lines[0].strip()
            not_appeared_str = lines[1].strip()
            
        return weekly_report_url, appeared_str, not_appeared_str
    
    def _send_weekly_summary_byweek(self,
                            week: int = None,
                            users: str | List[str] = "梁涵"):
        if not self.name_account:
            self._set_info_manager()
        name_account = self.name_account
        if isinstance(users, str):
            users = [users]
        
        for user in users:
            assert user in name_account.keys(), f"没有找到该用户: {user}"
        receive_names = users
        receive_ids = [name_account[user] for user in users]
        semester = self._year_semester
        week = self._this_week if not week else week

        # 加载发送给陈旭老师的模板
        with open(self.weekly_summary_template_path, "r", encoding="utf-8") as f:
            post_message = json.load(f)

        # 在此处构造数据
        image_key = self._fetch_daily_attendance(semester, week)
        weekly_report_url, appeared_str, not_appeared_str =self._fetch_weekly_report_submission(semester, week)
        attended_str, not_attended_str = self._fetch_seminar_attendance(semester, week)
        post_message["zh_cn"]["title"] = f"{semester}-第{week}周总结"
        post_message["zh_cn"]["content"][1][0]["image_key"] = image_key
        post_message["zh_cn"]["content"][3][0]["href"] = weekly_report_url
        post_message["zh_cn"]["content"][4][1]["text"] = appeared_str
        post_message["zh_cn"]["content"][5][1]["text"] = not_appeared_str
        post_message["zh_cn"]["content"][7][1]["text"] = attended_str
        post_message["zh_cn"]["content"][8][1]["text"] = not_attended_str

        post_string = json.dumps(post_message, ensure_ascii=False)
        # 构造请求对象
        for receive_id, receive_name in zip(receive_ids, receive_names):
            if receive_name == "梁涵":
                user_input = "yes"
            else:
                user_input = input(f"即将发送给'{receive_name}', 请确认(yes/y): ").strip()
                
            if user_input.lower() == "yes" or "y":
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
                self.logger.info("SMC每周总结发送成功: To %s", receive_names)
            else:
                self.logger.warning("SMC每周总结发送失败: To %s", receive_names)
                    
        return

    def send_this_week_summary(self,
                               users: str | List[str] = "梁涵"):
        self._send_weekly_summary_byweek(week=self._this_week, users=users)
        return

    def send_last_week_summary(self,
                               users: str | List[str] = "梁涵"):
        self._send_weekly_summary_byweek(week=self._this_week-1, users=users)
        return

    def send_this_week_seminar_attendance(self,
                                          user: str):
        self.logger.info("发送第%s周组会考勤给 %s", self._this_week, user)
        attended_str, not_attended_str = self._fetch_seminar_attendance(self._year_semester, self._this_week)
        message_string = f"{self._year_semester}-第{self._this_week}周组会考勤:\n" + f"参会: {attended_str}" + "\n" + f"未参会: {not_attended_str}"
        self.send_text(user = user, message = message_string)
        return

    def send_this_week_seminar_preview(self,
                                       users: str):
        if not self.name_account:
            self._set_info_manager()
        name_account = self.name_account
        if isinstance(users, str):
            users = [users]
        
        for user in users:
            assert user in name_account.keys(), f"没有找到该用户: {user}"

        receive_names = users
        receive_ids = [name_account[user] for user in users]


        post_message = self._build_seminar_preview_content()

        post_string = json.dumps(post_message, ensure_ascii=False)
        # 构造请求对象
        for receive_id, receive_name in zip(receive_ids, receive_names):
            if receive_name == "梁涵":
                user_input = "yes"
            else:
                user_input = input(f"即将发送给'{receive_name}', 请确认(yes/y): ").strip()
                
            if user_input.lower() == "yes" or "y":
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
                self.logger.info("组会预告发送成功: To %s", receive_names)
            else:
                self.logger.warning("组会预告发送失败: To %s", receive_names)
                    
        return


    def send_text(self,
                  user: str,
                  message: str):
        # 发送单条文本信息给指定人
        # 参考: https://open.feishu.cn/document/server-docs/im-v1/message-content-description/create_json#45e0953e
        
        if self.name_account:
            self._set_info_manager()
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
        self.logger.info("发送成功")

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
        
        if self.name_account:
            self._set_info_manager()
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
        self.logger.info("发送成功")

