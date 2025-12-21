"""引用管理器 - 高密度、不重复引用策略"""
import logging

logger = logging.getLogger(__name__)

class CitationManager:
    """引用管理器"""
    
    def __init__(self, literature_pool, retriever, config):
        """
        初始化引用管理器
        
        Args:
            literature_pool: 文献池
            retriever: 语义检索引擎
            config: 配置对象
        """
        self.pool = literature_pool
        self.retriever = retriever
        self.config = config
        
        # 引用跟踪
        self.citation_tracker = {}  # {lit_id: citation_number}
        self.next_citation_num = 1
        
        # 引用密度配置
        self.target_per_sentence = config.get('citation.target_per_sentence', 2)
        self.min_per_paragraph = config.get('citation.min_per_paragraph', 3)
        self.similarity_threshold = config.get('citation.similarity_threshold', 0.2)
        self.diversity_weight = config.get('citation.diversity_weight', 0.3)
        
        logger.info(f"引用管理器初始化: 每句目标{self.target_per_sentence}引用，每段最低{self.min_per_paragraph}引用")
    
    def generate_sentence_with_citations(self, sentence_skeleton, query):
        """
        为句子插入引用
        
        Args:
            sentence_skeleton: 句子骨架（不含引用）
            query: 检索查询词
            
        Returns:
            (带引用的句子, 使用的文献列表)
        """
        # 检索候选文献
        candidates = self.retriever.search(
            query, 
            top_k=10,
            threshold=self.similarity_threshold
        )
        
        if not candidates:
            logger.warning(f"查询 '{query}' 未找到相关文献")
            return f"{sentence_skeleton}。", []
        
        # 多样性选择
        selected = self._diverse_selection(candidates, self.target_per_sentence)
        
        # 生成引用序号
        citation_nums = []
        used_lits = []
        
        for lit_info in selected:
            lit = lit_info['literature']
            lit_id = lit['id']
            
            # 严格不重复引用检查
            if lit_id in self.citation_tracker:
                logger.debug(f"文献 {lit_id} 已引用过，跳过")
                continue
            
            # 分配新序号
            self.citation_tracker[lit_id] = self.next_citation_num
            citation_nums.append(self.next_citation_num)
            self.next_citation_num += 1
            
            # 标记为已使用
            lit['used'] = True
            used_lits.append(lit)
        
        # 插入引用
        if citation_nums:
            citation_str = ''.join([f'[{num}]' for num in citation_nums])
            sentence_with_citation = f"{sentence_skeleton}{citation_str}。"
            logger.debug(f"为句子添加了 {len(citation_nums)} 个引用: {citation_nums}")
        else:
            sentence_with_citation = f"{sentence_skeleton}。"
            logger.warning("未能为句子添加引用（文献池不足或已全部使用）")
        
        return sentence_with_citation, used_lits
    
    def _diverse_selection(self, candidates, target_num):
        """
        多样性选择策略
        
        优先选择不同作者、不同年份的文献
        """
        if len(candidates) <= target_num:
            return candidates
        
        selected = []
        used_authors = set()
        used_years = set()
        
        # 第一轮：优先多样性
        for candidate in candidates:
            lit = candidate['literature']
            author = lit['authors'].split(',')[0].strip()  # 第一作者
            year = lit['year']
            
            # 优先选择不同作者、不同年份
            if author not in used_authors or year not in used_years:
                selected.append(candidate)
                used_authors.add(author)
                used_years.add(year)
                
                if len(selected) >= target_num:
                    break
        
        # 第二轮：如果不足，补充相似度最高的
        if len(selected) < target_num:
            for candidate in candidates:
                if candidate not in selected:
                    selected.append(candidate)
                    if len(selected) >= target_num:
                        break
        
        return selected
    
    def generate_reference_list(self):
        """
        生成参考文献列表（按序号排序）
        
        Returns:
            参考文献列表字符串
        """
        if not self.citation_tracker:
            return ""
        
        # 按citation_number排序
        sorted_items = sorted(
            self.citation_tracker.items(), 
            key=lambda x: x[1]
        )
        
        reference_list = []
        for lit_id, citation_num in sorted_items:
            # 找到文献
            lit = next(l for l in self.pool if l['id'] == lit_id)
            
            # 使用完整题录
            reference = f"[{citation_num}] {lit['full_citation']}"
            reference_list.append(reference)
        
        logger.info(f"生成参考文献列表: {len(reference_list)} 条")
        return '\n'.join(reference_list)
    
    def get_statistics(self):
        """
        获取引用统计
        
        Returns:
            统计字典
        """
        total_citations = len(self.citation_tracker)
        unused_count = self.retriever.get_unused_count()
        
        return {
            'total_citations': total_citations,
            'unused_literature_count': unused_count,
            'literature_pool_size': len(self.pool)
        }
