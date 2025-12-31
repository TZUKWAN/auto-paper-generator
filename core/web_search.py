"""
DuckDuckGo 搜索模块 - 主要使用 duckduckgo_search 包
备用使用 Playwright 和 httpx
"""

import asyncio
from typing import List, Dict, Optional, Any
from playwright.async_api import async_playwright, Browser, Page
from bs4 import BeautifulSoup
import httpx
from loguru import logger

# 导入 ddgs 包（原 duckduckgo_search 已更名）
try:
    from ddgs import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False
    logger.warning("ddgs 包未安装，将使用备用方案")


class DuckDuckGoSearcher:
    """DuckDuckGo 搜索引擎封装"""
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        初始化搜索器
        
        Args:
            headless: 是否使用无头模式
            timeout: 页面加载超时时间(毫秒)
        """
        self.headless = headless
        self.timeout = timeout
        
    async def search(
        self, 
        query: str, 
        max_results: int = 10,
        region: str = "cn-zh",
        time: str = ""
    ) -> List[Dict[str, Any]]:
        """
        执行搜索并返回结果
        
        优先使用 duckduckgo_search 包，失败时使用备用方案
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
            region: 地区设置 (cn-zh, us-en, etc.)
            time: 时间筛选 (d, w, m, y)
        
        Returns:
            搜索结果列表，每项包含 title, url, snippet
        """
        # 方案1: 使用 duckduckgo_search 包 (最可靠)
        if DDGS_AVAILABLE:
            try:
                results = await self.search_ddgs(query, max_results, region)
                if results:
                    return results
            except Exception as e:
                logger.warning(f"DDGS搜索失败: {e}, 尝试备用方案")
        
        # 方案2: 使用httpx轻量级搜索
        try:
            results = await self.search_lite(query, max_results)
            if results:
                return results
        except Exception as e:
            logger.warning(f"轻量级搜索失败: {e}, 尝试Playwright搜索")
        
        # 方案3: 回退到Playwright搜索
        return await self.search_playwright(query, max_results, region, time)
    
    async def search_ddgs(self, query: str, max_results: int = 10, region: str = "cn-zh") -> List[Dict[str, Any]]:
        """
        使用 duckduckgo_search 包进行搜索
        """
        results = []
        
        # DDGS是同步API，在executor中运行
        def _sync_search():
            try:
                ddgs = DDGS()
                search_results = list(ddgs.text(
                    query, 
                    max_results=max_results
                ))
                return search_results
            except Exception as e:
                logger.warning(f"DDGS同步搜索异常: {e}")
                return []
        
        loop = asyncio.get_event_loop()
        search_results = await loop.run_in_executor(None, _sync_search)
        
        for r in search_results:
            results.append({
                "title": r.get("title", ""),
                "url": r.get("href", r.get("link", "")),
                "snippet": r.get("body", r.get("snippet", ""))
            })
        
        logger.info(f"DDGS搜索获取到 {len(results)} 条结果")
        return results
    
    async def search_lite(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        使用httpx轻量级搜索 (DuckDuckGo HTML版本)
        """
        results = []
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                # 使用DuckDuckGo HTML版本
                url = f"https://html.duckduckgo.com/html/?q={query}"
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, "html.parser")
                
                # 查找结果
                result_divs = soup.select(".result, .results_links_deep, .web-result")
                
                if not result_divs:
                    # 备用选择器
                    result_divs = soup.select("div.links_main")
                
                for div in result_divs[:max_results]:
                    try:
                        # 标题和链接
                        link = div.select_one("a.result__a, a.result__url, a")
                        title_elem = div.select_one(".result__title, .result__a, a")
                        snippet_elem = div.select_one(".result__snippet, .result__body")
                        
                        if link:
                            href = link.get("href", "")
                            title = title_elem.get_text(strip=True) if title_elem else ""
                            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                            
                            if href and title and "duckduckgo" not in href.lower():
                                results.append({
                                    "title": title,
                                    "url": href,
                                    "snippet": snippet
                                })
                    except Exception as e:
                        continue
                
                logger.info(f"轻量级搜索获取到 {len(results)} 条结果")
        except Exception as e:
            logger.warning(f"轻量级搜索请求失败: {e}")
        
        return results
    
    async def search_playwright(
        self, 
        query: str, 
        max_results: int = 10,
        region: str = "cn-zh",
        time: str = ""
    ) -> List[Dict[str, Any]]:
        """
        使用Playwright进行搜索（备用方案）
        """
        """
        执行搜索并返回结果
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
            region: 地区设置 (cn-zh, us-en, etc.)
            time: 时间筛选 (d, w, m, y)
        
        Returns:
            搜索结果列表，每项包含 title, url, snippet
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                locale="zh-CN",
                timezone_id="Asia/Shanghai"
            )
            page = await context.new_page()
            
            try:
                # 构建搜索URL
                search_url = f"https://duckduckgo.com/?q={query}&kl={region}"
                if time:
                    search_url += f"&df={time}"
                
                logger.info(f"搜索: {query}")
                await page.goto(search_url, wait_until="domcontentloaded", timeout=self.timeout)
                
                # 等待页面加载完成，尝试多个可能的选择器
                result_selectors = [
                    "[data-result]",  # 新版DuckDuckGo
                    "article[data-testid='result']",  # 另一种格式
                    ".result",  # 旧版格式
                    "article.result",  # 更旧版本
                    ".results--main article",  # 备用
                ]
                
                result_found = False
                for selector in result_selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=8000)
                        result_found = True
                        logger.info(f"使用选择器: {selector}")
                        break
                    except:
                        continue
                
                if not result_found:
                    # 如果没找到结果选择器，等待一下看页面是否加载
                    await asyncio.sleep(2)
                    logger.warning("未找到标准结果选择器，尝试通用提取")
                
                # 提取结果
                results = await self._extract_results(page)
                
                # 限制结果数量
                results = results[:max_results]
                
                logger.info(f"获取到 {len(results)} 条搜索结果")
                return results
                
            finally:
                await context.close()
                await browser.close()
    
    async def _extract_results(self, page: Page) -> List[Dict[str, Any]]:
        """从页面提取搜索结果"""
        results = []
        
        # 尝试多种选择器
        article_selectors = [
            "[data-result]",
            "article[data-testid='result']",
            ".result",
            "article.result",
            ".results--main article",
            "li[data-layout='organic']"
        ]
        
        articles = []
        for selector in article_selectors:
            articles = await page.query_selector_all(selector)
            if articles:
                logger.info(f"结果选择器 {selector} 找到 {len(articles)} 条")
                break
        
        if not articles:
            # 通用备用方案：提取所有带链接的区块
            logger.warning("使用备用链接提取方案")
            links = await page.query_selector_all("a[href^='http']")
            for link in links[:10]:
                try:
                    href = await link.get_attribute("href")
                    text = await link.inner_text()
                    if href and text and len(text) > 10 and "duckduckgo" not in href:
                        results.append({
                            "title": text[:100],
                            "url": href,
                            "snippet": ""
                        })
                except:
                    continue
            return results
        
        for article in articles:
            try:
                # 标题和链接 - 尝试多种选择器
                title_selectors = ["h2 a", "a[data-testid='result-title-a']", ".result__title a", "a"]
                title = ""
                url = ""
                for ts in title_selectors:
                    title_elem = await article.query_selector(ts)
                    if title_elem:
                        title = await title_elem.inner_text()
                        url = await title_elem.get_attribute("href")
                        if title and url:
                            break
                
                # 摘要
                snippet_selectors = [
                    "[data-result='snippet']",
                    ".result__snippet",
                    "span[data-testid='result-snippet']",
                    "p"
                ]
                snippet = ""
                for ss in snippet_selectors:
                    snippet_elem = await article.query_selector(ss)
                    if snippet_elem:
                        snippet = await snippet_elem.inner_text()
                        if snippet:
                            break
                
                if title and url:
                    results.append({
                        "title": title,
                        "url": url,
                        "snippet": snippet
                    })
            except Exception as e:
                logger.warning(f"解析单个结果失败: {e}")
                continue
        
        return results
    
    async def deep_crawl(
        self,
        url: str,
        extract_full_content: bool = True
    ) -> Dict[str, Any]:
        """
        深度抓取页面内容
        
        Args:
            url: 目标URL
            extract_full_content: 是否提取完整正文
        
        Returns:
            包含页面标题、正文、关键词等信息的字典
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                logger.info(f"深度抓取: {url}")
                await page.goto(url, wait_until="networkidle", timeout=self.timeout)
                
                # [*] 模拟滚动以触发懒加载
                try:
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
                    await page.wait_for_timeout(500)
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(1000)
                except Exception as e:
                    logger.warning(f"滚动页面失败: {e}")
                
                # 提取页面内容
                content = await self._extract_page_content(page, extract_full_content)
                content["url"] = url
                
                logger.info(f"抓取完成，内容长度: {len(content.get('content', ''))}")
                return content
                
            except Exception as e:
                logger.error(f"深度抓取失败 {url}: {e}")
                return {
                    "url": url,
                    "title": "",
                    "content": "",
                    "error": str(e)
                }
            finally:
                await context.close()
                await browser.close()
    
    async def _extract_page_content(
        self,
        page: Page,
        extract_full_content: bool = True
    ) -> Dict[str, Any]:
        """从页面提取结构化内容"""
        
        # 获取页面HTML
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        # 标题
        title = ""
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text().strip()
        
        # 元描述
        description = ""
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            description = meta_desc.get("content", "")
        
        # 提取正文内容 - 增强版
        content = ""
        if extract_full_content:
            # 1. 移除明确的无关元素
            for tags in soup(["script", "style", "nav", "footer", "aside", "header", "noscript", "iframe", "svg", "form", "button", "input"]):
                tags.decompose()
            
            # 2. 尝试常见的正文容器
            content_selectors = [
                "article", 
                'div[class*="content"]', 
                'div[class*="article"]',
                'div[class*="post"]',
                'div[id*="content"]',
                "main", 
                '[role="main"]'
            ]
            
            # 寻找文本最长的容器
            best_elem = None
            max_len = 0
            
            for selector in content_selectors:
                elems = soup.select(selector)
                for elem in elems:
                    text_len = len(elem.get_text(strip=True))
                    if text_len > max_len and text_len > 200:
                        max_len = text_len
                        best_elem = elem
            
            if best_elem:
                content = best_elem.get_text(separator="\n", strip=True)
            
            # 3. 如果没找到，回退到提取所有段落
            if not content or len(content) < 200:
                paragraphs = soup.find_all("p")
                # 过滤掉过短的段落
                valid_paras = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20]
                content = "\n".join(valid_paras)
                
            # 4. 如果还是太少，尝试提取body全文并简单清洗
            if not content or len(content) < 200:
                content = soup.get_text(separator="\n", strip=True)
        
        return {
            "title": title,
            "description": description,
            "content": content
        }
    
    async def search_and_crawl(
        self,
        query: str,
        max_results: int = 5,
        crawl_count: int = 3,
        deep_mode: bool = True
    ) -> List[Dict[str, Any]]:
        """
        搜索并深度抓取部分结果
        
        Args:
            query: 搜索查询
            max_results: 搜索结果最大数
            crawl_count: 深度抓取的结果数
            deep_mode: 是否启用深度抓取
        
        Returns:
            完整的结果列表，包含深度抓取的内容
        """
        # 先执行搜索
        search_results = await self.search(query, max_results=max_results)
        
        if not deep_mode:
            return search_results
        
        # 深度抓取前N个结果
        crawl_tasks = []
        for i, result in enumerate(search_results[:crawl_count]):
            crawl_tasks.append(self.deep_crawl(result["url"]))
        
        # 并发抓取
        crawled_results = await asyncio.gather(*crawl_tasks, return_exceptions=True)
        
        # 合并结果
        final_results = []
        for i, result in enumerate(search_results):
            final_result = {
                "title": result["title"],
                "url": result["url"],
                "snippet": result["snippet"]
            }
            
            # 如果已抓取，添加深度内容
            if i < len(crawled_results) and isinstance(crawled_results[i], dict):
                crawled = crawled_results[i]
                if "error" not in crawled:
                    final_result["full_title"] = crawled.get("title", "")
                    final_result["content"] = crawled.get("content", "")
                    final_result["description"] = crawled.get("description", "")
            
            final_results.append(final_result)
        
        return final_results


