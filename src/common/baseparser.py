import os
from ..utils import get_semester, get_semester_and_week
from ..config import Config

class SMCLabBaseParser:
    def __init__(self, config: Config = None) -> None:
        if config is None:
            config = Config()
        self._incre_data_path = config.incre_data_path
        self._sem_data_path = config.sem_data_path
        self._year_semester, self._this_week = get_semester_and_week(config.sysu_semesters_path)    
        
    def reset_time(self):
        self._year_semester, self._this_week = get_semester_and_week()

