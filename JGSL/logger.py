from loguru import logger
import os
import sys

# 移除默认的控制台输出
logger.remove()

# 配置日志输出到文件
logger.add(
    os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Logs', 'JGSL.log'),
    rotation='1 week',
    retention='1 month',
    encoding='utf-8',
    format='{time:YYYY-MM-DD HH:mm:ss} | {level} | PID:{process.id} TID:{thread.id} | {module} | {message}',
    diagnose=True,
    level="TRACE" # 显式设置文件日志级别为 TRACE
)

logger.add(
    sys.stderr, # 输出到标准错误流
    level="INFO", # 设置控制台日志级别为 INFO
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)