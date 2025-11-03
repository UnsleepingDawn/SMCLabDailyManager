import time
from datetime import datetime, timedelta

# TODO: 使该函数更加鲁棒
def get_year_semester(
        print_info=False
):
    current_timestamp = time.time()
    current_time = time.localtime(current_timestamp)
    # 提取年份和月份
    current_year = current_time.tm_year
    current_month = current_time.tm_mon
    if 2 <= current_month <= 8:
        semester = "Spring"
        academic_year = current_year
    else:
        semester = "Fall"
        academic_year = current_year
    year_semester = f"{academic_year}-{semester}"
    if print_info:
        print(year_semester)
    return year_semester



class TimeParser:
    # 获取上周一和周五的int
    @staticmethod
    def get_last_week_date():

        today = datetime.now()
        current_weekday = today.weekday()
        
        # 计算上周周一：当前日期 - 当前星期几 - 上周的6天（因为要回到上周）
        last_monday = today - timedelta(days=current_weekday + 7)
        
        # 计算上周周五：上周周一 + 4天
        last_friday = last_monday + timedelta(days=4)
        
        # 转换为整数格式 YYYYMMDD
        last_monday_int = int(last_monday.strftime("%Y%m%d"))
        last_friday_int = int(last_friday.strftime("%Y%m%d"))
        
        return last_monday_int, last_friday_int
    


# 使用示例
if __name__ == "__main__":
    last_monday, last_friday = TimeParser.get_last_week_date()
    print(f"上周周一: {last_monday}")
    print(f"上周周五: {last_friday}")

    # get_year_semester(True)