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

本项目基于飞书 API，自动化完成中山大学SMCLab 日常数据的爬取、解析与消息发送，主要功能包括：

- 学生基础及扩展信息抓取与维护
- 组会（Seminar）安排抓取、考勤信息获取与统计
- 日常考勤数据批量抓取与处理
- 周报提交情况统计
- 通过飞书机器人自动发送通知、汇总与提醒

## 主要功能介绍

1. **学生信息维护**：  
   自动下载、合并并同步飞书通讯录信息至本地 Excel 文件，保持学生名册的更新。

2. **组会管理与考勤**：  
   自动下载组会安排，统计每周出勤情况，并通过飞书自动推送考勤结果。

3. **课表与周报统计**：  
   自动同步课表；抓取各成员周报提交状态，并生成汇总报表，支持自动群发消息。

4. **灵活的配置支持**：  
   全部操作均可按需开关，可定制日志、路径、多账号token等参数，便于二次开发与扩展。

## 示例代码

如需一键执行上一周的周报与考勤统计并推送至指定同学，可在 `main.py` 中如下调用：

```python
from src.system import SMCLabDailyManager
from src.config import Config

if __name__ == "__main__":
    config = Config()
    system = SMCLabDailyManager(config)
    # 发送上周所有统计及考勤消息给梁涵
    system.send_last_week_summary(users=["梁涵"])
```

如需强制更新通讯录和课表，并推送上周统计：

```python
system.send_last_week_summary(
    users=["梁涵", "张三"],
    update_address_book=True,
    update_schedule=True,
    use_relay=False  # 设置为True可通过中转号发送
)
```

## 适用场景

- 科研实验室日常管理
- 研究生课题组排会签到
- 自动化统计与提醒、多维数据整合

**注：更多详细用法与自定义选项，请查阅 [src/system.py](src/system.py) 和 configs 下的配置文件。**  
如有问题或需求，欢迎提Issue或参与贡献！

# 未来更新(悬赏! 欢迎大家fork开发)
- 把group_info.json也加入到"SMCLab学生扩展信息.xlsx"中
- SeminarParser在爬取之后，要去解析未来周的组会信息，并与SeminarAttendanceParser联动，因为或许本学期的组会不一定会在每周三。
- Config中应该有一个字段用于指定本学期组会的时间, 2025-Fall默认为每周三的晚上。
- 按导师划分sheet处理周报的原始数据
- 输入拟安排的meeting排表, 根据课表情况将meeting的冲突单元格标红

暂时可以不用，但是后续可能要用：
- 设置多种事件, 用于自动更新SMC的各个多维表格
- 钩子检查
- 客户端部署, 简单的GUI开发([参考](https://github.com/overflow65537/MFW-PyQt6))

# 已知需要优化 & 已知Bug
- 现在每次实例化爬虫client都要实例化一个单独的baseclient, 可以开发一个类似于from_pretrained方法, 全部的爬虫都指向同一个baseclient
