from loguru import logger
import os

# 配置日志输出到文件
logger.add(
    os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Logs', 'JGSL.log'),
    rotation='1 week',
    retention='1 month',
    encoding='utf-8',
    format='{time:YYYY-MM-DD HH:mm:ss} | {level} | PID:{process.id} TID:{thread.id} | {module} | {message}',
    enqueue=True,
    diagnose=True
)