import schedule
import time
import threading
import signal
import sys
from datetime import datetime
import logging
import os

from .common.baseclient import SMCLabClient
from .crawler.bitable_crawler import (
    SMCLabWeeklyReportCrawler, 
    SMCLabSeminarCrawler,
    SMCLabScheduleCrawler
)
from .crawler.address_book_crawler import (
    SMCLabAddressBookCrawler
)
from .crawler.attendance_crawler import (
    SMCLabAttendanceCrawler
)
from .data_manager.schedule_parser import (
    SMCLabScheduleParser
)
from .data_manager.attendance_parser import (
    SMCLabDailyAttendanceParser
)
from .data_manager.bitable_parser import (
    SMCLabInfoManager,
    SMCLabWeeklyReportParser
)
from .message.sender import (
    SMCLabMessageSender
)

class SMCLabServer:
    def __init__(self):
        self.running = True
        ### 服务器相关
        self.pid_file = "server.pid"
        self.setup_logging()
        self.write_pid_file()  # 写入PID文件
        self.setup_signal_handlers()  # 设置信号处理器

        ### 飞书数据收发/处理相关
        # 下载
        self.address_book_crawler  = SMCLabAddressBookCrawler() # 每学期更新一次(或手动更新)
        self.weekly_report_crawler = SMCLabWeeklyReportCrawler() 
        self.group_meeting_crawler = SMCLabSeminarCrawler()
        self.schedule_crawler      = SMCLabScheduleCrawler()
        self.attendance_crawler    = SMCLabAttendanceCrawler()

        # 处理
        self.schedule_parser      = SMCLabScheduleParser()
        self.attendance_parser    = SMCLabDailyAttendanceParser()
        self.weekly_report_parser = SMCLabWeeklyReportParser()
        
        # 发送
        self.sender = SMCLabMessageSender()

        self.setup_schedules()

    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('server.log'),
                logging.StreamHandler()
            ]
        )
    def write_pid_file(self):
        """写入PID文件, 便于管理"""
        with open(self.pid_file, 'w') as f:
            f.write(str(os.getpid()))
        logging.info(f"PID文件已创建: {self.pid_file}, PID: {os.getpid()}")
    
    def remove_pid_file(self):
        """删除PID文件"""
        if os.path.exists(self.pid_file):
            os.remove(self.pid_file)
            logging.info("PID文件已删除")
    
    def setup_signal_handlers(self):
        """设置信号处理器"""
        signal.signal(signal.SIGINT, self.signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, self.signal_handler)  # kill命令
    
    def signal_handler(self, signum, frame):
        """信号处理函数"""
        signal_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"
        logging.info(f"收到信号: {signal_name}")
        self.stop()

    def weekly_task(self):
        """每周一中午12点执行的任务"""
        logging.info("执行每周任务")
        # 在这里添加你的每周任务逻辑
        self.send_last_week_attendence()
        logging.info("发送SMC每周总结: %s", datetime.now())
    
    def send_last_week_attendence(self, receivers: str or List[str] = ["梁涵"]):
        self.schedule_crawler.get_raw_records() # 下载最新课表数据
        self.schedule_parser.make_period_summary_json() # 处理最新的课表数据
        self.attendance_crawler.get_last_week_daily_records() # 下载上周的考勤数据
        self.attendance_parser.last_week_daily_attendance_to_excel() # 处理上周的考勤数据
        self.weekly_report_crawler.get_last_week_records() # 下载上周的周报数据
        self.weekly_report_parser.last_week_weekly_report_to_txt() # 处理上周的周报数据

        self.sender._send_weekly_summary_byweek(receivers)

    def monthly_task(self):
        """每月1号中午12点执行的任务"""
        logging.info("执行每月任务")
        # 在这里添加你的每月任务逻辑
        logging.info("每月任务执行时间: %s", datetime.now())
    
    def setup_schedules(self):
        """设置定时任务"""
        # 每周一中午12点执行
        schedule.every().monday.at("01:26").do(self.weekly_task)
        
        # 每月1号中午12点执行
        schedule.every().day.at("12:00").do(self.check_monthly_task)
        
        logging.info("定时任务设置完成")
    
    def check_monthly_task(self):
        """检查是否是每月1号，如果是则执行每月任务"""
        today = datetime.now()
        if today.day == 1:
            self.monthly_task()
    
    def main_loop(self):
        """主循环"""
        logging.info("服务器主循环启动")
        
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            logging.info("收到中断信号，正在停止服务器...")
        except Exception as e:
            logging.error(f"主循环发生错误: {e}")
        finally:
            self.cleanup()
    
    def stop(self):
        """停止服务器"""
        self.running = False
        logging.info("服务器停止信号已发送")
    
    def cleanup(self):
        """清理资源"""
        logging.info("正在清理资源...")
        self.remove_pid_file()
        logging.info("服务器已停止")

# 管理脚本功能
def manage_server(action):
    """管理服务器启动/停止"""
    if action == "start":
        if os.path.exists("server.pid"):
            with open("server.pid", 'r') as f:
                pid = f.read().strip()
            logging.info("服务器似乎已经在运行 (PID: %s)", pid)
            return
        
        logging.info("启动服务器...")
        server = SMCLabServer()
        server.main_loop()
    
    elif action == "stop":
        if not os.path.exists("server.pid"):
            logging.info("服务器未运行")
            return
        
        with open("server.pid", 'r') as f:
            pid = f.read().strip()
        
        try:
            os.kill(int(pid), signal.SIGTERM)
            logging.info("已发送停止信号到进程 %s", pid)
        except ProcessLookupError:
            logging.info("进程不存在，删除PID文件")
            os.remove("server.pid")
        except Exception as e:
            logging.error("停止服务器时出错: %s", e)
    
    elif action == "status":
        if os.path.exists("server.pid"):
            with open("server.pid", 'r') as f:
                pid = f.read().strip()
            try:
                os.kill(int(pid), 0)  # 检查进程是否存在
                logging.info("服务器正在运行 (PID: %s)", pid)
            except ProcessLookupError:
                logging.info("PID文件存在但进程未运行")
                os.remove("server.pid")
        else:
            logging.info("服务器未运行")


        