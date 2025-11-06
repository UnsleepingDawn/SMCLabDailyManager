<p align='center'><img src='./SMC_resource/icon/logo.png' width=30%></p>

本文档维护了中山大学计算机学院SMCLab的日常事务（基于飞书API）的爬取，包括**学生信息**、**组会维护**、**周报抓取**、**考勤记录**等，欢迎SMC实验室的同学一起来维护。
本仓库为非营利、永久免费的开源项目，希望对任何基于飞书进行管理的实验室甚至企业提供参考。如果帮助到了你，希望给一个Star🌟。

[![Stars](https://img.shields.io/github/stars/UnsleepingDawn/SMCLabDailyManager.svg)](https://github.com/UnsleepingDawn/SMCLabDailyManager/stargazers)
[![Forks](https://img.shields.io/github/forks/UnsleepingDawn/SMCLabDailyManager.svg)](https://github.com/UnsleepingDawn/SMCLabDailyManager/network/members)
![GitHub repo size](https://img.shields.io/github/repo-size/UnsleepingDawn/SMCLabDailyManager.svg)
[![Issues](https://img.shields.io/github/issues/UnsleepingDawn/SMCLabDailyManager.svg)]()
![GitHub pull requests](https://img.shields.io/github/issues-pr/UnsleepingDawn/SMCLabDailyManager.svg)

## 如何贡献

欢迎您成为仓库的Contributor（[如何贡献本仓库？](Contribution.md)）

### Contributors

对所有参与本项目建设的同学们表达衷心的感谢

<a href="https://github.com/UnsleepingDawn/SMCLabDailyManager/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=UnsleepingDawn/SMCLabDailyManager" />
</a>

## 开发准备

```bash
pip install lark-oapi -U
pip install pandas
pip install PySide6-Fluent-Widgets
pip install qasync
```

## 功能介绍

### 下载数据

#### 周报

1. 下载周报的原始数据: `data_raw\weekly_report_raw_data`

#### 组会信息表格

1. 下载组会信息表格的原始数据: `data_raw\group_meeting_raw_data`

#### 新生课表

1. 下载新生课表: `data_raw\schedule_raw_data`

#### SMC通讯录

1. 下载SMC通讯录: `data_raw\address_book_raw_data`的"address_book.json"

#### 考勤

1. 下载考勤原始数据(目前只实现了下载上周的元数据)

### 处理数据

1. 从 `data_raw/group_meeting_raw_data`中提取人员信息, 整理成"SMCLab学生基本信息.xlsx"
2. 基于"SMCLab学生基本信息.xlsx"和"address_book.json", 增量更新, 并冲突合并为"SMCLab学生扩展信息.xlsx"
3. 处理新生课表原始数据
4. 处理考勤原始数据(统计上周每个人的上班无故缺勤次数)

## 未来更新(悬赏)

- 消息发送系统(发送各种统计数据给指定用户)
- 下载考勤原始数据(按特定周/月进行下载)
- 处理新生课表原始数据(可视化)
- 处理考勤原始数据(并Python作图可视化保存)
- 处理周报的原始数据(根据"SMCLab学生扩展信息.xlsx", 按周/月/学期, 以及是否按导师划分sheet)
- 将密钥和token进行索引导出、压缩, 以及解压、索引导入
- 钩子检查
- 在SMC服务器部署, 定时触发下载、自动统计和自动发送
- 客户端部署, 简单的GUI开发([参考](https://github.com/overflow65537/MFW-PyQt6))
