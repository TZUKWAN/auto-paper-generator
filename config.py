"""配置管理模块"""
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """配置管理器"""
    
    def __init__(self, config_path="config.yaml"):
        self.config_path = config_path
        self._config = self._load_config()
    
    def _load_config(self):
        """加载YAML配置文件"""
        if not os.path.exists(self.config_path):
            # 返回默认配置
            return self._default_config()
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
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
                'default': 'ollama',
                'ollama': {
                    'base_url': 'http://localhost:11434',
                    'model': 'qwen3:8b'
                },
                'silicon': {
                    'api_key': os.getenv('SILICON_API_KEY', ''),
                    'model': 'Qwen/Qwen2.5-72B-Instruct'
                },
                'routing_rules': {
                    'local_nodes': ['literature_review', 'methodology'],
                    'online_nodes': ['introduction', 'conclusion']
                }
            },
            'literature': {
                'pool_path': 'data/literature_pool.txt',
                'external_search': {
                    'enabled': True,
                    'mode': 'searxng',
                    'searxng_url': 'http://localhost:8080',
                    'zhipu_api_key': os.getenv('ZHIPU_API_KEY', ''),
                    'trigger_threshold': 0.8
                }
            },
            'citation': {
                'target_per_sentence': 2,
                'min_per_paragraph': 3,
                'max_per_paragraph': 10,
                'similarity_threshold': 0.6,
                'diversity_weight': 0.3
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
    
    def get(self, key_path, default=None):
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
    
    def set(self, key_path, value):
        """设置配置值"""
        keys = key_path.split('.')
        config = self._config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def save(self):
        """保存配置到文件"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self._config, f, allow_unicode=True, default_flow_style=False)

# 全局配置实例
config = Config()
