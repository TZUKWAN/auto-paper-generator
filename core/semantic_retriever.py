"""语义检索引擎 - 基于FAISS的文献检索"""
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import logging

logger = logging.getLogger(__name__)

class SemanticRetriever:
    """语义检索引擎"""
    
    def __init__(self, literature_pool, model_name='paraphrase-multilingual-MiniLM-L12-v2'):
        """
        初始化检索引擎
        
        Args:
            literature_pool: 文献列表
            model_name: Sentence-Transformers模型名称
        """
        self.pool = literature_pool
        self.model_name = model_name
        self.index = None
        self.embeddings = None
        
        if not self.pool:
            logger.warning("文献池为空，跳过语义模型加载和索引构建")
            return

        logger.info(f"加载语义模型: {model_name}")
        self.model = SentenceTransformer(model_name)
        
        self._build_index()
    
    def _build_index(self):
        """构建FAISS索引"""
        if not self.pool:
            return
            
        logger.info(f"开始构建FAISS索引，文献数量: {len(self.pool)}")
        
        # 组合标题和摘要作为检索文本
        texts = [f"{lit['title']} {lit['abstract']}" for lit in self.pool]
        
        # 生成嵌入
        logger.info("生成文献嵌入向量...")
        self.embeddings = self.model.encode(texts, show_progress_bar=True)
        
        # 归一化（用于余弦相似度）
        faiss.normalize_L2(self.embeddings)
        
        # 构建FAISS索引
        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # 内积相似度（归一化后等于余弦相似度）
        self.index.add(self.embeddings)
        
        logger.info(f"FAISS索引构建完成，维度: {dimension}")
    
    def search(self, query, top_k=5, threshold=0.2):
        """
        语义检索
        
        Args:
            query: 查询文本
            top_k: 返回前k个结果
            threshold: 相似度阈值（0-1）
            
        Returns:
            结果列表，每个结果包含 literature, similarity, index
        """
        if not self.index or not self.pool:
            return []

        # 生成查询嵌入
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # 检索
        distances, indices = self.index.search(query_embedding, top_k)
        
        # 过滤：未使用 + 超过阈值
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if dist >= threshold and not self.pool[idx]['used']:
                results.append({
                    'literature': self.pool[idx],
                    'similarity': float(dist),
                    'index': int(idx)
                })
        
        logger.debug(f"检索到 {len(results)} 条相关文献（阈值: {threshold}）")
        return results
    
    def get_unused_count(self):
        """获取未使用文献数量"""
        return sum(1 for lit in self.pool if not lit['used'])
