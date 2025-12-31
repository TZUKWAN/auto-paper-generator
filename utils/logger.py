"""日志工具"""
import logging
import os
import sys
import io
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
    
    handlers = [
        logging.FileHandler(log_file, encoding='utf-8')
    ]

    # Only add stream handler if stdout is available (not None)
    if sys.stdout is not None:
        try:
            # Create UTF-8 safe stream handler
            if hasattr(sys.stdout, 'buffer'):
                stream = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            else:
                stream = sys.stdout
            
            stream_handler = logging.StreamHandler(stream=stream)
            handlers.append(stream_handler)
        except Exception:
            pass # Ignore stream errors in restricted environments

    # 配置日志
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"日志系统已初始化: {log_file}")
    
    return logger
