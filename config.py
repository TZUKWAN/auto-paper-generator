"""配置管理模块 - 增强版

支持:
- 单例模式
- 观察者模式（配置变更订阅）
- 热重载
"""
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from typing import Callable, List, Any, Optional

# 加载环境变量
load_dotenv()


class ConfigManager:
    """配置管理器 - 单例模式"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, config_path="config.yaml"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config_path="config.yaml"):
        # 避免重复初始化
        if ConfigManager._initialized:
            return
        
        self.config_path = config_path
        self._config = self._load_config()
        self._observers: List[Callable[[str, Any, Any], None]] = []
        ConfigManager._initialized = True
    
    def _load_config(self):
        """加载YAML配置文件"""
        import sys
        
        # Determine paths to check
        paths_to_check = [self.config_path] # default relative to CWD
        
        if getattr(sys, 'frozen', False):
            # If frozen, look in the same directory as the executable first (user override)
            exe_dir = os.path.dirname(os.path.abspath(sys.executable))
            paths_to_check.insert(0, os.path.join(exe_dir, 'config.yaml'))
            
            # Then check _internal (sys._MEIPASS) for bundled config
            if hasattr(sys, '_MEIPASS'):
                 paths_to_check.append(os.path.join(sys._MEIPASS, 'config.yaml'))
        
        for path in paths_to_check:
             if os.path.exists(path):
                 try:
                     with open(path, 'r', encoding='utf-8') as f:
                         return yaml.safe_load(f)
                 except Exception as e:
                     print(f"Error loading config from {path}: {e}")
                     
        # 返回默认配置
        return self._default_config()
    
    def _default_config(self):
        """默认配置"""
        return {
            'project': {
                'title': '未命名论文',
                'keywords': ''
            },
            'template': {
                'type': 'theoretical',
                'path': 'templates/theoretical_paper.yaml'
            },
            'model_routing': {
                'default_provider': 'siliconflow',
                'providers': {
                    'siliconflow': {
                        'enabled': True,
                        'base_url': 'https://api.siliconflow.cn/v1',
                        'api_key': os.getenv('SILICON_API_KEY', ''),
                        'models': ['deepseek-ai/DeepSeek-R1-0528-Qwen3-8B', 'Qwen/Qwen2.5-7B-Instruct'],
                        'max_tokens': 4096,
                        'temperature': 0.7,
                        'enable_thinking': True,
                        'thinking_budget': 4096
                    },
                    'openai': {
                        'enabled': False,
                        'base_url': 'https://api.openai.com/v1',
                        'api_key': os.getenv('OPENAI_API_KEY', ''),
                        'models': ['gpt-4o', 'gpt-4-turbo'],
                        'max_tokens': 4096
                    },
                    'zhipuai': {
                        'enabled': False,
                        'base_url': 'https://open.bigmodel.cn/api/paas/v4',
                        'api_key': os.getenv('ZHIPU_API_KEY', ''),
                        'models': ['glm-4', 'glm-4-air'],
                        'max_tokens': 4096
                    },
                    'deepseek': {
                        'enabled': False,
                        'base_url': 'https://api.deepseek.com/v1',
                        'api_key': os.getenv('DEEPSEEK_API_KEY', ''),
                        'models': ['deepseek-chat', 'deepseek-reasoner'],
                        'max_tokens': 4096
                    },
                    'tongyi': {
                        'enabled': False,
                        'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
                        'api_key': os.getenv('TONGYI_API_KEY', ''),
                        'models': ['qwen-max', 'qwen-plus'],
                        'max_tokens': 4096
                    }
                }
            },
            'literature': {
                'pool_path': 'data/literature_pool.txt',
                'projects_base_dir': 'data/projects',
                'web_search': {
                    'enabled': True,
                    'mode': 'deep',
                    'results_per_query': 10,
                    'crawl_count': 3,
                    'headless': True
                }
            },
            'citation': {
                'target_per_sentence': 2,
                'min_per_paragraph': 3,
                'max_per_paragraph': 10,
                'similarity_threshold': 0.6,
                'diversity_weight': 0.3
            },
            'reference_documents': {
                'enabled': False,
                'pdf_folder': 'data/pdfs'
            },
            'expert_review': {
                'enabled': False,
                'max_rounds': 3,
                'target_score': 90
            },
            'quality_metrics': {
                'enabled': True
            },
            'output': {
                'format': 'word',
                'path': 'output/论文初稿.docx'
            },
            'logging': {
                'level': 'INFO',
                'path': 'logs/generation.log'
            }
        }
    
    def subscribe(self, callback: Callable[[str, Any, Any], None]):
        """
        订阅配置变更
        
        Args:
            callback: 回调函数，签名 (key_path, old_value, new_value)
        """
        self._observers.append(callback)
    
    def unsubscribe(self, callback: Callable[[str, Any, Any], None]):
        """取消订阅"""
        if callback in self._observers:
            self._observers.remove(callback)
    
    def _notify(self, key_path: str, old_value: Any, new_value: Any):
        """通知所有观察者"""
        for callback in self._observers:
            try:
                callback(key_path, old_value, new_value)
            except Exception:
                pass  # 忽略回调错误
    
    def reload(self):
        """热重载配置文件"""
        self._config = self._load_config()
        # 通知观察者配置已重载
        for callback in self._observers:
            try:
                callback('__reload__', None, None)
            except Exception:
                pass
    
    def get(self, key_path: str, default=None):
        """
        获取配置值
        
        Args:
            key_path: 配置路径，如 'model_routing.ollama.model'
            default: 默认值
        """
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any, notify: bool = True):
        """
        设置配置值
        
        Args:
            key_path: 配置路径
            value: 新值
            notify: 是否通知观察者
        """
        keys = key_path.split('.')
        config = self._config
        
        # 获取旧值
        old_value = self.get(key_path)
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
        
        # 通知观察者
        if notify and old_value != value:
            self._notify(key_path, old_value, value)
    
    def save(self):
        """保存配置到文件"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self._config, f, allow_unicode=True, default_flow_style=False)


# 兼容旧代码：保留 Config 类别名
Config = ConfigManager

# 全局配置实例（单例）
config = ConfigManager()

