<p align='center'><img src='./SMC_resource/icon/logo.png' width=30%></p>

本文档维护了中山大学计算机学院SMCLab的日常事务（基于飞书API）的爬取，包括**学生信息**、**组会维护**、**周报抓取**、**考勤记录**等，欢迎SMC实验室的同学一起来维护。
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

```bash
pip install lark-oapi
pip install pandas
pip install PySide6-Fluent-Widgets
pip install qasync
pip install matplotlib
pip install seaborn
pip install schedule
pip install openpyxl
```

```bash
pip install lark-oapi pandas PySide6-Fluent-Widgets qasync matplotlib seaborn schedule openpyxl
```

# 功能介绍

分为服务器功能和任务功能

## 服务器功能

一个长期运行在服务器上的定时任务调度系统，支持每周和每月特定时间执行任务。
功能特点：

- 每周一中午12:00自动执行任务
- 每月1号中午12:00自动执行任务
- 完善的日志记录系统
- 优雅的启动/停止机制
- 进程管理和监控

有两种启动方法

1. 直接运行（开发测试）

```bash
python server.py
```

或者使用管理命令

```bash
python server.py start
```

按 `Ctrl+C`停止服务器

2. 后台运行（生产环境）

```bash
# 使用nohup在后台运行
nohup python server.py > server.log 2>&1 &

# 使用screen在后台运行
screen -S task_server
python server.py
# 按 Ctrl+A, 然后按 D 退出screen（程序继续运行）
# screen -r task_server 重新连接
```

3. 使用管理脚本

```bash
# 启动服务器
python server.py start

# 停止服务器
python server.py stop

# 查看服务器状态
python server.py status
```

### 配置说明

**定时任务配置**
在 server.py中修改定时任务：

```python
def setup_schedules(self):
    """设置定时任务"""
    # 每周一中午12点执行
    schedule.every().monday.at("12:00").do(self.weekly_task)
  
    # 每月1号中午12点执行
    schedule.every().day.at("12:00").do(self.check_monthly_task)
```

**自定义任务**
修改以下方法来添加你的业务逻辑：

```python
def weekly_task(self):
    """每周一中午12点执行的任务"""
    logging.info("执行每周任务")
    # 在这里添加你的每周任务逻辑
    # 例如：数据备份、报表生成等

def monthly_task(self):
    """每月1号中午12点执行的任务"""
    logging.info("执行每月任务")
    # 在这里添加你的每月任务逻辑
    # 例如：月度统计、账单生成等
```

## 数据收发/处理功能

### 收发功能

1. 下载周报的原始数据: `data_raw\weekly_report_raw_data`
2. 下载组会信息表格的原始数据: `data_raw\group_meeting_raw_data`
3. 下载新生课表: `data_raw\schedule_raw_data`
4. 下载SMC通讯录: `data_raw\address_book_raw_data`的"address_book.json"
5. 下载考勤原始数据(目前只实现了下载上周的元数据)
6. 处理新生课表原始数据(可视化)
7. 处理考勤原始数据(并Python作图可视化保存)
8. 消息发送系统

### 处理数据

1. 从 `data_raw/group_meeting_raw_data`中提取人员信息, 整理成"SMCLab学生基本信息.xlsx"
2. 基于"SMCLab学生基本信息.xlsx"和"address_book.json", 增量更新, 并冲突合并为"SMCLab学生扩展信息.xlsx"
3. 处理新生课表原始数据
4. 处理考勤原始数据(统计上周每个人的上班无故缺勤次数)

# 未来更新(悬赏! 欢迎大家fork开发)

- 下载考勤原始数据(按特定周/月进行下载)
- 处理周报的原始数据(根据"SMCLab学生扩展信息.xlsx", 按周/月/学期, 以及是否按导师划分sheet)
- 输入拟安排的meeting排表, 根据课表情况将meeting的冲突单元格标红
- 将密钥和token进行索引导出、压缩, 以及解压、索引导入
- 设置多种事件, 用于自动更新SMC的各个多维表格
- 钩子检查
- 客户端部署, 简单的GUI开发([参考](https://github.com/overflow65537/MFW-PyQt6))

# 已知需要优化 & 已知Bug

- 非常重要：服务器端维护一个每周已完成爬取的清单，防止重复消耗API。
- 现在每次实例化爬虫client都要实例化一个单独的baseclient, 可以开发一个类似于from_pretrained方法, 全部的爬虫都指向同一个baseclient
