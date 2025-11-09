import os, time
import json
import requests
import lark_oapi as lark
from lark_oapi.api.bitable.v1 import *
import lark_oapi.api.bitable.v1.resource as base_rsc
import lark_oapi.api.drive.v1.resource as drive_rsc

from ..utils import get_year_semester

ABS_PATH = os.path.abspath(__file__)        # SMCLabDailyManager\source_code\SMCLabCrawler\SMCLabClient.py
CURRENT_PATH = os.path.dirname(ABS_PATH)    # SMCLabDailyManager\source_code\SMCLabCrawler
SRC_PATH = os.path.dirname(CURRENT_PATH)    # SMCLabDailyManager\source_code
REPO_PATH = os.path.dirname(SRC_PATH)       # SMCLabDailyManager

TANENT_JSON_FILE = os.path.join(CURRENT_PATH, "last_tenant_access.json") # SMCLabDailyManager\source_code\SMCLabCrawler\table_tokens.json
APP_TOKENS_JSON_FILE = os.path.join(SRC_PATH, "app_tokens.json")

# 父类
class SMCLabClient(object):
    def __init__(self) -> None:
        app_info = self._get_app_tokens()
        app_id = app_info["app_id"]
        app_secret = app_info["app_secret"]
        tenant_access_token = self._get_tenant_access_token(app_id, app_secret) # 应用身份权限

        # 参考: https://open.feishu.cn/document/server-side-sdk/python--sdk/invoke-server-api
        client: lark.Client = (
            lark.Client.builder()
            .app_id(app_info["app_id"])
            .app_secret(app_info["app_secret"])
            # .log_level(lark.LogLevel.DEBUG)
            .build()
        )
        self._client = client
        self._tenant_access_token = tenant_access_token
        self._year_semester = get_year_semester()
        # lark.logger.info(tenant_access_token)

    @property
    def app_table_record(self) -> base_rsc.AppTableRecord:
        assert self._client.bitable is not None
        assert self._client.bitable.v1.app_table_record is not None
        return self._client.bitable.v1.app_table_record
    
    # @property
    # def department(self) -> base_rsc.AppTableRecord:
    #     assert self._client.contact is not None
    #     assert self._client.contact.v3.department is not None
    #     return self._client.contact.v3.department

    @property
    def media(self) -> drive_rsc.Media:
        assert self._client.drive is not None
        assert self._client.drive.v1.media is not None
        return self._client.drive.v1.media

    def _get_app_tokens(self):
        """
        从json中获取应用的app_id, app_secret
        input:
            tokens_json_file: app的配置, 令牌等
        return:
            app_info: 含有键app_id, app_secret的字典
            table_info: 含有键app_token, app_secret的字典
        """
        with open(APP_TOKENS_JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        app_info = data["SMCLab_Manager"]
        return app_info

    def _get_tenant_access_token(self, app_id: str, app_secret: str):
        """
        修改自: https://open.feishu.cn/document/server-docs/authentication-management/access-token/tenant_access_token_internal
        通过自建应用的id和secret获取tenant_access_token, 用于查询表格记录
        input:
            app_id
            app_secret
        return:
            tenant_access_token
        """
        # 检查本地是否有上次的应用身份权限tenant_access_token记录，且是否还有效

        if os.path.exists(TANENT_JSON_FILE):
            with open(TANENT_JSON_FILE, "r", encoding="utf-8") as f:
                last_tenant_access_info = json.load(f)
            last_token_time = last_tenant_access_info.get("time_stamp", 0)
            expire = last_tenant_access_info.get("expire", 0)
            tenant_access_token = last_tenant_access_info.get("tenant_access_token")
            # 如果上次的应用身份权限还在有效期内，则直接返回
            # TODO: 有关expire还没写好
            if time.time() - last_token_time < 7200 and tenant_access_token:
                print("上次应用身份权限依然有效, 复用...")
                return tenant_access_token

        print("申请应用身份权限")
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal/"  # 自建应用通过此接口获取
        payload = {"app_id": app_id, "app_secret": app_secret}
        response = requests.post(url, json=payload).json()
        expire = response["expire"]
        tenant_access_token = response["tenant_access_token"]

        with open(TANENT_JSON_FILE, 'w', encoding='utf-8') as f:
            time_now = time.time()
            json.dump({"time_stamp": time_now, 
                       "time_stamp_readable": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time_now)),
                       "expire": expire,
                       "tenant_access_token": tenant_access_token}, 
                      f, ensure_ascii=False, indent=4)

        return response["tenant_access_token"]  # 返回访问令牌
    
    def get_raw_records(self):
        raise NotImplementedError("Not implemented yet!")
    
    def _remove_past_record(self):
        raise NotImplementedError("Not implemented yet!")
    
    def _check_resp(self, resp):
        # TODO: 请针对所有的子类响应信息进行子类函数实现
        assert resp.code == 0
        assert resp.msg == "success"
        # assert resp.data is not None
        # assert resp.data.has_more is not None
        # assert resp.data.items is not None
        # assert not resp.data.has_more # 如果还有更多
    
    def print_basic_info(self):
        print("Year Semester:", self._year_semester)
        print("Tenant Access Token:", self._tenant_access_token)
    