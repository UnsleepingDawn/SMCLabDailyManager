from source_code.SMCLabCrawler.MdtableCrawler import (
    SMCLabWeeklyReportCrawler, 
    SMCLabGourpMeetingCrawler,
    SMCLabScheduleCrawler
)
from source_code.SMCLabCrawler.AddressBookCrawler import (
    SMCLabAddressBookCrawler
)

if __name__ == "__main__":
    smclab_wr_client = SMCLabWeeklyReportCrawler()
    smclab_wr_client.print_basic_info()
    smclab_wr_client.get_raw_records()
    
    # smclab_gm_client = SMCLabGourpMeetingCrawler()
    # smclab_gm_client.print_basic_info()
    # smclab_gm_client.get_raw_records()

    # smclab_s_client = SMCLabScheduleCrawler()
    # smclab_s_client.print_basic_info()
    # smclab_s_client.get_raw_records() 

    # smclab_ab_client = SMCLabAddressBookCrawler()
    # # smclab_ab_client.get_department_id()
    # smclab_ab_client.get_raw_records() 
