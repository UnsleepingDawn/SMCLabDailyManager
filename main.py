from source_code.SMCLabCrawler.BitableCrawler import (
    SMCLabWeeklyReportCrawler, 
    SMCLabGourpMeetingCrawler,
    SMCLabScheduleCrawler
)
from source_code.SMCLabCrawler.AddressBookCrawler import (
    SMCLabAddressBookCrawler
)
from source_code.SMCLabCrawler.AttendanceCrawler import (
    SMCLabAttendanceCrawler
)
from source_code.SMCLabDataManager.ScheduleParser import (
    SMCLabScheduleParser
)
from source_code.SMCLabDataManager.AttendanceParser import (
    SMCLabAttendanceParser
)

if __name__ == "__main__":
    # smclab_gm_client = SMCLabGourpMeetingCrawler()
    # smclab_gm_client.print_basic_info()
    # smclab_gm_client.get_raw_records()

    # smclab_wr_client = SMCLabWeeklyReportCrawler()
    # smclab_wr_client.print_basic_info()
    # smclab_wr_client.get_raw_records()

    # smclab_s_client = SMCLabScheduleCrawler()
    # smclab_s_client.print_basic_info()
    # smclab_s_client.get_raw_records() 

    # smclab_s_parser = SMCLabScheduleParser()
    # smclab_s_parser.make_count_schedule_xlsx()
    # smclab_s_parser.make_name_schedule_xlsx()
    # smclab_s_parser.make_period_summary_json()
    # smclab_s_parser.make_schedule_json()

    # smclab_ab_client = SMCLabAddressBookCrawler()
    # # smclab_ab_client.get_department_id()
    # smclab_ab_client.get_raw_records() 

    # smclab_a_client = SMCLabAttendanceCrawler()
    # smclab_a_client.get_last_week_record()

    smclab_a_parser = SMCLabAttendanceParser()
    smclab_a_parser.mark_class_absence()