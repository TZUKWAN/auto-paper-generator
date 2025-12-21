"""PDF参考文档管理器"""
import os
import logging
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

logger = logging.getLogger(__name__)

class PDFReferenceManager:
    """PDF参考文档管理器"""
    
    def __init__(self, pdf_folder_path, retriever_model=None):
        """
        初始化PDF管理器
        
        Args:
            pdf_folder_path: PDF文件夹路径
            retriever_model: 语义检索模型（可选，用于内容检索）
        """
        self.pdf_folder = pdf_folder_path
        self.retriever_model = retriever_model
        self.documents = []
        
        if not os.path.exists(pdf_folder_path):
            logger.warning(f"PDF文件夹不存在: {pdf_folder_path}")
            return
        
        self._load_pdfs()
    
    def _load_pdfs(self):
        """加载PDF文件夹中的所有PDF"""
        if not PyPDF2:
            logger.error("未安装PyPDF2，无法解析PDF。请运行：pip install PyPDF2")
            return
        
        logger.info(f"开始加载PDF文件: {self.pdf_folder}")
        
        pdf_count = 0
        for filename in os.listdir(self.pdf_folder):
            if filename.lower().endswith('.pdf'):
                filepath = os.path.join(self.pdf_folder, filename)
                content = self._extract_pdf_text(filepath)
                
                if content:
                    self.documents.append({
                        'filename': filename,
                        'filepath': filepath,
                        'content': content,
                        'snippets': self._split_into_snippets(content)
                    })
                    pdf_count += 1
        
        logger.info(f"PDF加载完成: {pdf_count} 个文件，共 {sum(len(d['snippets']) for d in self.documents)} 个片段")
    
    def _extract_pdf_text(self, filepath):
        """提取PDF文本内容"""
        try:
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
                
                logger.debug(f"成功提取PDF: {filepath} ({len(text)} 字符)")
                return text.strip()
        except Exception as e:
            logger.error(f"PDF解析失败 {filepath}: {e}")
            return ""
    
    def _split_into_snippets(self, content, snippet_length=500):
        """将内容分割为片段"""
        snippets = []
        
        # 按段落分割
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        current_snippet = ""
        for para in paragraphs:
            if len(current_snippet) + len(para) < snippet_length:
                current_snippet += para + "\n\n"
            else:
                if current_snippet:
                    snippets.append(current_snippet.strip())
                current_snippet = para + "\n\n"
        
        if current_snippet:
            snippets.append(current_snippet.strip())
        
        return snippets
    
    def search_relevant_snippets(self, query, top_k=3):
        """
        检索相关PDF内容片段
        
        Args:
            query: 查询文本
            top_k: 返回前k个片段
            
        Returns:
            相关片段列表
        """
        if not self.documents:
            return []
        
        # 简单实现：关键词匹配（可升级为语义检索）
        all_snippets = []
        for doc in self.documents:
            for snippet in doc['snippets']:
                # 计算关键词匹配度
                score = self._keyword_match_score(query, snippet)
                if score > 0:
                    all_snippets.append({
                        'content': snippet,
                        'source': doc['filename'],
                        'score': score
                    })
        
        # 按分数排序
        all_snippets.sort(key=lambda x: x['score'], reverse=True)
        
        # 返回topK
        results = all_snippets[:top_k]
        
        logger.debug(f"PDF检索: 查询='{query[:50]}...', 找到{len(results)}个相关片段")
        return [r['content'] for r in results]
    
    def _keyword_match_score(self, query, text):
        """简单的关键词匹配评分"""
        # 提取查询关键词（简化版）
        keywords = [w.strip() for w in query[:100].split() if len(w) > 2]
        
        score = 0
        for keyword in keywords:
            if keyword in text:
                score += 1
        
        return score
    
    def get_all_content_context(self, max_length=2000):
        """
        获取所有PDF内容的概要摘要（用于全局上下文）
        
        Args:
            max_length: 最大字符数
            
        Returns:
            合并的内容摘要
        """
        if not self.documents:
            return ""
        
        context = "【参考文档内容摘要】\n\n"
        
        for doc in self.documents:
            # 取每个文档的前500字符作为摘要
            excerpt = doc['content'][:500]
            context += f"文档: {doc['filename']}\n{excerpt}...\n\n"
            
            if len(context) > max_length:
                break
        
        return context[:max_length]
