import json
import os
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional

from ..common.baseparser import SMCLabBaseParser
from ..utils import TimeParser, get_semester_start_date
from ..config import Config


class SMCLabSeminarManager(SMCLabBaseParser):
    """组会信息管理类，用于管理和维护学期组会信息"""
    
    def __init__(self, config: Config = None):
        """
        初始化组会管理器
        
        Args:
            config: 配置对象，如果为None则使用默认配置
        """
        if config is None:
            config = Config()
        super().__init__(config)
        # 学期文件夹路径
        self.this_sem_path = os.path.join(self._sem_data_path, self._year_semester)
        # JSON文件路径
        self.json_file_path = os.path.join(self.this_sem_path, "seminar_information.json")
        # Excel文件路径
        self.excel_file_path = os.path.join(self.this_sem_path, "seminar_information.xlsx")
        # 学期起始日期
        self.sem_start_date = get_semester_start_date(self._year_semester)
    
    def load_from_excel(self) -> pd.DataFrame:
        """
        从Excel文件读取组会信息
        
        Returns:
            pd.DataFrame: 包含组会信息的DataFrame，列包括：姓名、上次讲组会时间、近期预期、是否确认、会议室、顺序、分享主题、摘要
            
        Raises:
            FileNotFoundError: 如果Excel文件不存在
        """
        if not os.path.exists(self.excel_file_path):
            raise FileNotFoundError(f"Excel文件不存在: {self.excel_file_path}")
        
        df = pd.read_excel(self.excel_file_path)
        self.logger.info(f"成功从Excel文件读取 {len(df)} 条组会记录")
        return df
    
    def _date_to_datetime(self, date_value) -> Optional[datetime]:
        """
        将日期值转换为datetime对象
        
        Args:
            date_value: 日期值，可以是整数（YYYYMMDD格式）、datetime对象、pandas Timestamp或None
            
        Returns:
            datetime对象，如果无法转换则返回None
        """
        if pd.isna(date_value) or date_value is None:
            return None
        
        # 如果是pandas Timestamp对象
        if isinstance(date_value, pd.Timestamp):
            return date_value.to_pydatetime()
        
        # 如果是datetime对象
        if isinstance(date_value, datetime):
            return date_value
        
        # 如果是整数格式（YYYYMMDD）
        if isinstance(date_value, (int, float)):
            date_str = str(int(date_value))
            if len(date_str) == 8:
                try:
                    return datetime.strptime(date_str, "%Y%m%d")
                except ValueError:
                    return None
        
        # 如果是字符串
        if isinstance(date_value, str):
            try:
                # 尝试YYYYMMDD格式
                if len(date_value) == 8:
                    return datetime.strptime(date_value, "%Y%m%d")
            except ValueError:
                pass
        
        return None
    
    # TODO: 把这个函数写成TimeParser的函数之一
    def _calculate_week_and_weekday(self, date_obj: datetime) -> tuple:
        """
        根据日期计算周数和星期几
        
        Args:
            date_obj: 日期对象
            
        Returns:
            tuple: (week, weekday)，week为周数（从1开始），weekday为星期几（1=周一，7=周日）
        """
        # 计算周数
        days_passed = (date_obj - self.sem_start_date).days
        week = days_passed // 7 + 1
        if week < 1:
            week = 1
        
        # 计算星期几（ISO 8601标准：1=周一，7=周日）
        weekday = date_obj.isoweekday()
        
        return week, weekday
    
    def _group_by_date(self, records: List[Dict]) -> Dict[int, List[Dict]]:
        """
        将记录按日期分组
        
        Args:
            records: 记录列表，每个记录包含日期信息
            
        Returns:
            dict: 键为日期整数（YYYYMMDD格式），值为该日期的记录列表
        """
        grouped = {}
        for record in records:
            date_obj = record.get('date_obj')
            if date_obj:
                date_int = int(date_obj.strftime("%Y%m%d"))
                if date_int not in grouped:
                    grouped[date_int] = []
                grouped[date_int].append(record)
        return grouped
    
    def _convert_record_to_presentation(self, record: Dict) -> Dict:
        """
        将Excel记录转换为presentation格式
        
        Args:
            record: Excel记录字典
            
        Returns:
            dict: presentation字典，包含presenter, track, title, abstract
        """
        # 处理track字段，确保是整数
        track_value = record.get("顺序", 1)
        if pd.notna(track_value):
            try:
                track = int(track_value)
            except (ValueError, TypeError):
                track = 1
        else:
            track = 1
        
        return {
            "presenter": record.get("姓名", ""),
            "track": track,
            "title": record.get("分享主题", "") if pd.notna(record.get("分享主题")) else "",
            "abstract": record.get("摘要", "") if pd.notna(record.get("摘要")) else "",
        }
    
    def _load_existing_json(self) -> List[Dict]:
        """
        加载现有的JSON文件
        
        Returns:
            list: 现有的组会信息列表，如果文件不存在则返回空列表
        """
        if os.path.exists(self.json_file_path):
            try:
                with open(self.json_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else []
            except Exception as e:
                self.logger.warning(f"加载现有JSON文件失败: {e}，将创建新文件")
                return []
        return []
    
    def _save_to_json(self, seminar_list: List[Dict]):
        """
        保存组会信息到JSON文件
        
        Args:
            seminar_list: 组会信息列表
        """
        os.makedirs(self.this_sem_path, exist_ok=True)
        with open(self.json_file_path, 'w', encoding='utf-8') as f:
            json.dump(seminar_list, f, ensure_ascii=False, indent=2)
        self.logger.info(f"组会信息已保存到: {self.json_file_path}")
    
    def _parse_seminars_from_df(self, df: pd.DataFrame, date_column: str, happened: bool) -> List[Dict]:
        """
        从DataFrame解析组会信息
        
        Args:
            df: 包含组会信息的DataFrame
            date_column: 日期列名（"上次讲组会时间" 或 "近期预期"）
            happened: 是否已发生
            
        Returns:
            list: 组会信息列表
        """
        seminars = []
        
        # 筛选有效记录
        valid_records = []
        for _, row in df.iterrows():
            date_value = row.get(date_column)
            date_obj = self._date_to_datetime(date_value)
            
            # 只处理在本学期起始日期之后的记录
            if date_obj and date_obj >= self.sem_start_date:
                record = row.to_dict()
                record['date_obj'] = date_obj
                valid_records.append(record)
        
        if not valid_records:
            self.logger.info(f"未找到符合条件（{date_column} >= 学期起始日期）的记录")
            return seminars
        
        # 按日期分组
        grouped_records = self._group_by_date(valid_records)
        
        # 为每个日期创建组会记录
        for date_int, records in grouped_records.items():
            # 获取第一条记录的日期信息（同一日期的记录应该有相同的日期）
            date_obj = records[0]['date_obj']
            week, weekday = self._calculate_week_and_weekday(date_obj)
            
            # 获取会议室信息（通常同一日期的记录应该有相同的会议室）
            room = ""
            for record in records:
                room_value = record.get("会议室", "")
                if pd.notna(room_value) and room_value:
                    room = str(room_value)
                    break
            
            # 转换为presentations格式
            presentations = []
            for record in sorted(records, key=lambda x: x.get("顺序", 999) if pd.notna(x.get("顺序")) else 999):
                presentation = self._convert_record_to_presentation(record)
                presentations.append(presentation)
            
            # 创建组会记录
            seminar = {
                "week": week,
                "weekday": weekday,
                "happened": happened,
                "room": room,
                "presentations": presentations
            }
            seminars.append(seminar)
        
        self.logger.info(f"解析到 {len(seminars)} 个组会记录（happened={happened}）")
        return seminars
    
    def parse_past_seminars(self) -> List[Dict]:
        """
        解析已完成的组会信息：根据"上次讲组会时间"字段大于本学期起始时间的行，收录进JSON文件
        
        Returns:
            list: 已完成的组会信息列表
        """
        df = self.load_from_excel()
        seminars = self._parse_seminars_from_df(df, "上次讲组会时间", happened=True)
        return seminars
    
    def parse_upcoming_seminars(self) -> List[Dict]:
        """
        解析将要开始的组会信息：根据"近期预期"字段大于本学期起始时间的行，收录进JSON文件
        与parse_past_seminars相同，但happened字段为False
        
        Returns:
            list: 将要开始的组会信息列表
        """
        df = self.load_from_excel()
        seminars = self._parse_seminars_from_df(df, "近期预期", happened=False)
        return seminars
    
    def update_seminar_schedule(self, merge: bool = True):
        """
        更新组会信息JSON文件，合并已完成的组会和将要开始的组会
        
        Args:
            merge: 是否与现有数据合并，如果为False则完全替换
        """
        # 解析已完成的组会
        past_seminars = self.parse_past_seminars()
        
        # 解析将要开始的组会
        upcoming_seminars = self.parse_upcoming_seminars()
        
        # 合并所有组会
        all_seminars = past_seminars + upcoming_seminars
        
        if merge:
            # 加载现有数据
            existing_seminars = self._load_existing_json()
            # 创建现有数据的索引（按week, weekday, happened）
            existing_index = {
                (s.get("week"), s.get("weekday"), s.get("happened")): s
                for s in existing_seminars
            }
            
            # 更新或添加新数据
            for seminar in all_seminars:
                key = (seminar.get("week"), seminar.get("weekday"), seminar.get("happened"))
                existing_index[key] = seminar
            
            # 转换回列表并排序
            all_seminars = list(existing_index.values())
        
        # 按周数和星期几排序
        all_seminars.sort(key=lambda x: (x.get("week", 0), x.get("weekday", 0)))
        
        # 保存到JSON
        self._save_to_json(all_seminars)
        
        self.logger.info(f"共更新 {len(all_seminars)} 个组会记录")
        return all_seminars
    
    def get_seminar_weekday_map(self, prefer_happened: bool = False) -> Dict[str, int]:
        """
        读取seminar_information.json文件，返回周数对应的星期几的字典
        
        Args:
            prefer_happened: 如果同一周有多条记录（已发生和未发生），是否优先使用已发生的组会
                           如果为True，优先使用已发生的；如果为False，使用第一次遇到的
            
        Returns:
            dict: 键为周数（字符串格式），值为星期几（1=周一，7=周日）
                  例如：{"4": 3, "5": 4} 表示第4周在周三，第5周在周四
        """
        seminars = self._load_existing_json()
        weekday_map = {}
        
        # 如果优先使用已发生的，先处理未发生的，再处理已发生的（后面的会覆盖前面的）
        # 如果不优先，直接按顺序处理（第一次遇到的就保留）
        if prefer_happened:
            # 先处理未发生的
            for seminar in seminars:
                week = seminar.get("week")
                weekday = seminar.get("weekday")
                if week is not None and weekday is not None and not seminar.get("happened", False):
                    weekday_map[str(week)] = weekday
            
            # 再处理已发生的（会覆盖未发生的）
            for seminar in seminars:
                week = seminar.get("week")
                weekday = seminar.get("weekday")
                if week is not None and weekday is not None and seminar.get("happened", False):
                    weekday_map[str(week)] = weekday
        else:
            # 按顺序处理，第一次遇到的保留
            for seminar in seminars:
                week = seminar.get("week")
                weekday = seminar.get("weekday")
                if week is not None and weekday is not None:
                    week_str = str(week)
                    if week_str not in weekday_map:
                        weekday_map[week_str] = weekday
        
        # self.logger.info(f"成功读取组会星期映射，共 {len(weekday_map)} 周")
        return weekday_map

    