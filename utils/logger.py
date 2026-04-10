import logging
import colorlog
from config.settings import settings

def setup_logging():
    """配置彩色日志"""
    # 创建根日志记录器
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    # 清除已有处理器
    logger.handlers.clear()

    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # 定义颜色格式
    formatter = colorlog.ColoredFormatter(
        fmt='%(log_color)s%(asctime)s [%(levelname)s] %(name)s - %(message)s',
        datefmt='%H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 可选：文件日志（不带颜色）
    if settings.LOG_FILE:
        file_handler = logging.FileHandler(settings.LOG_FILE, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        plain_formatter = logging.Formatter(
            fmt='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(plain_formatter)
        logger.addHandler(file_handler)

    # 降低第三方库日志级别
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("pynput").setLevel(logging.WARNING)