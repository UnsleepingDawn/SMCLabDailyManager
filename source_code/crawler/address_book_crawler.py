import os, glob
import json
import lark_oapi as lark
# from lark_oapi.api.bitable.v1 import *
from lark_oapi.api.contact.v3 import *
from lark_oapi.api.contact.v3.model.user import User

from ..common.baseclient import SMCLabClient

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
        if not os.path.exists(self.raw_data_path):
            os.makedirs(self.raw_data_path, exist_ok=True)
        self.department_id = {}
        self._remove_past_record()
    
    def _get_department_id(self, update = False):
        # 参考 https://open.feishu.cn/api-explorer/cli_a8cd4e246b70d013?apiName=children&from=op_doc&project=contact&resource=department&version=v3
        data_path = os.path.join(self.raw_data_path, "department_id.json")
        if not update and os.path.exists(data_path):
            with open(data_path, "r", encoding="utf-8") as f:
                self.department_id = json.load(f)
            return
        has_more = True
        page_token = ""
        page_cnt = 0
        print(f"正在下载部门id: ")
        while(has_more):
            print(f"\t请求下载第{page_cnt}页...")
            request: ChildrenDepartmentRequest = ChildrenDepartmentRequest.builder() \
                .department_id("0") \
                .user_id_type("open_id") \
                .department_id_type("open_department_id") \
                .fetch_child(True) \
                .page_size(self.page_size) \
                .page_token(page_token) \
                .build()
            # 发起请求
            resp: ChildrenDepartmentResponse = self._client.contact.v3.department.children(request)
            self._check_resp(resp)

            # 更新循环状态
            has_more = resp.data.has_more
            page_token = resp.data.page_token
            page_cnt += 1
        
        assert page_cnt == 1, "还未适配多页Json逻辑, 请首先尝试增大Page size"

        data = resp.data
        for item in data.items:
            department = {
                "department_name": item.name,
                "department_id": item.department_id,
                "open_department_id": item.open_department_id,
                "parent_department_id": item.parent_department_id,
                "member_count": item.member_count, # 当前部门及其下属部门的用户（包含部门负责人）个数。
                "primary_member_count": item.primary_member_count, # 当前部门及其下属部门的主属成员（即成员的主部门为当前部门）的数量。
            }
            self.department_id[item.name]=department
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(self.department_id, f, ensure_ascii=False, indent=4)
        
    def _remove_past_record(self):
        # 删去所有的下载数据
        search_pattern = os.path.join(self.raw_data_path, "**", "*.json")
        for file_path in glob.glob(search_pattern, recursive=True):
            os.remove(file_path)
        return

    def _get_one_department_records(self, 
                                   department_id: str = "") -> List[User]:
        # 获取其中一个部门的用户名单
        has_more = True
        page_token = ""
        page_cnt = 0
        users=[]
        while(has_more):
            print(f"\t请求下载第{page_cnt}页...")
            request = FindByDepartmentUserRequest.builder() \
                .department_id(department_id) \
                .page_size(self.page_size) \
                .page_token(page_token) \
                .build()
            
            # 发起请求
            resp: FindByDepartmentUserResponse = self._client.contact.v3.user.find_by_department(request)
            self._check_resp(resp) # 响应的合法性检查
            
            items = resp.data.items
            if items:
                users.extend(items)
            # 更新循环状态
            has_more = resp.data.has_more
            page_token = resp.data.page_token
            page_cnt += 1
        return users
    
    def _filter_primary_dept_users(self,
                                  users: List[User], 
                                  department_id: str) -> List[User]:
        # 只保留以当前部门为主部门的用户
        primary_users = []
        
        for user in users:
            orders = user.orders
            for order in orders:
                if order.department_id == department_id and order.is_primary_dept:
                    primary_users.append(user)
                    break  # 一个用户只有一个主部门，找到后即可跳出循环
        
        return primary_users

    def get_raw_records(self):
        # 递归下载各个部门的通讯录, 并整理
        raw_data_path = self.raw_data_path

        if self.department_id == {}:
            self._get_department_id()
        address_book = {}
        
        for department_name in self.department_id:
            department = self.department_id[department_name]
            open_department_id = department.get("open_department_id", "0")

            print(f"正在处理部门: {department_name} ({open_department_id})")
            users = self._get_one_department_records(open_department_id)
            primary_users = self._filter_primary_dept_users(users, open_department_id)
            address_book[department_name] = {
                "department_id": open_department_id,
                "department_name": department_name,
                "member_count": department.get("member_count"),
                "primary_members_count": department.get("primary_member_count"),
                "primary_members": [
                ]
            }
            for user in primary_users:
                if user.custom_attrs and len(user.custom_attrs) > 0 and hasattr(user.custom_attrs[0], 'value') and hasattr(user.custom_attrs[0].value, 'option_value'):
                    cultivation = user.custom_attrs[0].value.option_value
                    # print(f"用户 {user.name} 有培养属性: {user.custom_attrs[0].value.option_value}")
                else:
                    cultivation = ""
                    print(f"\t用户 {user.name} 没有培养属性")

                if user.custom_attrs and len(user.custom_attrs) > 1 and hasattr(user.custom_attrs[1], 'value') and hasattr(user.custom_attrs[1].value, 'generic_user') and hasattr(user.custom_attrs[1].value.generic_user, 'id'):
                    mentor_id = user.custom_attrs[1].value.generic_user.id
                    # print(f"用户 {user.name} 有导师属性: {user.custom_attrs[1].value.generic_user.id}")
                else:
                    mentor_id = ""
                    print(f"\t用户 {user.name} 没有导师属性")
                member_info = {
                        "name": user.name,
                        "union_id": user.union_id,
                        "open_id": user.open_id,
                        "user_id": user.user_id,
                        "email": user.email,
                        "mobile": user.mobile,
                        "cultivation": cultivation,
                        "mentor_id": mentor_id
                    } 
                address_book[department_name]["primary_members"].append(member_info)
                
        # 保存页面
        address_book_path = os.path.join(raw_data_path, f"address_book.json")
        with open(address_book_path, 'w', encoding='utf-8') as f:
            json.dump(address_book, f, ensure_ascii=False, indent=4)
        return