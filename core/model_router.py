"""大模型路由器 - 多提供商在线API支持"""
import requests
import logging
import time
import re
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class ProviderConfig:
    """API提供商配置"""
    
    def __init__(self, name: str, base_url: str, api_key: str, models: List[str] = None, **kwargs):
        self.name = name
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.models = models or []
        # 默认参数
        self.max_tokens = kwargs.get('max_tokens', 16000)
        self.temperature = kwargs.get('temperature', 0.7)
        self.top_p = kwargs.get('top_p', 0.7)
        self.top_k = kwargs.get('top_k', 50)
        self.min_p = kwargs.get('min_p', 0.05)
        self.frequency_penalty = kwargs.get('frequency_penalty', 0.5)
        self.enable_thinking = kwargs.get('enable_thinking', False)
        self.thinking_budget = kwargs.get('thinking_budget', 4096)
        self.rate_limit_seconds = kwargs.get('rate_limit_seconds', 0)


class ModelRouter:
    """大模型路由器 - 支持多个在线API提供商"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化路由器
        
        Args:
            config: 配置字典，包含 providers 列表
        """
        self.config = config
        self.providers: Dict[str, ProviderConfig] = {}
        self.active_provider_name = config.get('model_routing.default_provider', 'online')
        self._last_request_time: Dict[str, float] = {}
        
        # 初始化所有提供商
        self._init_providers(config)
        
        logger.info(f"模型路由器初始化完成，默认提供商: {self.active_provider_name}")
        logger.info(f"已加载提供商: {list(self.providers.keys())}")
    
    def _init_providers(self, config: Dict[str, Any]):
        """从配置初始化提供商"""
        providers_config = config.get('model_routing.providers', {})
        
        # 兼容旧配置格式 (online 单一配置)
        if 'online' in providers_config and not any(k != 'online' for k in providers_config.keys()):
            online_cfg = providers_config['online']
            provider = ProviderConfig(
                name='online',
                base_url=online_cfg.get('base_url', 'https://api.openai.com/v1'),
                api_key=online_cfg.get('api_key', ''),
                models=online_cfg.get('models', []),
                max_tokens=online_cfg.get('max_tokens', 16000),
                temperature=online_cfg.get('temperature', 0.7),
                top_p=online_cfg.get('top_p', 0.7),
                top_k=online_cfg.get('top_k', 50),
                min_p=online_cfg.get('min_p', 0.05),
                frequency_penalty=online_cfg.get('frequency_penalty', 0.5),
                enable_thinking=online_cfg.get('enable_thinking', False),
                thinking_budget=online_cfg.get('thinking_budget', 4096),
                rate_limit_seconds=online_cfg.get('rate_limit_seconds', 0)
            )
            self.providers['online'] = provider
            return
        
        # 新格式：多提供商
        for name, provider_cfg in providers_config.items():
            if not provider_cfg.get('enabled', True):
                continue
            
            provider = ProviderConfig(
                name=name,
                base_url=provider_cfg.get('base_url', ''),
                api_key=provider_cfg.get('api_key', ''),
                models=provider_cfg.get('models', []),
                max_tokens=provider_cfg.get('max_tokens', 16000),
                temperature=provider_cfg.get('temperature', 0.7),
                top_p=provider_cfg.get('top_p', 0.7),
                top_k=provider_cfg.get('top_k', 50),
                min_p=provider_cfg.get('min_p', 0.05),
                frequency_penalty=provider_cfg.get('frequency_penalty', 0.5),
                enable_thinking=provider_cfg.get('enable_thinking', False),
                thinking_budget=provider_cfg.get('thinking_budget', 4096),
                rate_limit_seconds=provider_cfg.get('rate_limit_seconds', 0)
            )
            self.providers[name] = provider
    
    def get_active_provider(self) -> ProviderConfig:
        """获取当前激活的提供商"""
        if self.active_provider_name not in self.providers:
            # 如果默认提供商不存在，使用第一个可用的
            available = list(self.providers.keys())
            if not available:
                raise ValueError("没有可用的API提供商")
            self.active_provider_name = available[0]
            logger.warning(f"默认提供商 {self.active_provider_name} 不可用，切换到 {self.active_provider_name}")
        
        return self.providers[self.active_provider_name]
    
    def set_active_provider(self, name: str):
        """切换到指定提供商"""
        if name not in self.providers:
            available = ", ".join(self.providers.keys())
            raise ValueError(f"提供商 '{name}' 不存在。可用: {available}")
        self.active_provider_name = name
        logger.info(f"切换到提供商: {name}")
    
    def generate_for_stage(
        self,
        prompt: str,
        stage: str,
        context: str = "",
        max_tokens: int = None
    ) -> str:
        """
        根据生成阶段选择不同的模型配置
        
        Args:
            prompt: 提示词
            stage: 生成阶段 (outline, content, review, expansion)
            context: 上下文
            max_tokens: 最大token数
            
        Returns:
            生成的文本
        """
        stage_models = self.config.get('stage_models', {})
        
        # 检查分阶段模型是否启用
        if not stage_models.get('enabled', False):
            return self.generate(prompt, context, max_tokens=max_tokens)
        
        # 获取阶段配置
        stage_config = stage_models.get(stage, {})
        if not stage_config:
            logger.warning(f"阶段 '{stage}' 没有配置，使用默认提供商")
            return self.generate(prompt, context, max_tokens=max_tokens)
        
        # 获取阶段指定的提供商
        provider_name = stage_config.get('provider', self.active_provider_name)
        if provider_name not in self.providers:
            logger.warning(f"阶段 '{stage}' 指定的提供商 '{provider_name}' 不存在，使用默认提供商")
            return self.generate(prompt, context, max_tokens=max_tokens)
        
        provider = self.providers[provider_name]
        
        # 临时覆盖提供商配置
        original_config = {
            'temperature': provider.temperature,
            'enable_thinking': provider.enable_thinking,
            'thinking_budget': provider.thinking_budget,
            'models': provider.models.copy() if provider.models else []
        }
        
        try:
            # 应用阶段配置
            if 'temperature' in stage_config:
                provider.temperature = stage_config['temperature']
            if 'enable_thinking' in stage_config:
                provider.enable_thinking = stage_config['enable_thinking']
            if 'thinking_budget' in stage_config:
                provider.thinking_budget = stage_config['thinking_budget']
            if 'model' in stage_config:
                provider.models = [stage_config['model']]
            
            logger.info(f"[分阶段模型] {stage}: 使用 {provider_name}/{provider.models[0] if provider.models else '默认'}")
            
            return self._call_provider(provider, prompt, context, max_tokens)
        finally:
            # 恢复原始配置
            provider.temperature = original_config['temperature']
            provider.enable_thinking = original_config['enable_thinking']
            provider.thinking_budget = original_config['thinking_budget']
            provider.models = original_config['models']
    
    def generate(
        self, 
        prompt: str, 
        context: str = "", 
        node_id: str = None, 
        max_tokens: int = None,
        provider_name: str = None
    ) -> str:
        """
        生成文本
        
        Args:
            prompt: 提示词
            context: 上下文
            node_id: 节点ID（未来可用于路由决策）
            max_tokens: 最大token数
            provider_name: 指定使用的提供商
        
        Returns:
            生成的文本
        """
        # 确定使用的提供商
        if provider_name and provider_name in self.providers:
            provider = self.providers[provider_name]
            logger.info(f"使用指定提供商: {provider_name}")
        else:
            provider = self.get_active_provider()
        
        return self._call_provider(provider, prompt, context, max_tokens)
    
    def _call_provider(
        self, 
        provider: ProviderConfig, 
        prompt: str, 
        context: str = "", 
        max_tokens: int = None
    ) -> str:
        """调用指定的提供商API"""
        
        # 频率限制
        if provider.rate_limit_seconds > 0:
            current_time = time.time()
            last_time = self._last_request_time.get(provider.name, 0)
            elapsed = current_time - last_time
            if elapsed < provider.rate_limit_seconds:
                wait_time = provider.rate_limit_seconds - elapsed
                logger.info(f"[{provider.name}] 触发频率限制，等待 {wait_time:.2f} 秒...")
                time.sleep(wait_time)
        
        self._last_request_time[provider.name] = time.time()
        
        # 构建消息
        messages = []

        # 添加强制中文输出的system prompt
        chinese_constraint = "你必须使用简体中文输出所有内容。请勿使用任何其他语言（如英语、日语等）编写正文。所有专业术语可以保留英文原文并在括号内添加中文解释。"

        if context:
            # 将中文约束合并到context中
            combined_context = f"{chinese_constraint}\n\n{context}"
            messages.append({"role": "system", "content": combined_context})
        else:
            messages.append({"role": "system", "content": chinese_constraint})

        messages.append({"role": "user", "content": prompt})
        
        # 构建端点URL（智能适配不同提供商）
        base_url = provider.base_url.rstrip('/')
        if not base_url.endswith('/chat/completions'):
            # 检查是否已有版本号（如 /v1, /v4 等）
            import re
            if re.search(r'/v\d+$', base_url):
                # 已有版本路径，直接添加 /chat/completions
                base_url = f"{base_url}/chat/completions"
            else:
                # 没有版本路径，使用标准 /v1/chat/completions
                base_url = f"{base_url}/v1/chat/completions"
        
        # 构建请求payload
        payload = {
            "model": provider.models[0] if provider.models else "gpt-3.5-turbo",
            "messages": messages,
            "max_tokens": max_tokens or provider.max_tokens,
            "temperature": provider.temperature,
            "top_p": provider.top_p,
            "frequency_penalty": provider.frequency_penalty,
            "n": 1,
            "stream": False  # 显式关闭流式输出，确保获取完整内容
        }
        
        # 添加可选参数（如果提供商支持）
        if provider.top_k:
            payload["top_k"] = provider.top_k
        if provider.min_p:
            payload["min_p"] = provider.min_p
        
        # DeepSeek 思维链
        if "deepseek" in provider.name.lower() or any("deepseek" in m.lower() for m in provider.models):
            payload["enable_thinking"] = provider.enable_thinking
            payload["thinking_budget"] = provider.thinking_budget
        
        # 智谱AI (ZhipuAI / GLM) 思维链模式
        is_zhipu = (
            "zhipu" in provider.name.lower() or 
            "glm" in provider.name.lower() or
            any("glm" in m.lower() for m in provider.models) or
            "zhipu" in provider.base_url.lower() or
            "bigmodel.cn" in provider.base_url.lower()
        )
        if is_zhipu and provider.enable_thinking:
            # 使用智谱官方thinking参数格式
            payload["thinking"] = {"type": "enabled"}
            # 智谱深度思考模式需要更大的max_tokens
            if payload.get("max_tokens", 0) < 65536:
                payload["max_tokens"] = 65536
            # 智谱思考模式建议temperature=1.0
            payload["temperature"] = 1.0
            # 移除智谱不支持的参数
            payload.pop("top_k", None)
            payload.pop("min_p", None)
            payload.pop("frequency_penalty", None)
        
        # 调用API（带重试）
        max_retries = 3
        retry_delay = 30
        
        for attempt in range(max_retries):
            try:
                headers = {
                    "Authorization": f"Bearer {provider.api_key}",
                    "Content-Type": "application/json"
                }
                
                response = requests.post(
                    base_url,
                    headers=headers,
                    json=payload,
                    timeout=1200
                )
                response.raise_for_status()
                data = response.json()

                # 检查响应是否被截断
                choice = data["choices"][0]
                finish_reason = choice.get("finish_reason", "unknown")

                result = choice["message"]["content"]

                # 过滤thinking标签
                result = re.sub(r'<thinking>.*?</thinking>', '', result, flags=re.DOTALL).strip()

                # 检查是否因长度限制被截断
                if finish_reason == "length":
                    logger.warning(f"[{provider.name}] 警告: 响应因max_tokens限制被截断! 当前max_tokens={payload.get('max_tokens', provider.max_tokens)}")
                    logger.warning(f"[{provider.name}] 建议增加max_tokens配置以获得完整响应")

                logger.debug(f"[{provider.name}] 生成完成，长度: {len(result)} 字符, finish_reason: {finish_reason}")
                return result
                
            except (requests.exceptions.ConnectionError, 
                    requests.exceptions.Timeout,
                    requests.exceptions.ChunkedEncodingError) as e:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    logger.warning(f"[{provider.name}] 连接失败 (尝试 {attempt+1}/{max_retries})，{wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"[{provider.name}] 连接失败，已达最大重试次数")
                    raise
            except requests.exceptions.HTTPError as e:
                # 特别处理429频率限制错误
                if e.response.status_code == 429:
                    if attempt < max_retries - 1:
                        # 尝试从响应头获取重试等待时间
                        retry_after = e.response.headers.get('Retry-After', None)
                        if retry_after:
                            wait_time = int(retry_after)
                        else:
                            wait_time = 60 * (2 ** attempt)  # 60秒起步，指数增长
                        logger.warning(f"[{provider.name}] 触发频率限制(429) (尝试 {attempt+1}/{max_retries})，等待 {wait_time}秒后重试...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"[{provider.name}] 频率限制(429)，已达最大重试次数。请稍后再试或检查API配额。")
                        raise
                else:
                    logger.error(f"[{provider.name}] HTTP错误: {e.response.status_code}")
                    raise
            except Exception as e:
                logger.error(f"[{provider.name}] API调用失败: {str(e)}")
                raise
    
    def update_provider_config(self, provider_name: str, **kwargs):
        """动态更新提供商配置"""
        if provider_name not in self.providers:
            raise ValueError(f"提供商 '{provider_name}' 不存在")
        
        provider = self.providers[provider_name]
        for key, value in kwargs.items():
            if hasattr(provider, key):
                setattr(provider, key, value)
        
        logger.info(f"[{provider_name}] 配置已更新: {kwargs}")
    
    def list_providers(self) -> List[Dict[str, Any]]:
        """列出所有提供商信息"""
        return [
            {
                "name": p.name,
                "base_url": p.base_url,
                "models": p.models,
                "active": p.name == self.active_provider_name
            }
            for p in self.providers.values()
        ]
