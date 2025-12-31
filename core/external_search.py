"""SearXNG外部检索模块"""
import requests
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class SearXNGSearcher:
    """SearXNG搜索引擎封装"""
    
    def __init__(self, searxng_url="http://localhost:8080", results_per_query=30):
        """
        初始化SearXNG搜索器
        
        Args:
            searxng_url: SearXNG服务地址
            results_per_query: 每次查询返回的结果数（默认30条）
        """
        self.base_url = searxng_url.rstrip('/')
        self.results_per_query = results_per_query
        logger.info(f"SearXNG搜索器初始化: {self.base_url}, 每次{results_per_query}条结果")
    
    def search(self, query: str, num_results: int = None) -> List[Dict]:
        """
        执行搜索
        
        Args:
            query: 搜索查询词
            num_results: 返回结果数量（默认使用初始化时的设置）
            
        Returns:
            搜索结果列表，每项包含：title, url, content
        """
        num_results = num_results or self.results_per_query
        
        # 检查是否已标记为API受限，直接使用HTML回退模式
        if getattr(self, 'json_api_blocked', False):
            return self._search_html(query, num_results)

        try:
            # SearXNG API endpoint
            search_url = f"{self.base_url}/search"
            
            params = {
                'q': query,
                'format': 'json',
                'pageno': 1,
                'language': 'zh-CN'  # 中文搜索
            }
            
            # 添加User-Agent以避免403错误
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(
                search_url,
                params=params,
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            # 提取结果
            results = []
            for item in data.get('results', [])[:num_results]:
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'content': item.get('content', '') or item.get('snippet', ''),
                    'engine': item.get('engine', 'unknown')
                })
            
            logger.info(f"SearXNG搜索完成: '{query}' -> {len(results)}条结果")
            return results
            
        except Exception as e:
            # ⭐ 自动回退：如果JSON API被禁用(403)，尝试HTML解析
            if "403" in str(e):
                if not getattr(self, 'json_api_blocked', False):
                    logger.warning(f"SearXNG JSON API受限(403)，已自动切换至网页采集模式 (HTML Fallback)")
                    self.json_api_blocked = True
                return self._search_html(query, num_results)
            
            logger.error(f"SearXNG搜索失败: {str(e)}")
            return []

    def _search_html(self, query: str, num_results: int) -> List[Dict]:
        """HTML解析模式 (Fallback)"""
        try:
            import re
            
            search_url = f"{self.base_url}/search"
            params = {
                'q': query,
                'pageno': 1,
                'language': 'zh-CN'
            }
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(search_url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            html = response.text
            
            results = []
            
            # 简单正则提取 (针对SearXNG默认主题)
            # 寻找 <article ...> 块 (不完全依赖article标签，直接找URL和标题模式)
            # 典型结构: <h3><a href="...">Title</a></h3> ... <p class="content">Snippet</p>
            
            # 1. 提取所有结果块 (rough split)
            articles = re.split(r'<article class="result', html)
            
            for art in articles[1:]: # 跳过第一个（头部）
                if len(results) >= num_results:
                    break
                
                # 提取URL和标题
                link_match = re.search(r'href="([^"]+)"[^>]*>([^<]+)</a></h3>', art)
                if not link_match:
                    continue
                
                url = link_match.group(1)
                title = link_match.group(2)
                
                # 提取摘要 (content)
                content_match = re.search(r'class="content">([^<]+)<', art)
                content = content_match.group(1) if content_match else ""
                
                # 清理HTML实体
                title = title.replace('<b>', '').replace('</b>', '').replace('&amp;', '&')
                content = content.replace('<b>', '').replace('</b>', '').replace('&amp;', '&')
                
                results.append({
                    'title': title.strip(),
                    'url': url.strip(),
                    'content': content.strip(),
                    'engine': 'html_fallback'
                })
            
            logger.info(f"SearXNG HTML fallback搜索完成: {len(results)}条结果")
            return results
            
        except Exception as e:
            logger.error(f"SearXNG HTML fallback失败: {e}")
            return []
    
    def search_multiple_queries(self, queries: List[str], num_results_per_query: int = None) -> List[Dict]:
        """
        批量搜索多个查询
        
        Args:
            queries: 查询词列表
            num_results_per_query: 每个查询返回的结果数
            
        Returns:
            合并去重后的搜索结果
        """
        all_results = []
        seen_urls = set()
        
        for query in queries:
            results = self.search(query, num_results_per_query)
            
            # 去重
            for result in results:
                url = result['url']
                if url not in seen_urls:
                    seen_urls.add(url)
                    all_results.append(result)
        
        logger.info(f"批量搜索完成: {len(queries)}个查询 -> {len(all_results)}条去重结果")
        return all_results
    
    def format_results_for_llm(self, results: List[Dict], max_length: int = 5000) -> str:
        """
        格式化搜索结果为LLM可读的文本
        
        Args:
            results: 搜索结果列表
            max_length: 最大字符数限制
            
        Returns:
            格式化后的文本
        """
        if not results:
            return ""
        
        formatted = "【联网检索结果】\n\n"
        
        for i, result in enumerate(results, 1):
            title = result.get('title', '无标题')
            content = result.get('content', '无内容')[:200]  # 每条限制200字符
            url = result.get('url', '')
            
            formatted += f"{i}. {title}\n"
            formatted += f"   {content}...\n"
            formatted += f"   来源: {url}\n\n"
            
            # 检查长度限制
            if len(formatted) > max_length:
                formatted = formatted[:max_length] + "\n...(结果已截断)"
                break
        
        return formatted


class ExternalSearchIntegration:
    """外部检索集成（支持SearXNG和智谱AI）"""
    
    def __init__(self, config):
        """
        初始化外部检索
        
        Args:
            config: 配置对象
        """
        self.enabled = config.get('literature.external_search.enabled', False)
        self.mode = config.get('literature.external_search.mode', 'searxng')
        
        if not self.enabled:
            logger.info("外部检索未启用")
            return
        
        if self.mode == 'searxng':
            searxng_url = config.get('literature.external_search.searxng_url')
            self.searcher = SearXNGSearcher(searxng_url, results_per_query=30)
            logger.info("外部检索模式: SearXNG")
        elif self.mode == 'zhipu':
            # TODO: 实现智谱AI搜索
            logger.warning("智谱AI搜索暂未实现")
            self.searcher = None
        else:
            logger.warning(f"未知的检索模式: {self.mode}")
            self.searcher = None
    
    def search_for_context(self, topic: str, num_results: int = 30) -> str:
        """
        为AI提供联网检索上下文
        
        Args:
            topic: 主题或查询词
            num_results: 结果数量
            
        Returns:
            格式化的搜索结果文本
        """
        if not self.enabled or not self.searcher:
            return ""
        
        try:
            results = self.searcher.search(topic, num_results)
            formatted = self.searcher.format_results_for_llm(results)
            return formatted
        except Exception as e:
            logger.error(f"联网检索失败: {str(e)}")
            return ""
