# -*- coding: utf-8 -*-
"""
配置管理器
管理应用程序的配置参数
"""

from typing import Dict, Any, Optional
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.yaml_handler import YAMLHandler
from src.core.logger import get_logger


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_file: str = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.logger = get_logger()
        
        if config_file is None:
            config_file = project_root / "config.yaml"
        
        self.config_file = Path(config_file)
        self.config_data = {}
        self.load_config()

    def load_config(self) -> bool:
        """
        加载配置文件
        
        Returns:
            加载成功返回True
        """
        try:
            self.config_data = YAMLHandler.load_yaml(str(self.config_file)) or {}
            self.logger.info(f"配置文件加载成功: {self.config_file}")
            return True
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            return False

    def save_config(self) -> bool:
        """
        保存配置文件
        
        Returns:
            保存成功返回True
        """
        try:
            success = YAMLHandler.save_yaml(str(self.config_file), self.config_data)
            if success:
                self.logger.info(f"配置文件保存成功: {self.config_file}")
            else:
                self.logger.error(f"配置文件保存失败")
            return success
        except Exception as e:
            self.logger.error(f"保存配置文件异常: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键（支持点号分隔的嵌套键）
            default: 默认值
            
        Returns:
            配置值或默认值
        """
        return YAMLHandler.get_value(self.config_data, key, default)

    def set(self, key: str, value: Any) -> None:
        """
        设置配置值
        
        Args:
            key: 配置键（支持点号分隔的嵌套键）
            value: 配置值
        """
        YAMLHandler.set_value(self.config_data, key, value)
        self.logger.debug(f"配置更新: {key} = {value}")

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self.config_data.copy()

    def update(self, data: Dict[str, Any]) -> None:
        """
        批量更新配置
        
        Args:
            data: 要更新的配置数据
        """
        for key, value in data.items():
            self.set(key, value)

    # 特定配置的便捷方法
    def get_model_config(self) -> Dict[str, Any]:
        """获取模型配置"""
        return self.get('models', {})

    def get_system_config(self) -> Dict[str, Any]:
        """获取系统配置"""
        return self.get('system', {})

    def get_expert_config(self) -> Dict[str, Any]:
        """获取专家审稿配置"""
        return self.get('expert_review', {})

    def get_search_config(self) -> Dict[str, Any]:
        """获取搜索配置"""
        return self.get('search', {})

    def set_model_config(self, key: str, value: Any) -> None:
        """设置模型配置"""
        self.set(f'models.{key}', value)

    def set_system_config(self, key: str, value: Any) -> None:
        """设置系统配置"""
        self.set(f'system.{key}', value)

    def reset_to_defaults(self) -> None:
        """重置为默认配置"""
        # 加载默认配置模板
        default_config = {
            'system': {
                'max_retries': 3,
                'timeout': 60,
                'log_level': 'INFO'
            },
            'models': {
                'primary': 'ollama',
                'ollama': {
                    'base_url': 'http://localhost:11434',
                    'model': 'llama3.1:8b',
                    'temperature': 0.7,
                    'max_tokens': 4000
                },
                'fallback': {
                    'enabled': True,
                    'base_url': 'http://localhost:11434',
                    'model': 'llama2'
                }
            },
            'expert_review': {
                'enabled': True,
                'review_steps': ['structure', 'content', 'language'],
                'acceptance_threshold': 0.8
            },
            'search': {
                'max_results': 10,
                'timeout': 30
            }
        }
        
        self.config_data = default_config
        self.logger.info("配置已重置为默认值")

    def reload(self) -> None:
        """重新加载配置文件"""
        self.load_config()


# 全局配置管理器实例
_global_config_manager = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigManager()
    return _global_config_manager


def get_config(key: str, default: Any = None) -> Any:
    """快捷方式：获取配置值"""
    return get_config_manager().get(key, default)


def set_config(key: str, value: Any) -> None:
    """快捷方式：设置配置值"""
    get_config_manager().set(key, value)