class WebSearchIntegration:
    """网络检索集成模块 - 替代原 ExternalSearchIntegration"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化检索集成
        
        Args:
            config: 配置字典或Config对象，包含:
                - literature.web_search.enabled: 是否启用
                - literature.web_search.mode: 搜索模式
                - literature.web_search.results_per_query: 每次查询结果数
                - literature.web_search.crawl_count: 深度抓取数量
        """
        self.config = config
        
        # 兼容两种配置格式: config.get('literature.web_search.xxx') 或 config['literature']['web_search']['xxx']
        if hasattr(config, 'get') and callable(getattr(config, 'get', None)):
            # 使用点号路径访问 (Config对象)
            try:
                self.enabled = config.get('literature.web_search.enabled', False)
                self.mode = config.get('literature.web_search.mode', 'standard')
                self.results_per_query = config.get('literature.web_search.results_per_query', 10)
                self.crawl_count = config.get('literature.web_search.crawl_count', 3)
                self.headless = config.get('literature.web_search.headless', True)
            except:
                # 回退到字典访问
                web_config = config.get('literature', {}).get('web_search', {}) if isinstance(config, dict) else {}
                self.enabled = web_config.get('enabled', False)
                self.mode = web_config.get('mode', 'standard')
                self.results_per_query = web_config.get('results_per_query', 10)
                self.crawl_count = web_config.get('crawl_count', 3)
                self.headless = web_config.get('headless', True)
        else:
            # 纯字典格式
            web_config = config.get('literature', {}).get('web_search', {}) if isinstance(config, dict) else {}
            self.enabled = web_config.get('enabled', False)
            self.mode = web_config.get('mode', 'standard')
            self.results_per_query = web_config.get('results_per_query', 10)
            self.crawl_count = web_config.get('crawl_count', 3)
            self.headless = web_config.get('headless', True)
        
        self.searcher = DuckDuckGoSearcher(headless=self.headless) if self.enabled else None
        
        logger.info(f"WebSearchIntegration 初始化: enabled={self.enabled}, mode={self.mode}")
    
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """
        执行搜索
        
        Args:
            query: 搜索查询
        
        Returns:
            搜索结果列表
        """
        if not self.enabled or not self.searcher:
            logger.warning("网络检索未启用或搜索器未初始化")
            return []
        
        deep_mode = self.mode == "deep"
        return await self.searcher.search_and_crawl(
            query=query,
            max_results=self.results_per_query,
            crawl_count=self.crawl_count,
            deep_mode=deep_mode
        )
    
    def format_results_as_context(self, results: List[Dict[str, Any]]) -> str:
        """
        将搜索结果格式化为上下文字符串
        
        Args:
            results: 搜索结果列表
        
        Returns:
            格式化的上下文文本
        """
        if not results:
            return ""
        
        context_lines = ["## 网络检索结果"]
        
        for i, result in enumerate(results, 1):
            context_lines.append(f"\n### {i}. {result.get('title', '无标题')}")
            context_lines.append(f"链接: {result.get('url', '')}")
            
            if result.get("content"):
                context_lines.append(f"内容摘要:\n{result['content'][:1000]}")
            elif result.get("snippet"):
                context_lines.append(f"摘要: {result['snippet']}")
        
        return "\n".join(context_lines)


# 同步包装器，用于兼容现有同步代码
def sync_search(query: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """同步版本的搜索函数"""
    integration = WebSearchIntegration(config)
    return asyncio.run(integration.search(query))
