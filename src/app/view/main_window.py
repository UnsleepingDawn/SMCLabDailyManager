import os, sys

from PySide6.QtCore import QSize, QTimer
from PySide6.QtGui import QIcon, QShortcut, QKeySequence
from PySide6.QtWidgets import QApplication

from qfluentwidgets import (
    NavigationItemPosition,
    FluentWindow,
    SplashScreen,
    SystemThemeListener,
    isDarkTheme,
    InfoBar,
)

from ..common.config import cfg
from ..common.signal_bus import signalBus

class CustomSystemThemeListener(SystemThemeListener):
    def run(self):
        try:
            # 调用原始的 run 方法
            super().run()
        except NotImplementedError:
            print("当前环境不支持主题监听，已忽略", file=sys.stderr)

class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.initWindow()
        # 使用自定义的主题监听器
        self.themeListener = CustomSystemThemeListener(self)        
        # 启用Fluent主题效果
        self.navigationInterface.setAcrylicEnabled(True)

        self.connectSignalToSlot()

        # 记录 AssistToolTaskInterface 导航项索引
        self.AssistTool_task_nav_index = None

        # 添加导航项
        # self.initNavigation()
        self.splashScreen.finish()

        QTimer.singleShot(5000, lambda: cfg.set(cfg.start_complete, True))

    def initWindow(self):
        """初始化窗口设置。"""
        self.resize(960, 780)
        self.setMinimumWidth(760)
        self.setWindowIcon(QIcon("./SMC_resource/icon/logo.png"))
        self.set_title() 
        self.setMicaEffectEnabled(cfg.get(cfg.micaEnabled))

        # 创建启动画面
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(106, 106))
        self.splashScreen.raise_()

        desktop = QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)
        self.show()
        QApplication.processEvents()

        # # 显示公告 MessageBox
        # if (
        #     cfg.get(cfg.show_notice)
        #     # or maa_config_data.interface_config.get("show_notice")
        # ) and not cfg.get(cfg.hide_notice):

        #     QTimer.singleShot(500, self.show_announcement)

    def set_title(self):
        """设置窗口标题"""
        title = cfg.get(cfg.title)
        if not title:
            title = self.tr("SMCLab Daily Manager")
        # resource_name = cfg.get(cfg.maa_resource_name)
        # config_name = cfg.get(cfg.maa_config_name)
        # version = maa_config_data.interface_config.get("version", "")

        # title += f" {__version__}"

        # if resource_name != "":
        #     title += f" {resource_name}"
        # if version != "":
        #     title += f" {version}"
        # if config_name != "":
        #     title += f" {config_name}"
        # if self.is_admin():
        #     title += " " + self.tr("admin")
        # if cfg.get(cfg.save_draw) or cfg.get(cfg.recording):
        #     title += " " + self.tr("Debug")

        # logger.info(f" 设置窗口标题：{title}")

        self.setWindowTitle(title)

    def connectSignalToSlot(self):
        """连接信号到槽函数。"""
        # signalBus.show_download.connect(self.show_download)
        # signalBus.micaEnableChanged.connect(self.setMicaEffectEnabled)
        # signalBus.title_changed.connect(self.set_title)
        # signalBus.bundle_download_finished.connect(self.show_info_bar)
        # signalBus.download_finished.connect(self.show_info_bar)
        # signalBus.update_download_finished.connect(self.show_info_bar)
        # signalBus.mirror_bundle_download_finished.connect(self.show_info_bar)
        # signalBus.download_self_finished.connect(self.show_info_bar)
        # signalBus.infobar_message.connect(self.show_info_bar)
        # signalBus.show_AssistTool_task.connect(self.toggle_AssistTool_task)
        # signalBus.notice_finished.connect(self.show_notice_finished)
        # self.settingInterface.dingtalk_noticeTypeCard.button.clicked.connect(
        #     self.dingtalk_setting
        # )
        # self.settingInterface.lark_noticeTypeCard.button.clicked.connect(
        #     self.lark_setting
        # )
        # self.settingInterface.SMTP_noticeTypeCard.button.clicked.connect(
        #     self.smtp_setting
        # )
        # self.settingInterface.WxPusher_noticeTypeCard.button.clicked.connect(
        #     self.wxpusher_setting
        # )
        # self.settingInterface.QYWX_noticeTypeCard.button.clicked.connect(
        #     self.QYWX_setting
        # )
        # self.settingInterface.send_settingCard.button.clicked.connect(
        #     self.send_setting_setting
        # )
        return