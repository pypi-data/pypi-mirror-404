import logging
import sys

import colorlog

# 定义自定义日志级别
INFO1 = 21
INFO2 = 22
INFO3 = 23

# 添加自定义日志级别到logging模块
logging.addLevelName(INFO1, "INFO1")
logging.addLevelName(INFO2, "INFO2")
logging.addLevelName(INFO3, "INFO3")


# 为logger添加自定义方法
def info1(self, message, *args, **kwargs):
    if self.isEnabledFor(INFO1):
        self._log(INFO1, message, args, **kwargs)


def info2(self, message, *args, **kwargs):
    if self.isEnabledFor(INFO2):
        self._log(INFO2, message, args, **kwargs)


def info3(self, message, *args, **kwargs):
    if self.isEnabledFor(INFO3):
        self._log(INFO3, message, args, **kwargs)


# 将自定义方法添加到Logger类
logging.Logger.info1 = info1  # type: ignore[attr-defined]
logging.Logger.info2 = info2  # type: ignore[attr-defined]
logging.Logger.info3 = info3  # type: ignore[attr-defined]

# 配置彩色logging
handler = logging.StreamHandler(sys.stdout)  # <-- 指向 stdout
handler.setFormatter(
    colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(name)s - %(levelname)-5s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "white",
            "INFO": "white",
            "INFO1": "green",
            "INFO2": "cyan",
            "INFO3": "blue",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )
)

logger = logging.getLogger("xiaozhi_sdk")
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
