"""日志工具"""
import logging
import os
from datetime import datetime

def setup_logging(log_path="logs/generation.log", level="INFO"):
    """
    配置日志系统
    
    Args:
        log_path: 日志文件路径
        level: 日志级别
    """
    # 确保日志目录存在
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    # 生成带时间戳的日志文件
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_path.replace('.log', f'_{timestamp}.log')
    
    # 配置日志
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"日志系统已初始化: {log_file}")
    
    return logger
