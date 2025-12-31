"""引用管理器 - 高密度、不重复引用策略"""
import logging

logger = logging.getLogger(__name__)

class CitationManager:
    """引用管理器"""
    
    def __init__(self, literature_pool, retriever, config, model_router=None):
        """
        初始化引用管理器
        
        Args:
            literature_pool: 文献池
            retriever: 语义检索引擎
            config: 配置对象
            model_router: LLM路由器（可选，用于智能文献筛选）
        """
        self.model_router = model_router  # LLM路由器
        self.pool = literature_pool
        self.retriever = retriever
        self.config = config
        
        # 引用跟踪
        self.citation_tracker = {}  # {lit_id: citation_number}
        self.next_citation_num = 1
        
        # 基础配置 - 阈值降至0.05以确保模糊匹配成功
        self.similarity_threshold = config.get('citation.similarity_threshold', 0.05)
        self.diversity_weight = config.get('citation.diversity_weight', 0.3)
        self.max_total_citations = config.get('citation.max_total', 25)
        
        # [*] 章节配额系统
        # 配额分配: 引言10%, 章节1-3各30%, 结论0%
        import math
        total = self.max_total_citations
        
        intro_quota = math.ceil(total * 0.10)  # 引言: 10%
        chapter_quota = math.ceil(total * 0.30)  # 每章节: 30%
        
        # 如果总和超出，从章节随机扣除
        total_allocated = intro_quota + chapter_quota * 3
        if total_allocated > total:
            excess = total_allocated - total
            chapter_quota = chapter_quota - (excess + 2) // 3  # 均匀扣除
        
        self.chapter_quotas = {
            'introduction': intro_quota,
            'chapter_1': chapter_quota,
            'chapter_2': chapter_quota,
            'chapter_3': chapter_quota,
            'conclusion': 0
        }
        
        # 章节使用计数
        self.chapter_used = {k: 0 for k in self.chapter_quotas}
        
        # 当前章节和二级标题跟踪
        self.current_chapter = 'introduction'
        self.current_subsection = 0
        self.subsection_used = 0  # 当前二级标题已使用的引用数
        
        # 每个二级标题最多使用章节配额的33%
        self.subsection_max_ratio = 0.34  # 略大于33%以处理取整
        
        logger.info(f"引用配额系统: 总计{total}条, 引言{intro_quota}, 章节1-3各{chapter_quota}, 结论0")
    
    def set_current_section(self, section_type, chapter_idx=0, subsection_idx=0):
        """
        设置当前正在生成的章节位置
        
        Args:
            section_type: 'introduction', 'chapter', 'conclusion'
            chapter_idx: 章节索引 (0-2)
            subsection_idx: 二级标题索引
        """
        if section_type == 'introduction':
            self.current_chapter = 'introduction'
        elif section_type == 'chapter':
            self.current_chapter = f'chapter_{chapter_idx + 1}'
        elif section_type == 'conclusion':
            self.current_chapter = 'conclusion'
        
        # 如果切换到新的二级标题，重置计数
        if subsection_idx != self.current_subsection:
            self.current_subsection = subsection_idx
            self.subsection_used = 0
        
        logger.debug(f"切换到章节: {self.current_chapter}, 二级标题: {subsection_idx}")
    
    def _llm_select_best_citation(self, sentence, candidates):
        """
        使用LLM从候选文献中选择最相关的一篇
        
        Args:
            sentence: 需要引用的句子
            candidates: 候选文献列表
            
        Returns:
            选中的文献信息 dict，如果失败则返回 None
        """
        if not self.model_router:
            logger.debug("LLM路由器未配置，使用语义相似度选择")
            return candidates[0] if candidates else None
        
        if len(candidates) <= 1:
            return candidates[0] if candidates else None
        
        # 构造候选文献描述
        candidates_desc = []
        for i, cand in enumerate(candidates, 1):
            lit = cand['literature']
            abstract_preview = lit.get('abstract', '')[:150]
            desc = f"{i}. 标题: {lit['title']}\n   摘要: {abstract_preview}..."
            candidates_desc.append(desc)
        
        prompt = f"""你是一个学术论文引用专家。请从以下候选参考文献中选择与给定句子最相关的一篇。

句子: {sentence}

候选文献:
{chr(10).join(candidates_desc)}

请只返回最相关文献的编号（如 "1"），不要返回其他任何内容。"""

        try:
            response = self.model_router.generate(prompt, max_tokens=10)
            # 解析数字
            import re
            match = re.search(r'(\d+)', response.strip())
            if match:
                selected_idx = int(match.group(1)) - 1
                if 0 <= selected_idx < len(candidates):
                    selected_lit = candidates[selected_idx]['literature']
                    logger.info(f"LLM选择了第 {selected_idx + 1} 篇文献: {selected_lit['title'][:40]}...")
                    return candidates[selected_idx]
            
            logger.warning(f"LLM返回无效: '{response}', 使用相似度最高的候选")
            return candidates[0]
        except Exception as e:
            logger.error(f"LLM筛选失败: {e}, 使用相似度最高的候选")
            return candidates[0]
    
    def generate_sentence_with_citations(self, sentence_skeleton, query):
        """
        为句子插入引用
        
        Args:
            sentence_skeleton: 句子骨架（不含引用）
            query: 检索查询词
            
        Returns:
            (带引用的句子, 使用的文献列表)
        """
        import math
        
        # [*] 基于章节配额的引用分配
        chapter = self.current_chapter
        chapter_quota = self.chapter_quotas.get(chapter, 0)
        chapter_used = self.chapter_used.get(chapter, 0)
        chapter_remaining = chapter_quota - chapter_used
        
        # 计算二级标题配额（章节配额的33%）
        subsection_max = math.ceil(chapter_quota * self.subsection_max_ratio)
        subsection_remaining = subsection_max - self.subsection_used
        
        # 全局限制
        total_used = len(self.citation_tracker)
        total_remaining = self.max_total_citations - total_used
        
        # 决定是否添加新引用
        # 条件: 章节有配额 AND 二级标题有配额 AND 全局有配额
        can_add = chapter_remaining > 0 and subsection_remaining > 0 and total_remaining > 0
        target_new = 1 if can_add else 0
        
        logger.debug(f"[{chapter}] 章节配额{chapter_used}/{chapter_quota}, "
                    f"二级标题{self.subsection_used}/{subsection_max}, "
                    f"全局{total_used}/{self.max_total_citations}, 添加={target_new}")
        
        # [*] 使用LLM智能筛选模式
        # 1. 获取原始候选文献（不应用阈值）
        raw_candidates = self.retriever.get_raw_candidates(query, top_k=10)
        
        if not raw_candidates:
            logger.warning(f"查询 '{query}' 未找到相关文献")
            return f"{sentence_skeleton}。", []
        
        # 2. 使用LLM选择最佳文献（如果配置了model_router）
        if self.model_router and len(raw_candidates) > 1:
            best_candidate = self._llm_select_best_citation(sentence_skeleton, raw_candidates)
            selected = [best_candidate] if best_candidate else [raw_candidates[0]]
        else:
            # 回退到多样性选择
            selected = self._diverse_selection(raw_candidates, max(target_new, 1))
        
        # 生成引用序号
        citation_nums = []
        used_lits = []
        new_added = 0  # 本次新增的引用数
        
        for lit_info in selected:
            # [*] 检查是否还允许添加新引用
            if new_added >= target_new and target_new > 0:
                break  # 已达到本次目标新增数
            
            if len(self.citation_tracker) >= self.max_total_citations:
                logger.info(f"已达到最大引用数量限制 ({self.max_total_citations})，停止添加新引用")
                break
            
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
            new_added += 1
            
            # [*] 更新章节和二级标题使用计数
            self.chapter_used[self.current_chapter] = self.chapter_used.get(self.current_chapter, 0) + 1
            self.subsection_used += 1
            
            # 标记为已使用
            lit['used'] = True
            used_lits.append(lit)
        
        # [*] 如果没有添加新引用且已有引用可复用，随机选择1-2个已有引用
        if not citation_nums and self.citation_tracker:
            import random
            existing_nums = list(self.citation_tracker.values())
            reuse_count = min(2, len(existing_nums))
            citation_nums = random.sample(existing_nums, reuse_count)
            logger.debug(f"复用已有引用: {citation_nums}")
        
        # 插入引用
        # 预处理：去掉骨架句末尾标点（包括可能的多余标点）
        clean_skeleton = sentence_skeleton.rstrip('。.,，!！?？ ')
        # 额外保护：如果还有句号，强制去除
        while clean_skeleton.endswith('。'):
            clean_skeleton = clean_skeleton[:-1]
        
        if citation_nums:
            citation_str = ''.join([f'[{num}]' for num in citation_nums])
            sentence_with_citation = f"{clean_skeleton}{citation_str}。"
            logger.debug(f"为句子添加了 {len(citation_nums)} 个引用: {citation_nums}")
        else:
            sentence_with_citation = f"{clean_skeleton}。"
        
        # 最终安全检查：确保没有双句号
        sentence_with_citation = sentence_with_citation.replace('。。', '。')
        
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
        import re
        for lit_id, citation_num in sorted_items:
            # 找到文献
            lit = next(l for l in self.pool if l['id'] == lit_id)
            
            # 清洗原有的序号 [1], [26] 等
            full_cit = lit['full_citation']
            clean_cit = re.sub(r'^\[\d+\]\s*', '', full_cit)
            
            # 使用完整题录
            reference = f"[{citation_num}] {clean_cit}"
            reference_list.append(reference)
        
        logger.info(f"生成参考文献列表: {len(reference_list)} 条")
        # 使用双换行确保分段
        return '\n\n'.join(reference_list)
    
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
    
    def sync_with_text(self, paper_text):
        """
        同步正文中的引用与citation_tracker
        
        扫描正文中所有[N]格式引用，确保：
        1. 正文中使用的每个引用编号都在tracker中有记录
        2. tracker中未在正文中使用的引用会被移除
        
        Args:
            paper_text: 论文正文
            
        Returns:
            同步报告字典
        """
        import re
        import random
        
        report = {
            'text_citations': set(),      # 正文中的引用编号
            'tracker_citations': set(),   # tracker中的引用编号
            'added': [],                  # 新添加的引用
            'removed': [],                # 移除的引用
            'matched': [],                # 匹配的引用
        }
        
        # 1. 提取正文中的所有引用编号
        text_citation_nums = set()
        for match in re.finditer(r'\[(\d+)\]', paper_text):
            num = int(match.group(1))
            text_citation_nums.add(num)
        
        report['text_citations'] = text_citation_nums
        report['tracker_citations'] = set(self.citation_tracker.values())
        
        logger.info(f"引用同步: 正文中有 {len(text_citation_nums)} 个引用编号, tracker中有 {len(self.citation_tracker)} 条记录")
        
        # 2. 找出差异
        tracker_nums = set(self.citation_tracker.values())
        
        # 正文有但tracker没有的编号（异常情况，不应发生）
        missing_in_tracker = text_citation_nums - tracker_nums
        
        # tracker有但正文没有的编号（正常，可能被AI在优化时删除）
        unused_in_text = tracker_nums - text_citation_nums
        
        # 匹配的编号
        matched = text_citation_nums & tracker_nums
        report['matched'] = list(matched)
        
        # 3. 记录缺失的引用（不再随机分配，只记录警告）
        # [*] 移除随机分配逻辑 - 确保引用的真实性
        if missing_in_tracker:
            logger.warning(f"发现 {len(missing_in_tracker)} 个正文引用未在tracker中: {sorted(missing_in_tracker)}")
            logger.warning("这些引用可能是AI在优化/扩写时错误添加的，将被保留但无法生成对应参考文献")
            report['missing'] = list(missing_in_tracker)
        
        # 4. 移除未使用的引用（可选，默认保留以避免丢失数据）
        # 注意：这里选择不移除，因为某些引用可能在后续处理中被使用
        if unused_in_text:
            logger.info(f"tracker中有 {len(unused_in_text)} 个引用未在正文中使用: {unused_in_text}")
            report['removed'] = list(unused_in_text)
            # 不实际删除，只记录
            # for lit_id, num in list(self.citation_tracker.items()):
            #     if num in unused_in_text:
            #         del self.citation_tracker[lit_id]
        
        # 5. 更新next_citation_num
        if text_citation_nums:
            self.next_citation_num = max(text_citation_nums) + 1
        
        logger.info(f"引用同步完成: 匹配{len(matched)}个, 新增{len(report['added'])}个")
        return report
    
    def get_tracker_state(self):
        """
        获取当前tracker状态快照（用于调试）
        
        Returns:
            {lit_id: citation_num, ...}
        """
        return dict(self.citation_tracker)
