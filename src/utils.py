import time, os, json
from datetime import datetime, timedelta

def get_semester(current_time: str = None,
                      sysu_semesters_path: str = "configs/sysu_semesters.json"):
    sysu_semesters_path = os.path.join("configs", "sysu_semesters.json")
    # 1. 读取JSON文件
    with open(sysu_semesters_path, 'r', encoding='utf-8') as f:
        semester_map = json.load(f)
    # 2. 将字符串日期转换为 datetime 对象
    semester_dates = []
    for sem, date_str in semester_map.items():
        date_obj = datetime.strptime(date_str, "%Y%m%d")
        semester_dates.append((sem, date_obj))

    # 按时间排序（防止字典无序）
    semester_dates.sort(key=lambda x: x[1])

    # 3. 获取当前时间
    if current_time is None:
        current_time = datetime.now()
    else:
        current_time = datetime.strptime(current_time, "%Y%m%d")

    # 4. 找到当前时间属于哪个学期
    current_semester = None
    for i in range(len(semester_dates)):
        sem, start = semester_dates[i]
        if i == len(semester_dates) - 1:  # 最后一个学期
            if current_time >= start:
                current_semester = sem
                break
        else:
            next_start = semester_dates[i + 1][1]
            if start <= current_time < next_start:
                current_semester = sem
                break

    # 如果当前时间在最早的学期开始之前，则返回第一个学期
    assert current_semester is not None, "未找到对应学期"
    return current_semester

def get_semester_and_week(print_info=True,
                          current_time: str = None,
                          sysu_semesters_path: str = "configs/sysu_semesters.json"):
    """
    根据json文件中学期起始时间（周一）映射，
    判断当前日期属于哪个学期，并返回第几周。
    """
    # 如果未指定时间，则使用当前时间
    if current_time is None:
        current_time = datetime.now()
    else:
        current_time = datetime.strptime(current_time, "%Y%m%d")

    # 读取JSON文件
    with open(sysu_semesters_path, 'r', encoding='utf-8') as f:
        semester_map = json.load(f)

    # 转换为 (学期, 起始日期) 列表，并按时间排序
    semester_dates = []
    for sem, date_str in semester_map.items():
        date_obj = datetime.strptime(date_str, "%Y%m%d")
        semester_dates.append((sem, date_obj))
    semester_dates.sort(key=lambda x: x[1])

    # 找到当前学期
    current_semester = None
    for i in range(len(semester_dates)):
        sem, start_date = semester_dates[i]
        if i == len(semester_dates) - 1:
            # 最后一个学期
            if current_time >= start_date:
                current_semester = sem
                start_of_semester = start_date
                break
        else:
            next_start = semester_dates[i + 1][1]
            if start_date <= current_time < next_start:
                current_semester = sem
                start_of_semester = start_date
                break

    # 如果当前时间在第一个学期开始前
    assert current_semester is not None, "未找到对应学期"

    # 计算第几周（以起始日期所在周为第1周）
    days_passed = (current_time - start_of_semester).days
    week_number = days_passed // 7 + 1
    if week_number < 1:
        week_number = 1  # 学期开始前视作第1周

    return current_semester, week_number

class TimeParser:
    # 获取上周一和周五的int
    @staticmethod
    def get_last_week_period():

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

    @staticmethod
    def get_last_week_date(weekday: int):
        today = datetime.now()
        current_weekday = today.weekday()
        # 计算上周周一：当前日期 - 当前星期几 - 上周的6天（因为要回到上周）
        last_weekday = today - timedelta(days=current_weekday + (8 - weekday) )
        last_weekday_int = int(last_weekday.strftime("%Y%m%d"))
        
        return last_weekday_int
    
    @staticmethod
    def get_this_week_period():
        today = datetime.now()
        current_weekday = today.weekday()
        # 计算上周周一：当前日期 - 当前星期几 - 上周的6天（因为要回到上周）
        this_monday = today - timedelta(days=current_weekday)
        this_friday = this_monday + timedelta(days=4)
        last_monday_int = int(this_monday.strftime("%Y%m%d"))
        last_friday_int = int(this_friday.strftime("%Y%m%d"))
        
        return this_monday, this_friday
    
    @staticmethod
    def get_this_week_date(weekday: int):
        today = datetime.now()
        current_weekday = today.weekday()
        
        # 计算上周周一：当前日期 - 当前星期几 - 上周的6天（因为要回到上周）
        this_weekday = today - timedelta(days=current_weekday + (1 - weekday) )
        this_weekday_int = int(this_weekday.strftime("%Y%m%d"))
        
        delta = current_weekday + (1 - weekday)

        return this_weekday_int, delta

    @staticmethod
    def get_last_week_date_maping():
        today = datetime.now()
        current_weekday = today.weekday()
        
        # 计算上周周一：当前日期 - 当前星期几 - 上周的6天（因为要回到上周）
        days = [""]
        for i in range(7):
            day = today - timedelta(days=current_weekday + 7 - i)
            days.append(day.strftime("%Y%m%d"))
        weekdays = ["", "周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        return {days[1]: weekdays[1],
                days[2]: weekdays[2],
                days[3]: weekdays[3],
                days[4]: weekdays[4],
                days[5]: weekdays[5],
                days[6]: weekdays[6],
                days[7]: weekdays[7]}
    
    @staticmethod
    def get_weekday_iso(date_str):
        date_obj = datetime.strptime(date_str, "%Y%m%d")
        
        # isoweekday()返回1-7，1代表周一，7代表周日
        weekday_num = date_obj.isoweekday()
        
        weekdays = ["", "周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        return weekdays[weekday_num]

    @staticmethod
    def get_timestamps(start_date: int, 
                       end_date: int = None, 
                       start_time: str = "0700", 
                       end_time: str = "2300"):
        """
        获取某一天起始和终点时间的秒级时间戳
        
        Args:
            date_int: 日期整数，格式如20251203
            start_time_str: 起始时间字符串，格式如0930
            end_time_str: 终点时间字符串，格式如0930
        
        Returns:
            tuple: (起始时间戳字符串, 终点时间戳字符串)
        """
        # 将整数日期转换为字符串并解析
        if not end_date:
            end_date = start_date
            assert int(end_time)>int(start_time)
        else:
            assert (start_date < end_date) or (start_date == end_date and int(end_time)>int(start_time))
        start_date = str(start_date)
        start_year = int(start_date[:4])
        start_month = int(start_date[4:6])
        start_day = int(start_date[6:8])
        end_date = str(end_date)
        end_year = int(end_date[:4])
        end_month = int(end_date[4:6])
        end_day = int(end_date[6:8])
        
        # 解析起始时间
        start_hour = int(start_time[:2])
        start_minute = int(start_time[2:4])
        
        # 解析结束时间
        end_hour = int(end_time[:2])
        end_minute = int(end_time[2:4])
        
        # 创建起始和结束时间的datetime对象
        start_dt = datetime(start_year, start_month, start_day, start_hour, start_minute)
        end_dt = datetime(end_year, end_month, end_day, end_hour, end_minute)
        
        # 转换为时间戳（秒级）
        start_timestamp = str(int(start_dt.timestamp()))
        end_timestamp = str(int(end_dt.timestamp()))
        
        return start_timestamp, end_timestamp


# 使用示例
if __name__ == "__main__":
    

    # last_monday, last_friday = TimeParser.get_last_week_date()
    # print(f"上周周一: {last_monday}")
    # print(f"上周周五: {last_friday}")

    # get_year_semester(True)
    today = datetime.now()
    current_weekday = today.weekday()
    print(today)
    print(current_weekday)
    print(TimeParser.get_this_week_date(5))