# -*- coding: utf-8 -*-
"""
YAML文件处理器
解决PyYAML依赖和中文编码问题
"""

import yaml
import os
from pathlib import Path
from typing import Any, Dict, Optional


class YAMLHandler:
    """YAML文件处理器，统一处理编码问题"""

    @staticmethod
    def load_yaml(filepath: str) -> Optional[Dict[str, Any]]:
        """
        加载YAML文件
        
        Args:
            filepath: YAML文件路径
            
        Returns:
            解析后的数据字典，失败返回None
        """
        try:
            if not os.path.exists(filepath):
                print(f"文件不存在: {filepath}")
                return None
            
            # 使用UTF-8编码读取
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            return data if data else {}
            
        except yaml.YAMLError as e:
            print(f"YAML解析错误: {e}")
            return None
        except Exception as e:
            print(f"读取文件错误: {e}")
            return None

    @staticmethod
    def save_yaml(filepath: str, data: Dict[str, Any]) -> bool:
        """
        保存数据到YAML文件
        
        Args:
            filepath: YAML文件路径
            data: 要保存的数据字典
            
        Returns:
            成功返回True，失败返回False
        """
        try:
            # 确保目录存在
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            # 使用UTF-8编码写入，允许Unicode字符
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.safe_dump(data, f, allow_unicode=True, 
                              default_flow_style=False,
                              sort_keys=False,
                              indent=2)
            
            return True
            
        except Exception as e:
            print(f"保存文件错误: {e}")
            return False

    @staticmethod
    def get_value(data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """
        安全获取字典中的值
        
        Args:
            data: 数据字典
            key: 键名（支持点号分隔的嵌套键，如'config.model'）
            default: 默认值
            
        Returns:
            键对应的值或默认值
        """
        keys = key.split('.')
        value = data
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    @staticmethod
    def set_value(data: Dict[str, Any], key: str, value: Any) -> None:
        """
        安全设置字典中的值
        
        Args:
            data: 数据字典
            key: 键名（支持点号分隔的嵌套键）
            value: 要设置的值
        """
        keys = key.split('.')
        current = data
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value


# 简化的全局访问函数
def load_config(filepath: str) -> Optional[Dict[str, Any]]:
    """加载配置文件"""
    return YAMLHandler.load_yaml(filepath)


def save_config(filepath: str, data: Dict[str, Any]) -> bool:
    """保存配置文件"""
    return YAMLHandler.save_yaml(filepath, data)
