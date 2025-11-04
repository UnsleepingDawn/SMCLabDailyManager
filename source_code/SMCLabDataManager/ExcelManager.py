import os
import pandas as pd

ABS_PATH = os.path.abspath(__file__)        # SMCLabDailyManager\source_code\SMCLabDataManager\ExcelManager.py
CURRENT_PATH = os.path.dirname(ABS_PATH)    # SMCLabDailyManager\source_code\SMCLabDataManager
SRC_PATH = os.path.dirname(CURRENT_PATH)    # SMCLabDailyManager\source_code
REPO_PATH = os.path.dirname(SRC_PATH)       # SMCLabDailyManager
RAW_DATA_PATH = os.path.join(REPO_PATH, "data_raw") # SMCLabDailyManager\data_raw
INCRE_DATA_PATH = os.path.join(REPO_PATH, "data_incremental") # SMCLabDailyManager\data_incremental

class SMCLabInfoManager:
    def __init__(self):
        self.filepath = os.path.join(INCRE_DATA_PATH, "SMCLab学生扩展信息.xlsx")
        try:
            self.df = pd.read_excel(self.filepath)
        except Exception as e:
            raise FileNotFoundError(f"无法读取文件 {self.filepath}，错误信息：{e}")

    def map_fields(self, field1: str, field2: str):
        """
        建立两个字段之间的映射关系。
        字段包括: 
        - 姓名	
        - 年级	
        - 导师	
        - 培养类型(该项还没做好一致性检查)
        - 在读情况	
        - 飞书账号: ou_1df99022ddb02b52947cd7a76f42df3b
        - 学号	
        - union_id	
        - user_id
        - 邮箱	
        - 电话
        - 导师user_id	
        - 部门

        返回：
            mapping_dict: {field1_value: field2_value}
            missing_names: list[姓名]
        """
        if field1 not in self.df.columns or field2 not in self.df.columns:
            raise ValueError(f"字段名错误：'{field1}' 或 '{field2}' 不存在于Excel中")

        mapping_dict = {} # 映射结果
        missing_names = [] # 统计缺失这两个字段的人员的姓名
        one2one_flag = True # 该映射是否是一对一映射

        for _, row in self.df.iterrows():
            val1, val2 = row[field1], row[field2]
            name = row.get("姓名", None)

            # 判断是否有缺失
            if pd.isna(val1) or pd.isna(val2):
                missing_names.append(name)
                continue  # 跳过这行，不加入映射

            # 若 val1 已存在，则追加到列表
            if val1 in mapping_dict:
                # 若不是列表则转为列表
                if not isinstance(mapping_dict[val1], list):
                    mapping_dict[val1] = [mapping_dict[val1]]
                    one2one_flag = False
                # 仅当 val2 不重复时才添加
                if val2 not in mapping_dict[val1]:
                    mapping_dict[val1].append(val2)
            else:
                mapping_dict[val1] = val2

        return mapping_dict, missing_names, one2one_flag
    


if __name__ == "__main__":
    manager = SMCLabInfoManager()
    mapping, missing_name = manager.map_fields("飞书账号", "user_id")

    print("映射数量：", len(mapping))
    print("缺失字段的学生名单：", missing_name)
    print("部分映射示例：", dict(list(mapping.items())[:5]))
