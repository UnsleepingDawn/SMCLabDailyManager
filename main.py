from source_code.crawler.bitable import (
    SMCLabWeeklyReportCrawler, 
    SMCLabGourpMeetingCrawler,
    SMCLabScheduleCrawler
)
from source_code.crawler.address_book import (
    SMCLabAddressBookCrawler
)
from source_code.crawler.attendance import (
    SMCLabAttendanceCrawler
)
from source_code.data_manager.schedule_parser import (
    SMCLabScheduleParser
)
from source_code.data_manager.attendance_parser import (
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
    # smclab_s_parser.make_schedule_count_xlsx()
    # smclab_s_parser.make_schedule_names_xlsx()
    # smclab_s_parser.make_period_summary_json()
    # smclab_s_parser.make_schedule_by_slot_json()

    # smclab_ab_client = SMCLabAddressBookCrawler()
    # # smclab_ab_client.get_department_id()
    # smclab_ab_client.get_raw_records() 

    # smclab_a_client = SMCLabAttendanceCrawler()
    # smclab_a_client.get_last_week_record()

    smclab_a_parser = SMCLabAttendanceParser()
    smclab_a_parser.last_week_attendance_to_excel()