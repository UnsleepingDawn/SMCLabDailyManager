import time

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

if __name__ == "__main__":
    get_year_semester(True)