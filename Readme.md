<p align='center'><img src='./SMC_resource/icon/logo.png' width=30%></p>

本文档维护了中山大学计算机学院SMCLab的日常事务（基于飞书API）的爬取与自动化管理，包括**学生信息**、**组会维护**、**周报抓取**、**考勤记录**、**小组会议智能排班**等，欢迎SMC实验室的同学一起来维护。

本仓库为非营利、永久免费的开源项目，希望对任何基于飞书进行管理的实验室甚至企业提供参考。如果帮助到了你，希望给一个Star🌟。

[![Stars](https://img.shields.io/github/stars/UnsleepingDawn/SMCLabDailyManager.svg)](https://github.com/UnsleepingDawn/SMCLabDailyManager/stargazers)
[![Forks](https://img.shields.io/github/forks/UnsleepingDawn/SMCLabDailyManager.svg)](https://github.com/UnsleepingDawn/SMCLabDailyManager/network/members)
![GitHub repo size](https://img.shields.io/github/repo-size/UnsleepingDawn/SMCLabDailyManager.svg)
[![Issues](https://img.shields.io/github/issues/UnsleepingDawn/SMCLabDailyManager.svg)]()
![GitHub pull requests](https://img.shields.io/github/issues-pr/UnsleepingDawn/SMCLabDailyManager.svg)

# 如何贡献

欢迎您成为仓库的Contributor（[如何贡献本仓库？](SMC_resource/docs/Contribution.md)）

## Contributors

<a href="https://github.com/UnsleepingDawn/SMCLabDailyManager/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=UnsleepingDawn/SMCLabDailyManager" />
</a>

# 开发准备

## 依赖安装

```bash
pip install lark-oapi pandas PySide6-Fluent-Widgets qasync matplotlib seaborn schedule openpyxl pulp
```

或逐个安装：

```bash
pip install lark-oapi    # 飞书 API SDK
pip install pandas       # 数据处理
pip install openpyxl     # Excel 读写
pip install matplotlib   # 数据可视化
pip install seaborn      # 统计图表
pip install pulp         # 整数线性规划（小组会议排班）
pip install PySide6-Fluent-Widgets  # GUI 组件（可选）
pip install qasync       # 异步支持（可选）
pip install schedule     # 定时任务（可选）
```

## 项目结构

```
SMCLabDailyManager/
├── configs/                    # 配置文件目录
│   ├── config.json            # 主配置文件
│   ├── bitable_info.json      # 多维表格信息
│   ├── sysu_semesters.json    # 学期日历
│   └── post_template/         # 消息模板
├── data_raw/                   # 原始数据（爬取结果）
├── data_sem/                   # 学期数据（按学期组织）
│   └── 2025-Fall/
│       ├── seminar_information.json   # 组会信息
│       ├── schedule_by_period.json    # 课程安排（按时段）
│       ├── group_meeting_name_list.json  # 小组会议名单
│       └── already_grouped.json       # 已确定的分组
├── data_incre/                 # 增量数据（学生信息等）
├── src/
│   ├── crawler/               # 爬虫模块
│   │   ├── address_book_crawler.py   # 通讯录爬虫
│   │   ├── attendance_crawler.py     # 考勤爬虫
│   │   └── bitable_crawler.py        # 多维表格爬虫
│   ├── data_manager/          # 数据解析模块
│   │   ├── address_book_parser.py    # 通讯录解析
│   │   ├── attendance_parser.py      # 考勤解析
│   │   ├── bitable_parser.py         # 多维表格解析
│   │   ├── schedule_parser.py        # 课表解析
│   │   ├── seminar_manager.py        # 组会管理
│   │   └── excel_manager.py          # Excel 管理
│   ├── message/               # 消息模块
│   │   └── sender.py          # 飞书消息发送
│   ├── operate/               # 操作模块
│   │   └── gourp_meeting_scheduler.py  # 小组会议排班（ILP算法）
│   ├── common/                # 公共组件
│   │   ├── baseclient.py      # 飞书客户端基类
│   │   └── baseparser.py      # 解析器基类
│   ├── config.py              # 配置类
│   ├── system.py              # 系统主类
│   └── utils.py               # 工具函数
├── main.py                    # 程序入口
└── Readme.md
```

# 功能介绍

本项目基于飞书 API，自动化完成中山大学 SMCLab 日常数据的爬取、解析与消息发送，主要功能包括：

## 1. 学生信息维护

自动下载、合并并同步飞书通讯录信息至本地 Excel 文件，保持学生名册的更新。

- 从飞书通讯录批量爬取成员信息
- 与组会表格中的扩展信息自动合并
- 支持按导师、在读情况等字段筛选

## 2. 组会管理与考勤

自动下载组会安排，统计每周出勤情况，并通过飞书自动推送考勤结果。

- 从多维表格爬取组会安排信息
- 自动解析并生成结构化的组会日程 JSON
- 统计组会出勤情况（到场/缺席名单）
- 支持按周次查询组会日期

## 3. 日常考勤统计

批量爬取日常打卡数据并生成统计图表。

- 按周爬取考勤打卡记录
- 自动生成考勤统计 Excel 和可视化图表
- 支持多种考勤组配置

## 4. 周报提交统计

爬取各成员周报提交状态，并生成汇总报表。

- 从飞书多维表格爬取周报记录
- 统计已提交/未提交名单
- 生成周报汇总报告

## 5. 消息自动推送

通过飞书机器人自动发送各类汇总与提醒。

- 支持发送富文本消息（包含图片）
- 可定制消息模板
- 支持群发给多个用户

## 6. 小组会议智能排班（新功能）

基于**二进制整数线性规划（BILP）**算法，自动安排小组会议时间，实现最优排班。

> 📄 算法原理详见：[BILP optimization.md](SMC_resource/docs/BILP%20optimization.md)，包含完整的数学建模与约束条件说明。

### 功能特点

- **课程冲突避让**：自动读取成员课表，确保会议时间不与课程冲突
- **分组规模控制**：支持 2-4 人的灵活分组
- **时段容量限制**：可设置每个时段最大会议组数
- **预设分组支持**：支持指定必须在同一组的成员
- **多目标优化**：最小化小组数量，均衡各时段安排

### 使用示例

```python
from src.operate.gourp_meeting_scheduler import SMCLabGourpMeetingScheduler
from src.config import Config

config = Config()
scheduler = SMCLabGourpMeetingScheduler(config)

# 加载学生名单（从文件或按导师筛选）
scheduler.build_student_list(from_file=True)

# 加载课程安排
scheduler.fetch_course_schedule()

# 加载已确定的分组（可选）
scheduler.fetch_already_grouped()

# 执行排班
result = scheduler.schedule_group_meeting(
    periods=["周四上午", "周四下午"],  # 可用时段
    max_groups_per_period=4           # 每时段最大组数
)

# 结果格式: {"周四上午": [["张三", "李四"], ["王五", "赵六"]], ...}
print(result)
```

### 配置说明

在 `configs/config.json` 中配置：

```json
{
    "group_meeting_scheduler": {
        "max_groups_per_period": 4,
        "default_periods": ["周四上午", "周四下午"]
    }
}
```

### 数据文件

在 `data_sem/{学期}/` 目录下：

- `group_meeting_name_list.json`：参与小组会议的学生名单
- `schedule_by_period.json`：学生课程安排（按时段汇总）
- `already_grouped.json`：已确定的分组（可选）

# 快速开始

## 示例1：发送上周汇总

一键执行上一周的周报与考勤统计并推送至指定同学：

```python
from src.system import SMCLabDailyManager
from src.config import Config

if __name__ == "__main__":
    config = Config()
    system = SMCLabDailyManager(config)
    system.send_last_week_summary(users=["梁涵"])
```

## 示例2：强制更新数据后推送

```python
system.send_last_week_summary(
    users=["梁涵", "张三"],
    update_address_book=True,  # 更新通讯录
    update_schedule=True,       # 更新课表
    update_seminar_info=True,   # 更新组会信息
    use_relay=False
)
```

## 示例3：更新通讯录

```python
system.update_address_book()
```

## 示例4：发送本周组会考勤

```python
system.send_this_week_seminar_attendance(user="梁涵")
```

# 配置说明

主要配置项在 `configs/config.json` 中：

| 配置项 | 说明 |
|--------|------|
| `paths.*` | 各类数据文件路径 |
| `logger.*` | 日志配置（级别、格式、文件） |
| `addressbook.*` | 通讯录爬虫配置 |
| `daily_attendance.*` | 日常考勤配置 |
| `seminar_attendance.*` | 组会考勤配置 |
| `group_meeting_scheduler.*` | 小组会议排班配置 |
| `bitable.*` | 多维表格爬虫配置 |

# 适用场景

- 科研实验室日常管理
- 研究生课题组排会签到
- 自动化统计与提醒
- 多维数据整合与可视化
- 小组会议智能排班

# 未来更新（悬赏！欢迎大家 fork 开发）

- [ ] 按导师划分 sheet 处理周报的原始数据
- [ ] 设置多种事件，用于自动更新 SMC 的各个多维表格
- [ ] 钩子检查机制
- [ ] 客户端部署，简单的 GUI 开发（[参考](https://github.com/overflow65537/MFW-PyQt6)）
- [ ] 小组会议排班结果可视化与导出

# 已知需要优化 & 已知 Bug

- 现在每次实例化爬虫 client 都要实例化一个单独的 baseclient，可以开发一个类似于 `from_pretrained` 方法，全部的爬虫都指向同一个 baseclient
- logger格式太复杂需要进行统一
- 如果当周没有组会，会报错，但是发送空消息即可，不需要assert报错

---

**更多详细用法与自定义选项，请查阅 [src/system.py](src/system.py) 和 configs 下的配置文件。**

如有问题或需求，欢迎提 Issue 或参与贡献！
