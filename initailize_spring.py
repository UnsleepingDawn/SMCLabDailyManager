from src.system import SMCLabDailyManager
from src.config import Config



if __name__ == "__main__":
    config = Config()
    system = SMCLabDailyManager(config)

    # system.initial_spring_semester(meeting_periods=["周三下午", "周三晚上"]) # 更新新的通讯录
    system.initial_spring_semester(meeting_periods=["周三上午", "周三下午"]) # 更新新的通讯录
    
