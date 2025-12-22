import time, os, json, logging
from datetime import datetime, timedelta
from typing import Union

def get_semester(current_time: str = None,
                 semester_info_path: str = "configs/semester_info.json"):
    # 1. 读取JSON文件
    with open(semester_info_path, 'r', encoding='utf-8') as f:
        semester_map = json.load(f)
    # 2. 将字符串日期转换为 datetime 对象
    semester_dates = []
    for sem, sem_info in semester_map.items():
        date_str = sem_info["start_date"]
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

def get_semester_and_week(current_time: str = None,
                          semester_info_path: str = "configs/semester_info.json"):
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
    with open(semester_info_path, 'r', encoding='utf-8') as f:
        semester_map = json.load(f)

    # 转换为 (学期, 起始日期) 列表，并按时间排序
    semester_dates = []
    for sem, sem_info in semester_map.items():
        date_str = sem_info["start_date"]
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

def get_semester_start_date(semester: str = None,
                            semester_info_path: str = "configs/semester_info.json"):
    with open(semester_info_path, 'r', encoding='utf-8') as f:
        semester_map = json.load(f)
    if semester is None:
        semester = get_semester()
    return datetime.strptime(semester_map[semester]["start_date"], "%Y%m%d")

class TimeParser:
    """时间解析工具类，提供学期周次计算、日期转换等功能"""

    @staticmethod
    def get_week_period(sem_start_date: Union[datetime, str] = None,
                        week: int = None):
        """
        根据学期起始日期和周数，计算指定周的周一和周五日期
        
        Args:
            sem_start_date: 学期起始日期，可以是datetime对象或"YYYYMMDD"格式字符串，默认为当前学期起始日期
            week: 周数（从1开始），默认为当前周
        
        Returns:
            tuple: (周一日期整数, 周五日期整数)，格式为YYYYMMDD
        
        Example:
            >>> monday, friday = TimeParser.get_week_period(week=5)
            >>> print(monday, friday)  # 20250106 20250110 (假设第5周)
        """
        if sem_start_date is None:
            sem_start_date = get_semester_start_date()
        if isinstance(sem_start_date, str):
            sem_start_date = datetime.strptime(sem_start_date, "%Y%m%d")
        if week is None:
            week = get_semester_and_week()[1]
        # 计算本周周一：学期起始日期 + （周数 - 1） * 7天
        monday = sem_start_date + timedelta(days=(week - 1) * 7)
        # 计算本周周五：本周周一 + 4天
        friday = monday + timedelta(days=4)
        # 转换为整数格式 YYYYMMDD
        monday_int = int(monday.strftime("%Y%m%d"))
        friday_int = int(friday.strftime("%Y%m%d"))
        
        return monday_int, friday_int

    @staticmethod
    def get_week_date(weekday: int,
                      week: int = None):
        """
        根据周数和星期几，计算指定周的具体日期
        
        Args:
            weekday: 星期几（1=周一, 2=周二, ..., 7=周日）
            week: 周数（从1开始），默认为当前周
        
        Returns:
            int: 日期整数，格式为YYYYMMDD
        
        Example:
            >>> date = TimeParser.get_week_date(weekday=3, week=5)
            >>> print(date)  # 20250108 (假设第5周的周三)
        """
        assert weekday in [1, 2, 3, 4, 5, 6, 7]
        if week is None:
            week = get_semester_and_week()[1]
        assert week >= 0
        sem_start_date = get_semester_start_date()
        target_date = sem_start_date + timedelta(days=(week - 1) * 7 + (weekday - 1))
        target_date_int = int(target_date.strftime("%Y%m%d"))
        return target_date_int
    
    @staticmethod
    def get_last_week_period():
        """
        获取上周的周一和周五日期
        
        Returns:
            tuple: (上周周一日期整数, 上周周五日期整数)，格式为YYYYMMDD
        
        Example:
            >>> last_monday, last_friday = TimeParser.get_last_week_period()
            >>> print(last_monday, last_friday)  # 20241230 20250103 (假设当前是2025年第1周)
        """
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
        """
        获取上周指定星期几的日期
        
        Args:
            weekday: 星期几（1=周一, 2=周二, ..., 7=周日）
        
        Returns:
            int: 日期整数，格式为YYYYMMDD
        
        Example:
            >>> date = TimeParser.get_last_week_date(weekday=5)
            >>> print(date)  # 20250103 (假设上周五是2025年1月3日)
        """
        today = datetime.now()
        current_weekday = today.weekday()
        # 计算上周周一：当前日期 - 当前星期几 - 上周的6天（因为要回到上周）
        last_weekday = today - timedelta(days=current_weekday + (8 - weekday) )
        last_weekday_int = int(last_weekday.strftime("%Y%m%d"))
        return last_weekday_int
    
    @staticmethod
    def get_this_week_period():
        """
        获取本周的周一和周五日期
        
        Returns:
            tuple: (本周周一日期整数, 本周周五日期整数)，格式为YYYYMMDD
        
        Example:
            >>> this_monday, this_friday = TimeParser.get_this_week_period()
            >>> print(this_monday, this_friday)  # 20250106 20250110 (假设本周是2025年1月6日到10日)
        """
        today = datetime.now()
        current_weekday = today.weekday()
        # 计算本周周一：当前日期 - 当前星期几
        this_monday = today - timedelta(days=current_weekday)
        this_friday = this_monday + timedelta(days=4)
        last_monday_int = int(this_monday.strftime("%Y%m%d"))
        last_friday_int = int(this_friday.strftime("%Y%m%d"))
        
        return last_monday_int, last_friday_int
    
    @staticmethod
    def get_this_week_date(weekday: int):
        """
        获取本周指定星期几的日期
        
        Args:
            weekday: 星期几（1=周一, 2=周二, ..., 7=周日）
        
        Returns:
            tuple: (日期整数, 天数差)，日期格式为YYYYMMDD，天数差表示距离今天的天数
        
        Example:
            >>> date, delta = TimeParser.get_this_week_date(weekday=3)
            >>> print(date, delta)  # 20250108 -2 (假设今天是周二，获取周三，差-2天)
        """
        today = datetime.now()
        current_weekday = today.weekday()
        
        # 计算上周周一：当前日期 - 当前星期几 - 上周的6天（因为要回到上周）
        this_weekday = today - timedelta(days=current_weekday + (1 - weekday) )
        this_weekday_int = int(this_weekday.strftime("%Y%m%d"))
        
        delta = current_weekday + (1 - weekday)

        return this_weekday_int, delta

    @staticmethod
    def get_last_week_date_maping():
        """
        获取上周所有日期与星期几的映射字典
        
        Returns:
            dict: 日期字符串到星期几的映射，格式为{"YYYYMMDD": "周X"}
        
        Example:
            >>> mapping = TimeParser.get_last_week_date_maping()
            >>> print(mapping)  
            # {"20241230": "周一", "20241231": "周二", ..., "20250105": "周日"}
        """
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
    def get_weekday_iso(date: Union[str, int]):
        """
        获取日期对应的星期几（ISO 8601标准：周一为一周的第一天）
        
        Args:
            date: 日期，可以是以下格式之一：
                - 整数1-7：直接表示星期几（1=周一, 7=周日）
                - 整数YYYYMMDD：日期整数，如20250108
                - 字符串"YYYYMMDD"：日期字符串
        
        Returns:
            str: 星期几的中文表示（"周一"到"周日"）
        
        Example:
            >>> weekday = TimeParser.get_weekday_iso(20250108)
            >>> print(weekday)  # "周三"
            >>> weekday = TimeParser.get_weekday_iso(3)
            >>> print(weekday)  # "周三"
        """
        # ISO 8601 标准定义: 星期一为一周的第一天, 星期日为一周的最后一天
        if isinstance(date, int) and date < 8:
            weekday_num = date
        elif isinstance(date, int) and date > 20010124:
            date_obj = datetime.strptime(str(date), "%Y%m%d")
            # isoweekday()返回1-7，1代表周一，7代表周日
            weekday_num = date_obj.isoweekday()
        else:
            date_obj = datetime.strptime(date, "%Y%m%d")
            # isoweekday()返回1-7，1代表周一，7代表周日
            weekday_num = date_obj.isoweekday()
        
        weekdays = ["", "周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        return weekdays[weekday_num]

    @staticmethod
    def get_day_period(time: int):
        """
        根据时间（24小时制）获取时间段，如"上午"、"下午"、"晚上"
        
        Args:
            time: 时间整数，格式为HHMM（如930表示9:30，1400表示14:00）
        
        Returns:
            str: 时间段（"上午"、"下午"、"晚上"或"错误时间"）
        
        Example:
            >>> period = TimeParser.get_day_period(930)
            >>> print(period)  # "上午"
            >>> period = TimeParser.get_day_period(1430)
            >>> print(period)  # "下午"
            >>> period = TimeParser.get_day_period(2000)
            >>> print(period)  # "晚上"
        """
        if time > 600 and time < 1200:
            return "上午"
        elif time > 1200 and time < 1800:
            return "下午"
        elif time > 1800 and time < 2400:
            return "晚上"
        else:
            return "错误时间"


    @staticmethod
    def get_sec_level_timestamps(start_date: int, 
                       end_date: int = None, 
                       start_time: str = "0700", 
                       end_time: str = "2300"):
        """
        获取指定日期时间范围的秒级时间戳
        
        Args:
            start_date: 起始日期整数，格式为YYYYMMDD，如20250108
            end_date: 结束日期整数，格式为YYYYMMDD，如20250110。如果为None，则与start_date相同
            start_time: 起始时间字符串，格式为HHMM（24小时制），如"0930"表示9:30
            end_time: 结束时间字符串，格式为HHMM（24小时制），如"2300"表示23:00
        
        Returns:
            tuple: (起始时间戳字符串, 结束时间戳字符串)，均为秒级时间戳
        
        Example:
            >>> start_ts, end_ts = TimeParser.get_sec_level_timestamps(20250108, start_time="0900", end_time="1800")
            >>> print(start_ts, end_ts)  # "1704691200" "1704754800" (示例时间戳)
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

    @staticmethod
    def timestamp_ms_to_date_int(timestamp_ms: int):
        """
        将毫秒级时间戳转换为年月日整数
        
        Args:
            timestamp_ms: 毫秒级时间戳（整数），如1751558400000
        
        Returns:
            int: 日期整数，格式为YYYYMMDD，如20250703
        
        Example:
            >>> date_int = TimeParser.timestamp_ms_to_date_int(1751558400000)
            >>> print(date_int)  # 20250703
        """
        if not timestamp_ms or timestamp_ms == 0:
            raise ValueError("时间戳不能为空或0")
        # 将毫秒时间戳转换为秒
        dt = datetime.fromtimestamp(timestamp_ms / 1000)
        return int(dt.strftime("%Y%m%d"))


# 使用示例
if __name__ == "__main__":
    # last_monday, last_friday = TimeParser.get_last_week_period()
    # get_semester_and_week(True)
    today = datetime.now()
    current_weekday = today.weekday()
    pass