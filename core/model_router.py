"""大模型路由器 - LM Studio本地和在线API"""
import requests
import logging
import time
import re

logger = logging.getLogger(__name__)

class ModelRouter:
    """大模型路由器"""
    
    def __init__(self, config):
        self.config = config
        self.default_mode = config.get('model_routing.default', 'lmstudio')
        
        # 初始化客户端
        self.lmstudio_client = LMStudioClient(
            base_url=config.get('model_routing.lmstudio.base_url'),
            model=config.get('model_routing.lmstudio.model')
        )
        
        self.silicon_client = SiliconFlowClient(
            api_key=config.get('model_routing.silicon.api_key'),
            model=config.get('model_routing.silicon.model'),
            config=config  # 传递完整配置
        )
        
        # 路由规则
        self.local_nodes = config.get('model_routing.routing_rules.local_nodes', [])
        self.online_nodes = config.get('model_routing.routing_rules.online_nodes', [])
        
        logger.info(f"模型路由器初始化完成，默认模式: {self.default_mode}")
    
    def generate(self, prompt, context="", node_id=None, max_tokens=32768):
        """
        生成文本
        
        Args:
            prompt: 提示词
            context: 上下文
            node_id: 节点ID（用于路由决策）
            max_tokens: 最大token数
            
        Returns:
            生成的文本
        """
        # 决定使用哪个模型
        if self._should_use_local(node_id):
            logger.info(f"节点 {node_id} 使用LM Studio本地模型")
            return self.lmstudio_client.generate(prompt, context, max_tokens)
        else:
            logger.info(f"节点 {node_id} 使用在线模型")
            return self.silicon_client.generate(prompt, context, max_tokens)
    
    def _should_use_local(self, node_id):
        """
        判断是否使用本地模型
        
        策略：
        - 如果node_id在local_nodes中 -> 本地LM Studio
        - 如果node_id在online_nodes中 -> 在线
        - 否则使用默认模式
        """
        if node_id in self.local_nodes:
            return True
        elif node_id in self.online_nodes:
            return False
        else:
            return self.default_mode == 'lmstudio'


class LMStudioClient:
    """LM Studio本地模型客户端（OpenAI兼容API）"""
    
    def __init__(self, base_url="http://localhost:1234/v1", model="local-model"):
        self.base_url = base_url
        self.model = model
        logger.info(f"LM Studio客户端初始化: {base_url}, 模型: {model}")
    
    def generate(self, prompt, context="", max_tokens=32768):
        """调用LM Studio生成文本"""
        messages = []
        
        # 添加系统消息（如果有上下文）
        if context:
            messages.append({"role": "system", "content": context})
        
        # 添加用户消息
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.7,
                    "stream": False
                },
                timeout=1200
            )
            
            response.raise_for_status()
            data = response.json()
            
            result = data['choices'][0]['message']['content']
            
            # 过滤 <think> 标签内容
            result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL).strip()
            
            logger.debug(f"LM Studio生成完成，长度: {len(result)}")
            
            return result
            
        except Exception as e:
            logger.error(f"LM Studio调用失败: {str(e)}")
            raise


class SiliconFlowClient:
    """硅基流动在线API客户端（支持完整参数配置）"""
    
    _last_request_time = 0  # 类变量记录上次请求时间
    
    def __init__(self, api_key, model="deepseek-ai/DeepSeek-R1-0528-Qwen3-8B", config=None):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.siliconflow.cn/v1/chat/completions"
        
        # 加载配置参数
        self.config = config or {}
        self.max_tokens = self.config.get('model_routing.silicon.max_tokens', 4096)
        self.temperature = self.config.get('model_routing.silicon.temperature', 0.7)
        self.top_p = self.config.get('model_routing.silicon.top_p', 0.7)
        self.top_k = self.config.get('model_routing.silicon.top_k', 50)
        self.min_p = self.config.get('model_routing.silicon.min_p', 0.05)
        self.frequency_penalty = self.config.get('model_routing.silicon.frequency_penalty', 0.5)
        self.n = self.config.get('model_routing.silicon.n', 1)
        self.enable_thinking = self.config.get('model_routing.silicon.enable_thinking', True)
        self.thinking_budget = self.config.get('model_routing.silicon.thinking_budget', 4096)
        
        logger.info(f"硅基流动客户端初始化，模型: {model}")
    
    def generate(self, prompt, context="", max_tokens=None):
        """调用硅基流动API（包含频率限制）"""
        # 频率限制：不仅是同一个实例，甚至是同一个类（如果多个线程），这里用类变量简单控制
        # 如果是多进程则无法防住，但在web_api.py里是threading，所以类变量有效
        current_time = time.time()
        elapsed = current_time - SiliconFlowClient._last_request_time
        if elapsed < 10:
            wait_time = 10 - elapsed
            logger.info(f"触发频率限制，等待 {wait_time:.2f} 秒...")
            time.sleep(wait_time)
        
        SiliconFlowClient._last_request_time = time.time()

        messages = []
        
        if context:
            messages.append({"role": "system", "content": context})
        
        messages.append({"role": "user", "content": prompt})
        
        # 构建请求payload
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "min_p": self.min_p,
            "frequency_penalty": self.frequency_penalty,
            "n": self.n
        }
        
        # DeepSeek思维链参数（仅适用于支持的模型）
        if "DeepSeek" in self.model or "deepseek" in self.model:
            payload["enable_thinking"] = self.enable_thinking
            payload["thinking_budget"] = self.thinking_budget
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=1200
            )
            
            response.raise_for_status()
            data = response.json()
            
            result = data["choices"][0]["message"]["content"]
            
            # 过滤 <think> 标签内容
            result = re.sub(r'<think>.*?</think>', '', result, flags=re.DOTALL).strip()
            
            logger.debug(f"硅基流动生成完成，长度: {len(result)}")
            
            return result
            
        except Exception as e:
            logger.error(f"硅基流动调用失败: {str(e)}")
            raise
    
    def update_config(self, **kwargs):
        """动态更新配置参数（供前端调用）"""
        if 'max_tokens' in kwargs:
            self.max_tokens = kwargs['max_tokens']
        if 'temperature' in kwargs:
            self.temperature = kwargs['temperature']
        if 'top_p' in kwargs:
            self.top_p = kwargs['top_p']
        if 'top_k' in kwargs:
            self.top_k = kwargs['top_k']
        if 'min_p' in kwargs:
            self.min_p = kwargs['min_p']
        if 'frequency_penalty' in kwargs:
            self.frequency_penalty = kwargs['frequency_penalty']
        if 'enable_thinking' in kwargs:
            self.enable_thinking = kwargs['enable_thinking']
        if 'thinking_budget' in kwargs:
            self.thinking_budget = kwargs['thinking_budget']
        
        logger.info(f"配置已更新: {kwargs}")
