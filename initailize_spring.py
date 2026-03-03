from src.system import SMCLabDailyManager
from src.config import Config



if __name__ == "__main__":
    config = Config()
    system = SMCLabDailyManager(config)

    system.ensure_directories()
    system.update_address_book()
    
