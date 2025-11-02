from source_code.SMCLabCrawler.MdtableCrawler import SMCLabClient, SMCLabWeeklyReportCrawler, SMCLabGourpMeetingCrawler

if __name__ == "__main__":
    smclab_wr_client = SMCLabWeeklyReportCrawler()
    smclab_wr_client.print_basic_info()
    smclab_wr_client.get_raw_records()